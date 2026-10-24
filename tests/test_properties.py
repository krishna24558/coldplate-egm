"""Water properties should match NIST reference values (1 atm)."""

import pytest

from coldplate.properties import props, temperature_from_hP

P = 101325.0


def test_water_25C():
    p = props(298.15, P)
    assert p.rho == pytest.approx(997.05, rel=1e-3)
    assert p.cp == pytest.approx(4181.3, rel=2e-3)
    assert p.mu == pytest.approx(8.90e-4, rel=1e-2)
    assert p.k == pytest.approx(0.6065, rel=1e-2)


def test_water_60C():
    p = props(333.15, P)
    assert p.rho == pytest.approx(983.2, rel=1e-3)
    assert p.mu == pytest.approx(4.66e-4, rel=1e-2)


def test_temperature_round_trip():
    p = props(320.0, 2e5)
    assert temperature_from_hP(p.h, 2e5) == pytest.approx(320.0, abs=1e-6)
