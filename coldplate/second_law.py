"""Entropy generation, lost work and exergy.

Control volumes (docs/equation_sheet.md, Section 2):

CV-C, the cold plate alone. Heat enters at the base surface temperature T_b(x):
    S_gen_C = m_dot (s_out - s_in) - integral(q / T_b) dA          (exact boundary term)
    S_gen_C_mean = m_dot (s_out - s_in) - Q / T_s_mean             (mean-temperature approx, A1)
    approximate split: S_dT = Q (1/T_f_mean - 1/T_s_mean),  S_dP = V_dot dP / T_f_mean

CV-L, cold plate + idealized return of the coolant to T_in (objective, per the
submitted proposal). Q + W_pump is rejected to a reservoir at T_in:
    S_gen_L = Q (1/T_in - 1/T_s) + W_pump / T_in
    split:  S_warm = Q (1/T_in - 1/T_f_mean)    coolant warming   (~1/V_dot)
            S_gap  = Q (1/T_f_mean - 1/T_s)      base to coolant   (~constant)
            S_pump = W_pump / T_in               pumping           (~V_dot^2)
    W_pump = W_elec (pump inside the CV) or W_hyd (pump outside), decision D7.
    Here 1/T_s is evaluated with the exact boundary term (integral q/T_b / Q).

CV-P, package and TIM (upstream, reported separately, not cold plate loss):
    S_gen_P = Q (1/T_s - 1/T_j),  T_j = T_s + Q R_tim (mean junction approx)

Lost work: X = T0 S_gen (Gouy-Stodola). Flow exergy: psi = (h - h0) - T0 (s - s0).
"""

from dataclasses import dataclass

import numpy as np

from .properties import enthalpy, entropy


@dataclass
class SecondLawResult:
    # CV-C (cold plate)
    S_gen_C: float          # exact boundary term (W/K)
    S_gen_C_mean: float     # mean boundary temperature approximation (W/K)
    S_C_dT: float           # approximate heat-transfer part (W/K)
    S_C_dP: float           # approximate friction part (W/K)
    # CV-L (objective)
    S_gen_L: float          # W/K
    S_warm: float           # W/K
    S_gap: float            # W/K
    S_pump: float           # W/K
    Be_L: float             # (S_warm + S_gap) / S_gen_L
    X_lost: float           # T0 S_gen_L (W)
    X_warm: float           # W
    X_gap: float            # W
    X_pump: float           # W
    # CV-P (upstream, separate)
    S_gen_P: float          # W/K
    # exergy of the coolant stream
    X_out: float            # m_dot (psi_out - psi_in) (W)
    T_s_eff: float          # Q / integral(q/T_b): effective boundary temperature (K)


def boundary_entropy_flow(Q: float, x: np.ndarray, T_b: np.ndarray, L: float) -> float:
    """integral(q / T_b) dA for uniform heat flux: (Q/L) integral(dx / T_b(x))."""
    return float(Q / L * np.trapezoid(1.0 / T_b, x))


def flow_exergy(T: float, P: float, T0: float, P0: float, fluid: str = "Water") -> float:
    """psi = (h - h0) - T0 (s - s0)  (J/kg)."""
    h, s = enthalpy(T, P, fluid), entropy(T, P, fluid)
    h0, s0 = enthalpy(T0, P0, fluid), entropy(T0, P0, fluid)
    return (h - h0) - T0 * (s - s0)


def lost_work(S_gen: float, T0: float) -> float:
    return T0 * S_gen


def entropy_generation(tr, hr, Q: float, m_dot: float, T_in: float, P_in: float,
                       P_out: float, L: float, T0: float, P0: float,
                       pump_inside_cv: bool = True, fluid: str = "Water") -> SecondLawResult:
    """All second-law quantities for one evaluated design.

    tr: ThermalResult, hr: HydraulicResult.
    """
    s_in, s_out = entropy(T_in, P_in, fluid), entropy(tr.T_out, P_out, fluid)
    dS_flow = m_dot * (s_out - s_in)
    S_bnd = boundary_entropy_flow(Q, tr.x, tr.T_b, L)
    T_s_eff = Q / S_bnd

    S_gen_C = dS_flow - S_bnd
    S_gen_C_mean = dS_flow - Q / tr.T_s_mean
    S_C_dT = Q * (1.0 / tr.T_f_mean - 1.0 / tr.T_s_mean)
    S_C_dP = hr.V_dot * hr.dP_total / tr.T_f_mean

    W_pump = hr.W_elec if pump_inside_cv else hr.W_hyd
    S_warm = Q * (1.0 / T_in - 1.0 / tr.T_f_mean)
    S_gap = Q * (1.0 / tr.T_f_mean - 1.0 / T_s_eff)
    S_pump = W_pump / T_in
    S_gen_L = S_warm + S_gap + S_pump        # = Q (1/T_in - 1/T_s_eff) + W_pump/T_in

    T_j = tr.T_s_mean + Q * tr.R_tim
    S_gen_P = Q * (1.0 / tr.T_s_mean - 1.0 / T_j)

    X_out = m_dot * (flow_exergy(tr.T_out, P_out, T0, P0, fluid)
                     - flow_exergy(T_in, P_in, T0, P0, fluid))
    return SecondLawResult(
        S_gen_C=S_gen_C, S_gen_C_mean=S_gen_C_mean, S_C_dT=S_C_dT, S_C_dP=S_C_dP,
        S_gen_L=S_gen_L, S_warm=S_warm, S_gap=S_gap, S_pump=S_pump,
        Be_L=(S_warm + S_gap) / S_gen_L, X_lost=T0 * S_gen_L,
        X_warm=T0 * S_warm, X_gap=T0 * S_gap, X_pump=T0 * S_pump,
        S_gen_P=S_gen_P, X_out=X_out, T_s_eff=T_s_eff,
    )
