"""Transient metric solvers (heuristic and ODE-based)."""
import math
import numpy as np

from app.models.schemas import TopologicalCircuit
from app.solvers.constants import ESR_L


def get_transient_metrics(circuit: TopologicalCircuit) -> tuple[float, float, float]:
    """Heuristic transient metric estimator based on 2nd-order lumped equivalents.

    Returns:
        (rise_time_ms, settling_time_ms, overshoot_pct)
    """
    eq_R = 1.0 + ESR_L
    eq_L = 1e-6
    eq_C = 1e-9
    for s in circuit.stages:
        if s.type == "R":
            eq_R += s.value
        elif s.type == "L":
            eq_L += s.value
        elif s.type == "C":
            eq_C += s.value

    zeta = (eq_R / 2) * math.sqrt(eq_C / eq_L) if eq_L > 0 and eq_C > 0 else 1.0
    wn = 1 / math.sqrt(eq_L * eq_C) if eq_L > 0 and eq_C > 0 else 0.0

    tr = 1.8 / wn if wn > 0 else 0.0
    mp = (
        math.exp(-math.pi * zeta / math.sqrt(1 - zeta**2))
        if (0 < zeta < 1)
        else 0.0
    )
    ts = 4 / (zeta * wn) if (zeta * wn > 0) else 0.0

    return tr * 1000, ts * 1000, mp * 100


def get_transient_metrics_ode(circuit: TopologicalCircuit) -> tuple[float, float, float]:
    """ODE-based transient metric solver using scipy RK45 integration.

    Models the circuit as a 2nd-order series RLC ODE:
        L * d²i/dt² + R * di/dt + i/C = Vin * omega * cos(omega*t)
    Step-response is evaluated to extract rise time, settling time, overshoot.

    Returns:
        (rise_time_ms, settling_time_ms, overshoot_pct)
    """
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return get_transient_metrics(circuit)

    eq_R = 1.0 + ESR_L
    eq_L = 1e-6
    eq_C = 1e-9
    for s in circuit.stages:
        if s.type == "R":
            eq_R += s.value
        elif s.type == "L":
            eq_L += s.value
        elif s.type == "C":
            eq_C += s.value

    if eq_L <= 0 or eq_C <= 0:
        return get_transient_metrics(circuit)

    Vin = circuit.vin
    omega = 2 * math.pi * circuit.frequency

    # State vector: [i, di/dt]
    # L*di'/dt = Vin*step(t) - R*i - q/C  (series RLC step response)
    def rhs(t, y):
        i, q = y
        di = (Vin - eq_R * i - q / eq_C) / eq_L
        dq = i
        return [di, dq]

    wn = 1 / math.sqrt(eq_L * eq_C)
    # Simulate for ~10 natural periods (or at least 10 ms)
    t_end = max(10.0 / wn, 0.01)
    t_span = (0.0, t_end)
    t_eval = np.linspace(0.0, t_end, 2000)

    try:
        sol = solve_ivp(rhs, t_span, [0.0, 0.0], method="RK45", t_eval=t_eval,
                        rtol=1e-6, atol=1e-9)
        if not sol.success:
            return get_transient_metrics(circuit)

        # Charge q → Vout = q/C
        q = sol.y[1]
        vout = q / eq_C
        vout_final = float(vout[-1])

        if abs(vout_final) < 1e-12:
            return get_transient_metrics(circuit)

        vout_norm = vout / vout_final
        t = sol.t

        # Rise time: 10% → 90%
        idx_10 = np.argmax(vout_norm >= 0.1)
        idx_90 = np.argmax(vout_norm >= 0.9)
        tr = (t[idx_90] - t[idx_10]) * 1000 if idx_90 > idx_10 else 0.0

        # Overshoot
        peak = float(np.max(vout_norm))
        mp = max(0.0, (peak - 1.0) * 100.0)

        # Settling time: last time outside ±2% band
        outside = np.where(np.abs(vout_norm - 1.0) > 0.02)[0]
        ts = (t[outside[-1]] * 1000) if len(outside) > 0 else 0.0

        return float(tr), float(ts), float(mp)
    except Exception:
        return get_transient_metrics(circuit)
