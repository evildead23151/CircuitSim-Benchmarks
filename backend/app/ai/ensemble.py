"""Weighted ensemble surrogate with uncertainty quantification (Model F)."""
import structlog
import numpy as np
from typing import Optional

from app.ai.base import BaseSurrogate

log = structlog.get_logger()


class EnsembleSurrogate(BaseSurrogate):
    """Weighted ensemble of RF + MLP + PINN with uncertainty estimation.

    Weights are the inverse-MAE weights learned on a held-out validation set
    (or uniform if models have not been evaluated).  If any sub-model fails
    during inference it is silently excluded and the remaining weights are
    renormalised.
    """

    # Default sub-model names to include (RF always first as anchor)
    DEFAULT_MEMBERS = ["random_forest", "mlp", "pinn"]

    def __init__(self, registry=None):
        """Args:
            registry: ModelRegistry instance (injected to avoid circular import).
        """
        self._registry = registry
        # Uniform weights; updated by set_weights()
        self._weights: dict[str, float] = {
            name: 1.0 / len(self.DEFAULT_MEMBERS) for name in self.DEFAULT_MEMBERS
        }

    def set_registry(self, registry) -> None:
        self._registry = registry

    def set_weights(self, weights: dict[str, float]) -> None:
        """Override member weights (will be normalised internally)."""
        total = sum(weights.values()) or 1.0
        self._weights = {k: v / total for k, v in weights.items()}

    def name(self) -> str:
        return "ensemble"

    def load(self) -> None:
        # Nothing to load for the ensemble itself; sub-models are loaded by the registry.
        pass

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self._registry is None:
            raise RuntimeError("Ensemble: registry not set")

        preds: list[np.ndarray] = []
        active_weights: list[float] = []

        for member_name, w in self._weights.items():
            model = self._registry.get(member_name)
            if model is None or not model.is_loaded():
                continue
            try:
                p = model.predict(features)
                preds.append(p)
                active_weights.append(w)
            except Exception as exc:
                log.warning("ensemble_member_failed", member=member_name, error=str(exc))

        if not preds:
            raise RuntimeError("Ensemble: no sub-models available")

        w_arr = np.array(active_weights, dtype=np.float64)
        w_arr /= w_arr.sum()
        stack = np.stack(preds, axis=0)  # (n_models, 6)
        return np.average(stack, axis=0, weights=w_arr)

    def predict_with_uncertainty(self, features: np.ndarray) -> tuple[np.ndarray, Optional[float]]:
        """Return (mean_prediction, uncertainty) where uncertainty is the mean
        std-deviation across outputs and models."""
        if self._registry is None:
            raise RuntimeError("Ensemble: registry not set")

        preds: list[np.ndarray] = []
        active_weights: list[float] = []

        for member_name, w in self._weights.items():
            model = self._registry.get(member_name)
            if model is None or not model.is_loaded():
                continue
            try:
                p = model.predict(features)
                preds.append(p)
                active_weights.append(w)
            except Exception as exc:
                log.warning("ensemble_member_failed", member=member_name, error=str(exc))

        if not preds:
            raise RuntimeError("Ensemble: no sub-models available")

        w_arr = np.array(active_weights, dtype=np.float64)
        w_arr /= w_arr.sum()
        stack = np.stack(preds, axis=0)

        mean_pred = np.average(stack, axis=0, weights=w_arr)
        uncertainty = float(np.std(stack, axis=0).mean()) if len(preds) > 1 else None
        return mean_pred, uncertainty

    def is_loaded(self) -> bool:
        if self._registry is None:
            return False
        return any(
            self._registry.get(n) is not None and self._registry.get(n).is_loaded()
            for n in self._weights
        )

    def metadata(self) -> dict:
        return {
            "type": "Ensemble",
            "members": list(self._weights.keys()),
            "weights": self._weights,
            "uncertainty": True,
        }
