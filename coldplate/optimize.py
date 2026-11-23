"""Design studies (proposal Studies 1-3).

Objectives (minimized, subject to the same constraints):
    "lost_work"          X_lost = T0 S_gen_L (CV-L, the proposal's objective)
    "thermal_resistance" R_th = (T_dev - T_in) / Q (the proposal's comparison)
    "hydraulic_power"    W_hyd = V dP (optional extra reference)

Constraints: T_dev <= T_dev_max, dP <= dP_max, Re <= Re_max, w_c >= w_c_min,
w_f >= w_f_min, plus variable bounds.

Method (proposal): coarse grid sweep, then SciPy SLSQP from the best feasible
grid point. SLSQP uses a fractional channel count so the objective is smooth;
the final design is re-evaluated with a whole number of channels and both are
returned.
"""

from dataclasses import dataclass, replace
from itertools import product
from typing import Callable, Optional, Sequence

import numpy as np
from scipy.optimize import brentq, minimize, minimize_scalar

from .config import Case, lpm
from .model import Result, evaluate
from .properties import props

OBJECTIVES: dict = {
    "lost_work": lambda r: r.sl.X_lost,
    "thermal_resistance": lambda r: r.R_th,
    "hydraulic_power": lambda r: r.hyd.W_hyd,
}


def with_design(case: Case, w_c: Optional[float] = None, w_f: Optional[float] = None,
                V_dot: Optional[float] = None, T_in: Optional[float] = None) -> Case:
    """Copy of `case` with some design variables replaced (SI units)."""
    g, op = case.geometry, case.operating
    g = replace(g, w_c=g.w_c if w_c is None else w_c, w_f=g.w_f if w_f is None else w_f)
    op = replace(op, V_dot=op.V_dot if V_dot is None else V_dot,
                 T_in=op.T_in if T_in is None else T_in)
    return replace(case, geometry=g, operating=op)


def safe_evaluate(case: Case, **kw) -> Optional[Result]:
    """evaluate(), returning None when the design cannot be evaluated."""
    try:
        return evaluate(case, **kw)
    except ValueError:
        return None


# ---------------------------------------------------------------- Study 1

def flow_sweep(case: Case, V_lpm: Sequence[float], **kw) -> list:
    """Evaluate the reference geometry over a list of flows (L/min)."""
    return [safe_evaluate(with_design(case, V_dot=lpm(v)), **kw) for v in V_lpm]


@dataclass
class FlowOptimum:
    V_dot: float                 # numerical optimum (m^3/s)
    result: Result
    B: float                     # W m^3/s, coefficient of 1/V_dot
    C: float                     # W s^2/m^6, coefficient of V_dot^2
    V_dot_analytical: float      # (B / 2C)^(1/3)
    warm_to_pump_ratio: float    # X_warm / X_pump at the numerical optimum (theory ~2)


def optimum_flow(case: Case, V_lpm_bounds=(0.3, 20.0), **kw) -> FlowOptimum:
    """Lost-work-minimizing flow at fixed geometry, with the analytical check.

    B = T0 Q^2 / (2 rho cp T_in^2) and C = X_pump / V_dot^2 evaluated at the
    numerical optimum (laminar friction makes X_pump ~ C V_dot^2).
    """
    def f(v):
        r = safe_evaluate(with_design(case, V_dot=lpm(v)), **kw)
        return np.inf if r is None else r.sl.X_lost

    res = minimize_scalar(f, bounds=V_lpm_bounds, method="bounded",
                          options={"xatol": 1e-3})
    r = evaluate(with_design(case, V_dot=lpm(res.x)), **kw)
    op, ds = case.operating, case.dead_state
    fp = props(op.T_in, op.P_in, op.fluid)
    B = ds.T0 * op.Q**2 / (2.0 * fp.rho * fp.cp * op.T_in**2)
    V = r.case.operating.V_dot
    C = r.sl.X_pump / V**2
    return FlowOptimum(V_dot=V, result=r, B=B, C=C,
                       V_dot_analytical=(B / (2.0 * C)) ** (1.0 / 3.0),
                       warm_to_pump_ratio=r.sl.X_warm / r.sl.X_pump)


# ---------------------------------------------------------------- Study 2

@dataclass
class GridPoint:
    w_c: float
    w_f: float
    V_dot: float
    result: Optional[Result]


def grid_sweep(case: Case, w_c: Sequence[float], w_f: Sequence[float],
               V_lpm: Sequence[float], n_x: int = 11) -> list:
    """Evaluate every combination (w_c, w_f in m; V in L/min)."""
    out = []
    for a, b, v in product(w_c, w_f, V_lpm):
        r = safe_evaluate(with_design(case, w_c=a, w_f=b, V_dot=lpm(v)), n_x=n_x)
        out.append(GridPoint(a, b, lpm(v), r))
    return out


def best_feasible(points: Sequence[GridPoint], objective: str) -> Optional[GridPoint]:
    obj = OBJECTIVES[objective]
    ok = [p for p in points if p.result is not None and p.result.feasible]
    return min(ok, key=lambda p: obj(p.result)) if ok else None


@dataclass
class DesignOptimum:
    objective: str
    w_c: float
    w_f: float
    V_dot: float
    result_fractional: Result     # optimizer result (fractional N)
    result: Result                # re-evaluated with whole channels
    success: bool
    message: str


def snap_to_bounds(w: float, lo: float, hi: float, tol: float = 1e-9) -> float:
    """Return lo or hi if w is within tol of it (all in m), else w unchanged."""
    if abs(w - lo) <= tol:
        return lo
    if abs(w - hi) <= tol:
        return hi
    return w


