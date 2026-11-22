"""Report figures (Figures 3-9 and 12-17 of docs/final_report.md).

    python analysis/make_report_figures.py              # all, in order
    python analysis/make_report_figures.py J2 J1        # selected figures

figures/fig_J2_designs.png           Study 2: four designs, lost-work split, hydraulic power, T_dev
figures/fig_J1_flow_sweep.png        Study 1: lost-work terms vs flow, numerical and Eq. (21) optimum
figures/fig_J3_inlet_temperature.png Study 3: optimum flow, T_dev, lost work, outlet exergy vs T_in
figures/fig_J5_below_limit.png       Study 5: lost-work terms and optimum flow vs w_c = w_f
figures/fig_J4_sensitivity.png       Study 4: change of optimum flow, lost work, T_dev per input
figures/fig_H_model_mape.png         Benchmark MAPE by model combination (thermal and pressure drop)
figures/fig_B_network.png            Fig. 3: thermal network, one station and along the channel
figures/fig_C_control_volumes.png    Fig. 4: CV-P, CV-C, CV-L and the loss terms of each
figures/fig_D_code_structure.png     Fig. 5: modules and the data passed between them
figures/fig_E_solver_flowchart.png   Fig. 6: model.evaluate() solution procedure
figures/fig_F_benchmark_setup.png    Fig. 8: Qu and Mudawar test section as modelled
figures/fig_G_data_extraction.png    Fig. 9: Fig. 6(a) original, detection overlay, calibrated values
figures/fig_I_local_Nu.png           Fig. 7: local Nu(x) of fd_H1, LG_3, MY_3 (benchmark, Re 900)

Data sources. J1-J5, H and the numbers on C and F: the CSVs in analysis/results/ and
validation/results/ (no model run). B: config.py inputs and thermal.stations() only.
F: validation/data/*.csv. G: validation/data/raw/ (the PDF scan, decoded here, the
overlay, meta and points files). I: coldplate.correlations.local_nusselt() with the
benchmark geometry from validation/data/ and Pr from CoolProp (no model run).
D and E are drawn from the code (coldplate/model.py, thermal.py), not from data.
One shared style: the same colour, line style, marker and hatch for each loss term in
every figure, one style for limits, and colours chosen so that the figures stay
readable in grayscale (identity is also carried by line style, marker or hatch).
"""

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "analysis" / "results"
VRES = ROOT / "validation" / "results"
FIG = ROOT / "figures"
DPI = 200

# ---------------------------------------------------------------- shared style
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.labelsize": 9,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "legend.frameon": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "0.3",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "0.88",
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "xtick.color": "0.25",
    "ytick.color": "0.25",
    "lines.markersize": 5,
    "hatch.linewidth": 0.8,
    "savefig.dpi": DPI,
})

INK = "0.1"
MUTED = "0.4"
NAVY = "#1F4E79"      # base-to-coolant (gap): dark in grayscale
VERM = "#D55E00"      # coolant warming: mid gray
GOLD = "#D49100"      # pumping: light-mid gray
PURPLE = "#7B3294"    # outlet exergy (J3); not a lost-work term
NEUTRAL = "0.45"      # single-series bars
SHADE = "0.93"        # infeasible / out-of-range regions
LIMIT = dict(color="0.2", ls=(0, (5, 2.5)), lw=1.0)   # every design limit

# Lost-work terms: same look in every figure (lines: J1, J5; bars: J2).
TERMS = ("X_lost_W", "X_gap_W", "X_warm_W", "X_pump_W")
LINE = {
    "X_lost_W": dict(color="black", ls="-", lw=2.4, marker="o",
                     label=r"Total lost work $X_\mathrm{lost}$"),
    "X_gap_W": dict(color=NAVY, ls=(0, (6, 2.5)), lw=1.8, marker="s",
                    label=r"Base-to-coolant heat transfer $X_\mathrm{gap}$"),
    "X_warm_W": dict(color=VERM, ls=(0, (7, 2, 1.5, 2)), lw=1.8, marker="^",
                     label=r"Coolant warming $X_\mathrm{warm}$"),
    "X_pump_W": dict(color=GOLD, ls=(0, (1.6, 1.4)), lw=2.2, marker="D",
                     label=r"Pumping $X_\mathrm{pump}$"),
}
BAR = {
    "X_gap_W": dict(color=NAVY, hatch=None, hatchcolor="white",
                    label=r"Base-to-coolant heat transfer $X_\mathrm{gap}$"),
    "X_warm_W": dict(color=VERM, hatch="\\\\\\", hatchcolor="white",
                     label=r"Coolant warming $X_\mathrm{warm}$"),
    "X_pump_W": dict(color=GOLD, hatch="////", hatchcolor="0.15",
                     label=r"Pumping $X_\mathrm{pump}$"),
}


# ---------------------------------------------------------------- helpers
def _val(s: str):
    if s in ("True", "False"):
        return s == "True"
    try:
        return float(s)
    except ValueError:
        return s


def read(path: Path) -> list:
    with open(path, newline="") as fh:
        return [{k: _val(v) for k, v in r.items()} for r in csv.DictReader(fh)]


def num(v: float, fmt: str = "{:.2f}") -> str:
    """Number with a typographic minus sign."""
    return fmt.format(v).replace("-", "−")


def col(rows, key) -> np.ndarray:
    return np.array([r[key] for r in rows], dtype=float)


def reference_optimum() -> dict:
    """Lost-work optimum of the reference geometry (pump inside CV-L, the default)."""
    return next(r for r in read(RES / "phase1_pump_cv.csv")
                if r["pump_cv"].startswith("inside")
                and r["design"] == "reference geometry, lost-work optimum flow")


def save(fig, name: str) -> Path:
    FIG.mkdir(exist_ok=True)
    out = FIG / name
    fig.savefig(out, dpi=DPI, bbox_inches="tight", pad_inches=0.06, facecolor="white")
    plt.close(fig)
    print(f"wrote {out.relative_to(ROOT)}")
    return out


def fig_title(fig, ax, text: str, y: float) -> None:
    """Figure title in the same size and weight in every figure, left-aligned with the
    first axes."""
    fig.suptitle(text, x=ax.get_position().x0, ha="left", fontsize=9, fontweight="normal",
                 y=y)


def bar_term(ax, x, h, bottom, key, width):
    s = BAR[key]
    return ax.bar(x, h, width, bottom=bottom, color=s["color"], hatch=s["hatch"],
                  hatchcolor=s["hatchcolor"], edgecolor="white", linewidth=1.0)


def term_patches():
    return [Patch(facecolor=BAR[k]["color"], hatch=BAR[k]["hatch"], edgecolor="white",
                  label=BAR[k]["label"]) for k in ("X_pump_W", "X_warm_W", "X_gap_W")]


def fix_patch_hatch(legend):
    """Legend patches take their hatch colour from the edge colour; match the bars."""
    for p, k in zip(legend.get_patches(), ("X_pump_W", "X_warm_W", "X_gap_W")):
        p.set_hatchcolor(BAR[k]["hatchcolor"])
        p.set_edgecolor("white")


# ---------------------------------------------------------------- Figure 14 (J2)
def fig_J2():
    """Study 2: the four designs side by side (study2_designs.csv)."""
    rows = read(RES / "study2_designs.csv")
    order = ["reference", "min lost_work", "min thermal_resistance", "min hydraulic_power"]
    rows = [next(r for r in rows if r["design"].startswith(o)) for o in order]
    name_long = ["Reference", "Min lost work", r"Min $R_\mathrm{th}$", "Min hydraulic power"]
    name_short = ["Reference", "Min\nlost work", "Min\n" + r"$R_\mathrm{th}$",
                  "Min\nhydraulic\npower"]
    ticks = [f"{n}\n{r['w_c_mm']:.3f} / {r['w_f_mm']:.3f} mm\n{r['V_lpm']:.2f} L/min"
             for n, r in zip(name_long, rows)]
    x = np.arange(4)
    iL, iR = 1, 2           # min lost work, min R_th

    fig = plt.figure(figsize=(7.4, 7.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1.0], hspace=0.62, wspace=0.32)
    a = fig.add_subplot(gs[0, :])
    b = fig.add_subplot(gs[1, 0])
    c = fig.add_subplot(gs[1, 1])

    # (a) lost work split into its three terms
    w = 0.5
    bottom = np.zeros(4)
    for key in ("X_gap_W", "X_warm_W", "X_pump_W"):
        h = col(rows, key)
        bar_term(a, x, h, bottom, key, w)
        for xi, hi, bi in zip(x, h, bottom):
            if hi >= 2.0:   # label segments that are big enough to see
                a.text(xi + w / 2 + 0.04, bi + hi / 2, f"{hi:.2f}", va="center", ha="left",
                       fontsize=7.5, color=MUTED)
        bottom += h
    tot = col(rows, "X_lost_W")
    for xi, t in zip(x, tot):
        a.text(xi, t + 1.5, f"{t:.2f} W", ha="center", va="bottom", fontsize=8.5,
               fontweight="bold", color=INK)
    save_L = 100 * (tot[iR] - tot[iL]) / tot[iR]
    ya = tot[iR] + 8.5          # above both total labels
    a.annotate("", xy=(iL, ya), xytext=(iR, ya),
               arrowprops=dict(arrowstyle="->", color=INK, lw=0.9))
    a.text((iL + iR) / 2, ya + 1.0, f"−{save_L:.1f} %", ha="center", va="bottom",
           fontsize=8.5, color=INK)
    a.set_xticks(x, ticks)
    a.set_ylim(0, 100)
    a.set_xlim(-0.55, 3.75)
    a.set_ylabel("Lost work (W)")
    a.set_title(r"(a) Lost work of CV-L, $X_\mathrm{lost}$, split into its three terms")
    a.grid(axis="x", visible=False)
    leg = a.legend(handles=term_patches(), loc="upper left", bbox_to_anchor=(0.0, 1.0),
                   handlelength=1.6, handleheight=1.1)
    fix_patch_hatch(leg)

    # (b) hydraulic power
    W = col(rows, "W_hyd_W")
    b.bar(x, W, 0.55, color=NEUTRAL, edgecolor="white")
    for xi, wi in zip(x, W):
        b.text(xi, wi + 0.08, f"{wi:.3f}" if wi < 0.1 else f"{wi:.2f}", ha="center",
               va="bottom", fontsize=8, color=INK)
    save_W = 100 * (W[iR] - W[iL]) / W[iR]
    yb = W[iR] + 0.6
    b.annotate("", xy=(iL, yb), xytext=(iR, yb),
               arrowprops=dict(arrowstyle="->", color=INK, lw=0.9))
    b.text((iL + iR) / 2, yb + 0.12, f"−{save_W:.0f} %", ha="center", va="bottom",
           fontsize=8.5, color=INK)
    b.set_xticks(x, name_short)
    b.set_ylim(0, 7.0)
    b.set_ylabel(r"Hydraulic power $\dot V\Delta P$ (W)")
    b.set_title("(b) Pumping power")
    b.text(0.98, 0.985, "pump electricity = 2 × this\n" + r"at $\eta_\mathrm{pump}$ = 0.5",
           transform=b.transAxes, ha="right", va="top", fontsize=7.3, color=MUTED,
           linespacing=1.1)
    b.grid(axis="x", visible=False)

    # (c) device temperature, bars from the 30 C inlet
    T = col(rows, "T_dev_C")
    T_in = rows[0]["T_in_C"]
    b_c = c.bar(x, T - T_in, 0.55, bottom=T_in, color=NEUTRAL, edgecolor="white")
    del b_c
    c.axhline(90.0, **LIMIT)
    c.text(-0.42, 90.6, "limit 90 °C", ha="left", va="bottom", fontsize=7.5, color=INK)
    for xi, ti in zip(x, T):
        yy = ti + 0.6 if ti < 88 else ti - 0.6
        c.text(xi, yy, f"{ti:.2f}", ha="center", va="bottom" if ti < 88 else "top",
               fontsize=8, color=INK if ti < 88 else "white")
    dT = T[iL] - T[iR]
    yc = max(T[iL], T[iR]) + 6.0
    c.annotate("", xy=(iL, yc), xytext=(iR, yc),
               arrowprops=dict(arrowstyle="->", color=INK, lw=0.9))
    c.text((iL + iR) / 2, yc + 0.7, f"+{dT:.2f} K", ha="center", va="bottom",
           fontsize=8.5, color=INK)
    c.set_xticks(x, name_short)
    c.set_ylim(T_in, 100)
    c.set_ylabel(r"Device temperature $T_\mathrm{dev}$ (°C)")
    c.set_title("(c) Device temperature")
    c.text(0.98, 0.985, f"bars start at the\n{T_in:.0f} °C inlet", transform=c.transAxes,
           ha="right", va="top", fontsize=7.3, color=MUTED, linespacing=1.1)
    c.grid(axis="x", visible=False)

    fig_title(fig, a, "Study 2: four designs, same limits (1 kW, inlet 30 °C, pump inside "
              r"CV-L, $\eta_\mathrm{pump}$ = 0.5)", y=0.95)
    return save(fig, "fig_J2_designs.png")


