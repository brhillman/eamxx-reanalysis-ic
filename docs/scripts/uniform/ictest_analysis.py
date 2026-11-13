"""Analyse the uniform-grid EAMxx IC test runs (run_ictest_pm.sh): how the model
responds to each IC and how the forecasts compare with ERA5.

Usage:
    python ictest_analysis.py OUT_PREFIX TOPO_PG2 ERA5_VERIF_DIR LABEL=RUNDIR [LABEL=RUNDIR ...]

RUNDIR holds <case>.eamxx.{hstep,h2d,h3d}.*.nc. TOPO_PG2 has PHIS on the
physics (pg2) columns, for z500. ERA5_VERIF_DIR from request_era5_verif.py.

Output (markdown on stdout, figure OUT_PREFIX.png):
  1. Initial adjustment, from per-step output (physics step):
       mean |dps/dt| (Pa/h), global and over terrain above 1500 m: gravity-wave
       noise from imbalance in the IC; precipitation in the first steps.
  2. Global means (area-weighted) of precipitation, TQV, LWP, IWP against ERA5.
  3. Forecast error against ERA5 every 6 h: RMSE of sea-level pressure, T850,
     z500 (hydrostatic from PHIS, ps, T, qv), 850 hPa vector wind, TQV, global.
  4. RMS difference of each run from the first run (how long IC differences
     persist compared with the forecast error).
"""
import os, sys, glob
import numpy as np, netCDF4 as nc
from scipy.interpolate import RegularGridInterpolator
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

RD, G, ZVIR = 287.042, 9.80616, 461.505 / 287.042 - 1
out, topo_f, vdir = sys.argv[1:4]
runs = dict(a.split('=', 1) for a in sys.argv[4:])
labels = list(runs)


def stream(rundir, key, vars_):
    fs = sorted(glob.glob(os.path.join(rundir, f'*.eamxx.{key}.*.nc')))
    d0 = nc.Dataset(fs[0])
    data = {v: [] for v in vars_}; t = []
    for f in fs:
        d = nc.Dataset(f)
        t.append(np.asarray(d['time'][:], float))
        for v in vars_:
            data[v].append(np.asarray(d[v][:], float))
    t = np.concatenate(t); o = np.argsort(t)
    res = {v: np.concatenate(x)[o] for v, x in data.items()}
    _, u = np.unique(t[o], return_index=True)          # drop duplicate times at file joins
    res = {v: x[u] for v, x in res.items()}
    return t[o][u], res, d0


# ---- grid and weights --------------------------------------------------------
t0, h, d0 = stream(runs[labels[0]], 'h2d', ['ps'])
lat = np.asarray(d0['lat'][:], float); lon = np.asarray(d0['lon'][:], float) % 360
area = np.asarray(d0['area'][:], float); wgt = area / area.sum()
phis = np.asarray(nc.Dataset(topo_f)['PHIS'][:], float)
assert phis.size == lat.size, (phis.size, lat.size)
high = phis / G > 1500
gm = lambda x, m=None: (np.sum(x * wgt, -1) if m is None else np.sum(x[..., m] * wgt[m], -1) / wgt[m].sum())

# ---- ERA5 verification on the columns ---------------------------------------
def era5_interp(f, var, level=None):
    e = nc.Dataset(f)
    la, lo = e['latitude'][:].data, e['longitude'][:].data % 360
    tv = e['valid_time']; times = nc.num2date(tv[:], tv.units)
    x = e[var]
    if level is not None:
        k = int(np.where(np.isclose(e['pressure_level'][:], level))[0][0])
    res = {}
    for i, tt in enumerate(times):
        fld = np.asarray(x[i, k] if level is not None else x[i], float)
        ip = RegularGridInterpolator((la[::-1], np.r_[lo, 360.0]), np.c_[fld, fld[:, :1]][::-1])
        res[(tt.day, tt.hour)] = ip(np.c_[lat, lon])
    return res

