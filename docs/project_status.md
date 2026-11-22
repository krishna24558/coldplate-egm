# Project status

**Update 2026-11-22 (Phase 2 figures finished; parity figure; flow-cap study).** No physics, model, data or report text changed; `coldplate/` untouched, so tests were not run. Not committed.

- **Seven figures made** by `analysis/make_report_figures.py` (new `fig_B` … `fig_I` plus shared schematic helpers; 200 dpi, same fonts/inks/term colours and hatches as the J/H figures; each checked by eye and in grayscale). All 13 report figures now regenerate in one run (`python analysis/make_report_figures.py`); the six existing J/H files came out byte-identical (md5).
  - `figures/fig_B_network.png` (Fig. 3): (a) one station: cross-section with the nodes T_dev, T_b, T_cf, T_f and the chain R_TIM (Q R_TIM = 20 K, lumped on max T_b), base (q″t_b/k_s = 2.85 K), convection 1/(G′Δx); (b) the ladder along x (stations 1, i, i+1, n; axial conduction between T_cf nodes, adiabatic ends, flow between T_f nodes, q′Δx into each T_b node) with the 41 design-case station positions drawn to scale (`thermal.stations`).
  - `figures/fig_C_control_volumes.png` (Fig. 4): loop with device/TIM, cold plate, pump, cooler, reservoir at T_in; CV-P dotted, CV-C dashed, CV-L dash-dot; loss terms tagged where they are destroyed (X_gap in the cold plate, X_pump at the pump, X_warm at the cooler); key with Eqs. 17, 18, 20 and the Eq. (26) link at 2 L/min from `study1_flow_sweep.csv`: 11.75 + 36.57 + 0.35 = 48.66 W; 36.97 + 11.34 + 0.35 = 48.66 W (closure asserted in the script).
  - `figures/fig_D_code_structure.png` (Fig. 5): config → [model.evaluate: geometry → correlations → hydraulic ⇄ thermal (Re, μ_fric) → second_law] → Result → optimize / benchmark → analysis / validation scripts; properties.py and validation/data as side inputs; arrows labelled with what is passed.
  - `figures/fig_E_solver_flowchart.png` (Fig. 6): evaluate() loop as coded: first guess, property iteration (properties → hydraulic → thermal → convergence test 10⁻⁶ K and 10⁻⁶ ΔP, 3 iterations for the reference design, at most 50), the fixed 4 wall-viscosity passes (no convergence test), P_out < 10 kPa error, second law, margins.
  - `figures/fig_F_benchmark_setup.png` (Fig. 8): (a) section along the channel, x to scale (TC1–TC4 at 5.000 / 16.588 / 28.176 / 39.764 mm), depth dimensioned (713 µm, d = 2.462 mm, H_th 3.175 mm, H_w2 5.637 mm = t_ax), cover, plenums with P and T sensors; heater layout and plenum shape drawn schematically and labelled so (not reported in the paper); (b) cross-section to scale; inputs and B1–B5; (c) table sensor → model quantity → MAPE (from `validation/results/*.csv`: 4.6 % TC, 157 points; ΔP 9.7 % / 26.7 % with K = 1, 39 points; water rise 2.8 %).
  - `figures/fig_G_data_extraction.png` (Fig. 9): (a) original Fig. 6(a) from the PDF next to (b) `fig6a_overlay.png`, the four calibration points ringed (x₁ Re 200, x₂ Re 1600, y₁ 20 K, y₂ 80 K from `fig6a_meta.json`); (c, d) the same zoom showing partly hidden repeat markers; (e) the calibrated values of `fig6a_points.csv` (114 markers, 14 partly hidden); a strip with the pipeline steps of the Figure 9 caption. PyMuPDF and pdftoppm are not installed, so the script decodes the page-9 CCITT G4 scan itself (Pillow) and places it by its PDF matrix; it matches the digitizer's pdftoppm render pixel for pixel (mean difference 0.000 on all grey overlay pixels, asserted on every run).
  - `figures/fig_I_local_Nu.png` (Fig. 7): local Nu(x) from `coldplate.correlations.local_nusselt` for fd_H1, LG_3, MY_3 in the Qu & Mudawar channel, 100 W/cm², Re = 900, Pr = 6.95 (CoolProp at the 20.3 °C mean water temperature of that run; constant properties, no wall-viscosity correction). At TC1: MY_3 11.0, LG_3 10.5, fd_H1 4.85 (2.3× / 2.2×); at the outlet 6.25 / 6.17 (1.29×). Lee–Garimella thermal entry length (Eq. 11) 92 mm against L = 44.8 mm: the whole channel is thermally developing. The fd_H1_3 reference line is 5.27, above fd_H1 (4.85) at this aspect ratio, as coded (the Shah & London fits are still unchecked in the original, section 7.7).
