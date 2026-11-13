"""Digitize Qu & Mudawar (2002) Figs. 4(a), 5, 6(a), 6(b) from the PDF.

    python validation/digitize/qm_figures.py path/to/qu_mudawar_2002.pdf

Steps per panel (all recorded in validation/data/raw/):
  1. Render the page at 600 dpi (pdftoppm; the figures are 600-dpi scans, so this
     is the native resolution).
  2. Fit the four frame lines (the scans are slightly rotated) and detect the
     major tick marks; the tick values below were assigned by reading the axis
     labels in the figure.
  3. Find the filled markers by template matching pursuit (markers.py), which
     also recovers markers partly hidden behind others. The legend is excluded.
  4. Convert pixel centroids to data with WebPlotDigitizer's own XYAxes
     calibration (wpd_run.js, 4-point calibration on major ticks, rotation
     corrected) and, as a cross-check, run WPD's blob detector on the same
     image: isolated markers must agree within 1.5 px.
  5. Write <panel>_points.csv (pixel and data coordinates, shape, series, flags)
     and <panel>_overlay.png (every detected marker circled) for the hard check.
"""

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from frames import find_frame, point_on, ticks  # noqa: E402
from markers import build_templates, dedupe, find_markers  # noqa: E402

RAW = HERE.parents[0] / "data" / "raw"

# Major-tick values read from the axis labels. box = approximate frame
# (top, bottom, left, right) in 600-dpi page pixels.
PANELS = {
    "fig4a": dict(page=7, box=(4750, 5477, 697, 2137), xmaj=list(range(200, 1601, 200)),
                  ymaj=[0.8, 0.6, 0.4, 0.2], series={"square": "100", "tri_up": "200"},
                  quantity="dP", yunit="bar"),
    "fig5": dict(page=8, box=(773, 1487, 2650, 4075), xmaj=list(range(200, 1601, 200)),
                 ymaj=[60, 40, 20], series={"square": "100", "tri_up": "200"},
                 quantity="water_temperature_rise", yunit="K"),
    "fig6a": dict(page=9, box=(774, 1494, 698, 2138), xmaj=list(range(200, 1601, 200)),
                  ymaj=[80, 60, 40, 20],
                  series={"tri_up": "TC1", "tri_down": "TC2", "square": "TC3", "diamond": "TC4"},
                  q=100, quantity="TC_rise", yunit="K"),
    "fig6b": dict(page=9, box=(768, 1488, 2530, 3965), xmaj=list(range(200, 1601, 200)),
                  ymaj=[100, 80, 60, 40],
                  series={"tri_up": "TC1", "tri_down": "TC2", "square": "TC3", "diamond": "TC4"},
                  q=200, quantity="TC_rise", yunit="K", templates_from="fig6a"),
}
_TEMPLATES = {}   # templates per panel, reused by panels drawn in the same style
COLORS = {"square": (230, 0, 0), "diamond": (0, 150, 0), "tri_up": (0, 0, 255),
          "tri_down": (255, 140, 0)}


def render(pdf: Path, page: int, out: Path) -> np.ndarray:
    stem = out / f"page{page}"
    if not Path(f"{stem}-{page:02d}.pgm").exists() and not Path(f"{stem}-{page}.pgm").exists():
        subprocess.run(["pdftoppm", "-r", "600", "-gray", "-f", str(page), "-l", str(page),
                        str(pdf), str(stem)], check=True)
    f = next(out.glob(f"page{page}-*.pgm"))
    return np.array(Image.open(f))