# ---------------------------------------------------------------- Figure 13 (J1)
def fig_J1():
    """Study 1: lost-work terms against flow (study1_flow_sweep.csv)."""
    rows = read(RES / "study1_flow_sweep.csv")
    o = reference_optimum()
    V = col(rows, "V_lpm")
    ok = np.array([r["feasible"] for r in rows])
    mark = [i for i, v in enumerate(V) if v in (0.5, 1, 2, 4, 6, 8, 10, 12)]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    # infeasible flows: Re > 2000 first (linear interpolation in the CSV), then dP > 50 kPa
    Re = col(rows, "Re")
    V_re = float(np.interp(2000.0, Re, V))
    ax.axvspan(V_re, 12.6, color=SHADE, lw=0, zorder=0)
    ax.text((V_re + 12.6) / 2, 72, "Re > 2000\nΔP > 50 kPa\n(infeasible)", rotation=90,
            ha="center", va="center", fontsize=7.5, color=MUTED, linespacing=1.1)
    for key in TERMS:
        s = LINE[key]
        ax.plot(V, col(rows, key), color=s["color"], ls=s["ls"], lw=s["lw"], marker=s["marker"],
                markevery=mark, ms=5.5, mec="white", mew=0.6, label=s["label"], zorder=3)

    Vn, Xn, Va = o["V_lpm"], o["X_lost_W"], o["V_analytical_lpm"]
    ax.axvline(Vn, color="0.25", lw=1.0, zorder=2)
    ax.axvline(Va, color="0.25", lw=1.0, ls=(0, (1, 1.8)), zorder=2)
    ax.plot(Vn, Xn, marker="*", ms=14, color="black", mec="white", mew=0.8, zorder=5,
            ls="none")
    ax.text(Vn + 0.15, 55, f"numerical optimum\n{Vn:.2f} L/min\n$X_\\mathrm{{lost}}$ = {Xn:.2f} W",
            ha="left", va="center", fontsize=8, color=INK)
    ax.text(Va - 0.15, 55, f"Eq. (21) estimate\n$(B/2C)^{{1/3}}$\n{Va:.2f} L/min",
            ha="right", va="center", fontsize=8, color=INK)

    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 85)
    ax.set_xticks(np.arange(0, 13, 1))
    ax.set_xlabel(r"Coolant flow rate $\dot V$ (L/min)")
    ax.set_ylabel("Lost work (W)")
    fig_title(fig, ax, "Study 1: lost work of CV-L against flow, reference geometry "
              "(0.2 / 0.2 mm, 75 channels, 1 kW, inlet 30 °C)", y=0.935)
    ax.legend(loc="upper right", bbox_to_anchor=(0.88, 1.0), handlelength=3.2)
    assert ok[V <= 11].all() and not ok[V >= 11.5].any()
    return save(fig, "fig_J1_flow_sweep.png")


# ---------------------------------------------------------------- Figure 15 (J3)
def fig_J3():
    """Study 3: inlet temperature 20-60 C (study3_inlet_temperature.csv)."""
    rows = read(RES / "study3_inlet_temperature.csv")
    T = col(rows, "T_in_C")
    ok = np.array([r["status"] == "entropy optimum" for r in rows])
    bad = [r for r in rows if r["status"] != "entropy optimum"]
    t_bad = min(r["T_in_C"] for r in bad)
    t_ok = T[ok].max()

    fig, axs = plt.subplots(1, 3, figsize=(10.0, 3.7))
    fig.subplots_adjust(wspace=0.36)
    for a in axs:
        a.axvspan(t_bad, 61.5, color=SHADE, lw=0, zorder=0)
        a.set_xlim(18.5, 61.5)
        a.set_xticks(np.arange(20, 61, 10))
        a.set_xlabel(r"Inlet temperature $T_\mathrm{in}$ (°C)")

    # (a) optimum flow
    a = axs[0]
    Vo = col(rows, "V_lpm")
    i55 = int(np.flatnonzero(ok)[-1])
    a.plot(T[ok], Vo[ok], color="black", lw=1.8, marker="o", ms=4.5, mec="white", mew=0.5)
    a.set_ylim(4.6, 5.9)
    a.set_ylabel(r"Optimum flow $\dot V$ (L/min)")
    a.set_title(r"(a) Optimum flow")
    a.annotate(f"{Vo[0]:.2f}", (T[0], Vo[0]), xytext=(6, -3), textcoords="offset points",
               ha="left", va="top", fontsize=8, color=INK)
    a.annotate(f"{Vo[i55]:.2f}", (T[i55], Vo[i55]), xytext=(0, 7), textcoords="offset points",
               ha="center", va="bottom", fontsize=8, color=INK)
    a.text((t_bad + 61.5) / 2, 4.65, "no feasible optimum", rotation=90, ha="center",
           va="bottom", fontsize=7.2, color=MUTED)

    # (b) device temperature with the limit
    a = axs[1]
    Td = col(rows, "T_dev_C")
    r57 = next(r for r in bad if r["status"].startswith("infeasible: Re"))
    r60 = next(r for r in bad if r["status"] == "infeasible at any flow")
    a.plot(T[ok], Td[ok], color="black", lw=1.8, marker="o", ms=4.5, mec="white", mew=0.5)
    a.plot(r57["T_in_C"], r57["T_dev_C"], marker="o", ms=6, mfc="white", mec="black", mew=1.1,
           ls="none")
    a.plot(r60["T_in_C"], r60["T_dev_floor_C"], marker="x", ms=7, mew=1.6, color="black",
           ls="none")
    a.text(0.985, 0.025,
           f"○  {r57['T_in_C']:g} °C: 90 °C needs\n"
           f"    {r57['V_lpm']:.1f} L/min, Re {r57['Re']:.0f}\n"
           f"×  {r60['T_in_C']:g} °C: floor {r60['T_dev_floor_C']:.2f} °C",
           transform=a.transAxes, ha="right", va="bottom", multialignment="left",
           fontsize=7.2, color=INK, linespacing=1.15)
    a.axhline(90.0, **LIMIT)
    a.text(19.5, 90.8, "limit 90 °C", ha="left", va="bottom", fontsize=7.5, color=INK)
    a.annotate(f"{Td[i55]:.2f} °C at {T[i55]:g} °C", (T[i55], Td[i55]), xytext=(-6, 11),
               textcoords="offset points", ha="right", va="bottom", fontsize=7.5, color=INK)
    a.annotate(f"{Td[0]:.2f}", (T[0], Td[0]), xytext=(6, -3), textcoords="offset points",
               ha="left", va="top", fontsize=8, color=INK)
    a.set_ylim(50, 100)
    a.set_ylabel(r"Device temperature $T_\mathrm{dev}$ (°C)")
    a.set_title(r"(b) Device temperature")

    # (c) lost work and outlet exergy
    a = axs[2]
    XL, XO = col(rows, "X_lost_W"), col(rows, "X_out_W")
    a.axhline(0, color="0.3", lw=0.7)
    a.axvline(25.0, color="0.3", lw=0.9, ls=(0, (1, 1.8)))
    a.text(25.6, 104, r"dead state $T_0$ = 25 °C", ha="left", va="top", fontsize=7.2,
           color=MUTED)
    a.plot(T[ok], XL[ok], color="black", lw=2.0, marker="o", ms=4.5, mec="white", mew=0.5,
           label=r"Lost work $X_\mathrm{lost}$")
    a.plot(T[ok], XO[ok], color=PURPLE, lw=1.6, ls="-", marker="v", ms=5,
           mfc="white", mec=PURPLE, mew=1.1, label=r"Outlet exergy $X_\mathrm{out}$")
    for arr, i, off, ha, va in ((XL, 0, (4, 6), "left", "bottom"),
                                (XL, i55, (0, 7), "center", "bottom"),
                                (XO, 0, (7, -2), "left", "center"),
                                (XO, i55, (-7, 0), "right", "center")):
        a.annotate(num(arr[i]), (T[i], arr[i]), xytext=off, textcoords="offset points",
                   ha=ha, va=va, fontsize=7.5, color=INK)
    a.set_ylim(-25, 105)
    a.set_ylabel("Exergy rate (W)")
    a.set_title("(c) Lost work and outlet exergy")
    a.legend(loc="lower right", bbox_to_anchor=(1.0, 0.0), fontsize=7.6, handlelength=2.4,
             borderaxespad=0.3)

    fig_title(fig, axs[0], f"Study 3: reference geometry (0.2 / 0.2 mm) at its lost-work "
              f"optimum flow; feasible up to {t_ok:g} °C, shaded: no feasible optimum "
              f"(from {t_bad:g} °C)", y=1.0)
    return save(fig, "fig_J3_inlet_temperature.png")


# ---------------------------------------------------------------- Figure 17 (J5)
def fig_J5():
    """Study 5: below the 0.1 mm bound (study5_below_limit.csv)."""
    rows = read(RES / "study5_below_limit.csv")
    line = [r for r in rows if r["case"].startswith("w_c = w_f")]
    free = next(r for r in rows if r["case"].startswith("free"))
    w = col(line, "w_c_mm")

    fig, (a, b) = plt.subplots(1, 2, figsize=(9.2, 4.2))
    fig.subplots_adjust(wspace=0.26)
    for ax in (a, b):
        ax.axvspan(0.035, 0.1, color=SHADE, lw=0, zorder=0)
        ax.axvline(0.1, color="0.25", lw=1.0)
        ax.set_xlim(0.035, 0.215)
        ax.set_xticks([0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2])
        ax.set_xticklabels(["0.05", "0.075", "0.10", "", "0.15", "", "0.20"])
        ax.set_xlabel(r"Channel and fin width $w_c = w_f$ (mm)")
    star = dict(marker="*", ms=13, color="black", mec="white", mew=0.8, ls="none", zorder=5)
    star_label = (f"Free optimum with 0.05 mm bounds\n($w_c$ {free['w_c_mm']:.3f} mm, "
                  f"$w_f$ {free['w_f_mm']:.3f} mm)")

    # (a) lost-work terms
    for key in TERMS:
        s = LINE[key]
        a.plot(w, col(line, key), color=s["color"], ls=s["ls"], lw=s["lw"], marker=s["marker"],
               ms=5.5, mec="white", mew=0.6, label=s["label"], zorder=3)
    a.plot(free["w_c_mm"], free["X_lost_W"], label=star_label, **star)
    a.annotate(f"{free['X_lost_W']:.2f}", (free["w_c_mm"], free["X_lost_W"]), xytext=(0, -9),
               textcoords="offset points", ha="center", va="top", fontsize=7.5, color=INK)
    XL = col(line, "X_lost_W")
    for i in range(len(w)):
        on_bound = abs(w[i] - 0.1) < 1e-9
        a.annotate(f"{XL[i]:.2f}", (w[i], XL[i]), xytext=(4, 11) if on_bound else (0, 7),
                   textcoords="offset points", ha="left" if on_bound else "center",
                   va="bottom", fontsize=7.5, color=INK)
    a.set_ylim(0, 50)
    a.set_ylabel("Lost work (W)")
    a.set_title("(a) Lost work, each width at its own optimum flow")
    a.text(0.0375, 49, "below the 0.1 mm bound\n(this study only)", ha="left", va="top",
           fontsize=7.2, color=MUTED)
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=7.6,
             handlelength=3.0, columnspacing=1.2)

    # (b) optimum flow, constrained and free, dP label at every point
    Vc, Vf, dP = col(line, "V_lpm"), col(line, "V_unconstrained_lpm"), col(line, "dP_kPa")
    b.plot(w, Vf, color="0.45", lw=1.4, ls=(0, (4, 2)), marker="o", ms=6, mfc="white",
           mec="0.35", mew=1.0, label="Optimum flow with no limits", zorder=3)
    b.plot(w, Vc, color="black", lw=1.8, marker="o", ms=5, mec="white", mew=0.5,
           label=r"Optimum flow within the ΔP, Re and $T_\mathrm{dev}$ limits", zorder=4)
    b.plot(free["w_c_mm"], free["V_lpm"], label=star_label, **star)
    for i in range(len(w)):
        if line[i]["active_constraint"] == "dP":
            b.annotate(f"{Vc[i]:.2f} L/min\nΔP {dP[i]:.1f} kPa\n= limit", (w[i], Vc[i]),
                       xytext=(8, 0), textcoords="offset points", ha="left", va="top",
                       fontsize=7.3, color=INK, fontweight="bold", linespacing=1.05)
        else:
            b.annotate(f"ΔP {dP[i]:.1f} kPa", (w[i], Vc[i]), xytext=(6, -12),
                       textcoords="offset points", ha="left", va="top", fontsize=7.3,
                       color=INK)
    i0 = int(np.argmin(w))
    b.annotate(f"{Vf[i0]:.2f}", (w[i0], Vf[i0]), xytext=(-6, 4), textcoords="offset points",
               ha="right", va="bottom", fontsize=7.3, color=INK)
    b.set_ylim(0, 6)
    b.set_ylabel(r"Optimum flow $\dot V$ (L/min)")
    b.set_title("(b) Optimum flow, with ΔP at that flow (limit 50 kPa)")
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1, fontsize=7.6)

    fig_title(fig, a, "Study 5: channels below the 0.1 mm manufacturing bound "
              r"(1 kW, inlet 30 °C; $H/w_c$ = 30–60, outside the validated aspect ratio)",
              y=1.0)
    return save(fig, "fig_J5_below_limit.png")