- **`figures/validation_parity.png` regenerated** (`validation/run_validation.py --skip-matrix --plots MY_3 1 MY 0 1`, 4 min 40 s). The title code already used `MAPE_TC`, so the script was not changed. Titles now: pressure drop 9.7 %, thermocouples **4.6 %** (current data, 156 points: 4.61 %). The thermocouple axes now read "K above inlet" (the old file said °C over the same values, which are rises above the inlet). **Cause of the old 4.3 % found:** one `compare()` run with the same model gives MAPE_TC 4.61 % (156 points), water rise 2.84 % (38 points) and their pooled mean `MAPE_thermal` **4.26 %**; the old title pooled the water-rise points with the thermocouples. ΔP 9.72 % (39 points). The file is still 150 dpi in the script's default style (not restyled).
- **Flow-cap study** (`python analysis/run_phase1_checks.py cap`, new part `flow_cap()`; 1.5–2.5 min): Study 2 lost-work optimization with V̇ ≤ 2 L/min, same procedure as the other Phase 1 optima (grid without the flows above the cap, SLSQP, widths snapped to 1 nm, whole-channel flow polish; the cap is the upper flow bound in all three steps). Output `analysis/results/phase1_flow_cap.csv` (unconstrained row copied from `phase1_pump_cv.csv`, not rerun).

| | No flow cap | V̇ ≤ 2 L/min |
|---|---|---|
| w_c / w_f (mm), N | 0.100 / 0.100, 150 | 0.100 / 0.100, 150 |
| V̇ (L/min), Re | 3.17, 298 | 2.00, 193 |
| ΔP (kPa) | 32.89 | 19.86 |
| T_dev (°C) | 61.57 | 64.07 |
| X_warm / X_gap / X_pump (W) | 7.40 / 22.52 / 3.42 | 11.71 / 22.35 / 1.30 |
| X_lost (W) | 33.34 | **35.37 (+2.03 W, +6.1 %)** |
| W_hyd (W) [W_elec] | 1.74 [3.48] | 0.66 [1.33] |
| Active | w_c, w_f bounds | flow cap, w_c, w_f bounds |

  The cap is active and the geometry does not move (both widths stay on the 0.1 mm bound; the best grid point was already 0.1/0.1 mm at 2 L/min and SLSQP stayed there). Capping the flow costs 6.1 % lost work: the warming term rises by 4.3 W (it depends almost only on flow, ≈ B/V̇), pumping falls by 2.1 W, the gap term hardly changes. Hydraulic power falls 62 % and T_dev rises 2.5 K. Against the min-R_th design (37.39 W, W_hyd 4.72 W, 60.17 °C) the capped design still has 5.4 % less lost work and 86 % less hydraulic power, for +3.90 K.
- **Choices made without asking:** fig_C draws the device/TIM apart from the base ("interface drawn open") so the three boundaries do not overlap, places X_warm at the cooler (Eq. 26, section 9.4) and gives no CV-P number (none in any CSV); fig_D draws model.py as a container around the modules evaluate() calls; fig_F quotes the 157-point matrix MAPE (the post-recheck 156-point value is 4.61 %); fig_G adds the zooms, the calibrated-value panel and the pipeline strip so the figure matches its caption; fig_I uses Re = 900 as the channel Re with Pr from the energy balance (inlet-defined Re, B1), adds the fd_H1_3 line, the z* top axis and TC1–TC4; the flow-cap CSV flags width bounds and the cap in `active_constraint`.
- **Report text to change (not edited):** (1) delete the "*(Figure not made yet …)*" notes in the captions of Figures 3–9 and the whole "Figures still to be made" section (all 13 exist now); (2) Figure 11 caption: "thermocouple temperatures in °C (right)" → "thermocouple temperature rise above the inlet, K (right)", and replace the last paragraph of section 8.2 (the 4.3 % inconsistency) with the explanation above; (3) Figure 7 caption: name the three models as plotted (fd_H1, LG_3, MY_3) and the condition (Qu & Mudawar channel, 100 W/cm², Re 900, Pr 6.95); section 6.1 could quote the 2.3× at TC1 and the 92 mm entry length; (4) Figure 8 caption: "… and the model quantity compared with each sensor"; Figure 9 caption: "(a) original, (b) overlay, (c, d) zoom, (e) calibrated values; Fig. 6(a) shown"; (5) optional: a sentence in 6.2 that the three-wall fully developed Nu (5.27) is above the four-wall value (4.85) at the benchmark aspect ratio, so a reader is not surprised by Figure 7; (6) the flow-cap result could go in section 10.5 as a short extra check.
- **Next:** report text (the changes above, section 11, abstract, appendices); the open items below are unchanged.

