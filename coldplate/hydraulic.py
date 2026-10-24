"""Pressure drop and pump work.  (Week 2: you write this.)

    u      = V_dot / (N w_c H)
    dP_fr  = 2 (fRe) mu u L / D_h^2
    dP     = dP_fr + (K_c + K_e) rho u^2 / 2
    W_pump = dP V_dot / eta_pump
"""


def pressure_drop(geom, op, losses):
    """Return a dict with u, Re, dP_friction, dP_minor and dP_total."""
    raise NotImplementedError


def pump_power(dP: float, V_dot: float, eta_pump: float) -> float:
    raise NotImplementedError
