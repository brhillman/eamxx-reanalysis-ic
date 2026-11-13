"""Near-surface fields over a Wyoming box (where grid-scale noise in the CONUS
x2/x3 runs was traced to the IC): grid imprinting and wind vs terrain mismatch.

Usage:
    python terrain_metrics.py TOPO ERA5_ML_DIR OUT.png LABEL=IC.nc [LABEL=IC.nc ...]

Metrics, lowest model level unless noted:
  roughness   mean |x - mean of its 6 nearest GLL nodes|. Blocky imprinting of
              the 0.25 deg source grid raises it; the source itself cannot
              contribute much at ~1-3 km node spacing.
  corr(dz)    correlation of wind speed with the model-minus-ERA5 surface
              height. ERA5's own near-surface wind has ~0 correlation with this
              (it never sees the model terrain); a large positive value means
              the IC placed free-atmosphere wind on ridges because of the
              surface mismatch, not because of any physics.
  speed by dz mean wind speed where the model surface is >= 50 m below ERA5's,
              within 20 m, and >= 100 m above.
"""
import os, sys, glob
import numpy as np, netCDF4 as nc
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.tri as mtri
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial import cKDTree

topo_f, mldir, out = sys.argv[1:4]
files = dict(a.split('=', 1) for a in sys.argv[4:])
# BOX=lat0,lat1,lon0,lon1 (deg, lon 0-360); default: the Wyoming box. NAME labels the
# figure. PL=ERA5 pressure-level file adds a hydrostatic check over the box.
box = tuple(map(float, os.environ.get('BOX', '42,44,252,254.5').split(',')))
name = os.environ.get('NAME', 'Wyoming')
pl_f = os.environ.get('PL')

t = nc.Dataset(topo_f)
lat = t['lat_d'][:].data; lon = t['lon_d'][:].data % 360
idx = np.nonzero((lat > box[0]) & (lat < box[1]) & (lon > box[2]) & (lon < box[3]))[0]
runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
def rd(ds, v, k=None):
    x = ds[v]
    pick = (lambda r: x[0, r[0]:r[-1] + 1, k]) if k is not None else \
           (lambda r: x[0, r[0]:r[-1] + 1]) if x.dimensions[0] == 'time' else (lambda r: x[r[0]:r[-1] + 1])
    return np.concatenate([np.asarray(pick(r)) for r in runs]).astype(float)
zm = rd(t, 'PHIS_d') / 9.80616
s = nc.Dataset(glob.glob(os.path.join(mldir, '*.sfc.nc'))[0])
la = s['latitude'][:].data; lo = s['longitude'][:].data
ip = lambda f: RegularGridInterpolator((la[::-1], lo), f[::-1])(np.c_[lat[idx], lon[idx]])
dz = zm - ip(np.squeeze(s['z'][:]) / 9.80616)
a3 = nc.Dataset(glob.glob(os.path.join(mldir, '*.3d.nc'))[0])
sp_era5 = ip(np.hypot(np.squeeze(a3['u'][0, -1]), np.squeeze(a3['v'][0, -1])))

clat = 0.5 * (box[0] + box[1])
xy = np.c_[lon[idx] * np.cos(np.radians(clat)), lat[idx]]
nb = cKDTree(xy).query(xy, k=7)[1][:, 1:]
rough = lambda x: np.mean(np.abs(x - x[nb].mean(1)))

print(f'{idx.size} columns in box {box}; model minus ERA5 surface 5/50/95%: {np.percentile(dz, [5, 50, 95]).round(0)} m')
print('\n| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) '
      '| speed, dz ≤ −50 m | \\|dz\\| < 20 m | dz ≥ 100 m |')
print('|---|---|---|---|---|---|---|---|')
row = lambda n, rT, rq, rU, sp: print(f'| {n} | {rT} | {rq} | {rU} | {np.corrcoef(sp, dz)[0, 1]:+.2f} | '
                                      f'{sp[dz <= -50].mean():.1f} | {sp[abs(dz) < 20].mean():.1f} | {sp[dz >= 100].mean():.1f} |')
