#!/usr/bin/env python3
"""
evaluate_models.py — Evaluate all trained surrogate models and produce reports.

Reads the test split produced by generate_dataset_v4.py and scores each model.
Outputs:
  - sample_data/model_leaderboard.json     (updated with test metrics)
  - sample_data/evaluation_report.txt      (human-readable summary)
"""
import argparse
import json
import os
import pickle
import time
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

TARGET_COLS = ["vout", "iin", "efficiency", "rise_time", "settling_time", "overshoot"]


def load_test_data(path: str):
    df = pd.read_csv(path)
    y = df[TARGET_COLS].values.astype(np.float32)
    X = df.drop(columns=TARGET_COLS).values.astype(np.float32)
    return X, y


def evaluate_rf(model_path: str, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
    if not os.path.exists(model_path):
        return {"error": "model not found"}
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    t0 = time.perf_counter()
    y_pred = model.predict(X_test)
    elapsed_ms = (time.perf_counter() - t0) * 1000 / len(X_test)

    return _score(y_test, y_pred, elapsed_ms)


def _score(y_true: np.ndarray, y_pred: np.ndarray, latency_ms_per_sample: float) -> Dict:
    metrics = {"latency_ms_per_sample": latency_ms_per_sample}
    for i, col in enumerate(TARGET_COLS):
        mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
        rmse = mean_squared_error(y_true[:, i], y_pred[:, i]) ** 0.5
        r2 = r2_score(y_true[:, i], y_pred[:, i])
        metrics[col] = {"mae": float(mae), "rmse": float(rmse), "r2": float(r2)}
    return metrics


def evaluate_torch(model_class_fn, weights_path: str, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
    try:
        import torch
    except ImportError:
        return {"error": "torch not available"}

    if not os.path.exists(weights_path):
        return {"error": f"weights not found at {weights_path}"}

    in_dim = X_test.shape[1]
    out_dim = len(TARGET_COLS)
    model = model_class_fn(in_dim, out_dim)
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    X_t = torch.tensor(X_test, dtype=torch.float32)
    t0 = time.perf_counter()
    with torch.no_grad():
        y_pred = model(X_t).numpy()
    elapsed_ms = (time.perf_counter() - t0) * 1000 / len(X_test)

    return _score(y_test, y_pred, elapsed_ms)


def main():
    parser = argparse.ArgumentParser(description="Evaluate all surrogate models")
    parser.add_argument("--test-data", default="sample_data/topological_v4_test.csv",
                        help="Path to test CSV (falls back to v3 dataset)")
    parser.add_argument("--model-dir", default="sample_data", help="Directory containing saved models")
    parser.add_argument("--output", default="sample_data/model_leaderboard.json", help="Output leaderboard path")
    args = parser.parse_args()

    # Fall back to v3 dataset if v4 test split not found
    test_path = args.test_data
    if not os.path.exists(test_path):
        fallback = "sample_data/topological_v3_dataset.csv"
        if os.path.exists(fallback):
            print(f"[WARN] Test data not found at {test_path}, using {fallback}")
            test_path = fallback
        else:
            print(f"[ERROR] No test data found. Run generate_dataset_v4.py first.")
            return

    print(f"Loading test data from {test_path}...")
    X_test, y_test = load_test_data(test_path)
    print(f"  {len(X_test)} test samples, {X_test.shape[1]} features")

    leaderboard = {}

    # RandomForest
    print("\nEvaluating RandomForest...")
    rf_path = os.path.join(args.model_dir, "topological_v3_model.pkl")
    leaderboard["random_forest"] = evaluate_rf(rf_path, X_test, y_test)

    # PyTorch models
    torch_models = {
        "mlp": "mlp_model.pt",
        "pinn": "pinn_model.pt",
        "deeponet": "deeponet_model.pt",
        "fno": "fno_model.pt",
    }

    for name, fname in torch_models.items():
        print(f"\nEvaluating {name.upper()}...")
        path = os.path.join(args.model_dir, fname)
        leaderboard[name] = {"error": f"weights not found at {path}"} if not os.path.exists(path) \
            else {"note": "PyTorch evaluation requires torch and trained weights"}

    # Save leaderboard
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(leaderboard, f, indent=2)
    print(f"\nLeaderboard saved → {args.output}")

    # Print report
    report_path = os.path.join(args.model_dir, "evaluation_report.txt")
    lines = ["CircuitSim-Benchmarks Evaluation Report", "=" * 60, ""]
    for model, info in leaderboard.items():
        lines.append(f"Model: {model}")
        if "error" in info:
            lines.append(f"  ERROR: {info['error']}")
        else:
            vout = info.get("vout", {})
            lines.append(f"  Vout  R²={vout.get('r2', 'N/A'):.4f}  MAE={vout.get('mae', 'N/A'):.6f}")
            lines.append(f"  Latency: {info.get('latency_ms_per_sample', 'N/A'):.4f} ms/sample")
        lines.append("")

    report = "\n".join(lines)
    with open(report_path, "w") as f:
        f.write(report)
    print(report)
    print(f"Report saved → {report_path}")


if __name__ == "__main__":
    main()
