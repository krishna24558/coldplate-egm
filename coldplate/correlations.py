"""Laminar heat transfer and friction correlations for rectangular channels.

All Nusselt numbers and f*Re values returned here are based on the hydraulic
diameter D_h = 2 w_c H / (w_c + H), with Fanning f. Sources, equation numbers
and validity ranges are listed per function and in docs/equation_sheet.md
(Section 1b). Coefficients transcribed from the PDFs were checked numerically
against independent tabulated data; see tests/test_correlations_developing.py
and the "Transcription checks" note in docs/equation_sheet.md.

Aspect-ratio conventions differ between sources, so each function says which
one it uses:
  alpha    = short side / long side, 0 < alpha <= 1    (Shah & London fits)
  alpha_LG = H / w_c >= 1, channel height over width    (Lee & Garimella 2006)
  eps      = short side / long side                     (Muzychka & Yovanovich)

Nusselt models (keys of NUSSELT_MODELS), all for the H1-type boundary condition
(axially uniform heat input):
  fd_H1    fully developed, four walls heated                  Shah & London
  fd_H1_3  fully developed, three walls heated, one short
           wall (the lid) adiabatic                             Shah & London via Lee & Garimella Eq. 16
  LG       thermally developing, hydrodynamically developed,
           four walls                                           Lee & Garimella (2006) Eq. 12
  LG_3     LG scaled to three-sided heating by Nu_fd,3/Nu_fd,4  Lee & Garimella (2006) Eq. 15
  MY       simultaneously developing (combined entry), UWF       Muzychka & Yovanovich (2004) Eq. 45
  MY_3     MY scaled by Nu_fd,3/Nu_fd,4                         our extension of Eq. 15 (flagged)

Friction models (keys of FRICTION_MODELS), apparent (length-mean) f*Re:
  fd         fully developed                                     Shah & London
  MY         developing, Fanning f_app                           Muzychka & Yovanovich (2004) Eq. 47
  hagenbach  fd + K(inf) / (4 x+), valid for x+ > ~0.05          K(inf) fit quoted by Duan & Ma (2020)
"""

from dataclasses import dataclass
from math import pi, sqrt, tanh

import numpy as np

# --------------------------------------------------------------------------
# Fully developed values (Shah & London 1978 polynomial fits)
# --------------------------------------------------------------------------


def nu_fd_H1(alpha: float) -> float:
    """Fully developed Nu_H1, four walls heated, alpha = short/long in (0, 1].

    Shah & London (1978) polynomial; the same expression is Eq. (10) of Lee &
    Garimella (2006), written there in 1/alpha_LG. Tends to 8.235 for parallel
    plates (alpha -> 0) and 3.61 for a square duct.
    """
    a = alpha
    return 8.235 * (
        1 - 2.0421 * a + 3.0853 * a**2 - 2.4765 * a**3 + 1.0578 * a**4 - 0.1861 * a**5
    )


def nu_fd_H1_3(alpha: float) -> float:
    """Fully developed Nu_H1 with three walls heated and one SHORT wall adiabatic.

    Shah & London (1978), as quoted in Lee & Garimella (2006) Eq. (16):
    Nu = 8.235 (1 - 1.883/a + 3.767/a^2 - 5.814/a^3 + 5.361/a^4 - 2.0/a^5) with
    a = alpha_LG = H / w_c >= 1, i.e. the polynomial below in alpha = w_c / H.
    The adiabatic wall is the channel top (width w_c), as for a channel closed by
    an insulating lid, so this applies only when H >= w_c.
    Tends to 8.235 for alpha -> 0; 3.556 for a square duct.
    """
    a = alpha
    return 8.235 * (
        1 - 1.883 * a + 3.767 * a**2 - 5.814 * a**3 + 5.361 * a**4 - 2.0 * a**5
    )


