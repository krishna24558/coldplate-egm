"""Geometry figures for the report.

    python analysis/make_geometry_figures.py

figures/geometry_3d_design.png      3D view of the 1 kW design cold plate + channel cross-section
figures/geometry_design_vs_qm.png   design case vs Qu & Mudawar (2002) unit cells, same scale,
                                    with the dimensionless numbers that show why the benchmark
                                    validates the correlations used for the design
Dimensions come from coldplate/config.py and validation/data/qu_mudawar_geometry.csv.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coldplate.config import Case  # noqa: E402
from coldplate.geometry import derive  # noqa: E402

FIG = ROOT / "figures"
CU = "#c98a4b"      # copper
CU_D = "#9c6331"
WATER = "#7fb3d5"


def box(ax, x0, y0, z0, dx, dy, dz, color, alpha=1.0, edge="k", lw=0.2):
    """Box drawn with only the faces visible from a camera at +x, -y, +z (painter order is
    set by the caller: computed_zorder is off, so boxes must be added back to front)."""
    x = [x0, x0 + dx]
    y = [y0, y0 + dy]
    z = [z0, z0 + dz]
    v = np.array([[x[i], y[j], z[k]] for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    # vertex index = 4i + 2j + k; visible faces: y = y0 (front), z = z1 (top), x = x1 (side)
    faces = [[0, 1, 5, 4], [1, 3, 7, 5], [4, 5, 7, 6]]
    pc = Poly3DCollection([v[f] for f in faces], facecolor=color, edgecolor=edge,
                          linewidths=lw, alpha=alpha)
    ax.add_collection3d(pc)


def design_3d():
    g = Case().geometry
    d = derive(g)
    W, L, H, wc, wf, tb = (v * 1e3 for v in (g.W, g.L, g.H, g.w_c, g.w_f, g.t_b))
    fig = plt.figure(figsize=(13, 5.6))
    ax = fig.add_subplot(1, 2, 1, projection="3d", computed_zorder=False)
    # chip footprint under the base
    box(ax, 0, 0, -0.6, W, L, 0.6, "#555555", alpha=0.9, lw=0.4)
    box(ax, 0, 0, 0, W, L, tb, CU, lw=0.4)                     # base
    pitch = wc + wf
    n = d.N
    x = wc                                                       # channel, then fin
    for i in range(n):
        box(ax, x, 0, tb, wf, L, H, CU if i % 2 else CU_D, lw=0.05)
        x += pitch
    ax.quiver(W * 0.7, -12, tb + H / 2, 0, 9, 0, color="#1f5f99", linewidth=2.5,
              arrow_length_ratio=0.3)
    ax.text(W * 0.7, -14, tb + H + 1.2, "water in", color="#1f5f99", ha="center", fontsize=9)
    ax.quiver(W * 0.7, L + 3, tb + H / 2, 0, 9, 0, color="#b03a2e", linewidth=2.5,
              arrow_length_ratio=0.3)
    ax.text(W * 0.7, L + 13, tb + H + 1.2, "water out", color="#b03a2e", ha="center", fontsize=9)
    ax.set_xlim(0, W)
    ax.set_ylim(-14, L + 14)
    ax.set_zlim(-1, 8)
    ax.set_box_aspect((W, L + 28, 9 * 2.5))     # vertical scale exaggerated x2.5
    ax.view_init(elev=24, azim=-68)
    ax.set_xlabel("across the channels, mm")
    ax.set_ylabel("flow direction, mm")
    ax.set_zlabel("height, mm")
    ax.set_title(f"1 kW design cold plate: 30 × 30 mm copper, {n} channels\n"
                 "lid removed; chip (grey) below the base; vertical scale ×2.5", fontsize=10)

    # cross-section of a few channels, to scale
    a2 = fig.add_subplot(1, 2, 2)
    ncell = 4
    a2.add_patch(Rectangle((0, -tb), ncell * pitch + wf, tb, fc=CU, ec="k"))
    for i in range(ncell + 1):
        a2.add_patch(Rectangle((i * pitch, 0), wf, H, fc=CU, ec="k"))
        if i < ncell:
            a2.add_patch(Rectangle((i * pitch + wf, 0), wc, H, fc=WATER, ec="none"))
    a2.add_patch(Rectangle((0, H), ncell * pitch + wf, 0.25, fc="#d9d9d9", ec="k"))
    a2.add_patch(Rectangle((0, -tb - 0.25), ncell * pitch + wf, 0.25, fc="#555555", ec="k"))

    def dim(x0, y0, x1, y1, text, off=(0, 0), ha="center"):
        a2.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="<->", mutation_scale=8, lw=0.9))
        a2.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], text, fontsize=9, ha=ha)

    dim(wf, H * 0.82, wf + wc, H * 0.82, f"w_c = {wc:.1f} mm", (0, 0.12))
    dim(pitch, H * 0.55, pitch + wf, H * 0.55, f"w_f = {wf:.1f} mm", (0.18, 0.12), ha="left")
    dim(ncell * pitch + wf + 0.12, 0, ncell * pitch + wf + 0.12, H, f" H = {H:.0f} mm", (0.05, 0), ha="left")
    dim(ncell * pitch + wf + 0.12, -tb, ncell * pitch + wf + 0.12, 0, f" t_b = {tb:.0f} mm", (0.05, 0), ha="left")
    a2.text(ncell * pitch / 2, H + 0.4, "lid (adiabatic)", ha="center", fontsize=8)
    a2.text(ncell * pitch / 2, -tb - 0.6, "chip / TIM (R_TIM = 0.02 K/W)", ha="center", fontsize=8)
    a2.text(wf + wc / 2, H * 0.3, "water", rotation=90, ha="center", va="center", fontsize=8)
    a2.set_xlim(-0.2, ncell * pitch + wf + 1.2)
    a2.set_ylim(-tb - 0.9, H + 0.8)
    a2.set_aspect("equal")
    a2.set_xlabel("mm")
    a2.set_title(f"Channel cross-section (to scale): D_h = {d.D_h * 1e3:.3f} mm, "
                 f"H/w_c = {H / wc:.0f}", fontsize=10)
    fig.tight_layout()
    out = FIG / "geometry_3d_design.png"
    fig.savefig(out, dpi=200)
    print("wrote", out)


def design_vs_qm():
    g = Case().geometry
    cells = {
        "1 kW design (this project)": dict(wc=g.w_c * 1e6, wf=g.w_f * 1e6, H=g.H * 1e6, tb=g.t_b * 1e6),
        "Qu & Mudawar (2002) benchmark": dict(wc=231, wf=236, H=713, tb=2462),
    }
    fig, axs = plt.subplots(1, 3, figsize=(14, 5.2), gridspec_kw={"width_ratios": [1, 1, 1.5]})
    for ax, (name, c) in zip(axs[:2], cells.items()):
        pitch = c["wc"] + c["wf"]
        for i in range(3):
            ax.add_patch(Rectangle((i * pitch, 0), c["wf"], c["H"], fc=CU, ec="k"))
            ax.add_patch(Rectangle((i * pitch + c["wf"], 0), c["wc"], c["H"], fc=WATER, ec="none"))
        ax.add_patch(Rectangle((3 * pitch, 0), c["wf"], c["H"], fc=CU, ec="k"))
        ax.add_patch(Rectangle((0, -c["tb"]), 3 * pitch + c["wf"], c["tb"], fc=CU, ec="k"))
        ax.add_patch(Rectangle((0, c["H"]), 3 * pitch + c["wf"], 150,
                               fc="#d9d9d9" if "design" in name else "#f2e6b3", ec="k"))
        ax.set_xlim(-100, 1600)
        ax.set_ylim(-2600, 3400)
        ax.set_aspect("equal")
        ax.set_xlabel("µm")
        ax.set_title(f"{name}\nw_c = {c['wc']:.0f}, w_f = {c['wf']:.0f}, H = {c['H']:.0f} µm",
                     fontsize=9)
        if "Qu" in name:
            ax.plot([0, 3 * pitch + c["wf"]], [-c["tb"], -c["tb"]], "r--", lw=1)
            ax.text(20, -c["tb"] + 80, "thermocouple plane", color="r", fontsize=8)
            ax.text(20, c["H"] + 220, "polycarbonate cover", fontsize=8)
        else:
            ax.text(20, c["H"] + 220, "lid", fontsize=8)
            ax.text(20, -c["tb"] - 250, "chip", fontsize=8)
    axs[1].set_yticklabels([])
    rows = [
        ("Quantity", "Design case", "Qu & Mudawar", "Same regime?"),
        ("Material / fluid", "copper / water", "copper / water", "yes"),
        ("Flow regime", "laminar, single-phase", "laminar, single-phase", "yes"),
        ("Hydraulic diameter D_h", "375 µm", "349 µm", "yes"),
        ("Reynolds number Re", "374 – 917", "139 – 1672", "yes (inside)"),
        ("Heat flux at base", "111 W/cm²", "100, 200 W/cm²", "yes (inside)"),
        ("Thermal entry z* at outlet", "0.017 – 0.043", "0.011 – 0.13", "yes (inside)"),
        ("Prandtl number", "≈ 5 (30 °C inlet)", "≈ 7 (15 °C inlet)", "close"),
        ("Heated walls", "3 (lid on top)", "3 (cover on top)", "yes"),
        ("Aspect ratio H/w_c", "15", "3.1", "NO: extrapolated"),
        ("Channel length L", "30 mm", "44.8 mm", "via z*"),
    ]
    a = axs[2]
    a.axis("off")
    t = a.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="left",
                colWidths=[0.34, 0.24, 0.24, 0.2])
    t.auto_set_font_size(False)
    t.set_fontsize(8.5)
    t.scale(1, 1.55)
    for (r, cidx), cell in t.get_celld().items():
        if r == 0:
            cell.set_text_props(weight="bold")
        if r > 0 and cidx == 3 and rows[r][3].startswith("NO"):
            cell.set_facecolor("#f5c6c6")
    a.set_title("We validate the physics (correlations), not the geometry:\n"
                "the design sits inside the benchmark's dimensionless range except H/w_c",
                fontsize=9)
    fig.suptitle("Unit cells drawn to the same scale", fontsize=10)
    fig.tight_layout()
    out = FIG / "geometry_design_vs_qm.png"
    fig.savefig(out, dpi=200)
    print("wrote", out)


if __name__ == "__main__":
    design_3d()
    design_vs_qm()
