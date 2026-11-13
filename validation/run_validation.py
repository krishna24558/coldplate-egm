"""Compare every correlation combination with the digitized Qu & Mudawar data.

    python validation/run_validation.py            # full matrix, writes validation/results/
    python validation/run_validation.py --plots    # also parity plots for the chosen models

Nothing is tuned: each combination uses the correlations as published, with the
benchmark assumptions B1-B5 (validation/README.md). Thermocouple errors are
percentages of the temperature rise above the inlet; dP errors are percentages
of the measured plenum-to-plenum pressure drop.
"""

import argparse
import csv
import itertools
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from coldplate.benchmark import compare  # noqa: E402
from coldplate.correlations import FRICTION_MODELS, NUSSELT_MODELS  # noqa: E402

OUT = ROOT / "validation" / "results"


def thermal_matrix():
    rows = []
    for nu, axial, visc in itertools.product(NUSSELT_MODELS, (False, True), (False, True)):
        r = compare(nusselt_model=nu, axial_conduction=axial, friction_model="fd",
                    viscosity_correction=visc)
        th = r["thermal"]
        if not th:
            return []
        tc = [t for t in th if t["quantity"].startswith("TC")]
        wr = [t for t in th if not t["quantity"].startswith("TC")]
        err = np.array([t["error"] for t in tc])
        per_tc = {f"MAPE_{k}": float(np.mean([abs(t["error"]) for t in tc if t["quantity"] == k]))
                  for k in sorted({t["quantity"] for t in tc})}
        rows.append({
            "nusselt_model": nu, "axial_conduction": axial, "viscosity_correction": visc,
            "n_TC": len(tc),
            "MAPE_TC": float(np.mean(np.abs(err))) if len(err) else None,
            "bias_TC": float(np.mean(err)) if len(err) else None,
            "max_abs_TC": float(np.max(np.abs(err))) if len(err) else None,
            **per_tc,
            "MAPE_water_dT": float(np.mean([abs(t["error"]) for t in wr])) if wr else None,
        })
    return rows


def dp_matrix(nu="MY_3", axial=True):
    """Friction choices, with the thermal model that sets the wall temperature."""
    rows = []
    for fr, minor, visc in itertools.product(FRICTION_MODELS, (True, False), (False, True)):
        r = compare(friction_model=fr, include_minor=minor, viscosity_correction=visc,
                    nusselt_model=nu, axial_conduction=axial)
        if not r["dP"]:
            return []
        err = np.array([d["error"] for d in r["dP"]])
        rows.append({"friction_model": fr, "minor_losses_K1": minor,
                     "viscosity_correction": visc, "thermal_model": f"{nu}, axial={axial}",
                     "n": len(err),
                     "MAPE_dP": float(np.mean(np.abs(err))), "bias_dP": float(np.mean(err)),
                     "max_abs_dP": float(np.max(np.abs(err)))})
    return rows


def write(rows, name):
    if not rows:
        print(f"{name}: no digitized data yet")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{name}")
    for r in rows:
        print("  " + ", ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
                               for k, v in r.items()))


