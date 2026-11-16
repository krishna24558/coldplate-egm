# Claude Code plan: finishing the MEEN 615 project

Each run: read the context files, do ONE phase (or the part named in the prompt), update docs/project_status.md, stop and summarize. Phase 0 (data recheck) and the geometry figures are already done.

## Context files (read at the start of every run)
CLAUDE.md, docs/project_status.md, docs/proposal_submitted.md, docs/equation_sheet.md, validation/README.md, validation/data/raw/recheck_log.md, docs/design_case_justification.md

## Rules (every run)
- Do not change the physics, the validated default models or the digitized data. Do not re-research correlations or redo the validation.
- Never invent numbers, citations or results. Every number in the report must come from a CSV in analysis/results/ or validation/results/, or from a run done in this project. If something is unknown or unresolved, say so.
- Run the tests before and after code changes (.\.venv\Scripts\python.exe -m pytest -q; expect 51 passed, about 4 min; more if tests were added). Do not commit or push.
- Reuse the CSVs in analysis/results/ unless a task needs a new run.
- Do not stop to ask questions mid-run: make the reasonable choice, write it down in docs/project_status.md, and continue.
- End every run with a short summary: what was done, test result, anything unverified, what the next run should start with.

## Phase 1: finish the technical work
1. D8: add to analysis/run_studies.py a trend below the 0.1 mm limit (w_c = w_f = 0.05, 0.075, 0.1, 0.15, 0.2 mm, each at its own lost-work optimum flow, same constraints). Save the CSV, and state whether the optimum is set by the manufacturing bound or by the dP limit.
2. D7: run the lost-work optimum with the pump inside and outside the control volume (Losses.pump_inside_cv) and tabulate the difference, including the pumping-power saving vs the min-R_th design. Keep "inside" as the default.
3. D5: tabulate how the plenum-loss coefficient (K total = 0, 1.5, 3) changes the optimum design, using Study 4.
4. Compare the validated model with the proposal's fully developed model on the 1 kW case (Models("fd_H1","fd",False,False)): T_dev, dP, optimum flow, lost work. One table.
5. Numerical checks: grid independence (n_x = 21, 41, 81 on the reference design and one benchmark point), energy-balance closure, property-iteration convergence. One small table.
6. Propagate the digitizing uncertainty: shift the thermocouple data by +/- the reading uncertainty and report how much the MAPE moves.
7. Write the final headline numbers of the Study 2 comparison (pumping-power saving, lost-work saving, T_dev difference) in docs/project_status.md under "Headline results".

## Phase 2: figures (save in figures/, 200 dpi, readable in grayscale, axis labels with units)
B. Thermal resistance network (device -> TIM -> base -> fins/convection -> coolant), with the station-by-station local-h idea.
C. Control volumes for the entropy balance (CV-P, CV-C, CV-L) and where each loss term belongs.
D. Code structure: modules as boxes with arrows showing data flow (config -> geometry -> correlations -> hydraulic + thermal -> second_law -> model.evaluate -> optimize / benchmark -> analysis and validation scripts).
E. Solver flowchart for model.evaluate.
F. Benchmark test section: sketch of the Qu & Mudawar heat sink with the thermocouple and pressure-tap locations and which model quantity is compared with each.
G. Data extraction: an original paper figure crop next to its overlay with detected markers and the calibration points (the PDF is validation/data/raw/qu_mudawar_2002.pdf).
H. Bar chart of thermocouple MAPE by model from validation/results/thermal_model_matrix.csv.
I. Local Nu(x) along the channel for the fully developed, LG_3 and MY_3 models at one benchmark condition.
J. Results: lost-work terms vs flow with the optimum marked (Study 1); design comparison bars (Study 2); inlet-temperature sweep (Study 3); sensitivity (Study 4); the D8 trend.
Put the plotting code in analysis/make_report_figures.py so it can be rerun. Draw schematics with matplotlib. Look at each figure after making it and fix overlaps or unreadable labels.

## Phase 3: the detailed report, docs/final_report.md
Our team's report (Sai Krishna Kommineni, Suneel Kumar, Sam), first person plural, plain student language, no marketing tone. Embed all figures (including figures/geometry_*.png and figures/validation_*.png). Number equations, figures and tables and refer to them in the text.
Part A (sections 1-8):
1. Abstract (placeholder; written in Part B).
2. Introduction and objective: the central question from the proposal, why second-law analysis for liquid cooling.
3. What we did, step by step: proposal -> model -> validation -> design studies, including what changed from the proposal and why (the fully developed assumption failed in validation).
4. Geometry and design case: from docs/design_case_justification.md (values vs published cold plates, with references).
5. Model: thermal network, hydraulic model, property handling, equations, assumption list.
6. Method and model selection with justification: for each choice (MY_3, three-sided heating, axial conduction, wall-viscosity correction, apparent friction, CV-L as objective, SLSQP with integer-channel polish) the alternatives tested, the evidence (numbers from the validation matrix), and the reason. Include why MY_3 over LG_3.
7. Validation data: why Qu & Mudawar; a table of every quantity taken from the paper (value, unit, location in the paper, status, why the model needs it); why Figs. 4(a), 5, 6 and why compare at the thermocouple plane and plenum to plenum; how a student would extract the data by hand with WebPlotDigitizer (step by step); how we actually did it (600-dpi rendering, frame and tick detection, WPD calibration and blob detection run headless, template matching for overlapping markers, partly hidden and rejected points, figure G); the recheck and its results; the reference tables used to check correlation coefficients.
8. Validation results: table, parity plots, model-by-model MAPE, effect of digitizing uncertainty, how validation transfers to our geometry (dimensionless comparison, aspect-ratio extrapolation), limitations.
Part B (sections 9-14, appendices, export):
9. Second-law analysis: entropy balances for each control volume, the three loss terms, the analytical optimum and why the numerical optimum differs with developing flow.
10. Design studies and results: Studies 1-4 plus D8, D7, D5 and the comparison with the fully developed model; what each result means physically.
11. Code structure: what each module does, inputs and outputs, how they connect (figures D and E), how to run everything, test coverage, numerical checks.
12. Conclusions answering the central question with numbers.
13. Limitations and future work.
14. References: full citations, only sources already cited in the repo docs; every reference cited in the text.
Then write the Abstract. Appendices: A, assumption table; B, checklist mapping each promise in docs/proposal_submitted.md to where the report delivers it or why it changed; C, commands to reproduce every number.
Finally re-read the whole report against the CSVs and fix any mismatched number, and export docs/final_report.docx (pandoc if available, otherwise python-docx).

## Phase 4: wrap up
- Update README.md (results summary with the validation figures, how to run) and docs/project_status.md.
- Write docs/presentation_outline.md: 10-12 slides, one line of message per slide and which figure goes on it.
- Run the tests one last time and give the final summary: what was completed, any number not verified, what a person still has to check.
