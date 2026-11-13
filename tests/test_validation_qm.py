"""Regression guard on the Qu & Mudawar comparison (digitized data in validation/data/).

These thresholds record the validation result reached on 2026-11-08; they are not
tuning targets. If a change to the physics moves them, update the docs with the
new numbers rather than loosening the test silently.
"""

import warnings

import pytest

from coldplate.benchmark import compare

warnings.simplefilter("ignore")


@pytest.fixture(scope="module")
def best():
    return compare(nusselt_model="MY_3", axial_conduction=True, viscosity_correction=True,
                   friction_model="MY", include_minor=False)


def test_digitized_data_present(best):
    assert len(best["dP"]) >= 35
    assert sum(r["quantity"].startswith("TC") for r in best["thermal"]) >= 150


def test_thermal_within_proposal_target(best):
    assert best["MAPE_TC"] < 0.10          # proposal target 10-15 %


def test_energy_balance(best):
    w = [abs(r["error"]) for r in best["thermal"] if r["quantity"] == "water_temperature_rise"]
    assert sum(w) / len(w) < 0.05


def test_pressure_drop_best_combination(best):
    assert best["MAPE_dP"] < 0.15


def test_fully_developed_fails_thermally():
    r = compare(nusselt_model="fd_H1", axial_conduction=False)
    assert r["MAPE_TC"] > 0.3               # the reason D4 was needed
