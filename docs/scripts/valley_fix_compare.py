"""Before/after comparison of the deep-valley wind blending fix (blending depth
max(D, 2*(psm - ps)) instead of a fixed D = 150 hPa).

Usage:
    python valley_fix_compare.py ERA5_ML_DIR OUT_PREFIX LABEL BEFORE.nc AFTER.nc
    (pressure-level ICs: set SP_FILE to the ERA5 surface file with sp)

1. Identity: on 300 random runs of 100 columns, every variable is bit-identical
   except U, V in columns where the model surface is more than D/2 below the
   source surface (dp = ps_model - ps_ERA5 > 75 hPa), the only columns the fix
   can touch. dp uses the ERA5 surface pressure exactly as make_ic.py
   interpolates it (bicubic on ln ps).
2. Candidate columns (dp > 70 hPa),
   read in contiguous runs: which changed, by how much, and on which levels.
3. Wind profile in the blending layer (pm > psm - max(D, 2 dp)), before and after:
     - distinct speed values per level (a folded lookup gives nearly constant wind)
     - monotonicity of the lookup pressure
     - RMS difference from the terrain-following target: the ERA5 wind
       (nearest point) at the same sigma, p/ps_ERA5 = pm/psm, i.e. about the
       same height above its own surface. Levels in the lowest 150 hPa.
4. Figure: speed profiles of the deepest columns against pressure above the
   model surface: before, after, pressure matching (ERA5 at the same pressure,
   held constant below its lowest level), and ERA5 at the same sigma.
"""
import os, sys, glob
import numpy as np, netCDF4 as nc
from scipy.interpolate import RegularGridInterpolator
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

mldir, prefix, label, fb, fa = sys.argv[1:6]
D = 15000.0
s = nc.Dataset(glob.glob(os.path.join(mldir, '*.sfc.nc'))[0])
a3 = nc.Dataset(glob.glob(os.path.join(mldir, '*.3d.nc'))[0])
ab = np.loadtxt(glob.glob(os.path.join(mldir, '*.ab.txt'))[0])
la = s['latitude'][:].data; lo = s['longitude'][:].data % 360
lnsp = np.squeeze(s['lnsp'][:]).astype(float)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import kernels as K
# SP_FILE: for pressure-level sources, the ERA5 surface file with sp (what make_ic.py reads then)
if os.environ.get('SP_FILE'):
    sp_ds = nc.Dataset(os.environ['SP_FILE'])
    lnps32 = np.ascontiguousarray(np.log(np.squeeze(sp_ds['sp'][:]).astype(np.float64)).astype(np.float32)[:, :, None])
    la_raw = sp_ds['latitude'][:].data.astype(np.float64); lo_raw = sp_ds['longitude'][:].data.astype(np.float64)
else:
    lnps32 = np.ascontiguousarray(lnsp.astype(np.float32)[:, :, None])
    la_raw = s['latitude'][:].data.astype(np.float64); lo_raw = s['longitude'][:].data.astype(np.float64)


def ps_source(lat, lon):
    """ERA5 surface pressure at the nodes exactly as make_ic.py computes it
    (bicubic stencil on ln ps), so the 75 hPa threshold can be tested exactly."""
    lat = np.ascontiguousarray(lat, np.float64); lon = np.ascontiguousarray(lon, np.float64)
    jj, ii, wy, wx = K.horiz_stencil(lat, lon, float(la_raw[0]), float(la_raw[1] - la_raw[0]), la_raw.size,
                                     float(lo_raw[0]), float(lo_raw[1] - lo_raw[0]), lo_raw.size, True)
    out = np.empty((lat.size, 1)); K.interp_scalar(lnps32, jj, ii, wy, wx, False, out)
    return np.exp(out[:, 0])
B, A = nc.Dataset(fb), nc.Dataset(fa)
n = A['ps'].shape[-1]
P0 = float(A['P0'][...]) if 'P0' in A.variables else 1e5
hyam, hybm = A['hyam'][:].astype(float), A['hybm'][:].astype(float)
nlev = hyam.size

# ---- 1. identity on random columns ------------------------------------------
rng = np.random.default_rng(1)
starts = np.sort(rng.choice(n - 100, 300, replace=False)) if n > 100_000 else [0]
width = 100 if n > 100_000 else n
skip = {'time', 'time_bnds', 'date', 'datesec', 'hyam', 'hybm', 'hyai', 'hybi', 'P0', 'lev', 'ilev'}
bad = {}
for v in A.variables:
    if v in skip or 'ncol' not in A[v].dimensions:
        continue
    for st in starts:
        sl = [slice(None)] * A[v].ndim
        sl[A[v].dimensions.index('ncol')] = slice(st, st + width)
        x, y = np.asarray(A[v][tuple(sl)]), np.asarray(B[v][tuple(sl)])
        if not np.array_equal(x, y):
            if v in ('U', 'V'):
                ps = np.asarray(A['ps'][0, st:st + width], float)
                lat = np.asarray(A['lat'][st:st + width], float); lon = np.asarray(A['lon'][st:st + width], float) % 360
                dp = ps - ps_source(lat, lon)
                diffcol = np.any(x != y, axis=-1)[0]
                if np.any(diffcol & (dp <= 7500)):
                    bad[v] = bad.get(v, 0) + int((diffcol & (dp <= 7500)).sum())
            else:
                bad[v] = bad.get(v, 0) + 1
