"""Thermal network along the channel: local convection, base conduction, coolant warming.

Heat path: device -> R_tim -> base conduction -> fin-array convection -> coolant.
Uniform heat flux q'' = Q / (W L) enters the base (A2). With a developing-flow
Nusselt model the convection coefficient varies along the channel, so the
network is solved station by station (x from the inlet, 0..L):

    Nu_x            = correlations.local_nusselt(model, x, Re, Pr, w_c, H)
    h(x)            = Nu_x k / D_h
    eta_f(x)        = tanh(m H)/(m H),  m = sqrt(2 h / (k_s w_f))   (adiabatic tip, A6)
    G'(x)           = h N (w_c + 2 eta_f H)           convective conductance per length (W/m-K)
    q'              = Q / L                            heat input per length

Without axial conduction (default, 1D per station, A3):
    T_cf(x) = T_f(x) + q' / G'(x)                     channel floor / fin base
    h_f(x)  = h_in + Q x / (m_dot L)                  -> T_f(x) from CoolProp
With axial conduction in the base (Models.axial_conduction, A14):
    k_s A_ax T_cf'' - G'(x) (T_cf - T_f) + q' = 0,    adiabatic ends,
    m_dot dh_f/dx = G'(x) (T_cf - T_f),               A_ax = W t_ax + N w_f H
With Models.viscosity_correction (A10), repeated 4 times:
    Nu_x    = Nu_x,cp (mu_b(T_f) / mu_w(T_cf))^0.14
    mu_fric = mu_b (mu_w / mu_b)^0.58 (heating), length-mean -> hydraulic.pressure_drop
Both:
    T_b(x)  = T_cf(x) + q'' t_b / k_s                 base surface where heat enters (CV-C boundary)
    T_dev   = max T_b + Q R_tim                       hottest device point

Reported lumped values: Nu, h, eta_f are length means; R_conv = (mean T_cf - mean
T_f) / Q; R_base = t_b / (k_s W L). For a fully developed model they reduce to the
constant-h network used before.
"""

from dataclasses import dataclass, field
from math import pi

import numpy as np

from .config import Geometry, Materials
from .correlations import local_nusselt
from .geometry import DerivedGeometry
from .properties import FluidProps, temperature_from_hP, viscosity

# Property-ratio exponents for laminar liquids, Kays & Crawford, Convective Heat and
# Mass Transfer, 3rd ed. (1993), as tabulated in the `ht` library (wall_factor):
# Nu/Nu_cp = (mu_b/mu_w)^0.14 (heating and cooling); f/f_cp = (mu_w/mu_b)^0.58 heating,
# 0.50 cooling.
N_NU_WALL = 0.14
M_F_WALL_HEATING = 0.58
M_F_WALL_COOLING = 0.50


def fin_efficiency(h, k_s: float, w_f: float, H: float):
    """Straight fin with an adiabatic tip; h may be an array."""
    mH = np.sqrt(2.0 * np.asarray(h, dtype=float) / (k_s * w_f)) * H
    safe = np.where(mH < 1e-12, 1.0, mH)
    eta = np.where(mH < 1e-12, 1.0, np.tanh(safe) / safe)
    return float(eta) if eta.ndim == 0 else eta


def effective_area(N: float, L: float, w_c: float, H: float, eta_f: float) -> float:
    return N * L * (w_c + 2.0 * eta_f * H)


def stations(L: float, n_x: int) -> np.ndarray:
    """Stations clustered toward the inlet, where developing-flow h changes fastest."""
    s = np.linspace(0.0, 1.0, n_x)
    x = L * (1.0 - np.cos(0.5 * pi * s))
    x[-1] = L
    return x


