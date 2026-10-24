import pytest

from coldplate.config import Geometry
from coldplate.correlations import fRe_fd, nu_fd_H1
from coldplate.geometry import derive


def test_channel_count_and_Dh():
    g = Geometry(W=0.030, w_c=0.5e-3, w_f=0.3e-3, H=3.0e-3)
    d = derive(g)
    assert d.N == 37                      # 30 mm / 0.8 mm = 37.5 -> 37
    assert d.D_h == pytest.approx(2 * 0.5e-3 * 3e-3 / 3.5e-3)
    assert d.alpha == pytest.approx(0.5 / 3.0)


def test_parallel_plate_limits():
    assert nu_fd_H1(0.0) == pytest.approx(8.235)
    assert fRe_fd(0.0) == pytest.approx(24.0)


def test_square_duct():
    # Square duct, Shah & London: fRe ~ 14.23, Nu_H1 ~ 3.61
    assert fRe_fd(1.0) == pytest.approx(14.23, rel=0.01)
    assert nu_fd_H1(1.0) == pytest.approx(3.61, rel=0.02)


def test_too_wide_raises():
    with pytest.raises(ValueError):
        derive(Geometry(W=0.5e-3, w_c=0.5e-3, w_f=0.3e-3))
