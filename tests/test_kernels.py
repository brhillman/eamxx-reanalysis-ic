"""
Unit tests against analytic answers. Run: python -m pytest -q tests
(or python tests/test_kernels.py). Small and fast; fine on a login node.
"""
import os, sys, tempfile
import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import kernels as K
import sources
from cdf5 import ColumnWriter

# Target levels: an EAMxx vertical grid file if VERT_FILE is set, otherwise a
# synthetic 80-level hybrid grid (pure pressure above 100 hPa, top 10 Pa,
# lowest layer ~1.3% of ps thick, i.e. ~100 m, like EAMxx grids).
VERT_FILE = os.environ.get('VERT_FILE')


def target_levels():
    if VERT_FILE:
        v = nc.Dataset(VERT_FILE)
        return tuple(np.asarray(v[k][:], np.float64) for k in ['hyam', 'hybm', 'hyai', 'hybi'])
    x = np.linspace(0.0, 1.0, 81)
    eta = np.exp(np.log(1e-4) * (1.0 - x) ** 1.5)               # interface p/P0, top -> surface
    hybi = np.clip((eta - 0.1) / 0.9, 0.0, 1.0) ** 1.2          # b = 0 above eta = 0.1
    hyai = eta - hybi
    return 0.5 * (hyai[:-1] + hyai[1:]), 0.5 * (hybi[:-1] + hybi[1:]), hyai, hybi
LAT = 90.0 - 0.25 * np.arange(721)
LON = 0.25 * np.arange(1440)
D2R = np.pi / 180


def grid_field(fun):
    la, lo = np.meshgrid(LAT, LON, indexing='ij')
    return np.ascontiguousarray(fun(la, lo)[:, :, None].astype(np.float64))


def stencil(lat, lon, cubic):
    return K.horiz_stencil(lat, lon, 90.0, -0.25, 721, 0.0, 0.25, 1440, cubic)


def test_horizontal_exact_for_linear_and_quadratic():
    rng = np.random.default_rng(1)
    lat = rng.uniform(-80, 80, 5000)
    lon = rng.uniform(0, 360, 5000)
    lin = lambda la, lo: 3.0 + 0.7 * la + 0.2 * np.where(lo > 180, lo - 360, lo)
    quad = lambda la, lo: (la - 10.0) ** 2
    keep = np.abs(np.where(lon > 180, lon - 360, lon)) < 179   # avoid the 180 jump of lin
    for cubic in (False, True):
        jj, ii, wy, wx = stencil(lat, lon, cubic)
        out = np.empty((lat.size, 1))
        K.interp_scalar(grid_field(lin), jj, ii, wy, wx, False, out)
        assert np.abs(out[keep, 0] - lin(lat, lon)[keep]).max() < 1e-9
        assert np.allclose(wy.sum(1), 1) and np.allclose(wx.sum(1), 1)
    jj, ii, wy, wx = stencil(lat, lon, True)
    K.interp_scalar(grid_field(quad), jj, ii, wy, wx, False, out)
    assert np.abs(out[:, 0] - quad(lat, lon)).max() < 1e-8       # cubic reproduces quadratics


def test_clip_prevents_new_extrema():
    f = np.zeros((721, 1440, 1))
    f[300, 700, 0] = 1.0                                          # spike: cubic undershoots
    lat = 90 - 0.25 * (300 + np.linspace(-2, 2, 401))
    lon = np.full(lat.size, 0.25 * 700 + 0.1)
    jj, ii, wy, wx = stencil(lat, lon, True)
    a = np.empty((lat.size, 1)); b = np.empty((lat.size, 1))
    K.interp_scalar(f, jj, ii, wy, wx, False, a)
    K.interp_scalar(f, jj, ii, wy, wx, True, b)
    assert a.min() < 0 and b.min() >= 0 and b.max() <= 1


def test_wind_cross_polar_flow():
    """Solid-body rotation about an axis tilted 60 deg: flow crosses the pole.
    u = U(cos a cos p + sin a sin p cos l), v = -U sin a sin l."""
    U, al = 30.0, 60 * D2R
    uf = lambda la, lo: U * (np.cos(al) * np.cos(la * D2R) + np.sin(al) * np.sin(la * D2R) * np.cos(lo * D2R))
    vf = lambda la, lo: -U * np.sin(al) * np.sin(lo * D2R)
    rng = np.random.default_rng(2)
    lat = np.concatenate([rng.uniform(89.0, 90.0, 2000), rng.uniform(-90, 90, 2000)])
    lon = rng.uniform(0, 360, lat.size)
    for cubic in (False, True):
        jj, ii, wy, wx = stencil(lat, lon, cubic)
        uo = np.empty((lat.size, 1)); vo = np.empty((lat.size, 1))
        K.interp_wind(grid_field(uf), grid_field(vf), LAT, LON, lat, lon, jj, ii, wy, wx, uo, vo)
        err = np.hypot(uo[:, 0] - uf(lat, lon), vo[:, 0] - vf(lat, lon))
        assert err.max() < 0.05, err.max()                        # m/s, incl. near the pole