@dataclass
class ThermalResult:
    Nu: float           # length-mean Nusselt number (D_h based)
    h: float            # length-mean convection coefficient (W/m^2-K)
    eta_f: float        # length-mean fin efficiency (-)
    A_eff: float        # effective convective area with mean eta_f (m^2)
    R_base: float       # K/W
    R_conv: float       # K/W, (mean T_cf - mean T_f) / Q
    R_cal: float        # K/W, 1/(m_dot cp)
    R_tim: float        # K/W
    T_in: float         # K
    T_out: float        # K, from h_out and P_out (includes viscous heating)
    T_f_mean: float     # K, mean of T_f(x)
    T_s_mean: float     # K, mean base temperature where heat enters (CV-C boundary)
    T_dev: float        # K, hottest device point
    nusselt_model: str = "fd_H1"
    axial_conduction: bool = False
    mu_fric_mean: float = float("nan")  # length-mean viscosity for friction (Pa-s), incl. wall factor
    x: np.ndarray = field(repr=False, default=None)     # stations along the channel (m)
    T_f: np.ndarray = field(repr=False, default=None)   # fluid temperature at x (K)
    T_cf: np.ndarray = field(repr=False, default=None)  # channel floor / fin base temperature (K)
    T_b: np.ndarray = field(repr=False, default=None)   # base (heat-entry) temperature (K)
    Nu_x: np.ndarray = field(repr=False, default=None)  # local Nusselt number (-)
    h_x: np.ndarray = field(repr=False, default=None)   # local h (W/m^2-K)
    q_conv: np.ndarray = field(repr=False, default=None)  # heat to fluid per length (W/m)


def _cumtrapz(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    out = np.zeros_like(y)
    out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))
    return out


def _conduction_matrix(x: np.ndarray, kA: float) -> np.ndarray:
    """Finite-volume operator for d/dx(kA dT/dx) with adiabatic ends (dense, small n)."""
    n = len(x)
    M = np.zeros((n, n))
    for i in range(n - 1):
        c = kA / (x[i + 1] - x[i])
        M[i, i] -= c
        M[i, i + 1] += c
        M[i + 1, i + 1] -= c
        M[i + 1, i] += c
    return M


def _cell_widths(x: np.ndarray) -> np.ndarray:
    mid = 0.5 * (x[1:] + x[:-1])
    edges = np.concatenate(([x[0]], mid, [x[-1]]))
    return np.diff(edges)


def _network(g, d, mat, fp, Q, m_dot, T_in, h_in, x, Nu_x, q_lin, T_of_h, axial_conduction, t_ax):
    """Solve fluid and channel-floor temperatures for a given local Nu_x."""
    h_x = Nu_x * fp.k / d.D_h
    eta_x = fin_efficiency(h_x, mat.k_s, g.w_f, g.H)
    G = h_x * d.N * (g.w_c + 2.0 * eta_x * g.H)       # W/m-K
    if not axial_conduction:
        h_f = h_in + Q * x / (m_dot * g.L)
        T_f = T_of_h(h_f)
        T_cf = T_f + q_lin / G
        q_conv = np.full_like(x, q_lin)
    else:
        t = g.t_b if t_ax is None else t_ax
        kA = mat.k_s * (g.W * t + d.N * g.w_f * g.H)
        M = _conduction_matrix(x, kA)
        dx = _cell_widths(x)
        Gd = G * dx
        n = len(x)
        # Coupled linear solve with constant cp: unknowns [T_cf, T_f].
        C = m_dot * fp.cp
        A = np.zeros((2 * n, 2 * n))
        b = np.zeros(2 * n)
        A[:n, :n] = M - np.diag(Gd)
        A[:n, n:] = np.diag(Gd)
        b[:n] = -q_lin * dx
        A[n, n] = 1.0
        b[n] = T_in
        for i in range(1, n):  # C (T_f,i - T_f,i-1) = trapz of G (T_cf - T_f)
            w = 0.5 * (x[i] - x[i - 1])
            r = n + i
            A[r, n + i] += C + w * G[i]
            A[r, n + i - 1] += -C + w * G[i - 1]
            A[r, i] += -w * G[i]
            A[r, i - 1] += -w * G[i - 1]
        sol = np.linalg.solve(A, b)
        T_cf_lin, T_f_lin = sol[:n], sol[n:]
        q_conv = G * (T_cf_lin - T_f_lin)
        # Exact energy for the fluid (CoolProp enthalpy), rescaled so the outlet gets Q.
        cum = _cumtrapz(q_conv, x)
        cum *= Q / cum[-1]
        T_f = T_of_h(h_in + cum / m_dot)
        T_cf = np.linalg.solve(M - np.diag(Gd), -q_lin * dx - Gd * T_f)
        q_conv = G * (T_cf - T_f)

    return T_f, T_cf, q_conv, G, h_x, eta_x


