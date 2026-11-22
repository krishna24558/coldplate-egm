"""Phase 1 closing checks on the 1 kW case (no physics changed).

    python analysis/run_phase1_checks.py            # everything
    python analysis/run_phase1_checks.py d7 d5 fd num digit cap   # pick parts

Writes to analysis/results/:
    phase1_pump_cv.csv              D7: pump inside / outside the CV-L control volume
    phase1_plenum_K.csv             D5: K_c + K_e = 0, 1.5, 3
    phase1_fd_vs_validated.csv      proposal's fully developed model vs the validated model
    phase1_numerical_checks.csv     grid independence, energy balance, property iteration
    phase1_digitizing_uncertainty.csv   thermocouple MAPE with the data shifted by its
                                        reading uncertainty
    phase1_flow_cap.csv             Study 2 lost-work optimum with the extra limit
                                    V <= 2 L/min (unconstrained row copied from
                                    phase1_pump_cv.csv)

Design optima use the same grid + SLSQP procedure as Study 2 (run_studies.py).
The digitized data and the validation matrix are not modified or rerun; the
benchmark is evaluated once with the default (selected) model.
"""

import csv
import re
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from coldplate.benchmark import DATA_DIR, _rows, compare, load_benchmark, predict  # noqa: E402
from coldplate.config import Case, Models, lpm  # noqa: E402
from coldplate.model import evaluate  # noqa: E402
from coldplate.optimize import (_polish_flow, best_feasible, compare_designs,  # noqa: E402
                                grid_sweep, optimize_design, optimum_flow, with_design)
from coldplate.properties import enthalpy  # noqa: E402

RES = Path(__file__).resolve().parents[1] / "analysis" / "results"

# Study 2 grids (run_studies.py, full)
WC = [1e-4, 1.25e-4, 1.5e-4, 2e-4, 2.5e-4, 3e-4, 4e-4, 5e-4, 7e-4, 1e-3]
WF = [1e-4, 1.5e-4, 2e-4, 3e-4, 4e-4, 5e-4]
VG = [0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 10, 12]


def write_csv(path: Path, rows: list) -> None:
    keys = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path.name}")


def _row(r, w_c, w_f) -> dict:
    s = r.summary()
    active = [k for k, tol in (("T_dev", 0.05), ("dP", 250.0), ("Re", 5.0))
              if abs(r.margins[k]) < tol]
    return {"w_c_mm": w_c * 1e3, "w_f_mm": w_f * 1e3,
            **{k: s[k] for k in ("N", "V_lpm", "Re", "T_dev_C", "dP_kPa", "W_hyd_W", "W_elec_W",
                                 "X_lost_W", "X_warm_W", "X_gap_W", "X_pump_W", "feasible")},
            "active_constraint": ", ".join(active) if active else "none"}


_cache: dict = {}


