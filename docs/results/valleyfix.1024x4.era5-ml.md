## 1024x4, ERA5 model levels

Identity check on 30,000 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 412,665 of 299,999,162
columns changed: 318,907; smallest dp among them 75.00 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 245,959 | 1.00 → 1.00 | 2.46 → 2.47 | 1.53 → 1.43 | 0.24 / 4.78 |
| dp > 100 hPa, not folded | 71,187 | 0.96 → 1.00 | 2.86 → 2.88 | 1.63 → 1.25 | 0.78 / 4.39 |
| folded before (dp > 150·ps_e/ps) | 1,761 | 0.69 → 1.00 | 1.74 → 1.75 | 2.42 → 2.07 | 2.48 / 4.00 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 55,938 | 500 | 0.57 / 4.00 |
| Coast Mountains / Cascades | 73,880 | 1,014 | 0.42 / 2.88 |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 3,336 | 77 | 0.65 / 3.79 |
| Andes | 2,977 | 63 | 0.57 / 4.28 |

highest changed level: 71 of 128 (lowest is 127); deepest dp 160 hPa at 35.43, 74.28

