48602 columns sampled (1 runs) from 48602 
model minus ERA5 surface height in sample: 1/50/99% = [-430.    0.  325.] m

| metric | HICCUP default (fv2se_flx) | HICCUP bilinear | new tool, ERA5 pressure levels | new tool |
|---|---|---|---|---|
| negative q/qc/qi/O3 values | 0 | 0 | 0 | 0 |
| max RH over liquid (EAMxx formula) | 101.08 % | 104.11 % | 100.00 % | 100.00 % |
| points with RH > 100 % | 3756 | 9868 | 0 | 0 |
| phis − PHIS_d, rms / max | 59 / 1126 m | 101 / 1625 m | 0 / 0 m | 0 / 0 m |
| z500 error, mean ± std (ps > 700 hPa) | -0.14 ± 5.02 m | -0.27 ± 1.86 m | -0.34 ± 1.30 m | -0.39 ± 0.40 m |
| z500 error, 99th pct / max abs | 18.0 / 164.6 m | 5.9 / 85.6 m | 3.9 / 56.7 m | 1.3 / 15.5 m |
| z500 error where surfaces differ > 300 m, mean ± std (n=1322) | +14.14 ± 18.78 m | +3.39 ± 8.26 m | +2.06 ± 4.96 m | -0.57 ± 1.08 m |
| z500 error where surfaces differ > 300 m, max abs | 164.6 m | 85.6 m | 56.7 m | 8.9 m |
| T − ERA5 at top level, mean ± std | +5.59 ± 6.01 K | +5.59 ± 6.02 K | +5.59 ± 6.02 K | -0.00 ± 0.07 K |
| T − ERA5 over all levels above 10 hPa, mean ± std | +0.27 ± 2.13 K | +0.29 ± 2.11 K | +0.29 ± 2.19 K | +0.02 ± 0.33 K |
| column water vapour − ERA5, |dz| < 20 m (n=35582) | +0.022 ± 0.582 kg/m² (+0.25 %) | +0.043 ± 0.296 kg/m² (+0.18 %) | +0.022 ± 0.296 kg/m² (+0.09 %) | -0.006 ± 0.282 kg/m² (-0.01 %) |
| ps − ERA5, |dz| < 20 m | -7.5 ± 51.6 Pa | -6.1 ± 49.2 Pa | -6.1 ± 49.0 Pa | -6.2 ± 49.0 Pa |
48431 columns in box (-90.0, 90.0, 0.0, 360.0); model minus ERA5 surface 5/50/95%: [-99.   0. 105.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | +0.04 | 2.9 | 7.0 | 3.3 |
| HICCUP default (fv2se_flx) | 0.417 | 0.2180 | 0.597 | +0.06 | 3.3 | 8.0 | 4.4 |
| HICCUP bilinear | 0.515 | 0.2905 | 0.785 | +0.10 | 3.1 | 8.1 | 5.1 |
| new tool, ERA5 pressure levels | 0.577 | 0.3133 | 0.904 | +0.03 | 4.6 | 8.4 | 4.8 |
| new tool | 0.604 | 0.3056 | 0.667 | +0.04 | 2.9 | 7.1 | 3.4 |

Hydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m); z500 where ps > 700 hPa, z300 everywhere
| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |
|---|---|---|---|---|
| HICCUP default (fv2se_flx) | -0.14 ± 5.03 | 164.6 | -0.28 ± 5.59 | 162.9 |
| HICCUP bilinear | -0.27 ± 1.86 | 85.6 | -0.20 ± 2.31 | 85.0 |
| new tool, ERA5 pressure levels | -0.34 ± 1.30 | 56.7 | -0.26 ± 1.95 | 56.5 |
| new tool | -0.39 ± 0.40 | 15.5 | -0.54 ± 0.73 | 45.3 |

wrote /pscratch/sd/b/bhillma/conus200/ne30_ic/comparison/wind_global.ne30np4.png
