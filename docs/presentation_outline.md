# Final presentation outline

MEEN 615, Fall 2026. Second-Law Analysis and Constrained Optimization of a Liquid-Cooled Cold Plate for a 1 kW Electronic Heat Source. Instructor: Prof. Dion Antao.

12–15 minute talk, 14 slides (about 14 min at the times given) plus backup. Every number below is from `docs/final_report.md` (section or table named) or from the CSVs in `analysis/results/` and `validation/results/`. Figures are the current report figures only.

Format per slide: title (the takeaway as a sentence), bullets, figure, numbers on the slide, speaker notes.

---

## 1. Minimizing thermal resistance always asks for more flow; we ask how much flow is actually worth it (0:45)

- AI processors dissipate close to 1 kW from about 30 × 30 mm; they are cooled by copper microchannel cold plates.
- Cold plates are usually sized for minimum thermal resistance, which has no reason to stop adding flow.
- Question (from the proposal): how much coolant flow is thermodynamically worthwhile before friction outweighs the gain in heat transfer, and how do geometry, the device limit and the inlet temperature move that optimum?

**Figure:** [figures/geometry_3d_design.png](../figures/geometry_3d_design.png)

**Numbers on the slide:** 1000 W on 30 × 30 mm (about 111 W/cm²); reference geometry 0.2 mm channels and fins, 75 channels, 3 mm fins, 1 mm copper base; water in at 30 °C, 2 L/min; limits T_dev ≤ 90 °C, ΔP ≤ 50 kPa, Re ≤ 2000 (report Table 2).

**Speaker notes:** The design case is a representative skived-fin plate, not a specific product (report section 4). Design variables are channel width, fin thickness and flow; everything else is fixed. Our answer will be in watts of lost work.

---

## 2. Thermal resistance sees one loss; the second law prices all three in the same unit, watts (1:00)

- Lost work X_lost = T0 Ṡ_gen (Gouy–Stodola), T0 = 25 °C.
- Three losses: coolant warming (falls with flow), heat transfer from the base to the water (the "gap"), pumping (rises with flow).
- The gap is the largest loss at every flow, and flow barely changes it.

**Figure:** table (report Table 17, `analysis/results/study1_flow_sweep.csv`, reference geometry):

| V̇ (L/min) | X_warm (W) | X_gap (W) | X_pump (W) | X_lost (W) | T_dev (°C) |
|---|---|---|---|---|---|
| 2.0 | 11.75 | 36.57 | 0.35 | 48.66 | 69.02 |
| 5.0 | 4.71 | 35.67 | 2.67 | 43.06 | 64.94 |
| 10.0 | 2.37 | 33.97 | 13.48 | 49.81 | 63.29 |

**Numbers on the slide:** the table; the gap term is 75 % of the lost work at 2 L/min (report section 9.2).

**Speaker notes:** Going from 2 to 10 L/min trades about 9 W of warming loss for about 13 W of pumping loss, while the gap term moves by only 2.6 W. So more flow cannot fix the biggest loss; only geometry can. That is the thread of the whole talk.

---

## 3. The heat path is one resistance chain, solved at 41 stations because h changes along the channel (1:00)

- Chain: device → TIM → copper base → convection from channel floor and fins → water.
- Developing flow makes h depend on x, so the chain is solved station by station, coupled by axial conduction in the base and by the water's enthalpy.
- T_dev is the hottest base point plus the TIM drop.

**Figure:** [figures/fig_B_network.png](../figures/fig_B_network.png)

**Numbers on the slide:** Q R_TIM = 20 K (R_TIM 0.02 K/W, assumed); base conduction q″t_b/k_s = 2.85 K; 41 stations clustered toward the inlet. Reference design at 2 L/min: water 30 → 37.2 °C, T_dev 69.02 °C (Study 1 CSV).

**Speaker notes:** Of the roughly 32 K between the outlet water and the device, 20 K is the TIM, which the cold plate designer cannot change (report section 10.1). Most of the remainder is convection. Three walls are heated; the lid is adiabatic.

---

## 4. Properties, pressure drop and temperatures depend on each other, so `evaluate()` iterates them to convergence (0:45)

- Properties at the mean water state → pressure drop → thermal network → new T_out and ΔP → repeat.
- The thermal network feeds a wall-corrected viscosity back to the friction model.
- Then the second-law terms and the constraint margins; every study and the benchmark call only this function.

**Figure:** [figures/fig_E_solver_flowchart.png](../figures/fig_E_solver_flowchart.png)

