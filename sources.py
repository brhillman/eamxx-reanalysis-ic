"""
Source data readers. Every reader returns a Source on a regular global
lat-lon grid (either latitude order, any longitude origin) with:
  is_ml, a_full, b_full, a_half, b_half: vertical coordinate, top->bottom,
    p_full = a_full + b_full*ps (pressure levels: a_full = p, b_full = 0)
  f3d: 3D fields as float32 [nlat, nlon, nlev] (levels contiguous per column)
    with standard names t, q (specific humidity), u, v (earth-relative),
    clwc, ciwc, o3 (mass mixing ratio), optional cswc (snow)
  lnps, zs: [nlat, nlon, 1] ln(surface pressure [Pa]), surface geopotential [m2/s2]

Readers:
  ecmwf-ml  ERA5 or IFS analysis on model levels (any number of levels),
            MARS/CDS GRIB converted to netCDF (see grib_to_nc.sh)
  era5-pl   ERA5 on pressure levels (CDS netCDF)
  merra2-ml MERRA-2 inst3_3d_asm_Nv (72 model levels)
  merra2-pl MERRA-2 inst3_3d_asm_Np (42 pressure levels)
"""
from dataclasses import dataclass, field
import numpy as np
import netCDF4 as nc

RD, G, GAMMA_STD = 287.042, 9.80616, 0.0065


@dataclass
class Source:
    lat: np.ndarray
    lon: np.ndarray
    is_ml: bool
    a_full: np.ndarray
    b_full: np.ndarray
    a_half: np.ndarray
    b_half: np.ndarray
    lnps: np.ndarray
    zs: np.ndarray
    f3d: dict = field(default_factory=dict)
    files: list = field(default_factory=list)


def check_grid(lat, lon):
    """Regular global lat-lon: uniform spacing, latitudes from pole to pole
    (either direction), longitudes covering 360 degrees."""
    dlat, dlon = np.diff(lat), np.diff(lon)
    if not (np.allclose(dlat, dlat[0]) and np.isclose(abs(lat[0]), 90) and np.isclose(lat[0], -lat[-1])):
        raise ValueError('latitudes must be uniform from pole to pole')
    if not (np.allclose(dlon, dlon[0]) and dlon[0] > 0 and np.isclose(dlon[0] * lon.size, 360)):
        raise ValueError('longitudes must be uniform, increasing and global')


def _level_last(a):
    """[nlev, nlat, nlon] -> contiguous float32 [nlat, nlon, nlev]"""
    return np.ascontiguousarray(np.moveaxis(np.asarray(a, dtype=np.float32), 0, -1))


def _read(ds, name, it=0, allow_missing=False):
    """Read a variable at time index it as float64; masked -> NaN."""
    v = ds[name]
    v.set_auto_maskandscale(True)
    if v.dimensions and v.dimensions[0] in ('time', 'valid_time'):
        a = v[it]
    else:
        a = v[:]
    a = np.ma.filled(np.ma.asarray(a).astype(np.float64), np.nan)
    if not allow_missing and np.isnan(a).any():
        raise ValueError(f'missing values in {name}')
    return a


def _time_index(ds, hour):
    """Index of the record at the requested hour (files holding one day)."""
    tname = 'time' if 'time' in ds.variables else 'valid_time'
    t = ds[tname]
    if t.size == 1:
        return 0
    units = t.units.split()[0]
    vals = np.asarray(t[:], np.float64) * {'minutes': 1 / 60, 'hours': 1, 'seconds': 1 / 3600}[units]
    hit = np.where(np.isclose(vals % 24, hour))[0]
    if hit.size != 1:
        raise ValueError(f'hour {hour} not found in {ds.filepath()}')
    return int(hit[0])


