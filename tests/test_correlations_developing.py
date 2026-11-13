"""Checks of the developing-flow correlations against independent reference data.

Reference values below are tabulated results from the literature (not model
output), used to confirm the coefficient transcriptions:
  * Wibulswas (1966) local Nu_x, H1, four walls, as tabulated in Lee, Garimella
    & Liu, IJHMT 48 (2005) Table 2 (columns alpha_LG = 3 and 4).
  * Shah & London (1978) apparent f_app Re for rectangular ducts, as tabulated
    in Duan & Ma (2020) Table 3 (columns eps = 1, 0.5, 0.2).
"""

import numpy as np
import pytest

from coldplate import correlations as c

WIB_ZSTAR = np.array([0.0025, 0.005, 0.00556, 0.00625, 0.00714, 0.00833, 0.01,
                      0.0125, 0.0167, 0.025, 0.033])
WIB = {
    3.0: np.array([9.9, 8.02, 7.76, 7.5, 7.22, 6.92, 6.57, 6.21, 5.82, 5.39, 5.17]),
    4.0: np.array([10.4, 8.44, 8.18, 7.92, 7.63, 7.32, 7.0, 6.63, 6.26, 5.87, 5.77]),
}
SL_XPLUS = np.array([0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2])
SL_FAPP = {
    1.0: np.array([111.0, 80.2, 51.8, 38.0, 28.6, 21.0, 17.8, 15.8]),
    0.5: np.array([111.0, 80.2, 51.8, 38.2, 29.1, 21.8, 18.8, 17.0]),
    0.2: np.array([111.0, 80.2, 52.5, 38.9, 30.2, 23.7, 21.4, 20.1]),
}


def test_fully_developed_limits():
    assert c.nu_fd_H1(1.0) == pytest.approx(3.61, abs=0.01)
    assert c.nu_fd_H1_3(1.0) == pytest.approx(3.556, abs=0.01)
    assert c.nu_fd_H1_3(1e-6) == pytest.approx(8.235, rel=1e-4)
    # Nu is based on the heated perimeter: an adiabatic short wall lowers it for a
    # square duct but raises it slightly for tall channels (Lee & Garimella Eq. 16)
    assert c.nu_fd_H1_3(1.0) < c.nu_fd_H1(1.0)
    assert 1.0 < c.nu_fd_H1_3(0.324) / c.nu_fd_H1(0.324) < 1.12


@pytest.mark.parametrize("a_LG", [1, 2, 3, 4, 6, 8, 10])
def test_lee_garimella_entry_length_definition(a_LG):
    """Eq. (12) at z*_th (Eq. 11) should be about 1.05 Nu_fd (the paper's definition)."""
    z = c.z_th_lee_garimella(a_LG)
    ratio = float(c.nu_lee_garimella(z, a_LG)) / c.nu_fd_H1(1.0 / a_LG)
    assert 1.0 < ratio < 1.10


@pytest.mark.parametrize("a_LG", [3.0, 4.0])
def test_lee_garimella_matches_wibulswas(a_LG):
    pred = c.nu_lee_garimella(WIB_ZSTAR, a_LG)
    err = (pred - WIB[a_LG]) / WIB[a_LG]
    assert np.max(np.abs(err)) < 0.07
    assert np.mean(np.abs(err)) < 0.04


def test_lee_garimella_local_tends_to_fd():
    w_c, H = 231e-6, 713e-6
    nu = c.nu_x_LG(np.array([1e-4, 1e-2, 0.2, 5.0]), w_c, H)
    assert np.all(np.diff(nu) <= 0)
    assert nu[-1] == pytest.approx(c.nu_fd_H1(w_c / H), rel=1e-9)


def test_muzychka_circle_limit_and_square_friction():
    # fully developed term reproduces the circular-tube values (Nu_D = 4.364 H, 3.657 T)
    k = c.MY_CONST
    assert k["H"]["C1"] * 2 / np.sqrt(np.pi) == pytest.approx(4.364, rel=0.005)
    assert k["T"]["C1"] * 2 / np.sqrt(np.pi) == pytest.approx(3.657, rel=0.005)
    assert c.fRe_sqrtA_rect(1.0) == pytest.approx(14.13, rel=0.002)


def test_muzychka_thermal_vs_wibulswas():
    """Thermal-only part (Pr -> inf) of Eq. (45) vs Wibulswas, alpha_LG = 3."""
    eps = 1.0 / 3.0
    r = (2 * eps / (1 + eps)) / np.sqrt(eps)        # D_h / sqrt(A)
    nu = c.nu_sqrtA_muzychka(WIB_ZSTAR * r**2, eps, Pr=7.0, combined=False) * r
    err = (nu - WIB[3.0]) / WIB[3.0]
    assert np.max(np.abs(err)) < 0.10    # paper claims about +/-15 %


def test_muzychka_combined_above_thermal_only():
    x = np.array([1e-3, 5e-3, 2e-2])
    args = dict(Re=1000.0, Pr=7.0, w_c=231e-6, H=713e-6)
    nu_comb = c.nu_x_MY(x, **args)
    D_h = 2 * 231e-6 * 713e-6 / (231e-6 + 713e-6)
    A = 231e-6 * 713e-6
    z = x / (1000.0 * 7.0 * D_h) * D_h**2 / A
    nu_th = c.nu_sqrtA_muzychka(z, 231 / 713, 7.0, combined=False) * D_h / np.sqrt(A)
    assert np.all(nu_comb >= nu_th)


@pytest.mark.parametrize("eps", [1.0, 0.5, 0.2])
def test_apparent_friction_matches_shah_london(eps):
    H = 1e-3
    w_c = eps * H
    D_h = 2 * w_c * H / (w_c + H)
    Re = 1000.0
    pred = np.array([c.fapp_Re_MY(xp * D_h * Re, Re, w_c, H) for xp in SL_XPLUS])
    err = (pred - SL_FAPP[eps]) / SL_FAPP[eps]
    assert np.max(np.abs(err)) < 0.04


def test_friction_models_tend_to_fully_developed():
    w_c, H, Re = 231e-6, 713e-6, 500.0
    fd = c.apparent_fRe("fd", 1.0, Re, w_c, H)
    assert c.apparent_fRe("MY", 50.0, Re, w_c, H) == pytest.approx(
        c.fRe_sqrtA_rect(w_c / H) * (2 * w_c * H / (w_c + H)) / np.sqrt(w_c * H), rel=0.01)
    assert c.apparent_fRe("hagenbach", 50.0, Re, w_c, H) == pytest.approx(fd, rel=0.01)
    assert c.apparent_fRe("MY", 0.01, Re, w_c, H) > fd


def test_local_nusselt_registry_and_errors():
    x = np.linspace(1e-4, 0.04, 5)
    for name in c.NUSSELT_MODELS:
        nu = c.local_nusselt(name, x, 800.0, 6.0, 231e-6, 713e-6)
        assert nu.shape == x.shape and np.all(nu > 0)
    with pytest.raises(NotImplementedError):
        c.local_nusselt("nope", x, 800.0, 6.0, 231e-6, 713e-6)
    with pytest.raises(ValueError):           # three-sided fit needs H >= w_c
        c.local_nusselt("fd_H1_3", x, 800.0, 6.0, 713e-6, 231e-6)