**Update 2026-11-20 (Phase 2 figures): six report figures made by the new script `analysis/make_report_figures.py` (reads only the CSVs in `analysis/results/` and `validation/results/`; no model run, no study rerun, no package/data/report change; tests not run since no package code changed): `figures/fig_J2_designs.png` (Fig. 14), `fig_J1_flow_sweep.png` (Fig. 13), `fig_J3_inlet_temperature.png` (Fig. 15), `fig_J5_below_limit.png` (Fig. 17), `fig_J4_sensitivity.png` (Fig. 16), `fig_H_model_mape.png` (Fig. 12). 200 dpi, one shared style (same colour + line style + marker/hatch for each lost-work term in J1, J2, J5; one limit-line style), checked in grayscale. Every number on them was recomputed independently from the CSVs and matches Tables 6, 7, 17–21. Baseline / optimum for J1 and J4 is the reference-geometry row of `phase1_pump_cv.csv` (5.13 L/min, 43.05 W, 64.87 °C; Eq. (21) 4.77 L/min). Choices made without asking: J1 shades the infeasible flows from Re = 2000, at 11.37 L/min by linear interpolation in the Study 1 CSV (the CSV itself only says 11.0 feasible, 11.5 not); J2 (c) draws T_dev bars from the 30 °C inlet; `fig_H` also has a pressure-drop panel from `dP_model_matrix.csv`, because the Figure 12 caption and section 8.3 say "thermocouple and pressure-drop MAPE" (Tables 6 and 7). Old drafts `figures/study1_flow_sweep.png` and `study3_inlet_temperature.png` are superseded but left in place. **Report text to change (not edited):** (1) delete the "*(Figure not made yet …)*" notes in the captions of Figures 12–17 and those six rows of "Figures still to be made" (the two draft-file mentions go with them); (2) optional caption additions so the text names what the figures show: Fig. 12 "(b) pressure drop computed with the selected thermal model `MY_3` + axial conduction; shaded band: the proposal's 10–15 % target", Fig. 13 "shaded: Re > 2000 and ΔP > 50 kPa (infeasible)", Fig. 15 "shaded: no feasible optimum (57.5 °C and above); open circle: 57.5 °C needs 13.5 L/min, Re 3834; cross: floor 90.33 °C at 60 °C", Fig. 17 "star: free optimum with 0.05 mm bounds (w_c 0.069, w_f 0.050 mm)", Fig. 14 "T_dev bars start at the 30 °C inlet"; (3) minor, not a figure issue: Table 19 gives 5.14 L/min at 30 °C while Study 1 / Table 20 give 5.13 L/min for the same case (separate optimizer runs, 5.137 vs 5.132 L/min, 0.1 %). No figure disagrees with sections 9 or 10. Next: the remaining figures (B, C, D, E, F, G, I) and regenerating `validation_parity.png` (its 4.3 % title, section 8.2).**

**Update 2026-11-20: `docs/final_report.md` sections 9 (second law, Eqs. 23–28), 10 (Studies 1–4 + Phase 1, Tables 17–22, Figs. 13–17 = fig_J1–J5, not made yet), 12 (conclusions) and 13 (limitations, future work) written from the CSVs; no code/data changed, tests not run. Next: section 11 (code structure), abstract, appendices A–C, then Phase 2 figures. Two small inconsistencies to fix: section 6.6 says the CV-C minimum is "near 1–2 L/min" (the CSV is flat within 0.5 % from 0.5 to 4.5 L/min, lowest at 0.75); Table 2 says Study 3 covers 20–55 °C (it runs 20–60 °C).**

**Update 2026-11-16: Phase 1 technical work finished (D8 trend, D7, D5, fully developed comparison, numerical checks, digitizing uncertainty, headline results). See "Phase 1 results" below; tests 50 passed, 1 skipped on Windows (digitizer test needs Node.js).**

Last updated: 2026-11-08, second session (developing-flow and three-sided correlations coded and checked against tabulated data; local-h thermal solver with optional axial conduction; headless WebPlotDigitizer pipeline; validation matrix script). **Qu & Mudawar Figs. 4(a), 5, 6 digitized and compared; developing-flow models selected and made the defaults (D4 closed). Awaiting a person's hard check of the digitized points.**

## Repository state

- Local checkout: `C:\Users\komin\OneDrive\Desktop\projects\coldplate-egm`, branch `main`, 1 commit: `db62fe6` (initial structure). `.venv` exists.
- **Clean-up needed:** a nested duplicate folder `coldplate-egm/coldplate-egm/` (with its own `.git`) exists from unzipping into the repo. It holds no unique work. Delete it before committing, or Git will treat it as an embedded repository.
- **No Git remote configured** locally. The proposal links https://github.com/krishna24558/coldplate-egm: `git remote add origin https://github.com/krishna24558/coldplate-egm.git` (if GitHub already has commits, `git pull origin main --allow-unrelated-histories` first).
- The 2026-11-08 implementation was delivered as a zip of the whole repository (no `.git`). Nothing is committed yet.

## Test result

`python -m pytest -q` → **51 passed** (second session; was 25; about 4 min because `tests/test_validation_qm.py` runs the benchmark) (Python 3.13, CoolProp 8.0.0, NumPy 2.5.3, SciPy 1.18.1), 2026-11-08, Linux workspace. **Not yet run on Windows:** `.\.venv\Scripts\python.exe -m pytest -q`, then record the result here.

Tests cover: properties vs reference values; geometry and correlation limits; Poiseuille parallel-plate limit for friction; dP scaling (friction ∝ V̇, minor ∝ V̇²); fin-efficiency limits; energy balance; temperature ordering; device-temperature floor; S_gen > 0 over a flow sweep; CV-L terms sum to the closed form; CV-C mean-temperature approximation and split within 1 % of the exact value; flow exergy zero at the dead state; interior flow optimum within 20 % of (B/2C)^(1/3); CV-C alone has no interior optimum; benchmark loads; Re definition reproduces the paper's stated flow rates; benchmark trends; min-R_th design feasible.

