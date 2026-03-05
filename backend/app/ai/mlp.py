"""Deep MLP surrogate model with residual connections (Model B)."""
import os
import structlog
import numpy as np

from app.ai.base import BaseSurrogate

log = structlog.get_logger()

N_FEATURES = 31
N_OUTPUTS = 6


def _build_mlp():
    """Build the MLP architecture.  Import torch lazily so the backend starts
    even when PyTorch is not installed."""
    import torch
    import torch.nn as nn

    class ResidualBlock(nn.Module):
        def __init__(self, in_dim: int, out_dim: int, dropout: float = 0.2):
            super().__init__()
            self.linear = nn.Linear(in_dim, out_dim)
            self.bn = nn.BatchNorm1d(out_dim)
            self.act = nn.GELU()
            self.drop = nn.Dropout(dropout)
            self.skip = nn.Linear(in_dim, out_dim) if in_dim != out_dim else nn.Identity()

        def forward(self, x):
            return self.act(self.bn(self.linear(x))) + self.skip(x)

    class MLPSurrogateNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = nn.Sequential(
                ResidualBlock(N_FEATURES, 256),
                self.drop(0.2),
                ResidualBlock(256, 512),
                self.drop(0.2),
                ResidualBlock(512, 256),
                self.drop(0.2),
                ResidualBlock(256, 128),
            )
            self.head = nn.Linear(128, N_OUTPUTS)

        @staticmethod
        def drop(p):
            return nn.Dropout(p)

        def forward(self, x):
            return self.head(self.layers(x))

    return MLPSurrogateNet()


# Rebuild using a cleaner sequential approach compatible with torch.nn
def _build_mlp_clean():
    import torch.nn as nn

    class ResBlock(nn.Module):
        def __init__(self, in_d: int, out_d: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(in_d, out_d),
                nn.BatchNorm1d(out_d),
                nn.GELU(),
                nn.Dropout(0.2),
            )
            self.skip = nn.Linear(in_d, out_d) if in_d != out_d else nn.Identity()

        def forward(self, x):
            return self.net(x) + self.skip(x)

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Sequential(
                ResBlock(N_FEATURES, 256),
                ResBlock(256, 512),
                ResBlock(512, 256),
                ResBlock(256, 128),
            )
            self.head = nn.Linear(128, N_OUTPUTS)

        def forward(self, x):
            return self.head(self.encoder(x))

    return Net()


class MLPSurrogate(BaseSurrogate):
    """Deep MLP surrogate: 4-layer with residual connections."""

    def __init__(self, model_path: str):
        self._path = model_path
        self._net = None
        self._scaler_mean = None
        self._scaler_std = None

    def name(self) -> str:
        return "mlp"

    def load(self) -> None:
        if not os.path.exists(self._path):
            log.warning("mlp_model_not_found", path=self._path)
            return
        try:
            import torch

            checkpoint = torch.load(self._path, map_location="cpu", weights_only=False)
            net = _build_mlp_clean()
            net.load_state_dict(checkpoint["model_state"])
            net.eval()
            self._net = net
            self._scaler_mean = checkpoint.get("scaler_mean")
            self._scaler_std = checkpoint.get("scaler_std")
            log.info("mlp_model_loaded", path=self._path)
        except Exception as exc:
            log.error("mlp_model_load_error", path=self._path, error=str(exc))

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self._net is None:
            raise RuntimeError("MLP model not loaded")
        import torch

        x = features.astype(np.float32)
        if self._scaler_mean is not None and self._scaler_std is not None:
            x = (x - self._scaler_mean) / (self._scaler_std + 1e-8)
        with torch.no_grad():
            out = self._net(torch.from_numpy(x))
        return out.numpy().astype(np.float64).flatten()

    def is_loaded(self) -> bool:
        return self._net is not None

    def metadata(self) -> dict:
        return {
            "type": "DeepMLP",
            "architecture": "[31]->256->512->256->128->[6]",
            "activations": "GELU",
            "residual": True,
            "path": self._path,
        }
