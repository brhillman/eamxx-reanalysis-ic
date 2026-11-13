## ne120np4, ERA5 model levels

Identity check on 30,000 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 44 of 777,602
columns changed: 28; smallest dp among them 75.41 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 26 | 1.00 → 1.00 | 3.49 → 3.51 | 2.46 → 2.15 | 0.50 / 1.57 |
| dp > 100 hPa, not folded | 2 | 0.98 → 0.98 | 4.35 → 4.36 | 2.09 → 1.67 | 1.15 / 1.16 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 0 | 0 | – |
| Coast Mountains / Cascades | 0 | 0 | – |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 0 | 0 | – |
| Andes | 6 | 0 | 0.24 / 0.41 |

highest changed level: 80 of 128 (lowest is 127); deepest dp 105 hPa at -9.33, 34.29