def _fill_below_ground(f, p, name):
    """Fill missing values below the lowest valid level of each column
    (pressure-level data that mask underground levels, e.g. MERRA-2):
    T by the standard lapse rate in pressure, other fields held constant.
    f: [nlev, nlat, nlon] top->bottom; p: [nlev] Pa."""
    valid = np.isfinite(f)
    if valid.all():
        return f
    if not valid[0].all():
        raise ValueError(f'{name}: missing values at the top level')
    out = f.copy()
    for k in range(1, f.shape[0]):
        miss = ~np.isfinite(out[k])
        if not miss.any():
            continue
        if name == 't':
            out[k][miss] = out[k - 1][miss] * (p[k] / p[k - 1]) ** (RD * GAMMA_STD / G)
        else:
            out[k][miss] = out[k - 1][miss]
    return out


def _fit_hybrid(pk, ps):
    """Fit p = a + b*ps per level from many columns: pk [nlev, ncol], ps [ncol].
    Exact for hybrid sigma-pressure data; the residual is checked."""
    A = np.vstack([np.ones_like(ps), ps]).T
    coef, *_ = np.linalg.lstsq(A, pk.T, rcond=None)
    a, b = coef[0], coef[1]
    res = np.abs(pk - (a[:, None] + b[:, None] * ps[None, :])).max()
    if res > 0.5:                                     # Pa (float32 data)
        raise ValueError(f'levels are not hybrid sigma-pressure (residual {res:.2f} Pa)')
    b[np.abs(b) < 1e-7] = 0.0
    return a, b


# ------------------------------------------------------------------------------
def read_ecmwf_ml(atm_file, sfc_file, ab_file, fields, hour):
    """ERA5 or IFS on model levels. atm_file: 3D fields with dims (time,)
    level, latitude, longitude; sfc_file: lnsp and z on model level 1;
    ab_file: half-level a [Pa] b, two columns, top->bottom (from GRIB pv)."""
    a = nc.Dataset(atm_file)
    s = nc.Dataset(sfc_file)
    lat, lon = a['latitude'][:].data, a['longitude'][:].data
    check_grid(lat, lon)
    ab = np.loadtxt(ab_file)
    ah, bh = ab[:, 0], ab[:, 1]
    lev = a['level'][:].data.astype(int)
    if not np.array_equal(lev, np.arange(1, ah.size)):
        raise ValueError(f'expected model levels 1..{ah.size - 1} to match {ab_file}')
    it, its = _time_index(a, hour), _time_index(s, hour)
    lnsp, zs = _read(s, 'lnsp', its), _read(s, 'z', its)
    while lnsp.ndim > 2:
        lnsp, zs = lnsp[0], zs[0]
    src = Source(lat=lat, lon=lon, is_ml=True,
                 a_full=0.5 * (ah[:-1] + ah[1:]), b_full=0.5 * (bh[:-1] + bh[1:]),
                 a_half=ah, b_half=bh,
                 lnps=lnsp[:, :, None].astype(np.float32), zs=zs[:, :, None].astype(np.float32),
                 files=[atm_file, sfc_file, ab_file])
    for f in fields:
        if f in a.variables:
            src.f3d[f] = _level_last(_read(a, f, it))
    return src


def read_era5_pl(atm_file, sfc_file, fields, hour):
    """ERA5 on pressure levels (CDS netCDF). ECMWF fills underground levels
    with extrapolated values, so no masking is needed."""
    a = nc.Dataset(atm_file)
    s = nc.Dataset(sfc_file)
    lat, lon = a['latitude'][:].data, a['longitude'][:].data
    check_grid(lat, lon)
    plev = a['pressure_level'][:].data * 100.0
    order = np.argsort(plev)                     # top -> bottom
    plev = plev[order]
    it, its = _time_index(a, hour), _time_index(s, hour)
    src = Source(lat=lat, lon=lon, is_ml=False,
                 a_full=plev, b_full=np.zeros_like(plev),
                 a_half=np.zeros(plev.size + 1), b_half=np.zeros(plev.size + 1),
                 lnps=np.log(_read(s, 'sp', its))[:, :, None].astype(np.float32),
                 zs=_read(s, 'z', its)[:, :, None].astype(np.float32),
                 files=[atm_file, sfc_file])
    for f in fields:
        if f in a.variables:
            src.f3d[f] = _level_last(_read(a, f, it)[order])
    return src


