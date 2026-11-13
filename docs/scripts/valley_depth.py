"""How often is the model surface far below the source surface? Counts columns
by dp = ps (IC, on the model surface) - ERA5 surface pressure (bilinear at the
node), where the terrain-following wind lookup folds (dp > D*ps_era5/ps,
about 125 hPa for the default D = 150 hPa).

Usage: python valley_depth.py ERA5_ML_DIR LABEL=IC.nc [LABEL=IC.nc ...]
"""
import os, sys, glob
import numpy as np, netCDF4 as nc
from scipy.interpolate import RegularGridInterpolator
mldir = sys.argv[1]
s = nc.Dataset(glob.glob(os.path.join(mldir, '*.sfc.nc'))[0])
la = s['latitude'][:].data; lo = s['longitude'][:].data
lnsp = np.squeeze(s['lnsp'][:]).astype(float)
lo2 = np.r_[lo, lo[0] + 360]; f2 = np.c_[lnsp, lnsp[:, :1]]
ip = RegularGridInterpolator((la[::-1], lo2), f2[::-1])
D = 15000.
print('| grid | columns | dp > 50 hPa | dp > 100 hPa | folded (dp > 150·ps_e/ps) | dp > 150 hPa | max dp | where (lat, lon) |')
print('|---|---|---|---|---|---|---|---|')
for lab, f in (a.split('=', 1) for a in sys.argv[2:]):
    d = nc.Dataset(f); n = d['ps'].shape[-1]
    cnt = np.zeros(4, int); mx = -1e9; where = None
    for c0 in range(0, n, 20_000_000):
        c1 = min(n, c0 + 20_000_000)
        ps = np.asarray(d['ps'][0, c0:c1], float)
        lat = np.asarray(d['lat'][c0:c1], float); lon = np.asarray(d['lon'][c0:c1], float) % 360
        pe = np.exp(ip(np.c_[lat, lon]))
        dp = ps - pe
        cnt += [(dp > 5000).sum(), (dp > 10000).sum(), (dp > D * pe / ps).sum(), (dp > 15000).sum()]
        i = dp.argmax()
        if dp[i] > mx: mx = dp[i]; where = (lat[i], lon[i])
    print(f'| {lab} | {n:,} | {cnt[0]:,} | {cnt[1]:,} | {cnt[2]:,} | {cnt[3]:,} | {mx/100:.0f} hPa | {where[0]:.2f}, {where[1]:.2f} |', flush=True)