**Numbers on the slide:** convergence when T_out changes by < 10⁻⁶ K and ΔP by < 10⁻⁶ ΔP; 3 iterations for the reference design, at most 50; 4 fixed wall-viscosity passes. Grid check 41 → 81 stations: T_dev −0.010 K, X_lost +0.016 % (report Table 27).

**Speaker notes:** One honest gap: the wall-viscosity loop runs a fixed 4 passes with no convergence test (report section 11.4). The numerical error is far below the 4.6 % validation error. The code structure is in backup (Figure 5).

---

## 5. The channels are too short for fully developed flow, so the proposal's model was off by 49 % (1:00)

- The proposal used fully developed Nusselt and friction values (Shah and London).
- In the benchmark channel the thermal entry length is twice the channel length: the whole channel is developing, and h near the inlet is more than twice the fully developed value.
- The proposal's fallback (switch to developing flow) was triggered.

**Figure:** [figures/fig_I_local_Nu.png](../figures/fig_I_local_Nu.png)

**Numbers on the slide:** at TC1 (5 mm from the inlet) local Nu 11.0 (`MY_3`) and 10.5 (`LG_3`) against 4.85 fully developed (2.3× / 2.2×); still 1.29× at the outlet; entry length 92 mm against a 44.8 mm channel. Proposal model: thermocouple MAPE 49.1 %, worst at TC1 (73.3 %), best at TC4 (31.1 %) (report Table 14).

**Speaker notes:** The error pattern itself is the evidence: largest at the inlet thermocouple and falling along the channel, exactly where the boundary layer is thinnest. We coded the developing-flow correlations of Lee and Garimella and of Muzychka and Yovanovich, with three-sided heating.

---

## 6. The paper gives its data only as figures, so we digitized them and checked them three ways (1:00)

- Qu and Mudawar (2002): 21 copper channels, 231 × 713 µm, water, 100 and 200 W/cm², Re 139–1672.
- Scripted pipeline: 600-dpi page → frame and tick detection → template matching of the markers (finds partly hidden repeats) → WebPlotDigitizer calibration.
- Checks: against values stated in the text, WebPlotDigitizer's own blob detector, and an independent recheck with separate code.

**Figure:** [figures/fig_G_data_extraction.png](../figures/fig_G_data_extraction.png)

**Numbers on the slide:** 43 ΔP, 43 water-rise and 187 thermocouple markers (report Tables 10 and 11); Fig. 6(a) alone 114 markers, 14 partly hidden. Last ΔP point 0.8585 bar at Re 1670 (`validation/data/qu_mudawar_dP.csv`) against 0.86 bar at Re 1672 in the text. Recheck agreement ≤ 0.003 bar and ≤ 0.4 K; independent hand check of 24 points, all within 1 % of the axis span; no value changed. Digitizing uncertainty moves the MAPE to 4.52–4.72 % (95 % range, report Table 15).

**Speaker notes:** Partly hidden markers are kept in the CSV but left out of the error; one Fig. 5 point was rejected with the reason recorded. An independent hand check of 24 points in the browser WebPlotDigitizer agreed within 1 % of every axis span.

---

## 7. Without tuning, the validated model is within 4.6 % on temperature and 9.7 % on pressure drop (1:00)

- Each correction was tested against the data and kept only with a physical reason; no coefficient was fitted.
- Developing flow is by far the largest step; three-sided heating, axial conduction and the wall-viscosity correction add a few points each.
- Both errors are inside the proposal's 10–15 % target.

**Figure:** [figures/fig_H_model_mape.png](../figures/fig_H_model_mape.png) (left) and [figures/validation_parity.png](../figures/validation_parity.png) (right)

**Numbers on the slide:** thermocouple MAPE 49.1 → 13.1 (developing) → 9.2 (three walls) → 6.7 (axial conduction) → 4.6 % (wall viscosity), 157 points, bias +0.7 %; water rise 2.8 %; ΔP 21.4 → 15.8 → 9.7 %, 39 points, bias +0.5 % (report section 8.3, Table 14).

**Speaker notes:** `LG_3` is equally good thermally (4.5 %); we chose `MY_3` because it matches the paper's uniform inlet velocity and has no aspect-ratio limit. The 9.7 % leaves out plenum losses; with K = 1 the model over-predicts by 27 %, which is the main open point of the validation (backup).

---

## 8. Only the loop control volume CV-L sees the coolant-warming loss, so only it has an optimum flow (1:15)

