"""Random Forest surrogate model (existing, wrapped in BaseSurrogate)."""
import math
import pickle
import structlog
import numpy as np

from app.ai.base import BaseSurrogate
from app.models.schemas import TopologicalCircuit

log = structlog.get_logger()

N_STAGES = 10
N_FEATURES = N_STAGES * 3 + 1  # 31


def vectorize_circuit(circuit: TopologicalCircuit) -> np.ndarray:
    """Convert a TopologicalCircuit into a (1, 31) feature vector.

    Features per stage: [tag, type_code, log10(value)]
    Final feature: log10(frequency)
    """
    features: list[float] = []
    for i in range(N_STAGES):
        if i < len(circuit.stages):
            s = circuit.stages[i]
            t_num = 1 if s.type == "R" else (2 if s.type == "L" else 3)
            val = max(s.value, 1e-12)
            features.extend([float(s.tag), float(t_num), math.log10(val)])
        else:
            features.extend([0.0, 0.0, -12.0])
    features.append(math.log10(max(circuit.frequency, 1.0)))
    return np.array([features], dtype=np.float32)


class RandomForestSurrogate(BaseSurrogate):
    """Wrapper around MultiOutputRegressor(RandomForestRegressor)."""

    def __init__(self, model_path: str):
        self._path = model_path
        self._model = None
        self._scaler = None

    def name(self) -> str:
        return "random_forest"

    def load(self) -> None:
        import os

        if not os.path.exists(self._path):
            log.warning("rf_model_not_found", path=self._path)
            return
        try:
            with open(self._path, "rb") as f:
                obj = pickle.load(f)
            if isinstance(obj, dict):
                self._model = obj.get("model", obj)
                self._scaler = obj.get("scaler")
            else:
                self._model = obj
            log.info("rf_model_loaded", path=self._path)
        except Exception as exc:
            log.error("rf_model_load_error", path=self._path, error=str(exc))

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Random Forest model not loaded")
        X = features.copy()
        if self._scaler is not None:
            X = self._scaler.transform(X)
        return np.array(self._model.predict(X)[0], dtype=np.float64)

    def is_loaded(self) -> bool:
        return self._model is not None

    def metadata(self) -> dict:
        return {
            "type": "RandomForest",
            "path": self._path,
            "n_features": N_FEATURES,
            "n_outputs": 6,
        }