pl, sfc, tpf = (os.path.join(vdir, f'ERA5.verif.{k}.nc') for k in ('pl', 'sfc', 'tp'))
E = {'msl': era5_interp(sfc, 'msl'), 'tcwv': era5_interp(sfc, 'tcwv'), 'tclw': era5_interp(sfc, 'tclw'),
     'tciw': era5_interp(sfc, 'tciw'), 't850': era5_interp(pl, 't', 850), 'u850': era5_interp(pl, 'u', 850),
     'v850': era5_interp(pl, 'v', 850), 'z500': era5_interp(pl, 'z', 500)}
tp = era5_interp(tpf, 'tp')        # m over the hour ending at the valid time
start_day, start_hour = 19, 18
key = lambda tdays: ((start_day * 24 + start_hour + int(round(tdays * 24))) // 24,
                     (start_day * 24 + start_hour + int(round(tdays * 24))) % 24)

# ---- per run -----------------------------------------------------------------
R = {}
for lab in labels:
    rd = runs[lab]
    ts, s, _ = stream(rd, 'hstep', ['ps', 'precip_total_surf_mass_flux'])
    t2, h2, _ = stream(rd, 'h2d', ['ps', 'SeaLevelPressure', 'precip_total_surf_mass_flux', 'VapWaterPath',
                                   'LiqWaterPath', 'IceWaterPath', 'T_mid_at_850hPa'])
    t3, h3, d3 = stream(rd, 'h3d', ['ps', 'T_mid', 'qv', 'U', 'V'])
    dt_h = np.diff(ts) * 24
    dpsdt = np.abs(np.diff(s['ps'], axis=0)) / dt_h[:, None]
    r = dict(ts=ts[1:], dpsdt=gm(dpsdt), dpsdt_hi=gm(dpsdt, high),
             pr_step=gm(s['precip_total_surf_mass_flux']) * 86400e3,   # m/s -> mm/day
             t2=t2, tqv=gm(h2['VapWaterPath']), lwp=gm(h2['LiqWaterPath']), iwp=gm(h2['IceWaterPath']),
             pr=gm(h2['precip_total_surf_mass_flux']) * 86400e3, h2=h2, t3=t3)
    # z500 and 850 hPa wind from 3D state
    P0 = float(d3['P0'][...]); hyam = d3['hyam'][:].astype(float); hybm = d3['hybm'][:].astype(float)
    vf = nc.Dataset(os.environ.get('VERT', '/global/cfs/cdirs/e3sm/inputdata/atm/scream/init/vertical_coordinates_L128v4_c20260820.nc'))
    hyai, hybi = vf['hyai'][:].astype(float), vf['hybi'][:].astype(float)
    z5, u8, v8 = [], [], []
    for i in range(t3.size):
        ps = h3['ps'][i]; T = h3['T_mid'][i]; q = h3['qv'][i]
        pi = hyai[None, :] * P0 + hybi[None, :] * ps[:, None]
        pm = hyam[None, :] * P0 + hybm[None, :] * ps[:, None]
        dphi = RD * T * (1 + ZVIR * q) * np.log(pi[:, 1:] / pi[:, :-1])
        phi_i = phis[:, None] + np.concatenate([np.cumsum(dphi[:, ::-1], 1)[:, ::-1], np.zeros((ps.size, 1))], 1)
        lp = np.log(pi); lm = np.log(pm)
        z5.append(np.array([np.interp(np.log(5e4), lp[c], phi_i[c]) for c in range(ps.size)]) / G)
        u8.append(np.array([np.interp(np.log(8.5e4), lm[c], h3['U'][i, c]) for c in range(ps.size)]))
        v8.append(np.array([np.interp(np.log(8.5e4), lm[c], h3['V'][i, c]) for c in range(ps.size)]))
    r['z500'], r['u850'], r['v850'] = np.array(z5), np.array(u8), np.array(v8)
    r['ps3'] = h3['ps']
    R[lab] = r

# ---- errors against ERA5 ------------------------------------------------------
def rmse(x, y, m=None):
    d2 = (x - y) ** 2
    return np.sqrt(gm(d2) if m is None else gm(d2, m))

