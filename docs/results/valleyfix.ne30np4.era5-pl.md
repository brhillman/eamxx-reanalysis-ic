## ne30np4, ERA5 pressure levels

Identity check on 48,602 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 137 of 48,602
columns changed: 109; smallest dp among them 75.38 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 72 | 0.68 → 0.72 | 2.00 → 2.04 | 2.38 → 2.20 | 0.40 / 1.49 |
| dp > 100 hPa, not folded | 27 | 0.44 → 0.65 | 1.07 → 1.07 | 2.48 → 1.91 | 1.30 / 7.46 |
| folded before (dp > 150·ps_e/ps) | 10 | 0.25 → 0.63 | 2.40 → 2.50 | 3.22 → 2.66 | 2.15 / 8.87 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 2 | 0 | 0.13 / 0.19 |
| Coast Mountains / Cascades | 1 | 0 | 0.08 / 0.08 |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 8 | 0 | 0.79 / 1.97 |
| Andes | 40 | 7 | 1.07 / 8.87 |

highest changed level: 72 of 128 (lowest is 127); deepest dp 163 hPa at 8.53, 288.83

