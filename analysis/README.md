# Analysis

`run_studies.py` runs the proposal studies on the 1 kW case:

| Study | Output |
|---|---|
| 1. Flow sweep at the reference geometry, lost-work optimum and (B/2C)^(1/3) check | `results/study1_flow_sweep.csv`, `../figures/study1_flow_sweep.png` |
| 2. Reference vs min lost work vs min thermal resistance vs min hydraulic power (grid + SLSQP) | `results/study2_designs.csv` |
| 3. Inlet temperature sweep 20–50 °C (extended to 60 °C) | `results/study3_inlet_temperature.csv`, `../figures/study3_inlet_temperature.png` |
| 4. Sensitivity: R_TIM, η_pump, T0, minor-loss K | `results/study4_sensitivity.csv` |

    python analysis/run_studies.py            # about 20 s
    python analysis/run_studies.py --quick    # coarser Study 2 grid

Results depend on unvalidated assumptions (fully developed flow, minor losses, D7); see `docs/project_status.md`.
