"""Run the proposal studies on the 1 kW application case.

    python analysis/run_studies.py            # all studies
    python analysis/run_studies.py --quick    # coarser grids

Writes CSVs to analysis/results/ and PNG figures to figures/.
Numbers depend on the open assumptions in docs/equation_sheet.md (A6-A9, D7)
and on fully developed correlations; treat them as model output, not validated
results, until the Qu & Mudawar comparison is done.
"""

import argparse
import csv
import sys
from dataclasses import replace
from pathlib import Path

# Works without `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from coldplate.config import Case, lpm  # noqa: E402
from coldplate.model import evaluate  # noqa: E402
from coldplate.optimize import (  # noqa: E402
    _polish_flow, compare_designs, flow_sweep, optimum_flow, with_design,
)

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "analysis" / "results"
FIG = ROOT / "figures"


def write_csv(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def study1_flow_sweep(case: Case) -> None:
    V = np.round(np.concatenate([np.arange(0.5, 2, 0.25), np.arange(2, 12.5, 0.5)]), 3)
    rows = [{**r.summary()} for r in flow_sweep(case, V) if r is not None]
    write_csv(RES / "study1_flow_sweep.csv", rows)
    o = optimum_flow(case)
    print(f"Study 1: lost-work optimum {o.V_dot*6e4:.2f} L/min (analytical "
          f"{o.V_dot_analytical*6e4:.2f}), X_lost {o.result.sl.X_lost:.2f} W, "
          f"X_warm/X_pump {o.warm_to_pump_ratio:.2f}, T_dev {o.result.th.T_dev-273.15:.1f} C")

    v = [r["V_lpm"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(v, [r["X_lost_W"] for r in rows], lw=2.2, label="Total lost work")
    ax.plot(v, [r["X_gap_W"] for r in rows], ls=":", label="Base-to-coolant")
    ax.plot(v, [r["X_warm_W"] for r in rows], label="Coolant warming")
    ax.plot(v, [r["X_pump_W"] for r in rows], ls="--", label="Pumping")
    ax.axvline(o.V_dot * 6e4, color="0.5", lw=0.8)
    ax.set_xlabel("Coolant flow (L/min)")
    ax.set_ylabel("Lost work, T0·S_gen (W)")
    ax.set_title(f"Lost work minimum at {o.V_dot*6e4:.1f} L/min "
                 f"(0.2 mm channels and fins, 1 kW)", fontsize=10)
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "study1_flow_sweep.png", dpi=150)
    plt.close(fig)


def study2_designs(case: Case, quick: bool) -> None:
    wc = [1e-4, 1.5e-4, 2e-4, 3e-4, 5e-4, 1e-3] if quick else \
        [1e-4, 1.25e-4, 1.5e-4, 2e-4, 2.5e-4, 3e-4, 4e-4, 5e-4, 7e-4, 1e-3]
    wf = [1e-4, 2e-4, 3e-4, 5e-4] if quick else [1e-4, 1.5e-4, 2e-4, 3e-4, 4e-4, 5e-4]
    V = [0.5, 1, 2, 4, 8, 12] if quick else [0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 10, 12]
    designs = compare_designs(case, wc, wf, V,
                              ("lost_work", "thermal_resistance", "hydraulic_power"))
    rows = [{"design": "reference (0.2/0.2 mm, 2 L/min)", "w_c_mm": 0.2, "w_f_mm": 0.2,
             **evaluate(case).summary()}]
    for name, d in designs.items():
        if d is None:
            print(f"Study 2: no feasible grid point for {name}")
            continue
        rows.append({"design": f"min {name}", "w_c_mm": d.w_c * 1e3, "w_f_mm": d.w_f * 1e3,
                     **d.result.summary()})
    write_csv(RES / "study2_designs.csv", rows)
    print("Study 2:")
    for r in rows:
        print(f"  {r['design']:34s} w_c {r['w_c_mm']:.3f} w_f {r['w_f_mm']:.3f} "
              f"V {r['V_lpm']:.2f} L/min  T_dev {r['T_dev_C']:.1f} C  dP {r['dP_kPa']:.1f} kPa  "
              f"W_hyd {r['W_hyd_W']:.3f} W  X_lost {r['X_lost_W']:.2f} W  feasible {r['feasible']}")


def study3_inlet(case: Case) -> None:
    g = case.geometry
    rows = []
    V = 4.0
    for T in np.arange(20, 60.1, 2.5):   # proposal range 20-50 C; extended to show the crossover
        c = with_design(case, T_in=T + 273.15)
        V = _polish_flow(c, "lost_work", g.w_c, g.w_f, V, (0.3, 20.0))
        r = evaluate(with_design(c, V_dot=lpm(V)))
        # Lowest possible device temperature at this geometry (infinite flow):
        floor_C = T + case.operating.Q * (r.th.R_conv + r.th.R_base + r.th.R_tim)
        T_lim_C = case.limits.T_dev_max - 273.15
        violated = [k for k, v in r.margins.items() if v < 0]
        status = ("infeasible at any flow" if floor_C > T_lim_C else
                  "infeasible: " + ", ".join(violated) + " limit" if not r.feasible else
                  "T_dev limit binding" if abs(r.margins["T_dev"]) < 0.05 else
                  "entropy optimum")
        rows.append({**r.summary(), "T_dev_floor_C": floor_C, "status": status})
    write_csv(RES / "study3_inlet_temperature.csv", rows)
    bind = [r["T_in_C"] for r in rows if r["status"] != "entropy optimum"]
    print(f"Study 3: entropy optimum feasible up to T_in = "
          f"{max(r['T_in_C'] for r in rows if r['status'] == 'entropy optimum'):.1f} C; "
          f"device limit governs from {min(bind):.1f} C" if bind else
          "Study 3: device limit never binds at the reference geometry")

    t = np.array([r["T_in_C"] for r in rows])
    ok = np.array([not r["status"].startswith("infeasible") for r in rows])
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    ax[0].plot(t[ok], [r["V_lpm"] for r, k in zip(rows, ok) if k], marker="o")
    if (~ok).any():
        ax[0].axvspan(t[~ok].min() - 1.25, t.max() + 1.25, color="0.85")
        ax[0].text(t[~ok].min(), ax[0].get_ylim()[1] * 0.97, " no feasible flow", va="top",
                   fontsize=8, color="0.3")
    ax[0].set_xlabel("Inlet temperature (°C)")
    ax[0].set_ylabel("Constrained optimum flow (L/min)")
    ax[0].grid(alpha=0.3)
    ax[1].plot(t[ok], [r["X_out_W"] for r, k in zip(rows, ok) if k], marker="o",
               label="Exergy carried by outlet water")
    ax[1].plot(t[ok], [r["X_lost_W"] for r, k in zip(rows, ok) if k], marker="s",
               label="Lost work")
    ax[1].axhline(0, color="0.5", lw=0.6)
    ax[1].set_xlabel("Inlet temperature (°C)  [dead state 25 °C]")
    ax[1].set_ylabel("W")
    ax[1].legend(frameon=False)
    ax[1].grid(alpha=0.3)
    fig.suptitle("Reference geometry (0.2 mm), lost-work optimum flow with T_dev ≤ 90 °C; "
                 "proposal range 20-50 °C, extended to 60 °C", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "study3_inlet_temperature.png", dpi=150)
    plt.close(fig)


def study4_sensitivity(case: Case) -> None:
    base = optimum_flow(case)
    rows = []

    def add(name, value, c):
        o = optimum_flow(c)
        rows.append({"parameter": name, "value": value, "V_opt_lpm": o.V_dot * 6e4,
                     "X_lost_W": o.result.sl.X_lost, "T_dev_C": o.result.th.T_dev - 273.15})

    for f in (0.5, 1.5):
        add("R_tim", case.materials.R_tim_jc * f,
            replace(case, materials=replace(case.materials, R_tim_jc=case.materials.R_tim_jc * f)))
    for eta in (0.3, 0.7):
        add("eta_pump", eta, replace(case, losses=replace(case.losses, eta_pump=eta)))
    for T0 in (283.15, 308.15):
        add("T0_C", T0 - 273.15, replace(case, dead_state=replace(case.dead_state, T0=T0)))
    for K in (0.0, 3.0):
        add("K_total", K, replace(case, losses=replace(case.losses, K_c=K / 2, K_e=K / 2)))
    write_csv(RES / "study4_sensitivity.csv", rows)
    print(f"Study 4 (baseline: V_opt {base.V_dot*6e4:.2f} L/min, X_lost "
          f"{base.result.sl.X_lost:.2f} W, T_dev {base.result.th.T_dev-273.15:.1f} C):")
    for r in rows:
        print(f"  {r['parameter']:9s} {r['value']:<7.3g} V_opt {r['V_opt_lpm']:.2f} L/min  "
              f"X_lost {r['X_lost_W']:.2f} W  T_dev {r['T_dev_C']:.1f} C")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    case = Case()
    r = evaluate(case)
    print("Reference design:", {k: (round(v, 4) if isinstance(v, float) else v)
                                for k, v in r.summary().items()})
    study1_flow_sweep(case)
    study2_designs(case, args.quick)
    study3_inlet(case)
    study4_sensitivity(case)


if __name__ == "__main__":
    main()
