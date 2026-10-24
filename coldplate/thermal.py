"""Thermal resistance network and device temperature.  (Week 2: you write this.)

Chain: device -> R_tim_jc -> base conduction -> fin-array convection ->
coolant temperature rise (caloric resistance). Hottest point is at the outlet.

    m      = sqrt(2 h / (k_s w_f))
    eta_f  = tanh(m H) / (m H)
    A_eff  = N L (w_c + 2 eta_f H)
    R_base = t_b / (k_s W L)
    R_conv = 1 / (h A_eff)
    R_cal  = 1 / (m_dot cp)
    T_dev  = T_in + Q (R_cal + R_conv + R_base + R_tim_jc)
"""


def fin_efficiency(h: float, k_s: float, w_f: float, H: float) -> float:
    """Straight fin with an adiabatic tip."""
    raise NotImplementedError


def effective_area(N: int, L: float, w_c: float, H: float, eta_f: float) -> float:
    raise NotImplementedError


def solve_thermal(geom, op, mat):
    """Return a dict with h, eta_f, R_base, R_conv, R_cal, T_out, T_s (mean base
    temperature) and T_dev.

    Iterate: guess T_out, evaluate properties at the mean fluid temperature,
    update T_out from the energy balance, repeat until it changes < 1e-4 K.
    """
    raise NotImplementedError