- CV-P (package and TIM): reported separately; the cold plate designer cannot change it.
- CV-C (cold plate only): heat transfer and friction, but no warming term; it is flat with flow.
- CV-L (cold plate + pump + idealized cooler back to T_in): the objective; the warm outlet water's exergy is destroyed in the cooler.

**Figure:** [figures/fig_C_control_volumes.png](../figures/fig_C_control_volumes.png)

**Numbers on the slide:** reference design, 2 L/min: CV-L 11.75 + 36.57 + 0.35 = 48.66 W; exact link (report Eq. 26) 36.97 (T0 Ṡ_gen,C) + 11.34 (cooler) + 0.35 (pump) = 48.66 W; CV-C flat within 0.5 % from 0.5 to 4.5 L/min (lowest at 0.75 L/min); CV-P 55.2 W at T̄_s 45.7 °C (report section 9.1).

**Speaker notes:** The TIM destroys more exergy than the whole cold plate loop, but putting it in the objective would reward a hotter base (backup). CV-C counts hot outlet water as a product; that is right only if the heat is reused, which a data-center loop does not do. Eq. (26) closes at all 27 Study 1 points.

---

## 9. An optimum flow exists because warming falls as 1/V̇ while pumping rises as about V̇² (1:15)

- With X_warm ≈ B/V̇ and X_pump ≈ C V̇² and a constant gap term: V̇* = (B/2C)^(1/3), and at V̇* the warming loss is twice the pumping loss (the 2:1 rule).
- The full model's optimum is higher: with developing flow, extra flow also lowers the gap loss.
- The minimum is flat; above it, flow buys almost nothing.

**Figure:** [figures/fig_J1_flow_sweep.png](../figures/fig_J1_flow_sweep.png)

**Numbers on the slide:** B = 23.4 W·(L/min), C = 0.108 W/(L/min)², (B/2C)^(1/3) = 4.77 L/min; numerical optimum 5.13 L/min, X_lost 43.05 W; X_warm/X_pump = 1.62 (fully developed model 2.43); Eq. (28): (2.28 − 0.67)/0.99 = 1.62. Within 5 % of the minimum: 3 to 7.5 L/min. From 5 to 10 L/min: hydraulic power × 5.0, T_dev −1.65 K (report sections 9.3, 10.1).

**Speaker notes:** The 2:1 rule holds only for constant h and pure V̇² pumping. Our model departs from it in the direction its physics predicts: the falling gap term lowers the ratio by 0.67, steeper-than-V̇² pumping raises it by 0.28. In the fully developed model the sign flips and the ratio is 2.43. Either way the formula is within 8 % of the numerical optimum.

---

## 10. The second-law design uses 63 % less pumping power than the minimum thermal resistance design, for a 1.4 K hotter device (1:15)

- Optimizing w_c, w_f and flow together: both objectives pick the thinnest fins and (nearly) the narrowest channels; they differ in flow.
- Minimum R_th stops only at the 50 kPa limit; minimum lost work stops at an interior optimum, well inside it.
- Geometry is worth about twice as much as flow.

**Figure:** [figures/fig_J2_designs.png](../figures/fig_J2_designs.png)

**Numbers on the slide** (report Table 18; savings from `phase1_pump_cv.csv`, report Table 23):

| | Min lost work | Min R_th |
|---|---|---|
| w_c / w_f (mm), N | 0.100 / 0.100, 150 | 0.110 / 0.100, 142 |
| V̇ (L/min), ΔP (kPa) | 3.17, 32.9 | 5.66, 50.0 (limit) |
| Ẇ_hyd (W) | 1.74 | 4.72 |
| X_lost (W) | 33.34 | 37.38 |
| T_dev (°C) | 61.57 | 60.17 |

Savings: −63.2 % pumping power, −10.8 % lost work, +1.40 K. Geometry vs flow: 22.5 % vs 11.5 % less lost work.

**Speaker notes:** The lost-work design still has 28 K of margin to 90 °C, so the extra 1.4 K is rarely worth 2.7 times the pump power. A design that sits on a constraint inherits its uncertainty; ours does not. The 63 % assumes the pump inside the control volume with η_pump = 0.5 (next slide). The minimum hydraulic power design (89.80 W, 89.91 °C) shows the other extreme.

---

## 11. The optimum geometry and the direction of the saving survive every assumption we could vary (1:00)

- Pump placement changes the size of the saving most; plenum K and the correlation choice move it by a few points.
- Below the 0.1 mm manufacturing bound the gain is small before the ΔP limit takes over.
- Capping the flow at 2 L/min costs little, with the same geometry.