def optimize_design(case: Case, objective: str, x0, bounds=None,
                    n_x: int = 21) -> DesignOptimum:
    """SLSQP over (w_c, w_f, V_dot) starting from x0 = (w_c [m], w_f [m], V_dot [m^3/s]).

    Variables are scaled to mm and L/min internally.
    """
    if objective not in OBJECTIVES:
        raise ValueError(f"objective must be one of {list(OBJECTIVES)}")
    obj = OBJECTIVES[objective]
    lim = case.limits
    if bounds is None:
        bounds = [(max(0.1, lim.w_c_min * 1e3), 1.0),
                  (max(0.1, lim.w_f_min * 1e3), 0.5), (0.3, 20.0)]
    cache: dict = {}

    def run(z) -> Optional[Result]:
        key = tuple(np.round(z, 12))
        if key not in cache:
            cache[key] = safe_evaluate(
                with_design(case, w_c=z[0] * 1e-3, w_f=z[1] * 1e-3, V_dot=lpm(z[2])),
                integer_channels=False, n_x=n_x)
        return cache[key]

    def scale(name):
        return {"lost_work": 1.0, "thermal_resistance": 100.0, "hydraulic_power": 1.0}[name]

    def f(z):
        r = run(z)
        return 1e6 if r is None else obj(r) * scale(objective)

    def margin(name, s):
        def g(z):
            r = run(z)
            return -1.0 if r is None else r.margins[name] * s
        return g

    cons = [{"type": "ineq", "fun": margin("T_dev", 1.0)},
            {"type": "ineq", "fun": margin("dP", 1e-3)},
            {"type": "ineq", "fun": margin("Re", 1e-2)}]
    z0 = np.array([x0[0] * 1e3, x0[1] * 1e3, x0[2] * 60000.0])
    res = minimize(f, z0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 200, "ftol": 1e-9})
    z = res.x
    r_frac = run(z)
    # Whole channels change dP and h slightly; re-tune the flow alone (smooth in V)
    # so the reported design satisfies the constraints with integer N.
    # SLSQP can return a width at its bound as e.g. 0.1000000000041 mm, which drops
    # N = floor(W / (w_c + w_f)) from 150 to 149 (report section 6.7). Snap widths
    # within 1e-9 m of a bound onto the bound before counting whole channels.
    w_c = snap_to_bounds(z[0] * 1e-3, bounds[0][0] * 1e-3, bounds[0][1] * 1e-3)
    w_f = snap_to_bounds(z[1] * 1e-3, bounds[1][0] * 1e-3, bounds[1][1] * 1e-3)
    V_int = _polish_flow(case, objective, w_c, w_f, z[2], bounds[2])
    r_int = evaluate(with_design(case, w_c=w_c, w_f=w_f, V_dot=lpm(V_int)), n_x=41)
    return DesignOptimum(objective, w_c, w_f, lpm(V_int), r_frac, r_int,
                         bool(res.success), str(res.message))


def _polish_flow(case: Case, objective: str, w_c: float, w_f: float,
                 V0_lpm: float, V_bounds) -> float:
    """SLSQP on flow only, whole channels. Returns the flow in L/min."""
    obj = OBJECTIVES[objective]
    cache: dict = {}

    def run(v):
        key = round(float(v), 12)
        if key not in cache:
            cache[key] = safe_evaluate(with_design(case, w_c=w_c, w_f=w_f, V_dot=lpm(key)),
                                       n_x=21)
        return cache[key]

    s = {"lost_work": 1.0, "thermal_resistance": 100.0, "hydraulic_power": 1.0}[objective]
    cons = [{"type": "ineq", "fun": (lambda v, n=n, k=k: -1.0 if run(v[0]) is None
                                     else run(v[0]).margins[n] * k)}
            for n, k in (("T_dev", 1.0), ("dP", 1e-3), ("Re", 1e-2))]
    res = minimize(lambda v: 1e6 if run(v[0]) is None else obj(run(v[0])) * s,
                   [V0_lpm], method="SLSQP", bounds=[V_bounds], constraints=cons,
                   options={"maxiter": 100, "ftol": 1e-10})
    V = float(np.clip(res.x[0], *V_bounds))
    r = run(V)
    # SLSQP can stop a hair outside the T_dev limit. T_dev falls monotonically
    # with flow, so solve T_dev margin = 0 directly if more flow is allowed.
    if r is not None and r.margins["T_dev"] < 0:
        hi = V_bounds[1]
        r_hi = run(hi)
        if r_hi is not None and r_hi.margins["T_dev"] > 0:
            V = brentq(lambda v: run(v).margins["T_dev"] - 1e-4, V, hi, xtol=1e-6)
    return V


def compare_designs(case: Case, w_c_grid, w_f_grid, V_grid,
                    objectives=("lost_work", "thermal_resistance")) -> dict:
    """Grid sweep once, then refine each objective from its best grid point."""
    pts = grid_sweep(case, w_c_grid, w_f_grid, V_grid)
    out = {}
    for name in objectives:
        p = best_feasible(pts, name)
        if p is None:
            out[name] = None
            continue
        out[name] = optimize_design(case, name, (p.w_c, p.w_f, p.V_dot))
    return out


# ---------------------------------------------------------------- Study 3

def inlet_temperature_sweep(case: Case, T_in_C: Sequence[float], design_fn: Callable) -> list:
    """For each inlet temperature, call design_fn(case_at_T) -> Result or None."""
    return [(t, design_fn(with_design(case, T_in=t + 273.15))) for t in T_in_C]
