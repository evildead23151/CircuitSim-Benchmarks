import math
import logging
import numpy as np
from .constants import ESR_L, G_C, LOAD_R, OOD_R_MIN, OOD_R_MAX, OOD_L_MIN, OOD_L_MAX, OOD_C_MIN, OOD_C_MAX

logger = logging.getLogger(__name__)


def analytical_solver(R: float, L: float, C: float, frequency: float, vin: float):
    """Simple series RLC analytical solver. Returns (vout, iin_mA, is_ood)."""
    is_ood = not (OOD_R_MIN <= R <= OOD_R_MAX and OOD_L_MIN <= L <= OOD_L_MAX and OOD_C_MIN <= C <= OOD_C_MAX)
    omega = 2 * math.pi * frequency
    if C <= 0:
        return 0.0, 0.0, is_ood

    Z_val = complex(R, omega * L - (1 / (omega * C) if C > 0 else 1e12))
    Z_mag = abs(Z_val)
    iin = vin / Z_mag if Z_mag != 0 else 0.0

    Zc_mag = 1 / (omega * C) if C > 0 else 1e12
    vout = iin * Zc_mag
    return vout, iin * 1000, is_ood


def solve_topological(stages: list, frequency: float, vin: float):
    """
    ABCD matrix solver for cascaded topological circuit stages.
    stages: list of dicts with keys: tag (int), type (str), value (float)
    Returns (vout, iin_mA, efficiency).
    """
    logger.debug("Solving topological circuit with %d stages", len(stages))
    M = np.identity(2, dtype=complex)

    for stage in stages:
        tag = stage["tag"]
        if tag == 0:
            break

        omega = 2 * math.pi * frequency
        stype = stage["type"]
        value = stage["value"]

        if stype == 'R':
            Z = complex(value, 0)
        elif stype == 'L':
            Z = complex(ESR_L, omega * value)
        elif stype == 'C':
            if value == 0:
                Z = complex(1e12, 0)
            else:
                Y = complex(G_C, omega * value)
                Z = 1 / Y
        else:
            continue

        if tag == 1:
            matrix = np.array([[1, Z], [0, 1]])
        elif tag == 2:
            Y_m = 1 / Z if Z != 0 else complex(1e12, 0)
            matrix = np.array([[1, 0], [Y_m, 1]])
        else:
            continue

        M = M @ matrix

    m11 = M[0, 0]
    vout = vin / m11 if m11 != 0 else complex(0)
    iin = M[1, 0] * vout

    RL = LOAD_R
    denom = M[0, 0] * RL + M[0, 1]
    iout_load = vin / denom if denom != 0 else complex(0)
    vout_load = iout_load * RL
    iin_load = M[1, 0] * vout_load + M[1, 1] * iout_load
    p_in = (vin * iin_load.conjugate()).real
    p_out = (vout_load * iout_load.conjugate()).real
    eff = p_out / p_in if p_in > 1e-9 else 0.0

    return float(abs(vout)), float(abs(iin)) * 1000, float(eff)