print(f'## {label}\n')
print(f'Identity check on {len(starts) * width:,} random columns: '
      + ('all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)' if not bad else f'UNEXPECTED differences: {bad}'))

# ---- 2. candidate columns ---------------------------------------------------
cand = []
for c0 in range(0, n, 20_000_000):
    c1 = min(n, c0 + 20_000_000)
    ps = np.asarray(A['ps'][0, c0:c1], float)
    lat = np.asarray(A['lat'][c0:c1], float); lon = np.asarray(A['lon'][c0:c1], float) % 360
    pe = ps_source(lat, lon)
    cand.append(c0 + np.nonzero(ps - pe > 7000)[0])
cand = np.concatenate(cand)
print(f'columns with dp > 70 hPa (candidates): {cand.size:,} of {n:,}')
if cand.size == 0:
    sys.exit()
brk = np.nonzero(np.diff(cand) > 2000)[0]
runs = np.split(cand, brk + 1)
k0 = nlev - 80          # lowest 80 levels hold every blending layer (<= ~2*200 hPa)

rows = []
ue_v = a3['u']; ve_v = a3['v']
elat = s['latitude'][:].data; elon = s['longitude'][:].data % 360
for r in runs:
    i0, i1 = r[0], r[-1] + 1
    sel = r - i0
    psm = np.asarray(A['ps'][0, i0:i1], float)[sel]
    lat = np.asarray(A['lat'][i0:i1], float)[sel]; lon = np.asarray(A['lon'][i0:i1], float)[sel] % 360
    ub, vb = (np.asarray(B[x][0, i0:i1, k0:], float)[sel] for x in ('U', 'V'))
    ua, va = (np.asarray(A[x][0, i0:i1, k0:], float)[sel] for x in ('U', 'V'))
    pe = ps_source(lat, lon)
    for j in range(sel.size):
        rows.append((r[j], lat[j], lon[j], psm[j], pe[j], ub[j], vb[j], ua[j], va[j]))

idx = np.array([x[0] for x in rows]); lat = np.array([x[1] for x in rows]); lon = np.array([x[2] for x in rows])
psm = np.array([x[3] for x in rows]); pse = np.array([x[4] for x in rows])
ub = np.array([x[5] for x in rows]); vb = np.array([x[6] for x in rows])
ua = np.array([x[7] for x in rows]); va = np.array([x[8] for x in rows])
dp = psm - pse
pm = hyam[None, k0:] * P0 + hybm[None, k0:] * psm[:, None]
dU = np.maximum(np.abs(ua - ub), np.abs(va - vb)).max(1)
changed = dU > 0
print(f'columns changed: {changed.sum():,}; smallest dp among them {dp[changed].min() / 100:.2f} hPa; '
      f'columns with dp > 75 hPa unchanged: {(~changed & (dp > 7500)).sum():,}')

# ERA5 nearest-point profile for the target and the figure
jj = np.abs(elat[None, :] - lat[:, None]).argmin(1)
ii = np.round((lon - elon[0]) / (elon[1] - elon[0])).astype(int) % elon.size
U3 = np.squeeze(np.asarray(ue_v[:])); ue = U3[:, jj, ii].T.astype(float); del U3
V3 = np.squeeze(np.asarray(ve_v[:])); ve = V3[:, jj, ii].T.astype(float); del V3
pse_n = np.exp(lnsp[jj, ii])                      # nearest-point ERA5 surface pressure, for sigma
pfe = 0.5 * (ab[None, 1:, 0] + ab[None, :-1, 0] + (ab[None, 1:, 1] + ab[None, :-1, 1]) * pse_n[:, None])


def at_p(pp, prof, pfull):
    """ERA5 profile at pressures pp, linear in ln p, held constant outside."""
    return np.interp(np.log(pp), np.log(pfull), prof)


def metrics(u, v, m):
    depth = max(D, 2 * dp[m]) if dp[m] > 0 else D
    lay = pm[m] > psm[m] - depth
    sp = np.hypot(u[m], v[m])[lay]
    distinct = len(np.unique(np.round(sp, 4)))
    low = pm[m] > psm[m] - D                    # lowest 150 hPa: compare with ERA5 at same sigma
    sig = pm[m][low] / psm[m]
    ut, vt = at_p(sig * pse_n[m], ue[m], pfe[m]), at_p(sig * pse_n[m], ve[m], pfe[m])
    rms = np.sqrt(np.mean((u[m][low] - ut) ** 2 + (v[m][low] - vt) ** 2))
    return distinct, lay.sum(), sp.max() - sp.min(), rms


