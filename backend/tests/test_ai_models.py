import numpy as np
import pytest
from app.ai.random_forest import RandomForestSurrogate
from app.ai.mlp_surrogate import MLPSurrogate
from app.ai.pinn import PINNSurrogate
from app.ai.deeponet import DeepONetSurrogate
from app.ai.fno import FNOSurrogate
from app.ai.ensemble import EnsembleSurrogate

DUMMY_FEATURES = np.zeros((1, 31))


def _check_predict(model):
    result = model.predict(DUMMY_FEATURES)
    assert isinstance(result, np.ndarray), f"{model.name} must return np.ndarray"
    assert result.shape[0] >= 1, f"{model.name} output must have at least 1 element"
    assert not np.any(np.isnan(result)), f"{model.name} must not return NaN"


def test_random_forest_instantiation():
    m = RandomForestSurrogate(model_dir="/nonexistent")
    assert m.name == "random_forest"
    _check_predict(m)


def test_mlp_instantiation():
    m = MLPSurrogate()
    assert m.name == "mlp"
    _check_predict(m)


def test_pinn_instantiation():
    m = PINNSurrogate()
    assert m.name == "pinn"
    _check_predict(m)


def test_deeponet_instantiation():
    m = DeepONetSurrogate()
    assert m.name == "deeponet"
    _check_predict(m)


def test_fno_instantiation():
    m = FNOSurrogate()
    assert m.name == "fno"
    _check_predict(m)


def test_ensemble_instantiation():
    models = [RandomForestSurrogate(model_dir="/nonexistent"), MLPSurrogate()]
    m = EnsembleSurrogate(models)
    assert m.name == "ensemble"
    _check_predict(m)


def test_ensemble_weights():
    m1 = RandomForestSurrogate(model_dir="/nonexistent")
    m2 = MLPSurrogate()
    ens = EnsembleSurrogate([m1, m2], weights=[0.7, 0.3])
    result = ens.predict(DUMMY_FEATURES)
    assert not np.any(np.isnan(result))