MERRA2_NAMES = {'t': 'T', 'q': 'QV', 'u': 'U', 'v': 'V', 'clwc': 'QL', 'ciwc': 'QI', 'o3': 'O3'}


def read_merra2_ml(atm_file, fields, hour):
    """MERRA-2 inst3_3d_asm_Nv: 72 hybrid levels (level 1 = top). DELP and
    PS give the level pressures; a and b are fitted from them (and from PL
    for full levels) rather than typed in."""
    a = nc.Dataset(atm_file)
    lat, lon = a['lat'][:].data, a['lon'][:].data
    check_grid(lat, lon)
    it = _time_index(a, hour)
    ps = _read(a, 'PS', it)
    delp = _read(a, 'DELP', it)
    ptop = ps - delp.sum(0)
    if np.ptp(ptop) > 0.5:
        raise ValueError(f'model top pressure varies ({ptop.min():.2f}..{ptop.max():.2f} Pa)')
    ph = float(ptop.mean()) + np.concatenate([np.zeros((1,) + ps.shape), np.cumsum(delp, 0)])
    rng = np.random.default_rng(0)
    sel = rng.choice(ps.size, min(20000, ps.size), replace=False)
    psf = ps.ravel()[sel]
    ah, bh = _fit_hybrid(ph.reshape(ph.shape[0], -1)[:, sel], psf)
    if 'PL' in a.variables:
        af, bf = _fit_hybrid(_read(a, 'PL', it).reshape(delp.shape[0], -1)[:, sel], psf)
    else:
        af, bf = 0.5 * (ah[:-1] + ah[1:]), 0.5 * (bh[:-1] + bh[1:])
    src = Source(lat=lat, lon=lon, is_ml=True, a_full=af, b_full=bf, a_half=ah, b_half=bh,
                 lnps=np.log(ps)[:, :, None].astype(np.float32),
                 zs=_read(a, 'PHIS', it)[:, :, None].astype(np.float32),
                 files=[atm_file])
    for f in fields:
        if f in MERRA2_NAMES and MERRA2_NAMES[f] in a.variables:
            src.f3d[f] = _level_last(_read(a, MERRA2_NAMES[f], it))
    return src


def read_merra2_pl(atm_file, fields, hour):
    """MERRA-2 inst3_3d_asm_Np: 42 pressure levels; underground levels are
    missing and are filled below the lowest valid level (_fill_below_ground)."""
    a = nc.Dataset(atm_file)
    lat, lon = a['lat'][:].data, a['lon'][:].data
    check_grid(lat, lon)
    it = _time_index(a, hour)
    plev = a['lev'][:].data * 100.0
    order = np.argsort(plev)
    plev = plev[order]
    src = Source(lat=lat, lon=lon, is_ml=False,
                 a_full=plev, b_full=np.zeros_like(plev),
                 a_half=np.zeros(plev.size + 1), b_half=np.zeros(plev.size + 1),
                 lnps=np.log(_read(a, 'PS', it))[:, :, None].astype(np.float32),
                 zs=_read(a, 'PHIS', it)[:, :, None].astype(np.float32),
                 files=[atm_file])
    for f in fields:
        if f in MERRA2_NAMES and MERRA2_NAMES[f] in a.variables:
            x = _read(a, MERRA2_NAMES[f], it, allow_missing=True)[order]
            src.f3d[f] = _level_last(_fill_below_ground(x, plev, f))
    return src


SOURCES = ['era5-ml', 'ifs-ml', 'era5-pl', 'merra2-ml', 'merra2-pl']


def read_source(kind, atm, sfc, ab, fields, hour):
    if kind in ('era5-ml', 'ifs-ml'):
        return read_ecmwf_ml(atm, sfc, ab, fields, hour)
    if kind == 'era5-pl':
        return read_era5_pl(atm, sfc, fields, hour)
    if kind == 'merra2-ml':
        return read_merra2_ml(atm, fields, hour)
    if kind == 'merra2-pl':
        return read_merra2_pl(atm, fields, hour)
    raise ValueError(f'unknown source {kind}')
