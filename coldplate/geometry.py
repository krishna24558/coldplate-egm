"""Derived geometry of a straight-fin microchannel cold plate."""

from dataclasses import dataclass
from typing import Optional

from .config import Geometry


@dataclass
class DerivedGeometry:
    N: float        # number of channels (-); whole number unless integer=False
    D_h: float      # hydraulic diameter (m)
    alpha: float    # aspect ratio, short side / long side (-), between 0 and 1
    A_c: float      # flow area of one channel (m^2)
    A_flow: float   # total flow area (m^2)
    A_base: float   # heated footprint W x L (m^2)


def derive(g: Geometry, integer: bool = True, N_override: Optional[int] = None) -> DerivedGeometry:
    """Compute channel count, hydraulic diameter and areas.

    N is rounded down to a whole number of channels that fits in W. With
    integer=False, N = W / (w_c + w_f) is kept fractional; this is only used to
    give the optimizer a smooth objective, and final designs are re-evaluated
    with integer N. N_override fixes N (used for the Qu & Mudawar benchmark,
    which states 21 channels).

    alpha is always short side / long side so the rectangular-duct
    correlations (valid for 0 < alpha <= 1) can be applied.
    """
    if N_override is not None:
        N = float(N_override)
    else:
        N = g.W / (g.w_c + g.w_f)
        if integer:
            N = float(int(N + 1e-9))  # tolerance: 0.030 / 0.0004 must give 75, not 74
    if N < 1:
        raise ValueError("Channel width plus fin thickness exceeds the plate width.")
    D_h = 2.0 * g.w_c * g.H / (g.w_c + g.H)
    alpha = min(g.w_c, g.H) / max(g.w_c, g.H)
    A_c = g.w_c * g.H
    if integer and N_override is None:
        N = int(N)
    return DerivedGeometry(
        N=N, D_h=D_h, alpha=alpha, A_c=A_c, A_flow=N * A_c, A_base=g.W * g.L
    )
