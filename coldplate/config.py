"""Baseline inputs for the cold plate problem.

All values are SI units. Every number here is a starting assumption: confirm
it from a datasheet, standard or paper and cite the source in the report.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Geometry:
    """Microchannel cold plate geometry (m)."""

    W: float = 0.030      # plate width across the channels (heated width)
    L: float = 0.030      # channel length in the flow direction (heated length)
    H: float = 3.0e-3     # fin / channel height (fixed in the optimization)
    w_c: float = 0.2e-3   # channel width (design variable, 0.1-1.0 mm); reference 0.2 mm
    w_f: float = 0.2e-3   # fin thickness (design variable, 0.1-0.5 mm); reference 0.2 mm
    t_b: float = 1.0e-3   # base thickness below the channels
    t_ax: Optional[float] = None  # base thickness for axial conduction (A14); None -> t_b


@dataclass
class Operating:
    """Heat load, coolant and limits."""

    Q: float = 1000.0          # heat load (W)
    T_in: float = 303.15       # coolant inlet temperature (K), 30 C
    V_dot: float = 2.0 / 60000 # volumetric flow (m^3/s), 2.0 L/min (reference)
    P_in: float = 2.0e5        # coolant inlet pressure (Pa)
    fluid: str = "Water"       # CoolProp fluid name


@dataclass
class Materials:
    k_s: float = 390.0         # copper conductivity (W/m-K)
    R_tim_jc: float = 0.02     # junction-to-plate + TIM resistance (K/W)


@dataclass
class Limits:
    T_dev_max: float = 363.15  # device temperature limit (K), 90 C
    dP_max: float = 50.0e3     # pressure-drop limit (Pa)
    Re_max: float = 2000.0     # laminar limit
    w_c_min: float = 0.1e-3    # manufacturing limits (m)
    w_f_min: float = 0.1e-3


@dataclass
class Losses:
    K_c: float = 0.5           # contraction loss coefficient (assumed, unsourced; A8)
    K_e: float = 1.0           # expansion loss coefficient (assumed, unsourced; A8)
    eta_pump: float = 0.5      # pump efficiency (sensitivity 0.3-0.7)
    pump_inside_cv: bool = True  # D7: True -> W_pump = V dP / eta in the CV-L entropy


@dataclass
class DeadState:
    T0: float = 298.15         # dead-state temperature (K), 25 C
    P0: float = 101325.0       # dead-state pressure (Pa)


@dataclass
class Models:
    """Correlation choices (keys of correlations.NUSSELT_MODELS / FRICTION_MODELS).

    Defaults are the combination selected by the Qu & Mudawar comparison on
    2026-11-08 (decision D4, validation/README.md): thermocouple MAPE 4.6 %,
    pressure-drop MAPE 9.7 %. Models("fd_H1", "fd", False, False) reproduces the
    fully developed model of the proposal (thermocouple MAPE 49 %).
    """

    nusselt: str = "MY_3"      # fd_H1, fd_H1_3, LG, LG_3, MY, MY_3
    friction: str = "MY"       # fd, MY, hagenbach
    axial_conduction: bool = True   # base axial conduction (thermal.py); off = 1D per station
    # Local bulk viscosity along x plus wall-viscosity correction for laminar liquids
    # (Kays & Crawford): f/f_cp = (mu_w/mu_b)^0.58 heating, Nu/Nu_cp = (mu_b/mu_w)^0.14 (A10)
    viscosity_correction: bool = True


@dataclass
class Case:
    """Everything needed to evaluate one design (the 1 kW application case by default)."""

    geometry: Geometry = field(default_factory=Geometry)
    operating: Operating = field(default_factory=Operating)
    materials: Materials = field(default_factory=Materials)
    limits: Limits = field(default_factory=Limits)
    losses: Losses = field(default_factory=Losses)
    dead_state: DeadState = field(default_factory=DeadState)
    models: Models = field(default_factory=Models)


def lpm(V_lpm: float) -> float:
    """L/min -> m^3/s."""
    return V_lpm / 60000.0


def to_lpm(V_dot: float) -> float:
    """m^3/s -> L/min."""
    return V_dot * 60000.0
