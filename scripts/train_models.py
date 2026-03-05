#!/usr/bin/env python3
"""
train_models.py — Unified training script for all surrogate models.

Trains RF, MLP, PINN, DeepONet, FNO models from the same dataset.
Produces:
  - sample_data/topological_v3_model.pkl     (RandomForest, sklearn)
  - sample_data/mlp_model.pt                 (MLP, PyTorch)
  - sample_data/pinn_model.pt                (PINN, PyTorch)
  - sample_data/deeponet_model.pt            (DeepONet, PyTorch)
  - sample_data/fno_model.pt                 (FNO, PyTorch)
  - sample_data/model_leaderboard.json       (comparison metrics)
"""
import argparse
import json
import math
import os
import pickle
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler

TARGET_COLS = ["vout", "iin", "efficiency", "rise_time", "settling_time", "overshoot"]
N_FEATURES = 31  # 10 stages × 3 features + log_freq
INPUT_DIM = N_FEATURES
OUTPUT_DIM = len(TARGET_COLS)
RANDOM_SEED = 42


# ── helpers ──────────────────────────────────────────────────────────────────

def load_dataset(data_path: str) -> Tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(data_path)
    y = df[TARGET_COLS].values
    X = df.drop(columns=TARGET_COLS).values
    return X.astype(np.float32), y.astype(np.float32)


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    metrics = {}
    for i, col in enumerate(TARGET_COLS):
        mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
        r2 = r2_score(y_true[:, i], y_pred[:, i])
        metrics[col] = {"mae": float(mae), "r2": float(r2)}
    return metrics


# ── Random Forest ─────────────────────────────────────────────────────────────

def train_random_forest(X_train, y_train, X_test, y_test, model_dir: str):
    print("\n[RF] Training RandomForest...")
    t0 = time.time()
    base = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=RANDOM_SEED, n_jobs=-1)
    model = MultiOutputRegressor(base)
    model.fit(X_train, y_train)
    elapsed = time.time() - t0

    y_pred = model.predict(X_test)
    metrics = evaluate(y_test, y_pred)
    print(f"  Trained in {elapsed:.1f}s  |  Vout R²={metrics['vout']['r2']:.4f}")

    path = os.path.join(model_dir, "topological_v3_model.pkl")
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"  Saved → {path}")
    return metrics, elapsed


# ── PyTorch helpers ───────────────────────────────────────────────────────────

def _torch_available() -> bool:
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


