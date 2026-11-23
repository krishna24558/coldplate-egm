# Equation sheet

One entry per equation you code: the equation, symbols, validity range, and exact source (paper, page, equation number). Anything without a verified source is marked **unverified**. Open assumptions are listed at the end as **A#**; decisions that change results are tracked as **D#** in `docs/project_status.md`.

Symbols (SI): Q heat load [W]; ṁ mass flow [kg/s]; V̇ volume flow [m³/s]; T temperature [K]; P pressure [Pa]; s specific entropy [J/kg·K]; h specific enthalpy [J/kg]; T0, P0 dead state.

## 1. Equations to code

| # | Quantity | Equation | Valid for | Source | Status |
|---|---|---|---|---|---|
| 1 | Channel count | N = ⌊W / (w_c + w_f)⌋ | straight fins | geometry | coded (`geometry.py`) |
| 2 | Hydraulic diameter | D_h = 2 w_c H / (w_c + H) | rectangular duct | definition 4A/P | coded |
| 3 | Aspect ratio | α = min(w_c, H) / max(w_c, H) | 0 < α ≤ 1 | Shah & London convention | coded |
| 4 | Nusselt number | Nu = 8.235(1 − 2.0421α + 3.0853α² − 2.4765α³ + 1.0578α⁴ − 0.1861α⁵) | laminar, hydrodynamically and thermally fully developed, H1 boundary condition, **four walls heated** | Shah & London (1978), page/eq **unverified** | coded (`correlations.py`), coefficients unverified |
| 5 | Friction | fRe = 24(1 − 1.3553α + 1.9467α² − 1.7012α³ + 0.9564α⁴ − 0.2537α⁵) (Fanning) | laminar, fully developed | Shah & London (1978), page/eq **unverified** | coded (`correlations.py`), coefficients unverified |
| 6 | Reynolds number | Re = ρ u D_h / μ, u = V̇ / (N w_c H) | equal flow per channel (A5) | definition | coded |
| 7 | Fin efficiency | η_f = tanh(mH)/(mH), m = √(2h / (k_s w_f)) | straight fin, uniform h, adiabatic tip (A6) | Bergman et al. (2011), page/eq **unverified** | coded |
| 8 | Effective area | A_eff = N L (w_c + 2 η_f H) | channel floor + two fin faces | derived | coded |
| 9 | Resistances | R_base = t_b/(k_s W L); R_conv = 1/(h A_eff); R_cal = 1/(ṁ c_p) | 1D base conduction, no spreading (A3) | derived | coded |
| 10 | Device temperature | T_dev = T_out + Q (R_conv + R_base + R_TIM) | uniform flux, hottest point at outlet (A2, A4) | derived | coded |
| 11 | Outlet state | h_out = h_in + Q/ṁ; T_out = T(h_out, P_out) | steady, adiabatic except base | first law | coded |
| 12 | Friction pressure drop | ΔP_f = 2 (fRe) μ u L / D_h² | fully developed laminar (A7) | from #5 | coded |
| 13 | Minor losses | ΔP_m = (K_c + K_e) ρ u²/2 | depends on manifold (A8) | K values **assumed, no source** | coded |
| 14 | Hydraulic power | Ẇ_hyd = V̇ ΔP | — | definition | coded |
| 15 | Pump electricity (estimate) | Ẇ_elec = V̇ ΔP / η_pump | η_pump assumed (A9) | assumption | coded |
| 16 | Entropy generation, cold plate | see Section 2 | steady open system | second law | coded |
| 17 | Exergy destruction | Ẋ_d = T0 Ṡ_gen | Gouy–Stodola | Bejan (1996), page **unverified** | coded |
| 18 | Flow exergy | ψ = (h − h0) − T0 (s − s0) | dead state T0, P0 | standard | coded |

## 1b. Developing-flow and three-sided-heating correlations (decision D4)

Coded in `coldplate/correlations.py`, selected with `Case.models` (`Models.nusselt`, `Models.friction`, `Models.axial_conduction`). All Nu and fRe are D_h based, Fanning f. Default stays `fd_H1` / `fd` until the Qu & Mudawar comparison picks the models.

