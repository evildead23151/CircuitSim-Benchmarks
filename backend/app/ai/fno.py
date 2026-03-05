"""Fourier Neural Operator (FNO-1D) surrogate (Model E)."""
import os
import structlog
import numpy as np

from app.ai.base import BaseSurrogate

log = structlog.get_logger()

N_STAGES = 10
N_CHANNELS = 3   # tag, type, log_val
N_MODES = 8
WIDTH = 64
N_OUTPUTS = 6


def _build_fno():
    import torch
    import torch.nn as nn
    import torch.fft

    class SpectralConv1d(nn.Module):
        """Single Fourier layer: FFT → truncate → linear in freq domain → IFFT + bypass."""

        def __init__(self, in_channels: int, out_channels: int, modes: int):
            super().__init__()
            self.modes = modes
            self.scale = 1 / (in_channels * out_channels)
            self.weights = nn.Parameter(
                self.scale * torch.rand(in_channels, out_channels, modes, dtype=torch.cfloat)
            )

        def compl_mul1d(self, x, w):
            return torch.einsum("bim,iom->bom", x, w)

        def forward(self, x):
            # x: (batch, channels, length)
            B, C, L = x.shape
            x_ft = torch.fft.rfft(x)
            out_ft = torch.zeros(B, self.weights.shape[1], x_ft.shape[-1],
                                 dtype=torch.cfloat, device=x.device)
            out_ft[:, :, :self.modes] = self.compl_mul1d(x_ft[:, :, :self.modes], self.weights)
            return torch.fft.irfft(out_ft, n=L)

    class FNOBlock(nn.Module):
        def __init__(self, width: int, modes: int):
            super().__init__()
            self.spectral = SpectralConv1d(width, width, modes)
            self.bypass = nn.Conv1d(width, width, 1)
            self.bn = nn.BatchNorm1d(width)
            self.act = nn.GELU()

        def forward(self, x):
            return self.act(self.bn(self.spectral(x) + self.bypass(x)))

    class FNO1d(nn.Module):
        def __init__(self):
            super().__init__()
            self.lift = nn.Conv1d(N_CHANNELS, WIDTH, 1)
            self.blocks = nn.Sequential(
                FNOBlock(WIDTH, N_MODES),
                FNOBlock(WIDTH, N_MODES),
                FNOBlock(WIDTH, N_MODES),
                FNOBlock(WIDTH, N_MODES),
            )
            # After global avg pool: WIDTH features + 1 log_freq
            self.head = nn.Sequential(
                nn.Linear(WIDTH + 1, 128),
                nn.GELU(),
                nn.Linear(128, N_OUTPUTS),
            )

        def forward(self, x_seq, log_freq):
            # x_seq: (batch, N_STAGES, N_CHANNELS) → transpose to (batch, N_CHANNELS, N_STAGES)
            x = x_seq.permute(0, 2, 1)
            x = self.lift(x)
            x = self.blocks(x)
            x = x.mean(dim=-1)  # global average pool → (batch, WIDTH)
            x = torch.cat([x, log_freq], dim=-1)
            return self.head(x)

    return FNO1d()


class FNOSurrogate(BaseSurrogate):
    """Fourier Neural Operator 1D surrogate."""

    def __init__(self, model_path: str):
        self._path = model_path
        self._net = None

    def name(self) -> str:
        return "fno"

    def load(self) -> None:
        if not os.path.exists(self._path):
            log.warning("fno_model_not_found", path=self._path)
            return
        try:
            import torch

            checkpoint = torch.load(self._path, map_location="cpu", weights_only=False)
            net = _build_fno()
            net.load_state_dict(checkpoint["model_state"])
            net.eval()
            self._net = net
            log.info("fno_model_loaded", path=self._path)
        except Exception as exc:
            log.error("fno_model_load_error", path=self._path, error=str(exc))

    def predict(self, features: np.ndarray) -> np.ndarray:
        """features: (1, 31) — first 30 are stage features, last is log_freq."""
        if self._net is None:
            raise RuntimeError("FNO model not loaded")
        import torch

        x = features.astype(np.float32)
        stage_feats = x[:, :30].reshape(1, N_STAGES, N_CHANNELS)  # (1, 10, 3)
        log_freq = x[:, 30:31]  # (1, 1)

        with torch.no_grad():
            out = self._net(
                torch.from_numpy(stage_feats),
                torch.from_numpy(log_freq),
            )
        return out.numpy().astype(np.float64).flatten()

    def is_loaded(self) -> bool:
        return self._net is not None

    def metadata(self) -> dict:
        return {
            "type": "FNO-1D",
            "n_fourier_layers": 4,
            "modes": N_MODES,
            "width": WIDTH,
            "input_channels": N_CHANNELS,
            "sequence_length": N_STAGES,
            "path": self._path,
        }
