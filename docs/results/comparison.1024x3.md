30000 columns sampled (300 runs of 100) from 117157709 
model minus ERA5 surface height in sample: 1/50/99% = [-393.   -0.  523.] m

| metric | HICCUP conservative (20260918, in use) | HICCUP bilinear (20261113) | new tool (20261113) |
|---|---|---|---|
| negative q/qc/qi/O3 values | 0 | 0 | 0 |
| max RH over liquid (EAMxx formula) | 101.03 % | 101.02 % | 100.00 % |
| points with RH > 100 % | 20730 | 19096 | 0 |
| phis − PHIS_d, rms / max | 183 / 2086 m | 124 / 1492 m | 0 / 0 m |
| z500 error, mean ± std (ps > 700 hPa) | +0.59 ± 6.22 m | +0.19 ± 3.13 m | -0.37 ± 0.44 m |
| z500 error, 99th pct / max abs | 16.0 / 94.9 m | 11.0 / 70.9 m | 1.7 / 10.4 m |
| z500 error where surfaces differ > 300 m, mean ± std (n=1524) | +4.80 ± 14.75 m | +3.33 ± 6.94 m | -0.53 ± 0.80 m |
| z500 error where surfaces differ > 300 m, max abs | 94.9 m | 40.0 m | 6.9 m |
| T − ERA5 at top level, mean ± std | +7.54 ± 4.39 K | +7.60 ± 4.38 K | -0.00 ± 0.06 K |
| T − ERA5 over all levels above 10 hPa, mean ± std | +0.28 ± 2.13 K | +0.29 ± 2.11 K | +0.03 ± 0.30 K |
| column water vapour − ERA5, |dz| < 20 m (n=17965) | +0.086 ± 0.682 kg/m² (+0.39 %) | +0.067 ± 0.283 kg/m² (+0.26 %) | +0.009 ± 0.267 kg/m² (+0.03 %) |
| ps − ERA5, |dz| < 20 m | -7.9 ± 84.7 Pa | -3.1 ± 80.3 Pa | -3.7 ± 79.7 Pa |
274106 columns in box (42.0, 44.0, 252.0, 254.5); model minus ERA5 surface 5/50/95%: [-189.  -12.  300.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.07 | 5.3 | 5.9 | 4.8 |
| HICCUP conservative (20260918, in use) | 0.032 | 0.0039 | 0.035 | +0.45 | 5.6 | 6.5 | 7.8 |
| HICCUP bilinear (20261113) | 0.027 | 0.0030 | 0.030 | +0.53 | 5.7 | 7.0 | 8.2 |
| new tool (20261113) | 0.033 | 0.0044 | 0.003 | -0.05 | 5.4 | 6.1 | 5.0 |

wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wyoming_wind.1024x3.png
wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wyoming_imprint.1024x3.png