## What works

| Module | Contents |
|---|---|
| `config.py` | 1 kW case dataclasses, `Case` bundle, `lpm()` / `to_lpm()`. `Losses.pump_inside_cv` encodes D7 (default True). `Models` (Nu, friction, axial conduction; defaults fully developed). `Geometry.t_ax`. |
| `properties.py` | CoolProp wrappers. |
| `geometry.py` | N, D_h, α, areas; `integer=False` (fractional N for the optimizer) and `N_override` (benchmark). |
| `correlations.py` | Nu models `fd_H1`, `fd_H1_3`, `LG`, `LG_3`, `MY`, `MY_3` (local Nu_x) and friction models `fd`, `MY`, `hagenbach` (apparent fRe); `local_nusselt()`, `apparent_fRe()`; `entry_lengths()` incl. Lee & Garimella z*_th. Sources and checks: equation sheet Section 1b. |
| `hydraulic.py` | Friction + minor losses, Re, W_hyd = V̇ΔP, W_elec = V̇ΔP/η. |
| `thermal.py` | Station-by-station network with local h(x), η_f(x); optional base axial conduction (coupled FV solve, A14); T_f(x), T_cf(x), T_b(x) via CoolProp enthalpy; lumped Nu, h, R_conv reported as length means; `temperature_below_channels()`. |
| `second_law.py` | CV-C exact (∫q/T_b) and mean-T approximation with split; CV-L objective with warming / gap / pumping terms; CV-P (TIM) separate; lost work; flow exergy and X_out. |
| `model.py` | `evaluate(case)`: coupled iteration of properties, ΔP and T_out; constraint margins and feasibility; `Result.summary()` in report units. |
| `optimize.py` | Study 1 `flow_sweep`, `optimum_flow` (with B, C, analytical V̇*); Study 2 `grid_sweep`, `optimize_design` (SLSQP, fractional N, then flow re-tuned with whole channels), `compare_designs`; Study 3 helper. Objectives: lost_work, thermal_resistance, hydraulic_power. |
| `benchmark.py` | Builds the Qu & Mudawar case from `validation/data/*.csv` only; `flow_from_reynolds`, `predict` (plenum-to-plenum ΔP, TC1–TC4 temperatures, water ΔT); `compare()` computes MAPE once digitized data exist. Warns while values are unverified. |
| `analysis/run_studies.py` | Runs Studies 1–4, writes `analysis/results/*.csv` and `figures/*.png`. |

## Model output (validated models: MY_3 + axial conduction + wall viscosity, MY friction)

Benchmark (validation/README.md "Results"): thermocouple MAPE 4.6 % (157 points, bias +0.7 %), water ΔT 2.8 %, ΔP 9.7 % (39 points, without plenum losses; 27 % with K = 1). The proposal's fully developed model gave 49 % (thermal) and 44 % (ΔP).

1 kW case (`analysis/run_studies.py`, 2026-11-08 with the new defaults; previous fully developed numbers in brackets):
- Reference design (0.2/0.2 mm, 2 L/min, 30 °C): T_dev 69.0 °C [70.5], ΔP 5.3 kPa [5.6], X_lost 48.7 W [52.3] (warming 11.7, gap 36.6, pumping 0.35).
- Study 1: lost-work optimum 5.13 L/min [4.53], analytical (B/2C)^(1/3) 4.77 L/min; X_warm/X_pump = 1.62 [2.43]. With developing flow h rises with velocity, so the gap term also falls with flow and the optimum moves to higher flow than the constant-h estimate.
- Study 2: min lost work at the 0.1 mm bounds, 3.17 L/min, X_lost 33.3 W, W_hyd 1.74 W, T_dev 61.6 °C. Min R_th: w_c 0.110 mm, 5.66 L/min, ΔP at 50 kPa, W_hyd 4.72 W, T_dev 60.2 °C, X_lost 37.4 W. Second-law design: 63 % less hydraulic power and 11 % less lost work for 1.4 K higher T_dev.
- Study 3: entropy optimum feasible up to T_in = 55 °C [52.5]; device limit governs from 57.5 °C.
- Study 4: R_TIM moves T_dev ±10 K, not the optimum; η_pump 0.3–0.7 moves V̇* 4.3–5.8 L/min; plenum K 0–3 moves V̇* 5.6–4.8 L/min.
- CV-C entropy generation is now almost flat with flow (0.1237–0.1294 W/K for 1–8 L/min), with a shallow minimum near 1–2 L/min; CV-L is still the objective.

## Benchmark: one text-stated point checked

The paper states (Sec. 3.2) a measured ΔP of 0.86 bar at 100 W/cm², Re = 1672. Model: 1.03 bar with K_c = K_e = 1.0 (+19 %), 0.73 bar with friction only (−15 %). The minor-loss treatment (B3) is the main uncertainty. Not tuned; one point is not a validation.

## Known issues and limitations