def calibrate(ink, cfg):
    fits = find_frame(ink, cfg["box"], band=25)
    xt = [p for p, n in ticks(ink, fits, "bottom") if n >= 12]
    yt = [p for p, n in ticks(ink, fits, "left") if n >= 12]
    if len(xt) != len(cfg["xmaj"]) or len(yt) != len(cfg["ymaj"]):
        raise RuntimeError(f"major ticks found {len(xt)}/{len(yt)}, expected "
                           f"{len(cfg['xmaj'])}/{len(cfg['ymaj'])}")
    cal = {"x1": [*point_on(fits, "bottom", xt[0]), cfg["xmaj"][0]],
           "x2": [*point_on(fits, "bottom", xt[-1]), cfg["xmaj"][-1]],
           "y1": [*point_on(fits, "left", yt[-1]), cfg["ymaj"][-1]],
           "y2": [*point_on(fits, "left", yt[0]), cfg["ymaj"][0]],
           "logX": False, "logY": False}
    # linearity check of the tick spacing (scan distortion), px
    sx = np.polyfit(cfg["xmaj"], xt, 1)
    sy = np.polyfit(cfg["ymaj"], yt, 1)
    res = {"x_tick_residual_px": float(np.max(np.abs(np.polyval(sx, cfg["xmaj"]) - xt))),
           "y_tick_residual_px": float(np.max(np.abs(np.polyval(sy, cfg["ymaj"]) - yt))),
           "px_per_x_unit": float(sx[0]), "px_per_y_unit": float(-sy[0])}
    return fits, cal, res


def wpd(image_gray, cal, datasets, workdir: Path):
    H, W = image_gray.shape
    rgba = np.dstack([image_gray] * 3 + [np.full_like(image_gray, 255)]).astype(np.uint8)
    (workdir / "img.rgba").write_bytes(rgba.tobytes())
    cfg = {"rgba": "img.rgba", "width": W, "height": H, "calibration": cal,
           "datasets": datasets, "out": "res.json"}
    (workdir / "cfg.json").write_text(json.dumps(cfg))
    subprocess.run(["node", str(HERE / "wpd_run.js"), str(workdir / "cfg.json")], check=True,
                   capture_output=True)
    return json.loads((workdir / "res.json").read_text())["datasets"]


