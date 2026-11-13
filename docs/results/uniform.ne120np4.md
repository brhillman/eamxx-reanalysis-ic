30000 columns sampled (300 runs) from 777602 
model minus ERA5 surface height in sample: 1/50/99% = [-142.   -0.  127.] m

| metric | HICCUP default (fv2se_flx) | HICCUP bilinear | new tool, ERA5 pressure levels | new tool |
|---|---|---|---|---|
| negative q/qc/qi/O3 values | 0 | 0 | 0 | 0 |
| max RH over liquid (EAMxx formula) | 101.10 % | 101.12 % | 100.00 % | 100.00 % |
| points with RH > 100 % | 5831 | 6299 | 0 | 0 |
| phis − PHIS_d, rms / max | 37 / 990 m | 31 / 995 m | 0 / 0 m | 0 / 0 m |
| z500 error, mean ± std (ps > 700 hPa) | -0.66 ± 2.28 m | -0.22 ± 1.80 m | -0.31 ± 1.50 m | -0.39 ± 0.48 m |
| z500 error, 99th pct / max abs | 6.7 / 61.6 m | 5.5 / 64.3 m | 4.5 / 63.6 m | 1.3 / 13.2 m |
| z500 error where surfaces differ > 300 m, mean ± std (n=88) | +10.41 ± 13.38 m | +9.75 ± 12.96 m | +6.16 ± 8.37 m | -1.45 ± 1.82 m |
| z500 error where surfaces differ > 300 m, max abs | 47.7 m | 49.4 m | 32.2 m | 8.9 m |
| T − ERA5 at top level, mean ± std | +5.72 ± 6.13 K | +5.73 ± 6.12 K | +5.73 ± 6.12 K | +0.00 ± 0.07 K |
| T − ERA5 over all levels above 10 hPa, mean ± std | +0.25 ± 2.10 K | +0.27 ± 2.09 K | +0.27 ± 2.14 K | +0.01 ± 0.30 K |
| column water vapour − ERA5, |dz| < 20 m (n=24778) | +0.032 ± 0.298 kg/m² (+0.08 %) | +0.051 ± 0.269 kg/m² (+0.22 %) | +0.029 ± 0.270 kg/m² (+0.11 %) | -0.002 ± 0.252 kg/m² (+0.00 %) |
| ps − ERA5, |dz| < 20 m | -2.1 ± 52.2 Pa | -0.5 ± 51.5 Pa | -0.6 ± 51.3 Pa | -0.9 ± 51.3 Pa |

776919 columns in box (-90.0, 90.0, 0.0, 360.0); model minus ERA5 surface 5/50/95%: [-26.   0.  26.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.01 | 2.9 | 6.5 | 2.3 |
| HICCUP default (fv2se_flx) | 0.146 | 0.0671 | 0.170 | +0.01 | 3.3 | 7.6 | 3.5 |
| HICCUP bilinear | 0.147 | 0.0684 | 0.168 | +0.01 | 3.3 | 7.6 | 3.5 |
| new tool, ERA5 pressure levels | 0.185 | 0.0866 | 0.257 | -0.01 | 4.3 | 7.9 | 3.5 |
| new tool | 0.168 | 0.0779 | 0.147 | -0.01 | 2.9 | 6.6 | 2.4 |

Hydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m); z500 where ps > 700 hPa, z300 everywhere
| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |
|---|---|---|---|---|
| HICCUP default (fv2se_flx) | -0.73 ± 2.13 | 97.8 | -0.91 ± 2.66 | 96.9 |
| HICCUP bilinear | -0.25 ± 1.63 | 94.7 | -0.17 ± 2.14 | 94.5 |
| new tool, ERA5 pressure levels | -0.33 ± 1.32 | 85.4 | -0.25 ± 1.99 | 84.3 |
| new tool | -0.40 ± 0.39 | 19.1 | -0.54 ± 0.70 | 45.5 |