| Key | Quantity | Equation | Valid for | Source | Transcription check |
|---|---|---|---|---|---|
| `fd_H1_3` | Nu_fd, three walls heated, short top wall adiabatic | 8.235(1 − 1.883/a + 3.767/a² − 5.814/a³ + 5.361/a⁴ − 2.0/a⁵), a = H/w_c ≥ 1 | fully developed, H1 | Shah & London (1978), quoted as Eq. (16) of Lee & Garimella (2006) | endpoints 8.235 (a→∞) and 3.556 (square); signs agree with a second quotation (Mital-type network paper, akademiabaru ARFMTSV56) |
| `LG` | local Nu_x, thermally developing | Nu = 1/(C1 z*^C2 + C3) + C4, z* = x/(Re Pr D_h); C1 = −3.122e-3a³ + 2.435e-2a² + 0.2143a + 7.325; C2 = 0.6412; C3 = 1.589e-4a² − 2.603e-3a + 2.444e-2; C4 = 7.148 − 13.28/a + 15.15/a² − 5.936/a³, a = H/w_c | 1 ≤ a ≤ 10, z* < z*_th, H1 four walls, hydrodynamically developed inlet, water | Lee & Garimella, IJHMT 49 (2006) 3060, Eq. (12); z*_th Eq. (11) | PDF text lost minus signs. Checked: (i) at z*_th the fit gives 1.06–1.09 Nu_fd (paper defines z*_th at 1.05 Nu_fd), (ii) within 6 % (mean 2.5–2.8 %) of Wibulswas Nu_x for a = 3 and 4 (Lee et al. 2005 Table 2). The C4 exponents are 10⁺¹ (10⁻¹ gives Nu below Nu_fd); the leading C1 sign is negative (fits Wibulswas better, and matches the second quotation). `tests/test_correlations_developing.py` |
| `LG` (use) | Nu_x along the whole channel | max(Eq. 12, Nu_fd); a clipped to [1, 10] in Eq. 12 | — | our blending choice: keeps Nu_x continuous; the paper switches to Nu_fd at z*_th | — |
| `LG_3` | three-sided developing | Nu_x,3 = Nu_x · Nu_fd,3/Nu_fd,4 | assumes the developing 3/4-wall ratio equals the fully developed ratio | Lee & Garimella (2006) Eq. (15), after Phillips | — |
| `MY` | local Nu_x, simultaneously developing (combined entry) | Nu_√A = [(C4 f(Pr)/√z*)^m + ({C1 fRe_√A/(8√π ε^γ)}⁵ + {C2 C3 (fRe_√A/z*)^(1/3)}⁵)^(m/5)]^(1/m); UWF: C1 = 3.86, C3 = 0.501; local C2 = C4 = 1; γ = 1/10; m = 2.27 + 1.65 Pr^(1/3); f(Pr) = 0.886/[1 + (1.909 Pr^(1/6))^(9/2)]^(2/9); z* = z/(√A Re_√A Pr) | 0.1 < Pr < ∞, all z*; about ±15 % (rectangles worst) | Muzychka & Yovanovich, ASME JHT 126 (2004) 54, Eqs. (21), (22), (42)–(46), Table 1 | fd term reproduces the circular-tube Nu_D = 4.364 / 3.657 exactly (fixes where ε^γ sits); Graetz term reproduces Lévêque 1.302 x*^(−1/3) for a circle; thermal-only part within 9 % of Wibulswas for a = 3 (fd limit about 7–9 % high for rectangles). Tests |
| `MY_3` | three-sided combined entry | MY · Nu_fd,3/Nu_fd,4 | — | **our extension** of Eq. (15) to MY; flagged | — |
| `MY` friction | apparent f_app Re | f_app Re_√A = [(3.44/√z⁺)² + (fRe_√A)²]^(1/2), z⁺ = z/(√A Re_√A); fRe_√A = 12/(√ε(1+ε)[1 − 192ε/π⁵ tanh(π/2ε)]) | uniform inlet velocity, laminar | Muzychka & Yovanovich (2004) Eq. (47), (21) | within 4 % of Shah & London tabulated f_app Re (ε = 1, 0.5, 0.2; x⁺ = 0.001–0.2), quoted in Duan & Ma (2020) Table 3. Test |
| `hagenbach` friction | f_app Re = fRe_fd + K(∞)/(4x⁺) | K(∞) = 0.6796 + 1.2197α + 3.3089α² − 9.5921α³ + 8.9089α⁴ − 2.9959α⁵ | x⁺ > ~0.05 only (+75 % error at x⁺ = 0.005) | Steinke & Kandlikar, quoted in Duan & Ma (2020) Eq. (33); **secondary source** | within 4 % of Shah & London for x⁺ ≥ 0.05 |

| `viscosity_correction` | wall-to-bulk viscosity correction, laminar liquid | Nu/Nu_cp = (μ_b/μ_w)^0.14; f/f_cp = (μ_w/μ_b)^0.58 heating (0.50 cooling); μ_b from local T_f(x), μ_w from T_cf(x); friction uses the length mean of μ_b(μ_w/μ_b)^m | property-ratio method, laminar liquids | Kays & Crawford, *Convective Heat and Mass Transfer*, 3rd ed. (1993), exponents as tabulated in the `ht` library (`wall_factor`); original table not yet checked | — |

