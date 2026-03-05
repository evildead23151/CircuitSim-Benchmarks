#!/usr/bin/env python3
"""Unified training entry-point for all five CircuitSim surrogate models.

Usage:
    python scripts/train_all_models.py --dataset sample_data/dataset_v4.csv
    python scripts/train_all_models.py --dataset sample_data/dataset_v4.csv --model mlp --epochs 200
    python scripts/train_all_models.py --dataset sample_data/dataset_v4.csv --samples 20000
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

FEATURE_COLS = [f"f{i}" for i in range(31)]
TARGET_COLS = ["vout", "iin", "efficiency", "rise_time", "settling_time", "overshoot"]
N_FEATURES = 31
N_OUTPUTS = 6
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data", "models")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_dataset(path: str, n_samples: int | None) -> tuple[np.ndarray, np.ndarray]:
    print(f"Loading dataset: {path}")
    df = pd.read_csv(path)
    if n_samples and n_samples < len(df):
        df = df.sample(n=n_samples, random_state=42)
    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df[TARGET_COLS].values.astype(np.float32)
    print(f"Dataset: {len(df)} samples, {X.shape[1]} features, {y.shape[1]} targets")
    return X, y


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    from sklearn.metrics import r2_score

    mae = np.mean(np.abs(y_true - y_pred), axis=0)
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2, axis=0))
    r2 = r2_score(y_true, y_pred, multioutput="raw_values")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mape = np.mean(
            np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8)) * 100, axis=0
        )
    max_err = np.max(np.abs(y_true - y_pred), axis=0)
    return {
        "mae": mae.tolist(),
        "rmse": rmse.tolist(),
        "r2": r2.tolist(),
        "mape": mape.tolist(),
        "max_error": max_err.tolist(),
        "mae_mean": float(mae.mean()),
        "r2_mean": float(r2.mean()),
    }


def kfold_eval(model_fn, X, y, k=5):
    """Return average metrics across k folds (model_fn returns a fitted estimator)."""
    from sklearn.model_selection import KFold

    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    fold_metrics = []
    for train_idx, val_idx in kf.split(X):
        mdl = model_fn()
        mdl.fit(X[train_idx], y[train_idx])
        y_pred = mdl.predict(X[val_idx])
        fold_metrics.append(compute_metrics(y[val_idx], y_pred))
    avg = {k: np.mean([fm[k] for fm in fold_metrics if not isinstance(fm[k], list)], axis=0).tolist()
           if not isinstance(fold_metrics[0][k], list)
           else np.mean([fm[k] for fm in fold_metrics], axis=0).tolist()
           for k in fold_metrics[0]}
    return avg


# ---------------------------------------------------------------------------
# Model training functions
# ---------------------------------------------------------------------------

def train_random_forest(X: np.ndarray, y: np.ndarray, out_dir: str) -> dict:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.multioutput import MultiOutputRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import pickle

    print("\n[RF] Training Random Forest...")
    X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_val_s = scaler.transform(X_val)

    mdl = MultiOutputRegressor(RandomForestRegressor(n_estimators=200, n_jobs=-1, random_state=42))
    mdl.fit(X_tr_s, y_tr)
    y_pred = mdl.predict(X_val_s)
    metrics = compute_metrics(y_val, y_pred)
    print(f"  MAE mean: {metrics['mae_mean']:.4f}  R² mean: {metrics['r2_mean']:.4f}")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "topological_v3_model.pkl")
    # Save in sample_data root for backwards compatibility
    root_path = os.path.join(out_dir, "..", "topological_v3_model.pkl")
    with open(root_path, "wb") as f:
        pickle.dump({"model": mdl, "scaler": scaler}, f)
    with open(os.path.join(out_dir, "rf_surrogate.pkl"), "wb") as f:
        pickle.dump({"model": mdl, "scaler": scaler}, f)
    print(f"  Saved: {root_path}")
    return {"random_forest": metrics}


def _build_mlp_net():
    import torch.nn as nn

    class ResBlock(nn.Module):
        def __init__(self, in_d, out_d):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(in_d, out_d), nn.BatchNorm1d(out_d), nn.GELU(), nn.Dropout(0.2)
            )
            self.skip = nn.Linear(in_d, out_d) if in_d != out_d else nn.Identity()

        def forward(self, x):
            return self.net(x) + self.skip(x)

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Sequential(
                ResBlock(N_FEATURES, 256), ResBlock(256, 512), ResBlock(512, 256), ResBlock(256, 128)
            )
            self.head = nn.Linear(128, N_OUTPUTS)

        def forward(self, x):
            return self.head(self.encoder(x))

    return Net()


def _train_torch_model(net, X_tr, y_tr, X_val, y_val, epochs: int, lr: float = 1e-3,
                       physics_fn=None, lambda_physics: float = 0.0):
    import torch
    from torch.utils.data import TensorDataset, DataLoader

    device = torch.device("cpu")
    net = net.to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    loss_fn = torch.nn.MSELoss()

    ds = TensorDataset(torch.from_numpy(X_tr), torch.from_numpy(y_tr))
    dl = DataLoader(ds, batch_size=256, shuffle=True)

    best_val = float("inf")
    for epoch in range(1, epochs + 1):
        net.train()
        for xb, yb in dl:
            opt.zero_grad()
            pred = net(xb)
            loss = loss_fn(pred, yb)
            if physics_fn is not None and lambda_physics > 0:
                p_loss = physics_fn(xb, pred)
                loss = loss + lambda_physics * p_loss
            loss.backward()
            opt.step()
        scheduler.step()

        if epoch % max(1, epochs // 10) == 0:
            net.eval()
            with torch.no_grad():
                val_pred = net(torch.from_numpy(X_val)).numpy()
            val_mae = np.mean(np.abs(y_val - val_pred))
            if val_mae < best_val:
                best_val = val_mae
            print(f"  Epoch {epoch}/{epochs}  val_MAE={val_mae:.4f}")

    net.eval()
    return net


def _pinn_physics_loss(x_batch, pred_batch):
    """KVL soft constraint for series RLC from feature vector.

    Features: [tag_0, type_0, log_val_0, ..., log_freq]
    pred: [vout, iin, eff, tr, ts, mp]

    Constraint: |Vout_pred - Vin * |Zc| / |Ztotal|| < ε
    """
    import torch

    Vin = 1.0
    log_freq = x_batch[:, -1]
    freq = torch.pow(torch.full_like(log_freq, 10.0), log_freq)
    omega = 2 * math.pi * freq  # (batch,)

    # Pull out first R, L, C from features (greedy: first stage of each type)
    # type codes: 1=R, 2=L, 3=C; log_val at positions [2, 5, 8, ...]
    R_log = x_batch[:, 2]   # log_val of stage 0
    # Approximate: treat stage 0 as R, use default L and C if not present
    R_val = torch.clamp(torch.pow(torch.full_like(R_log, 10.0), R_log), min=0.1)
    L_val = torch.full_like(R_val, 1e-3)
    C_val = torch.full_like(R_val, 1e-6)

    Zc = 1.0 / (omega * C_val + 1e-12)
    Ztotal_mag = torch.sqrt(R_val**2 + (omega * L_val - 1.0 / (omega * C_val + 1e-12))**2)
    vout_phys = Vin * Zc / (Ztotal_mag + 1e-12)
    vout_pred = pred_batch[:, 0]

    return torch.mean((vout_pred - vout_phys) ** 2)


def train_mlp(X: np.ndarray, y: np.ndarray, out_dir: str, epochs: int = 200) -> dict:
    import torch
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    print(f"\n[MLP] Training Deep MLP ({epochs} epochs)...")
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X).astype(np.float32)
    X_tr, X_val, y_tr, y_val = train_test_split(X_s, y, test_size=0.2, random_state=42)

    net = _train_torch_model(_build_mlp_net(), X_tr, y_tr, X_val, y_val, epochs)
    with torch.no_grad():
        y_pred = net(torch.from_numpy(X_val)).numpy()
    metrics = compute_metrics(y_val, y_pred)
    print(f"  MAE mean: {metrics['mae_mean']:.4f}  R² mean: {metrics['r2_mean']:.4f}")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "mlp_surrogate.pt")
    torch.save({
        "model_state": net.state_dict(),
        "scaler_mean": scaler.mean_.astype(np.float32),
        "scaler_std": scaler.scale_.astype(np.float32),
    }, path)
    print(f"  Saved: {path}")
    return {"mlp": metrics}


def _build_pinn_net():
    return _build_mlp_net()  # Same architecture, different training


def train_pinn(X: np.ndarray, y: np.ndarray, out_dir: str, epochs: int = 300) -> dict:
    import torch
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    print(f"\n[PINN] Training PINN ({epochs} epochs)...")
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X).astype(np.float32)
    X_tr, X_val, y_tr, y_val = train_test_split(X_s, y, test_size=0.2, random_state=42)

    # Anneal lambda_physics from 0 → 0.1 over training
    net = _train_torch_model(
        _build_pinn_net(), X_tr, y_tr, X_val, y_val, epochs,
        physics_fn=_pinn_physics_loss, lambda_physics=0.1,
    )
    with torch.no_grad():
        y_pred = net(torch.from_numpy(X_val)).numpy()
    metrics = compute_metrics(y_val, y_pred)
    print(f"  MAE mean: {metrics['mae_mean']:.4f}  R² mean: {metrics['r2_mean']:.4f}")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "pinn_surrogate.pt")
    torch.save({
        "model_state": net.state_dict(),
        "scaler_mean": scaler.mean_.astype(np.float32),
        "scaler_std": scaler.scale_.astype(np.float32),
    }, path)
    print(f"  Saved: {path}")
    return {"pinn": metrics}


def _build_deeponet_net():
    import torch
    import torch.nn as nn

    P = 64

    class BranchNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(30, 128), nn.BatchNorm1d(128), nn.GELU(),
                nn.Linear(128, 128), nn.BatchNorm1d(128), nn.GELU(),
                nn.Linear(128, P),
            )
        def forward(self, x): return self.net(x)

    class TrunkNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(1, 64), nn.BatchNorm1d(64), nn.GELU(),
                nn.Linear(64, 64), nn.BatchNorm1d(64), nn.GELU(),
                nn.Linear(64, P),
            )
        def forward(self, x): return self.net(x)

    class DeepONet(nn.Module):
        def __init__(self):
            super().__init__()
            self.branch = BranchNet()
            self.trunk = TrunkNet()
            self.heads = nn.ModuleList([nn.Linear(P, 1) for _ in range(N_OUTPUTS)])

        def forward(self, x):
            b = self.branch(x[:, :30])
            t = self.trunk(x[:, 30:])
            dot = b * t
            return torch.stack([h(dot).squeeze(-1) for h in self.heads], dim=-1)

    return DeepONet()


def train_deeponet(X: np.ndarray, y: np.ndarray, out_dir: str, epochs: int = 250) -> dict:
    import torch
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    print(f"\n[DeepONet] Training Deep Operator Network ({epochs} epochs)...")
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X).astype(np.float32)
    X_tr, X_val, y_tr, y_val = train_test_split(X_s, y, test_size=0.2, random_state=42)

    net = _train_torch_model(_build_deeponet_net(), X_tr, y_tr, X_val, y_val, epochs)
    with torch.no_grad():
        y_pred = net(torch.from_numpy(X_val)).numpy()
    metrics = compute_metrics(y_val, y_pred)
    print(f"  MAE mean: {metrics['mae_mean']:.4f}  R² mean: {metrics['r2_mean']:.4f}")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "deeponet_surrogate.pt")
    torch.save({
        "model_state": net.state_dict(),
        "scaler_mean": scaler.mean_.astype(np.float32),
        "scaler_std": scaler.scale_.astype(np.float32),
    }, path)
    print(f"  Saved: {path}")
    return {"deeponet": metrics}


def _build_fno_net():
    import torch
    import torch.nn as nn
    import torch.fft

    N_STAGES, N_CHANNELS, N_MODES, WIDTH = 10, 3, 8, 64

    class SpectralConv1d(nn.Module):
        def __init__(self):
            super().__init__()
            self.weights = nn.Parameter(
                (1 / (N_CHANNELS * WIDTH)) * torch.rand(N_CHANNELS, WIDTH, N_MODES, dtype=torch.cfloat)
            )

        def forward(self, x):
            B, C, L = x.shape
            x_ft = torch.fft.rfft(x)
            out_ft = torch.zeros(B, WIDTH, x_ft.shape[-1], dtype=torch.cfloat, device=x.device)
            m = min(N_MODES, x_ft.shape[-1])
            out_ft[:, :, :m] = torch.einsum("bim,iom->bom", x_ft[:, :, :m], self.weights[:, :, :m])
            return torch.fft.irfft(out_ft, n=L)

    class FNOBlock(nn.Module):
        def __init__(self):
            super().__init__()
            self.spec = SpectralConv1d()
            self.bypass = nn.Conv1d(N_CHANNELS, WIDTH, 1)
            self.bn = nn.BatchNorm1d(WIDTH)
            self.act = nn.GELU()

        def forward(self, x):
            return self.act(self.bn(self.spec(x) + self.bypass(x)))

    class FNOBlock2(nn.Module):
        def __init__(self):
            super().__init__()
            self.spec = nn.Conv1d(WIDTH, WIDTH, N_MODES * 2 + 1, padding=N_MODES)
            self.bypass = nn.Conv1d(WIDTH, WIDTH, 1)
            self.bn = nn.BatchNorm1d(WIDTH)
            self.act = nn.GELU()

        def forward(self, x):
            return self.act(self.bn(self.spec(x) + self.bypass(x)))

    class FNO1d(nn.Module):
        def __init__(self):
            super().__init__()
            self.lift = nn.Conv1d(N_CHANNELS, N_CHANNELS, 1)
            self.b1 = FNOBlock()
            self.b2 = FNOBlock2()
            self.b3 = FNOBlock2()
            self.b4 = FNOBlock2()
            self.head = nn.Sequential(nn.Linear(WIDTH + 1, 128), nn.GELU(), nn.Linear(128, N_OUTPUTS))

        def forward(self, x):
            # x: (B, 31) → split
            seq = x[:, :30].view(-1, N_STAGES, N_CHANNELS).permute(0, 2, 1)  # (B, C, L)
            log_freq = x[:, 30:31]
            seq = self.lift(seq)
            seq = self.b1(seq)
            seq = self.b2(seq)
            seq = self.b3(seq)
            seq = self.b4(seq)
            pooled = seq.mean(dim=-1)
            return self.head(torch.cat([pooled, log_freq], dim=-1))

    return FNO1d()


def train_fno(X: np.ndarray, y: np.ndarray, out_dir: str, epochs: int = 250) -> dict:
    import torch
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    print(f"\n[FNO] Training Fourier Neural Operator ({epochs} epochs)...")
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X).astype(np.float32)
    X_tr, X_val, y_tr, y_val = train_test_split(X_s, y, test_size=0.2, random_state=42)

    net = _train_torch_model(_build_fno_net(), X_tr, y_tr, X_val, y_val, epochs)
    with torch.no_grad():
        y_pred = net(torch.from_numpy(X_val)).numpy()
    metrics = compute_metrics(y_val, y_pred)
    print(f"  MAE mean: {metrics['mae_mean']:.4f}  R² mean: {metrics['r2_mean']:.4f}")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "fno_surrogate.pt")
    torch.save({"model_state": net.state_dict()}, path)
    print(f"  Saved: {path}")
    return {"fno": metrics}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

ALL_MODELS = ["random_forest", "mlp", "pinn", "deeponet", "fno"]

TRAINER_MAP = {
    "random_forest": train_random_forest,
    "mlp": train_mlp,
    "pinn": train_pinn,
    "deeponet": train_deeponet,
    "fno": train_fno,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to CSV dataset")
    parser.add_argument("--model", default="all", choices=["all"] + ALL_MODELS)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--samples", type=int, default=None)
    parser.add_argument("--out", default=OUTPUT_DIR)
    args = parser.parse_args()

    X, y = load_dataset(args.dataset, args.samples)
    os.makedirs(args.out, exist_ok=True)

    to_train = ALL_MODELS if args.model == "all" else [args.model]
    leaderboard = {}

    for model_name in to_train:
        trainer = TRAINER_MAP[model_name]
        t0 = time.time()
        kwargs = {"out_dir": args.out}
        if args.epochs and model_name != "random_forest":
            kwargs["epochs"] = args.epochs
        try:
            result = trainer(X, y, **kwargs)
            leaderboard.update(result)
        except Exception as exc:
            print(f"  [FAILED] {model_name}: {exc}")
            leaderboard[model_name] = {"error": str(exc)}
        print(f"  Time: {time.time()-t0:.1f}s")

    lb_path = os.path.join(args.out, "leaderboard.json")
    with open(lb_path, "w") as f:
        json.dump(leaderboard, f, indent=2)
    print(f"\nLeaderboard saved: {lb_path}")

    print("\n=== Model Comparison Leaderboard ===")
    for name, m in leaderboard.items():
        if "mae_mean" in m:
            print(f"  {name:<20} MAE={m['mae_mean']:.4f}  R²={m['r2_mean']:.4f}")
        else:
            print(f"  {name:<20} {m}")


if __name__ == "__main__":
    main()
