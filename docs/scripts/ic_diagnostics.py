"""Apply identical diagnostics to several EAMxx IC files on the same columns.

Usage:
    python ic_diagnostics.py TOPO ERA5_ML_DIR ERA5_PL_FILE LABEL=IC.nc [LABEL=IC.nc ...]

All files must be on the np4 grid of TOPO (same column order). Columns are
sampled as 300 random runs of 100 consecutive columns (fast on Lustre), the
same runs for every file. Reference data are ERA5 for 2011-05-19 18Z:
    ERA5_ML_DIR  ERA5.ml.<date>.<hh>.{3d,sfc}.nc and .ab.txt (137 model levels)
    ERA5_PL_FILE ERA5 pressure levels with z (analysed 500 hPa height)

Metrics (all on the IC as written; EAMxx constants and saturation formula):
  negatives       count of negative qv, qc, qi, o3
  RH max, n>1     max relative humidity over liquid (Murphy-Koop, as P3) and
                  number of points above 100.001 %
  phis            rms and max |phis - PHIS_d| (EAMxx uses PHIS_d at run time)
  z500            500 hPa height integrated from PHIS_d with ps, T, qv
                  minus ERA5's analysed z500, columns with ps > 700 hPa;
                  also for columns where the model surface is > 300 m from
                  ERA5's (where the surface-pressure adjustment matters)
  T upper         T minus ERA5 model-level T (nearest ERA5 point, linear in
                  ln p) at target levels above 10 hPa, where ERA5 pressure
                  levels (top 1 hPa) have to be extrapolated
  TQV, ps         column water vapour and ps minus ERA5 (nearest point), in
                  columns where model and ERA5 surfaces agree within 20 m,
                  so the vertical remap's conservation is tested directly
"""
import os, sys, glob
import numpy as np, netCDF4 as nc
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import kernels as K

topo_f, mldir, pl_f = sys.argv[1:4]
files = dict(a.split('=', 1) for a in sys.argv[4:])

t = nc.Dataset(topo_f)
ncol = t.dimensions['ncol_d'].size if 'ncol_d' in t.dimensions else t['lat_d'].size
rng = np.random.default_rng(0)
starts = np.sort(rng.choice(ncol - 100, 300, replace=False))
runs = [slice(s, s + 100) for s in starts]
cat = lambda f: np.concatenate([f(r) for r in runs])
lat = cat(lambda r: t['lat_d'][r].data).astype(float)
lon = cat(lambda r: t['lon_d'][r].data).astype(float) % 360
phis_t = cat(lambda r: t['PHIS_d'][r].data).astype(float)
n = lat.size

# --- ERA5 references at the nearest 0.25 deg point -------------------------
s = nc.Dataset(glob.glob(os.path.join(mldir, '*.sfc.nc'))[0])
a3 = nc.Dataset(glob.glob(os.path.join(mldir, '*.3d.nc'))[0])
ab = np.loadtxt(glob.glob(os.path.join(mldir, '*.ab.txt'))[0])   # half levels: a [Pa], b
ela = s['latitude'][:].data; elo = s['longitude'][:].data % 360
j = np.abs(ela[None, :] - lat[:, None]).argmin(1)
i = np.round((lon - elo[0]) / (elo[1] - elo[0])).astype(int) % elo.size
ps_e = np.exp(np.squeeze(s['lnsp'][:])[j, i].astype(float))
zs_e = np.squeeze(s['z'][:])[j, i].astype(float) / K.G
pi_e = ab[None, :, 0] + ab[None, :, 1] * ps_e[:, None]           # (n, 138)
pm_e = 0.5 * (pi_e[:, 1:] + pi_e[:, :-1])
Te = np.squeeze(a3['t'][:]); qe = np.squeeze(a3['q'][:])
T_e = Te[:, j, i].T.astype(float); q_e = qe[:, j, i].T.astype(float)
tqv_e = (q_e * np.diff(pi_e, axis=1)).sum(1) / K.G
dz_surf = phis_t / K.G - zs_e

# ERA5 analysed z500, bilinear at the GLL nodes
e = nc.Dataset(pl_f)
k500 = int(np.where(np.isclose(e['pressure_level'][:], 500))[0][0])
z5 = np.squeeze(e['z'][0, k500]).astype(np.float32)[:, :, None] / K.G
plat, plon = e['latitude'][:].data, e['longitude'][:].data
jj, ii, wy, wx = K.horiz_stencil(lat, lon, float(plat[0]), float(plat[1] - plat[0]), plat.size,
                                 float(plon[0]), float(plon[1] - plon[0]), plon.size, False)
z500_e = np.empty((n, 1)); K.interp_scalar(np.ascontiguousarray(z5), jj, ii, wy, wx, False, z500_e)
z500_e = z500_e[:, 0]

