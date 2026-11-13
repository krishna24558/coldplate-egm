"""Qu & Mudawar (2002) benchmark: build the experiment case and predict what was measured.

Inputs come only from validation/data/*.csv (never from config.py). Every value
there carries a status and paper location; see validation/README.md.

Benchmark-specific assumptions (also listed in validation/README.md):
  B1  Reynolds number uses inlet-temperature properties. Supported by the paper's
      own numbers: Re = 1672 at 15 C gives ~1133 ml/min vs the stated 1136.4.
  B2  Heat Q = q_eff x A_t (Eq. 1) enters uniformly over the planform; heat loss
      (< 1 %) is neglected.
  B3  Plenum contraction and expansion losses use K_c = K_e = 1.0 at channel
      velocity, from the paper's remark that its coefficients are "close to
      unity". The paper's Eq. 18-22 are not yet transcribed.
  B4  Inlet pressure 2 bar (not reported); it only affects properties slightly.
  B5  Thermocouples: 1D conduction from the channel floor through
      tc_depth_below_channel_bottom of copper at the planform heat flux.
"""

import csv
import warnings
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

import numpy as np

from .config import Case, DeadState, Geometry, Limits, Losses, Materials, Operating
from .model import evaluate
from .properties import props
from .thermal import temperature_below_channels

DATA_DIR = Path(__file__).resolve().parents[1] / "validation" / "data"


def load_table(name: str, key: str = "parameter", data_dir: Path = DATA_DIR) -> dict:
    """Read a benchmark CSV into {key: row dict}."""
    with open(data_dir / name, newline="", encoding="utf-8") as fh:
        return {row[key]: row for row in csv.DictReader(fh)}


def _num(table: dict, name: str) -> float:
    row = table[name]
    if row.get("status") == "missing" or row["value"] == "":
        raise ValueError(f"benchmark value '{name}' is missing")
    return float(row["value"])


def _warn_unverified(*tables: dict) -> None:
    n = sum(1 for t in tables for r in t.values() if r.get("verified_against_pdf", "yes") != "yes")
    if n:
        warnings.warn(f"{n} benchmark values are not yet verified against the PDF "
                      "(validation/README.md).", stacklevel=3)


@dataclass
class Benchmark:
    case: Case                 # experiment geometry and materials; flow/heat set per point
    N: int
    tc_x: np.ndarray           # thermocouple x positions (m)
    tc_depth: float            # m below the channel floor
    A_t: float                 # planform area for q_eff (m^2)


def load_benchmark(data_dir: Path = DATA_DIR) -> Benchmark:
    geo = load_table("qu_mudawar_geometry.csv", data_dir=data_dir)
    cond = load_table("qu_mudawar_conditions.csv", data_dir=data_dir)
    sens = load_table("qu_mudawar_sensors.csv", key="sensor", data_dir=data_dir)
    _warn_unverified(geo, cond, sens)

    N = int(_num(geo, "n_channels"))
    tc_depth = _num(geo, "tc_depth_below_channel_bottom")
    g = Geometry(
        W=_num(geo, "heat_sink_top_width"),
        L=_num(geo, "channel_length_L"),
        H=_num(geo, "channel_depth_Hch"),
        w_c=_num(geo, "channel_width_Wch"),
        w_f=_num(geo, "wall_thickness"),
        t_b=tc_depth,              # base layer = copper between channels and TC plane
        t_ax=_num(geo, "bottom_to_channel_bottom_Hw2"),  # copper slab for axial conduction (A14)
    )
    case = Case(
        geometry=g,
        operating=Operating(Q=0.0, T_in=_num(cond, "inlet_temperature") + 273.15,
                            V_dot=0.0, P_in=2.0e5),                       # B4
        materials=Materials(k_s=_num(geo, "solid_conductivity"), R_tim_jc=0.0),
        limits=Limits(T_dev_max=1e9, dP_max=1e9, Re_max=1e9),             # no limits
        losses=Losses(K_c=1.0, K_e=1.0, eta_pump=1.0),                    # B3
        dead_state=DeadState(),
    )
    tc_x = np.array([float(sens[f"TC{i}"]["x_from_inlet_m"]) for i in range(1, 5)])
    return Benchmark(case=case, N=N, tc_x=tc_x, tc_depth=tc_depth,
                     A_t=_num(cond, "planform_area_At"))


def flow_from_reynolds(bm: Benchmark, Re: float, T_in: Optional[float] = None) -> float:
    """Inlet volumetric flow (m^3/s) for a channel Reynolds number (assumption B1)."""
    g, op = bm.case.geometry, bm.case.operating
    T = op.T_in if T_in is None else T_in
    fp = props(T, op.P_in, op.fluid)
    D_h = 2.0 * g.w_c * g.H / (g.w_c + g.H)
    m_dot = Re * fp.mu * bm.N * g.w_c * g.H / D_h
    return m_dot / fp.rho


