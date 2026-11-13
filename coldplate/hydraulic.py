"""Pressure drop, hydraulic power and pump electricity estimate.

    u      = V_dot / A_flow                      (V_dot at mean-fluid density)
    Re     = rho u D_h / mu
    dP_f   = 2 (fRe) mu u L / D_h^2              fRe fully developed, or apparent
                                                 (length-mean, developing) per Models.friction
    dP_m   = (K_c + K_e) rho u^2 / 2             minor losses (A8, K assumed)
    W_hyd  = V_dot dP                            hydraulic power
    W_elec = V_dot dP / eta_pump                 pump electricity estimate (A9)

Laminar flow only. With a developing friction model the apparent f*Re already
includes the entrance excess pressure drop (momentum change and extra wall shear);
K_c and K_e then represent only the plenum contraction / expansion.
"""

from dataclasses import dataclass

from .config import Geometry, Losses
from .correlations import apparent_fRe, reynolds
from .geometry import DerivedGeometry
from .properties import FluidProps


@dataclass
class HydraulicResult:
    V_dot: float        # volumetric flow at mean fluid density (m^3/s)
    u: float            # mean channel velocity (m/s)
    Re: float           # channel Reynolds number (-)
    fRe: float          # Fanning f x Re (-), apparent (length-mean) for developing models
    dP_friction: float  # channel friction pressure drop (Pa)
    dP_minor: float     # entrance + exit losses (Pa)
    dP_total: float     # dP_friction + dP_minor (Pa)
    W_hyd: float        # hydraulic power V dP (W)
    W_elec: float       # pump electricity estimate V dP / eta (W)


def pressure_drop(
    g: Geometry,
    d: DerivedGeometry,
    fp: FluidProps,
    m_dot: float,
    losses: Losses,
    include_minor: bool = True,
    friction_model: str = "fd",
    mu_friction: float = None,
) -> HydraulicResult:
    """Pressure drop through the channel array for mass flow m_dot (kg/s).

    fp: properties at the mean fluid temperature. mu_friction, if given, replaces
    fp.mu in the friction term (length-mean local viscosity with the wall
    correction, from thermal.solve_thermal with viscosity_correction).
    """
    V_dot = m_dot / fp.rho
    u = V_dot / d.A_flow
    Re = reynolds(fp.rho, u, d.D_h, fp.mu)
    fRe = apparent_fRe(friction_model, g.L, Re, g.w_c, g.H)
    mu_f = fp.mu if mu_friction is None else mu_friction  # length-mean incl. wall factor (A10)
    dP_f = 2.0 * fRe * mu_f * u * g.L / d.D_h**2
    dP_m = (losses.K_c + losses.K_e) * fp.rho * u**2 / 2.0 if include_minor else 0.0
    dP = dP_f + dP_m
    W_hyd = V_dot * dP
    return HydraulicResult(
        V_dot=V_dot, u=u, Re=Re, fRe=fRe, dP_friction=dP_f, dP_minor=dP_m,
        dP_total=dP, W_hyd=W_hyd, W_elec=pump_power(dP, V_dot, losses.eta_pump),
    )


def pump_power(dP: float, V_dot: float, eta_pump: float) -> float:
    """Electrical pump power estimate (W)."""
    if not 0.0 < eta_pump <= 1.0:
        raise ValueError("eta_pump must be in (0, 1].")
    return dP * V_dot / eta_pump
