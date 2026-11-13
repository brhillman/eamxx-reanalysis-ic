## 1024x3, ERA5 model levels

Identity check on 30,000 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 111,564 of 117,157,709
columns changed: 84,986; smallest dp among them 75.00 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 66,497 | 1.00 → 1.00 | 2.42 → 2.45 | 1.61 → 1.49 | 0.26 / 4.78 |
| dp > 100 hPa, not folded | 18,021 | 0.96 → 1.00 | 2.47 → 2.52 | 1.66 → 1.28 | 0.79 / 4.39 |
| folded before (dp > 150·ps_e/ps) | 468 | 0.68 → 1.00 | 2.46 → 2.52 | 2.31 → 1.85 | 2.25 / 3.79 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 13,579 | 68 | 0.55 / 3.64 |
| Coast Mountains / Cascades | 17,794 | 180 | 0.41 / 2.85 |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 3,336 | 77 | 0.65 / 3.79 |
| Andes | 2,977 | 63 | 0.57 / 4.28 |

highest changed level: 71 of 128 (lowest is 127); deepest dp 160 hPa at 35.43, 74.28

