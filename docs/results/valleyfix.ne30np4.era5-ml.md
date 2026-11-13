## ne30np4, ERA5 model levels

Identity check on 48,602 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 151 of 48,602
columns changed: 120; smallest dp among them 75.48 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 73 | 1.00 → 1.00 | 3.06 → 3.10 | 2.41 → 2.20 | 0.47 / 1.59 |
| dp > 100 hPa, not folded | 35 | 0.95 → 1.00 | 2.75 → 2.82 | 2.66 → 1.93 | 1.49 / 8.14 |
| folded before (dp > 150·ps_e/ps) | 12 | 0.53 → 1.00 | 3.13 → 3.14 | 3.50 → 2.21 | 2.72 / 10.74 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 2 | 0 | 0.16 / 0.17 |
| Coast Mountains / Cascades | 1 | 0 | 0.30 / 0.30 |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 8 | 0 | 1.06 / 2.13 |
| Andes | 37 | 8 | 1.52 / 10.74 |

highest changed level: 71 of 128 (lowest is 127); deepest dp 181 hPa at 8.53, 288.83

