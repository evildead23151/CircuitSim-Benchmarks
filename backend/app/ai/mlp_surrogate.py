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
    logger.info("MLP: PyTorch not available, using numpy fallback")


def _build_mlp(input_dim: int, output_dim: int):
    if not _TORCH_AVAILABLE:
        return None
    import torch.nn as nn
    return nn.Sequential(
        nn.Linear(input_dim, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.2),
        nn.Linear(128, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.2),
        nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.1),
        nn.Linear(128, output_dim),
    )


class MLPSurrogate(BaseSurrogate):
    INPUT_DIM = 31   # 10 stages × 3 features + 1 freq
    OUTPUT_DIM = 6

    def __init__(self, model_path: str | None = None):
        self._net = None
        if _TORCH_AVAILABLE:
            import torch
            self._net = _build_mlp(self.INPUT_DIM, self.OUTPUT_DIM)
            self._net.eval()
            if model_path and __import__("os").path.exists(model_path):
                try:
                    state = torch.load(model_path, map_location="cpu")
                    self._net.load_state_dict(state)
                    logger.info("MLP: loaded weights from %s", model_path)
                except Exception as e:
                    logger.warning("MLP: failed to load weights: %s", e)

    @property
    def name(self) -> str:
        return "mlp"

    @property
    def description(self) -> str:
        return "4-layer MLP with batch norm & dropout (PyTorch)."

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