- Developing flow and three-sided heating are now modelled (D4 closed). The 1 kW geometry (H/w_c = 15–30) is outside the benchmark's aspect ratio (3.1); MY has no aspect-ratio limit, but this is an extrapolation of the validation.
- ΔP plenum losses unresolved (D5).
- K_c, K_e unsourced (A8); benchmark uses 1.0 each (B3).
- Correlation coefficients not yet checked against the original Shah & London text.
- Benchmark inputs extracted automatically from the PDF text and not yet verified by a person.
- Optimizer: N is fractional during SLSQP; the reported design is re-evaluated with whole channels and its flow re-tuned.

## Decisions

The submitted proposal (`docs/proposal_submitted.md`) settles D1–D3:

| ID | Decision | Resolved by proposal |
|---|---|---|
| D1 | Entropy control volume | **CV-L** (objective); CV-C computed as a diagnostic. |
| D2 | Comparison design | **Minimum thermal resistance**; minimum hydraulic power also computed. |
| D3 | Fin thickness | **Design variable**, 0.1–0.5 mm. |
| D4 | Developing flow / three-sided heating | **Closed 2026-11-08 by the benchmark:** `MY_3` + axial conduction + wall-viscosity correction, `MY` friction (validation/README.md). `LG_3` equally good thermally. |

Still open:

| ID | Decision | Notes |
|---|---|---|

| D5 | Minor losses | Eq. 18–22 transcribed: no K values or plenum dimensions are given. Data agree best with no plenum losses (9.7 %) and the paper's K≈1 over-predicts by 27 %. Unresolved; treat K as a sensitivity (Study 4). The 1 kW case keeps K_c = 0.5, K_e = 1.0. |
| D6 | Sources for R_TIM, T_dev,max, η_pump | or label as assumptions in the report. |
| D7 | Ẇ_pump in CV-L | Implemented as V̇ΔP/η (pump inside CV, default); switch with `Losses.pump_inside_cv`. **Quantified 2026-11-16** (Phase 1 section 2): outside gives the same geometry, 26 % more flow, pumping saving 41 % instead of 63 %. State it in the report. |
| D8 | Lower manufacturing bound | **Quantified 2026-11-16** (Phase 1 section 1, Study 5): the optimum at 0.1 mm is set by the manufacturing bound, not the ΔP limit; going to 0.05 mm bounds gains at most about 6 % lost work. |

## Schedule (proposal dates)

Model and tests by Nov 3 (done Nov 8, late), validation and second-law module by Nov 12, studies by Nov 22, report and code by Dec 3.

## Session log 2026-11-08 (second session)

- Literature: Lee & Garimella (2006) Eqs. 11–13, 15, 16; Muzychka & Yovanovich (2004) Eqs. 21, 22, 42–47; Shah & London apparent friction table and Hagenbach K(∞) (via Duan & Ma 2020); Wibulswas Nu_x table (via Lee et al. 2005). Lost minus signs in the PDF text were resolved by numerical checks, not guessed (equation sheet 1b).
- Qu & Mudawar text re-read: uniform inlet velocity in their simulation; variable viscosity; K values "close to unity" with no source; no plenum dimensions.
- Benchmark predictions now differ strongly by model: at 100 W/cm², Re 1672, TC1 is 57.5 °C (fd_H1) vs 35–36 °C (developing). The figures will discriminate.
- ΔP at the text-stated point (0.86 bar): fd + K = 1.03, fd only 0.73, MY only 0.91, MY + K 1.21 bar.
- 1 kW case: developing models move T_dev by < 0.7 K (outlet nearly developed) and X_lost by 3–6 %.
- Tests: 45 passed (Linux).
- After the PDF arrived: digitized Figs. 4(a), 5, 6(a), 6(b) (headless WebPlotDigitizer calibration + blob detection, template matching for overlapping markers; `validation/digitize/`); compared 24 thermal and 12 friction combinations; added the wall-viscosity correction (A10), which was needed for ΔP; made the selected models the defaults; reran the studies. Tests: 51 passed (about 4 min; the validation tests run the benchmark).


## Added 2026-11-13 to 2026-11-16 (outside Claude Code)

- Data recheck: `validation/data/raw/recheck_log.md` (no values changed; one status corrected; geometry/conditions/sensors `verified_against_pdf = yes`).
- Geometry figures: `figures/geometry_3d_design.png`, `figures/geometry_design_vs_qm.png` (script `analysis/make_geometry_figures.py`).
- `docs/design_case_justification.md`: design values vs published cold plates (with references), and why the benchmark validates the design case (dimensionless comparison; the aspect ratio H/w_c = 15 vs 3.1 is an extrapolation).
- `docs/team_tasks.md`: Suneel (hand check of digitized data, introduction background), Sam (hand calculation of the reference design, presentation outline). Not on the critical path.
- `docs/claude_code_plan.md`: phased plan for finishing the project in Claude Code (Phase 1 technical work, Phase 2 figures, Phase 3 report, Phase 4 wrap-up).
- Resume entry uses "60 % less pumping power" (rounded down from 63 %); update if Phase 1 changes the Study 2 numbers.

