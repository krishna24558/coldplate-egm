"""Hydraulic and thermal modules: analytic limits and conservation checks."""

from dataclasses import replace

import pytest

from coldplate.config import Case, Geometry, Losses, Materials
from coldplate.geometry import derive
from coldplate.hydraulic import pressure_drop, pump_power
from coldplate.model import evaluate
from coldplate.optimize import with_design
from coldplate.properties import props
from coldplate.thermal import fin_efficiency


def test_poiseuille_parallel_plate_limit():
    # Very tall, thin channel ~ parallel plates of gap b: dP = 12 mu u L / b^2
    g = Geometry(W=0.03, L=0.03, H=0.2, w_c=1e-4, w_f=1e-4)
    d = derive(g)
    fp = props(300.0, 2e5)
    m_dot = 1e-3
    hr = pressure_drop(g, d, fp, m_dot, Losses(), include_minor=False)
    analytic = 12.0 * fp.mu * hr.u * g.L / g.w_c**2
    assert hr.dP_friction == pytest.approx(analytic, rel=0.01)


def test_friction_linear_minor_quadratic_in_flow():
    g = Geometry()
    d = derive(g)
    fp = props(305.0, 2e5)
    a = pressure_drop(g, d, fp, 0.02, Losses())
    b = pressure_drop(g, d, fp, 0.04, Losses())
    assert b.dP_friction / a.dP_friction == pytest.approx(2.0, rel=1e-9)
    assert b.dP_minor / a.dP_minor == pytest.approx(4.0, rel=1e-9)
    assert a.W_hyd == pytest.approx(a.V_dot * a.dP_total)
    assert a.W_elec == pytest.approx(a.W_hyd / Losses().eta_pump)


def test_pump_power_rejects_bad_efficiency():
    with pytest.raises(ValueError):
        pump_power(1e4, 1e-5, 0.0)


def test_fin_efficiency_limits():
    assert fin_efficiency(1e-9, 390.0, 2e-4, 3e-3) == pytest.approx(1.0, abs=1e-6)
    eta = fin_efficiency(1e4, 390.0, 2e-4, 3e-3)
    assert 0.0 < eta < 1.0
    assert fin_efficiency(2e4, 390.0, 2e-4, 3e-3) < eta  # higher h -> lower efficiency


def test_energy_balance_and_temperature_order():
    r = evaluate(Case())
    op = r.case.operating
    fp = props(0.5 * (op.T_in + r.th.T_out), op.P_in)
    # Q = m (h_out - h_in) exactly; with mean cp it closes to well within 0.5 %
    assert r.m_dot * fp.cp * (r.th.T_out - op.T_in) == pytest.approx(op.Q, rel=5e-3)
    assert op.T_in < r.th.T_f_mean < r.th.T_out < r.th.T_s_mean < r.th.T_dev
    assert r.R_th == pytest.approx((r.th.T_dev - op.T_in) / op.Q)


def test_more_flow_cools_less_than_its_cost():
    base = Case()
    lo = evaluate(with_design(base, V_dot=2.0 / 60000))
    hi = evaluate(with_design(base, V_dot=4.0 / 60000))
    assert hi.th.T_dev < lo.th.T_dev
    assert hi.hyd.W_hyd > 4.0 * lo.hyd.W_hyd   # laminar friction ~V^2 plus minor ~V^3


def test_device_temperature_floor_set_by_geometry():
    # Even unlimited flow cannot remove R_conv + R_base + R_tim
    r = evaluate(Case())
    floor = r.case.operating.T_in + r.case.operating.Q * (r.th.R_conv + r.th.R_base + r.th.R_tim)
    assert r.th.T_dev > floor
