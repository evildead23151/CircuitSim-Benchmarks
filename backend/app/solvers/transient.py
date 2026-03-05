import math
import logging
from .constants import ESR_L, EQ_L_BASE, EQ_C_BASE, EQ_R_BASE

logger = logging.getLogger(__name__)


def get_transient_metrics(stages: list):
    """
    Estimate rise time, settling time, overshoot from equivalent lumped circuit.
    Returns (rise_time_ms, settling_time_ms, overshoot_pct).
    """
    eq_R = EQ_R_BASE + ESR_L
    eq_L = EQ_L_BASE
    eq_C = EQ_C_BASE

    for s in stages:
        if s["type"] == 'R':
            eq_R += s["value"]
        elif s["type"] == 'L':
            eq_L += s["value"]
        elif s["type"] == 'C':
            eq_C += s["value"]

    if eq_L > 0 and eq_C > 0:
        zeta = (eq_R / 2) * math.sqrt(eq_C / eq_L)
        wn = 1 / math.sqrt(eq_L * eq_C)
    else:
        zeta, wn = 1.0, 0.0

    tr = 1.8 / wn if wn > 0 else 0.0
    mp = (math.exp(-math.pi * zeta / math.sqrt(max(1 - zeta ** 2, 1e-12)))
          if 0 < zeta < 1 else 0.0)
    ts = 4 / (zeta * wn) if (zeta * wn > 0) else 0.0

    return tr * 1000, ts * 1000, mp * 100