def process(name, cfg, pdf, work):
    page = render(pdf, cfg["page"], work)
    ink = page < 128
    fits, cal, res = calibrate(ink, cfg)
    T, B, L, R = cfg["box"]
    ink = ink.copy()
    # erase frame tick marks (all four sides) so markers sitting near the frame survive
    for side in ("bottom", "top", "left", "right"):
        for pos, n in ticks(ink, fits, side):
            c, r = point_on(fits, side, pos)
            c, r = int(round(c)), int(round(r))
            if side in ("bottom", "top"):
                sgn = -1 if side == "bottom" else 1
                rr = sorted((r, r + sgn * (n + 5)))
                ink[rr[0]:rr[1] + 1, c - 4:c + 5] = False
            else:
                sgn = 1 if side == "left" else -1
                cc = sorted((c, c + sgn * (n + 5)))
                ink[r - 4:r + 5, cc[0]:cc[1] + 1] = False
    m = 6                                     # just inside the frame lines
    r0, c0 = T + m, L + m
    sub = ink[r0:B - m, c0:R - m].copy()
    # exclude the legend and any other large non-marker object (frames, text blocks)
    lab, _ = ndi.label(sub, structure=np.ones((3, 3)))
    excl = []
    for sl in ndi.find_objects(lab):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if (h > 150 and w > 150) or h > 400 or w > 400:   # legend box, frame remnants
            excl.append((sl[0].start, sl[1].start, sl[0].stop, sl[1].stop))
            sub[sl[0].start:sl[0].stop, sl[1].start:sl[1].stop] = False
    if cfg.get("templates_from"):
        if cfg["templates_from"] not in _TEMPLATES:
            process(cfg["templates_from"], PANELS[cfg["templates_from"]], pdf, work)
        tm = _TEMPLATES[cfg["templates_from"]]
    else:
        tm = build_templates(sub)
    tm = {k: v for k, v in tm.items() if k in cfg["series"]}
    _TEMPLATES[name] = tm
    mk, left = find_markers(sub, tm, min_cov=0.82, max_spill=0.45)
    mk = dedupe(mk)
    pts = [[k.col + c0, k.row + r0] for k in mk]
    data = wpd(page, cal, [{"name": "markers", "manual": pts}], work)[0]["points"]
    lookup = {(round(p["px"], 3), round(p["py"], 3)): p for p in data}
    # WPD blob detector on the same masked area, for isolated markers
    mask = [[c0, r0, R - m, B - m]]
    exclude = [[c0 + e[1], r0 + e[0], c0 + e[3], r0 + e[2]] for e in excl]
    blobs = wpd(page, cal, [{"name": "blobs", "mask": mask, "exclude": exclude,
                             "fgColor": [0, 0, 0], "colorDistance": 120,
                             "minDia": 10, "maxDia": 40}], work)[0]["points"]
    rows = []
    for k, p in zip(mk, pts):
        d = lookup[(round(p[0], 3), round(p[1], 3))]
        near = [b for b in blobs if abs(b["px"] - p[0]) < 4 and abs(b["py"] - p[1]) < 4]
        rows.append({
            "panel": name, "series": cfg["series"][k.shape], "shape": k.shape,
            "x": d["x"], "y": d["y"], "px": p[0], "py": p[1],
            "coverage": round(k.coverage, 3), "spill": round(k.spill, 3),
            "partly_hidden": k.hidden,
            "wpd_blob_dpx": (round(float(np.hypot(near[0]["px"] - p[0], near[0]["py"] - p[1])), 2)
                             if len(near) == 1 else ""),
        })
    rows.sort(key=lambda r: (r["series"], r["x"]))
    out_csv = RAW / f"{name}_points.csv"
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    # overlay for the hard check
    pad = 30
    crop = Image.fromarray(page).convert("RGB").crop((L - pad, T - pad, R + pad, B + pad))
    d = ImageDraw.Draw(crop)
    for k, p in zip(mk, pts):
        x, y = p[0] - (L - pad), p[1] - (T - pad)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), outline=COLORS[k.shape], width=2)
        if k.hidden:
            d.rectangle((x - 15, y - 15, x + 15, y + 15), outline=(255, 0, 255), width=2)
    for key in ("x1", "x2", "y1", "y2"):
        x, y = cal[key][0] - (L - pad), cal[key][1] - (T - pad)
        d.line((x - 12, y, x + 12, y), fill=(255, 0, 255), width=2)
        d.line((x, y - 12, x, y + 12), fill=(255, 0, 255), width=2)
    crop.save(RAW / f"{name}_overlay.png")
    lab2, n2 = ndi.label(left, structure=np.ones((3, 3)))
    sizes = ndi.sum(left, lab2, range(1, n2 + 1)) if n2 else []
    meta = {"panel": name, "page": cfg["page"], "calibration": cal, **res,
            "templates": {k: {"shape_px": list(v["mask"].shape), "n_examples": v["n_examples"]}
                          for k, v in tm.items()},
            "n_markers": len(rows), "n_partly_hidden": int(sum(r["partly_hidden"] for r in rows)),
            "unexplained_ink_blobs_over_60px": int(sum(s > 60 for s in sizes)),
            "wpd_blob_check_max_dpx": max([r["wpd_blob_dpx"] for r in rows
                                           if r["wpd_blob_dpx"] != ""], default=None)}
    (RAW / f"{name}_meta.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ("panel", "n_markers", "n_partly_hidden",
                                           "unexplained_ink_blobs_over_60px",
                                           "wpd_blob_check_max_dpx", "x_tick_residual_px",
                                           "y_tick_residual_px")}))
    return rows


if __name__ == "__main__":
    pdf = Path(sys.argv[1]).resolve()
    names = sys.argv[2:] or list(PANELS)
    RAW.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for n in names:
            process(n, PANELS[n], pdf, Path(tmp))