# ---------------------------------------------------------------- Figure 16 (J4)
def fig_J4():
    """Study 4: one input at a time (study4_sensitivity.csv; baseline from phase1_pump_cv.csv)."""
    rows = read(RES / "study4_sensitivity.csv")
    o = reference_optimum()
    base = {"V": o["V_lpm"], "X": o["X_lost_W"], "T": o["T_dev_C"]}
    label = {
        ("R_tim", 0.01): r"$R_\mathrm{TIM}$ 0.01 K/W", ("R_tim", 0.03): r"$R_\mathrm{TIM}$ 0.03 K/W",
        ("eta_pump", 0.3): r"$\eta_\mathrm{pump}$ 0.3", ("eta_pump", 0.7): r"$\eta_\mathrm{pump}$ 0.7",
        ("T0_C", 10.0): r"$T_0$ 10 °C", ("T0_C", 35.0): r"$T_0$ 35 °C",
        ("K_total", 0.0): r"$K_c + K_e$ 0", ("K_total", 3.0): r"$K_c + K_e$ 3",
    }
    order = ["R_tim", "eta_pump", "T0_C", "K_total"]
    rows = sorted(rows, key=lambda r: (order.index(r["parameter"]), r["value"]))
    y = np.array([3 * (i // 2) + (i % 2) for i in range(len(rows))], dtype=float)
    lowhigh = ["low" if i % 2 == 0 else "high" for i in range(len(rows))]
    fill = {"low": "#BDBDBD", "high": "#4D4D4D"}
    hatch = {"low": "////", "high": None}

    panels = [
        ("V_opt_lpm", "V", lambda v, b0: 100 * (v - b0) / b0, "Change of optimum flow (%)",
         f"(a) Optimum flow\nbaseline {base['V']:.2f} L/min", "{:.2f}", 25),
        ("X_lost_W", "X", lambda v, b0: 100 * (v - b0) / b0, "Change of lost work (%)",
         f"(b) Lost work at the optimum\nbaseline {base['X']:.2f} W", "{:.2f}", 7.5),
        ("T_dev_C", "T", lambda v, b0: v - b0, r"Change of $T_\mathrm{dev}$ (K)",
         f"(c) Device temperature\nbaseline {base['T']:.2f} °C", "{:.2f}", 15.5),
    ]
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.9), sharey=True)
    fig.subplots_adjust(wspace=0.12)
    for a, (key, bk, f, xl, title, fmt, lim) in zip(axs, panels):
        d = np.array([f(r[key], base[bk]) for r in rows])
        d[np.abs(d) < 1e-4] = 0.0   # optimizer noise (~1e-9): shown as "no change"
        for yi, di, lh, r in zip(y, d, lowhigh, rows):
            a.barh(yi, di, 0.78, color=fill[lh], hatch=hatch[lh], edgecolor="white",
                   hatchcolor="0.35" if lh == "low" else "white", linewidth=0.8)
            txt = fmt.format(r[key])
            if di == 0.0:
                txt += "  (no change)"
            ha = "left" if di >= 0 else "right"
            a.text(di + (0.025 * lim if di >= 0 else -0.025 * lim), yi, txt, ha=ha,
                   va="center", fontsize=7.3, color=INK if di != 0.0 else MUTED)
        a.axvline(0, color="0.2", lw=0.9)
        a.set_xlim(-lim, lim)
        a.set_xlabel(xl)
        a.set_title(title, fontsize=9)
        a.grid(axis="y", visible=False)
    axs[0].set_yticks(y, [label[(r["parameter"], r["value"])] for r in rows])
    axs[0].invert_yaxis()
    axs[0].tick_params(axis="y", length=0)
    fig.legend(handles=[Patch(facecolor=fill["low"], hatch="////", edgecolor="white",
                              label="lower input value"),
                        Patch(facecolor=fill["high"], edgecolor="white",
                              label="higher input value")],
               loc="lower center", ncol=2, bbox_to_anchor=(0.55, -0.07), fontsize=8)
    fig_title(fig, axs[0], "Study 4: one input changed at a time, reference geometry at its "
              "lost-work optimum flow; bar labels give the new value", y=1.03)
    return save(fig, "fig_J4_sensitivity.png")


# ---------------------------------------------------------------- Figure 12 (H)
def fig_H():
    """MAPE by model combination (thermal_model_matrix.csv, dP_model_matrix.csv)."""
    th = read(VRES / "thermal_model_matrix.csv")
    dp = read(VRES / "dP_model_matrix.csv")
    nu_order = ["fd_H1", "fd_H1_3", "LG", "LG_3", "MY", "MY_3"]
    nu_name = {"fd_H1": "fd_H1 (proposal)", "fd_H1_3": "fd_H1_3", "LG": "LG", "LG_3": "LG_3",
               "MY": "MY", "MY_3": "MY_3"}
    f_order = ["fd", "MY", "hagenbach"]
    f_name = {"fd": "fd (proposal)", "MY": "MY apparent", "hagenbach": "hagenbach"}
    # Encoding shared by both panels: wall-viscosity correction = dark fill;
    # the second option (axial conduction / plenum losses K = 1) = hatched.
    light, dark = "#A9C4DE", NAVY
    combos_th = [(False, False, "1D base", light, None),
                 (False, True, "1D base + wall viscosity", dark, None),
                 (True, False, "axial conduction", light, "////"),
                 (True, True, "axial conduction + wall viscosity", dark, "////")]
    combos_dp = [(False, False, "no plenum losses, mean-T viscosity", light, None),
                 (False, True, "no plenum losses, wall viscosity", dark, None),
                 (True, False, r"$K_c = K_e = 1$, mean-T viscosity", light, "////"),
                 (True, True, r"$K_c = K_e = 1$, wall viscosity", dark, "////")]
    bh, step = 0.19, 1.0

    fig, (a, b) = plt.subplots(2, 1, figsize=(7.4, 8.4), sharex=True,
                               gridspec_kw=dict(height_ratios=[6, 3], hspace=0.2))
    xmax = 70

    def panel(ax, groups, names, combos, lookup, sel, title, n_pts):
        yt = []
        for gi, g in enumerate(groups):
            y0 = gi * step
            yt.append(y0 + 1.5 * bh)
            for ci, (o1, o2, lab, colr, hat) in enumerate(combos):
                v = 100 * lookup(g, o1, o2)
                yy = y0 + ci * bh
                ax.barh(yy, v, bh * 0.92, color=colr, hatch=hat, edgecolor="white",
                        hatchcolor="white" if colr == dark else "0.3", linewidth=0.6,
                        label=lab if gi == 0 else None)
                is_sel = (g, o1, o2) == sel
                ax.text(v + 0.6, yy, f"{v:.1f}" + ("  ◀ selected" if is_sel else ""),
                        va="center", ha="left", fontsize=7 if not is_sel else 7.5,
                        color=INK, fontweight="bold" if is_sel else "normal")
        ax.set_yticks(yt, [names[g] for g in groups])
        ax.invert_yaxis()
        ax.tick_params(axis="y", length=0)
        ax.axvspan(10, 15, color="0.9", lw=0, zorder=0)
        ax.set_title(title + f" ({n_pts} points)", fontsize=9)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, xmax)

    def lk_th(g, ax_, vc):
        return next(r["MAPE_TC"] for r in th if r["nusselt_model"] == g
                    and r["axial_conduction"] == ax_ and r["viscosity_correction"] == vc)

    def lk_dp(g, k1, vc):
        return next(r["MAPE_dP"] for r in dp if r["friction_model"] == g
                    and r["minor_losses_K1"] == k1 and r["viscosity_correction"] == vc)

    panel(a, nu_order, nu_name, combos_th, lk_th, ("MY_3", True, True),
          "(a) Thermocouple temperature rise, by Nusselt model", int(th[0]["n_TC"]))
    target = Patch(facecolor="0.9", edgecolor="none", label="proposal's target, 10–15 %")
    h, l = a.get_legend_handles_labels()
    a.legend(handles=h + [target], loc="lower right", fontsize=7.8,
             title="base conduction / properties", title_fontsize=7.8, handlelength=1.8,
             handleheight=1.0, frameon=True, facecolor="white", edgecolor="none",
             framealpha=1.0)
    panel(b, f_order, f_name, combos_dp, lk_dp, ("MY", False, True),
          "(b) Plenum-to-plenum pressure drop, by friction model", int(dp[0]["n"]))
    h, l = b.get_legend_handles_labels()
    b.legend(handles=h[:2] + [target] + h[2:], loc="upper center", bbox_to_anchor=(0.45, -0.2), ncol=2,
             fontsize=7.8, title="plenum losses / properties", title_fontsize=7.8,
             handlelength=1.8, handleheight=1.0, columnspacing=1.5)
    b.set_xlabel("Mean absolute percentage error, MAPE (%)")
    b.text(0.0, -0.62, "Thermocouple MAPE is on the temperature rise above the inlet. The "
           "pressure drop is computed with\nthe selected thermal model (MY_3, axial "
           "conduction).",
           transform=b.transAxes, ha="left", va="top", fontsize=7, color=MUTED)
    fig_title(fig, a, "Qu and Mudawar (2002) benchmark: error of every model combination",
              y=0.935)
    return save(fig, "fig_H_model_mape.png")


# ================================================================ schematics (B-G)
# Materials in the schematics: chosen to stay distinct in grayscale (labels carry
# identity as well). Copper as in make_geometry_figures.py, water lighter.
CU = "#C98A4B"        # copper, gray ~150
WATER = "#CFE3F1"     # water, gray ~223
LID = "#BDBDBD"       # lid / cover, gray ~189
CHIP = "#4D4D4D"      # device
TIM_C = "#8C8C8C"     # TIM layer
BOX_FC = "#F4F4F4"    # neutral process box
BOX_HI = "#DCE6F0"    # highlighted box (light navy tint)


def canvas(figsize, xlim, ylim):
    """Axes in drawing units, equal aspect, no frame or grid."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def rbox(ax, x, y, w, h, text="", fc=BOX_FC, ec="0.3", lw=0.9, fs=8, r=0.6, ls="-",
         weight="normal", color=INK, ha="center", z=2, **kw):
    """Rounded box with (x, y) the lower-left corner; text centred unless ha='left'."""
    from matplotlib.patches import FancyBboxPatch
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc,
                       ec=ec, lw=lw, ls=ls, zorder=z)
    ax.add_patch(p)
    if text:
        tx = x + w / 2 if ha == "center" else x + 0.8
        ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=color,
                fontweight=weight, zorder=z + 1, linespacing=1.2, **kw)
    return p


def arrow(ax, p0, p1, color=INK, lw=1.0, style="-|>", ms=8, ls="-", z=3, shrink=0.0,
          conn="arc3"):
    from matplotlib.patches import FancyArrowPatch
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, color=color, lw=lw,
                        ls=ls, zorder=z, shrinkA=shrink, shrinkB=shrink, connectionstyle=conn)
    ax.add_patch(a)
    return a


def resistor(ax, p0, p1, n=4, amp=0.9, lead=0.32, color=INK, lw=1.1, z=3):
    """Zigzag resistor from p0 to p1 (straight leads take `lead` of the length)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.hypot(*d)
    t, nrm = d / L, np.array([-d[1], d[0]]) / L
    s = np.concatenate(([0, lead / 2], lead / 2 + (1 - lead) * (np.arange(2 * n) + 0.5) / (2 * n),
                        [1 - lead / 2, 1]))
    off = np.concatenate(([0, 0], amp * np.tile([1, -1], n), [0, 0]))
    pts = p0 + np.outer(s * L, t) + np.outer(off, nrm)
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, zorder=z, solid_joinstyle="miter")


def node(ax, x, y, fc="black", r=0.55, z=5):
    from matplotlib.patches import Circle
    ax.add_patch(Circle((x, y), r, fc=fc, ec="black", lw=0.8, zorder=z))


def rect(ax, x, y, w, h, fc, ec="0.2", lw=0.6, hatch=None, z=1, **kw):
    from matplotlib.patches import Rectangle
    p = Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, **kw)
    ax.add_patch(p)
    return p


def _coldplate():
    """Import the package lazily (only the schematics and Figure 7 need it)."""
    sys.path.insert(0, str(ROOT))
    import coldplate  # noqa: F401
    return coldplate


