## ne256np4, ERA5 pressure levels

Identity check on 30,000 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 326 of 3,538,946
columns changed: 205; smallest dp among them 75.03 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 181 | 0.74 → 0.77 | 2.30 → 2.31 | 2.36 → 2.13 | 0.46 / 2.23 |
| dp > 100 hPa, not folded | 24 | 0.66 → 0.80 | 2.05 → 2.07 | 2.20 → 1.66 | 1.18 / 2.49 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 0 | 0 | – |
| Coast Mountains / Cascades | 0 | 0 | – |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 9 | 0 | 0.33 / 1.04 |
| Andes | 67 | 0 | 0.28 / 1.22 |

highest changed level: 73 of 128 (lowest is 127); deepest dp 126 hPa at -12.60, 286.27