def solve_thermal(
    g: Geometry,
    d: DerivedGeometry,
    mat: Materials,
    fp: FluidProps,
    Q: float,
    m_dot: float,
    T_in: float,
    h_in: float,
    P_in: float,
    P_out: float,
    fluid: str = "Water",
    nusselt_model: str = "fd_H1",
    n_x: int = 41,
    Re: float = None,
    axial_conduction: bool = False,
    t_ax: float = None,
    viscosity_correction: bool = False,
) -> ThermalResult:
    """Solve the network with properties fp at the mean fluid temperature (A10).

    Re is the channel Reynolds number (needed by developing-flow models). The fluid
    pressure is taken to fall linearly from P_in to P_out.
    """
    if Re is None:
        Re = m_dot / (d.A_flow * fp.mu) * d.D_h
    x = stations(g.L, n_x)
    # Station 0 represents the cell [0, x1/2]; the cell-mean of a 1/sqrt(x) law
    # equals its value at a quarter of the cell, so evaluate h at x1/8 there.
    x_eval = x.copy()
    x_eval[0] = x[1] / 8.0
    Nu_cp = np.asarray(local_nusselt(nusselt_model, x_eval, Re, fp.Pr, g.w_c, g.H), dtype=float)
    q_lin = Q / g.L                                    # W/m
    P_x = P_in - (P_in - P_out) * x / g.L

    def T_of_h(hf):
        return np.array([temperature_from_hP(hh, pp, fluid) for hh, pp in zip(hf, P_x)])

    wall = np.ones_like(x)
    passes = 4 if viscosity_correction else 1
    for _ in range(passes):
        Nu_x = Nu_cp * wall
        T_f, T_cf, q_conv, G, h_x, eta_x = _network(
            g, d, mat, fp, Q, m_dot, T_in, h_in, x, Nu_x, q_lin, T_of_h, axial_conduction, t_ax)
        if viscosity_correction:
            mu_b = np.array([viscosity(t, p, fluid) for t, p in zip(T_f, P_x)])
            mu_w = np.array([viscosity(t, p, fluid) for t, p in zip(T_cf, P_x)])
            wall = (mu_b / mu_w) ** N_NU_WALL
    if viscosity_correction:
        m_exp = np.where(T_cf >= T_f, M_F_WALL_HEATING, M_F_WALL_COOLING)
        mu_fric = mu_b * (mu_w / mu_b) ** m_exp
    else:
        mu_fric = np.full_like(x, fp.mu)

    T_b = T_cf + Q / (g.W * g.L) * g.t_b / mat.k_s
    R_base = g.t_b / (mat.k_s * g.W * g.L)
    R_cal = 1.0 / (m_dot * fp.cp)
    mean = lambda y: float(np.trapezoid(y, x) / g.L)  # noqa: E731
    T_f_mean, T_cf_mean = mean(T_f), mean(T_cf)
    eta_mean = mean(eta_x)
    return ThermalResult(
        Nu=mean(Nu_x), h=mean(h_x), eta_f=eta_mean,
        A_eff=effective_area(d.N, g.L, g.w_c, g.H, eta_mean),
        R_base=R_base, R_conv=(T_cf_mean - T_f_mean) / Q, R_cal=R_cal, R_tim=mat.R_tim_jc,
        T_in=T_in, T_out=float(T_f[-1]), T_f_mean=T_f_mean, T_s_mean=mean(T_b),
        T_dev=float(np.max(T_b) + Q * mat.R_tim_jc),
        nusselt_model=nusselt_model, axial_conduction=axial_conduction,
        mu_fric_mean=mean(mu_fric), x=x, T_f=T_f, T_cf=T_cf, T_b=T_b, Nu_x=Nu_x, h_x=h_x, q_conv=q_conv,
    )


def temperature_below_channels(tr: ThermalResult, x_query, depth: float,
                               q_flux: float, k_s: float) -> np.ndarray:
    """Copper temperature at `depth` below the channel floor, at positions x_query.

    T = T_cf(x) + q_flux * depth / k_s (1D through-thickness conduction at the
    footprint flux, B5). Used for the Qu & Mudawar thermocouples, which sit in
    the copper below the channels.
    """
    T_cf_q = np.interp(np.asarray(x_query, dtype=float), tr.x, tr.T_cf)
    return T_cf_q + q_flux * depth / k_s
