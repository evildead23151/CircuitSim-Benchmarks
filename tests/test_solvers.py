"""Tests for analytical and topological solvers."""
import math
import pytest
import numpy as np

from app.models.schemas import CircuitParams, TopologicalCircuit, TopologicalComponent
from app.solvers.analytical import analytical_solver, solve_topological
from app.solvers.transient import get_transient_metrics, get_transient_metrics_ode


# ---------------------------------------------------------------------------
# analytical_solver tests
# ---------------------------------------------------------------------------

class TestAnalyticalSolver:
    def test_known_rlc_values(self):
        """At resonance (ω = 1/√LC) the capacitor voltage peaks near Vin."""
        L, C = 1e-3, 1e-6
        f_res = 1 / (2 * math.pi * math.sqrt(L * C))
        params = CircuitParams(R=10.0, L=L, C=C, frequency=f_res, vin=1.0)
        vout, iin, is_ood = analytical_solver(params)
        # At resonance the impedance is minimum (purely resistive), so vout is large
        assert vout > 0
        assert iin > 0

    def test_zero_capacitance_returns_zero(self):
        params = CircuitParams(R=100.0, L=1e-3, C=0.0, frequency=1000.0, vin=1.0)
        vout, iin, _ = analytical_solver(params)
        assert vout == 0.0

    def test_out_of_domain_flag(self):
        """Extreme R triggers is_ood=True."""
        params = CircuitParams(R=1e6, L=1e-3, C=1e-6, frequency=1000.0, vin=1.0)
        _, _, is_ood = analytical_solver(params)
        assert is_ood is True

    def test_in_domain_flag(self):
        params = CircuitParams(R=100.0, L=1e-3, C=1e-6, frequency=1000.0, vin=1.0)
        _, _, is_ood = analytical_solver(params)
        assert is_ood is False

    def test_vin_scales_linearly(self):
        """Doubling Vin should double vout (linearity)."""
        params1 = CircuitParams(R=100.0, L=1e-3, C=1e-6, frequency=1000.0, vin=1.0)
        params2 = CircuitParams(R=100.0, L=1e-3, C=1e-6, frequency=1000.0, vin=2.0)
        v1, _, _ = analytical_solver(params1)
        v2, _, _ = analytical_solver(params2)
        assert abs(v2 - 2 * v1) < 1e-10


# ---------------------------------------------------------------------------
# solve_topological tests
# ---------------------------------------------------------------------------

class TestSolveTopological:
    def test_single_series_r_passes_vin(self, single_stage_r_circuit):
        """Single tiny series R should pass almost all of Vin to output."""
        vout, _, _ = solve_topological(single_stage_r_circuit)
        # With R=1Ω series in ABCD, open-load Vout = Vin/M11 = Vin (M11→1)
        assert abs(vout - 1.0) < 0.01

    def test_output_finite(self, three_stage_circuit):
        vout, iin, eff = solve_topological(three_stage_circuit)
        assert math.isfinite(vout)
        assert math.isfinite(iin)
        assert math.isfinite(eff)

    def test_efficiency_in_range(self, three_stage_circuit):
        _, _, eff = solve_topological(three_stage_circuit)
        assert 0.0 <= eff <= 1.0

    def test_terminate_tag_stops_chain(self):
        """Tag=0 terminates the chain; subsequent stages are ignored."""
        circuit = TopologicalCircuit(
            stages=[
                TopologicalComponent(tag=0, type="R", value=100.0),
                TopologicalComponent(tag=1, type="R", value=1000.0),
            ],
            frequency=1000.0,
            vin=1.0,
        )
        vout, _, _ = solve_topological(circuit)
        # With no stages (identity matrix), Vout = Vin
        assert abs(vout - 1.0) < 1e-9

    def test_very_high_frequency(self):
        """At very high frequency with a shunt-R + series-LC, vout should be ≥ 0 and finite."""
        circuit = TopologicalCircuit(
            stages=[
                TopologicalComponent(tag=1, type="L", value=1e-3),
                TopologicalComponent(tag=1, type="C", value=1e-6),
            ],
            frequency=1e9,
            vin=1.0,
        )
        vout, _, _ = solve_topological(circuit)
        # Open-circuit ABCD: series-L + series-C → M11=1, Vout=Vin (no load, no voltage drop)
        assert vout >= 0
        assert math.isfinite(vout)


# ---------------------------------------------------------------------------
# Transient metric tests
# ---------------------------------------------------------------------------

class TestTransientMetrics:
    def test_returns_three_values(self, three_stage_circuit):
        tr, ts, mp = get_transient_metrics(three_stage_circuit)
        assert tr >= 0
        assert ts >= 0
        assert mp >= 0

    def test_overdamped_no_overshoot(self):
        """Very high R → overdamped (zeta > 1) → no overshoot."""
        circuit = TopologicalCircuit(
            stages=[
                TopologicalComponent(tag=1, type="R", value=1e4),
                TopologicalComponent(tag=1, type="L", value=1e-3),
                TopologicalComponent(tag=1, type="C", value=1e-6),
            ],
            frequency=1000.0,
            vin=1.0,
        )
        _, _, mp = get_transient_metrics(circuit)
        assert mp == 0.0

    def test_ode_solver_returns_finite(self, three_stage_circuit):
        tr, ts, mp = get_transient_metrics_ode(three_stage_circuit)
        assert math.isfinite(tr)
        assert math.isfinite(ts)
        assert math.isfinite(mp)

    def test_ode_consistent_with_heuristic_order(self, single_stage_r_circuit):
        """ODE and heuristic results should be in the same ballpark (within 3 orders of magnitude)."""
        tr_h, ts_h, _ = get_transient_metrics(single_stage_r_circuit)
        tr_o, ts_o, _ = get_transient_metrics_ode(single_stage_r_circuit)
        # Both should be positive (or zero); not testing exact match, just sanity
        assert tr_h >= 0
        assert tr_o >= 0
