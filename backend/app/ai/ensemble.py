import logging
import numpy as np
from .base import BaseSurrogate

logger = logging.getLogger(__name__)


class EnsembleSurrogate(BaseSurrogate):
    """Weighted ensemble of multiple BaseSurrogate models."""

    def __init__(self, models: list, weights: list[float] | None = None):
        self._models = models
        if weights is None:
            self._weights = [1.0 / len(models)] * len(models) if models else []
        else:
            total = sum(weights) or 1.0
            self._weights = [w / total for w in weights]

    @property
    def name(self) -> str:
        return "ensemble"

    @property
    def description(self) -> str:
        names = [m.name for m in self._models]
        return f"Weighted ensemble of: {', '.join(names)}."

    @property
    def is_available(self) -> bool:
        return any(m.is_available for m in self._models)

    def predict(self, features: np.ndarray) -> np.ndarray:
        preds = []
        ws = []
        for model, w in zip(self._models, self._weights):
            try:
                p = model.predict(features)
                preds.append(p * w)
                ws.append(w)
            except Exception as e:
                logger.warning("Ensemble sub-model %s failed: %s", model.name, e)
        if not preds:
            return np.zeros(6)
        total_w = sum(ws) or 1.0
        result = np.sum(preds, axis=0) / total_w
        return result
