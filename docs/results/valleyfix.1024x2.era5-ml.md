## 1024x2, ERA5 model levels

Identity check on 30,000 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 37,992 of 71,174,684
columns changed: 28,222; smallest dp among them 75.00 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 22,614 | 1.00 → 1.00 | 2.30 → 2.32 | 1.81 → 1.68 | 0.31 / 4.78 |
| dp > 100 hPa, not folded | 5,369 | 0.96 → 1.00 | 2.44 → 2.48 | 1.81 → 1.40 | 0.88 / 4.39 |
| folded before (dp > 150·ps_e/ps) | 239 | 0.65 → 1.00 | 2.87 → 2.88 | 2.20 → 1.57 | 1.89 / 3.79 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 3,229 | 2 | 0.51 / 2.68 |
| Coast Mountains / Cascades | 3,968 | 17 | 0.37 / 2.73 |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 3,336 | 77 | 0.65 / 3.79 |
| Andes | 2,977 | 63 | 0.57 / 4.28 |

highest changed level: 71 of 128 (lowest is 127); deepest dp 160 hPa at 35.43, 74.28

