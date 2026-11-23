# Recheck of the digitized Qu & Mudawar (2002) data

Started 2026-11-13 by Claude (Opus 5.5), independent of the digitizing script where possible. Each check is appended when it finishes; a check not listed here has not been done yet.

Data files checked: `validation/data/qu_mudawar_dP.csv`, `qu_mudawar_thermal.csv` (status `digitized` rows unless stated), against `raw/qu_mudawar_2002.pdf`.

## Check 1. Same test runs at the same Re in Figs. 4(a), 5 and 6 — PASS with two notes

Each test run should appear once in every figure at the same Re.

| q″ (W/cm²) | Fig. 4(a) | Fig. 5 | Fig. 6 TC1/TC2/TC3/TC4 | Max Re mismatch vs Fig. 4(a) |
|---|---|---|---|---|
| 100 | 25 | 25 | 25 / 25 / 25 / 25 | 3.8 (Fig. 5), 2.4–2.8 (Fig. 6) |
| 200 | 14 | 13 | 14 / 14 / 15 / 14 | 2.7 (Fig. 6) |

- Re mismatches of ≤ 4 are within the reading uncertainty (1 px ≈ 1.2–1.3 in Re).
- Note 1: Fig. 5 at 200 W/cm² has only 13 `digitized` points because its Re 444.7 point (41.4 K) is flagged `digitized_partly_hidden`. The point exists; it is only excluded from the MAPE.
- Note 2: Fig. 6(b) TC3 has 15 points: two fully visible squares at Re 787.6 (70.0 and 71.8 K). Checked visually in Check 5.

## Check 2. Values stated in the paper's text — PASS

| Quantity | Text (Sec. 2.4 / 3.2) | Digitized |
|---|---|---|
| ΔP at the highest Re, 100 W/cm² | 0.86 bar at Re 1672 | 0.859 bar at Re 1670 |
| Re range, 100 W/cm² | 139–1672 | 139–1670 |
| Re range, 200 W/cm² | 385–1289 | 386–1288 |

## Check 3. Fig. 5 water temperature rise against the energy balance — PASS (no digitizing error); one physical note

