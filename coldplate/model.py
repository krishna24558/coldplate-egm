"""Evaluate one cold plate design: hydraulics, thermal network, second law.

The volumetric flow in Operating.V_dot is defined at inlet conditions, so
m_dot = rho(T_in, P_in) V_dot. Properties for friction and convection are
evaluated at the mean fluid temperature and mean pressure (A10), and the
outlet temperature, pressure drop and properties are iterated to convergence.
"""

from dataclasses import dataclass, field
from typing import Optional

from .config import Case
from .correlations import EntryLengths, entry_lengths
from .geometry import DerivedGeometry, derive
from .hydraulic import HydraulicResult, pressure_drop
from .properties import enthalpy, props
from .second_law import SecondLawResult, entropy_generation
from .thermal import ThermalResult, solve_thermal

P_OUT_MIN = 1.0e4  # Pa; below this the outlet state is unphysical for this model
# A design sitting exactly on a limit (optimizer output) counts as feasible.
FEAS_TOL = {"T_dev": 1e-3, "dP": 1.0, "Re": 1e-3, "w_c": 1e-12, "w_f": 1e-12}


@dataclass
class Result:
    case: Case = field(repr=False)
    geom: DerivedGeometry
    m_dot: float
    hyd: HydraulicResult
    th: ThermalResult
    sl: SecondLawResult
    entry: EntryLengths
    R_th: float                 # (T_dev - T_in) / Q  (K/W)
    margins: dict               # constraint margins, >= 0 means satisfied
    feasible: bool
    iterations: int

    def summary(self) -> dict:
        """Main numbers in report units (degC, L/min, kPa, W)."""
        op = self.case.operating
        return {
            "N": self.geom.N,
            "V_lpm": op.V_dot * 60000.0,
            "Re": self.hyd.Re,
            "T_in_C": op.T_in - 273.15,
            "T_out_C": self.th.T_out - 273.15,
            "T_dev_C": self.th.T_dev - 273.15,
            "R_th_K_per_W": self.R_th,
            "dP_kPa": self.hyd.dP_total / 1e3,
            "W_hyd_W": self.hyd.W_hyd,
            "W_elec_W": self.hyd.W_elec,
            "X_lost_W": self.sl.X_lost,
            "X_warm_W": self.sl.X_warm,
            "X_gap_W": self.sl.X_gap,
            "X_pump_W": self.sl.X_pump,
            "S_gen_C_W_per_K": self.sl.S_gen_C,
            "X_out_W": self.sl.X_out,
            "L_th_over_L": self.entry.L_th_ratio,
            "nusselt_model": self.th.nusselt_model,
            "Nu_mean": self.th.Nu,
            "feasible": self.feasible,
        }


def evaluate(
    case: Case,
    integer_channels: bool = True,
    N_override: Optional[int] = None,
    nusselt_model: Optional[str] = None,
    include_minor: bool = True,
    friction_model: Optional[str] = None,
    axial_conduction: Optional[bool] = None,
    viscosity_correction: Optional[bool] = None,
    n_x: int = 41,
    tol: float = 1e-6,
    max_iter: int = 50,
) -> Result:
    g, op, mat = case.geometry, case.operating, case.materials
    lim, los, ds = case.limits, case.losses, case.dead_state
    d = derive(g, integer=integer_channels, N_override=N_override)
    mdl = case.models
    nu_model = mdl.nusselt if nusselt_model is None else nusselt_model
    fr_model = mdl.friction if friction_model is None else friction_model
    axial = mdl.axial_conduction if axial_conduction is None else axial_conduction
    visc = mdl.viscosity_correction if viscosity_correction is None else viscosity_correction
    mu_fric = None

    fp_in = props(op.T_in, op.P_in, op.fluid)
    m_dot = fp_in.rho * op.V_dot
    h_in = enthalpy(op.T_in, op.P_in, op.fluid)
    T_out = op.T_in + op.Q / (m_dot * fp_in.cp)
    dP = 0.0

    for it in range(1, max_iter + 1):
        T_m = 0.5 * (op.T_in + T_out)
        fp = props(T_m, op.P_in - 0.5 * dP, op.fluid)
        hr = pressure_drop(g, d, fp, m_dot, los, include_minor, fr_model, mu_fric)
        P_out = op.P_in - hr.dP_total
        if P_out < P_OUT_MIN:
            raise ValueError(
                f"Outlet pressure {P_out:.0f} Pa is too low (dP = {hr.dP_total:.0f} Pa); "
                "raise P_in or reduce the flow."
            )
        tr = solve_thermal(g, d, mat, fp, op.Q, m_dot, op.T_in, h_in, op.P_in, P_out,
                           op.fluid, nu_model, n_x, Re=hr.Re, axial_conduction=axial,
                           t_ax=g.t_ax, viscosity_correction=visc)
        if visc:
            mu_fric = tr.mu_fric_mean
        converged = abs(tr.T_out - T_out) < tol and abs(hr.dP_total - dP) < max(1e-6 * hr.dP_total, 1e-9)
        T_out, dP = tr.T_out, hr.dP_total
        if converged:
            break

    sl = entropy_generation(tr, hr, op.Q, m_dot, op.T_in, op.P_in, P_out, g.L,
                            ds.T0, ds.P0, los.pump_inside_cv, op.fluid)
    el = entry_lengths(hr.Re, fp.Pr, d.D_h, g.L, g.w_c, g.H)
    margins = {
        "T_dev": lim.T_dev_max - tr.T_dev,
        "dP": lim.dP_max - hr.dP_total,
        "Re": lim.Re_max - hr.Re,
        "w_c": g.w_c - lim.w_c_min,
        "w_f": g.w_f - lim.w_f_min,
    }
    return Result(
        case=case, geom=d, m_dot=m_dot, hyd=hr, th=tr, sl=sl, entry=el,
        R_th=(tr.T_dev - op.T_in) / op.Q, margins=margins,
        feasible=all(v >= -FEAS_TOL[k] for k, v in margins.items()), iterations=it,
    )
