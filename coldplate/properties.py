"""Coolant properties from CoolProp.

All inputs and outputs are SI: temperature in K, pressure in Pa.
"""

from dataclasses import dataclass

from CoolProp.CoolProp import PropsSI


@dataclass
class FluidProps:
    rho: float   # density (kg/m^3)
    mu: float    # dynamic viscosity (Pa-s)
    cp: float    # specific heat (J/kg-K)
    k: float     # thermal conductivity (W/m-K)
    Pr: float    # Prandtl number (-)
    h: float     # specific enthalpy (J/kg)
    s: float     # specific entropy (J/kg-K)


def props(T: float, P: float, fluid: str = "Water") -> FluidProps:
    """Return the coolant properties at temperature T (K) and pressure P (Pa)."""
    rho = PropsSI("D", "T", T, "P", P, fluid)
    mu = PropsSI("V", "T", T, "P", P, fluid)
    cp = PropsSI("C", "T", T, "P", P, fluid)
    k = PropsSI("L", "T", T, "P", P, fluid)
    h = PropsSI("H", "T", T, "P", P, fluid)
    s = PropsSI("S", "T", T, "P", P, fluid)
    return FluidProps(rho=rho, mu=mu, cp=cp, k=k, Pr=cp * mu / k, h=h, s=s)


def enthalpy(T: float, P: float, fluid: str = "Water") -> float:
    return PropsSI("H", "T", T, "P", P, fluid)


def entropy(T: float, P: float, fluid: str = "Water") -> float:
    return PropsSI("S", "T", T, "P", P, fluid)


def temperature_from_hP(h: float, P: float, fluid: str = "Water") -> float:
    """Temperature (K) from enthalpy and pressure; used to get the outlet state."""
    return PropsSI("T", "H", h, "P", P, fluid)
