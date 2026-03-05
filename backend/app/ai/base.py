"""Abstract base class for all circuit surrogate models."""
from abc import ABC, abstractmethod
import numpy as np


class BaseSurrogate(ABC):
    """Abstract base class for all circuit surrogate models.

    All subclasses must implement the following interface so that the model
    registry can treat every surrogate identically.
    """

    @abstractmethod
    def name(self) -> str:
        """Return a stable, unique identifier for this model."""
        ...

    @abstractmethod
    def load(self) -> None:
        """Load model weights / artefacts from disk.

        Must not raise on missing files — set an internal flag instead so
        ``is_loaded()`` can return ``False`` and the model can be excluded
        from ensemble inference gracefully.
        """
        ...

    @abstractmethod
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Run inference.

        Args:
            features: float32 array of shape ``(1, 31)`` — the 30 stage
                features (tag, type, log_val for up to 10 stages) plus
                log10(frequency).

        Returns:
            float64 array of shape ``(6,)`` with predictions
            ``[vout, iin, efficiency, rise_time, settling_time, overshoot]``.
        """
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Return ``True`` if model weights have been loaded successfully."""
        ...

    @abstractmethod
    def metadata(self) -> dict:
        """Return a dictionary with model metadata (architecture, paths, etc.)."""
        ...
