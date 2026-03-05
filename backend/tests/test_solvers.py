import pytest
from app.solvers.analytical import solve_topological
from app.solvers.transient import get_transient_metrics


SIMPLE_R_CIRCUIT = [
    {"tag": 1, "type": "R", "value": 100.0},
]

SERIES_RLC = [
    {"tag": 1, "type": "R", "value": 50.0},
    {"tag": 1, "type": "L", "value": 1e-3},
    {"tag": 1, "type": "C", "value": 1e-6},
]


def test_resistor_vout_lte_vin():
    vout, iin_ma, eff = solve_topological(SIMPLE_R_CIRCUIT, frequency=1000.0, vin=1.0)
    assert vout <= 1.0, f"vout={vout} must be <= vin=1.0"
    assert eff >= 0.0


def test_rlc_vout_nonneg():
    vout, iin_ma, eff = solve_topological(SERIES_RLC, frequency=1000.0, vin=5.0)
    assert vout >= 0.0
    assert iin_ma >= 0.0


def test_empty_stages():
    vout, iin_ma, eff = solve_topological([], frequency=1000.0, vin=1.0)
    # With identity matrix, vout = vin/1 = vin
    assert vout == pytest.approx(1.0, abs=1e-6)


def test_transient_metrics_positive():
    tr, ts, mp = get_transient_metrics(SERIES_RLC)
    assert tr >= 0.0
    assert ts >= 0.0
    assert mp >= 0.0


def test_terminate_tag_stops_chain():
    stages = [
        {"tag": 0, "type": "R", "value": 100.0},
    ]
    vout, _, _ = solve_topological(stages, frequency=1000.0, vin=1.0)
    # Should be same as identity (vin/1)
    assert vout == pytest.approx(1.0, abs=1e-6)
