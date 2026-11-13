## ne256np4, ERA5 model levels

Identity check on 30,000 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 336 of 3,538,946
columns changed: 227; smallest dp among them 75.02 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 201 | 1.00 → 1.00 | 3.37 → 3.40 | 2.33 → 2.06 | 0.47 / 2.05 |
| dp > 100 hPa, not folded | 26 | 0.96 → 1.00 | 3.77 → 3.82 | 2.43 → 1.75 | 1.42 / 2.51 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 0 | 0 | – |
| Coast Mountains / Cascades | 0 | 0 | – |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 8 | 0 | 0.32 / 0.75 |
| Andes | 76 | 0 | 0.38 / 1.99 |

highest changed level: 74 of 128 (lowest is 127); deepest dp 126 hPa at -12.60, 286.27