Expected ΔT from Q = q″ × 4.48 cm² (448 W / 896 W) and ṁ from Re with inlet properties (B1, which reproduces the paper's 93.5 ml/min at Re 139 to 0.7 %), using CoolProp enthalpy.

| q″ (W/cm²) | Points | Mean (measured − energy balance) | MAPE | Largest |
|---|---|---|---|---|
| 100 | 25 | −0.8 % | 2.0 % | −5.4 % at Re 442 (20.36 vs 21.52 K) |
| 200 | 13 | −4.1 % | 4.1 % | −5.7 % at Re 1290 (13.89 vs 14.73 K) |

- The reading uncertainty of Fig. 5 is about ±0.11 K (1 px), i.e. 0.1–0.8 % of these values, so the deviations are not digitizing errors: they are in the paper's data.
- At 200 W/cm² every point lies 2.5–5.7 % below the energy balance. This is within the paper's flow-rate uncertainty (rotameter, about ±4 %) plus heat loss, so the data are kept unchanged. It means the model (which uses the full Q) will slightly over-predict the water temperature rise at 200 W/cm².

## Check 4. Thermocouple order and smoothness (Fig. 6) — PASS

- Order: at every run TC1 < TC2 < TC3 < TC4 (downstream thermocouples hotter), at both heat fluxes. No violations.
- Smoothness: residual from a smooth fit (quadratic in log T-rise vs log Re), per thermocouple:

| | TC1 | TC2 | TC3 | TC4 |
|---|---|---|---|---|
| 100 W/cm², rms | 1.9 % | 1.8 % | 2.3 % | 2.0 % |
| 200 W/cm², rms | 1.0 % | 0.6 % | 0.8 % | 0.8 % |

- Points more than 4 % off the trend (100 W/cm² only): Re 443 (TC1 −5.6 %, TC3 −5.0 %, TC4 −4.7 %); Re 976 TC3 (+4.4 %); Re 1672 TC4 (−4.4 %).
- The Re ≈ 442 run is low on all thermocouples and also in Fig. 5 (−5.4 %, Check 3). A whole run reading low on four sensors and on the water ΔT points to that run's real conditions (probably a slightly higher actual flow), not to a misread marker. Kept unchanged.

## Check 5. Geometry, conditions and sensor CSVs against the PDF text — PASS; `verified_against_pdf` set to `yes`

Confirmed in the PDF text (page 6 Table 1, Secs. 2.2–2.4, 3.2, 3.3, Eqs. 2, 11, 12, 27):
- Table 1 column alignment, which was the main open question: Ww 118, Wch 231, Hw1 12 700, Hch 713, Hw2 5637, Hth 3175 µm; L1 5, L2 = L3 = L4 11.588, L 44.764 mm. The Nomenclature defines Hw1 as the cover plate thickness and Hw2 as the unit-cell bottom wall to channel bottom wall.
- Thermocouple depth 2.462 mm = Hw2 − Hth: Eq. (27) evaluates the temperature at z = Hth (thermocouple plane) with z from the unit-cell bottom, and the channel occupies Hw2 ≤ z ≤ Hw2 + Hch (Eqs. 11–12).
- 21 channels; planform 1.0 cm × 4.48 cm; inlet 15 °C; Re "based on inlet parameters" (Eq. 2), which confirms assumption B1; flow 93.5–1136.4 ml/min (100 W/cm²) and 259.1–859.5 ml/min (200 W/cm²); 0.86 bar measured maximum ΔP; heat loss < 1 %; uncertainties 0.5 % (wattmeter), 4 % (rotameter), 3.5 % (pressure transducers), 0.3 °C (thermocouples); k = 401 (copper) and 0.2 W/m·K (cover); 12 cartridge heaters in 6.35 mm holes; pressure transducers in the deep plenums.
- Channel depth: Table 1 says 713 µm, Sec. 2.2 says 712 µm. 0.14 % difference; 713 kept.
- Thermocouple x positions: symmetric about the channel middle (5 mm from either end), and TC1 reads coolest, so TC1 is the inlet-side sensor. No ambiguity remains.
- Still missing: outlet or system pressure (not reported). Only affects water properties negligibly (B4: 2 bar assumed).

## Check 6. Independent re-reading of the figures — PASS; one status corrected

Method, independent of the digitizing script where possible:
- Pages re-rendered at 600 dpi with a different renderer (PyMuPDF instead of pdftoppm).
- Calibration rebuilt with separate code: frame line found from ink counts, major ticks from their ink runs, and a least-squares fit through **all** major ticks (the script used the two end ticks).
- 12 randomly chosen `digitized` points per figure: each marker's area centroid taken from the new render and converted with the new calibration.

| Figure | Points compared | Max \|ΔRe\| | Max \|Δy\| | Mean \|Δy\| |
|---|---|---|---|---|
| Fig. 4(a) ΔP | 12 | 3.3 | 0.003 bar | 0.001 bar |
| Fig. 5 water ΔT | 11 (1 merged marker skipped) | 23.8* | 0.83 K* | 0.12 K |
| Fig. 6(a) TC rise | 12 | 1.3 | 0.38 K | 0.23 K |
| Fig. 6(b) TC rise | 12 | 1.9 | 0.37 K | 0.17 K |

- Agreement is within 1–3 px, i.e. about the reading uncertainty: ≤ 0.003 bar (0.3 % of full scale) for ΔP and ≤ 0.4 K for the thermocouple rises (0.4–2 % of the values).
- *The two larger Fig. 5 differences (Re 951.5 and 977.4) come from the check, not the data: in Fig. 5 the paper's prediction line passes through the markers and two squares touch, so the check's simple blob centroid included part of the line and the neighbouring square. Zoomed crops show the CSV positions sit on the marker centres.
- Visual check of the stacked markers flagged in Check 1: at Re 787.6 in Fig. 6(b) there are two TC3 squares, the lower partly behind the upper (white halo line between them), i.e. a repeat run. Both were `digitized`; the lower one (70.02 K) is now `digitized_partly_hidden`, consistent with every other repeat marker. Value unchanged.

Effect of the status change on the selected model's validation: thermocouple MAPE 4.60 % → 4.61 % (156 points). The README and status numbers are unchanged at the precision reported; the full matrix was not rerun.

Not covered by this recheck: a person's own reading (e.g. in the WebPlotDigitizer browser app). This recheck shares the same assumption that a marker's plotted value is its area centroid; for triangles the plotting anchor could instead be the bounding-box centre, about 3 px (0.4 K) higher in Fig. 6.

## Summary

- **No data values changed.** One status change (Fig. 6(b), TC3, Re 787.6, 70.02 K → `digitized_partly_hidden`).
- Geometry, conditions and sensor CSVs verified against the PDF text and Table 1 (`verified_against_pdf = yes`), including the Table 1 column alignment and the 2.462 mm thermocouple depth. Outlet pressure is still not reported in the paper.
- The digitized points agree with an independent reading within the reading uncertainty (≤ 0.003 bar, ≤ 0.4 K).
- Physical observations kept in the data: at 200 W/cm² the measured water ΔT is 2.5–5.7 % below the energy balance (within the 4 % flow uncertainty); the Re ≈ 442 run at 100 W/cm² reads about 5 % low on every sensor.
- Still for a person at the time of this recheck: spot-check points per figure in WebPlotDigitizer. Done afterwards; see "Hand check" below.

## Hand check (independent, by hand in the WebPlotDigitizer browser app) — PASS

Done after the recheck above, by the manual route of report section 7.4. 24 points were read by hand: 8 from Fig. 4(a), 8 from Fig. 5 and 8 from Figs. 6(a) and 6(b) (TC1–TC4 at 100 and 200 W/cm²), spread over the Re range and both heat fluxes. Readings: `raw/hand_check_points.csv` (its "Data" columns equal the benchmark CSV values; the original percentage columns divide by the hand reading). Each point was matched to its row in `qu_mudawar_dP.csv` / `qu_mudawar_thermal.csv` (same figure, heat flux, sensor, Re and value), and the agreement was recomputed with the CSV value as the reference. Axis spans from the digitizer's frame boxes and calibration (`digitize/qm_figures.py`, `raw/fig*_meta.json`): Re 0–1800, ΔP 0–1 bar, water rise 0–80 K, thermocouple rise 10–100 K (Fig. 6(a)) and 30–120 K (Fig. 6(b)).

| Figure | Points | Re difference, largest | Value difference, mean / largest | Largest absolute | Largest, % of axis span (Re / value) |
|---|---|---|---|---|---|
| Fig. 4(a) ΔP | 8 (2 partly hidden) | 0.65 % | 1.2 % / 2.7 % | 0.0063 bar | 0.32 % / 0.63 % |
| Fig. 5 water ΔT | 8 (2 partly hidden) | 1.39 % | 1.0 % / 1.8 % | 0.76 K | 0.43 % / 0.95 % |
| Figs. 6(a)+(b) TC rise | 8 | 0.70 % | 0.5 % / 1.5 % | 0.49 K | 0.24 % / 0.54 % |

- Every difference is under 1 % of the axis span. The largest Fig. 4(a) and Fig. 5 differences are at markers classed `digitized_partly_hidden` (left out of the MAPE); among the Fig. 4(a) points used in the MAPE the largest difference is 2.5 % (0.0020 bar at 0.079 bar).
- **No data value or status changed.** The hand check closes the open item above.
