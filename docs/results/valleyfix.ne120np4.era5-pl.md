## ne120np4, ERA5 pressure levels

Identity check on 30,000 random columns: all variables bit-identical except U/V in columns with dp > 75 hPa (= D/2)
columns with dp > 70 hPa (candidates): 41 of 777,602
columns changed: 26; smallest dp among them 75.15 hPa; columns with dp > 75 hPa unchanged: 0

Blending-layer wind profile, before → after (means over columns; ERA5 target = nearest ERA5 column at the same sigma, lowest 150 hPa)

| columns | n | distinct speeds per level | speed range in layer, median (m/s) | RMS vector difference from ERA5 at same sigma (m/s) | max \|ΔU\|,\|ΔV\| per column, mean / max (m/s) |
|---|---|---|---|---|---|
| dp ≤ 100 hPa | 24 | 0.73 → 0.76 | 2.63 → 2.66 | 2.49 → 2.25 | 0.46 / 1.53 |
| dp > 100 hPa, not folded | 2 | 0.65 → 0.77 | 2.78 → 2.80 | 2.04 → 1.66 | 1.10 / 1.19 |

| region | columns changed | of which folded before | mean / max of max \|ΔU\|,\|ΔV\| (m/s) |
|---|---|---|---|
| Sierra Nevada | 0 | 0 | – |
| Coast Mountains / Cascades | 0 | 0 | – |
| Wyoming | 0 | 0 | – |
| Himalaya / Karakoram | 0 | 0 | – |
| Andes | 6 | 0 | 0.07 / 0.12 |

highest changed level: 81 of 128 (lowest is 127); deepest dp 104 hPa at 82.68, 322.20

