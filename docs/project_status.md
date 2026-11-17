# Project status

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