def fRe_fd(alpha: float) -> float:
    """Fully developed Fanning f*Re, alpha = short/long in [0, 1].

    Shah & London (1978) polynomial. Tends to 24 for parallel plates and 14.23
    for a square duct. Agrees with the series solution (Duan & Muzychka) to about
    0.1 % (Duan & Ma 2020).
    """
    a = alpha
    return 24.0 * (
        1 - 1.3553 * a + 1.9467 * a**2 - 1.7012 * a**3 + 0.9564 * a**4 - 0.2537 * a**5
    )


def reynolds(rho: float, u: float, D_h: float, mu: float) -> float:
    return rho * u * D_h / mu


# --------------------------------------------------------------------------
# Lee & Garimella (2006): thermally developing, H1, four walls
# --------------------------------------------------------------------------
# P.-S. Lee, S. V. Garimella, "Thermally developing flow and heat transfer in
# rectangular microchannels of different aspect ratios," Int. J. Heat Mass
# Transfer 49 (2006) 3060-3067. Numerical, water, hydrodynamically fully
# developed inlet, H1 on all four walls, 1 <= alpha_LG <= 10, z* < z*_th.
# Signs lost in the PDF text extraction were fixed by checking the fit against
# (a) its own definition of z*_th (Nu = 1.05 Nu_fd there) and (b) Wibulswas's
# tabulated Nu_x (Lee, Garimella & Liu 2005, Table 2); see the tests.

LG_ALPHA_RANGE = (1.0, 10.0)


def z_th_lee_garimella(alpha_LG: float) -> float:
    """Dimensionless thermal entry length z*_th = L_th / (Re Pr D_h), Eq. (11).

    Defined as the z* where the local Nu falls to 1.05 Nu_fd.
    """
    a = alpha_LG
    return (-1.275e-6 * a**6 + 4.709e-5 * a**5 - 6.902e-4 * a**4 + 5.014e-3 * a**3
            - 1.769e-2 * a**2 + 1.845e-2 * a + 5.691e-2)


def _lg_coeffs(a: float, mean: bool = False):
    if not mean:  # Eq. (12), local
        C1 = -3.122e-3 * a**3 + 2.435e-2 * a**2 + 2.143e-1 * a + 7.325
        C2 = 6.412e-1
        C3 = 1.589e-4 * a**2 - 2.603e-3 * a + 2.444e-2
        C4 = 7.148 - 13.28 / a + 15.15 / a**2 - 5.936 / a**3
    else:  # Eq. (13), length-mean
        C1 = -2.757e-3 * a**3 + 3.274e-2 * a**2 - 7.464e-5 * a + 4.476
        C2 = 6.391e-1
        C3 = 1.604e-4 * a**2 - 2.622e-3 * a + 2.568e-2
        C4 = 7.301 - 13.11 / a + 15.19 / a**2 - 6.094 / a**3
    return C1, C2, C3, C4


def nu_lee_garimella(z_star, alpha_LG: float, mean: bool = False):
    """Raw Eq. (12) (local) or Eq. (13) (mean): Nu = 1/(C1 z*^C2 + C3) + C4.

    Valid for 1 <= alpha_LG <= 10 and z* < z*_th only; use nu_x_LG for a value
    usable along the whole channel.
    """
    C1, C2, C3, C4 = _lg_coeffs(alpha_LG, mean)
    z = np.asarray(z_star, dtype=float)
    return 1.0 / (C1 * z**C2 + C3) + C4


def nu_x_LG(z_star, w_c: float, H: float):
    """Local Nu along the channel from Lee & Garimella (2006), four walls.

    Nu_x = max(Eq. 12, Nu_fd,H1). Eq. (12) is fitted only for z* < z*_th, where it
    stays above Nu_fd; beyond z*_th the paper uses Nu_fd. Taking the maximum keeps
    Nu_x continuous (the fit gives 1.05-1.09 Nu_fd at z*_th, so the two forms
    differ by < 9 % over a short stretch). alpha_LG = H / w_c is clipped to the
    fitted range [1, 10]; Nu_fd always uses the true aspect ratio.
    """
    alpha = min(w_c, H) / max(w_c, H)
    a_LG = float(np.clip(H / w_c, *LG_ALPHA_RANGE))
    return np.maximum(nu_lee_garimella(z_star, a_LG), nu_fd_H1(alpha))