@dataclass
class Prediction:
    q_eff_W_cm2: float
    Re: float                  # requested Re (inlet properties)
    Re_model: float            # Re at mean-fluid properties, as used in the model
    V_ml_min: float
    dP_Pa: float               # plenum-to-plenum (friction + K losses)
    dP_friction_Pa: float
    dT_water_K: float          # T_out - T_in
    T_tc_C: np.ndarray         # TC1..TC4
    L_th_over_L: float


def predict(bm: Benchmark, q_eff_W_cm2: float, Re: float, T_in_C: Optional[float] = None,
            include_minor: bool = True, nusselt_model: Optional[str] = None,
            friction_model: Optional[str] = None, axial_conduction: Optional[bool] = None,
            viscosity_correction: Optional[bool] = None, n_x: int = 61) -> Prediction:
    """Predict the measured quantities at one test condition.

    Model choices default to bm.case.models; pass names to override (see
    correlations.NUSSELT_MODELS / FRICTION_MODELS).
    """
    T_in = bm.case.operating.T_in if T_in_C is None else T_in_C + 273.15
    V = flow_from_reynolds(bm, Re, T_in)
    Q = q_eff_W_cm2 * 1e4 * bm.A_t
    op = replace(bm.case.operating, Q=Q, V_dot=V, T_in=T_in)
    r = evaluate(replace(bm.case, operating=op), N_override=bm.N,
                 include_minor=include_minor, nusselt_model=nusselt_model,
                 friction_model=friction_model, axial_conduction=axial_conduction,
                 viscosity_correction=viscosity_correction, n_x=n_x)
    g = bm.case.geometry
    q_flux = Q / (g.W * g.L)
    T_tc = temperature_below_channels(r.th, bm.tc_x, bm.tc_depth, q_flux,
                                      bm.case.materials.k_s) - 273.15
    return Prediction(q_eff_W_cm2, Re, r.hyd.Re, V * 6e7, r.hyd.dP_total, r.hyd.dP_friction,
                      r.th.T_out - T_in, T_tc, r.entry.L_th_ratio)


def _rows(name: str, data_dir: Path) -> list:
    with open(data_dir / name, newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if any(v.strip() for v in r.values() if v)]


def compare(data_dir: Path = DATA_DIR, statuses=("digitized", "measured"), **kw) -> dict:
    """Compare digitized data with predictions. Returns rows and MAPE.

    dP: qu_mudawar_dP.csv (dP_Pa column). Thermal: qu_mudawar_thermal.csv rows
    with quantity TC1..TC4 or water_temperature_rise. Values with unit
    "K_above_inlet" are rises above the inlet water temperature (Fig. 5, 6);
    values in "degC" are absolute. Thermocouple errors are percentages of the
    rise above the inlet. Only rows whose status is in `statuses` are used.
    Predictions are cached per (q, Re), so each condition is solved once.
    """
    bm = load_benchmark(data_dir)
    T_in_C = bm.case.operating.T_in - 273.15
    cache = {}

    def pred(q, Re):
        key = (q, round(Re, 3))
        if key not in cache:
            cache[key] = predict(bm, q, Re, **kw)
        return cache[key]

    out = {"dP": [], "thermal": []}
    for row in _rows("qu_mudawar_dP.csv", data_dir):
        if row["status"] not in statuses:
            continue
        p = pred(float(row["q_eff_W_per_cm2"]), float(row["Re"]))
        meas = float(row["dP_Pa"])
        out["dP"].append({"Re": p.Re, "q_eff": p.q_eff_W_cm2, "measured": meas,
                          "predicted": p.dP_Pa, "error": (p.dP_Pa - meas) / meas})
    for row in _rows("qu_mudawar_thermal.csv", data_dir):
        if row["status"] not in statuses:
            continue
        p = pred(float(row["q_eff_W_per_cm2"]), float(row["Re"]))
        q, meas, unit = row["quantity"], float(row["value"]), row["unit"]
        if q.startswith("TC"):
            T_pred = float(p.T_tc_C[int(q[2:]) - 1])
            pred_rise = T_pred - T_in_C
            meas_rise = meas if unit == "K_above_inlet" else meas - T_in_C
            pred_v = pred_rise if unit == "K_above_inlet" else T_pred
            err = (pred_rise - meas_rise) / meas_rise
        else:
            pred_v = p.dT_water_K
            err = (pred_v - meas) / meas
        out["thermal"].append({"Re": p.Re, "q_eff": p.q_eff_W_cm2, "quantity": q,
                               "measured": meas, "predicted": pred_v, "error": err})
    for k in ("dP", "thermal"):
        errs = [abs(r["error"]) for r in out[k]]
        out[f"MAPE_{k}"] = float(np.mean(errs)) if errs else None
    tc = [abs(r["error"]) for r in out["thermal"] if r["quantity"].startswith("TC")]
    out["MAPE_TC"] = float(np.mean(tc)) if tc else None
    return out
