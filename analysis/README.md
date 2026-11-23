# Analysis

Scripts that produce the design-study results (report section 10) and the report figures. All runs use the validated default models in `coldplate/config.py`: `MY_3` Nusselt number (Muzychka–Yovanovich, simultaneously developing, three heated walls), axial conduction in the base, wall-viscosity correction and `MY` apparent friction (validation: `../validation/README.md`).

| Script | What it does | Writes |
|---|---|---|
| `run_studies.py` | Studies 1–5 on the 1 kW case | `results/study1_…` to `study5_….csv` |
| `run_phase1_checks.py` | robustness checks: parts `d7` (pump inside/outside CV-L), `d5` (plenum K), `fd` (fully developed model), `num` (grid and iteration), `digit` (digitizing uncertainty), `cap` (flow ≤ 2 L/min) | `results/phase1_*.csv` |
| `make_report_figures.py` | report Figures 3–9 and 12–17 from the CSVs, the data files and the code (no study is rerun) | `../figures/fig_*.png` |
| `make_geometry_figures.py` | report Figures 1–2 | `../figures/geometry_*.png` |

Studies (`run_studies.py`):

| Study | What is varied | Results | Report |
|---|---|---|---|
| 1 | flow 0.5–12 L/min at the reference geometry (0.2 / 0.2 mm); lost-work optimum and the (B/2C)^(1/3) check | `results/study1_flow_sweep.csv` | Table 17, Figure 13 (`fig_J1_flow_sweep.png`) |
| 2 | w_c, w_f and flow (grid, SLSQP, whole-channel polish) for minimum lost work, minimum thermal resistance and minimum hydraulic power | `results/study2_designs.csv` | Table 18, Figure 14 (`fig_J2_designs.png`) |
| 3 | inlet temperature 20–60 °C at the reference geometry, lost-work optimum flow under the limits | `results/study3_inlet_temperature.csv` | Table 19, Figure 15 (`fig_J3_inlet_temperature.png`) |
| 4 | R_TIM, pump efficiency, dead state T0, plenum K, one at a time | `results/study4_sensitivity.csv` | Table 20, Figure 16 (`fig_J4_sensitivity.png`) |
| 5 | w_c = w_f from 0.05 to 0.2 mm (below the 0.1 mm bound), plus a free optimum with 0.05 mm bounds | `results/study5_below_limit.csv` | Table 21, Figure 17 (`fig_J5_below_limit.png`) |

Commands (from the repository folder; on Windows set `$env:OPENBLAS_NUM_THREADS=1` first):

    python analysis/run_studies.py              # Studies 1-5
    python analysis/run_studies.py --only 2     # one study
    python analysis/run_studies.py --quick      # coarser Study 2 grid
    python analysis/run_phase1_checks.py        # all Phase 1 parts, or name them: d7 d5 fd num digit cap
    python analysis/make_report_figures.py      # all report figures, or one key: B C D E F G H I J1 J2 J3 J4 J5
    python analysis/make_geometry_figures.py

Runtime: `run_studies.py` (all five studies) took 925 s (about 15 min) on Windows with `OPENBLAS_NUM_THREADS=1` (2026-11-22); `run_phase1_checks.py cap` takes about 2 min. Other runtimes were not recorded.

The scripts overwrite their CSVs. SLSQP can return a width at its bound as 0.1000000000041 mm, which would drop the whole-channel count from 150 to 149 (report section 6.7); since 2026-11-22 `optimize.optimize_design` snaps any width within 1e-9 m of a bound onto the bound, and a rerun of Study 2 gives N = 150 and X_lost = 33.34 W for the minimum lost-work design. The minimum R_th design sits on the ΔP limit and its optimizer result varies slightly between runs: the committed CSV (2026-11-08, Linux) has X_lost 37.38 W, Windows reruns on 2026-11-22 give 37.39 W (about 0.01 %; same geometry and flow to the reported precision, savings unchanged at 63.2 % pumping and 10.8 % lost work). The report keeps the committed 37.38 W.
