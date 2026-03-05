"""Shared pytest fixtures for the CircuitSim-Benchmarks test suite."""
import math
import pytest
import numpy as np
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Sample circuit data
# ---------------------------------------------------------------------------

@pytest.fixture
def series_rlc_params():
    """Simple series RLC at 1 kHz."""
    from app.models.schemas import CircuitParams
    return CircuitParams(R=100.0, L=1e-3, C=1e-6, frequency=1000.0, vin=1.0)


@pytest.fixture
def single_stage_r_circuit():
    """Single-stage series resistor circuit (degenerate, mostly passes Vin)."""
    from app.models.schemas import TopologicalCircuit, TopologicalComponent
    return TopologicalCircuit(
        stages=[TopologicalComponent(tag=1, type="R", value=1.0)],
        frequency=1000.0,
        vin=1.0,
    )


@pytest.fixture
def three_stage_circuit():
    """Three-stage RLC series circuit."""
    from app.models.schemas import TopologicalCircuit, TopologicalComponent
    return TopologicalCircuit(
        stages=[
            TopologicalComponent(tag=1, type="R", value=100.0),
            TopologicalComponent(tag=1, type="L", value=1e-3),
            TopologicalComponent(tag=1, type="C", value=1e-6),
        ],
        frequency=1000.0,
        vin=1.0,
    )


@pytest.fixture
def sample_features():
    """A (1, 31) feature vector with sensible defaults (all R stages)."""
    feats = []
    for i in range(10):
        if i == 0:
            feats.extend([1.0, 1.0, math.log10(100.0)])  # series R=100Ω
        else:
            feats.extend([0.0, 0.0, -12.0])  # padding
    feats.append(math.log10(1000.0))  # log_freq
    return np.array([feats], dtype=np.float32)


# ---------------------------------------------------------------------------
# Mock model fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_surrogate():
    """A mock BaseSurrogate that always returns a fixed prediction."""
    from app.ai.base import BaseSurrogate

    class MockModel(BaseSurrogate):
        def name(self):
            return "mock"

        def load(self):
            pass

        def predict(self, features):
            return np.array([0.9, 0.01, 0.85, 1.0, 5.0, 5.0], dtype=np.float64)

        def is_loaded(self):
            return True

        def metadata(self):
            return {"type": "mock"}

    return MockModel()