## Phase 1 results (2026-11-16, Claude Code session)

Physics, default models and digitized data unchanged; `validation/run_validation.py` not rerun. Tests at session start: see the end of this section. New scripts: Study 5 in `analysis/run_studies.py` (`--only N` runs one study), and `analysis/run_phase1_checks.py` (parts `d7 d5 fd num digit`). Choices made without asking are marked *(choice)*.

### 1. D8: trend below the 0.1 mm bound (`analysis/results/study5_below_limit.csv`)

w_c = w_f, each at its own lost-work optimum flow, same T_dev / ΔP / Re limits. *(choice)* the manufacturing bound is lowered to 0.05 mm for this study only; "free" is the optimum flow with no constraints.

| w_c = w_f (mm) | V̇ (L/min) | free V̇ | ΔP (kPa) | T_dev (°C) | X_lost (W) | W_hyd (W) | Re | Active limit |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 1.32 | 2.03 | 50.0 | 65.5 | 35.14 | 1.10 | 67 | ΔP |
| 0.075 | 2.64 | 2.64 | 47.3 | 61.3 | 32.03 | 2.08 | 189 | none |
| 0.10 | 3.17 | 3.17 | 32.9 | 61.6 | 33.34 | 1.74 | 298 | none |
| 0.15 | 4.12 | 4.12 | 20.8 | 62.9 | 37.78 | 1.43 | 565 | none |
| 0.20 | 5.13 | 5.13 | 16.9 | 64.9 | 43.05 | 1.44 | 917 | none |
| free geometry, 0.05 mm bounds: w_c 0.069, w_f 0.050 | 2.63 | – | 47.7 | 61.1 | 31.28 | 2.09 | 150 | none (w_f at its bound) |

**Answer to D8:** inside the proposal's range the lost-work optimum is set by the **manufacturing bound**, not by the ΔP limit (ΔP is 32.9 kPa of the 50 kPa allowed at 0.1 mm; no other limit is active). Below the bound the gain is small: about 4 % less lost work at 0.075 mm and about 6 % with free geometry (w_c 0.069 mm), where the optimum in w_c becomes interior. The ΔP limit only takes over near 0.05 mm, where it cuts the flow from 2.03 to 1.32 L/min and lost work rises again. So 0.1 mm costs at most about 6 % of lost work against a 0.05 mm process. Caveat: H/w_c is 30–60 here, far outside the benchmark's 3.1 (extrapolation), and 0.05 mm × 3 mm fins are not a realistic skived fin.

### 2. D7: pump inside or outside CV-L (`analysis/results/phase1_pump_cv.csv`)

Design optima by the Study 2 procedure (same grid, SLSQP, whole channels). "Inside" (Ẇ_pump = V̇ΔP/η, η = 0.5) **stays the default**; "outside" uses Ẇ_pump = V̇ΔP. The min-R_th design does not depend on this choice; only its X_lost does.

| | Pump inside (default) | Pump outside |
|---|---|---|
| Reference geometry: optimum flow (L/min) / X_lost (W) | 5.13 / 43.05 | 6.61 / 41.19 |
| Min lost work: w_c / w_f (mm) | 0.100 / 0.100 | 0.100 / 0.100 |
| Min lost work: flow (L/min) | 3.17 | 3.98 |
| Min lost work: ΔP (kPa) | 32.9 | 42.2 |
| Min lost work: T_dev (°C) | 61.57 | 60.70 |
| Min lost work: W_hyd / W_elec (W) | 1.74 / 3.48 | 2.80 / 5.61 |
| Min lost work: X_lost (W) | 33.34 | 31.21 |
| Min R_th (0.110 / 0.100 mm, 5.66 L/min, ΔP 50 kPa, 60.17 °C, W_hyd 4.72 W): X_lost (W) | 37.39 | 32.74 |
| **Pumping-power saving vs min R_th** | **63.2 %** | **40.6 %** |
| Lost-work saving vs min R_th | 10.8 % | 4.7 % |
| T_dev penalty vs min R_th (K) | +1.40 | +0.53 |

The geometry of the optimum does not change (both at the 0.1 mm bounds, no other limit active). With the pump outside, pumping is charged at half the price, so the optimum flow rises 26–29 % and the two designs move closer: the pumping-power saving falls from 63 % to 41 %. The headline saving therefore depends on D7 and on η_pump = 0.5 (assumed, A9); state both next to it.

### 3. D5: plenum-loss coefficient (`analysis/results/phase1_plenum_K.csv`)

New runs (Study 4 only varied the flow at the reference geometry). K = 1.5 is the default (K_c 0.5, K_e 1.0); *(choice)* 0 and 3 are split equally, as in Study 4 (only the sum enters, at channel velocity).