print(f'{n} columns sampled ({len(runs)} runs of 100) from {ncol} ')
print(f'model minus ERA5 surface height in sample: 1/50/99% = {np.percentile(dz_surf, [1, 50, 99]).round(0)} m')
rows = []
for label, f in files.items():
    d = nc.Dataset(f)
    def rd(v):
        x = d[v]
        if x.dimensions[0] == 'time':
            return cat(lambda r: x[0, r].data).astype(float)
        return cat(lambda r: x[r].data).astype(float)
    T, q, qc, qi, o3 = (rd(v) for v in ['T_mid', 'qv', 'qc', 'qi', 'o3_volume_mix_ratio'])
    ps, phis = rd('ps'), rd('phis')
    P0 = float(d['P0'][...]) if 'P0' in d.variables else 1e5
    pm = d['hyam'][:][None, :] * P0 + d['hybm'][:][None, :] * ps[:, None]
    pi = d['hyai'][:][None, :] * P0 + d['hybi'][:][None, :] * ps[:, None]
    neg = sum(int((x < 0).sum()) for x in (q, qc, qi, o3))
    rh = q / np.vectorize(K.qsat_liq)(T, pm)
    # z500 from PHIS_d (what EAMxx uses), not the file's phis
    Tv = T * (1 + K.ZVIR * q)
    phi_i = np.empty(pi.shape); phi_i[:, -1] = phis_t
    for k in range(pm.shape[1] - 1, -1, -1):
        phi_i[:, k] = phi_i[:, k + 1] + K.RD * Tv[:, k] * np.log(pi[:, k + 1] / pi[:, k])
    z500 = np.array([np.interp(np.log(5e4), np.log(pi[c]), phi_i[c]) for c in range(n)]) / K.G
    dz5 = z500 - z500_e
    ok = pi[:, -1] > 7e4
    big = ok & (np.abs(dz_surf) > 300)
    # upper-level T vs ERA5 model levels
    up = np.nonzero(d['hyam'][:] * P0 < 1000)[0]
    Ti = np.array([np.interp(np.log(pm[c, up]), np.log(pm_e[c]), T_e[c]) for c in range(n)])
    dTu = T[:, up] - Ti
    # conservation where surfaces agree
    flat = np.abs(dz_surf) < 20
    tqv = (q * np.diff(pi, axis=1)).sum(1) / K.G
    r = dict(label=label, neg=neg, rhmax=100 * rh.max(), nss=int((rh > 1.00001).sum()),
             phis_rms=np.sqrt(np.mean((phis - phis_t) ** 2)) / K.G, phis_max=np.abs(phis - phis_t).max() / K.G,
             z5=(dz5[ok].mean(), dz5[ok].std(), np.percentile(np.abs(dz5[ok]), 99), np.abs(dz5[ok]).max()),
             z5big=(dz5[big].mean(), dz5[big].std(), np.abs(dz5[big]).max(), int(big.sum())),
             Tup=(dTu[:, 0].mean(), dTu[:, 0].std(), dTu.mean(), dTu.std(), d['hyam'][up[-1]] * P0, up.size),
             tqv=((tqv - tqv_e)[flat].mean(), (tqv - tqv_e)[flat].std(), ((tqv - tqv_e) / tqv_e)[flat].mean() * 100),
             ps=((ps - ps_e)[flat].mean(), (ps - ps_e)[flat].std(), int(flat.sum())))
    rows.append(r)

print('\n| metric | ' + ' | '.join(r['label'] for r in rows) + ' |')
print('|---|' + '---|' * len(rows))
line = lambda name, fmt: print(f'| {name} | ' + ' | '.join(fmt(r) for r in rows) + ' |')
line('negative q/qc/qi/O3 values', lambda r: f"{r['neg']}")
line('max RH over liquid (EAMxx formula)', lambda r: f"{r['rhmax']:.2f} %")
line('points with RH > 100 %', lambda r: f"{r['nss']}")
line('phis − PHIS_d, rms / max', lambda r: f"{r['phis_rms']:.0f} / {r['phis_max']:.0f} m")
line('z500 error, mean ± std (ps > 700 hPa)', lambda r: f"{r['z5'][0]:+.2f} ± {r['z5'][1]:.2f} m")
line('z500 error, 99th pct / max abs', lambda r: f"{r['z5'][2]:.1f} / {r['z5'][3]:.1f} m")
line(f"z500 error where surfaces differ > 300 m, mean ± std (n={rows[0]['z5big'][3]})", lambda r: f"{r['z5big'][0]:+.2f} ± {r['z5big'][1]:.2f} m")
line('z500 error where surfaces differ > 300 m, max abs', lambda r: f"{r['z5big'][2]:.1f} m")
line('T − ERA5 at top level, mean ± std', lambda r: f"{r['Tup'][0]:+.2f} ± {r['Tup'][1]:.2f} K")
line("T − ERA5 over all levels above 10 hPa, mean ± std", lambda r: f"{r['Tup'][2]:+.2f} ± {r['Tup'][3]:.2f} K")
line(f"column water vapour − ERA5, |dz| < 20 m (n={rows[0]['ps'][2]})", lambda r: f"{r['tqv'][0]:+.3f} ± {r['tqv'][1]:.3f} kg/m² ({r['tqv'][2]:+.2f} %)")
line('ps − ERA5, |dz| < 20 m', lambda r: f"{r['ps'][0]:+.1f} ± {r['ps'][1]:.1f} Pa")