def test_remap_plm_conserves_and_bounds():
    rng = np.random.default_rng(3)
    e = np.sort(np.concatenate([[0.0, 1e5], rng.uniform(0, 1e5, 60)]))
    q = np.abs(rng.normal(size=e.size - 1)) * 1e-3
    q[10:20] = 0.0
    pt = np.linspace(50.0, 1e5, 129)
    out = np.empty(128)
    K.remap_plm(e, q, q.size, pt, out)
    src_mass = np.sum(q * np.diff(e)) - (q[0] * (pt[0] - e[0]))   # first layer is constant-slope 0
    assert abs(np.sum(out * np.diff(pt)) - src_mass) < 1e-9 * src_mass
    assert out.min() >= 0 and out.max() <= q.max() * (1 + 1e-12)


def _column(T, ps, zs, phis, q=0.0, nsrc=60, u_of_p=None, tf=15000.0, full=False):
    """Isothermal ERA5-like column on pressure-based hybrid levels."""
    ah = np.concatenate([np.linspace(0, 2e4, nsrc // 2 + 1)[:-1], np.linspace(2e4, 0, nsrc - nsrc // 2 + 1)])
    bh = np.concatenate([np.zeros(nsrc // 2), np.linspace(0, 1, nsrc - nsrc // 2 + 1)])
    af, bf = 0.5 * (ah[:-1] + ah[1:]), 0.5 * (bh[:-1] + bh[1:])
    hyam, hybm, hyai, hybi = target_levels()
    n, nt = 1, hyam.size
    Ts = np.full((n, nsrc), T); qs = np.full((n, nsrc), q)
    us = np.full((n, nsrc), 5.0); vs = np.full((n, nsrc), -3.0)
    if u_of_p is not None:
        us[0] = u_of_p(af + bf * ps)
    trc = np.full((1, n, nsrc), 2e-6)
    To, qo, uo, vo = (np.empty((n, nt)) for _ in range(4))
    tro = np.empty((1, n, nt)); pso = np.empty(n); diag = np.empty((n, 3))
    K.column_kernel(True, af, bf, ah, bh, np.array([ps]), np.array([zs]), np.array([phis]),
                    Ts, qs, us, vs, trc, hyam, hybm, hyai, hybi, 1e5, tf,
                    To, qo, uo, vo, tro, pso, diag)
    if full:
        return pso[0], To[0], uo[0], hyam * 1e5 + hybm * pso[0], af + bf * ps
    return pso[0], To[0], qo[0], uo[0], tro[0, 0], diag[0]


def test_ps_adjust_isothermal_upward_is_exact():
    T, ps, zs = 260.0, 9.5e4, 500 * K.G
    phis = 1500 * K.G                                             # model surface 1000 m higher
    psm, To, qo, uo, tro, diag = _column(T, ps, zs, phis)
    exact = ps * np.exp(-(phis - zs) / (K.RD * T))
    # Not bit-exact: between the lowest source level and the surface the
    # kernel assumes the standard lapse rate (as ECMWF does), which in this
    # coarse synthetic column (30 hPa bottom layer) adds ~0.8 K -> ~1.4 Pa.
    assert abs(psm - exact) < 2.0, (psm, exact)                   # Pa
    assert np.allclose(To, T) and np.allclose(uo, 5.0) and np.allclose(tro, 2e-6)


def test_ps_adjust_downward_lapse_rate():
    T, ps, zs = 280.0, 9.0e4, 1000 * K.G
    phis = 800 * K.G                                              # model surface 200 m lower
    psm, To, qo, uo, tro, diag = _column(T, ps, zs, phis)
    # extrapolation from the surface temperature with 6.5 K/km
    assert 1.0 < psm / ps < 1.03 and abs(diag[0] - 200) < 1e-6
    assert To[-1] > T                                             # warmer below the ERA5 surface


def test_winds_terrain_following_near_surface():
    """Model surface 300 m above the source surface; source wind increases
    with height above the source ground (a boundary layer). Terrain-following:
    the lowest model level gets the source wind at the same sigma (near-surface
    value); pressure matching gets the faster wind from 300 m up. Well above
    the blending depth both agree."""
    T, ps, zs = 280.0, 9.0e4, 1000 * K.G
    phis = 1300 * K.G
    u_of_p = lambda p: 2.0 + 10.0 * (1.0 - p / ps) / 0.1        # 2 m/s at ps, +10 m/s per 100 hPa
    psm, To, u_tf, pm, ps_src = _column(T, ps, zs, phis, nsrc=137, u_of_p=u_of_p, tf=15000.0, full=True)
    _, To0, u_p, _, _ = _column(T, ps, zs, phis, nsrc=137, u_of_p=u_of_p, tf=0.0, full=True)
    assert np.allclose(To, To0)                                   # T unaffected
    w = 1.0 - (psm - pm[-1]) / 15000.0                            # ~0.99 at the lowest level
    expect = u_of_p(pm[-1] * (1.0 + w * (ps / psm - 1.0)))        # ~ same-sigma source wind
    assert abs(u_tf[-1] - expect) < 0.05, (u_tf[-1], expect)
    assert abs(u_tf[-1] - u_of_p(pm[-1] * ps / psm)) < 0.2
    assert u_p[-1] > u_tf[-1] + 2.0                               # pressure matching: faster
    hi = pm < psm - 15000.0
    assert np.allclose(u_tf[hi], u_p[hi])                         # identical above the blend
    assert np.all(np.diff(u_tf[pm > 5e4]) < 0)                    # still monotone with height


def test_winds_terrain_following_deep_valley():
    """Model surface ~1.5 km (about 150 hPa) below the source surface. With a
    fixed 150 hPa blending depth the lookup pressure folds and the lowest
    ~150 hPa all take the lowest source wind. The per-column depth
    max(D, 2*(psm - ps)) keeps the lookup monotonic, so the wind still varies
    smoothly through the layer, starts from the near-surface source wind, and
    joins pressure matching above the (deeper) blend."""
    T, ps, zs = 280.0, 8.0e4, 2000 * K.G
    phis = 500 * K.G
    u_of_p = lambda p: 2.0 + 10.0 * (1.0 - p / ps) / 0.1
    psm, _, u_tf, pm, ps_src = _column(T, ps, zs, phis, nsrc=137, u_of_p=u_of_p, tf=15000.0, full=True)
    _, _, u_p, _, _ = _column(T, ps, zs, phis, nsrc=137, u_of_p=u_of_p, tf=0.0, full=True)
    dp = psm - ps
    assert dp > 15000.0 * ps / psm                         # a fixed 150 hPa depth would fold here
    depth = 2.0 * dp
    w = np.clip(1.0 - (psm - pm) / depth, 0.0, None)
    plook = pm * (1.0 + w * (ps / psm - 1.0))
    lay = pm > psm - depth
    assert np.all(np.diff(plook) > 0)                      # monotonic: increases toward the surface
    assert abs(u_tf[-1] - u_of_p(ps_src[-1])) < 0.3        # near-surface source wind at the bottom
    assert np.all(np.diff(u_tf[lay]) < 0)                  # varies through the layer, monotone
    assert len(np.unique(np.round(u_tf[lay], 6))) == lay.sum()
    hi = pm < psm - depth
    assert np.allclose(u_tf[hi], u_p[hi])                  # pressure matching above the blend


def test_interp_lnp_any_matches_sorted():
    pn = np.sort(np.random.default_rng(3).uniform(1e3, 1e5, 40)); fn = np.sin(pn / 1e4)
    pt = np.random.default_rng(4).uniform(5e2, 1.1e5, 200)
    a = np.empty(200); K._interp_lnp_any(pn, fn, 40, pt, a)
    o = np.argsort(pt); b = np.empty(200)
    K._interp_lnp(pn, fn, 40, pt[o], b, False, 0.0, 1e5, 0.0)
    assert np.allclose(a[o], b)


def test_supersaturation_removed():
    psm, To, qo, uo, tro, diag = _column(290.0, 1e5, 0.0, 0.0, q=0.05)
    hyam, hybm = target_levels()[:2]
    pm = hyam * 1e5 + hybm * psm
    qs = np.array([K.qsat_liq(t, p) for t, p in zip(To, pm)])
    assert np.all(qo <= qs * (1 + 1e-12)) and diag[1] > 0
    assert np.isclose(qo[-1], qs[-1])                             # clipped to saturation


def test_cdf5_column_writer_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 't.nc')
        o = nc.Dataset(f, 'w', format='NETCDF3_64BIT_DATA')
        o.set_fill_off()
        o.createDimension('time', None); o.createDimension('ncol', 1000); o.createDimension('lev', 7)
        o.createVariable('A', 'f4', ('time', 'ncol', 'lev'))
        o.createVariable('B', 'f8', ('time', 'ncol'))
        o.createVariable('lat', 'f8', ('ncol',))
        o.createVariable('time', 'f8', ('time',))
        o.title = 'x' * 999                                        # odd-length attribute padding
        o['time'][0] = 0.0
        o['lat'][:] = np.arange(1000)
        o.close()
        a = np.random.default_rng(4).normal(size=(1000, 7))
        b = np.random.default_rng(5).normal(size=1000)
        w = ColumnWriter(f)
        for c0 in (600, 0, 300):                                   # out of order, like tasks
            w.write('A', c0, a[c0:c0 + 300])
            w.write('B', c0, b[c0:c0 + 300])
        w.write('A', 900, a[900:]); w.write('B', 900, b[900:])
        w.close()
        r = nc.Dataset(f)
        assert np.allclose(r['A'][0], a.astype(np.float32)) and np.allclose(r['B'][0], b)
        assert np.array_equal(r['lat'][:], np.arange(1000))


def test_horizontal_south_to_north_grid_from_minus180():
    """MERRA-2 layout: 361 latitudes from -90, 576 longitudes from -180."""
    lat_s = -90.0 + 0.5 * np.arange(361)
    lon_s = -180.0 + 0.625 * np.arange(576)
    sources.check_grid(lat_s, lon_s)
    la, lo = np.meshgrid(lat_s, lon_s, indexing='ij')
    f = np.ascontiguousarray((2.0 + 0.3 * la + 0.01 * lo)[:, :, None])
    rng = np.random.default_rng(6)
    lat = rng.uniform(-80, 80, 3000)
    lon = rng.uniform(-170, 170, 3000) % 360             # destination in 0..360
    for cubic in (False, True):
        jj, ii, wy, wx = K.horiz_stencil(lat, lon, -90.0, 0.5, 361, -180.0, 0.625, 576, cubic)
        out = np.empty((lat.size, 1))
        K.interp_scalar(f, jj, ii, wy, wx, False, out)
        lon180 = np.where(lon > 180, lon - 360, lon)
        assert np.abs(out[:, 0] - (2.0 + 0.3 * lat + 0.01 * lon180)).max() < 1e-9


def test_fit_hybrid_recovers_coefficients():
    rng = np.random.default_rng(7)
    a = np.concatenate([np.linspace(1, 2e4, 30), np.linspace(2e4, 0, 43)])
    b = np.concatenate([np.zeros(30), np.linspace(0, 1, 43)])
    ps = rng.uniform(5e4, 1.05e5, 5000)
    pk = (a[:, None] + b[:, None] * ps[None, :]).astype(np.float32).astype(np.float64)
    af, bf = sources._fit_hybrid(pk, ps)
    assert np.abs(af - a).max() < 0.05 and np.abs(bf - b).max() < 1e-6
    bad = pk + rng.normal(0, 50, pk.shape)               # not hybrid: must be rejected
    try:
        sources._fit_hybrid(bad, ps)
        assert False, 'non-hybrid levels accepted'
    except ValueError:
        pass


def test_fill_below_ground():
    p = np.array([5e4, 7e4, 8.5e4, 1e5])
    t = np.full((4, 2, 2), np.nan); q = np.full((4, 2, 2), np.nan)
    t[:2] = 250.0; q[:2] = 1e-3
    t[2, 0, 0] = 260.0; q[2, 0, 0] = 2e-3                 # one column valid one level deeper
    tf = sources._fill_below_ground(t, p, 't')
    qf = sources._fill_below_ground(q, p, 'q')
    assert np.isfinite(tf).all() and np.isfinite(qf).all()
    assert np.isclose(tf[3, 0, 0], 260.0 * (1e5 / 8.5e4) ** (sources.RD * sources.GAMMA_STD / sources.G))
    assert tf[2, 1, 1] > 250.0 and qf[3, 1, 1] == 1e-3 and qf[3, 0, 0] == 2e-3


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