| K_c + K_e | Ref. geometry V̇* (L/min) / X_lost (W) | Min lost work: w_c/w_f (mm), V̇ (L/min), ΔP (kPa), T_dev (°C), X_lost (W), W_hyd (W) | Min R_th: w_c (mm), V̇, T_dev, W_hyd | W_hyd saving | X_lost saving | ΔT_dev (K) |
|---|---|---|---|---|---|---|
| 0 | 5.63 / 42.53 | 0.100/0.100, 3.22, 32.4, 61.51, 33.23, 1.74 | 0.111, 6.15, 60.01, 5.13 | 66.1 % | 12.3 % | +1.50 |
| 1.5 | 5.13 / 43.05 | 0.100/0.100, 3.17, 32.9, 61.57, 33.34, 1.74 | 0.110, 5.66, 60.17, 4.72 | 63.2 % | 10.8 % | +1.40 |
| 3 | 4.80 / 43.46 | 0.100/0.100, 3.12, 33.4, 61.63, 33.45, 1.74 | 0.109, 5.35, 60.27, 4.46 | 61.0 % | 9.6 % | +1.37 |

The lost-work optimum is insensitive to K: same geometry, flow within ±1.5 %, X_lost within ±0.3 %, T_dev within ±0.06 K (its channel velocity is low, so minor losses are a small part of its ΔP). The min-R_th design sits on the ΔP limit, so K changes its flow (5.35–6.15 L/min) and with it the pumping-power saving, 61–66 %. D5 stays unresolved as physics, but it does not change the design conclusion.

Implementation note: SLSQP returns a width at its bound as 0.1000000000028 mm, which drops the whole-channel count from 150 to 149 and changes X_lost by 0.3 % (33.45 instead of 33.34 W). `run_phase1_checks.py` snaps widths to 1 nm and re-tunes the flow. `optimize.optimize_design` was not changed; Study 2 as run on 2026-11-08 has N = 150.

### 4. Validated model vs the proposal's fully developed model, 1 kW case (`analysis/results/phase1_fd_vs_validated.csv`)

Validated = `MY_3` + axial conduction + wall viscosity, `MY` friction. Proposal = `Models("fd_H1","fd",False,False)`.

| Quantity | Validated | Fully developed | Difference (fd − validated) |
|---|---|---|---|
| Reference design, 2 L/min: T_dev (°C) | 69.02 | 70.51 | +1.49 K |
| Reference design: ΔP (kPa) | 5.32 | 5.57 | +4.7 % |
| Reference design: X_lost (W) | 48.66 | 52.28 | +7.4 % |
| Reference geometry: optimum flow (L/min) | 5.13 | 4.53 | −11.8 % |
| at that optimum: T_dev (°C) / ΔP (kPa) / X_lost (W) | 64.87 / 16.86 / 43.05 | 66.52 / 14.25 / 48.26 | +1.65 K / −15.5 % / +12.1 % |
| at that optimum: X_warm / X_pump (theory 2) | 1.62 | 2.43 | – |
| Min lost-work design: w_c / w_f (mm) | 0.100 / 0.100 | 0.100 / 0.100 | same |
| Min lost-work design: flow (L/min) | 3.17 | 3.10 | −2.1 % |
| Min lost-work design: T_dev (°C) / ΔP (kPa) / X_lost (W) | 61.57 / 32.89 / 33.34 | 62.32 / 33.09 / 34.73 | +0.75 K / +0.6 % / +4.2 % |
| Pumping-power / lost-work saving vs min R_th | 63.2 % / 10.8 % | 63.8 % / 11.2 % | – |

On the 1 kW case the two models differ by 1.5 K and 4–12 % at the reference geometry and by less at the optimum design, and both give the same optimum geometry and the same savings, although on the benchmark they differ strongly (thermocouple MAPE 4.6 % vs 49 %). Reason: the design channels are narrow and long in z* terms, so the outlet is close to fully developed. The design conclusions are robust to the correlation choice.

### 5. Numerical checks (`analysis/results/phase1_numerical_checks.csv`)

| Check | n_x = 21 | 41 (default) | 81 | 41 → 81 change |
|---|---|---|---|---|
| 1 kW reference: T_dev (°C) | 69.052 | 69.017 | 69.008 | −0.010 K |
| 1 kW reference: ΔP (kPa) | 5.3224 | 5.3220 | 5.3218 | −0.003 % |
| 1 kW reference: X_lost (W) | 48.642 | 48.660 | 48.668 | +0.016 % |
| Qu & Mudawar 100 W/cm², Re 1672: TC1 (°C) | 33.716 | 33.762 | 33.783 | +0.022 K |
| same: TC4 (°C) | 47.450 | 47.465 | 47.464 | −0.0003 K |
| same: friction ΔP (kPa) | 72.773 | 72.753 | 72.744 | −0.011 % |

- Grid: the default grids (41 for the 1 kW case, 61 for the benchmark, 21 inside the optimizer) are converged to about 0.01–0.05 K and 0.05 % or better; that is far below the 4.6 % validation error.
- Energy balance (1 kW reference): ṁ(h_out − h_in)/Q − 1 = 3 × 10⁻¹¹; ∫q_conv dx/Q − 1 ≤ 2 × 10⁻¹³ for all three grids. Note the solver rescales the convective heat so that the fluid receives exactly Q, so this closure holds by construction; it confirms the implementation, it is not an independent check.
- Property iteration (T_out, ΔP, properties): converges in 3 iterations at tol 10⁻⁶ K; with tol 10⁻¹⁰ (9 iterations) T_dev is unchanged to 8 decimals, ΔP changes by 2 × 10⁻⁸ kPa and X_lost by 10⁻⁸ W.
- Not checked: the wall-viscosity loop in `thermal.py` uses a fixed 4 passes with no convergence test (would need a code change to vary).

