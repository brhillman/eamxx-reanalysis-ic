"""
ERA5 source data readers. Each returns a Source with:
  lat (N->S), lon (from 0), regular 0.25 deg global grid
  is_ml, a_full, b_full, a_half, b_half: vertical coordinate, top->bottom,
    p_full = a_full + b_full*ps (pressure levels: a_full = p, b_full = 0)
  f3d: dict of 3D fields as float32 [nlat, nlon, nlev] (level fastest, so a
    column's levels are contiguous for the interpolation kernels)
  lnps, zs: [nlat, nlon, 1] log surface pressure [ln Pa], surface
    geopotential [m2/s2]
Fields: t, q, u, v, clwc, ciwc, o3, and optionally cswc (snow; added to
cloud ice since P3's single ice category includes snow) and crwc (rain).
"""
from dataclasses import dataclass, field
import numpy as np
import netCDF4 as nc


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


def _level_last(a):
    """[nlev, nlat, nlon] -> contiguous float32 [nlat, nlon, nlev]"""
    return np.ascontiguousarray(np.moveaxis(np.asarray(a, dtype=np.float32), 0, -1))


def _check_grid(lat, lon):
    if not (np.isclose(lat[0], 90) and np.isclose(lat[-1], -90) and lat.size == 721):
        raise ValueError('expected 721 latitudes from 90 to -90')
    if not (np.isclose(lon[0], 0) and lon.size == 1440 and np.allclose(np.diff(lon), 0.25)):
        raise ValueError('expected 1440 longitudes from 0 by 0.25')


def _read(ds, name):
    v = ds[name]
    v.set_auto_maskandscale(True)
    a = v[:]
    a = np.ma.filled(a.astype(np.float64), np.nan) if np.ma.isMaskedArray(a) else np.asarray(a, np.float64)
    if v.dimensions[0] in ('time', 'valid_time'):
        a = a[0]
    if np.isnan(a).any():
        raise ValueError(f'NaN or missing values in {name}')
    return a


def read_era5_pl(atm_file, sfc_file, fields):
    """ERA5 on pressure levels (CDS netCDF; e.g. the HICCUP input files)."""
    a = nc.Dataset(atm_file)
    s = nc.Dataset(sfc_file)
    lat, lon = a['latitude'][:].data, a['longitude'][:].data
    _check_grid(lat, lon)
    plev = a['pressure_level'][:].data * 100.0
    order = np.argsort(plev)                     # top -> bottom
    plev = plev[order]
    src = Source(lat=lat, lon=lon, is_ml=False,
                 a_full=plev, b_full=np.zeros_like(plev),
                 a_half=np.zeros(plev.size + 1), b_half=np.zeros(plev.size + 1),
                 lnps=np.log(_read(s, 'sp'))[:, :, None].astype(np.float32),
                 zs=_read(s, 'z')[:, :, None].astype(np.float32),
                 files=[atm_file, sfc_file])
    for f in fields:
        if f in a.variables:
            src.f3d[f] = _level_last(_read(a, f)[order])
    return src


def read_ab(ab_file):
    """L137 hybrid coefficients (a [Pa], b) at the 138 half levels, top->bottom.
    Text file with two columns a b, from the GRIB 'pv' array (see
    grib_to_nc.sh)."""
    ab = np.loadtxt(ab_file)
    return ab[:, 0], ab[:, 1]


def read_era5_ml(ml_file, sfc_file, ab_file, fields):
    """ERA5 on model levels (CDS reanalysis-era5-complete GRIB converted to
    netCDF by grib_to_nc.sh). sfc_file holds lnsp and z on model level 1."""
    a = nc.Dataset(ml_file)
    s = nc.Dataset(sfc_file)
    lat, lon = a['latitude'][:].data, a['longitude'][:].data
    _check_grid(lat, lon)
    lev = a['level'][:].data.astype(int)
    if not np.array_equal(lev, np.arange(1, 138)):
        raise ValueError('expected model levels 1..137')
    ah, bh = read_ab(ab_file)
    if ah.size != 138:
        raise ValueError('expected 138 half-level coefficients')
    lnsp = _read(s, 'lnsp')
    zs = _read(s, 'z')
    if lnsp.ndim == 3:
        lnsp, zs = lnsp[0], zs[0]
    src = Source(lat=lat, lon=lon, is_ml=True,
                 a_full=0.5 * (ah[:-1] + ah[1:]), b_full=0.5 * (bh[:-1] + bh[1:]),
                 a_half=ah, b_half=bh,
                 lnps=lnsp[:, :, None].astype(np.float32),
                 zs=zs[:, :, None].astype(np.float32),
                 files=[ml_file, sfc_file, ab_file])
    for f in fields:
        if f in a.variables:
            src.f3d[f] = _level_last(_read(a, f))
    return src