def _train_torch_model(model_class, X_train, y_train, X_test, y_test,
                        model_dir: str, filename: str,
                        epochs: int = 100, lr: float = 3e-3, batch_size: int = 512):
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_tr = torch.tensor(X_train, dtype=torch.float32)
    y_tr = torch.tensor(y_train, dtype=torch.float32)
    X_te = torch.tensor(X_test, dtype=torch.float32)
    y_te = torch.tensor(y_test, dtype=torch.float32)

    ds = TensorDataset(X_tr, y_tr)
    dl = DataLoader(ds, batch_size=batch_size, shuffle=True)

    net = model_class(INPUT_DIM, OUTPUT_DIM).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    loss_fn = nn.MSELoss()

    t0 = time.time()
    for epoch in range(epochs):
        net.train()
        for xb, yb in dl:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            pred = net(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()
        sched.step()
        if (epoch + 1) % 20 == 0:
            net.eval()
            with torch.no_grad():
                val_loss = loss_fn(net(X_te.to(device)), y_te.to(device)).item()
            print(f"    Epoch {epoch+1}/{epochs}  val_loss={val_loss:.6f}")

    elapsed = time.time() - t0
    net.eval()
    with torch.no_grad():
        y_pred = net(X_te.to(device)).cpu().numpy()
    metrics = evaluate(y_test, y_pred)

    path = os.path.join(model_dir, filename)
    torch.save(net.state_dict(), path)
    print(f"  Trained in {elapsed:.1f}s  |  Vout R²={metrics['vout']['r2']:.4f}")
    print(f"  Saved → {path}")
    return metrics, elapsed


# ── MLP ───────────────────────────────────────────────────────────────────────

def _make_mlp_class():
    import torch.nn as nn

    class MLP(nn.Module):
        def __init__(self, in_dim, out_dim):
            super().__init__()
            hidden = 256
            self.net = nn.Sequential(
                nn.Linear(in_dim, hidden), nn.BatchNorm1d(hidden), nn.GELU(), nn.Dropout(0.1),
                nn.Linear(hidden, hidden), nn.BatchNorm1d(hidden), nn.GELU(), nn.Dropout(0.1),
                nn.Linear(hidden, hidden), nn.BatchNorm1d(hidden), nn.GELU(), nn.Dropout(0.1),
                nn.Linear(hidden, out_dim),
            )
            self.skip = nn.Linear(in_dim, out_dim)

        def forward(self, x):
            return self.net(x) + self.skip(x)

    return MLP


# ── PINN ──────────────────────────────────────────────────────────────────────

def _make_pinn_class():
    import torch
    import torch.nn as nn

    class PINN(nn.Module):
        def __init__(self, in_dim, out_dim):
            super().__init__()
            hidden = 256
            self.shared = nn.Sequential(
                nn.Linear(in_dim, hidden), nn.Tanh(),
                nn.Linear(hidden, hidden), nn.Tanh(),
                nn.Linear(hidden, hidden), nn.Tanh(),
            )
            self.head = nn.Linear(hidden, out_dim)

        def forward(self, x):
            h = self.shared(x)
            out = self.head(h)
            # Enforce Vout ≤ Vin (passivity): vout index 0 ∈ [0,1]
            out = out.clone()
            out[:, 0] = torch.sigmoid(out[:, 0])
            return out

    return PINN


# ── DeepONet ──────────────────────────────────────────────────────────────────

def _make_deeponet_class():
    import torch.nn as nn

    class DeepONet(nn.Module):
        """Simplified DeepONet: branch encodes topology, trunk encodes frequency."""
        def __init__(self, in_dim, out_dim):
            super().__init__()
            topo_dim = in_dim - 1  # all but log_freq
            freq_dim = 1
            latent = 128

            self.branch = nn.Sequential(
                nn.Linear(topo_dim, 256), nn.ReLU(),
                nn.Linear(256, latent), nn.ReLU(),
            )
            self.trunk = nn.Sequential(
                nn.Linear(freq_dim, 64), nn.ReLU(),
                nn.Linear(64, latent), nn.ReLU(),
            )
            self.out = nn.Linear(latent, out_dim)

        def forward(self, x):
            topo = x[:, :-1]
            freq = x[:, -1:]
            b = self.branch(topo)
            t = self.trunk(freq)
            return self.out(b * t)

    return DeepONet


# ── FNO ───────────────────────────────────────────────────────────────────────

def _make_fno_class():
    import torch
    import torch.nn as nn

    class SpectralConv1d(nn.Module):
        def __init__(self, in_ch, out_ch, modes):
            super().__init__()
            self.modes = modes
            scale = 1 / (in_ch * out_ch)
            self.W = nn.Parameter(scale * torch.rand(in_ch, out_ch, modes, dtype=torch.cfloat))

        def forward(self, x):
            # x: (B, C, L)
            x_ft = torch.fft.rfft(x, dim=-1)
            out_ft = torch.zeros_like(x_ft)
            m = min(self.modes, x_ft.shape[-1])
            out_ft[:, :self.W.shape[1], :m] = torch.einsum(
                "bcl,col->bol", x_ft[:, :, :m], self.W[:, :, :m]
            )
            return torch.fft.irfft(out_ft, n=x.shape[-1], dim=-1)

    class FNO(nn.Module):
        """1D FNO treating the feature vector as a 1D signal."""
        def __init__(self, in_dim, out_dim, modes=8, width=32):
            super().__init__()
            self.lift = nn.Linear(1, width)
            self.convs = nn.ModuleList([SpectralConv1d(width, width, modes) for _ in range(4)])
            self.ws = nn.ModuleList([nn.Conv1d(width, width, 1) for _ in range(4)])
            self.proj1 = nn.Linear(width * in_dim, 128)
            self.proj2 = nn.Linear(128, out_dim)
            self.act = nn.GELU()

        def forward(self, x):
            # x: (B, L) — treat L features as sequence length
            x = x.unsqueeze(-1)           # (B, L, 1)
            x = self.lift(x)              # (B, L, W)
            x = x.permute(0, 2, 1)       # (B, W, L)
            for conv, w in zip(self.convs, self.ws):
                x = self.act(conv(x) + w(x))
            x = x.reshape(x.shape[0], -1)  # (B, W*L)
            return self.proj2(self.act(self.proj1(x)))

    return FNO


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Train all surrogate models")
    parser.add_argument("--data", default="sample_data/topological_v3_dataset.csv",
                        help="Path to training dataset CSV")
    parser.add_argument("--model-dir", default="sample_data", help="Directory to save models")
    parser.add_argument("--epochs", type=int, default=100, help="PyTorch training epochs")
    parser.add_argument("--skip-torch", action="store_true", help="Skip PyTorch models")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"Dataset not found at {args.data}. Run generate_dataset_v4.py first.")
        return

    os.makedirs(args.model_dir, exist_ok=True)
    X, y = load_dataset(args.data)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=RANDOM_SEED)

    # Normalize targets
    scaler = StandardScaler()
    y_train_s = scaler.fit_transform(y_train)
    y_test_s = scaler.transform(y_test)

    leaderboard = {}

    # Train RF
    rf_metrics, rf_time = train_random_forest(X_train, y_train, X_test, y_test, args.model_dir)
    leaderboard["random_forest"] = {"metrics": rf_metrics, "train_time_s": rf_time}

    if not args.skip_torch and _torch_available():
        torch_configs = [
            ("MLP", _make_mlp_class(), "mlp_model.pt"),
            ("PINN", _make_pinn_class(), "pinn_model.pt"),
            ("DeepONet", _make_deeponet_class(), "deeponet_model.pt"),
            ("FNO", _make_fno_class(), "fno_model.pt"),
        ]
        for name, cls, fname in torch_configs:
            print(f"\n[{name}] Training...")
            try:
                metrics, elapsed = _train_torch_model(
                    cls, X_train, y_train_s, X_test, y_test_s,
                    args.model_dir, fname, epochs=args.epochs
                )
                leaderboard[name.lower()] = {"metrics": metrics, "train_time_s": elapsed}
            except Exception as e:
                print(f"  !! {name} training failed: {e}")
    else:
        if args.skip_torch:
            print("\n[INFO] Skipping PyTorch models (--skip-torch).")
        else:
            print("\n[INFO] PyTorch not available; skipping neural models.")

    # Save leaderboard
    lb_path = os.path.join(args.model_dir, "model_leaderboard.json")
    with open(lb_path, "w") as f:
        json.dump(leaderboard, f, indent=2)
    print(f"\nLeaderboard saved → {lb_path}")

    # Print summary table
    print("\n{'='*60}")
    print(f"{'Model':<15} {'Vout R²':>10} {'Vout MAE':>12} {'Time (s)':>10}")
    print("-" * 60)
    for model, info in leaderboard.items():
        r2 = info["metrics"].get("vout", {}).get("r2", float("nan"))
        mae = info["metrics"].get("vout", {}).get("mae", float("nan"))
        t = info["train_time_s"]
        print(f"{model:<15} {r2:>10.4f} {mae:>12.6f} {t:>10.1f}")


if __name__ == "__main__":
    main()