times6 = [t for t in R[labels[0]]['t3']]
errs = {lab: {k: [] for k in ('slp', 't850', 'z500', 'wind850', 'tqv')} for lab in labels}
for lab in labels:
    r = R[lab]
    for i, t in enumerate(r['t3']):
        k = key(t)
        j = int(np.argmin(np.abs(r['t2'] - t)))
        ok850 = r['ps3'][i] > 9e4
        errs[lab]['slp'].append(rmse(r['h2']['SeaLevelPressure'][j], E['msl'][k]) / 100)
        errs[lab]['t850'].append(rmse(r['h2']['T_mid_at_850hPa'][j], E['t850'][k], ok850))
        errs[lab]['z500'].append(rmse(r['z500'][i], E['z500'][k] / G))
        errs[lab]['wind850'].append(np.sqrt(gm((r['u850'][i] - E['u850'][k]) ** 2 + (r['v850'][i] - E['v850'][k]) ** 2, ok850)))
        errs[lab]['tqv'].append(rmse(r['h2']['VapWaterPath'][j], E['tcwv'][k]))

hours6 = np.round(np.array(times6) * 24).astype(int)
print('## Initial adjustment\n')
print('Mean |dps/dt| between physics steps (Pa/h), global / over terrain above 1500 m')
print('\n| run | first step | mean, hours 0–3 | mean, hours 3–24 | mean, day 3 |')
print('|---|---|---|---|---|')
for lab in labels:
    r = R[lab]; th = r['ts'] * 24
    f = lambda a, b, x: x[(th > a) & (th <= b)].mean()
    print(f"| {lab} | {r['dpsdt'][0]:.0f} / {r['dpsdt_hi'][0]:.0f} | {f(0, 3, r['dpsdt']):.0f} / {f(0, 3, r['dpsdt_hi']):.0f} "
          f"| {f(3, 24, r['dpsdt']):.0f} / {f(3, 24, r['dpsdt_hi']):.0f} | {f(48, 72, r['dpsdt']):.0f} / {f(48, 72, r['dpsdt_hi']):.0f} |")
print('\nGlobal-mean precipitation (mm/day): first physics step (the t=0 record is a fill value), hours 0–6, day 1, day 3; ERA5 for the same periods')
era5_pr = lambda a, b: np.mean([gm(tp[key(hh / 24)]) * 1000 * 24 for hh in range(a + 1, b + 1)])
print('\n| run | first step | hours 0–6 | day 1 | day 3 |')
print('|---|---|---|---|---|')
for lab in labels:
    r = R[lab]; th = r['ts'] * 24; t2h = r['t2'] * 24
    print(f"| {lab} | {r['pr_step'][1]:.2f} | {r['pr'][(t2h > 0) & (t2h <= 6)].mean():.2f} | "
          f"{r['pr'][(t2h > 0) & (t2h <= 24)].mean():.2f} | {r['pr'][(t2h > 48) & (t2h <= 72)].mean():.2f} |")
print(f"| ERA5 | – | {era5_pr(0, 6):.2f} | {era5_pr(0, 24):.2f} | {era5_pr(48, 72):.2f} |")
print('\nGlobal means at 0 h / 6 h / 24 h / 72 h; ERA5 analysis at the same times')
print('\n| run | TQV (kg/m²) | LWP (g/m²) | IWP (g/m²) |')
print('|---|---|---|---|')
pick = lambda r, x, hh: x[int(np.argmin(np.abs(r['t2'] * 24 - hh)))]
for lab in labels:
    r = R[lab]
    print(f"| {lab} | " + ' / '.join(f"{pick(r, r['tqv'], hh):.2f}" for hh in (0, 6, 24, 72)) + ' | '
          + ' / '.join(f"{pick(r, r['lwp'], hh) * 1e3:.1f}" for hh in (0, 6, 24, 72)) + ' | '
          + ' / '.join(f"{pick(r, r['iwp'], hh) * 1e3:.1f}" for hh in (0, 6, 24, 72)) + ' |')