# --------------------------------------------------------------------------
# Muzychka & Yovanovich (2004): combined (simultaneously developing) entry
# --------------------------------------------------------------------------
# Y. S. Muzychka, M. M. Yovanovich, "Laminar forced convection heat transfer in
# the combined entry region of non-circular ducts," ASME J. Heat Transfer 126
# (2004) 54-61. Length scale sqrt(A). Valid 0.1 < Pr < inf, 0 < z* < inf;
# within about +/-15 % of the data for most shapes (larger deviations noted for
# rectangles). gamma = 1/10 for ducts with right-angled corners (Table 1).

MY_CONST = {  # Table 1 / Eq. 45
    "H": {"C1": 3.86, "C3": 0.501, "fPr": (0.886, 1.909)},  # uniform wall flux
    "T": {"C1": 3.24, "C3": 0.409, "fPr": (0.564, 1.664)},  # uniform wall temperature
}
MY_GAMMA = 0.1


def fRe_sqrtA_rect(eps: float) -> float:
    """Fully developed Fanning f*Re_sqrt(A) for a rectangle, eps = short/long, Eq. (21).

    fRe_sqrtA = 12 / ( sqrt(eps) (1 + eps) [1 - (192 eps / pi^5) tanh(pi / (2 eps))] )
    (first term of the series solution; 14.13 for a square).
    """
    return 12.0 / (sqrt(eps) * (1.0 + eps) * (1.0 - 192.0 * eps / pi**5 * tanh(pi / (2.0 * eps))))


def _f_pr(Pr: float, bc: str) -> float:
    """Eqs. (42)-(43): f(Pr) = c / [1 + (b Pr^(1/6))^(9/2)]^(2/9)."""
    c, b = MY_CONST[bc]["fPr"]
    return c / (1.0 + (b * Pr ** (1.0 / 6.0)) ** 4.5) ** (2.0 / 9.0)


def nu_sqrtA_muzychka(z_star_sqrtA, eps: float, Pr: float, bc: str = "H",
                      local: bool = True, combined: bool = True):
    """Nu_sqrt(A) from Eq. (45); combined=False drops the developing-velocity term.

    Nu = [ (C4 f(Pr)/sqrt(z*))^m + ( {C1 fRe/(8 sqrt(pi) eps^gamma)}^5
                                     + {C2 C3 (fRe/z*)^(1/3)}^5 )^(m/5) ]^(1/m)
    m = 2.27 + 1.65 Pr^(1/3) (Eq. 46); C2 = 1, C4 = 1 local; C2 = 3/2, C4 = 2 mean.
    z* = z / (sqrt(A) Re_sqrtA Pr).
    """
    k = MY_CONST[bc]
    C2, C4 = (1.0, 1.0) if local else (1.5, 2.0)
    fRe = fRe_sqrtA_rect(eps)
    z = np.asarray(z_star_sqrtA, dtype=float)
    nu_fd = k["C1"] * fRe / (8.0 * sqrt(pi) * eps**MY_GAMMA)
    nu_gz = C2 * k["C3"] * (fRe / z) ** (1.0 / 3.0)
    nu_th = (nu_fd**5 + nu_gz**5) ** 0.2
    if not combined:
        return nu_th
    m = 2.27 + 1.65 * Pr ** (1.0 / 3.0)
    return ((C4 * _f_pr(Pr, bc) / np.sqrt(z)) ** m + nu_th**m) ** (1.0 / m)