# ---------------------------------------------------------------- Figure 3 (B)
def fig_B():
    """Thermal network: one station (cross-section) and the ladder along the channel."""
    _coldplate()
    from coldplate.config import Case
    from coldplate.thermal import stations
    case = Case()
    g, mat, op = case.geometry, case.materials, case.operating
    dT_base = op.Q / (g.W * g.L) * g.t_b / mat.k_s          # q'' t_b / k_s
    dT_tim = op.Q * mat.R_tim_jc

    fig, ax = canvas((7.4, 6.9), (0, 100), (-13, 80))

    # ---------------- (a) one station: cross-section with the node positions
    ax.text(0, 79, "(a) One station: where the nodes sit, and the resistance chain",
            fontsize=9.5, fontweight="bold", va="top", color=INK)
    x0, u = 17.0, 2.0                       # cross-section left edge, strip width
    y_chip, y_tim, y_base, y_fin, y_lid = 44.0, 48.0, 49.4, 55.0, 70.0
    rect(ax, x0, y_chip, 9 * u, y_tim - y_chip, CHIP)
    rect(ax, x0, y_tim, 9 * u, y_base - y_tim, TIM_C)
    rect(ax, x0, y_base, 9 * u, y_fin - y_base, CU)
    for k in range(9):
        rect(ax, x0 + k * u, y_fin, u, y_lid - y_fin, CU if k % 2 == 0 else WATER)
    rect(ax, x0, y_lid, 9 * u, 1.6, LID)
    for txt, yy in (("lid (adiabatic)", y_lid + 0.8), ("fins and channels, H", (y_fin + y_lid) / 2),
                    ("base, $t_b$", (y_base + y_fin) / 2), ("TIM", (y_tim + y_base) / 2),
                    ("device", (y_chip + y_tim) / 2)):
        ax.text(x0 - 1.0, yy, txt, ha="right", va="center", fontsize=7.6, color=INK)
    xc = x0 + 3.5 * u                       # centre of a water channel (odd strips)
    geo = {"T_f": (xc, 62.5), "T_cf": (xc, y_fin), "T_b": (xc, y_base), "T_dev": (xc, 46.0)}
    for k, (xx, yy) in geo.items():
        node(ax, xx, yy, fc="white" if k == "T_dev" else "black", r=0.5, z=6)

    # resistance chain next to it, nodes joined to the cross-section by leaders
    xr = 50.0
    ch = {"T_f": 75.0, "T_cf": 66.0, "T_b": 57.0, "T_dev": 47.0}
    sym = {"T_f": r"$T_f(x)$", "T_cf": r"$T_{cf}(x)$", "T_b": r"$T_b(x)$",
           "T_dev": r"$T_\mathrm{dev}$"}
    for k in ch:
        gx, gy = geo[k]
        ax.plot([gx, xr], [gy, ch[k]], color="0.55", lw=0.7, ls=(0, (1, 1.5)), zorder=2)
        node(ax, xr, ch[k], fc="white" if k == "T_dev" else "black")
        ax.text(xr - 1.4, ch[k], sym[k], ha="right", va="center", fontsize=8.5, color=INK,
                bbox=dict(fc="white", ec="none", pad=0.6), zorder=7)
    resistor(ax, (xr, ch["T_dev"]), (xr, ch["T_b"]))
    resistor(ax, (xr, ch["T_b"]), (xr, ch["T_cf"]))
    resistor(ax, (xr, ch["T_cf"]), (xr, ch["T_f"]))
    lab = dict(ha="left", va="center", fontsize=7.6, color=INK, linespacing=1.2)
    ax.text(xr + 2.0, (ch["T_dev"] + ch["T_b"]) / 2,
            r"TIM, $R_\mathrm{TIM}$ = " + f"{mat.R_tim_jc:g} K/W, lumped: " + r"$Q R_\mathrm{TIM}$"
            + f" = {dT_tim:.0f} K\n" + r"$T_\mathrm{dev} = \mathrm{max}_x\, T_b(x) + Q R_\mathrm{TIM}$"
            + "  (Eq. 7, CV-P)", **lab)
    ax.text(xr + 2.0, (ch["T_b"] + ch["T_cf"]) / 2,
            r"base conduction, 1D: $T_b - T_{cf} = q'' t_b / k_s$" + f" = {dT_base:.2f} K\n"
            r"$T_b$ is the CV-C boundary where heat enters", **lab)
    ax.text(xr + 2.0, (ch["T_cf"] + ch["T_f"]) / 2,
            r"convection from channel floor and fins: $1/(G'\,\Delta x)$" + "\n"
            r"$G' = h(x)\,N\,(w_c + 2\eta_f H)$, $h = Nu_x k / D_h$  (Eqs. 4, 5)", **lab)
    arrow(ax, (xr, ch["T_dev"] - 4.2), (xr, ch["T_dev"] - 0.7), lw=1.1)
    ax.text(xr + 1.2, ch["T_dev"] - 3.4, "Q = 1 kW", ha="left", va="center", fontsize=7.6,
            color=INK)
    arrow(ax, (xr + 0.7, ch["T_f"]), (xr + 6.0, ch["T_f"]), lw=1.1)
    ax.text(xr + 6.8, ch["T_f"], r"to the water, $\dot m\,dh_f/dx = G'\,(T_{cf} - T_f)$  (Eq. 3)",
            ha="left", va="center", fontsize=7.6, color=INK)

    # ---------------- (b) the ladder along the channel
    ax.text(0, 38.5, "(b) Along the channel: the same chain at every station, coupled by "
            "axial conduction and by the flow", fontsize=9.5, fontweight="bold", va="top",
            color=INK)
    yF, yC, yB, yS = 29.0, 19.5, 10.0, 3.2
    cols = {"1": 12.0, "i": 40.0, "i+1": 62.0, "n": 88.0}
    head = {"1": "station 1, x = 0", "i": "station i", "i+1": "station i + 1",
            "n": "station n, x = L"}
    dots = (24.0, 76.0)
    for name, xx in cols.items():
        node(ax, xx, yF)
        node(ax, xx, yC)
        node(ax, xx, yB)
        resistor(ax, (xx, yC), (xx, yF), n=3, amp=0.8)
        resistor(ax, (xx, yB), (xx, yC), n=3, amp=0.8)
        arrow(ax, (xx, yS + 1.6), (xx, yB - 0.7), lw=1.0)
        ax.text(xx, yF + 2.0, head[name], ha="center", va="bottom", fontsize=7.6, color=MUTED)
    # axial conduction between the T_cf nodes and flow between the T_f nodes (i to i+1 drawn,
    # the rest dashed through the dots)
    resistor(ax, (cols["i"], yC), (cols["i+1"], yC), n=4, amp=0.8, lead=0.45)
    arrow(ax, (cols["i"] + 0.6, yF), (cols["i+1"] - 0.6, yF), lw=1.0)
    for xa, xb in ((cols["1"], dots[0] - 2.5), (dots[0] + 2.5, cols["i"]),
                   (cols["i+1"], dots[1] - 2.5), (dots[1] + 2.5, cols["n"])):
        for yy in (yF, yC):
            ax.plot([xa, xb], [yy, yy], color=INK, lw=1.0, ls=(0, (2, 2)), zorder=2)
    for xd in dots:
        for yy in (yF, yC, yB):
            ax.text(xd, yy, "···", ha="center", va="center", fontsize=11, color=INK)
    # adiabatic ends of the base
    for xe in (cols["1"] - 5.0, cols["n"] + 5.0):
        ax.plot([xe, xe], [yC - 2.2, yC + 2.2], color=INK, lw=2.4, solid_capstyle="butt")
    ax.plot([cols["1"] - 5.0, cols["1"]], [yC, yC], color=INK, lw=1.0)
    ax.plot([cols["n"], cols["n"] + 5.0], [yC, yC], color=INK, lw=1.0)
    ax.text(cols["1"] - 5.6, yC, "adiabatic\nend", ha="right", va="center", fontsize=7.2,
            color=MUTED, linespacing=1.1)
    ax.text(cols["n"] + 5.6, yC, "adiabatic\nend", ha="left", va="center", fontsize=7.2,
            color=MUTED, linespacing=1.1)
    # inlet and outlet
    arrow(ax, (cols["1"] - 7.0, yF), (cols["1"] - 0.6, yF), lw=1.0)
    ax.text(cols["1"] - 7.6, yF, r"$T_\mathrm{in}$", ha="right", va="center", fontsize=8.5)
    arrow(ax, (cols["n"] + 0.6, yF), (cols["n"] + 7.0, yF), lw=1.0)
    ax.text(cols["n"] + 7.6, yF, r"$T_\mathrm{out}$", ha="left", va="center", fontsize=8.5)
    # element labels, once: on the left of station i and between stations i and i+1
    xm = (cols["i"] + cols["i+1"]) / 2
    ax.text(xm, yF - 0.9, r"flow $\dot m$, enthalpy $h_f$ (Eq. 3)", ha="center", va="top",
            fontsize=7.6, color=INK)
    ax.text(xm, yC + 1.6, r"axial: $\Delta x / (k_s A_{ax})$ (Eq. 6)", ha="center",
            va="bottom", fontsize=7.6, color=INK)
    xl = cols["i"] - 1.6
    ax.text(xl, (yC + yF) / 2, r"$1/(G'_i\,\Delta x_i)$", ha="right", va="center",
            fontsize=7.6, color=INK)
    ax.text(xl, (yB + yC) / 2, r"$t_b / (k_s W \Delta x_i)$", ha="right", va="center",
            fontsize=7.6, color=INK)
    ax.text(cols["i"] + 1.2, (yS + yB) / 2 + 0.4, r"$q'\,\Delta x_i$, $q' = Q/L$",
            ha="left", va="center", fontsize=7.6, color=INK)
    for txt, yy in ((r"$T_{f,i}$", yF), (r"$T_{cf,i}$", yC), (r"$T_{b,i}$", yB)):
        ax.text(cols["i"] - 1.0, yy - 0.9, txt, ha="right", va="top", fontsize=7.6,
                color=MUTED, bbox=dict(fc="white", ec="none", pad=0.3), zorder=4)
    rect(ax, 4.0, yS - 1.2, 92.0, 2.8, CHIP, ec="0.2", z=1)
    ax.text(50.0, yS + 0.2, "device and TIM (CV-P): uniform heat flux q″ = Q / (W L) into the base",
            ha="center", va="center", fontsize=7.6, color="white", fontweight="bold", zorder=3)

    # ---------------- station positions actually used (design case), aligned with 1 ... n
    xs_ = stations(g.L, 41)
    xa, xw = cols["1"], cols["n"] - cols["1"]
    yb = -7.5
    ax.plot([xa, xa + xw], [yb, yb], color="0.3", lw=0.8)
    for xi in xs_:
        ax.plot([xa + xw * xi / g.L] * 2, [yb, yb + 1.6], color=INK, lw=0.7)
    for v in (0, 5, 10, 15, 20, 25, 30):
        xx = xa + xw * v / (g.L * 1e3)
        ax.plot([xx, xx], [yb, yb - 0.8], color="0.3", lw=0.8)
        ax.text(xx, yb - 1.3, f"{v}", ha="center", va="top", fontsize=7.6, color=INK)
    ax.text(xa + xw + 2.0, yb - 1.3, "x (mm)", ha="left", va="top", fontsize=7.6, color=INK)
    ax.text(xa, yb + 2.6, f"Station positions used by the solver for the design case: "
            f"n = {len(xs_)} over L = {g.L * 1e3:.0f} mm, clustered toward the inlet where h(x) "
            "changes fastest:\n" + r"$x_i = L\,[1 - \cos(\pi s_i / 2)]$, "
            r"$s_i = (i - 1)/(n - 1)$; the benchmark uses n = 61",
            ha="left", va="bottom", fontsize=7.6, color=INK, linespacing=1.3)
    return save(fig, "fig_B_network.png")


# ---------------------------------------------------------------- Figure 4 (C)
CV_STYLE = {   # control-volume boundaries: identity by dash pattern (and label), not colour
    "CV-P": dict(color="0.35", lw=1.3, ls=(0, (1.2, 1.6))),
    "CV-C": dict(color="0.1", lw=1.4, ls=(0, (5, 2.5))),
    "CV-L": dict(color="0.1", lw=1.4, ls=(0, (9, 2.2, 1.6, 2.2))),
}


def term_tag(ax, x, y, key, text, fs=7.6, ha="left"):
    """Small swatch in the loss-term style of Figures 13-17, then the text."""
    s = BAR[key]
    sw = rect(ax, x, y - 1.0, 2.6, 2.0, s["color"], ec="white", lw=0.5, hatch=s["hatch"], z=6)
    sw.set_hatchcolor(s["hatchcolor"])
    ax.text(x + 3.4, y, text, ha="left", va="center", fontsize=fs, color=INK, zorder=6,
            linespacing=1.15)


