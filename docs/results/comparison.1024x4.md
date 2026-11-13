30000 columns sampled (300 runs of 100) from 299999162 
model minus ERA5 surface height in sample: 1/50/99% = [-395.   -0.  447.] m

| metric | HICCUP conservative (20260918, in use) | HICCUP bilinear (20261113) | new tool (20261113) |
|---|---|---|---|
| negative q/qc/qi/O3 values | 0 | 0 | 0 |
| max RH over liquid (EAMxx formula) | 101.16 % | 101.00 % | 100.00 % |
| points with RH > 100 % | 22524 | 16361 | 0 |
| phis − PHIS_d, rms / max | 154 / 1175 m | 118 / 945 m | 0 / 0 m |
| z500 error, mean ± std (ps > 700 hPa) | +0.84 ± 3.61 m | +0.04 ± 1.18 m | -0.38 ± 0.33 m |
| z500 error, 99th pct / max abs | 12.9 / 17.5 m | 4.1 / 11.3 m | 1.4 / 2.8 m |
| z500 error where surfaces differ > 300 m, mean ± std (n=1384) | +1.37 ± 3.61 m | +1.17 ± 1.69 m | -0.60 ± 0.31 m |
| z500 error where surfaces differ > 300 m, max abs | 14.3 m | 6.9 m | 2.2 m |
| T − ERA5 at top level, mean ± std | +8.65 ± 2.45 K | +8.69 ± 2.45 K | -0.00 ± 0.06 K |
| T − ERA5 over all levels above 10 hPa, mean ± std | +0.33 ± 2.19 K | +0.33 ± 2.16 K | +0.02 ± 0.30 K |
| column water vapour − ERA5, |dz| < 20 m (n=15417) | +0.091 ± 0.758 kg/m² (+0.48 %) | +0.030 ± 0.335 kg/m² (+0.14 %) | -0.041 ± 0.321 kg/m² (-0.15 %) |
| ps − ERA5, |dz| < 20 m | +4.8 ± 96.1 Pa | +6.2 ± 93.0 Pa | +4.8 ± 92.1 Pa |
1096459 columns in box (42.0, 44.0, 252.0, 254.5); model minus ERA5 surface 5/50/95%: [-190.  -12.  302.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.07 | 5.3 | 5.9 | 4.8 |
| HICCUP conservative (20260918, in use) | 0.022 | 0.0024 | 0.023 | +0.45 | 5.6 | 6.5 | 7.8 |
| HICCUP bilinear (20261113) | 0.019 | 0.0021 | 0.021 | +0.54 | 5.7 | 7.0 | 8.2 |
| new tool (20261113) | 0.024 | 0.0030 | 0.002 | -0.05 | 5.4 | 6.0 | 5.0 |

wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wyoming_wind.1024x4.png
wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wyoming_imprint.1024x4.png