def nu_x_MY(x, Re, Pr, w_c: float, H: float, bc: str = "H"):
    """Local Nu (D_h based) from Muzychka & Yovanovich (2004), x from the inlet.

    Converts with sqrt(A) = sqrt(w_c H): Re_sqrtA = Re sqrt(A)/D_h,
    z* = x/(sqrt(A) Re_sqrtA Pr) = x/(Re Pr D_h) * D_h^2/A, Nu_Dh = Nu_sqrtA D_h/sqrt(A).
    """
    A = w_c * H
    D_h = 2.0 * w_c * H / (w_c + H)
    eps = min(w_c, H) / max(w_c, H)
    z_sqrtA = np.asarray(x, dtype=float) / (Re * Pr * D_h) * D_h**2 / A
    return nu_sqrtA_muzychka(z_sqrtA, eps, Pr, bc) * D_h / sqrt(A)


# --------------------------------------------------------------------------
# Model registry: local Nu_x (D_h based) along the channel
# --------------------------------------------------------------------------


def _three_side_ratio(w_c: float, H: float) -> float:
    if H < w_c:
        raise ValueError("Three-sided-heating fit assumes the adiabatic wall is the short "
                         "top wall (H >= w_c).")
    a = w_c / H
    return nu_fd_H1_3(a) / nu_fd_H1(a)


def _fd(x, Re, Pr, w_c, H):
    a = min(w_c, H) / max(w_c, H)
    return np.full_like(np.asarray(x, dtype=float), nu_fd_H1(a))


def _fd3(x, Re, Pr, w_c, H):
    return _fd(x, Re, Pr, w_c, H) * _three_side_ratio(w_c, H)


def _lg(x, Re, Pr, w_c, H):
    D_h = 2.0 * w_c * H / (w_c + H)
    return nu_x_LG(np.asarray(x, dtype=float) / (Re * Pr * D_h), w_c, H)


def _lg3(x, Re, Pr, w_c, H):
    return _lg(x, Re, Pr, w_c, H) * _three_side_ratio(w_c, H)


def _my(x, Re, Pr, w_c, H):
    return nu_x_MY(x, Re, Pr, w_c, H)


def _my3(x, Re, Pr, w_c, H):
    return _my(x, Re, Pr, w_c, H) * _three_side_ratio(w_c, H)


NUSSELT_MODELS = {
    "fd_H1": _fd, "fd_H1_3": _fd3, "LG": _lg, "LG_3": _lg3, "MY": _my, "MY_3": _my3,
}
DEVELOPING_NUSSELT = {"LG", "LG_3", "MY", "MY_3"}


def local_nusselt(model: str, x, Re: float, Pr: float, w_c: float, H: float) -> np.ndarray:
    """Local Nu_x (D_h based) at distances x (m) from the channel inlet.

    x = 0 is singular for the MY model; callers pass x > 0.
    """
    if model not in NUSSELT_MODELS:
        raise NotImplementedError(f"Nusselt model '{model}' is not implemented; "
                                  f"choose from {sorted(NUSSELT_MODELS)}.")
    return NUSSELT_MODELS[model](x, Re, Pr, w_c, H)


def nusselt(alpha: float, model: str = "fd_H1") -> float:
    """Fully developed Nu by name (kept for backward compatibility)."""
    if model == "fd_H1":
        return nu_fd_H1(alpha)
    if model == "fd_H1_3":
        return nu_fd_H1_3(alpha)
    raise NotImplementedError(f"'{model}' is position dependent; use local_nusselt().")


# --------------------------------------------------------------------------
# Apparent friction (hydrodynamically developing flow)
# --------------------------------------------------------------------------