def design_set(label: str, case: Case) -> list:
    """Reference point, optimum flow at the reference geometry, min lost work, min R_th."""
    if label in _cache:
        return _cache[label]
    g = case.geometry
    rows = [{"design": "reference 0.2/0.2 mm, 2 L/min", **_row(evaluate(case), g.w_c, g.w_f)}]
    o = optimum_flow(case)
    rows.append({"design": "reference geometry, lost-work optimum flow",
                 **_row(o.result, g.w_c, g.w_f), "V_analytical_lpm": o.V_dot_analytical * 6e4,
                 "X_warm_over_X_pump": o.warm_to_pump_ratio})
    d = compare_designs(case, WC, WF, VG, ("lost_work", "thermal_resistance"))
    for name, key in (("min lost work", "lost_work"), ("min R_th", "thermal_resistance")):
        o = d[key]
        # SLSQP returns a width at its bound as e.g. 0.1000000000028 mm, which drops the
        # whole-channel count from 150 to 149. Snap widths to 1 nm and re-tune the flow.
        w_c, w_f = round(o.w_c, 9), round(o.w_f, 9)
        V = _polish_flow(case, key, w_c, w_f, o.V_dot * 6e4, (0.3, 20.0))
        r = evaluate(with_design(case, w_c=w_c, w_f=w_f, V_dot=lpm(V)))
        rows.append({"design": name, **_row(r, w_c, w_f)})
    a, b = rows[2], rows[3]
    rows[2].update({
        "W_hyd_saving_vs_minRth_pct": 100 * (1 - a["W_hyd_W"] / b["W_hyd_W"]),
        "X_lost_saving_vs_minRth_pct": 100 * (1 - a["X_lost_W"] / b["X_lost_W"]),
        "T_dev_minus_minRth_K": a["T_dev_C"] - b["T_dev_C"]})
    _cache[label] = rows
    for r in rows:
        print(f"  [{label}] {r['design']:44s} w_c {r['w_c_mm']:.3f} w_f {r['w_f_mm']:.3f} "
              f"V {r['V_lpm']:.2f}  T_dev {r['T_dev_C']:.2f}  dP {r['dP_kPa']:.2f}  "
              f"W_hyd {r['W_hyd_W']:.3f}  X_lost {r['X_lost_W']:.2f}  {r['active_constraint']}")
    return rows


def tagged(col: str, value, rows: list) -> list:
    return [{col: value, **r} for r in rows]


def d7_pump_cv() -> None:
    base = Case()
    out = Case(losses=replace(base.losses, pump_inside_cv=False))
    rows = tagged("pump_cv", "inside (W_pump = V dP / eta, default)", design_set("base", base))
    rows += tagged("pump_cv", "outside (W_pump = V dP)", design_set("pump outside", out))
    write_csv(RES / "phase1_pump_cv.csv", rows)


def d5_plenum_K() -> None:
    base = Case()
    rows = []
    for K in (0.0, 1.5, 3.0):
        if K == 1.5:   # the default split K_c = 0.5, K_e = 1.0
            rows += tagged("K_total", K, design_set("base", base))
        else:
            c = Case(losses=replace(base.losses, K_c=K / 2, K_e=K / 2))
            rows += tagged("K_total", K, design_set(f"K={K:g}", c))
    write_csv(RES / "phase1_plenum_K.csv", rows)


def fd_vs_validated() -> None:
    rows = tagged("model", "validated (MY_3 + axial + wall viscosity, MY friction)",
                  design_set("base", Case()))
    rows += tagged("model", "proposal (fd_H1, fd, no axial, no wall viscosity)",
                   design_set("fd", Case(models=Models("fd_H1", "fd", False, False))))
    write_csv(RES / "phase1_fd_vs_validated.csv", rows)


def numerical_checks() -> None:
    rows = []
    case = Case()
    for n in (21, 41, 81):
        r = evaluate(case, n_x=n)
        op = case.operating
        P_out = op.P_in - r.hyd.dP_total
        dH = r.m_dot * (enthalpy(r.th.T_out, P_out, op.fluid) - enthalpy(op.T_in, op.P_in, op.fluid))
        rows.append({"check": "grid", "case": "1 kW reference design (2 L/min)", "n_x": n,
                     "tol": 1e-6, "iterations": r.iterations,
                     "T_dev_C": r.th.T_dev - 273.15, "dP_kPa": r.hyd.dP_total / 1e3,
                     "X_lost_W": r.sl.X_lost,
                     "fluid_enthalpy_rise_minus_Q_over_Q": dH / op.Q - 1,
                     "integral_q_conv_minus_Q_over_Q":
                         float(np.trapezoid(r.th.q_conv, r.th.x)) / op.Q - 1})
    for tol, mx in ((1e-6, 50), (1e-10, 200)):
        r = evaluate(case, tol=tol, max_iter=mx)
        rows.append({"check": "property iteration", "case": "1 kW reference design (2 L/min)",
                     "n_x": 41, "tol": tol, "iterations": r.iterations,
                     "T_dev_C": r.th.T_dev - 273.15, "dP_kPa": r.hyd.dP_total / 1e3,
                     "X_lost_W": r.sl.X_lost})
    bm = load_benchmark()
    for n in (21, 41, 81):
        p = predict(bm, 100.0, 1672.0, n_x=n)
        rows.append({"check": "grid", "case": "Qu & Mudawar 100 W/cm2, Re 1672", "n_x": n,
                     "TC1_C": p.T_tc_C[0], "TC2_C": p.T_tc_C[1], "TC3_C": p.T_tc_C[2],
                     "TC4_C": p.T_tc_C[3], "dP_friction_kPa": p.dP_friction_Pa / 1e3,
                     "dT_water_K": p.dT_water_K})
    write_csv(RES / "phase1_numerical_checks.csv", rows)
    for r in rows:
        print("  ", {k: (round(v, 8) if isinstance(v, float) else v) for k, v in r.items()})