Thermal model with local h(x) (`thermal.py`): G′(x) = h(x) N (w_c + 2η_f(x) H); T_cf = T_f + q′/G′ (1D, default) or the base axial-conduction equation k_s A_ax T_cf″ − G′(T_cf − T_f) + q′ = 0 with adiabatic ends and ṁ dh_f/dx = G′(T_cf − T_f) (A14). Stations are clustered toward the inlet; the inlet station uses h at x₁/8 (cell mean of a 1/√x law).

Effect on the 1 kW reference design (2 L/min, 30 °C): T_dev 70.5 → 69.8–70.5 °C (the outlet is close to fully developed, L_th,LG/L = 0.43, so T_dev hardly moves); length-mean Nu 7.2 → 8.2 (LG) / 8.8 (MY); X_lost 52.3 → 49.1–50.7 W; ΔP 5.57 → 5.85 kPa with MY friction. a = H/w_c = 15 is outside LG's fitted range (clipped to 10); MY has no aspect-ratio limit.

## 2. Control volumes for entropy

Keep these separate. Report each term against the control volume it belongs to.

**CV-P (upstream, package/TIM, not part of the cold plate).** Heat Q leaves the junction at T_j and enters the cold plate base at T_s. Its entropy generation, Ṡ_gen,P = Q (1/T_s − 1/T_j), belongs to the package and TIM. It is not cold plate loss. Report it, if at all, as a separate line.

**CV-C (the cold plate).** Boundary: copper base surface where heat enters, channel walls, inlet and outlet ports. Steady, single inlet and outlet:

    Ṡ_gen,C = ṁ (s_out − s_in) − ∫ q″ / T_b dA        (exact form, A1)
            ≈ ṁ (s_out − s_in) − Q / T̄_s               (mean boundary temperature)

- s_in, s_out from CoolProp at (T, P), so the pressure drop is included automatically.
- **The mean boundary temperature T̄_s is an approximation.** The base temperature rises along the flow, and 1/T is convex, so Q/T̄_s differs slightly from ∫ q″/T dA. Estimate the error once, for example by evaluating q″/T at several stations along the channel, before relying on small differences in Ṡ_gen.
- Decomposition (approximate, for interpretation only; must sum close to the exact value):
  - heat transfer: Q (1/T̄_f − 1/T̄_s)
  - friction: V̇ ΔP / T̄_f (to first order)

**CV-L (cold plate + idealized return to T_in): the objective control volume, per the submitted proposal.** Adds the warm outlet water being cooled back to T_in, with Q plus all pump work rejected at T_in:

    Ṡ_gen,L = Q (1/T_in − 1/T̄_s) + Ẇ_pump / T_in,      X_lost = T0 Ṡ_gen,L

It is **not** a full loop model: it idealizes the CDU as a reservoir at T_in. CV-C is still computed, as a diagnostic and for the decomposition.

Why it matters: in fully developed laminar flow h does not depend on velocity, so under CV-C more flow only makes the water colder and Ṡ_gen,C slightly rises. **CV-C alone has no interior optimum flow.** With the validated developing-flow model h rises with velocity and Ṡ_gen,C becomes almost flat (flat within 0.5 % from 0.5 to 4.5 L/min (lowest at 0.75 L/min) for the reference design; report section 6.6), still too weak to set the design. CV-L adds a coolant-warming term that falls roughly as 1/V̇, which creates one.

Split at the mean water temperature T̄_f (proposal): coolant warming Q(1/T_in − 1/T̄_f) ∝ ~1/V̇; base-to-coolant Q(1/T̄_f − 1/T̄_s) ≈ constant; pumping Ẇ_pump/T_in ∝ V̇². Approximate optimum V̇* = (B/2C)^(1/3), B = T0 Q²/(2 ρ c_p T_in²). Check at the optimum: T0 × coolant-warming term ≈ 2 × T0 × pumping term.

**Open interpretation (D7):** which Ẇ_pump goes in the CV-L formula. The proposal includes a pump-efficiency sensitivity, which only matters if Ẇ_pump = V̇ΔP/η_pump (pump inside the CV, electrical input). With Ẇ_pump = V̇ΔP the pump is outside. Pick one, state it, and use it consistently in Section 3.

## 3. Keep these quantities distinct