**Figure:** [figures/fig_J5_below_limit.png](../figures/fig_J5_below_limit.png), plus a table (report Tables 21–23):

| Variant | Lost-work design | Pumping saving | Lost-work saving | ΔT_dev (K) |
|---|---|---|---|---|
| Default (pump inside, η 0.5, K 1.5) | 0.1 / 0.1 mm, 3.17 L/min | 63.2 % | 10.8 % | +1.40 |
| K_c + K_e = 0 / 3 | same geometry, 3.22 / 3.12 L/min | 66.1 / 61.0 % | 12.3 / 9.6 % | +1.50 / +1.37 |
| Pump outside CV-L | same geometry, 3.98 L/min | 40.6 % | 4.7 % | +0.53 |
| Fully developed model | same geometry, 3.10 L/min | 63.8 % | 11.2 % | +1.56 |

**Numbers on the slide:** the table; 0.05 mm bounds: best 31.28 W at w_c 0.069 mm (6.2 % below the 0.1 mm design); flow capped at 2 L/min: 35.37 W (+6.1 %), same geometry.

**Speaker notes:** In every variant the lost-work design has the same geometry, less pumping power and less lost work than minimum R_th, for 0.5–1.6 K. Pump inside or outside is a question of who pays the pump losses: the data-center operator pays the electricity, hence our default. The sub-0.1 mm results are H/w_c 30–60, further outside the validation.

---

## 12. Warmer inlets cut lost work until the 90 °C device limit takes over near 55 °C (1:00)

- Optimum flow barely moves with inlet temperature.
- The same temperature differences at higher absolute temperature destroy less exergy, and the outlet water carries more.
- Above about 55 °C the device limit governs, and laminar flow cannot meet it.

**Figure:** [figures/fig_J3_inlet_temperature.png](../figures/fig_J3_inlet_temperature.png)

**Numbers on the slide:** 20 → 55 °C: V̇* 4.93 → 5.50 L/min, X_lost 46.71 → 35.80 W, X_out −13.58 → 93.93 W; at 55 °C T_dev 89.46 °C (0.54 K below the limit); 57.5 °C would need 13.5 L/min, Re 3834; at 60 °C the floor is 90.33 °C, infeasible at any flow (report Table 19). Reference geometry only.

**Speaker notes:** This covers the ASHRAE liquid-cooling classes up to W45. Above 55 °C the levers are geometry and the TIM, which is 20 K of the roughly 35 K rise. The 0.1 mm design has a lower thermal resistance, so its crossover would be a few kelvin higher, but we did not run it.

---

## 13. 3.17 L/min is the optimum for one cold plate whose heat is thrown away, not a rack-level recommendation (0:45)

- 3.17 L/min for 1 kW is above the 1–2 L/min per kW of current practice (proposal).
- Reason 1: CV-L charges the warming of the coolant as lost work; with heat reuse that loss would shrink and the optimum would move to lower flow (an argument from Eq. 26, not a run).
- Reason 2: rack-level limits (shared pump, CDU flow and head) are not modelled.

**Figure:** table (report Table 22, `analysis/results/phase1_flow_cap.csv`):

| | No cap | V̇ ≤ 2 L/min |
|---|---|---|
| Geometry | 0.1 / 0.1 mm, 150 channels | same |
| V̇ (L/min), ΔP (kPa) | 3.17, 32.9 | 2.00, 19.9 |
| X_lost (W) | 33.34 | 35.37 (+6.1 %) |
| Ẇ_hyd (W) | 1.74 | 0.66 |
| T_dev (°C) | 61.57 | 64.07 |

**Numbers on the slide:** the table; the capped design still has 5.4 % less lost work and 86 % less hydraulic power than minimum R_th, for 3.90 K.

**Speaker notes:** Even uncapped we use 44 % less flow than the minimum R_th design (5.66 L/min). Because the minimum is flat, a flow limit set by the rest of the loop costs little thermodynamically, as long as the geometry is the fine one.

---

## 14. Geometry beats flow, and the control volume is part of the answer (1:00)

- **Conclusions.** At 0.2 mm the worthwhile flow is 5.13 L/min (flat from 3 to 7.5 L/min). The base-to-coolant loss dominates, so optimizing the geometry (0.1 mm, 3.17 L/min, 33.34 W) gains twice what flow alone does. Against minimum R_th: −63 % pumping, −10.8 % lost work, +1.40 K. The device limit decides feasibility, not the optimum. The cold plate alone has no useful optimum flow; the loop does.
- **Limitations.** Validated at H/w_c = 3.1, design at 15–30 (extrapolation); plenum K unsourced; uniform heat flux; equal flow per channel; CV-L idealizes the CDU as a reservoir at T_in. Assumed: R_TIM, 90 °C, 50 kPa, η_pump 0.5.
- **Next.** CFD of the 0.1 mm design; a tall-channel benchmark; heat-reuse variant of CV-L; manifold model.

