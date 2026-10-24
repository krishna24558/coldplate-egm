# Cold Plate Second-Law Optimization

**Second-Law Analysis and Constrained Optimization of a Liquid-Cooled Cold Plate for a 1 kW Electronic Heat Source**

A reduced-order Python model of a water-cooled copper microchannel cold plate. It quantifies entropy generation and exergy destruction, then finds the channel geometry and coolant flow that minimize entropy generation while meeting device-temperature, pressure-drop and manufacturing limits.

**Central question:** How much coolant flow is thermodynamically worthwhile before added friction losses outweigh the reduction in heat-transfer irreversibility, and how do channel geometry, the device-temperature limit and coolant inlet temperature shift that optimum?

> Status: in progress (MEEN 615, Texas A&M University, Fall 2026)

## Method

1. **Thermal-hydraulic model:** base conduction, fin-array convection (laminar rectangular-duct correlations), coolant temperature rise, pressure drop and pump work. Water properties from CoolProp.
2. **Validation:** against the single-phase copper microchannel experiments of Qu & Mudawar (2002).
3. **Second-law analysis:** exact entropy balance, split into heat-transfer and friction terms; lost work via the Gouy–Stodola theorem, including pump inefficiency.
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

## Results

_To be added._

## References

- W. Qu and I. Mudawar, "Experimental and numerical study of pressure drop and heat transfer in a single-phase micro-channel heat sink," *Int. J. Heat Mass Transfer* 45 (2002) 2549–2565.
- R. K. Shah and A. L. London, *Laminar Flow Forced Convection in Ducts*, Academic Press, 1978.
- A. Bejan, *Entropy Generation Minimization*, CRC Press, 1996.
- I. H. Bell et al., "Pure and Pseudo-pure Fluid Thermophysical Property Evaluation and the Open-Source Thermophysical Property Library CoolProp," *Ind. Eng. Chem. Res.* 53 (2014) 2498–2508.

## Author

Sai Krishna Kommineni, M.S. Mechanical Engineering, Texas A&M University
