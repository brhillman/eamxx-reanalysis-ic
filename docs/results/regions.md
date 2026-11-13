=== 1024x3 Coast Mountains (48.5,50.5,236,239)
=== 1024x2 Wyoming (42,44,252,254.5)
=== 1024x2 Sierra Nevada (36,39.5,239.5,242)
=== 1024x2 Coast Mountains (48.5,50.5,236,239)
57178 columns in box (48.5, 50.5, 236.0, 239.0); model minus ERA5 surface 5/50/95%: [-653.  -25.  529.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.07 | 1.2 | 1.4 | 0.8 |
| HICCUP conservative (in use) | 0.292 | 0.0389 | 0.052 | +0.21 | 1.4 | 1.8 | 1.5 |
| HICCUP bilinear | 0.284 | 0.0200 | 0.031 | +0.20 | 1.3 | 1.7 | 1.3 |
| new tool, pressure-matched winds | 0.338 | 0.0258 | 0.047 | +0.26 | 1.2 | 1.5 | 1.4 |
| new tool | 0.338 | 0.0258 | 0.004 | -0.03 | 1.2 | 1.4 | 0.9 |

Hydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m); z500 where ps > 700 hPa, z300 everywhere
| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |
|---|---|---|---|---|
| HICCUP conservative (in use) | +0.86 ± 1.99 | 10.3 | +4.78 ± 3.26 | 19.6 |
| HICCUP bilinear | +1.89 ± 2.00 | 8.9 | +1.71 ± 1.99 | 8.1 |
| new tool, pressure-matched winds | -0.69 ± 0.35 | 2.0 | -0.91 ± 0.28 | 2.1 |
| new tool | -0.69 ± 0.35 | 2.0 | -0.91 ± 0.28 | 2.1 |

wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wind_Coast_Mountains.1024x2.png
68536 columns in box (42.0, 44.0, 252.0, 254.5); model minus ERA5 surface 5/50/95%: [-187.  -12.  296.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.07 | 5.3 | 5.9 | 4.8 |
| HICCUP conservative (in use) | 0.047 | 0.0063 | 0.055 | +0.45 | 5.6 | 6.5 | 7.7 |
| HICCUP bilinear | 0.039 | 0.0045 | 0.044 | +0.53 | 5.7 | 7.0 | 8.2 |
| new tool, pressure-matched winds | 0.048 | 0.0066 | 0.079 | +0.58 | 5.3 | 6.5 | 8.5 |
| new tool | 0.048 | 0.0066 | 0.005 | -0.05 | 5.4 | 6.1 | 4.9 |

Hydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m); z500 where ps > 700 hPa, z300 everywhere
| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |
|---|---|---|---|---|
| HICCUP conservative (in use) | -2.73 ± 2.25 | 10.1 | -8.18 ± 3.55 | 17.5 |
| HICCUP bilinear | +1.39 ± 0.97 | 7.6 | +1.15 ± 1.45 | 6.9 |
| new tool, pressure-matched winds | +0.37 ± 0.45 | 3.1 | +0.52 ± 0.54 | 3.6 |
| new tool | +0.37 ± 0.45 | 3.1 | +0.52 ± 0.54 | 3.6 |

wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wind_Wyoming.1024x2.png
133605 columns in box (36.0, 39.5, 239.5, 242.0); model minus ERA5 surface 5/50/95%: [-538.  -25.  606.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.04 | 2.6 | 2.1 | 2.4 |
| HICCUP conservative (in use) | 0.141 | 0.0171 | 0.038 | +0.41 | 2.6 | 2.6 | 3.9 |
| HICCUP bilinear | 0.136 | 0.0083 | 0.025 | +0.39 | 2.7 | 2.6 | 4.1 |
| new tool, pressure-matched winds | 0.166 | 0.0104 | 0.039 | +0.40 | 2.6 | 2.4 | 4.2 |
| new tool | 0.166 | 0.0104 | 0.004 | -0.01 | 2.6 | 2.1 | 2.5 |

Hydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m); z500 where ps > 700 hPa, z300 everywhere
| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |
|---|---|---|---|---|
| HICCUP conservative (in use) | +2.59 ± 6.26 | 47.0 | +8.57 ± 8.17 | 60.8 |
| HICCUP bilinear | +4.83 ± 7.34 | 45.5 | +6.33 ± 7.28 | 45.1 |
| new tool, pressure-matched winds | -0.65 ± 1.00 | 5.8 | -0.82 ± 0.81 | 4.7 |
| new tool | -0.65 ± 1.00 | 5.8 | -0.82 ± 0.81 | 4.7 |

wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wind_Sierra_Nevada.1024x2.png
215987 columns in box (48.5, 50.5, 236.0, 239.0); model minus ERA5 surface 5/50/95%: [-678.  -29.  575.] m

| | roughness T (K) | roughness qv (g/kg) | roughness U (m/s) | corr(speed, dz) | speed, dz ≤ −50 m | \|dz\| < 20 m | dz ≥ 100 m |
|---|---|---|---|---|---|---|---|
| ERA5 lowest model level (~10 m), interpolated | – | – | – | -0.06 | 1.2 | 1.4 | 0.9 |
| HICCUP conservative (in use) | 0.178 | 0.0255 | 0.036 | +0.25 | 1.4 | 1.8 | 1.6 |
| HICCUP bilinear | 0.175 | 0.0134 | 0.022 | +0.23 | 1.3 | 1.7 | 1.3 |
| new tool | 0.208 | 0.0173 | 0.002 | -0.02 | 1.2 | 1.4 | 0.9 |

Hydrostatic check over the box: height integrated from PHIS_d minus ERA5 analysed (m); z500 where ps > 700 hPa, z300 everywhere
| | z500 mean ± std | z500 max abs | z300 mean ± std | z300 max abs |
|---|---|---|---|---|
| HICCUP conservative (in use) | +0.89 ± 1.98 | 10.7 | +4.83 ± 3.29 | 19.9 |
| HICCUP bilinear | +1.93 ± 2.03 | 9.0 | +1.74 ± 2.04 | 8.6 |
| new tool | -0.70 ± 0.35 | 2.0 | -0.91 ± 0.28 | 2.1 |

wrote /pscratch/sd/b/bhillma/conus200/era5_ic/comparison/wind_Coast_Mountains.1024x3.png