**Figure:** [figures/geometry_design_vs_qm.png](../figures/geometry_design_vs_qm.png) (to show the aspect-ratio gap)

**Numbers on the slide:** validated range Re 139–1672, z* 0.011–0.13; design H/w_c 15 (reference) to 30 (optimum) against 3.1 (report section 8.5).

**Speaker notes:** Close on the question: about 5 L/min per kW is worth it at the reference geometry, but the bigger win is narrower channels, which then need less flow. Open items we state plainly: an independent hand calculation of the reference design, and the viscosity exponents and Shah and London fits not yet checked in the originals.

---

## Backup slides

Figures to keep ready: [figures/fig_D_code_structure.png](../figures/fig_D_code_structure.png) (code structure), [figures/fig_F_benchmark_setup.png](../figures/fig_F_benchmark_setup.png) (benchmark as modelled), [figures/validation_vs_Re.png](../figures/validation_vs_Re.png) (data and model against Re), [figures/fig_J4_sensitivity.png](../figures/fig_J4_sensitivity.png) (Study 4 sensitivities).

## Likely questions

**Q1. Why accept a device that is 1.4 K hotter?**
At 61.57 °C the lost-work design has 28.4 K of margin to the 90 °C limit, and the 1.4 K costs 2.7 times the pump power. The minimum R_th design sits on the 50 kPa limit, so its flow and its pump power follow whatever that budget is set to; the lost-work design's ΔP limit is not active (report section 10.2).

**Q2. The TIM destroys 55.2 W, more than the whole loop. Why is it not in the objective?**
The cold plate designer cannot change it (Q R_TIM is fixed at 20 K), and by Ṡ_gen,P = Q(1/T_s − 1/T_j) the same 20 K at a higher temperature generates less entropy, so adding it would reward a hotter base. Its effect on the cold plate is through the device limit: R_TIM ±50 % moves T_dev by ±10 K and does not move the optimum flow (report sections 9.1, 10.4; Figure 16).

**Q3. How can you use the model at H/w_c = 30 when the benchmark is 3.1?**
It is an extrapolation and we say so. Three reasons we still use it: the Muzychka–Yovanovich model uses √A as its length scale to cover any aspect ratio and tends to the parallel-plate limit; Re, z*, heat flux and D_h of the design are inside the validated range; and the fully developed model, which does not use the developing-flow correlations, gives the same optimum geometry and a 63.8 % saving (report section 8.5, Table 9). A CFD check and a tall-channel benchmark are future work.

**Q4. Your best pressure-drop fit leaves out the plenum losses. Isn't that unphysical?**
Yes, it cannot be exactly right, and it is the main open point (D5). The paper gives no K values or plenum dimensions; with its "close to unity" K the model over-predicts by 27 %. For the design it hardly matters: with K_c + K_e from 0 to 3 the lost-work design keeps its geometry, its flow moves ±1.5 % and its lost work ±0.3 %; the saving moves between 61 % and 66 % (report sections 8.6, 10.5.3).

**Q5. How much does the 63 % depend on your assumptions?**
Mostly on where the pump is counted: 63.2 % with the pump inside the control volume (electricity, η_pump = 0.5), 40.6 % with it outside. The pump efficiency moves the optimum flow at the reference geometry from 4.27 to 5.80 L/min for η 0.3–0.7. The geometry recommendation is the same in every case (report sections 6.6, 10.4, Table 23).

**Q6. Were the digitized data checked by a person?**
Yes, on a sample: an independent hand check read 24 points by hand in WebPlotDigitizer (8 per figure group); against our CSV values Re agrees within 1.39 %, ΔP within 2.7 % (0.0063 bar), water rise within 1.8 % (0.76 K) and thermocouple rise within 1.5 % (0.49 K), all under 1 % of the axis span (report section 7.6, Table 12). Before that they were checked against the values stated in the paper's text, against WebPlotDigitizer's own marker detection (≤ 1.5 px), and by an independent recheck with separate code (≤ 0.003 bar, ≤ 0.4 K; no value changed). Shifting every reading by its uncertainty moves the thermocouple MAPE by about 0.1 point (4.52–4.72 %), far less than the 4.6 % model error (report sections 7.5, 7.6, 8.4).
