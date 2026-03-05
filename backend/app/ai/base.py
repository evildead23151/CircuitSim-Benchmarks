from abc import ABC, abstractmethod
import numpy as np


class BaseSurrogate(ABC):
    """Abstract base class for all surrogate/AI models."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique model name."""

    @property
    def description(self) -> str:
        return ""

    @property
    def is_available(self) -> bool:
        return True

    @abstractmethod
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Run inference.
        features: shape (1, N)
        Returns: 1-D numpy array of predictions (at least length 1).
        """