def digitizing_uncertainty() -> None:
    """Shift the thermocouple readings by their reading uncertainty (notes column)."""
    res = compare()   # default = selected model; same rows and order as the CSV filter below
    src = [r for r in _rows("qu_mudawar_thermal.csv", DATA_DIR)
           if r["status"] in ("digitized", "measured")]
    assert len(src) == len(res["thermal"])
    meas, pred, u = [], [], []
    for s, c in zip(src, res["thermal"]):
        if not s["quantity"].startswith("TC"):
            continue
        assert s["unit"] == "K_above_inlet" and abs(float(s["value"]) - c["measured"]) < 1e-9
        m = re.search(r"\+/-\s*([\d.]+)\s*\(y\)", s["notes"])
        if m is None:
            raise ValueError("no reading uncertainty in notes: " + s["notes"])
        meas.append(c["measured"]); pred.append(c["predicted"]); u.append(float(m.group(1)))
    meas, pred, u = map(np.array, (meas, pred, u))

    def stats(mm):
        e = (pred - mm) / mm
        return 100 * float(np.mean(np.abs(e))), 100 * float(np.mean(e))

    rows = []

    def add(name, mm):
        mape, bias = stats(mm)
        rows.append({"case": name, "points": len(mm), "MAPE_TC_pct": mape, "bias_pct": bias})

    add("as digitized", meas)
    add("all readings + reading uncertainty", meas + u)
    add("all readings - reading uncertainty", meas - u)
    rng = np.random.default_rng(0)
    mc = np.array([stats(meas + rng.uniform(-1, 1, len(meas)) * u)[0] for _ in range(2000)])
    rows.append({"case": "independent uniform +/- shifts, 2000 draws (seed 0): mean",
                 "points": len(meas), "MAPE_TC_pct": float(mc.mean())})
    rows.append({"case": "independent uniform +/- shifts: 2.5th percentile",
                 "points": len(meas), "MAPE_TC_pct": float(np.percentile(mc, 2.5))})
    rows.append({"case": "independent uniform +/- shifts: 97.5th percentile",
                 "points": len(meas), "MAPE_TC_pct": float(np.percentile(mc, 97.5))})
    for r in rows:
        r["reading_uncertainty_K"] = f"{u.min():g}-{u.max():g}"
        r["MAPE_change_points"] = r["MAPE_TC_pct"] - rows[0]["MAPE_TC_pct"]
        print("  ", r)
    write_csv(RES / "phase1_digitizing_uncertainty.csv", rows)


