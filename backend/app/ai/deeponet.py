"""Deep Operator Network (DeepONet) surrogate (Model D)."""
import os
import structlog
import numpy as np

from app.ai.base import BaseSurrogate

log = structlog.get_logger()

N_BRANCH = 30  # 10 stages × 3 features
N_TRUNK = 1    # log10(frequency)
P = 64         # basis dimension
N_OUTPUTS = 6


def _build_deeponet():
    import torch.nn as nn

    class BranchNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(N_BRANCH, 128),
                nn.BatchNorm1d(128),
                nn.GELU(),
                nn.Linear(128, 128),
                nn.BatchNorm1d(128),
                nn.GELU(),
                nn.Linear(128, P),
            )

        def forward(self, x):
            return self.net(x)

    class TrunkNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(N_TRUNK, 64),
                nn.BatchNorm1d(64),
                nn.GELU(),
                nn.Linear(64, 64),
                nn.BatchNorm1d(64),
                nn.GELU(),
                nn.Linear(64, P),
            )

        def forward(self, x):
            return self.net(x)

    class DeepONet(nn.Module):
        def __init__(self):
            super().__init__()
            self.branch = BranchNet()
            self.trunk = TrunkNet()
            # One output head per target
            self.heads = nn.ModuleList([nn.Linear(P, 1) for _ in range(N_OUTPUTS)])

        def forward(self, branch_input, trunk_input):
            b = self.branch(branch_input)   # (batch, P)
            t = self.trunk(trunk_input)     # (batch, P)
            dot = b * t                     # element-wise product
            out = torch.stack([h(dot).squeeze(-1) for h in self.heads], dim=-1)
            return out                      # (batch, N_OUTPUTS)

    import torch  # noqa: F401 — needed for the forward pass
    return DeepONet()


class DeepONetSurrogate(BaseSurrogate):
    """Deep Operator Network surrogate."""

    def __init__(self, model_path: str):
        self._path = model_path
        self._net = None
        self._scaler_mean = None
        self._scaler_std = None

    def name(self) -> str:
        return "deeponet"

    def load(self) -> None:
        if not os.path.exists(self._path):
            log.warning("deeponet_model_not_found", path=self._path)
            return
        try:
            import torch

            checkpoint = torch.load(self._path, map_location="cpu", weights_only=False)
            net = _build_deeponet()
            net.load_state_dict(checkpoint["model_state"])
            net.eval()
            self._net = net
            self._scaler_mean = checkpoint.get("scaler_mean")
            self._scaler_std = checkpoint.get("scaler_std")
            log.info("deeponet_model_loaded", path=self._path)
        except Exception as exc:
            log.error("deeponet_model_load_error", path=self._path, error=str(exc))

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self._net is None:
            raise RuntimeError("DeepONet model not loaded")
        import torch

        x = features.astype(np.float32)
        if self._scaler_mean is not None and self._scaler_std is not None:
            x = (x - self._scaler_mean) / (self._scaler_std + 1e-8)

        # Branch: first 30 features; Trunk: last 1 feature (log_freq)
        branch_in = torch.from_numpy(x[:, :N_BRANCH])
        trunk_in = torch.from_numpy(x[:, N_BRANCH:])
        with torch.no_grad():
            out = self._net(branch_in, trunk_in)
        return out.numpy().astype(np.float64).flatten()

    def is_loaded(self) -> bool:
        return self._net is not None

    def metadata(self) -> dict:
        return {
            "type": "DeepONet",
            "branch_net": "[30]->128->128->64",
            "trunk_net": "[1]->64->64->64",
            "basis_dim": P,
            "n_outputs": N_OUTPUTS,
            "path": self._path,
        }
