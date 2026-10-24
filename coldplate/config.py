"""Baseline inputs for the cold plate problem.

All values are SI units. Every number here is a starting assumption: confirm
it from a datasheet, standard or paper and cite the source in the report.
"""

from dataclasses import dataclass


@dataclass
class Geometry:
    """Microchannel cold plate geometry (m)."""

    W: float = 0.030      # plate width across the channels (heated width)
    L: float = 0.030      # channel length in the flow direction (heated length)
    H: float = 3.0e-3     # fin / channel height (fixed in the optimization)
    w_c: float = 0.5e-3   # channel width (design variable, 0.1-1.0 mm)
    w_f: float = 0.3e-3   # fin thickness (design variable, 0.1-0.5 mm)
    t_b: float = 1.0e-3   # base thickness below the channels


@dataclass
class Operating:
    """Heat load, coolant and limits."""

    Q: float = 1000.0          # heat load (W)
    T_in: float = 303.15       # coolant inlet temperature (K), 30 C
    V_dot: float = 1.0 / 60000 # volumetric flow (m^3/s), 1.0 L/min
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
    K_c: float = 0.5           # contraction loss coefficient (assumed)
    K_e: float = 1.0           # expansion loss coefficient (assumed)
    eta_pump: float = 0.5      # pump efficiency (sensitivity 0.3-0.7)


@dataclass
class DeadState:
    T0: float = 298.15         # dead-state temperature (K), 25 C
    P0: float = 101325.0       # dead-state pressure (Pa)