def fig_C():
    """Control volumes CV-P, CV-C, CV-L and the loss terms of each (reference design, 2 L/min)."""
    r = next(q for q in read(RES / "study1_flow_sweep.csv") if q["V_lpm"] == 2.0)
    T0, Tin, Q = 298.15, r["T_in_C"] + 273.15, 1000.0
    XC = T0 * r["S_gen_C_W_per_K"]
    Xrej = Q * (1 - T0 / Tin)
    assert abs(XC + r["X_out_W"] - Xrej + r["X_pump_W"] - r["X_lost_W"]) < 1e-3   # Eq. (26)

    fig, ax = canvas((7.4, 7.0), (0, 100), (-28, 67))
    pipe = dict(color="#7FA7C9", lw=3.4, solid_capstyle="butt", zorder=2)
    flow = dict(color=INK, lw=1.0, ms=8)
    b = 22.0                    # bottom of the cold-plate base; loop drawn relative to it
    yp = b + 6.0                # pipe / channel centre line

    # ---- hardware: device + TIM (drawn apart from the base), cold plate, pump, cooler
    rect(ax, 24, 6.5, 22, 5.5, CHIP)                       # device
    rect(ax, 24, 12.0, 22, 1.6, TIM_C)                     # TIM
    ax.text(35, 9.2, "device, junction $T_j$", ha="center", va="center", fontsize=7.6,
            color="white")
    ax.text(21.6, 12.8, "TIM", ha="right", va="center", fontsize=7.6, color=INK)
    rect(ax, 22, b, 26, 3.2, CU)                           # base
    rect(ax, 22, b + 3.2, 26, 5.6, WATER)                  # channel (section along the flow)
    rect(ax, 22, b + 8.8, 26, 1.2, LID)
    for xx in (25, 41):
        arrow(ax, (xx, yp), (xx + 4, yp), **flow)
    ax.text(35, b + 1.6, "cold plate: base", ha="center", va="center", fontsize=7.3, color=INK)
    ax.text(35, yp, "channels", ha="center", va="center", fontsize=7.3, color=INK)
    arrow(ax, (35, 13.9), (35, b - 0.2), lw=1.6, ms=10)
    ax.text(36.2, 17.6, r"$Q$ enters the base at $T_b(x)$", ha="left", va="center",
            fontsize=7.6, color=INK)
    ax.text(60.0, 17.6, "(interface drawn open)", ha="left", va="center", fontsize=7.0,
            color=MUTED)

    # loop: outlet -> up -> cooler -> left -> pump -> down -> inlet
    yt = b + 27.0               # top pipe
    ax.plot([48, 62.5, 62.5], [yp, yp, yt - 5.0], **pipe)
    ax.plot([56, 13.4], [yt, yt], **pipe)
    ax.plot([9, 9, 22], [yt - 4.4, yp, yp], **pipe)
    arrow(ax, (52.5, yp), (56.5, yp), **flow)
    arrow(ax, (36, yt), (32, yt), **flow)
    arrow(ax, (9, yp + 9.5), (9, yp + 5.5), **flow)
    rbox(ax, 56, yt - 5.0, 13, 10.5, "cooler\n(CDU)", fc=BOX_FC, fs=7.8)
    from matplotlib.patches import Circle, Polygon
    ax.add_patch(Circle((9, yt), 4.4, fc=BOX_FC, ec="0.3", lw=0.9, zorder=3))
    ax.add_patch(Polygon([(6.6, yt - 2.4), (6.6, yt + 2.4), (12.0, yt)], closed=True, fc="0.3",
                         ec="none", zorder=4))
    ax.text(10.4, yt - 5.4, "pump", ha="left", va="top", fontsize=7.6, color=INK)
    # states at the cold plate ports
    ax.text(15.5, yp - 0.8, r"in: $T_\mathrm{in}$, $P_\mathrm{in}$", ha="center", va="top",
            fontsize=7.3, color=INK)
    ax.text(55.5, yp - 0.8, r"out: $T_\mathrm{out}$, $P_\mathrm{out}$", ha="center", va="top",
            fontsize=7.3, color=INK)
    # work in, heat out
    arrow(ax, (9, 65.0), (9, yt + 4.8), lw=1.4, ms=9)
    ax.text(10.4, 63.0, r"$\dot W_\mathrm{pump} = \dot V \Delta P / \eta_\mathrm{pump}$"
            "\n(electricity, pump inside CV-L)", ha="left", va="center", fontsize=7.6,
            color=INK, linespacing=1.2)
    arrow(ax, (69.2, yt), (86.1, yt), lw=1.4, ms=9)
    rbox(ax, 86.5, yt - 4.6, 13, 9.2, "reservoir\nat $T_\\mathrm{in}$", fc="white", fs=7.6)
    ax.text(74.0, yt - 1.0, r"$Q + \dot W_\mathrm{pump}$" "\nrejected at $T_\\mathrm{in}$",
            ha="left", va="top", fontsize=7.3, color=INK, linespacing=1.15)

    # ---- control-volume boundaries
    def cv(name, x0, y0, x1, y1, lx, ly):
        s = CV_STYLE[name]
        ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=s["color"], lw=s["lw"],
                ls=s["ls"], zorder=4)
        ax.text(lx, ly, name, ha="left", va="center", fontsize=8.5, fontweight="bold",
                color=INK, zorder=7, bbox=dict(fc="white", ec="none", pad=0.4))
    cv("CV-P", 22.4, 5.0, 47.6, 15.0, 22.9, 3.6)
    cv("CV-C", 19.6, b - 1.2, 50.4, b + 12.0, 20.1, b + 13.3)
    cv("CV-L", 3.0, b - 2.4, 73.2, yt + 10.0, 3.5, yt + 11.3)

    # ---- where each loss term is destroyed (colour + hatch as in Figures 13-17)
    term_tag(ax, 22.0, b + 17.6, "X_gap_W", r"$X_\mathrm{gap}$: heat transfer from base to water")
    ax.text(25.4, b + 15.0, "(channel friction is also destroyed here;\nCV-L counts it in "
            r"$X_\mathrm{pump}$)", ha="left", va="center", fontsize=7.0, color=MUTED,
            linespacing=1.15)
    term_tag(ax, 47.0, yt + 7.9, "X_warm_W", r"$X_\mathrm{warm}$: warm outlet water" "\n"
             r"cooled back to $T_\mathrm{in}$")
    term_tag(ax, 15.5, yt + 6.8, "X_pump_W", r"$X_\mathrm{pump}$: pump electricity" "\n"
             "(pump losses + channel friction)")
    ax.text(49.0, 9.2, r"TIM loss: $\dot S_{gen,P} = Q\,(1/T_s - 1/T_j)$",
            ha="left", va="center", fontsize=7.6, color=INK)

    # ---- key: one row per control volume
    ax.text(0, -1.0, "Loss terms by control volume (reference design, 0.2 / 0.2 mm, "
            f"{r['V_lpm']:g} L/min, 1 kW, inlet {r['T_in_C']:g} °C; "
            "study1_flow_sweep.csv)", fontsize=8.5, fontweight="bold", va="center", color=INK)
    rows = [
        ("CV-P", "package and TIM", "reported separately",
         r"$\dot S_{gen,P} = Q\,(1/T_s - 1/T_j)$  (Eq. 17)" "\n"
         r"set by $R_\mathrm{TIM}$; not cold-plate loss, the designer cannot change it"),
        ("CV-C", "cold plate only", "diagnostic",
         r"$\dot S_{gen,C} = \dot m\,(s_\mathrm{out} - s_\mathrm{in}) - \int q''/T_b\,dA$  (Eq. 18)"
         r"  $\approx$ heat transfer + friction (Eq. 24)" "\n"
         rf"$T_0 \dot S_{{gen,C}}$ = {XC:.2f} W; the outlet water leaves with "
         rf"$X_\mathrm{{out}}$ = {r['X_out_W']:.2f} W of exergy"),
        ("CV-L", "cold plate + pump + cooler", "objective",
         rf"$X_\mathrm{{lost}} = X_\mathrm{{warm}} + X_\mathrm{{gap}} + X_\mathrm{{pump}}$ = "
         rf"{r['X_warm_W']:.2f} + {r['X_gap_W']:.2f} + {r['X_pump_W']:.2f} = "
         rf"{r['X_lost_W']:.2f} W  (Eq. 20)" "\n"
         rf"Eq. (26): $T_0\dot S_{{gen,C}} + [X_\mathrm{{out}} - Q(1 - T_0/T_\mathrm{{in}})]"
         rf" + X_\mathrm{{pump}}$ = {XC:.2f} + {r['X_out_W'] - Xrej:.2f} + "
         rf"{r['X_pump_W']:.2f} = {XC + r['X_out_W'] - Xrej + r['X_pump_W']:.2f} W"),
    ]
    y = -6.8
    for name, what, role, eq in rows:
        s = CV_STYLE[name]
        ax.plot([0.5, 7.0], [y + 1.1, y + 1.1], color=s["color"], lw=s["lw"], ls=s["ls"])
        ax.text(8.0, y + 1.1, name, ha="left", va="center", fontsize=8.5, fontweight="bold",
                color=INK)
        ax.text(15.0, y + 1.1, what, ha="left", va="center", fontsize=7.6, color=INK)
        ax.text(15.0, y - 1.3, role, ha="left", va="center", fontsize=7.2, color=MUTED,
                style="italic")
        ax.text(38.0, y, eq, ha="left", va="center", fontsize=7.6, color=INK, linespacing=1.35)
        y -= 7.6
    return save(fig, "fig_C_control_volumes.png")


# ---------------------------------------------------------------- Figure 5 (D)
MONO = "DejaVu Sans Mono"


def mod_box(ax, x, y, w, h, name, desc, fc=BOX_FC, ec="0.3", fs=7.4, lw=0.9, z=3):
    """Module box: file name (monospace, bold) on top, contents below."""
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, z=z)
    ax.text(x + w / 2, y + h - 1.0, name, ha="center", va="top", fontsize=8.0,
            family=MONO, fontweight="bold", color=INK, zorder=z + 1)
    ax.text(x + w / 2, y + h - 4.0, desc, ha="center", va="top", fontsize=fs, color=INK,
            zorder=z + 1, linespacing=1.2)


def flow_label(ax, x, y, text, ha="left", fs=7.0):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=MUTED, style="italic",
            zorder=6, linespacing=1.15)


def fig_D():
    """Code structure: modules as boxes, arrows for the data passed between them."""
    fig, ax = canvas((7.4, 8.4), (0, 100), (1, 114))
    cx = 50.0                                   # centre of the main column
    A = dict(lw=1.1, ms=9)
    dash = dict(color="0.45", lw=1.0, ls=(0, (3, 2)))

    # inputs
    mod_box(ax, cx - 19, 101, 38, 12, "coldplate/config.py",
            "1 kW case: Case = Geometry, Operating, Materials,\nLimits, Losses, DeadState, "
            "Models", fc=BOX_HI)
    mod_box(ax, 0, 101, 26, 12, "coldplate/properties.py",
            "CoolProp: ρ, μ, c_p, k, h, s;\nT(h, P); SI units, kelvin")
    mod_box(ax, 74, 101, 26, 12, "validation/data/*.csv",
            "Qu & Mudawar inputs:\ngeometry, conditions,\nsensors, digitized data", fs=7.2)

    # model.evaluate container
    x0c, x1c = 18.0, 82.0
    rbox(ax, x0c, 31.0, x1c - x0c, 66.0, fc="#F7F9FC", ec="0.35", lw=1.0, ls=(0, (4, 2)),
         r=1.2, z=1)
    ax.text(x0c + 1.2, 95.8, "coldplate/model.py:\nevaluate(case)", ha="left", va="top",
            fontsize=8.0, family=MONO, fontweight="bold", color=INK, zorder=3, linespacing=1.2)
    ax.text(x1c - 1.2, 95.8, "calls the modules below in a loop\nuntil T_out and ΔP "
            "converge (Figure 6)", ha="right", va="top", fontsize=7.0, color=MUTED, zorder=3,
            linespacing=1.2)
    mod_box(ax, cx - 16, 79, 32, 9, "geometry.py", "derive(): N, D_h, α, flow areas")
    mod_box(ax, cx - 24, 63.5, 48, 10.5, "correlations.py",
            "local_nusselt(): fd_H1, fd_H1_3, LG, LG_3, MY, MY_3\n"
            "apparent_fRe(): fd, MY, hagenbach; entry_lengths()")
    mod_box(ax, cx - 28, 45.0, 22, 12.5, "hydraulic.py",
            "pressure_drop():\nRe, ΔP_f + ΔP_m,\nW_hyd, W_elec")
    mod_box(ax, cx + 6, 45.0, 22, 12.5, "thermal.py",
            "solve_thermal(): stations,\nh(x), η_f(x), T_f, T_cf,\nT_b, T_dev (Figure 3)")
    mod_box(ax, cx - 24, 32.0, 48, 9.5, "second_law.py",
            "entropy_generation(): CV-C, CV-L (X_warm, X_gap,\nX_pump), CV-P, X_out (Figure 4)",
            fs=7.1)

    # arrows inside the model
    arrow(ax, (cx, 101), (cx, 88.2), **A)
    flow_label(ax, cx + 1.2, 99.0, "geometry, Q, T_in, V̇, models")
    arrow(ax, (cx, 79), (cx, 74.2), **A)
    flow_label(ax, cx + 1.2, 76.6, "D_h, α, N")
    xh, xt = cx - 17, cx + 17
    arrow(ax, (xh, 63.5), (xh, 57.7), **A)
    flow_label(ax, xh - 1.2, 60.6, "f_app Re", ha="right")
    arrow(ax, (xt, 63.5), (xt, 57.7), **A)
    flow_label(ax, xt + 1.2, 60.6, "Nu_x(x)")
    arrow(ax, (cx - 5.8, 53.4), (cx + 5.8, 53.4), **A)
    arrow(ax, (cx + 5.8, 49.0), (cx - 5.8, 49.0), **A)
    flow_label(ax, cx, 55.2, "Re", ha="center")
    flow_label(ax, cx, 47.2, "μ_fric (wall", ha="center")
    flow_label(ax, cx, 45.4, "viscosity)", ha="center")
    arrow(ax, (xh, 45.0), (xh, 41.7), **A)
    arrow(ax, (xt, 45.0), (xt, 41.7), **A)
    flow_label(ax, xh - 1.2, 43.4, "ΔP, W_elec", ha="right")
    flow_label(ax, xt + 1.2, 43.4, "T_f(x), T_b(x), T_out")

    # properties into the model; data into the benchmark
    ax.plot([13, 13, x0c - 0.2], [101, 68.5, 68.5], zorder=2, **dash)
    arrow(ax, (14, 68.5), (x0c - 0.2, 68.5), color="0.45", lw=1.0, ms=8)
    flow_label(ax, 1.0, 65.0, "properties at (T, P)\nfor every module")
    arrow(ax, (90, 101), (90, 25.2), color="0.45", lw=1.0, ms=8, ls=(0, (3, 2)))
    flow_label(ax, 91.0, 66, "experiment\ninputs and\ndata, never\nconfig.py")

    # outputs of evaluate: Result
    ax.text(cx, 30.2, "Result: summary(), constraint margins, feasible", ha="center",
            va="top", fontsize=7.4, color=INK, zorder=3)

    # users of evaluate
    mod_box(ax, 2, 15.5, 44, 9.5, "coldplate/optimize.py",
            "Study 1 flow_sweep, optimum_flow, (B/2C)^(1/3);\n"
            "Study 2 grid_sweep → optimize_design (SLSQP)", fs=7.1)
    mod_box(ax, 54, 15.5, 44, 9.5, "coldplate/benchmark.py",
            "load_benchmark() from validation/data only;\n"
            "predict() TC1–TC4, ΔP, water ΔT; compare() → MAPE", fs=7.1)
    arrow(ax, (cx - 12, 26.6), (24, 25.2), **A)
    arrow(ax, (cx + 12, 26.6), (76, 25.2), **A)

    # scripts and their outputs
    mod_box(ax, 2, 2, 44, 9.5, "analysis/*.py",
            "run_studies.py, run_phase1_checks.py,\nmake_report_figures.py → results/*.csv, "
            "figures/", fs=7.1)
    mod_box(ax, 54, 2, 44, 9.5, "validation/run_validation.py",
            "model matrix → validation/results/*.csv;\nparity and vs-Re plots → figures/",
            fs=7.1)
    arrow(ax, (24, 15.5), (24, 11.7), **A)
    arrow(ax, (76, 15.5), (76, 11.7), **A)
    return save(fig, "fig_D_code_structure.png")


