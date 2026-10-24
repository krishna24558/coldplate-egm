"""Design studies.  (Weeks 4-5: you write this.)

Study 1: flow sweep at fixed geometry -> optimum V_dot* (compare with
         the analytical estimate V_dot* = (B / 2C)^(1/3)).
Study 2: minimize X_lost over (w_c, w_f, V_dot) subject to T_dev <= T_dev_max,
         dP <= dP_max, Re <= Re_max and manufacturing limits; compare with the
         minimum-thermal-resistance design; Pareto front.
Study 3: repeat Study 2 for T_in = 20-50 C; find where the device limit binds.

Method: coarse grid sweep first, then scipy.optimize.minimize(method="SLSQP")
starting from the best grid point.
"""


def evaluate(w_c: float, w_f: float, V_dot: float, base_config):
    """Run the full model for one design; return all outputs in one dict."""
    raise NotImplementedError


def flow_sweep(base_config, V_dots):
    raise NotImplementedError


def optimize_design(base_config, objective: str = "lost_work"):
    raise NotImplementedError
