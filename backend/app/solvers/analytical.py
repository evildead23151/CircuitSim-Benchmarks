"""Analytical and topological (ABCD matrix) circuit solvers."""
import math
import numpy as np

from app.models.schemas import CircuitParams, TopologicalCircuit
from app.solvers.constants import ESR_L, G_C


def analytical_solver(params: CircuitParams) -> tuple[float, float, bool]:
    """Closed-form analytical solver for steady-state LTI AC series-RLC circuits.

    Returns:
        (vout, iin_mA, is_ood)
    """
    R, L, C = params.R, params.L, params.C
    Vin, f = params.vin, params.frequency
    is_ood = not (0.1 <= R <= 10000 and 1e-6 <= L <= 1.0 and 1e-9 <= C <= 1e-3)
    omega = 2 * math.pi * f

    if C <= 0:
        return 0.0, 0.0, is_ood

    Z_val = complex(R, omega * L - (1 / (omega * C) if C > 0 else 1e12))
    Z_mag = abs(Z_val)
    iin = Vin / Z_mag if Z_mag != 0 else 0.0

    Zc_mag = 1 / (omega * C) if C > 0 else 1e12
    vout = iin * Zc_mag
    return vout, iin * 1000, is_ood


def solve_topological(circuit: TopologicalCircuit) -> tuple[float, float, float]:
    """ABCD matrix solver for cascaded topological circuit.

    Non-ideal model: inductors include ESR, capacitors include leakage.

    Returns:
        (vout, iin_mA, efficiency)
    """
    M = np.identity(2, dtype=complex)

    for stage in circuit.stages:
        tag = stage.tag
        if tag == 0:
            break

        omega = 2 * math.pi * circuit.frequency
        if stage.type == "R":
            Z = complex(stage.value, 0)
        elif stage.type == "L":
            Z = complex(ESR_L, omega * stage.value)
        elif stage.type == "C":
            if stage.value == 0:
                Z = complex(1e12, 0)
            else:
                Y = complex(G_C, omega * stage.value)
                Z = 1 / Y
        else:
            continue

        if tag == 1:  # Series
            matrix = np.array([[1, Z], [0, 1]])
        elif tag == 2:  # Shunt
            Y_m = 1 / Z if Z != 0 else complex(1e12, 0)
            matrix = np.array([[1, 0], [Y_m, 1]])
        else:
            continue

        M = M @ matrix

    m11 = M[0, 0]
    m21 = M[1, 0]
    vout = circuit.vin / m11 if m11 != 0 else complex(0)
    iin = m21 * vout

    # Efficiency with reference load RL = 1 kΩ (heuristic for passive network)
    RL = 1000.0
    denom = M[0, 0] * RL + M[0, 1]
    iout_load = circuit.vin / denom if denom != 0 else complex(0)
    vout_load = iout_load * RL
    iin_load = M[1, 0] * vout_load + M[1, 1] * iout_load
    p_in = (circuit.vin * iin_load.conjugate()).real
    p_out = (vout_load * iout_load.conjugate()).real
    eff = p_out / p_in if p_in > 1e-9 else 0.0

    return float(abs(vout)), float(abs(iin)) * 1000, float(eff)
