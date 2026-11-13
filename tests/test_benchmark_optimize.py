"""Benchmark loader and optimizer behaviour (no accuracy claims)."""

import warnings

import numpy as np
import pytest

from coldplate.benchmark import compare, flow_from_reynolds, load_benchmark, predict
from coldplate.config import Case
from coldplate.optimize import optimize_design


@pytest.fixture(scope="module")
def bm():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return load_benchmark()


def test_benchmark_geometry_loaded(bm):
    g = bm.case.geometry
    assert bm.N == 21
    assert g.w_c == pytest.approx(231e-6) and g.H == pytest.approx(713e-6)
    assert np.all(np.diff(bm.tc_x) > 0)


def test_reynolds_definition_matches_stated_flow_rates(bm):
    # Paper (Sec. 2.3): Re 139 -> 93.5 ml/min and Re 1672 -> 1136.4 ml/min at 100 W/cm2.
    # Agreement supports assumption B1 (Re at inlet-temperature properties).
    assert flow_from_reynolds(bm, 139) * 6e7 == pytest.approx(93.5, rel=0.02)
    assert flow_from_reynolds(bm, 1672) * 6e7 == pytest.approx(1136.4, rel=0.02)


def test_prediction_trends(bm):
    p = predict(bm, 100, 890)
    assert p.dP_Pa > p.dP_friction_Pa > 0
    assert np.all(np.diff(p.T_tc_C) > 0)           # warmer toward the outlet
    hi = predict(bm, 100, 1672)
    assert hi.dP_Pa > p.dP_Pa and hi.dT_water_K < p.dT_water_K


def test_compare_runs_with_empty_digitized_files():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = compare()
    assert "MAPE_dP" in out and "MAPE_thermal" in out


def test_min_thermal_resistance_design_is_feasible_and_beats_start():
    case = Case()
    opt = optimize_design(case, "thermal_resistance", (2e-4, 2e-4, 2.0 / 60000))
    assert opt.result.feasible
    from coldplate.model import evaluate
    assert opt.result.R_th < evaluate(case).R_th
