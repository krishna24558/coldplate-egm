# Cold Plate Second-Law Optimization

**Second-Law Analysis and Constrained Optimization of a Liquid-Cooled Cold Plate for a 1 kW Electronic Heat Source**

A reduced-order Python model of a water-cooled copper microchannel cold plate. It quantifies entropy generation and exergy destruction, then finds the channel geometry and coolant flow that minimize entropy generation while meeting device-temperature, pressure-drop and manufacturing limits.

**Central question:** How much coolant flow is thermodynamically worthwhile before added friction losses outweigh the reduction in heat-transfer irreversibility, and how do channel geometry, the device-temperature limit and coolant inlet temperature shift that optimum?

> Status: in progress (MEEN 615, Texas A&M University, Fall 2026)

## Method

1. **Thermal-hydraulic model:** base conduction, fin-array convection (laminar rectangular-duct correlations), coolant temperature rise, pressure drop and pump work. Water properties from CoolProp.
2. **Validation:** against the single-phase copper microchannel experiments of Qu & Mudawar (2002).
3. **Second-law analysis:** entropy balance over the cold plate plus the return of the coolant to its inlet temperature, S_gen = Q(1/T_in − 1/T_s) + W_pump/T_in, split into coolant-warming, base-to-coolant and pumping losses; lost work via the Gouy–Stodola theorem.
4. **Optimization:** flow sweep, constrained optimization of channel width, fin thickness and flow, and a coolant inlet temperature sweep (ASHRAE W17–W45).

## Repository layout

```
coldplate/       physics modules (properties, geometry, correlations, thermal, hydraulic, second_law, optimize)
tests/           pytest unit tests
validation/      Qu & Mudawar data and validation notebook
analysis/        notebooks for the studies
figures/         generated figures
docs/            equation sheet and notes
```

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
pytest
```

## Usage

```python
from coldplate.config import Case, lpm
from coldplate.model import evaluate
from coldplate.optimize import with_design, optimum_flow

r = evaluate(Case())                      # 1 kW reference design
print(r.summary())                        # T_dev, dP, lost work, ...
r2 = evaluate(with_design(Case(), w_c=0.15e-3, V_dot=lpm(3.0)))
print(optimum_flow(Case()).V_dot * 60000) # lost-work optimum flow, L/min
```

Run all studies (CSVs in `analysis/results/`, figures in `figures/`):

```bash
python analysis/run_studies.py
```

Benchmark against Qu & Mudawar (after digitizing the figures, see `validation/README.md`):

```bash
python -c "from coldplate.benchmark import compare; print(compare())"
```

## Results

Model output exists but is not yet validated; see `docs/project_status.md`.

## References

- W. Qu and I. Mudawar, "Experimental and numerical study of pressure drop and heat transfer in a single-phase micro-channel heat sink," *Int. J. Heat Mass Transfer* 45 (2002) 2549–2565.
- R. K. Shah and A. L. London, *Laminar Flow Forced Convection in Ducts*, Academic Press, 1978.
- A. Bejan, *Entropy Generation Minimization*, CRC Press, 1996.
- I. H. Bell et al., "Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the Open-Source Thermophysical Property Library CoolProp," *Ind. Eng. Chem. Res.* 53 (2014) 2498–2508.

## Team

- Sai Krishna Kommineni
- Suneel Kumar
- Sam

MEEN 615 (Advanced Engineering Thermodynamics), Texas A&M University, Fall 2026
