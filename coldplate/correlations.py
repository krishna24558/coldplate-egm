"""Laminar heat transfer and friction correlations for rectangular ducts.

Source: R. K. Shah and A. L. London, Laminar Flow Forced Convection in Ducts
(1978). Fully developed flow, alpha = short side / long side, 0 < alpha <= 1.

TODO before relying on these: check every coefficient against the original
source (not a secondary paper) and note the page/equation number here.
"""


def nu_fd_H1(alpha: float) -> float:
    """Fully developed Nusselt number, H1 boundary condition (axially constant
    heat flux, peripherally constant wall temperature), all four walls heated.

    Tends to 8.235 for parallel plates (alpha -> 0).
    """
    a = alpha
    return 8.235 * (
        1 - 2.0421 * a + 3.0853 * a**2 - 2.4765 * a**3 + 1.0578 * a**4 - 0.1861 * a**5
    )


def fRe_fd(alpha: float) -> float:
    """Fully developed Fanning friction factor times Reynolds number.

    Tends to 24 for parallel plates (alpha -> 0); about 14.23 for a square duct.
    """
    a = alpha
    return 24.0 * (
        1 - 1.3553 * a + 1.9467 * a**2 - 1.7012 * a**3 + 0.9564 * a**4 - 0.2537 * a**5
    )


def reynolds(rho: float, u: float, D_h: float, mu: float) -> float:
    return rho * u * D_h / mu


# TODO (optional upgrade): developing-flow Nusselt number and apparent friction
# factor, e.g. from Lee & Garimella or Shah & London, for short channels.