### 6. Digitizing uncertainty on the thermocouple MAPE (`analysis/results/phase1_digitizing_uncertainty.csv`)

Selected model, 156 thermocouple points, model run once; each reading shifted by the reading uncertainty in its `notes` column (0.125–0.5 K; `recheck_log.md` found ≤ 0.4 K against an independent reading). The data CSV is not modified.

| Case | Thermocouple MAPE | Bias |
|---|---|---|
| As digitized | 4.61 % | +0.64 % |
| All readings + uncertainty | 4.65 % | −0.23 % |
| All readings − uncertainty | 4.66 % | +1.53 % |
| Independent random shifts within ± uncertainty (2000 draws) | 4.63 % mean, 4.52–4.72 % (95 % range) | – |

The MAPE moves by at most about 0.1 percentage point; the digitizing uncertainty does not affect the validation conclusion. *(choice)* Only the temperature reading was shifted; the Re reading uncertainty (±1.3) was not propagated, since it needs model reruns and is under 1 % of Re.

Side note: `load_benchmark()` warns that 1 benchmark value is unverified. It is the `outlet_or_system_pressure` row (status `missing`, not reported in the paper), not a data problem.

### 7. Headline results (Study 2, `analysis/results/study2_designs.csv`, validated model, pump inside CV-L, η_pump 0.5, K = 1.5)

Lost-work design (w_c = w_f = 0.1 mm, 150 channels) against the minimum-thermal-resistance design (w_c 0.110 mm, w_f 0.1 mm, 142 channels), same constraints, 1 kW, 30 °C inlet:

| | Min lost work | Min R_th | Difference |
|---|---|---|---|
| Optimum flow (L/min) | 3.17 | 5.66 | −44 % |
| ΔP (kPa) | 32.9 | 50.0 (at the limit) | |
| Hydraulic power (W) [pump electricity at η 0.5] | 1.74 [3.48] | 4.72 [9.43] | **−63 % pumping power** |
| Lost work X_lost (W) | 33.34 | 37.38 | **−10.8 % lost work** |
| T_dev (°C) | 61.57 | 60.17 | **+1.40 K** |

- Robustness (sections 1–4 above): saving 61–66 % for K = 0–3; 41 % if the pump is outside the control volume; 64 % with the fully developed model; the 0.1 mm bound sets the optimum and costs at most about 6 % of lost work against 0.05 mm.
- Reference geometry (0.2/0.2 mm): lost-work optimum flow 5.13 L/min (analytical (B/2C)^(1/3) 4.77 L/min).
- The resume line "60 % less pumping power" is still valid (63 %, rounded down).

### Tests (2026-11-16, Windows, Python in `.venv`)

`.\.venv\Scripts\python.exe -m pytest -q`: **50 passed, 1 skipped** at the start (47 min) and again at the end (24 min with `OPENBLAS_NUM_THREADS=1`). Not the expected "51 passed": `tests/test_digitizer.py` is skipped because Node.js is not installed on this machine (`node not installed`). The runtime is far above the 4 min seen on Linux; setting `OPENBLAS_NUM_THREADS=1` halves it (NumPy threads the small dense solves).

### Unverified / open after Phase 1

- The digitizer test did not run here (needs Node.js).
- Wall-viscosity loop convergence (fixed 4 passes) not tested.
- Re reading uncertainty not propagated (section 6).
- All results below w = 0.1 mm and the design case in general are an aspect-ratio extrapolation of the validation.
- D5 (true plenum K) and D6 (sources for R_TIM, T_dev,max, η_pump) remain assumptions; D7 and D8 are now quantified and can be stated in the report.

## Next task

Phase 1 technical work is finished (sections above). Next: Phase 2 figures (`docs/claude_code_plan.md`). Older items:

0. Data recheck done 2026-11-13 (`validation/data/raw/recheck_log.md`): no values changed, one status corrected, geometry/conditions/sensors verified against the PDF; thermocouple MAPE 4.61 %.
1. **Hard check of the digitized data** (person, still recommended): open `validation/data/raw/fig4a_overlay.png`, `fig5_overlay.png`, `fig6a_overlay.png`, `fig6b_overlay.png`; every marker should carry one circle in its shape colour (square red, diamond green, up-triangle blue, down-triangle orange); magenta boxes are partly hidden repeat markers. Spot-check 5–10 values per figure in the browser WebPlotDigitizer. Record the check in `validation/README.md`.
2. ~~Verify the geometry/conditions CSVs against the PDF~~ done in the recheck (outlet pressure is not reported).
3. Check the Kays & Crawford property-ratio exponents in the original table (now quoted via the `ht` library).
4. Report: use `figures/validation_vs_Re.png` and `figures/validation_parity.png`; state the ΔP limitation (D5).
5. D8 (0.1 mm bound) and D7 remain open for the report.
