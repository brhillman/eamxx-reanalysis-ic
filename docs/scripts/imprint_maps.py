"""Maps of lowest-level T and qv, and qv near 600 hPa, over the Wyoming box,
with the ERA5 0.25 deg grid overlaid, to show source-grid imprinting.

Usage:
    python imprint_maps.py TOPO OUT.png LABEL=IC.nc [LABEL=IC.nc ...]
"""
import sys
import numpy as np, netCDF4 as nc
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.tri as mtri

topo_f, out = sys.argv[1:3]
files = dict(a.split('=', 1) for a in sys.argv[3:])
box = (42.0, 44.0, 252.0, 254.5)
t = nc.Dataset(topo_f)
lat = t['lat_d'][:].data; lon = t['lon_d'][:].data % 360
idx = np.nonzero((lat > box[0]) & (lat < box[1]) & (lon > box[2]) & (lon < box[3]))[0]
runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
rd = lambda ds, v, k: np.concatenate([np.asarray(ds[v][0, r[0]:r[-1] + 1, k]) for r in runs]).astype(float)
fields = [('T_mid', 127, 'K', 'lowest-level T', 1), ('qv', 127, 'g/kg', 'lowest-level qv', 1e3),
          ('qv', 80, 'g/kg', 'qv, level 80 (~600 hPa)', 1e3)]
data = {n: [rd(nc.Dataset(f), v, k) * s for v, k, _, _, s in fields] for n, f in files.items()}

tri = mtri.Triangulation(lon[idx], lat[idx])
fig, ax = plt.subplots(len(fields), len(files), figsize=(4.6 * len(files), 3.9 * len(fields)),
                       constrained_layout=True, squeeze=False)
for j, (v, k, units, title, _) in enumerate(fields):
    lo = min(np.percentile(d[j], 1) for d in data.values()); hi = max(np.percentile(d[j], 99) for d in data.values())
    for i, n in enumerate(files):
        a = ax[j, i]
        m = a.tripcolor(tri, data[n][j], shading='gouraud', vmin=lo, vmax=hi, cmap='viridis')
        a.set_title(f'{n}\n{title}', fontsize=8.5)
        for g in np.arange(box[2], box[3] + 0.01, 0.25): a.axvline(g, color='w', lw=0.2, alpha=0.5)
        for g in np.arange(box[0], box[1] + 0.01, 0.25): a.axhline(g, color='w', lw=0.2, alpha=0.5)
        a.set_aspect(1 / np.cos(np.radians(43))); a.tick_params(labelsize=7)
    fig.colorbar(m, ax=ax[j, :], shrink=0.8, label=units)
fig.savefig(out, dpi=90)
print('wrote', out)