ek = lambda v, hh: gm(E[v][key(hh / 24)])
print('| ERA5 | ' + ' / '.join(f'{ek("tcwv", hh):.2f}' for hh in (0, 6, 24, 72)) + ' | '
      + ' / '.join(f'{ek("tclw", hh) * 1e3:.1f}' for hh in (0, 6, 24, 72)) + ' | '
      + ' / '.join(f'{ek("tciw", hh) * 1e3:.1f}' for hh in (0, 6, 24, 72)) + ' |')

print('\n## Forecast error against ERA5 (global RMSE)\n')
for v, unit in (('slp', 'hPa'), ('z500', 'm'), ('t850', 'K'), ('wind850', 'm/s'), ('tqv', 'kg/m²')):
    print(f'\n{v} ({unit}), by forecast hour: ' + ', '.join(str(x) for x in hours6))
    print('\n| run | ' + ' | '.join(f'{x} h' for x in hours6) + ' |')
    print('|---|' + '---|' * len(hours6))
    for lab in labels:
        print(f'| {lab} | ' + ' | '.join(f'{x:.2f}' for x in errs[lab][v]) + ' |')

print(f'\n## RMS difference from "{labels[0]}" (same fields)\n')
print('| run | SLP 6 h / 24 h / 72 h (hPa) | z500 6 h / 24 h / 72 h (m) | T850 6 h / 24 h / 72 h (K) |')
print('|---|---|---|---|')
r0 = R[labels[0]]
for lab in labels[1:]:
    r = R[lab]; cells = []
    for v in ('slp', 'z500', 't850'):
        vals = []
        for hh in (6, 24, 72):
            i3 = int(np.argmin(np.abs(r['t3'] * 24 - hh))); j2 = int(np.argmin(np.abs(r['t2'] * 24 - hh)))
            if v == 'slp':
                vals.append(rmse(r['h2']['SeaLevelPressure'][j2], r0['h2']['SeaLevelPressure'][j2]) / 100)
            elif v == 'z500':
                vals.append(rmse(r['z500'][i3], r0['z500'][i3]))
            else:
                vals.append(rmse(r['h2']['T_mid_at_850hPa'][j2], r0['h2']['T_mid_at_850hPa'][j2], r0['ps3'][i3] > 9e4))
        cells.append(' / '.join(f'{x:.2f}' for x in vals))
    print(f'| {lab} | ' + ' | '.join(cells) + ' |')

# ---- figure ---------------------------------------------------------------------
fig, ax = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
for lab in labels:
    r = R[lab]
    ax[0, 0].plot(r['ts'] * 24, r['dpsdt'], label=lab)
    ax[0, 1].plot(r['ts'] * 24, r['dpsdt_hi'], label=lab)
    ok = r['t2'] > 0                                  # t=0 precipitation is a fill value
    ax[0, 2].plot(r['t2'][ok] * 24, r['pr'][ok], label=lab)
    ax[1, 0].plot(hours6, errs[lab]['z500'], 'o-', label=lab)
    ax[1, 1].plot(hours6, errs[lab]['slp'], 'o-', label=lab)
    ax[1, 2].plot(r['t2'] * 24, r['tqv'], label=lab)
ax[0, 2].plot(np.arange(1, 73), [gm(tp[key(hh / 24)]) * 1000 * 24 for hh in range(1, 73)], 'k--', label='ERA5')
ax[1, 2].plot(hours6, [gm(E['tcwv'][key(hh / 24)]) for hh in hours6], 'ko', label='ERA5')
for a_, t_ in zip(ax.flat, ['mean |dps/dt|, global (Pa/h)', 'mean |dps/dt|, terrain > 1500 m (Pa/h)',
                            'global-mean precipitation (mm/day)', 'z500 RMSE vs ERA5 (m)', 'SLP RMSE vs ERA5 (hPa)',
                            'global-mean TQV (kg/m²)']):
    a_.set_title(t_, fontsize=9); a_.set_xlabel('forecast hour')
ax[0, 0].set_xlim(0, 24); ax[0, 1].set_xlim(0, 24)
ax[0, 0].set_yscale('log'); ax[0, 1].set_yscale('log')
ax[0, 2].legend(fontsize=7)
fig.savefig(f'{out}.png', dpi=90)
print(f'\nwrote {out}.png')