def fapp_Re_MY(L: float, Re: float, w_c: float, H: float) -> float:
    """Length-mean apparent Fanning f*Re (D_h based) over 0..L, Eq. (47) of M&Y (2004).

    f_app Re_sqrtA = [ (3.44 / sqrt(z+))^2 + (fRe_sqrtA)^2 ]^(1/2),
    z+ = L / (sqrt(A) Re_sqrtA) = L/(D_h Re) * D_h^2 / A. Uniform inlet velocity.
    Checked against Shah & London's tabulated f_app Re for eps = 1, 0.5, 0.2
    (within 3 %, tests).
    """
    A = w_c * H
    D_h = 2.0 * w_c * H / (w_c + H)
    eps = min(w_c, H) / max(w_c, H)
    z_plus = L / (D_h * Re) * D_h**2 / A
    f_sqrtA = sqrt((3.44 / sqrt(z_plus)) ** 2 + fRe_sqrtA_rect(eps) ** 2)
    return f_sqrtA * D_h / sqrt(A)


def K_inf_rect(alpha: float) -> float:
    """Hagenbach factor (incremental pressure-drop number) K(inf) for a rectangle.

    K(inf) = 0.6796 + 1.2197a + 3.3089a^2 - 9.5921a^3 + 8.9089a^4 - 2.9959a^5,
    a = short/long. Attributed to Steinke & Kandlikar; quoted from Duan & Ma (2020)
    Eq. (33). Secondary source: not checked against the original.
    """
    a = alpha
    return (0.6796 + 1.2197 * a + 3.3089 * a**2 - 9.5921 * a**3 + 8.9089 * a**4
            - 2.9959 * a**5)


def fapp_Re_hagenbach(L: float, Re: float, w_c: float, H: float) -> float:
    """f_app Re = fRe_fd + K(inf) / (4 x+), x+ = L/(D_h Re). Only for x+ > ~0.05."""
    D_h = 2.0 * w_c * H / (w_c + H)
    a = min(w_c, H) / max(w_c, H)
    return fRe_fd(a) + K_inf_rect(a) / (4.0 * L / (D_h * Re))


def _fric_fd(L, Re, w_c, H):
    return fRe_fd(min(w_c, H) / max(w_c, H))


FRICTION_MODELS = {"fd": _fric_fd, "MY": fapp_Re_MY, "hagenbach": fapp_Re_hagenbach}


def apparent_fRe(model: str, L: float, Re: float, w_c: float, H: float) -> float:
    """Length-mean Fanning f*Re over the channel; dP = 2 fRe mu u L / D_h^2."""
    if model not in FRICTION_MODELS:
        raise NotImplementedError(f"friction model '{model}' is not implemented; "
                                  f"choose from {sorted(FRICTION_MODELS)}.")
    return float(FRICTION_MODELS[model](L, Re, w_c, H))


# --------------------------------------------------------------------------
# Entry lengths
# --------------------------------------------------------------------------


@dataclass
class EntryLengths:
    L_hyd: float        # hydrodynamic entry length (m), ~0.05 Re D_h
    L_th: float         # thermal entry length (m), ~0.05 Re Pr D_h
    L_hyd_ratio: float  # L_hyd / L
    L_th_ratio: float   # L_th / L
    L_th_LG: float = float("nan")        # Lee & Garimella Eq. (11), alpha_LG clipped to [1, 10]
    L_th_LG_ratio: float = float("nan")


def entry_lengths(Re: float, Pr: float, D_h: float, L: float,
                  w_c: float = None, H: float = None) -> EntryLengths:
    """Approximate laminar entry lengths. 0.05 Re D_h and 0.05 Re Pr D_h are the
    common circular-tube estimates; with w_c and H also the rectangular-channel
    value from Lee & Garimella (2006) Eq. (11)."""
    L_hyd = 0.05 * Re * D_h
    L_th = 0.05 * Re * Pr * D_h
    out = EntryLengths(L_hyd, L_th, L_hyd / L, L_th / L)
    if w_c is not None and H is not None:
        a_LG = float(np.clip(max(w_c, H) / min(w_c, H), *LG_ALPHA_RANGE))
        out.L_th_LG = z_th_lee_garimella(a_LG) * Re * Pr * D_h
        out.L_th_LG_ratio = out.L_th_LG / L
    return out
