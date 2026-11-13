"""Second-law consistency checks (validation layer 3 in validation/README.md)."""

import pytest

from coldplate.config import Case, DeadState, Models
from coldplate.model import evaluate
from coldplate.optimize import flow_sweep, optimum_flow
from coldplate.second_law import flow_exergy


def test_entropy_generation_positive_over_flow_range():
    for r in flow_sweep(Case(), [0.5, 1, 2, 4, 8]):
        assert r.sl.S_gen_C > 0
        assert r.sl.S_gen_L > 0
        assert r.sl.S_gen_P > 0
        assert min(r.sl.S_warm, r.sl.S_gap, r.sl.S_pump) > 0


def test_cv_l_terms_sum_to_closed_form():
    r = evaluate(Case())
    op, sl = r.case.operating, r.sl
    W = r.hyd.W_elec  # pump inside the CV by default (D7)
    closed = op.Q * (1 / op.T_in - 1 / sl.T_s_eff) + W / op.T_in
    assert sl.S_warm + sl.S_gap + sl.S_pump == pytest.approx(closed, rel=1e-12)
    assert sl.X_lost == pytest.approx(r.case.dead_state.T0 * sl.S_gen_L)


def test_cv_c_mean_boundary_and_split_close_to_exact():
    sl = evaluate(Case()).sl
    assert sl.S_gen_C_mean == pytest.approx(sl.S_gen_C, rel=0.01)       # A1 error small
    assert sl.S_C_dT + sl.S_C_dP == pytest.approx(sl.S_gen_C, rel=0.01)


def test_flow_exergy_zero_at_dead_state():
    ds = DeadState()
    assert flow_exergy(ds.T0, ds.P0, ds.T0, ds.P0) == pytest.approx(0.0, abs=1e-6)
    assert flow_exergy(330.0, ds.P0, ds.T0, ds.P0) > 0


def test_interior_flow_optimum_and_analytical_estimate():
    o = optimum_flow(Case())
    V_lpm = o.V_dot * 60000
    assert 0.5 < V_lpm < 15.0                                   # interior, not at a bound
    assert o.V_dot_analytical == pytest.approx(o.V_dot, rel=0.20)
    assert 1.5 < o.warm_to_pump_ratio < 3.5                     # laminar theory: about 2


def test_cv_c_alone_has_no_interior_optimum_fully_developed():
    # Documented behaviour (equation_sheet.md section 2): with fully developed flow,
    # h does not depend on velocity and S_gen_C keeps rising with flow
    fd = Case(models=Models("fd_H1", "fd", False, False))
    rs = flow_sweep(fd, [1, 2, 4, 8])
    s = [r.sl.S_gen_C for r in rs]
    assert all(b > a for a, b in zip(s, s[1:]))


def test_cv_c_with_developing_flow():
    # With developing flow h rises with velocity, so S_gen_C can fall with flow; record
    # only that it stays positive and finite (equation_sheet.md section 2)
    rs = flow_sweep(Case(), [1, 2, 4, 8])
    assert all(r.sl.S_gen_C > 0 for r in rs)