# ---------------------------------------------------------------- Figure 6 (E)
def fig_E():
    """Solution of one case: model.evaluate() (coldplate/model.py, thermal.py)."""
    from matplotlib.patches import Polygon
    fig, ax = canvas((7.4, 8.5), (0, 100), (2, 117))
    x0, w = 16.0, 54.0                  # main column
    xc = x0 + w / 2
    gap = 3.1
    A = dict(lw=1.1, ms=9)
    steps = [   # (kind, height, text)
        ("end", 6.0, "evaluate(case): geometry, Q, $T_\\mathrm{in}$, $\\dot V$ (inlet state), "
                     "$P_\\mathrm{in}$, models"),
        ("box", 7.0, "Geometry: N, $D_h$, α, flow areas (Eq. 1)\n"
                     "inlet state: $\\dot m = \\rho(T_\\mathrm{in}, P_\\mathrm{in})\\,\\dot V$, "
                     "$h_\\mathrm{in}$"),
        ("box", 7.0, "First guess: $T_\\mathrm{out} = T_\\mathrm{in} + Q/(\\dot m c_p)$, "
                     "ΔP = 0,\nfriction viscosity = μ at the mean temperature"),
        ("box", 7.0, "Properties (CoolProp) at $T_m = (T_\\mathrm{in} + T_\\mathrm{out})/2$\n"
                     "and $P_\\mathrm{in} - \\Delta P/2$"),
        ("box", 9.0, "Hydraulic model: u, Re, $f_{app}Re$ (MY, Eq. 14),\n"
                     "ΔP = ΔP$_f$ + ΔP$_m$ (Eq. 13), friction μ from the last thermal pass,\n"
                     "$P_\\mathrm{out} = P_\\mathrm{in} - \\Delta P$"),
        ("box", 11.5, "Thermal network along x (Figure 3): $Nu_x$ (MY_3, Eqs. 8, 9),\n"
                      "h(x), $\\eta_f(x)$ at every station; coupled solve of $T_{cf}(x)$, "
                      "$T_f(x)$\nwith axial conduction (Eqs. 3, 6), $T_f$ from CoolProp h;\n"
                      "$T_b(x)$, $T_\\mathrm{out}$, $T_\\mathrm{dev}$ (Eq. 7)"),
        ("dec", 13.0, "$T_\\mathrm{out}$ changed by < $10^{-6}$ K\nand ΔP by < $10^{-6}$ ΔP ?"),
        ("box", 9.0, "Second law (Figure 4): CV-C with the exact $\\int q''/T_b\\,dA$,\n"
                     "CV-L split into $X_\\mathrm{warm}$, $X_\\mathrm{gap}$, $X_\\mathrm{pump}$; "
                     "CV-P;\noutlet exergy $X_\\mathrm{out}$ (Eqs. 17–22)"),
        ("box", 9.0, "Entry lengths; constraint margins $T_\\mathrm{dev,max} - T_\\mathrm{dev}$,\n"
                     "$\\Delta P_\\mathrm{max} - \\Delta P$, $Re_\\mathrm{max} - Re$, "
                     "$w_c - w_{c,\\min}$, $w_f - w_{f,\\min}$;\nfeasible if all ≥ 0 "
                     "(small tolerance)"),
        ("end", 6.0, "Result → optimize.py (studies), benchmark.py (Qu and Mudawar)"),
    ]
    y = 116.0
    pos = []                              # (top, bottom) of each step
    for kind, h, text in steps:
        top, bot = y, y - h
        if kind == "dec":
            ax.add_patch(Polygon([(xc, top), (x0 + w - 6, (top + bot) / 2), (xc, bot),
                                  (x0 + 6, (top + bot) / 2)], closed=True, fc="white",
                                 ec="0.2", lw=1.0, zorder=2))
            ax.text(xc, (top + bot) / 2, text, ha="center", va="center", fontsize=7.6,
                    color=INK, zorder=3, linespacing=1.25)
        else:
            rbox(ax, x0, bot, w, h, text, fc=BOX_HI if kind == "end" else BOX_FC,
                 r=2.5 if kind == "end" else 0.6, fs=7.6)
        pos.append((top, bot))
        y = bot - gap
    for (t0, b0), (t1, b1) in zip(pos[:-1], pos[1:]):
        arrow(ax, (xc, b0), (xc, t1), **A)

    # property iteration: shaded region, loop back from the decision to the properties
    i_prop, i_dec = 3, 6
    top_it, bot_it = pos[i_prop][0] + 1.6, pos[i_dec][1] - 1.4
    rect(ax, x0 - 9.5, bot_it, w + 11.5, top_it - bot_it, "#EEF2F7", ec="none", z=0)
    ax.text(x0 - 7.6, (pos[4][0] + pos[4][1]) / 2, "property iteration", ha="center",
            va="center", fontsize=7.4, color=MUTED, style="italic", rotation=90)
    ymid = (pos[i_dec][0] + pos[i_dec][1]) / 2
    yp = (pos[i_prop][0] + pos[i_prop][1]) / 2
    ax.plot([x0 + 6, x0 - 5, x0 - 5], [ymid, ymid, yp], color=INK, lw=1.1, zorder=2)
    arrow(ax, (x0 - 5, yp), (x0, yp), **A)
    ax.text(x0 - 4.0, ymid - 1.2, "no: update\n$T_\\mathrm{out}$, ΔP, μ", ha="left",
            va="top", fontsize=7.2, color=INK, linespacing=1.15)
    ax.text(xc + 1.2, pos[i_dec][1] - 0.6, "yes", ha="left", va="top", fontsize=7.4,
            color=INK)

    # side notes
    xn = x0 + w + 2.5
    note = dict(ha="left", va="center", fontsize=7.2, color=INK, linespacing=1.2)
    th_t, th_b = pos[5]
    yc5 = (th_t + th_b) / 2
    # inner loop on the thermal box: fixed 4 passes of the wall-viscosity correction
    arrow(ax, (x0 + w, yc5 - 2.6), (x0 + w, yc5 + 2.6), lw=1.0, ms=8,
          conn="arc3,rad=1.6")
    ax.text(xn + 3.6, yc5, "4 passes (fixed, no\nconvergence test):\n"
            "$Nu_x \\leftarrow Nu_{x,cp}(\\mu_b/\\mu_w)^{0.14}$;\n"
            "friction μ = mean of\n$\\mu_b(\\mu_w/\\mu_b)^{0.58}$ for the\nnext ΔP (Eq. 12)", **note)
    hy_t, hy_b = pos[4]
    ax.text(xn, (hy_t + hy_b) / 2, "if $P_\\mathrm{out}$ < 10 kPa: stop with\nan error; the "
            "optimizer\ncounts the design as\ninfeasible", **note)
    ax.text(xn, ymid, "reference design:\n3 iterations;\nat most 50", **note)
    return save(fig, "fig_E_solver_flowchart.png")


# ---------------------------------------------------------------- Figure 8 (F)
def _csv_param(name: str, key: str = "parameter") -> dict:
    with open(ROOT / "validation" / "data" / name, newline="", encoding="utf-8") as fh:
        return {r[key]: r for r in csv.DictReader(fh)}


def fig_F():
    """Qu and Mudawar test section as modelled (validation/data/*.csv, validation/results/)."""
    from matplotlib.patches import Circle
    geo = _csv_param("qu_mudawar_geometry.csv")
    sen = _csv_param("qu_mudawar_sensors.csv", key="sensor")
    con = _csv_param("qu_mudawar_conditions.csv")
    v = {k: float(geo[k]["value"]) for k in ("n_channels", "channel_width_Wch",
                                             "channel_depth_Hch", "wall_thickness",
                                             "channel_length_L", "cover_plate_thickness_Hw1",
                                             "bottom_to_channel_bottom_Hw2",
                                             "thermocouple_plane_Hth",
                                             "tc_depth_below_channel_bottom",
                                             "solid_conductivity", "cover_plate_conductivity",
                                             "heat_sink_top_width", "heat_sink_top_length")}
    tcx = [float(sen[f"TC{i}"]["x_from_inlet_m"]) for i in range(1, 5)]
    th = next(r for r in read(VRES / "thermal_model_matrix.csv") if r["nusselt_model"] == "MY_3"
              and r["axial_conduction"] is True and r["viscosity_correction"] is True)
    dp = {r["minor_losses_K1"]: r for r in read(VRES / "dP_model_matrix.csv")
          if r["friction_model"] == "MY" and r["viscosity_correction"] is True}

    fig, ax = canvas((7.4, 8.3), (0, 100), (-3, 109))
    L_mm = v["channel_length_L"] * 1e3

    # ---------------- (a) section along the flow
    ax.text(0, 108, "(a) Section along a channel, at the centre plane (x to scale; depth "
            "exaggerated)", fontsize=9.5, fontweight="bold", va="top", color=INK)
    xa, xb = 24.0, 72.0                         # channel inlet and outlet
    sx = (xb - xa) / L_mm                       # drawing units per mm along x
    sz = 2.2                                    # drawing units per mm in depth
    y_ch = 82.0                                 # channel floor
    y_top = y_ch + 3.0                          # channel top (depth exaggerated x 1.9)
    y_tc = y_ch - v["tc_depth_below_channel_bottom"] * 1e3 * sz
    y_uc = y_ch - v["bottom_to_channel_bottom_Hw2"] * 1e3 * sz
    rect(ax, 10, 61.5, 76, y_uc - 61.5, CU, ec="0.3", hatch="xx", z=1).set_hatchcolor("#A87038")
    rect(ax, 10, y_uc, 76, y_ch - y_uc, CU, ec="0.3", z=1)
    rect(ax, xa, y_ch, xb - xa, y_top - y_ch, WATER, ec="0.3", z=2)
    rect(ax, 10, y_ch, xa - 10, y_top - y_ch, CU, ec="none", z=1)
    rect(ax, xb, y_ch, 86 - xb, y_top - y_ch, CU, ec="none", z=1)
    for x0p in (12.0, xb):                      # plenums (shape not reported: schematic)
        rect(ax, x0p, 73.5, 12.0, y_top - 73.5, WATER, ec="0.3", z=2)
    rect(ax, 10, y_top, 76, 5.0, LID, ec="0.3", z=2)
    ax.text(48, y_top + 2.5, f"polycarbonate cover, {v['cover_plate_thickness_Hw1'] * 1e3:.1f} mm, "
            f"k = {v['cover_plate_conductivity']:g} W/m·K (top wall ≈ adiabatic)",
            ha="center", va="center", fontsize=7.4, color=INK, zorder=4)
    for xx in (30, 46, 62):
        arrow(ax, (xx, (y_ch + y_top) / 2), (xx + 4, (y_ch + y_top) / 2), lw=0.9, ms=6, z=4)
    ax.text(48, 64.4, "copper block with 12 cartridge heaters (Ø 6.35 mm holes); "
            "layout drawn schematically", ha="center", va="center", fontsize=7.2, color=INK,
            zorder=4, bbox=dict(fc="white", ec="none", pad=0.8, alpha=0.85))
    ax.plot([10, 86], [y_uc, y_uc], color=INK, lw=1.0, ls=(0, (4, 2)), zorder=3)
    for xx in np.linspace(41, 69, 5):
        arrow(ax, (xx, y_uc - 2.6), (xx, y_uc - 0.2), lw=0.9, ms=6, z=4)
    ax.text(10.6, y_uc - 1.5, "unit-cell bottom: uniform q″ in the model", ha="left",
            va="center", fontsize=7.0, color=INK, zorder=4,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    # thermocouple plane and TC1-TC4 at their true x
    ax.plot([xa, xb], [y_tc, y_tc], color="0.25", lw=0.8, ls=(0, (1, 1.5)), zorder=3)
    for i, xt in enumerate(tcx, start=1):
        xx = xa + sx * xt * 1e3
        node(ax, xx, y_tc, r=0.75)
        ax.text(xx, y_tc - 1.4, f"TC{i}", ha="center", va="top", fontsize=7.4, color=INK,
                fontweight="bold")
        ax.text(xx, y_tc + 1.2, f"x = {xt * 1e3:.3f} mm", ha="center", va="bottom",
                fontsize=6.8, color=INK)
    # inlet / outlet ports, water thermocouples and pressure taps in the deep plenums
    for side, x_port, x_T, x_P, sgn in (("in", 15.0, 18.6, 22.2, -1), ("out", 81.0, 77.4,
                                                                       73.8, 1)):
        if side == "in":
            arrow(ax, (x_port, 98.5), (x_port, 80.0), lw=1.3, ms=9, z=5)
        else:
            arrow(ax, (x_port, 80.0), (x_port, 98.5), lw=1.3, ms=9, z=5)
        ax.text(x_port + (-1.0 if side == "in" else 1.0), 97.5,
                "water in,\n15 °C" if side == "in" else "water\nout",
                ha="right" if side == "in" else "left", va="top", fontsize=7.2, color=INK)
        ax.plot([x_T, x_T], [78.0, 95.5], color=INK, lw=1.2, zorder=5)
        rbox(ax, x_T - 1.5, 95.5, 3.0, 2.8, "T", fc="white", ec=INK, fs=7.0, r=0.3, z=5,
             weight="bold")
        ax.plot([x_P, x_P], [74.6, 95.5], color=INK, lw=2.0, zorder=5)
        ax.add_patch(Circle((x_P, 97.0), 1.6, fc="white", ec=INK, lw=1.0, zorder=6))
        ax.text(x_P, 97.0, "P", ha="center", va="center", fontsize=7.0, fontweight="bold",
                color=INK, zorder=7)
        ax.text(x_P, 99.4, f"$P_\\mathrm{{{side}}}$", ha="center", va="bottom", fontsize=7.4,
                color=INK)
        ax.text(x_T, 99.4, f"$T_\\mathrm{{{side}}}$", ha="center", va="bottom", fontsize=7.4,
                color=INK)
    ax.text(18.0, 72.6, "inlet plenum", ha="center", va="top", fontsize=7.0, color=INK)
    ax.text(78.0, 72.6, "outlet plenum", ha="center", va="top", fontsize=7.0, color=INK)
    # length dimension
    ax.annotate("", xy=(xa, 102.6), xytext=(xb, 102.6),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.8, shrinkA=0, shrinkB=0))
    ax.text(48, 103.2, f"channel length L = {L_mm:.3f} mm", ha="center", va="bottom",
            fontsize=7.4, color=INK)
    for xx in (xa, xb):
        ax.plot([xx, xx], [y_top + 5.0, 102.6], color="0.5", lw=0.6, ls=(0, (2, 2)))
    # depth dimensions on the right
    def vdim(x, y0, y1, text):
        ax.annotate("", xy=(x, y0), xytext=(x, y1),
                    arrowprops=dict(arrowstyle="<->", color=INK, lw=0.8, shrinkA=0, shrinkB=0))
        ax.text(x + 0.8, (y0 + y1) / 2, text, ha="left", va="center", fontsize=7.0, color=INK,
                linespacing=1.1)
    vdim(87.5, y_ch, y_top, f"$H_{{ch}}$ = {v['channel_depth_Hch'] * 1e6:.0f} µm")
    vdim(87.5, y_tc, y_ch, f"d = {v['tc_depth_below_channel_bottom'] * 1e3:.3f} mm")
    vdim(87.5, y_uc, y_tc, f"$H_{{th}}$ = {v['thermocouple_plane_Hth'] * 1e3:.3f} mm")
    ax.text(87.5, y_uc - 1.0, f"$H_{{w2}}$ = d + $H_{{th}}$\n= "
            f"{v['bottom_to_channel_bottom_Hw2'] * 1e3:.3f} mm,\nthe copper for axial\n"
            "conduction ($t_{ax}$)", ha="left", va="top", fontsize=7.0, color=INK,
            linespacing=1.1)

    # ---------------- (b) cross-section across the channels, to scale
    ax.text(0, 58.0, f"(b) Cross-section across the channels (to scale; 3 of the "
            f"{v['n_channels']:.0f} channels shown)", fontsize=9.5, fontweight="bold",
            va="top", color=INK)
    s = 0.0215                                   # drawing units per µm
    wc, wf, H = (v[k] * 1e6 for k in ("channel_width_Wch", "wall_thickness",
                                      "channel_depth_Hch"))
    xb0, yb0 = 5.0, 34.5
    n_c = 3
    width = n_c * wc + (n_c + 1) * wf
    rect(ax, xb0, yb0 - 2.6, width * s, 2.6, CU, ec="0.3")
    xx = xb0
    for k in range(2 * n_c + 1):
        wk = wf if k % 2 == 0 else wc
        rect(ax, xx, yb0, wk * s, H * s, CU if k % 2 == 0 else WATER, ec="0.3")
        if k % 2 == 1:
            xm = xx + wk * s / 2
            for p0, p1 in (((xm, yb0 + 0.3), (xm, yb0 + 3.6)),
                           ((xx + 0.25, yb0 + H * s / 2), (xx + 1.8, yb0 + H * s / 2)),
                           ((xx + wk * s - 0.25, yb0 + H * s / 2 - 3.0),
                            (xx + wk * s - 1.8, yb0 + H * s / 2 - 3.0))):
                arrow(ax, p0, p1, color=VERM, lw=0.9, ms=5, z=4)
        xx += wk * s
    rect(ax, xb0, yb0 + H * s, width * s, 3.0, LID, ec="0.3")
    ax.text(xb0 + width * s / 2, yb0 + H * s + 1.5, "cover", ha="center", va="center",
            fontsize=7.0, color=INK)
    ax.text(xb0 + width * s / 2, yb0 - 1.3, "copper", ha="center", va="center", fontsize=7.0,
            color=INK)
    # dimensions: the left wall and the middle channel, on one line
    yd = yb0 - 3.8
    for xs0, span, lab in ((xb0, wf, f"wall {wf:.0f} µm"),
                           (xb0 + (2 * wf + wc) * s, wc, f"channel {wc:.0f} µm")):
        ax.annotate("", xy=(xs0, yd), xytext=(xs0 + span * s, yd),
                    arrowprops=dict(arrowstyle="<->", color=INK, lw=0.7, shrinkA=0, shrinkB=0))
        ax.text(xs0 + span * s / 2, yd - 0.6, lab, ha="center", va="top", fontsize=7.0)
    xr = xb0 + width * s + 1.0
    ax.annotate("", xy=(xr, yb0), xytext=(xr, yb0 + H * s),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.7, shrinkA=0, shrinkB=0))
    ax.text(xr + 0.8, yb0 + H * s / 2 + 2.0, f"{H:.0f} µm", ha="left", va="center",
            fontsize=7.0)
    ax.text(xr + 0.8, yb0 + 3.0, "arrows: heat enters\nthe water through\nthree walls; the "
            "cover\nis the fourth", ha="left", va="center", fontsize=7.0, color=INK,
            linespacing=1.15)

    # model inputs, next to (b)
    c = {k: con[k]["value"] for k in ("inlet_temperature", "q_eff_level_1", "q_eff_level_2",
                                      "power_at_100_W_cm2", "power_at_200_W_cm2")}
    txt = ("As modelled (inputs only from validation/data/*.csv,\nnever config.py):\n"
           f"• {v['n_channels']:.0f} channels, L = {L_mm:.3f} mm, copper\n"
           f"   k = {v['solid_conductivity']:g} W/m·K, inlet {c['inlet_temperature']} °C\n"
           f"• q″ = {c['q_eff_level_1']} and {c['q_eff_level_2']} W/cm² on "
           f"{v['heat_sink_top_width'] * 1e2:.1f} × {v['heat_sink_top_length'] * 1e2:.2f} cm\n"
           f"   ({c['power_at_100_W_cm2']} and {c['power_at_200_W_cm2']} W), uniform (B2)\n"
           "• flow from the paper's Re with inlet properties (B1);\n"
           "   inlet pressure 2 bar, not reported (B4)\n"
           "• thermocouples: 1D conduction through d below\n   the channel floor (B5)\n"
           "• plenum losses: none, or $K_c = K_e = 1$ at channel\n   velocity (B3)")
    ax.text(58.0, 54.5, txt, ha="left", va="top", fontsize=7.2, color=INK, linespacing=1.32)

    # ---------------- (c) what is compared with what
    ax.text(0, 25.5, "(c) Measured quantity, where it is measured, and the model quantity it is "
            "compared with", fontsize=9.5, fontweight="bold", va="top", color=INK)
    cols = (4.0, 28.0, 52.5, 83.0)
    yh = 20.4
    for xcol, head in zip(cols, ("Measured (paper figure)", "Sensor location",
                                 "Model quantity", "Selected model, MAPE")):
        ax.text(xcol, yh, head, ha="left", va="center", fontsize=7.6, fontweight="bold",
                color=INK)
    ax.plot([0, 100], [yh - 1.8, yh - 1.8], color="0.3", lw=0.8)
    rows = [
        ("tc", "Thermocouple rise above\nthe inlet, TC1–TC4,\nFigs. 6(a), 6(b)",
         "copper, d = 2.462 mm below\nthe channel floor, centre plane,\n"
         "x = 5.0, 16.6, 28.2, 39.8 mm",
         r"$T_{cf}(x_i) + q''d/k_s - T_\mathrm{in}$" "\n(Eq. 7 with d instead of $t_b$)",
         f"{100 * th['MAPE_TC']:.1f} % ({th['n_TC']:.0f} points)"),
        ("P", "Pressure drop,\nFig. 4(a)", "taps in the deep parts of\nthe inlet and outlet "
         "plenums", "plenum to plenum: channel\nfriction (MY apparent, wall\nviscosity), "
         "± plenum losses",
         f"{100 * dp[False]['MAPE_dP']:.1f} % without plenum\nlosses; {100 * dp[True]['MAPE_dP']:.1f} % "
         f"with K = 1\n({dp[False]['n']:.0f} points)"),
        ("T", "Water temperature rise,\nFig. 5", "thermocouples in the inlet\nand outlet plenums",
         r"$T_\mathrm{out} - T_\mathrm{in}$ from the first law," "\n"
         r"$h_\mathrm{out} = h_\mathrm{in} + Q/\dot m$ (energy check)",
         f"{100 * th['MAPE_water_dT']:.1f} %"),
    ]
    y = yh - 5.4
    for mark, *cells in rows:
        if mark == "tc":
            node(ax, 1.6, y, r=0.75)
        elif mark == "P":
            ax.add_patch(Circle((1.6, y), 1.3, fc="white", ec=INK, lw=0.9))
            ax.text(1.6, y, "P", ha="center", va="center", fontsize=6.4, fontweight="bold")
        else:
            rbox(ax, 0.3, y - 1.2, 2.6, 2.4, "T", fc="white", ec=INK, fs=6.4, r=0.2,
                 weight="bold")
        for xcol, cell in zip(cols, cells):
            ax.text(xcol, y, cell, ha="left", va="center", fontsize=7.2, color=INK,
                    linespacing=1.2)
        y -= 7.0
        ax.plot([0, 100], [y + 3.0, y + 3.0], color="0.8", lw=0.6)
    return save(fig, "fig_F_benchmark_setup.png")


