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


def _mlp_block(in_dim, out_dim):
    if not _TORCH_AVAILABLE:
        return None
    import torch.nn as nn
    return nn.Sequential(nn.Linear(in_dim, out_dim), nn.ReLU())


class DeepONetSurrogate(BaseSurrogate):
    """
    Simplified Deep Operator Network: branch net (circuit params) + trunk net (frequency).
    """
    BRANCH_DIM = 30   # 10 stages × 3 features
    TRUNK_DIM = 1     # log10(frequency)
    HIDDEN = 64
    OUTPUT_DIM = 6

    def __init__(self):
        self._branch = None
        self._trunk = None
        self._head = None
        if _TORCH_AVAILABLE:
            import torch.nn as nn
            self._branch = nn.Sequential(
                nn.Linear(self.BRANCH_DIM, self.HIDDEN), nn.ReLU(),
                nn.Linear(self.HIDDEN, self.HIDDEN), nn.ReLU(),
            )
            self._trunk = nn.Sequential(
                nn.Linear(self.TRUNK_DIM, self.HIDDEN), nn.ReLU(),
                nn.Linear(self.HIDDEN, self.HIDDEN), nn.ReLU(),
            )
            self._head = nn.Linear(self.HIDDEN, self.OUTPUT_DIM)

    @property
    def name(self) -> str:
        return "deeponet"

    @property
    def description(self) -> str:
        return "Deep Operator Network with branch (circuit) + trunk (frequency) nets."

    @property
    def is_available(self) -> bool:
        return _TORCH_AVAILABLE

    def predict(self, features: np.ndarray) -> np.ndarray:
        if not _TORCH_AVAILABLE or self._branch is None:
            return np.zeros(self.OUTPUT_DIM)
        import torch
        arr = features.flatten()
        branch_in = torch.tensor(arr[:self.BRANCH_DIM], dtype=torch.float32).unsqueeze(0)
        trunk_in = torch.tensor([[arr[-1]]], dtype=torch.float32)
        with torch.no_grad():
            b = self._branch(branch_in)
            t = self._trunk(trunk_in)
            combined = b * t
            out = self._head(combined)
        return out.numpy().flatten()