row('ERA5 lowest model level (~10 m), interpolated', '–', '–', '–', sp_era5)
speeds = {}
zerr = {}
if pl_f:
    e = nc.Dataset(pl_f)
    eplev = e['pressure_level'][:]
    zref = {p: ip(np.squeeze(e['z'][0, int(np.where(np.isclose(eplev, p))[0][0])]) / 9.80616) for p in (500, 300)}
for n, f in files.items():
    d = nc.Dataset(f)
    T, q, u, v = (rd(d, x, 127) for x in ['T_mid', 'qv', 'U', 'V'])
    speeds[n] = np.hypot(u, v)
    row(n, f'{rough(T):.3f}', f'{rough(q) * 1e3:.4f}', f'{rough(u):.3f}', speeds[n])
    if pl_f:
        # height of 500 and 300 hPa integrated up from PHIS_d through the IC's ps, T, qv
        Tf = np.concatenate([np.asarray(d['T_mid'][0, r[0]:r[-1] + 1, :]) for r in runs]).astype(float)
        qf = np.concatenate([np.asarray(d['qv'][0, r[0]:r[-1] + 1, :]) for r in runs]).astype(float)
        ps = rd(d, 'ps')
        P0 = float(d['P0'][...]) if 'P0' in d.variables else 1e5
        pi = d['hyai'][:][None, :] * P0 + d['hybi'][:][None, :] * ps[:, None]
        Tv = Tf * (1 + (461.505 / 287.042 - 1) * qf)
        dphi = 287.042 * Tv * np.log(pi[:, 1:] / pi[:, :-1])
        phi_i = zm[:, None] * 9.80616 + np.concatenate([np.cumsum(dphi[:, ::-1], axis=1)[:, ::-1], np.zeros((ps.size, 1))], axis=1)
        zerr[n] = {}
        for p in (500, 300):
            zp = np.array([np.interp(np.log(p * 100.), np.log(pi[c]), phi_i[c]) for c in range(ps.size)]) / 9.80616
            ok = ps > (700e2 if p == 500 else 0)
            zerr[n][p] = (zp - zref[p])[ok]
if pl_f:
    print(f'\nHydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m);'
          f' z500 where ps > 700 hPa, z300 everywhere')
    print('| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |')
    print('|---|---|---|---|---|')
    for n, z in zerr.items():
        a, b = z[500], z[300]
        f5 = f'{a.mean():+.2f} ± {a.std():.2f} | {np.abs(a).max():.1f}' if a.size else '– | –'
        print(f'| {n} | {f5} | {b.mean():+.2f} ± {b.std():.2f} | {np.abs(b).max():.1f} |')

tri = mtri.Triangulation(lon[idx], lat[idx])
m_ = len(files) + 1
fig, ax = plt.subplots(1, m_, figsize=(4.4 * m_, 4.6), constrained_layout=True)
asp = 1 / np.cos(np.radians(0.5 * (box[0] + box[1])))
vmax = np.ceil(max(np.percentile(sp, 99) for sp in speeds.values()))
for i, (n, sp) in enumerate(speeds.items()):
    m = ax[i].tripcolor(tri, sp, shading='gouraud', vmin=0, vmax=vmax)
    ax[i].set_title(f'{n}\n{name}: lowest-level wind speed', fontsize=8.5); ax[i].set_aspect(asp)
fig.colorbar(m, ax=ax[:-1], shrink=0.8, label='m/s')
m = ax[-1].tripcolor(tri, dz, shading='gouraud', cmap='RdBu_r', vmin=-400, vmax=400)
ax[-1].set_title('model surface minus ERA5 surface', fontsize=8.5); ax[-1].set_aspect(asp)
fig.colorbar(m, ax=ax[-1], shrink=0.8, label='m')
for a in ax: a.set_xlabel('longitude'); a.tick_params(labelsize=7)
ax[0].set_ylabel('latitude')
fig.savefig(out, dpi=100)
print('\nwrote', out)