def parity(nu, axial, fr, minor, visc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = compare(nusselt_model=nu, axial_conduction=axial, friction_model=fr, include_minor=minor,
                viscosity_correction=visc)
    fig, axs = plt.subplots(1, 2, figsize=(9, 4))
    for ax, key, unit, scale in ((axs[0], "dP", "kPa", 1e-3),
                                 (axs[1], "thermal", "K above inlet", 1.0)):
        pts = [p for p in r[key] if key == "dP" or p["quantity"].startswith("TC")]
        if not pts:
            continue
        for q, mk in ((100, "o"), (200, "s")):
            sel = [p for p in pts if p["q_eff"] == q]
            ax.plot([p["measured"] * scale for p in sel], [p["predicted"] * scale for p in sel],
                    mk, mfc="none", label=f"{q} W/cm²")
        lo = min(min(p["measured"], p["predicted"]) for p in pts) * scale
        hi = max(max(p["measured"], p["predicted"]) for p in pts) * scale
        ax.plot([lo, hi], [lo, hi], "k-", lw=0.8)
        if key == "dP":
            for f in (0.9, 1.1):
                ax.plot([lo, hi], [lo * f, hi * f], "k:", lw=0.6)
        ax.set_xlabel(f"measured ({unit})")
        ax.set_ylabel(f"predicted ({unit})")
        mape = r["MAPE_dP"] if key == "dP" else r["MAPE_TC"]
        ax.set_title(f"{'pressure drop' if key == 'dP' else 'thermocouples'}: MAPE {100 * mape:.1f} %")
        ax.legend()
    fig.suptitle(f"Qu & Mudawar (2002): Nu={nu}, axial={axial}, friction={fr}, "
                 f"K-losses={minor}, wall viscosity={visc}", fontsize=9)
    fig.tight_layout()
    path = ROOT / "figures" / "validation_parity.png"
    fig.savefig(path, dpi=150)
    print(f"wrote {path}")


def figure_vs_re(models=(("fd_H1", False, "fd", True, False, "fully developed (as proposed)"),
                         ("MY_3", True, "MY", False, True, "selected model"))):
    """Thermocouple rise and pressure drop vs Re: digitized data and model curves."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from coldplate.benchmark import load_benchmark, predict

    bm = load_benchmark()
    T_in = bm.case.operating.T_in - 273.15
    data = list(csv.DictReader(open(ROOT / "validation/data/qu_mudawar_thermal.csv")))
    dpd = list(csv.DictReader(open(ROOT / "validation/data/qu_mudawar_dP.csv")))
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
    mk = {"TC1": "^", "TC2": "v", "TC3": "s", "TC4": "D"}
    for ax, q, Re_rng in ((axs[0], "100", (139, 1672)), (axs[1], "200", (385, 1289))):
        for tc, m in mk.items():
            pts = [(float(r["Re"]), float(r["value"])) for r in data
                   if r["quantity"] == tc and r["q_eff_W_per_cm2"] == q and r["status"] == "digitized"]
            ax.plot(*zip(*pts), m, color="k", mfc="none", ms=5, label=f"{tc} data")
        Re = np.linspace(*Re_rng, 14)
        for (nu, axl, fr, mi, vi, lab), ls in zip(models, ("--", "-")):
            pr = [predict(bm, float(q), R, nusselt_model=nu, axial_conduction=axl,
                          friction_model=fr, include_minor=mi, viscosity_correction=vi) for R in Re]
            for i in range(4):
                ax.plot(Re, [p.T_tc_C[i] - T_in for p in pr], ls, color=f"C{i}", lw=1.2,
                        label=lab if i == 0 else None)
        ax.set_xlabel("Re")
        ax.set_ylabel("T_tc − T_in (K)")
        ax.set_title(f"Fig. 6({'a' if q == '100' else 'b'}): {q} W/cm²")
        ax.legend(fontsize=7, ncol=2)
    ax = axs[2]
    for q, m in (("100", "s"), ("200", "^")):
        pts = [(float(r["Re"]), float(r["dP_Pa"]) / 1e3) for r in dpd
               if r["q_eff_W_per_cm2"] == q and r["status"] == "digitized"]
        ax.plot(*zip(*pts), m, color="k", mfc="none", ms=5, label=f"{q} W/cm² data")
    for (nu, axl, fr, mi, vi, lab), ls in zip(
            models + (("MY_3", True, "MY", True, True, "selected + K=1 plenum losses"),),
            ("--", "-", ":")):
        Re = np.linspace(139, 1672, 14)
        pr = [predict(bm, 100.0, R, nusselt_model=nu, axial_conduction=axl, friction_model=fr,
                      include_minor=mi, viscosity_correction=vi) for R in Re]
        ax.plot(Re, [p.dP_Pa / 1e3 for p in pr], ls, color="C0", label=f"{lab} (100 W/cm²)")
    ax.set_xlabel("Re")
    ax.set_ylabel("ΔP (kPa)")
    ax.set_title("Fig. 4(a): plenum-to-plenum pressure drop")
    ax.legend(fontsize=7)
    fig.tight_layout()
    path = ROOT / "figures" / "validation_vs_Re.png"
    fig.savefig(path, dpi=150)
    print(f"wrote {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plots", nargs=5, metavar=("NU", "AXIAL", "FRICTION", "MINOR", "VISC"),
                    help="e.g. --plots MY_3 1 MY 0 1")
    ap.add_argument("--skip-matrix", action="store_true")
    ap.add_argument("--vs-re", action="store_true", help="data and model curves vs Re")
    a = ap.parse_args()
    warnings.simplefilter("ignore")
    if not a.skip_matrix:
        write(thermal_matrix(), "thermal_model_matrix.csv")
        write(dp_matrix(), "dP_model_matrix.csv")
    if a.plots:
        nu, ax, fr, mi, vi = a.plots
        parity(nu, ax == "1", fr, mi == "1", vi == "1")
    if a.vs_re:
        figure_vs_re()
