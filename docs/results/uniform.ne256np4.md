30000 columns sampled (300 runs) from 3538946 
model minus ERA5 surface height in sample: 1/50/99% = [-158.   -0.  230.] m

| metric | HICCUP default (fv2se_flx) | HICCUP bilinear | new tool, ERA5 pressure levels | new tool |
|---|---|---|---|---|
| negative q/qc/qi/O3 values | 0 | 0 | 0 | 0 |
| max RH over liquid (EAMxx formula) | 101.09 % | 101.07 % | 100.00 % | 100.00 % |
| points with RH > 100 % | 5224 | 4905 | 0 | 0 |
| phis − PHIS_d, rms / max | 65 / 1331 m | 62 / 1303 m | 0 / 0 m | 0 / 0 m |
| z500 error, mean ± std (ps > 700 hPa) | -0.76 ± 2.16 m | -0.20 ± 1.87 m | -0.29 ± 1.53 m | -0.40 ± 0.34 m |
| z500 error, 99th pct / max abs | 6.4 / 71.8 m | 5.4 / 58.7 m | 4.1 / 63.8 m | 1.4 / 6.7 m |
| z500 error where surfaces differ > 300 m, mean ± std (n=246) | +3.59 ± 11.11 m | +4.65 ± 11.96 m | +4.51 ± 8.18 m | -0.98 ± 1.34 m |
| z500 error where surfaces differ > 300 m, max abs | 71.8 m | 58.5 m | 52.1 m | 6.7 m |
| T − ERA5 at top level, mean ± std | +5.62 ± 6.44 K | +5.63 ± 6.42 K | +5.63 ± 6.42 K | -0.00 ± 0.08 K |
| T − ERA5 over all levels above 10 hPa, mean ± std | +0.23 ± 2.15 K | +0.25 ± 2.14 K | +0.27 ± 2.25 K | +0.01 ± 0.24 K |
| column water vapour − ERA5, |dz| < 20 m (n=24618) | +0.039 ± 0.280 kg/m² (+0.08 %) | +0.054 ± 0.298 kg/m² (+0.21 %) | +0.034 ± 0.297 kg/m² (+0.13 %) | +0.005 ± 0.280 kg/m² (+0.03 %) |
| ps − ERA5, |dz| < 20 m | -0.4 ± 51.2 Pa | +1.6 ± 50.1 Pa | +1.5 ± 50.0 Pa | +1.1 ± 50.0 Pa |

3537439 columns in box (-90.0, 90.0, 0.0, 360.0); model minus ERA5 surface 5/50/95%: [-39.   0.  36.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.02 | 2.8 | 6.6 | 2.1 |
| HICCUP default (fv2se_flx) | 0.096 | 0.0447 | 0.115 | +0.02 | 3.2 | 7.7 | 3.7 |
| HICCUP bilinear | 0.073 | 0.0273 | 0.072 | +0.02 | 3.2 | 7.7 | 3.7 |
| new tool, ERA5 pressure levels | 0.094 | 0.0379 | 0.120 | -0.01 | 4.3 | 8.1 | 3.5 |
| new tool | 0.089 | 0.0331 | 0.052 | -0.02 | 2.8 | 6.7 | 2.2 |

Hydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m); z500 where ps > 700 hPa, z300 everywhere
| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |
|---|---|---|---|---|
| HICCUP default (fv2se_flx) | -0.79 ± 2.00 | 110.7 | -0.97 ± 2.59 | 109.0 |
| HICCUP bilinear | -0.23 ± 1.71 | 103.2 | -0.15 ± 2.22 | 102.1 |
| new tool, ERA5 pressure levels | -0.34 ± 1.28 | 99.3 | -0.25 ± 1.97 | 98.2 |
| new tool | -0.40 ± 0.39 | 17.3 | -0.54 ± 0.70 | 46.9 |