# ---------------------------------------------------------------- Figure 9 (G)
RAW = ROOT / "validation" / "data" / "raw"


def _pdf_page_images(pdf: Path, page: int) -> list:
    """Scanned images of one PDF page, decoded, with their position in 600-dpi page pixels.

    Minimal reader for this file only: the Qu and Mudawar PDF stores each figure row as a
    1-bit CCITT G4 image mask placed by a `cm` matrix. Decoding is done by Pillow (libtiff)
    after wrapping the G4 data in a TIFF header; no PDF renderer is needed. The integer
    offset (floor of the placement at 600 dpi) reproduces the pdftoppm render that the
    digitizer used (checked against the overlay in fig_G).
    """
    import io
    import re
    import struct
    import zlib
    from math import floor

    from PIL import Image
    b = pdf.read_bytes()

    def obj(n):
        return re.search(rb"(?<![0-9])%d 0 obj(.*?)endobj" % n, b, re.S).group(1)

    def leaves(n):
        d = obj(n)
        if re.search(rb"/Type\s*/Pages", d):
            ks = re.findall(rb"(\d+) 0 R", re.search(rb"/Kids\s*\[(.*?)\]", d, re.S).group(1))
            return [p for k in ks for p in leaves(int(k))]
        return [n]

    def stream(o):
        n = int(re.search(rb"/Length (\d+)", o).group(1))
        i = o.index(b"stream") + len(b"stream")
        while o[i:i + 1] in (b"\r", b"\n"):
            i += 1
        return o[i:i + n]

    root = int(re.search(rb"/Root (\d+) 0 R", b).group(1))
    pg = obj(leaves(int(re.search(rb"/Pages (\d+) 0 R", obj(root)).group(1)))[page - 1])
    res = obj(int(re.search(rb"/Resources (\d+) 0 R", pg).group(1)))
    xobj = {k.decode(): int(v) for k, v in re.findall(rb"/(Im\d+) (\d+) 0 R", res)}
    content = b""
    for c in re.findall(rb"(\d+) 0 R", re.search(rb"/Contents\s*(\[.*?\]|\d+ 0 R)", pg,
                                                   re.S).group(1)):
        o = obj(int(c))
        s = re.search(rb"stream\r?\n(.*?)endstream", o, re.S).group(1)
        content += zlib.decompress(s) if b"FlateDecode" in o[:200] else s
    cms = {m.group(2).decode(): [float(t) for t in m.group(1).split()]
           for m in re.finditer(rb"([-\d. ]+) cm\s*/(Im\d+) Do", content)}
    h_pt = float(re.search(rb"/MediaBox \[([^\]]+)\]", pg).group(1).split()[3])
    out = []
    for name, n in xobj.items():
        o = obj(n)
        assert b"/CCITTFaxDecode" in o and b"/K -1" in o, "only CCITT G4 images handled"
        W = int(re.search(rb"/Width (\d+)", o).group(1))
        H = int(re.search(rb"/Height (\d+)", o).group(1))
        data = stream(o)
        tags = [(256, 4, W), (257, 4, H), (258, 3, 1), (259, 3, 4), (262, 3, 0),
                (273, 4, 8 + 2 + 12 * 8 + 4), (278, 4, H), (279, 4, len(data))]
        tif = bytearray(b"II*\x00" + struct.pack("<IH", 8, len(tags)))
        for tag, typ, val in tags:
            tif += struct.pack("<HHIHH" if typ == 3 else "<HHII", tag, typ, 1,
                               *((val, 0) if typ == 3 else (val,)))
        tif += struct.pack("<I", 0) + data
        arr = np.array(Image.open(io.BytesIO(bytes(tif))).convert("L"))
        a, _, _, d, e, f = cms[name]
        out.append({"name": name, "img": arr, "x0": floor(e * 600 / 72),
                    "y0": floor((h_pt - f - d) * 600 / 72)})
    return out


