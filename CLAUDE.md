# CLAUDE.md

MEEN 615 course project (Texas A&M, Fall 2026): **Second-Law Analysis and Constrained Optimization of a Liquid-Cooled Cold Plate for a 1 kW Electronic Heat Source.** A steady, reduced-order, single-phase Python model of a water-cooled copper microchannel cold plate (CoolProp properties), checked against Qu & Mudawar (2002), then used for entropy-generation / exergy-destruction studies.

## Start and finish every session

1. Read `docs/project_status.md` first. It says what works, what is a placeholder, open decisions and the next task.
2. After any meaningful change, update `docs/project_status.md` (what changed, test result, next task).
3. Do not commit or push unless the user asks.

## Tests

- Windows: `.\.venv\Scripts\python.exe -m pytest -q`
- Linux / macOS: `.venv/bin/python -m pytest -q` (or `python -m pytest -q` with deps installed)
- Setup: `python -m venv .venv`, then `pip install -r requirements.txt` and `pip install -e .`
- Studies: `python analysis/run_studies.py` (CSVs to `analysis/results/`, figures to `figures/`)

## Units

- SI everywhere inside the package: m, kg, s, K, Pa, W, J/kg, J/kg·K, m³/s, kg/s.
- °C, L/min, mm and µm only at input/output edges (notebooks, CSVs, plots), and the variable or column name says so (`T_in_C`, `V_lpm`, `w_c_mm`).
- Temperatures passed to CoolProp and to entropy terms are always in K.

## Sources and data

- Every correlation or coefficient cites its original source with page / equation / table number, in the docstring and in `docs/equation_sheet.md`. State its validity range.
- Every experimental value records units, exact paper location, and status (measured / digitized / assumed / missing). See `validation/README.md`.
- Never fabricate data, citations, test results or validation claims. If something is unknown, write it down as unresolved.
- Assumptions are flagged in `docs/equation_sheet.md` before the physics that uses them is coded.

## Consult before changing physics or validation

- `docs/proposal_submitted.md`: the proposal submitted to Prof. Dion Antao. It is the base for scope, objectives, control volume, comparison design, validation target and dates. Do not edit it; flag any change of direction to the user.
- `docs/project_scope.md`: what is in and out of scope for this course
- `docs/equation_sheet.md`: equations, control volumes, assumptions, open questions
- `validation/README.md`: benchmark inputs, data status, comparison rules
- `coldplate/config.py`: the 1 kW application case (keep experiment inputs separate from it)
- `docs/claude_code_plan.md`: the phased plan for finishing the project (which phase is next: see `docs/project_status.md`)
- `docs/design_case_justification.md`: why the design values, and how the benchmark validates them
- `validation/data/raw/recheck_log.md`: independent recheck of the digitized data

## Code map

`config.py` (case) → `geometry.py` → `correlations.py` → `hydraulic.py` + `thermal.py` → `second_law.py` → `model.evaluate()` → `optimize.py` (studies) / `benchmark.py` (Qu & Mudawar, inputs from `validation/data/` only).

## Order of work

Baseline model → Qu–Mudawar benchmark comparison → second-law terms → design studies. Optimization comes last.
