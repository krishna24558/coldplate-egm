# Project status

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
| D7 | Ẇ_pump in CV-L | Implemented as V̇ΔP/η (pump inside CV); switch with `Losses.pump_inside_cv`. State it in the report. |
| D8 | Lower manufacturing bound | Lost-work optimum sits at w_c = w_f = 0.1 mm; the result depends on that bound. Justify 0.1 mm or show the trend below it. |

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

## Next task

1. **Hard check of the digitized data** (person): open `validation/data/raw/fig4a_overlay.png`, `fig5_overlay.png`, `fig6a_overlay.png`, `fig6b_overlay.png`; every marker should carry one circle in its shape colour (square red, diamond green, up-triangle blue, down-triangle orange); magenta boxes are partly hidden repeat markers. Spot-check 5–10 values per figure in the browser WebPlotDigitizer. Record the check in `validation/README.md`.
2. Verify the geometry/conditions CSVs against the PDF and set `verified_against_pdf = yes`.
3. Check the Kays & Crawford property-ratio exponents in the original table (now quoted via the `ht` library).
4. Report: use `figures/validation_vs_Re.png` and `figures/validation_parity.png`; state the ΔP limitation (D5).
5. D8 (0.1 mm bound) and D7 remain open for the report.
