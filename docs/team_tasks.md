# Team tasks (MEEN 615 cold plate)

Written 2026-11-13. Owner of the code and the main analysis: Sai. The two tasks below are **checks and supporting material**: the project does not depend on them to run, so if one slips, the report goes ahead without it. Each one still adds real value to the report and gives each of you a section you can present.

Dates from the proposal: design studies Nov 22, report Dec 3.

## Setup (both, about 20 min)

```powershell
git clone https://github.com/krishna24558/coldplate-egm.git
cd coldplate-egm
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pytest -q        # 51 passed, about 4 min
```

Read first, in this order: `README.md`, `docs/proposal_submitted.md`, `docs/project_status.md`, `validation/README.md` (Results section).

**Working rule:** work on your own branch (`git checkout -b suneel` / `git checkout -b sam`), only **add** files inside `team/<your name>/`, and do not edit files in `coldplate/`, `validation/data/` or `docs/`. Push your branch and tell Sai; he merges. That way nothing you do can break the model.

---

## Suneel: independent check of the validation data + report background

**A. Hand check of the digitized data (due Nov 20, about 2 h).** The experimental points we validate against were read from the figures of Qu & Mudawar (2002) by a script, then rechecked by a second script (`validation/data/raw/recheck_log.md`). A person's reading is the last missing check.

1. Get the paper (free PDF): https://engineering.purdue.edu/mudawar/files/articles-all/2002/2002_1.pdf
2. Open WebPlotDigitizer in the browser: https://automeris.io/WebPlotDigitizer. Steps are in `validation/README.md`, section "B. By hand in the browser app".
3. For each of Fig. 4(a), Fig. 5, Fig. 6(a), Fig. 6(b): calibrate the axes, then click **8 markers spread over the Re range** (both heat fluxes where there are two). Export the CSV.
4. Compare each of your points with the matching row in `validation/data/qu_mudawar_dP.csv` / `qu_mudawar_thermal.csv` (same figure, same series, nearest Re).
5. Deliverable: `team/suneel/hand_check.md` with a table (figure, series, Re, your value, CSV value, difference) and one line of conclusion, plus your WPD CSV exports in `team/suneel/`.

Done when: 32 points compared. Agreement within about 2 % of the axis range is a pass; list any point that is off by more.

**B. Background section for the report (due Nov 25, about 3 h).** 1–1.5 pages for the Introduction: why AI/data-center chips need liquid cold plates (heat flux trend), what warm-water cooling is (ASHRAE liquid-cooling classes W17–W45), and why a second-law (entropy generation) view is useful for cooling design. 5–8 references, each with a link, no Wikipedia. Deliverable: `team/suneel/background.md`.

---

## Sam: independent hand calculation of the model + presentation draft

**A. Hand calculation of the reference design (due Nov 20, about 3 h).** Check the code against a calculation done without it, in Google Sheets or on paper, using the simplest version of the model (fully developed laminar flow, no developing-flow corrections).

Inputs (from `coldplate/config.py`): Q = 1000 W; plate W = L = 30 mm; channel height H = 3 mm; channel width w_c = 0.2 mm; fin thickness w_f = 0.2 mm; base t_b = 1 mm; copper k = 390 W/m·K; R_TIM = 0.02 K/W; water in at 30 °C, 2.0 L/min; take water properties at the mean temperature (about 33.6 °C) from any table.

Calculate in this order (equations: `docs/equation_sheet.md`, Section 1, rows 1–15):
1. N = floor(W / (w_c + w_f)), D_h, aspect ratio α, channel velocity u, Re
2. Nu (Shah & London four-wall fit) and h; fin efficiency η_f; effective area A_eff
3. R_base, R_conv, R_cal; outlet temperature T_out; device temperature T_dev = T_out + Q (R_conv + R_base + R_TIM)
4. fRe, friction pressure drop, minor losses (K_c = 0.5, K_e = 1.0), total ΔP, hydraulic power V̇ΔP

Compare with the model in the same simple mode:
```powershell
.\.venv\Scripts\python.exe -c "from coldplate.config import Case, Models; from coldplate.model import evaluate; print(evaluate(Case(models=Models('fd_H1','fd',False,False))).summary())"
```
Deliverable: `team/sam/hand_calc.md` (or a link to the Google Sheet) with your value, the model's value and the difference for N, Re, Nu, T_out, T_dev, ΔP. Within about 2 % is a pass (property-table rounding); explain anything larger.

**B. Presentation draft (due Nov 28, about 3 h).** A 10–12 slide outline for the final presentation: problem and question, model (one schematic), validation (use `figures/validation_vs_Re.png` and `figures/validation_parity.png`), second-law result (`figures/study1_flow_sweep.png`), design comparison, inlet-temperature study (`figures/study3_inlet_temperature.png`), conclusions. One line of message per slide and which figure goes on it. Deliverable: `team/sam/presentation_outline.md` or a Google Slides link.

---

## How this fits together

| Task | Feeds | If it slips |
|---|---|---|
| Suneel A, hand check | Validation section: "checked by a person" | The two script checks already stand; we state the hand check was not done |
| Suneel B, background | Report Introduction | Sai writes a shorter introduction |
| Sam A, hand calculation | Model section: "verified against a hand calculation" | The unit tests already cover the physics limits; we drop the sentence |
| Sam B, presentation outline | Final presentation | Sai drafts it from the report |

In the final report and presentation, each of you presents your own part.