def summarise(sel, name):
    if not np.any(sel):
        return
    mb = np.array([metrics(ub, vb, m) for m in np.nonzero(sel)[0]])
    ma = np.array([metrics(ua, va, m) for m in np.nonzero(sel)[0]])
    print(f'| {name} | {sel.sum():,} | {np.mean(mb[:, 0] / mb[:, 1]):.2f} → {np.mean(ma[:, 0] / ma[:, 1]):.2f} '
          f'| {np.median(mb[:, 2]):.2f} → {np.median(ma[:, 2]):.2f} | {np.mean(mb[:, 3]):.2f} → {np.mean(ma[:, 3]):.2f} '
          f'| {np.mean(dU[sel]):.2f} / {dU[sel].max():.2f} |')


fold = dp > D * pse / psm
print('\nBlending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)\n')
print('| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \\|ΔU\\|,\\|ΔV\\| per column, mean / max (m/s) |')
print('|---|---|---|---|---|---|')
summarise(changed & (dp <= 10000), 'dp ≤ 100 hPa')
summarise(changed & (dp > 10000) & ~fold, 'dp > 100 hPa, not folded')
summarise(changed & fold, 'folded before (dp > 150·ps_e/ps)')
boxes = {'Sierra Nevada': (36, 39.5, 239.5, 242), 'Coast Mountains / Cascades': (45, 51, 235, 240),
         'Wyoming': (42, 44, 252, 254.5), 'Himalaya / Karakoram': (25, 40, 70, 100), 'Andes': (-40, 12, 280, 295)}
print('\n| region | columns changed | of which folded before | mean / max of max \\|ΔU\\|,\\|ΔV\\| (m/s) |')
print('|---|---|---|---|')
for name, (y0, y1, x0, x1) in boxes.items():
    inb = changed & (lat > y0) & (lat < y1) & (lon > x0) & (lon < x1)
    if inb.any():
        print(f'| {name} | {inb.sum():,} | {(inb & fold).sum():,} | {dU[inb].mean():.2f} / {dU[inb].max():.2f} |')
    else:
        print(f'| {name} | 0 | 0 | – |')
lev_changed = np.any((np.abs(ua - ub) > 0) | (np.abs(va - vb) > 0), axis=0)
print(f'\nhighest changed level: {k0 + np.nonzero(lev_changed)[0].min() if lev_changed.any() else "none"} of {nlev} '
      f'(lowest is {nlev - 1}); deepest dp {dp.max() / 100:.0f} hPa at {lat[dp.argmax()]:.2f}, {lon[dp.argmax()]:.2f}')

# ---- 4. figure ----------------------------------------------------------------
order = np.argsort(-dp)[:3]
fig, ax = plt.subplots(1, len(order), figsize=(4.2 * len(order), 4.6), constrained_layout=True, squeeze=False)
for a_, m in zip(ax[0], order):
    depth = max(D, 2 * dp[m])
    lay = pm[m] > psm[m] - depth - 5000
    y = (psm[m] - pm[m][lay]) / 100
    a_.plot(np.hypot(ub[m], vb[m])[lay], y, 'C3-o', ms=3, label='before (fixed 150 hPa)')
    a_.plot(np.hypot(ua[m], va[m])[lay], y, 'C0-o', ms=3, label='after (max(150, 2·dp))')
    pmatch = np.hypot(at_p(pm[m][lay], ue[m], pfe[m]), at_p(pm[m][lay], ve[m], pfe[m]))
    a_.plot(pmatch, y, 'k:', label='pressure matching')
    sig = pm[m][lay] / psm[m]
    a_.plot(np.hypot(at_p(sig * pse_n[m], ue[m], pfe[m]), at_p(sig * pse_n[m], ve[m], pfe[m])), y, 'C2--',
            label='ERA5 at same sigma (target)')
    a_.axhline(D / 100, color='0.6', lw=0.6); a_.axhline(depth / 100, color='C0', lw=0.6)
    a_.set_title(f'{lat[m]:.2f}N {lon[m]:.2f}E, dp = {dp[m] / 100:.0f} hPa', fontsize=9)
    a_.set_xlabel('wind speed (m/s)'); a_.set_ylabel('pressure above model surface (hPa)')
ax[0, 0].legend(fontsize=7)
fig.suptitle(f'{label}: deepest columns below the ERA5 surface', fontsize=10)
fig.savefig(f'{prefix}.png', dpi=100)
print(f'\nwrote {prefix}.png')
