# Why these design-case values, and how the benchmark validates them

Figures: `figures/geometry_3d_design.png` (3D view and cross-section), `figures/geometry_design_vs_qm.png` (design vs benchmark unit cells and dimensionless numbers). Script: `analysis/make_geometry_figures.py`.

## 1. Design-case values compared with published cold plates

| Our value (`coldplate/config.py`) | Published / industry value | Source |
|---|---|---|
| Copper plate, skived-fin style straight channels | Copper base and skived microchannels are the dominant data-center cold plate design | [Shedd, "The Skinny on Skived Cold Plates"](https://timshedd26.substack.com/p/the-skinny-on-skived-cold-plates) |
| Channel width w_c = 0.2 mm, fin w_f = 0.2 mm (optimizer down to 0.1 mm) | Fins and gaps historically limited to about 100 µm, state of the art about 50 µm; worked examples use 100 and 200 µm gaps | Shedd (above) |
| | W_ch = W_fin = 0.2 mm baseline in a microchannel cold plate model | [Wang et al., Accelsius, "Thermohydraulic Modeling of Microchannel Cold Plates for Two-Phase Data Center Cooling", IEEE ITherm](https://accelsius.com/wp-content/uploads/Thermodynamic-Modeling-of-Microchannel-Cold-Plates-Q.-Wang.pdf) |
| Fin / channel height H = 3 mm | 3 mm to about 7 mm for very thin fins | Shedd (above) |
| | ≥ 3 mm fin height reported for the NVIDIA GB200 cold plate (blog claim, not a primary source) | [FiberMall blog](https://www.fibermall.com/blog/nvidia-gb200-liquid-cooling-plate.htm) |
| Base thickness t_b = 1 mm | 1–3 mm for GPU/CPU cold plates | Shedd (above) |
| Channel length L = 30 mm, footprint 30 × 30 mm | L_ch = 30 mm in the Accelsius model | Wang et al. (above) |
| Heat load 1 kW on 9 cm² = 111 W/cm² | 100 W/cm² footprint flux in the Accelsius model; packages "climbing past 1500 W" | Wang et al.; Shedd |
| Inlet water 30 °C (sweep 20–55 °C) | 45 °C inlet with PG25 coolant reported for GB200 (blog claim); ASHRAE liquid-cooling classes W17–W45 (cited in the proposal) | FiberMall; proposal |
| ΔP limit 50 kPa | < 20 kPa cold plate pressure drop reported for GB200 (blog claim) | FiberMall |
| 2 L/min reference flow | 1.8 L/min per GB200 cold plate (blog claim) | FiberMall |

**Caveats.** The FiberMall numbers are a vendor blog's claims without a primary source; use them only as "typical" values. The Accelsius paper models a two-phase (R515B) cold plate, but its channel geometry is the same family as ours. Manufacturers do not publish full drawings, so no exact commercial geometry is reproduced; our design is a representative skived-fin plate inside the published ranges. Do not copy images of commercial cold plates into the report without permission; cite the link instead.

## 2. How validation works when the geometries differ

What we validate is the **physics model** (the correlations for heat transfer and friction, the property handling, the conduction model), not a specific plate. Correlations are written in dimensionless groups, so a model that reproduces an experiment in a range of Re, Pr, z* and heat flux is trusted for any geometry inside that range.

| Dimensionless quantity | Design case | Qu & Mudawar | Inside the validated range? |
|---|---|---|---|
| Re | 374 (2 L/min) – 917 (5.1 L/min optimum) | 139 – 1672 | yes |
| Thermal entry z* = L/(Re Pr D_h) at the outlet | 0.017 – 0.043 | 0.011 – 0.13 | yes |
| Heat flux at the base | 111 W/cm² | 100 and 200 W/cm² | yes |
| D_h | 375 µm | 349 µm | yes |
| Pr | ≈ 5 | ≈ 7 | close; the Muzychka–Yovanovich model is stated for 0.1 < Pr < ∞ |
| Heated walls | 3 | 3 | yes |
| Aspect ratio H/w_c | 15 | 3.1 | **no: extrapolation** |

**The one gap is the aspect ratio.** Our design channels are much taller and narrower (H/w_c = 15) than the experiment's (3.1). Why we still accept it, and how we state it:
- The Muzychka–Yovanovich correlation uses √A as the length scale precisely to handle any aspect ratio, and tends to the parallel-plate limit for tall channels. Our coefficient checks cover aspect ratios 1–4 (thermal, Wibulswas) and 0.2–1 short/long (friction, Shah & London); the tall-channel limit is the textbook parallel-plate result.
- The fully developed fits (Shah & London) are exact series fits valid for all aspect ratios.
- In the report: "The model is validated for laminar water flow in copper microchannels at Re 139–1672 and z* 0.011–0.13; the design case lies inside this range except for its aspect ratio, which is an extrapolation of the validation."

A stronger validation would need a second benchmark with tall channels (H/w_c ≥ 10). That is listed as future work.
