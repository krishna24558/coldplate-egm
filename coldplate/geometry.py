"""Derived geometry of a straight-fin microchannel cold plate."""

from dataclasses import dataclass

from .config import Geometry


@dataclass
class DerivedGeometry:
    N: int          # number of channels (-)
    D_h: float      # hydraulic diameter (m)
    alpha: float    # aspect ratio, short side / long side (-), between 0 and 1
    A_c: float      # flow area of one channel (m^2)
    A_flow: float   # total flow area (m^2)
    A_base: float   # heated footprint W x L (m^2)


def derive(g: Geometry) -> DerivedGeometry:
    """Compute channel count, hydraulic diameter and areas.

    N is rounded down to a whole number of channels that fits in W.
    alpha is always defined as short side / long side so the rectangular-duct
    correlations (valid for 0 < alpha <= 1) can be applied.
    """
    N = int(g.W // (g.w_c + g.w_f))
    if N < 1:
        raise ValueError("Channel width plus fin thickness exceeds the plate width.")
    D_h = 2.0 * g.w_c * g.H / (g.w_c + g.H)
    alpha = min(g.w_c, g.H) / max(g.w_c, g.H)
    A_c = g.w_c * g.H
    return DerivedGeometry(
        N=N, D_h=D_h, alpha=alpha, A_c=A_c, A_flow=N * A_c, A_base=g.W * g.L
    )
