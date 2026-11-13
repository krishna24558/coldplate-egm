# Project scope

**Base document:** `docs/proposal_submitted.md`, the proposal submitted to Prof. Dion Antao. Where this file and the proposal disagree, the proposal wins unless the instructor agrees to a change.

## Course objective

MEEN 615 (Advanced Engineering Thermodynamics), Texas A&M, Fall 2026. Instructor: Prof. Dion Antao. Group: Sai Krishna Kommineni, Suneel Kumar, Sam. Budget: about 35 hours. Repository: https://github.com/krishna24558/coldplate-egm (proposal promises weekly updates).

Central question (from the proposal): how much coolant flow is thermodynamically worthwhile before the extra friction losses outweigh the reduction in heat-transfer irreversibility, and how do the channel geometry, the device temperature limit and the coolant inlet temperature change that optimum?

## Objectives (from the proposal)

1. Build a model that gives device temperature, pressure drop and pump power for any channel width, fin thickness and flow rate.
2. Validate it against the measured data of Qu and Mudawar (2002).
3. Calculate entropy generation, split it into its sources, and express it as lost work.
4. Find the flow and geometry that minimize lost work under the constraints, and compare with the **minimum thermal resistance** design.
5. Find the highest inlet temperature at which the optimum is still feasible, and the exergy of the outlet water.

## Studies (from the proposal)

1. Flow sweep at the reference geometry (0.2 mm channels and fins).
2. Constrained optimization of all three variables (grid sweep, then SciPy SLSQP), compared with the minimum thermal resistance design.
3. Inlet temperature sweep, 20–50 °C.
4. Short sensitivity check on TIM resistance and pump efficiency.

Optional extra reference point, not promised in the proposal: the minimum hydraulic pumping power design that meets the constraints. Cheap to add once Study 2 works.

## Model (from the proposal)

- Steady, single-phase, laminar, reduced-order (1D resistance network): TIM → base conduction → fin-array convection → coolant temperature rise.
- Fully developed laminar Nu and fRe for rectangular ducts (Shah and London), standard fin efficiency, CoolProp water properties.
- Hottest device point above the outlet.
- Entropy control volume: **cold plate plus the return of the coolant to T_in** (see `docs/equation_sheet.md` §2). Lost work X_lost = T0 S_gen.
- Uniform heat flux, equal flow in all channels.

## Application case (1 kW)

| Item | Value | Justification in proposal | Still needs |
|---|---|---|---|
| Heat load | 1000 W, uniform over 30 mm × 30 mm (~110 W/cm²) | power class of current AI accelerators | a source |
| Cold plate | copper, k = 390 W/m·K; fin height 3 mm (fixed); base 1 mm | usual material; common skived-fin values | sources |
| Junction + TIM | 0.02 K/W (varied in sensitivity) | typical for large packages, ~20 K at 1 kW | a source |
| Inlet water | 30 °C (study 20–50 °C) | ASHRAE W32 (W17–W45 for the sweep) | — |
| Reference design | 0.2 mm channels, 0.2 mm fins, 2 L/min | — | — |
| Dead state | T0 = 25 °C | reference environment | — |
| Pump efficiency | 0.5 (varied in sensitivity) | — | a source or label as assumed |

## Design variables and constraints

- Variables: channel width 0.1–1.0 mm; fin thickness 0.1–0.5 mm; flow 0.5–12 L/min.
- Fixed: footprint 30 mm × 30 mm, fin height 3 mm, base 1 mm.
- Constraints: device ≤ 90 °C (near GPU throttling); ΔP ≤ 50 kPa (assumed per-plate budget); laminar flow (correlation validity), plus any other validity limits in the equation sheet.
- Objective: minimize lost work T0·S_gen.

## Validation (from the proposal)

Run the model at the Qu and Mudawar (2002) test conditions and compare measured pressure drop and temperatures. **Target: errors within about 10–15%.** If the error is too large, switch to a developing-flow Nusselt correlation. Second-law checks: S_gen positive everywhere; at the laminar optimum the coolant-warming loss is about twice the pumping loss.

## Timeline (from the proposal)

| Milestone | Proposal date | Status on 2026-11-07 |
|---|---|---|
| Model and tests | Nov 3 | **behind**: thermal and hydraulic modules are placeholders |
| Validation and second-law module | Nov 12 | not started |
| Studies | Nov 22 | not started |
| Final report and code | Dec 3 | — |

## Deliverables

Python package with tests (this repo, updated weekly on GitHub), validation against Qu and Mudawar, study figures, final report.

## Out of scope (later courses or extensions)

CFD or conjugate simulation; full cooling-loop coupling (pump curves, manifolds, CDU, chiller, plant); two-phase flow; hotspot maps and spreading; transient behavior; surrogate/ML models; a heat-pump or heat-reuse plant model beyond the outlet-water exergy.

The coolant-return term in the control volume is an idealization (heat rejected to a reservoir at T_in), not a loop model, and stays in scope because the proposal relies on it.
