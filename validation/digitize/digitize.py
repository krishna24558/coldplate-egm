"""Run WebPlotDigitizer (headless, wpd_run.js) on one figure and export a raw CSV.

    python validation/digitize/digitize.py validation/digitize/configs/fig4a.json

Config (JSON):
  image        PNG of the plot (rendered from the PDF, see README)
  calibration  {"x1": [px, py, value], "x2": ..., "y1": ..., "y2": ..., "logX", "logY"}
               pixel positions of two x-axis ticks and two y-axis ticks
  datasets     WPD datasets (mask rectangles, colour, blob diameter range, or "manual" points)
  classes      optional {series_name: [min_area, max_area]}: split one dataset's blobs into
               series by marker area (e.g. open vs filled symbols)
  raw_csv      output CSV (raw digitized points, pixel and data coordinates)

The raw CSV is what a person checks; copying into qu_mudawar_*.csv is done by
fill_csv.py so the conversion is recorded.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent


def run(cfg_path: Path) -> list:
    cfg = json.loads(cfg_path.read_text())
    base = cfg_path.parent
    img = np.asarray(Image.open(base / cfg["image"]).convert("RGBA"))
    H, W = img.shape[:2]
    rgba = base / (Path(cfg["image"]).stem + ".rgba")
    rgba.write_bytes(img.tobytes())
    run_cfg = {"rgba": rgba.name, "width": W, "height": H,
               "calibration": cfg["calibration"], "datasets": cfg["datasets"],
               "out": Path(cfg["image"]).stem + "_wpd.json"}
    tmp = base / (Path(cfg["image"]).stem + "_wpdcfg.json")
    tmp.write_text(json.dumps(run_cfg))
    subprocess.run(["node", str(HERE / "wpd_run.js"), str(tmp)], check=True)
    res = json.loads((base / run_cfg["out"]).read_text())
    rgba.unlink()
    rows = []
    classes = cfg.get("classes")
    for ds in res["datasets"]:
        for p in ds["points"]:
            series = ds["name"]
            if classes and p["area"] is not None:
                hit = [k for k, (lo, hi) in classes.items() if lo <= p["area"] <= hi]
                series = hit[0] if len(hit) == 1 else f"{ds['name']}:UNCLASSIFIED"
            rows.append({"series": series, "x": p["x"], "y": p["y"], "px": p["px"],
                         "py": p["py"], "blob_area_px": p["area"]})
    out = base / cfg["raw_csv"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} points)")
    return rows


if __name__ == "__main__":
    run(Path(sys.argv[1]).resolve())