| Quantity | Symbol | Meaning | Where it appears |
|---|---|---|---|
| Hydraulic power | Ẇ_hyd = V̇ ΔP | flow work the cold plate consumes | cold plate; drives friction entropy in CV-C |
| Pump electricity (estimate) | Ẇ_elec = V̇ ΔP / η_pump | electrical input to a pump; η_pump assumed | outside CV-C; motor and pump losses happen in the pump |
| Exergy destruction | Ẋ_d = T0 Ṡ_gen | lost work for a stated control volume | must name its CV (C, L or P) |

- The friction part of Ẋ_d in CV-C is about (T0/T̄_f) Ẇ_hyd, not Ẇ_hyd and not Ẇ_elec.
- Pump inefficiency, (1 − η_pump) Ẇ_elec, is destroyed inside the pump. Include it only if the pump is inside the chosen CV, and say so.
- The proposal's comparison design is **minimum thermal resistance**, R_th = (T_dev − T_in)/Q, under the same constraints. A minimum hydraulic power design (minimize Ẇ_hyd) is an optional extra reference. Both are different objectives from minimum Ẋ_d.

## 3a. Where each quantity is coded

| Quantity | Function |
|---|---|
| ΔP, Re, W_hyd, W_elec | `hydraulic.pressure_drop` |
| η_f, A_eff, R's, T_f(x), T_cf(x), T_b(x), T_out, T_s_mean, T_dev | `thermal.solve_thermal` |
| Thermocouple temperature at depth | `thermal.temperature_below_channels` |
| S_gen_C (exact and mean-T), split; S_gen_L and its terms; S_gen_P; X_lost; X_out | `second_law.entropy_generation` |
| Coupled solution and constraint margins | `model.evaluate` |
| Optimum flow and (B/2C)^(1/3) | `optimize.optimum_flow` |

## 4. Assumptions and open questions

| ID | Assumption | Effect | Status |
|---|---|---|---|
| A1 | Heat enters CV-C at a single mean temperature T̄_s | small bias in the boundary entropy-transfer term | checked: the code uses the exact ∫q″/T_b dA. Reference design (one `evaluate(Case())` run, 2026-11-22): the boundary term Q/T̄_s differs from ∫q″/T_b dA by 0.006 %; Ṡ_gen,C computed with the mean form differs by 0.15 % (a small difference of two large terms); the two-term split of Section 2 (heat transfer + friction, report Eq. 24) by 0.48 %. The test allows 1 % |
| A2 | Uniform heat flux over the footprint | no hotspots; T_dev under-predicted for real chips | accepted for this course |
| A3 | 1D base conduction, no spreading | footprint = heated area, so spreading is small | accepted for 1 kW case; check for the experiment, whose heated area may differ from the channel area |
| A4 | Hottest device point above the outlet, with local h = mean h | ignores entrance-region enhancement | open |
| A5 | Equal flow in every channel | no manifold maldistribution | accepted |
| A6 | Fin tip adiabatic (insulated lid); h uniform over fin and floor | duct Nu (#4) is a wall average for four-walled heating, while the real channel is heated on three sides with an insulated lid | open: compare with a three-sided-heating correlation |
| A7 | Fully developed flow | thermal entry length ≈ 0.05 Re Pr D_h | **fails**: L_th/L ≈ 1.17 for the reference design and 0.4–5 for the benchmark (`Result.entry`). Developing-flow models now coded (Section 1b); choice by benchmark (D4) |
| A8 | Minor-loss coefficients K_c = 0.5, K_e = 1.0 | unsourced; matter more at high Re | open: source K values, and match the benchmark's pressure taps (see `validation/README.md`) |
| A9 | Pump efficiency η_pump = 0.5 | affects Ẇ_elec, and Ẋ_d if the pump is inside the CV (D7) | assumed; proposal varies it in the sensitivity study |
| A10 | Properties at mean fluid temperature; no wall-temperature viscosity correction | **not small** for the benchmark: walls run 20–40 K above the water, so friction is over-predicted by 20–40 % without it | option `Models.viscosity_correction` (local bulk μ and Kays & Crawford property ratios); used for the validated model |
| A11 | Viscous heating ignored in T_out | about ΔP/(ρ c_p), under 0.01 K here | accepted; keep in entropy via CoolProp |
| A12 | R_TIM = 0.02 K/W and T_dev,max = 90 °C | set feasibility | assumed; need sources |
| A13 | Dead state T0 = 25 °C | scales Ẋ_d and ψ | assumed; sensitivity |
| A14 | Base conduction 1D per station (no axial conduction) | with strong inlet h, axial conduction in the copper smooths T near the inlet (smoothing length √(k t/h_eff) ≈ 8 mm for Qu & Mudawar) | option `Models.axial_conduction`; to be decided by the benchmark |

## Notes from reading

(Add page and equation numbers here as each source is checked.)
