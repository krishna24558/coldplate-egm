"""Entropy generation, lost work and exergy.  (Week 3: you write this.)

Control volume = cold plate; heat Q enters at the mean base temperature T_s.

    S_gen_cp  = m_dot (s_out - s_in) - Q / T_s          (exact, must be >= 0)
    S_gen_dT ~= Q (1/T_f_mean - 1/T_s)                    (heat transfer)
    S_gen_dP ~= V_dot dP / T_f_mean                       (friction)
    Be        = S_gen_dT / S_gen_cp
    X_lost    = T0 S_gen_cp + (1 - eta_pump) W_pump       (Gouy-Stodola + pump)
    psi       = (h - h0) - T0 (s - s0)
    X_out     = m_dot (psi_out - psi_in)                   (value of outlet water)

Checks: S_gen_dT + S_gen_dP within a few percent of S_gen_cp;
T0 * S_gen_cp equals the exergy destroyed from an independent exergy balance.
"""


def entropy_generation(thermal_result, hydraulic_result, op):
    """Return a dict with S_gen_cp, S_gen_dT, S_gen_dP and Be."""
    raise NotImplementedError


def lost_work(S_gen_cp: float, W_pump: float, eta_pump: float, T0: float) -> float:
    raise NotImplementedError


def flow_exergy(T: float, P: float, T0: float, P0: float, fluid: str = "Water") -> float:
    raise NotImplementedError
