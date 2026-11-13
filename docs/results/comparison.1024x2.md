30000 columns sampled (300 runs of 100) from 71174684 
model minus ERA5 surface height in sample: 1/50/99% = [-345.   -0.  395.] m

| metric | HICCUP conservative (20260918, in use) | HICCUP bilinear (20261113) | new tool, pressure-matched winds | new tool (20261113) |
|---|---|---|---|---|
| negative q/qc/qi/O3 values | 0 | 0 | 0 | 0 |
| max RH over liquid (EAMxx formula) | 101.06 % | 101.05 % | 100.00 % | 100.00 % |
| points with RH > 100 % | 5983 | 6633 | 0 | 0 |
| phis − PHIS_d, rms / max | 152 / 2179 m | 107 / 1419 m | 0 / 0 m | 0 / 0 m |
| z500 error, mean ± std (ps > 700 hPa) | -0.27 ± 3.93 m | -0.15 ± 1.88 m | -0.39 ± 0.30 m | -0.39 ± 0.30 m |
| z500 error, 99th pct / max abs | 13.0 / 31.8 m | 5.0 / 49.3 m | 1.2 / 7.3 m | 1.2 / 7.3 m |
| z500 error where surfaces differ > 300 m, mean ± std (n=618) | +2.61 ± 5.24 m | +3.77 ± 8.47 m | -0.54 ± 0.84 m | -0.54 ± 0.84 m |
| z500 error where surfaces differ > 300 m, max abs | 31.8 m | 49.3 m | 6.6 m | 6.6 m |
| T − ERA5 at top level, mean ± std | +6.20 ± 5.21 K | +6.28 ± 5.16 K | +0.00 ± 0.08 K | +0.00 ± 0.08 K |
| T − ERA5 over all levels above 10 hPa, mean ± std | +0.24 ± 2.07 K | +0.28 ± 2.03 K | +0.02 ± 0.30 K | +0.02 ± 0.30 K |
| column water vapour − ERA5, |dz| < 20 m (n=22492) | -0.049 ± 0.823 kg/m² (-0.36 %) | +0.053 ± 0.309 kg/m² (+0.18 %) | -0.001 ± 0.297 kg/m² (+0.01 %) | -0.001 ± 0.297 kg/m² (+0.01 %) |
| ps − ERA5, |dz| < 20 m | -3.1 ± 66.3 Pa | +0.8 ± 62.3 Pa | +0.6 ± 61.9 Pa | +0.6 ± 61.9 Pa |
68536 columns in box (42.0, 44.0, 252.0, 254.5); model minus ERA5 surface 5/50/95%: [-187.  -12.  296.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.07 | 5.3 | 5.9 | 4.8 |
| HICCUP conservative (20260918, in use) | 0.047 | 0.0063 | 0.055 | +0.45 | 5.6 | 6.5 | 7.7 |
| HICCUP bilinear (20261113) | 0.039 | 0.0045 | 0.044 | +0.53 | 5.7 | 7.0 | 8.2 |
| new tool, pressure-matched winds | 0.048 | 0.0066 | 0.079 | +0.58 | 5.3 | 6.5 | 8.5 |
| new tool (20261113) | 0.048 | 0.0066 | 0.005 | -0.05 | 5.4 | 6.1 | 4.9 |

wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wyoming_wind.1024x2.png
