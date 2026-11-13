"""The headless WebPlotDigitizer pipeline recovers known points from a synthetic plot."""

import csv
import json
import shutil

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from validation.digitize.digitize import run  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def test_wpd_recovers_markers(tmp_path):
    xo = np.array([139, 300, 600, 900, 1200, 1672.0]); yo = 0.86 * (xo / 1672) ** 1.3
    xs = np.array([450, 750, 1050, 1289.0]); ys = 0.5 * (xs / 1289) ** 1.3
    fig, ax = plt.subplots(figsize=(4, 3), dpi=150)
    ax.plot(xo, yo, "o", mfc="none", mec="k", ms=6)
    ax.plot(xs, ys, "s", color="k", ms=5)
    ax.set_xlim(0, 1800); ax.set_ylim(0, 1.0)
    fig.canvas.draw()
    H = fig.canvas.get_width_height()[1]
    pix = lambda x, y: [float(ax.transData.transform((x, y))[0]),            # noqa: E731
                        float(H - ax.transData.transform((x, y))[1])]
    fig.savefig(tmp_path / "p.png", dpi=150)
    bb = ax.get_window_extent()
    cfg = {"image": "p.png",
           "calibration": {"x1": pix(0, 0) + [0], "x2": pix(1800, 0) + [1800],
                           "y1": pix(0, 0) + [0], "y2": pix(0, 1) + [1.0]},
           "datasets": [{"name": "all", "fgColor": [0, 0, 0], "colorDistance": 150,
                         "minDia": 3, "maxDia": 30,
                         "mask": [[int(bb.x0) + 4, int(H - bb.y1) + 4, int(bb.x1) - 4, int(H - bb.y0) - 4]]}],
           "classes": {"open": [40, 110], "filled": [111, 200]},
           "raw_csv": "raw.csv"}
    (tmp_path / "c.json").write_text(json.dumps(cfg))
    run(tmp_path / "c.json")
    rows = list(csv.DictReader(open(tmp_path / "raw.csv")))
    for name, xt, yt in (("open", xo, yo), ("filled", xs, ys)):
        got = sorted((float(r["x"]), float(r["y"])) for r in rows if r["series"] == name)
        assert len(got) == len(xt)
        g = np.array(got)
        assert np.max(np.abs(g[:, 0] - xt)) < 0.003 * 1800
        assert np.max(np.abs(g[:, 1] - yt)) < 0.005
