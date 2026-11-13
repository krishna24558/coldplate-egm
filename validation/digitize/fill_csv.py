"""Copy the digitized points (validation/data/raw/fig*_points.csv) into the
benchmark CSVs read by coldplate.benchmark.compare().

    python validation/digitize/fill_csv.py

Status values written:
  digitized                 marker fully visible, centroid found
  digitized_partly_hidden   second marker partly hidden behind another one at
                            nearly the same Re (repeat run); position less certain,
                            not used in the MAPE by default
  rejected                  listed in REJECT below with the reason (kept for the record)
Reading uncertainty in `notes`: 1 px centroid error, plus h/6 for triangles
(area centroid vs. the plotting anchor is not known), converted with the
calibration scale of that panel.
"""

import csv
import json
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
DATA = RAW.parent

# Manual QC decisions after inspecting the overlays (panel, series, Re, value, reason).
REJECT = [
    ("fig5", "100", 444, 40.7,
     "square-template hit on the second (partly hidden) 200 W/cm2 triangle at Re 445; "
     "the 100 W/cm2 point at Re 442 is 20.4 K"),
]


def _rejected(panel, series, x, y):
    for p, s, re, v, why in REJECT:
        if p == panel and s == series and abs(x - re) < 6 and abs(y - v) < 0.5:
            return why
    return None


def load(panel):
    rows = list(csv.DictReader(open(RAW / f"{panel}_points.csv")))
    meta = json.loads((RAW / f"{panel}_meta.json").read_text())
    return rows, meta


def unc(meta, shape):
    px = 1.0 + (3.0 if shape.startswith("tri") else 0.0)
    return px / meta["px_per_y_unit"], 1.0 / meta["px_per_x_unit"]


def status_and_note(panel, r, meta):
    x, y = float(r["x"]), float(r["y"])
    why = _rejected(panel, r["series"], x, y)
    uy, ux = unc(meta, r["shape"])
    note = (f"{r['shape']} at px ({float(r['px']):.1f}, {float(r['py']):.1f}) on 600-dpi page "
            f"{meta['page']}; reading uncertainty about +/-{uy:.3g} (y), +/-{ux:.2g} (Re)")
    if why:
        return "rejected", note + "; REJECTED: " + why
    if r["partly_hidden"] == "True":
        return "digitized_partly_hidden", note + "; partly hidden behind another marker"
    return "digitized", note


def main():
    out = []
    rows, meta = load("fig4a")
    for r in rows:
        st, note = status_and_note("fig4a", r, meta)
        v = float(r["y"])
        out.append({"source_figure": "Fig. 4(a)", "q_eff_W_per_cm2": r["series"],
                    "Re": f"{float(r['x']):.1f}", "dP_axis_value": f"{v:.4f}",
                    "dP_axis_unit": "bar", "dP_Pa": f"{v * 1e5:.0f}", "status": st,
                    "notes": note})
    out.sort(key=lambda d: (d["q_eff_W_per_cm2"], float(d["Re"])))
    with open(DATA / "qu_mudawar_dP.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    th = []
    for panel, fig in (("fig5", "Fig. 5"), ("fig6a", "Fig. 6(a)"), ("fig6b", "Fig. 6(b)")):
        rows, meta = load(panel)
        for r in rows:
            st, note = status_and_note(panel, r, meta)
            if panel == "fig5":
                q, quantity = r["series"], "water_temperature_rise"
            else:
                q, quantity = ("100" if panel == "fig6a" else "200"), r["series"]
            th.append({"source_figure": fig, "q_eff_W_per_cm2": q, "quantity": quantity,
                       "Re": f"{float(r['x']):.1f}", "value": f"{float(r['y']):.3f}",
                       "unit": "K_above_inlet", "status": st, "notes": note})
    th.sort(key=lambda d: (d["source_figure"], d["quantity"], d["q_eff_W_per_cm2"], float(d["Re"])))
    with open(DATA / "qu_mudawar_thermal.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(th[0]))
        w.writeheader()
        w.writerows(th)
    n = lambda rows, s: sum(r["status"] == s for r in rows)  # noqa: E731
    print(f"dP: {len(out)} rows ({n(out, 'digitized')} digitized, "
          f"{n(out, 'digitized_partly_hidden')} partly hidden, {n(out, 'rejected')} rejected)")
    print(f"thermal: {len(th)} rows ({n(th, 'digitized')} digitized, "
          f"{n(th, 'digitized_partly_hidden')} partly hidden, {n(th, 'rejected')} rejected)")


if __name__ == "__main__":
    main()
