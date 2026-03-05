"""Tests for BaseSurrogate interface compliance and surrogate models."""
import math
import pytest
import numpy as np

from app.ai.base import BaseSurrogate
from app.ai.random_forest import RandomForestSurrogate, vectorize_circuit, N_FEATURES
from app.ai.mlp import MLPSurrogate
from app.ai.pinn import PINNSurrogate
from app.ai.deeponet import DeepONetSurrogate
from app.ai.fno import FNOSurrogate
from app.ai.ensemble import EnsembleSurrogate
from app.models.schemas import TopologicalCircuit, TopologicalComponent


# ---------------------------------------------------------------------------
# Interface compliance via the mock fixture
# ---------------------------------------------------------------------------

class TestBaseSurrogateInterface:
    def test_mock_implements_interface(self, mock_surrogate):
        assert isinstance(mock_surrogate, BaseSurrogate)
        assert isinstance(mock_surrogate.name(), str)
        assert isinstance(mock_surrogate.is_loaded(), bool)
        assert isinstance(mock_surrogate.metadata(), dict)

    def test_mock_prediction_shape(self, mock_surrogate, sample_features):
        out = mock_surrogate.predict(sample_features)
        assert out.shape == (6,)

    def test_mock_prediction_finite(self, mock_surrogate, sample_features):
        out = mock_surrogate.predict(sample_features)
        assert np.all(np.isfinite(out))


# ---------------------------------------------------------------------------
# Feature vectorisation
# ---------------------------------------------------------------------------

class TestVectorizeCircuit:
    def test_output_shape(self, three_stage_circuit):
        feats = vectorize_circuit(three_stage_circuit)
        assert feats.shape == (1, N_FEATURES)

    def test_single_stage_shape(self, single_stage_r_circuit):
        feats = vectorize_circuit(single_stage_r_circuit)
        assert feats.shape == (1, N_FEATURES)

    def test_padding_for_short_circuit(self, single_stage_r_circuit):
        """Stages < 10 should be zero-padded correctly."""
        feats = vectorize_circuit(single_stage_r_circuit)
        # Positions 3..29 (stages 1-9) should be padded
        assert feats[0, 3] == 0.0   # tag of stage index 1
        assert feats[0, 5] == -12.0  # log_val of stage index 1

    def test_frequency_is_last_feature(self):
        circuit = TopologicalCircuit(
            stages=[TopologicalComponent(tag=1, type="R", value=100.0)],
            frequency=1000.0,
            vin=1.0,
        )
        feats = vectorize_circuit(circuit)
        assert abs(feats[0, -1] - math.log10(1000.0)) < 1e-6


# ---------------------------------------------------------------------------
# Un-loaded model behaviour
# ---------------------------------------------------------------------------

SURROGATE_CLASSES = [
    (RandomForestSurrogate, "/tmp/nonexistent_rf.pkl"),
    (MLPSurrogate, "/tmp/nonexistent_mlp.pt"),
    (PINNSurrogate, "/tmp/nonexistent_pinn.pt"),
    (DeepONetSurrogate, "/tmp/nonexistent_deeponet.pt"),
    (FNOSurrogate, "/tmp/nonexistent_fno.pt"),
]


@pytest.mark.parametrize("cls,path", SURROGATE_CLASSES)
class TestUnloadedSurrogates:
    def test_is_not_loaded_when_file_missing(self, cls, path):
        m = cls(path)
        m.load()
        assert m.is_loaded() is False

    def test_predict_raises_when_not_loaded(self, cls, path, sample_features):
        m = cls(path)
        m.load()
        with pytest.raises(RuntimeError):
            m.predict(sample_features)

    def test_metadata_returns_dict(self, cls, path):
        m = cls(path)
        assert isinstance(m.metadata(), dict)

    def test_name_returns_string(self, cls, path):
        m = cls(path)
        assert isinstance(m.name(), str)


# ---------------------------------------------------------------------------
# Ensemble model
# ---------------------------------------------------------------------------

class TestEnsembleSurrogate:
    def test_ensemble_with_mock_models(self, mock_surrogate, sample_features):
        from app.models.registry import ModelRegistry

        reg = ModelRegistry()
        # Register mock under a name that ensemble will look for
        ens = EnsembleSurrogate()
        ens._weights = {"mock": 1.0}

        class NamedMock(BaseSurrogate):
            def name(self): return "mock"
            def load(self): pass
            def predict(self, f): return np.array([0.9, 0.01, 0.85, 1.0, 5.0, 5.0])
            def is_loaded(self): return True
            def metadata(self): return {}

        reg.register(NamedMock())
        ens.set_registry(reg)

        out = ens.predict(sample_features)
        assert out.shape == (6,)
        assert np.isclose(out[0], 0.9)

    def test_ensemble_uncertainty(self, sample_features):
        from app.models.registry import ModelRegistry
        from app.ai.base import BaseSurrogate

        class MockA(BaseSurrogate):
            def name(self): return "mock_a"
            def load(self): pass
            def predict(self, f): return np.array([0.9, 0.01, 0.85, 1.0, 5.0, 5.0])
            def is_loaded(self): return True
            def metadata(self): return {}

        class MockB(BaseSurrogate):
            def name(self): return "mock_b"
            def load(self): pass
            def predict(self, f): return np.array([0.8, 0.02, 0.80, 1.5, 6.0, 6.0])
            def is_loaded(self): return True
            def metadata(self): return {}

        reg = ModelRegistry()
        reg.register(MockA())
        reg.register(MockB())

        ens = EnsembleSurrogate()
        ens._weights = {"mock_a": 0.5, "mock_b": 0.5}
        ens.set_registry(reg)

        mean_pred, uncertainty = ens.predict_with_uncertainty(sample_features)
        assert mean_pred.shape == (6,)
        assert uncertainty is not None
        assert uncertainty >= 0

    def test_ensemble_no_registry_raises(self, sample_features):
        ens = EnsembleSurrogate()
        with pytest.raises(RuntimeError):
            ens.predict(sample_features)