def fig_G():
    """Data extraction for Fig. 6(a): original scan, detection overlay, calibrated points."""
    import json

    from matplotlib.patches import Rectangle
    from PIL import Image
    meta = json.loads((RAW / "fig6a_meta.json").read_text())
    pts = read(RAW / "fig6a_points.csv")
    cal = meta["calibration"]
    # the scan holding Fig. 6(a): the image that contains the calibration points
    imgs = _pdf_page_images(RAW / "qu_mudawar_2002.pdf", meta["page"])
    sc = next(m for m in imgs if m["y0"] < cal["y2"][1] < m["y0"] + m["img"].shape[0])
    ov = np.array(Image.open(RAW / "fig6a_overlay.png").convert("RGB"))
    pad = 30                                   # qm_figures.py: overlay = frame box +/- 30 px
    box = (774, 1494, 698, 2138)               # qm_figures.py PANELS["fig6a"]["box"] (T, B, L, R)
    ox, oy = box[2] - pad, box[0] - pad
    # check: the PDF scan reproduces the digitizer's render pixel for pixel (grey pixels only)
    iy = np.arange(ov.shape[0]) + oy - sc["y0"]
    ix = np.arange(ov.shape[1]) + ox - sc["x0"]
    sub = sc["img"][np.ix_(iy, ix)].astype(int)
    o16 = ov.astype(int)
    grey = (np.abs(o16[..., 0] - o16[..., 1]) + np.abs(o16[..., 1] - o16[..., 2])) < 10
    mad = float(np.mean(np.abs(sub[grey] - o16[..., 0][grey])))
    print(f"  fig_G: scan vs overlay render, mean |difference| on grey pixels = {mad:.3f}")
    assert mad < 1.0, "the PDF scan does not line up with the digitizer's render"

    CAL = "#C2185B"                             # calibration rings (magenta, as in the overlay)
    H_, W_ = sc["img"].shape
    ext_sc = (sc["x0"] - 0.5, sc["x0"] + W_ - 0.5, sc["y0"] + H_ - 0.5, sc["y0"] - 0.5)
    ext_ov = (ox - 0.5, ox + ov.shape[1] - 0.5, oy + ov.shape[0] - 0.5, oy - 0.5)
    win_a = (585, 2190, oy, 1622)               # original: overlay window + tick labels
    zoom = (818, 1058, 1064, 1254)              # page px of the zoom window

    def to_data(px, py):                        # the two-point calibration of fig6a_meta.json
        (x1, _, v1), (x2, _, v2) = cal["x1"], cal["x2"]
        (_, y1, w1), (_, y2, w2) = cal["y1"], cal["y2"]
        return v1 + (px - x1) * (v2 - v1) / (x2 - x1), w1 + (py - y1) * (w2 - w1) / (y2 - y1)

    FW, FH = 7.4, 5.92
    fig = plt.figure(figsize=(FW, FH))

    def axes_in(x, y, w, h):                    # axes placed in inches
        return fig.add_axes([x / FW, y / FH, w / FW, h / FH])

    def frame(ax_):
        ax_.set_xticks([])
        ax_.set_yticks([])
        ax_.grid(False)
        for sp in ax_.spines.values():
            sp.set_visible(True)
            sp.set_color("0.6")
            sp.set_linewidth(0.6)

    wa = 3.6
    ha_ = wa * (win_a[3] - win_a[2]) / (win_a[1] - win_a[0])
    hb = wa * ov.shape[0] / ov.shape[1]
    ytop = FH - 0.32
    a = axes_in(0.02, ytop - ha_, wa, ha_)
    b = axes_in(FW - wa - 0.02, ytop - hb, wa, hb)
    a.imshow(sc["img"], cmap="gray", vmin=0, vmax=255, extent=ext_sc, interpolation="none")
    a.set_xlim(win_a[0], win_a[1])
    a.set_ylim(win_a[3], win_a[2])
    b.imshow(ov, extent=ext_ov, interpolation="none")
    b.set_xlim(ext_ov[0], ext_ov[1])
    b.set_ylim(ext_ov[2], ext_ov[3])
    for ax_, title in ((a, "(a) Original Fig. 6(a): PDF page 9 at 600 dpi"),
                       (b, "(b) Detected markers (fig6a_overlay.png)")):
        frame(ax_)
        ax_.set_title(title, fontsize=8.2, loc="left", pad=4)
        for key, lab, off, ha in (("x1", "x₁", (0, 7), "center"), ("x2", "x₂", (0, 7), "center"),
                                  ("y1", "y₁", (7, 2), "left"), ("y2", "y₂", (7, 2), "left")):
            px, py = cal[key][0], cal[key][1]
            ax_.plot(px, py, "o", ms=7, mfc="none", mec=CAL, mew=1.5, zorder=5)
            ax_.annotate(lab, (px, py), xytext=off, textcoords="offset points", ha=ha,
                         va="bottom", fontsize=7.4, color=INK, fontweight="bold",
                         bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.9), zorder=6)
        ax_.add_patch(Rectangle((zoom[0], zoom[2]), zoom[1] - zoom[0], zoom[3] - zoom[2],
                                fill=False, ec="black", lw=0.9, ls=(0, (3, 1.5)), zorder=6))
    yt = ytop - max(ha_, hb) - 0.06
    fig.text(0.02 / FW, yt / FH,
             "Rings: the four calibration points on major ticks, x₁ = Re 200, x₂ = Re 1600, "
             "y₁ = 20 K, y₂ = 80 K (WebPlotDigitizer 4-point\ncalibration, rotation corrected). "
             "Dashed box: zoom in (c) and (d). The scan and the digitizer's render agree pixel "
             "for pixel.", ha="left", va="top", fontsize=7.0, color=INK, linespacing=1.25)

    # zooms and calibrated values
    wz = 2.2
    hz = wz * (zoom[3] - zoom[2]) / (zoom[1] - zoom[0])
    yz = yt - 0.62 - hz
    c = axes_in(0.02, yz, wz, hz)
    d = axes_in(0.02 + wz + 0.14, yz, wz, hz)
    for ax_, img, ext, title in ((c, sc["img"], ext_sc, "(c) Zoom, original"),
                                 (d, ov, ext_ov, "(d) Zoom, overlay")):
        ax_.imshow(img, cmap="gray" if img.ndim == 2 else None, vmin=0, vmax=255, extent=ext,
                   interpolation="none")
        ax_.set_xlim(zoom[0], zoom[1])
        ax_.set_ylim(zoom[3], zoom[2])
        frame(ax_)
        ax_.set_title(title, fontsize=8.2, loc="left", pad=4)
    fig.text(0.02 / FW, (yz - 0.06) / FH,
             "Overlay: a circle on every detected marker, coloured by series (TC1 blue, "
             "TC2 orange,\nTC3 red, TC4 green); magenta box: marker partly hidden behind a "
             "repeat run, kept\nin the CSV but left out of the MAPE.", ha="left", va="top",
             fontsize=7.0, color=INK, linespacing=1.25)

    e = axes_in(5.32, yz, FW - 5.32 - 0.08, hz)
    shape = {"TC1": "^", "TC2": "v", "TC3": "s", "TC4": "D"}
    for tc, mk in shape.items():
        for hid in (False, True):
            sel = [p for p in pts if p["series"] == tc and p["partly_hidden"] is hid]
            if sel:
                e.plot([p["x"] for p in sel], [p["y"] for p in sel], mk, ms=3.4,
                       mfc="white" if hid else "black", mec="black", mew=0.7, ls="none",
                       label=tc if not hid else None)
    e.plot([], [], "s", ms=3.4, mfc="white", mec="black", mew=0.7, label="partly hidden")
    (r0, t1), (r1, t0) = to_data(zoom[0], zoom[2]), to_data(zoom[1], zoom[3])
    e.add_patch(Rectangle((r0, t0), r1 - r0, t1 - t0, fill=False, ec="black", lw=0.8,
                          ls=(0, (3, 1.5))))
    e.set_xlim(0, 1800)
    e.set_ylim(10, 100)
    e.set_xticks([0, 600, 1200, 1800])
    e.set_xlabel("Re", fontsize=8, labelpad=1)
    e.set_ylabel(r"$T_{th} - T_\mathrm{in}$ (K)", fontsize=8, labelpad=1)
    e.tick_params(labelsize=7.2)
    n_h = sum(p["partly_hidden"] is True for p in pts)
    e.set_title("(e) Calibrated values", fontsize=8.2, loc="left", pad=4)
    e.legend(loc="upper right", fontsize=6.6, handletextpad=0.2, borderaxespad=0.3,
             labelspacing=0.2, frameon=True, framealpha=0.95, edgecolor="none")
    fig.text(5.32 / FW, (yz - 0.36) / FH, f"fig6a_points.csv: {len(pts)} markers,\n"
             f"{n_h} of them partly hidden", ha="left", va="top", fontsize=7.0, color=INK,
             linespacing=1.25)

    # pipeline strip (the steps of section 7.5)
    s_ax = axes_in(0.02, 0.05, FW - 0.04, 0.42)
    s_ax.axis("off")
    s_ax.set_xlim(0, 100)
    s_ax.set_ylim(0, 10)
    steps = ["PDF page → 600-dpi\nimage", "frame lines and\nmajor ticks",
             "template matching\nof the markers", "WebPlotDigitizer\ncalibration",
             "raw points\nand overlay", "benchmark CSVs\n(fill_csv.py)"]
    wbox, gap_ = 14.6, 2.48
    for i, t in enumerate(steps):
        x = i * (wbox + gap_)
        rbox(s_ax, x, 0.4, wbox, 9.2, t, fc=BOX_HI if i in (0, 5) else BOX_FC, fs=6.8, r=0.5)
        if i:
            arrow(s_ax, (x - gap_ + 0.2, 5.0), (x - 0.2, 5.0), lw=0.9, ms=6)
    return save(fig, "fig_G_data_extraction.png")


# ---------------------------------------------------------------- Figure 7 (I)
def fig_I():
    """Local Nu(x) of fd_H1, LG_3 and MY_3 in the Qu and Mudawar channel (correlations only)."""
    import warnings
    _coldplate()
    from coldplate.benchmark import flow_from_reynolds, load_benchmark
    from coldplate.correlations import local_nusselt, nu_fd_H1_3, z_th_lee_garimella
    from coldplate.properties import props
    with warnings.catch_warnings():      # one benchmark row (system pressure) is 'missing'
        warnings.simplefilter("ignore")
        bm = load_benchmark()
    g, op = bm.case.geometry, bm.case.operating
    q_W_cm2, Re = 100.0, 900.0
    # Pr at the mean water temperature of this run (first law, inlet-defined Re as in B1)
    f_in = props(op.T_in, op.P_in, op.fluid)
    m_dot = f_in.rho * flow_from_reynolds(bm, Re)
    T_m = op.T_in + 0.5 * q_W_cm2 * 1e4 * bm.A_t / (m_dot * f_in.cp)
    Pr = props(T_m, op.P_in, op.fluid).Pr
    D_h = 2 * g.w_c * g.H / (g.w_c + g.H)
    L_mm = g.L * 1e3
    x = np.concatenate([np.geomspace(0.01e-3, 2e-3, 300), np.linspace(2e-3, g.L, 500)[1:]])
    nu = {m: np.asarray(local_nusselt(m, x, Re, Pr, g.w_c, g.H), dtype=float)
          for m in ("fd_H1", "LG_3", "MY_3")}
    nu_fd3 = nu_fd_H1_3(g.w_c / g.H)
    L_th = z_th_lee_garimella(g.H / g.w_c) * Re * Pr * D_h          # Eq. (11), alpha_LG = H/w_c
    tcx = [float(r["x_from_inlet_m"]) for k, r in _csv_param("qu_mudawar_sensors.csv",
                                                             key="sensor").items()
           if k.startswith("TC")]

    style = {
        "MY_3": dict(color="black", ls="-", lw=2.3,
                     label="MY_3 (selected): simultaneously developing, 3 walls"),
        "LG_3": dict(color=NAVY, ls=(0, (6, 2.5)), lw=1.8,
                     label="LG_3: thermally developing, 3 walls"),
        "fd_H1": dict(color="0.5", ls=(0, (7, 2, 1.5, 2)), lw=1.8,
                      label="fd_H1 (proposal): fully developed, 4 walls"),
    }
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.axhline(nu_fd3, color="0.55", lw=0.9, ls=(0, (1, 1.6)), zorder=1)
    ax.text(24.0, nu_fd3 + 0.2, f"fully developed, 3 walls (fd_H1_3) = {nu_fd3:.2f}",
            ha="center", va="bottom", fontsize=7.4, color=MUTED)
    for i, xt in enumerate(tcx, start=1):
        ax.axvline(xt * 1e3, color="0.6", lw=0.8, ls=(0, (2, 2)), zorder=1)
        ax.text(xt * 1e3 + 0.4, 0.5, f"TC{i}", ha="left", va="bottom", fontsize=7.6, color=INK)
    for m in ("fd_H1", "LG_3", "MY_3"):
        ax.plot(x * 1e3, nu[m], zorder=3, **style[m])
    # selective labels: values at TC1 and at the outlet
    i1 = int(np.argmin(np.abs(x - tcx[0])))
    xt1 = x[i1] * 1e3
    ax.annotate(f"{nu['MY_3'][i1]:.1f}", (xt1, nu["MY_3"][i1]), xytext=(5, 3),
                textcoords="offset points", ha="left", va="bottom", fontsize=7.6, color=INK)
    ax.annotate(f"{nu['LG_3'][i1]:.1f}", (xt1, nu["LG_3"][i1]), xytext=(-5, -3),
                textcoords="offset points", ha="right", va="top", fontsize=7.6, color=NAVY)
    ax.annotate(f"{nu['fd_H1'][0]:.2f} everywhere", (xt1, nu["fd_H1"][i1]),
                xytext=(5, -4), textcoords="offset points", ha="left", va="top", fontsize=7.6,
                color=INK)
    ax.text(L_mm - 0.3, nu["MY_3"][-1] + 0.45, f"outlet: {nu['MY_3'][-1]:.2f} (MY_3), "
            f"{nu['LG_3'][-1]:.2f} (LG_3)", ha="right", va="bottom", fontsize=7.6, color=INK)
    ax.text(0.985, 0.56,
            f"At TC1 the developing models give {nu['MY_3'][i1] / nu['fd_H1'][i1]:.1f}× "
            f"(MY_3) and {nu['LG_3'][i1] / nu['fd_H1'][i1]:.1f}× (LG_3)\n"
            "the fully developed value, and still "
            f"{nu['MY_3'][-1] / nu['fd_H1'][-1]:.2f}× at the outlet.\n"
            f"Thermal entry length (Lee-Garimella Eq. 11): {L_th * 1e3:.0f} mm, more than "
            f"L = {L_mm:.1f} mm:\nthe whole channel is thermally developing.",
            transform=ax.transAxes, ha="right", va="center", fontsize=7.6, color=INK,
            linespacing=1.3, bbox=dict(fc="white", ec="none", pad=1.5, alpha=0.9))
    ax.set_xlim(0, L_mm)
    ax.set_ylim(0, 25)
    ax.set_xlabel("Distance from the channel inlet x (mm)")
    ax.set_ylabel(r"Local Nusselt number $Nu_x$ ($D_h$ based)")
    top = ax.secondary_xaxis("top", functions=(lambda v: v * 1e-3 / (Re * Pr * D_h),
                                               lambda z: z * Re * Pr * D_h * 1e3))
    top.set_xlabel(r"$z^* = x / (Re\,Pr\,D_h)$", fontsize=8.5, labelpad=4)
    top.set_xticks([0, 0.005, 0.01, 0.015, 0.02])
    top.tick_params(labelsize=8)
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.985), handlelength=3.2, fontsize=7.8,
              frameon=True, facecolor="white", edgecolor="none", framealpha=0.95)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.8, bottom=0.115)
    fig_title(fig, ax, "Local Nusselt number along the Qu and Mudawar channel "
              f"({g.w_c * 1e6:.0f} × {g.H * 1e6:.0f} µm, $D_h$ = {D_h * 1e6:.0f} µm, "
              f"L = {L_mm:.1f} mm)\n{q_W_cm2:.0f} W/cm², Re = {Re:.0f}, Pr = {Pr:.2f} "
              f"(water at the {T_m - 273.15:.1f} °C mean)\ncorrelations only: constant "
              "properties, no wall-viscosity correction", y=1.02)
    return save(fig, "fig_I_local_Nu.png")


FIGS = {"J2": fig_J2, "J1": fig_J1, "J3": fig_J3, "J5": fig_J5, "J4": fig_J4, "H": fig_H,
        "B": fig_B, "C": fig_C, "D": fig_D, "E": fig_E, "F": fig_F, "G": fig_G, "I": fig_I}

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(FIGS)):
        FIGS[k]()
