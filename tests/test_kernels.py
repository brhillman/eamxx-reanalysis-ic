"""
Unit tests against analytic answers. Run: python -m pytest -q tests
(or python tests/test_kernels.py). Small and fast; fine on a login node.
"""
import os, sys, tempfile
import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import kernels as K
from cdf5 import ColumnWriter

VERT_FILE = os.environ.get('VERT_FILE',
    '/global/homes/b/bhillma/codes/HICCUP-latest/files_vert/L128_for_E3SMv4_c20260820.nc')
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


def _column(T, ps, zs, phis, q=0.0, nsrc=60):
    """Isothermal ERA5-like column on pressure-based hybrid levels."""
    ah = np.concatenate([np.linspace(0, 2e4, nsrc // 2 + 1)[:-1], np.linspace(2e4, 0, nsrc - nsrc // 2 + 1)])
    bh = np.concatenate([np.zeros(nsrc // 2), np.linspace(0, 1, nsrc - nsrc // 2 + 1)])
    af, bf = 0.5 * (ah[:-1] + ah[1:]), 0.5 * (bh[:-1] + bh[1:])
    v = nc.Dataset(VERT_FILE)
    hyam, hybm, hyai, hybi = (np.asarray(v[k][:], np.float64) for k in ['hyam', 'hybm', 'hyai', 'hybi'])
    n, nt = 1, hyam.size
    Ts = np.full((n, nsrc), T); qs = np.full((n, nsrc), q)
    us = np.full((n, nsrc), 5.0); vs = np.full((n, nsrc), -3.0)
    trc = np.full((1, n, nsrc), 2e-6)
    To, qo, uo, vo = (np.empty((n, nt)) for _ in range(4))
    tro = np.empty((1, n, nt)); pso = np.empty(n); diag = np.empty((n, 3))
    K.column_kernel(True, af, bf, ah, bh, np.array([ps]), np.array([zs]), np.array([phis]),
                    Ts, qs, us, vs, trc, hyam, hybm, hyai, hybi, 1e5,
                    To, qo, uo, vo, tro, pso, diag)
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


def test_supersaturation_removed():
    psm, To, qo, uo, tro, diag = _column(290.0, 1e5, 0.0, 0.0, q=0.05)
    v = nc.Dataset(VERT_FILE)
    pm = np.asarray(v['hyam'][:]) * 1e5 + np.asarray(v['hybm'][:]) * psm
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


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