def flow_cap(V_cap: float = 2.0) -> None:
    """Study 2 lost-work optimum with the extra limit V <= V_cap (L/min).

    Same procedure as design_set(): grid sweep (flows above the cap left out), SLSQP
    from the best feasible grid point, widths snapped to 1 nm, flow re-tuned with whole
    channels. The cap is applied as the upper flow bound in all three steps. Default
    case otherwise (pump inside CV-L, eta_pump 0.5, K_c + K_e = 1.5).
    """
    case = Case()
    lim = case.limits
    pts = grid_sweep(case, WC, WF, [v for v in VG if v <= V_cap])
    p = best_feasible(pts, "lost_work")
    print(f"  best grid point: w_c {p.w_c * 1e3:.3f} w_f {p.w_f * 1e3:.3f} mm, "
          f"V {p.V_dot * 6e4:.2f} L/min, X_lost {p.result.sl.X_lost:.2f} W")
    bounds = [(max(0.1, lim.w_c_min * 1e3), 1.0), (max(0.1, lim.w_f_min * 1e3), 0.5),
              (0.3, V_cap)]
    o = optimize_design(case, "lost_work", (p.w_c, p.w_f, p.V_dot), bounds=bounds)
    print(f"  SLSQP: {o.message} (success {o.success}); w_c {o.w_c * 1e3:.10f} "
          f"w_f {o.w_f * 1e3:.10f} mm, V {o.V_dot * 6e4:.4f} L/min")
    w_c, w_f = round(o.w_c, 9), round(o.w_f, 9)
    V = _polish_flow(case, "lost_work", w_c, w_f, o.V_dot * 6e4, (0.3, V_cap))
    r = evaluate(with_design(case, w_c=w_c, w_f=w_f, V_dot=lpm(V)))
    capped = {"design": f"min lost work, V <= {V_cap:g} L/min", "source": "this run",
              **_row(r, w_c, w_f)}

    ref = next(q for q in _read_csv(RES / "phase1_pump_cv.csv")
               if q["pump_cv"].startswith("inside") and q["design"] == "min lost work")
    keys = [k for k in capped if k not in ("design", "source")]
    free = {"design": "min lost work, no flow cap",
            "source": "copied from phase1_pump_cv.csv (pump inside)",
            **{k: ref[k] for k in keys}}
    X0 = float(ref["X_lost_W"])
    for row in (free, capped):
        # _row() flags only T_dev, dP and Re; add the width bounds and the flow cap
        wc, wf = float(row["w_c_mm"]) * 1e-3, float(row["w_f_mm"]) * 1e-3
        v = float(row["V_lpm"])
        extra = [k for k, on in (("flow cap", abs(v - V_cap) < 1e-3),
                                 ("w_c bound", abs(wc - lim.w_c_min) < 1e-12),
                                 ("w_f bound", abs(wf - lim.w_f_min) < 1e-12)) if on]
        act = [] if row["active_constraint"] == "none" else [row["active_constraint"]]
        row["active_constraint"] = ", ".join(act + extra) if act + extra else "none"
        row["X_lost_increase_vs_unconstrained_W"] = float(row["X_lost_W"]) - X0
        row["X_lost_increase_vs_unconstrained_pct"] = 100 * (float(row["X_lost_W"]) / X0 - 1)
    rows = [free, capped]
    for q in rows:
        print(f"  {q['design']:36s} w_c {float(q['w_c_mm']):.3f} w_f {float(q['w_f_mm']):.3f} "
              f"N {q['N']} V {float(q['V_lpm']):.3f} dP {float(q['dP_kPa']):.2f} "
              f"T_dev {float(q['T_dev_C']):.2f} X_lost {float(q['X_lost_W']):.3f} "
              f"(+{q['X_lost_increase_vs_unconstrained_pct']:.2f} %) {q['active_constraint']}")
    write_csv(RES / "phase1_flow_cap.csv", rows)


def _read_csv(path: Path) -> list:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


PARTS = {"d7": d7_pump_cv, "d5": d5_plenum_K, "fd": fd_vs_validated,
         "num": numerical_checks, "digit": digitizing_uncertainty, "cap": flow_cap}

if __name__ == "__main__":
    for name in (sys.argv[1:] or list(PARTS)):
        print(f"--- {name}")
        PARTS[name]()
