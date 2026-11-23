# Validation

**Dataset:** W. Qu and I. Mudawar (2002), *Experimental and numerical study of pressure drop and heat transfer in a single-phase micro-channel heat sink*, Int. J. Heat Mass Transfer 45, 2549–2565.
Free PDF: https://engineering.purdue.edu/mudawar/files/articles-all/2002/2002_1.pdf

## Rules

1. **The benchmark case is separate from the 1 kW application case.** Experiment inputs live in `validation/data/`, never in `coldplate/config.py`. The model is run at the experiment's own geometry, heat input and flow.
2. **Every value has a status:** `measured` (number stated in the paper's text or tables), `digitized` (read from a figure), `derived` (computed from stated values; the formula is in the location column), `assumed` (our choice, with reason), `missing`.
3. **Every value records** its unit and paper location (section, table, equation or figure). Page numbers are still to be added.
4. **`verified_against_pdf`**: the text values were extracted on 2026-11-07 by an automated reading of the PDF text, which garbles some symbols (µm appeared as "lm"). Set this column to `yes` only after a person checks the value in the PDF.
5. **No comparison until** the temperature-measurement and pressure-tap sections below are confirmed.

## Data files

| File | Contents | State |
|---|---|---|
| `data/qu_mudawar_geometry.csv` | heat sink geometry and materials | filled from text and Table 1; not yet verified |
| `data/qu_mudawar_conditions.csv` | fluid, inlet temperature, heat flux, Re and flow ranges, uncertainties | filled from text; outlet pressure missing |
| `data/qu_mudawar_sensors.csv` | thermocouple and pressure-tap locations | filled from text and Table 1; x positions derived |
| `data/qu_mudawar_dP.csv` | measured pressure drop vs Re | header only: digitize Fig. 4(a) |
| `data/qu_mudawar_thermal.csv` | measured temperatures vs Re | header only: digitize Fig. 5 and Fig. 6 |

## Key facts from the paper (see the CSVs for locations)

- 21 channels, 231 µm × 713 µm (Sec. 2.2 says 712 µm), wall 236 µm (2 × W_w), channel length 44.764 mm, planform 1.0 cm × 4.48 cm.
- Polycarbonate cover on top: channels are heated on three sides with a nearly adiabatic top. Relevant to assumption A6.
- Heat enters from 12 cartridge heaters in the copper below the channels.
- q″_eff = 100 and 200 W/cm² on the 4.48 cm² planform (448 W and 896 W), deionized water, inlet 15 °C (to confirm).
- Re 139–1672 (100 W/cm²) and 385–1289 (200 W/cm²).

**Open reading issues:**
- Table 1's data row was extracted as "118 231 12 700 713 5637 3175". It is read here as W_w = 118, W_ch = 231, H_w1 = 12 700, H_ch = 713, H_w2 = 5637, H_th = 3175 µm. Confirm the column alignment in the PDF.
- H_th is not defined in the Nomenclature. Eq. (27) uses z = H_th for the thermocouple plane, so it is taken as the thermocouple plane height above the unit-cell bottom. That puts the thermocouples 2.46 mm below the channel bottom (derived).

## Temperature measurements

- Four Type-K thermocouples (0.33 mm bead) sit in holes drilled from the side wall to the heat sink center plane, in the copper **below** the channels, at x ≈ 5, 16.6, 28.2, 39.8 mm (derived from Table 1, L1 = 5 mm, L2 = L3 = L4 = 11.588 mm). Confirm from which end x is measured on Fig. 2(b) / Fig. 3.
- Inlet and outlet water temperatures are measured in the inlet and outlet plenums.
- **Consequence for the model:** compare predicted copper temperature at the thermocouple plane, i.e. local water temperature + convection + conduction through about 2.46 mm of copper. Do not compare the 1 kW device temperature or the channel-wall temperature directly.

## Pressure drop

- Two absolute pressure transducers connect to the **deep portions of the inlet and outlet plenums** (Sec. 2.2).
- So the measured ΔP includes plenum contraction and expansion losses, not channel friction alone. The paper's own prediction adds them: ΔP = ΔP_c1 + ΔP_c2 + ΔP_ch + ΔP_e2 + ΔP_e1 (Eq. 18–22), with loss coefficients "close to unity".
- **Consequence for the model:** compare against channel friction + minor losses, and take the contraction/expansion treatment from Eq. 18–22 (record the K values and the plenum and transition dimensions it uses). This settles decision D5.

## How to digitize the figures

Measured results are only in the figures. Two routes give the same kind of output; the raw exports go in `data/raw/` either way.

**A. Scripted (WebPlotDigitizer's own algorithms, headless).** `digitize/wpd_run.js` runs WPD's calibration (`wpd.XYAxes`), colour masking (`wpd.AutoDetectionData`) and marker detection (`wpd.BlobDetectorAlgo`) from the unmodified WPD source in `digitize/wpd_core/` (AGPL-3.0, commit in `SOURCE_COMMIT.txt`). `digitize/digitize.py config.json` renders nothing itself: give it a PNG of the figure (e.g. `pdftoppm -r 600 -f <page> -l <page> -png paper.pdf page`, then crop), the pixel positions of two ticks on each axis, the plot-area mask and the marker size range. Open and filled symbols are separated by blob area (`classes`). Overlapping markers come out as one blob outside both area classes and are labelled `UNCLASSIFIED`; place those by hand (`manual`). `tests/test_digitizer.py` checks the pipeline on a synthetic plot (positions recovered within 0.3 % of the axis range). If the figure in the PDF is vector art, markers can instead be read exactly from the drawing commands.

**B. By hand in the browser app** (https://automeris.io/WebPlotDigitizer), steps below.

1. **Get a clean image.** Open the PDF, zoom to 200–400% on the figure, and take a screenshot of just that plot (PNG). Higher resolution means smaller reading error.
2. **Load and calibrate.** In WebPlotDigitizer: *File → Load image*, choose *2D (X-Y) Plot*, then click four reference points: two on the x axis (e.g. Re = 0 and 1500) and two on the y axis, and type their values. Tick *log scale* if an axis is logarithmic. Use tick marks far apart to reduce error.
3. **Pick points.** Use manual mode (click each marker's center). Experimental data are discrete markers, so digitize markers, not fitted lines. Make a separate dataset for each series (100 vs 200 W/cm², or TC1–TC4), named after its legend entry.
4. **Check calibration.** Digitize one or two points whose values you know (an axis tick, or a value stated in the text, e.g. the 0.86 bar maximum ΔP at Re = 1672 for 100 W/cm²). If they are off by more than about 1–2% of the axis range, recalibrate.
5. **Export.** *View data → Download .CSV* for each dataset. Save the raw exports and the WebPlotDigitizer project (*File → Save project*, a .tar file) in `validation/data/raw/`, so the digitizing can be redone.
6. **Copy into our CSVs** with one row per point:
   - `qu_mudawar_dP.csv`: `source_figure` = "Fig. 4(a)"; `q_eff_W_per_cm2`; `Re`; `dP_axis_value` and `dP_axis_unit` as read from the plot; `dP_Pa` converted to Pa (1 bar = 1e5 Pa); `status` = digitized.
   - `qu_mudawar_thermal.csv`: Fig. 6, quantity = TC1…TC4, value in °C; Fig. 5, quantity = water temperature rise (T_out − T_in), value in °C or K as the axis shows.
7. **Record the reading uncertainty** in `notes` (about half a marker width, converted to axis units).

Figures to digitize, in order of priority:

| Figure | What it shows | Use |
|---|---|---|
| Fig. 4(a) | measured ΔP vs Re, both heat fluxes | pressure-drop validation |
| Fig. 6(a), 6(b) | thermocouple readings vs Re, 100 and 200 W/cm² | thermal validation |
| Fig. 5(a), 5(b) | water temperature rise vs Re | energy-balance check |
| Fig. 7 | temperature along the thermocouple line | optional, axial profile |

Check the axis labels and units on each figure in the PDF; the extracted text did not include them.

## Model assumptions for the benchmark (`coldplate/benchmark.py`)

| ID | Assumption | Basis |
|---|---|---|
| B1 | Re uses inlet-temperature properties: ṁ = Re·μ_in·N·w_c·H / D_h | Reproduces the paper's stated flow rates: Re 139 → 94.1 vs 93.5 ml/min, Re 1672 → 1132 vs 1136.4 ml/min (test) |
| B2 | Q = q″_eff × A_t enters uniformly over the planform; heat loss neglected | Eq. (1); heat loss < 1 % (Sec. 2.4) |
| B3 | Plenum contraction and expansion: K_c = K_e = 1.0 at channel velocity | Paper says its coefficients are "close to unity"; Eq. 18–22 not yet transcribed |
| B4 | Inlet pressure 2 bar | Not reported; only affects properties slightly |
| B5 | Thermocouple temperature = channel-floor temperature + q″·d/k_s, d = 2.462 mm | 1D conduction; depends on the H_th reading |

The model's `Geometry.t_b` is set to the thermocouple depth for the benchmark, and R_TIM = 0.

### First check against a text-stated value (not a validation)

Sec. 3.2 states a measured ΔP of 0.86 bar at 100 W/cm², Re = 1672. The model gives 1.03 bar with B3 (+19 %) and 0.73 bar with friction only (−15 %). The minor-loss treatment is the main uncertainty for ΔP. Do not tune K to this one point; transcribe Eq. 18–22 first.

## Running the comparison

    python -c "from coldplate.benchmark import compare; r = compare(); print(r['MAPE_dP'], r['MAPE_thermal'])"
    python validation/run_validation.py                    # every correlation combination
    python validation/run_validation.py --plots LG_3 1 MY 1   # parity plots for one choice

`run_validation.py` writes `results/thermal_model_matrix.csv` (Nu model × axial conduction) and `results/dP_model_matrix.csv` (friction model × minor losses). No coefficient is tuned to the data.

### Facts from the paper that bear on the model choice (text, 2026-11-08 reading)

- The paper's numerical model uses a **uniform velocity at the channel inlet** (Eq. 11) and the measured inlet water temperature (Eq. 16): simultaneously developing flow. That favours `MY` (combined entry) and apparent friction over fully developed values.
- It uses temperature-dependent viscosity at the mean temperature, as this model does; ΔP at the same Re is lower at 200 W/cm² because the water is warmer.
- The contraction/expansion terms (Eqs. 18–22) need plenum velocities and K values. The plenum dimensions are not given and the K values are only "close to unity" (forms from Todreas & Kazimi). With plenum velocity ≪ channel velocity they reduce to ΔP_minor ≈ (K_c2 + K_e2) ρu²/2, which is what B3 uses.
- The top wall is the polycarbonate cover (k = 0.2 W/m·K) with a weak convective condition, so three-sided heating (`*_3` models) is the closer boundary condition.

`compare()` reads every row in `qu_mudawar_dP.csv` (uses `dP_Pa`) and `qu_mudawar_thermal.csv` (`quantity` = TC1–TC4 in °C, or `water_temperature_rise`). For thermocouples, the percentage error is computed on the temperature rise above the inlet, not on °C.

## Comparison method

1. Run the model at each test condition with the experiment's geometry.
2. Compare like with like: copper temperature at the thermocouple plane, and total plenum-to-plenum ΔP.
3. Report parity plots and mean absolute percentage error (MAPE), separately for thermal and pressure-drop results. **Target from the submitted proposal: about 10–15%.**
4. If the error is too large, the proposal's fallback is a developing-flow Nusselt correlation. Also check A6 (three-sided heating: the cover is polycarbonate) and A8 (minor losses).
5. The proposal says the channels are short compared with the thermal entry length. Check 0.05·Re·Pr·D_h against L = 44.8 mm across the Re range.

## Results (2026-11-08)

Data: 43 ΔP points (Fig. 4a), 43 water-ΔT points (Fig. 5), 187 thermocouple rises (Fig. 6a/b), digitized as described above. Points partly hidden behind another marker (repeat runs) and one rejected point are kept in the CSVs with their own status and left out of the MAPE. Calibration checks: the last ΔP point reads 0.858 bar at Re 1670 (text: 0.86 bar at Re 1672); the Re ranges read 139–1670 and 386–1288 (text: 139–1672, 385–1289); major-tick spacing is linear to within 1.4 px; isolated markers agree with WebPlotDigitizer's own blob centroids to ≤ 1.5 px. Independent recheck done 2026-11-13 (`data/raw/recheck_log.md`): no values changed, one status corrected, geometry/conditions/sensors verified against the PDF. Independent hand check done afterwards: 24 points read by hand in the WebPlotDigitizer browser app (8 from Fig. 4(a), 8 from Fig. 5, 8 from Figs. 6(a)+(b); `data/raw/hand_check_points.csv`). Against the CSV values: Re within 1.39 %; ΔP mean 1.2 %, largest 2.7 % (0.0063 bar); water rise mean 1.0 %, largest 1.8 % (0.76 K); thermocouple rise mean 0.5 %, largest 1.5 % (0.49 K); all under 1 % of the axis span (`data/raw/recheck_log.md`, "Hand check"). No value changed.

Full matrix: `results/thermal_model_matrix.csv`, `results/dP_model_matrix.csv`. MAPE of thermocouple rise above inlet (157 points) and of ΔP (39 points); no coefficient tuned:

| Thermal model | 1D base | + axial conduction | + axial + wall viscosity |
|---|---|---|---|
| `fd_H1` (proposal) | 49.1 % | 50.3 % | 39.3 % |
| `fd_H1_3` | 40.6 % | 41.8 % | 32.2 % |
| `LG` | 14.4 % | 12.5 % | 7.6 % |
| `LG_3` | 9.8 % | 7.5 % | **4.5 %** (bias +2.4 %) |
| `MY` | 13.1 % | 10.5 % | 6.6 % |
| `MY_3` | 9.2 % | 6.7 % | **4.6 %** (bias +0.7 %) |

Water temperature rise (energy balance): 2.8–2.9 % for every model.

| Friction | no plenum losses | + K_c = K_e = 1 (B3) |
|---|---|---|
| `fd`, mean-T viscosity | 21.4 % | 44.3 % |
| `fd` + wall viscosity | 15.8 % (bias −12 %) | 14.4 % (+14 %) |
| `MY` apparent + wall viscosity | **9.7 %** (bias +0.5 %) | 26.7 % (+27 %) |
| `hagenbach` + wall viscosity | 9.8 % | 26.0 % |

**Selected (now the `Models` defaults):** `MY_3` + axial conduction + wall-viscosity correction, `MY` apparent friction, thermocouple MAPE 4.6 % (4.61 % after the recheck status change) (both heat fluxes, `figures/validation_parity.png`), ΔP MAPE 9.7 %. Both are inside the proposal's 10–15 % target. `LG_3` gives the same thermal accuracy and is fully sourced (Eq. 15 of Lee & Garimella); `MY_3` was chosen because the paper's inlet is a uniform velocity (simultaneously developing flow) and because MY has no aspect-ratio limit, while the 1 kW design (H/w_c = 15–30) is outside LG's fitted range 1–10.

What the matrix shows:
1. **The fully developed assumption fails** (49 %): the thermal entry region covers much of the channel and the inlet h is several times the fully developed value. This is the proposal's stated fallback, now confirmed.
2. Three-sided heating (adiabatic lid) is worth 3–5 points; axial conduction in the 5.6 mm copper base 2–3 points (mainly TC1, near the inlet); the wall-viscosity correction 3–4 points thermally and is essential for ΔP (walls 20–40 K above the water).
3. **ΔP is not fully explained.** The best agreement leaves out the plenum contraction/expansion losses, which must be positive. With the paper's "close to unity" K values the model over-predicts by 27 %, and so does the paper's own 3D model in its Fig. 4(b) by roughly 5–30 % (visual reading, not digitized). The residual has a Re trend (model above the data at mid Re, below at Re > 1300). Candidate causes, not resolved: the K values and plenum geometry (not given), the property-ratio exponent 0.58 (from fully developed flow) applied in the entrance region, and the 4 % rotameter uncertainty. For the 1 kW study this matters through the ΔP constraint and the pumping term; Study 4's K sensitivity covers it.
4. Remaining thermal bias pattern: TC1 at 200 W/cm² is under-predicted by up to about 8 % at low Re. Entrance conduction and spreading in the real 3D copper block are the likely cause.

## Status

Digitized, compared and rechecked (above; `data/raw/recheck_log.md`). Geometry, conditions and sensors verified against the PDF (outlet pressure not reported). Independent hand check of 24 points done (all within 1 % of the axis span; `data/raw/recheck_log.md`).
