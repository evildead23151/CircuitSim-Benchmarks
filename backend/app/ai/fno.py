import logging
import numpy as np
from .base import BaseSurrogate

logger = logging.getLogger(__name__)

_TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    import torch.fft
    _TORCH_AVAILABLE = True
except ImportError:
    pass

_BASE_CLASS = nn.Module if _TORCH_AVAILABLE else object


class SpectralConv1d(_BASE_CLASS):
    """1-D Fourier layer."""

    def __init__(self, in_ch: int, out_ch: int, modes: int):
        if _TORCH_AVAILABLE:
            super().__init__()
            import torch
            self.modes = modes
            scale = 1 / (in_ch * out_ch)
            self.weights = nn.Parameter(
                scale * torch.rand(in_ch, out_ch, modes, dtype=torch.cfloat)
            )

    def forward(self, x):
        import torch
        B, C, N = x.shape
        x_ft = torch.fft.rfft(x)
        out_ft = torch.zeros(B, self.weights.shape[1], x_ft.shape[-1], dtype=torch.cfloat, device=x.device)
        modes = min(self.modes, x_ft.shape[-1])
        out_ft[:, :, :modes] = torch.einsum("bci,coi->boi", x_ft[:, :, :modes], self.weights[:, :, :modes])
        return torch.fft.irfft(out_ft, n=N)


class FNOSurrogate(BaseSurrogate):
    """1-D Fourier Neural Operator surrogate."""
    SEQ_LEN = 31
    CHANNELS = 16
    MODES = 8
    OUTPUT_DIM = 6

    def __init__(self):
        self._lift = None
        self._spectral = None
        self._w = None
        self._proj = None
        if _TORCH_AVAILABLE:
            import torch.nn as nn
            self._lift = nn.Linear(1, self.CHANNELS)
            self._spectral = SpectralConv1d(self.CHANNELS, self.CHANNELS, self.MODES)
            self._w = nn.Linear(self.CHANNELS, self.CHANNELS)
            self._proj = nn.Sequential(
                nn.Linear(self.CHANNELS * self.SEQ_LEN, 128),
                nn.ReLU(),
                nn.Linear(128, self.OUTPUT_DIM),
            )

    @property
    def name(self) -> str:
        return "fno"

    @property
    def description(self) -> str:
        return "1-D Fourier Neural Operator for circuit response prediction."

    @property
    def is_available(self) -> bool:
        return _TORCH_AVAILABLE

    def predict(self, features: np.ndarray) -> np.ndarray:
        if not _TORCH_AVAILABLE or self._lift is None:
            return np.zeros(self.OUTPUT_DIM)
        import torch
        x = torch.tensor(features.flatten(), dtype=torch.float32)
        x = x.unsqueeze(0).unsqueeze(-1)  # (1, SEQ_LEN, 1)
        with torch.no_grad():
            x = self._lift(x)            # (1, SEQ_LEN, CHANNELS)
            x = x.permute(0, 2, 1)      # (1, CHANNELS, SEQ_LEN)
            x = self._spectral(x) + self._w(x.permute(0, 2, 1)).permute(0, 2, 1)
            x = x.reshape(1, -1)
            out = self._proj(x)
        return out.numpy().flatten()
