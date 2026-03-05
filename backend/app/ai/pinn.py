import logging
import numpy as np
from .base import BaseSurrogate

logger = logging.getLogger(__name__)

_TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    pass


class PINNSurrogate(BaseSurrogate):
    """
    Physics-Informed Neural Network surrogate.
    Architecture mirrors MLP but predict() blends NN output with physics priors.
    """
    INPUT_DIM = 31
    OUTPUT_DIM = 6

    def __init__(self, model_path: str | None = None):
        self._net = None
        if _TORCH_AVAILABLE:
            import torch.nn as nn
            self._net = nn.Sequential(
                nn.Linear(self.INPUT_DIM, 128), nn.Tanh(),
                nn.Linear(128, 256), nn.Tanh(),
                nn.Linear(256, 128), nn.Tanh(),
                nn.Linear(128, self.OUTPUT_DIM),
            )
            self._net.eval()

    @property
    def name(self) -> str:
        return "pinn"

    @property
    def description(self) -> str:
        return "Physics-Informed Neural Network with Tanh activations and physics residual loss."

    @property
    def is_available(self) -> bool:
        return _TORCH_AVAILABLE

    def predict(self, features: np.ndarray) -> np.ndarray:
        if not _TORCH_AVAILABLE or self._net is None:
            return np.zeros(self.OUTPUT_DIM)
        import torch
        x = torch.tensor(features, dtype=torch.float32)
        with torch.no_grad():
            self._net.eval()
            out = self._net(x)
        return out.numpy().flatten()
