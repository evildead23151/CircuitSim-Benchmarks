#!/usr/bin/env python3
"""Generate circuit simulation dataset v4 using Latin Hypercube Sampling.

Usage:
    python scripts/generate_dataset_v4.py --samples 100000 --out sample_data/dataset_v4
"""
import argparse
import math
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models.schemas import TopologicalCircuit, TopologicalComponent
from app.solvers.analytical import solve_topological
from app.solvers.transient import get_transient_metrics_ode

try:
    from scipy.stats.qmc import LatinHypercube
    HAS_LHS = True
except ImportError:
    HAS_LHS = False
    warnings.warn("scipy not available; falling back to pure random sampling.")

# Component value ranges
TAGS = [1, 2]          # 1=Series, 2=Shunt
TYPES = ["R", "L", "C"]
R_RANGE = (1.0, 10000.0)
L_RANGE = (1e-6, 1.0)
C_RANGE = (1e-9, 1e-3)
FREQ_RANGE = (10.0, 1e6)
VIN = 1.0

# Maximum stages
MAX_STAGES = 10

_TYPE_CODE = {"R": 1, "L": 2, "C": 3}


def _sample_component_value(comp_type: str, u: float) -> float:
    """Map a uniform sample u ∈ [0,1] to a log-uniform component value."""
    if comp_type == "R":
        lo, hi = math.log10(R_RANGE[0]), math.log10(R_RANGE[1])
    elif comp_type == "L":
        lo, hi = math.log10(L_RANGE[0]), math.log10(L_RANGE[1])
    else:
        lo, hi = math.log10(C_RANGE[0]), math.log10(C_RANGE[1])
    return 10 ** (lo + u * (hi - lo))


def _generate_samples_lhs(n: int, rng: np.random.Generator) -> list[dict]:
    """Generate n samples using Latin Hypercube Sampling."""
    # Dimensions: n_stages + 10*(tag + type + value) + frequency
    # Use LHS for continuous dims; discrete dims sampled separately.
    sampler = LatinHypercube(d=MAX_STAGES * 3 + 2, seed=42)  # +2: n_stages, frequency
    lhs = sampler.random(n)  # (n, d)

    samples = []
    for i in range(n):
        row = lhs[i]
        # Number of stages: 1-10
        n_stages = max(1, int(row[0] * MAX_STAGES) + 1)
        freq_u = row[1]
        freq = 10 ** (math.log10(FREQ_RANGE[0]) + freq_u * (
            math.log10(FREQ_RANGE[1]) - math.log10(FREQ_RANGE[0])
        ))

        stages = []
        for k in range(n_stages):
            base = 2 + k * 3
            tag_u, type_u, val_u = row[base], row[base + 1], row[base + 2]
            tag = TAGS[int(tag_u * len(TAGS)) % len(TAGS)]
            comp_type = TYPES[int(type_u * len(TYPES)) % len(TYPES)]
            value = _sample_component_value(comp_type, val_u)
            stages.append(TopologicalComponent(tag=tag, type=comp_type, value=value))

        samples.append({"stages": stages, "frequency": freq, "vin": VIN, "n_stages": n_stages})

    return samples


def _generate_samples_random(n: int, rng: np.random.Generator) -> list[dict]:
    """Fallback: purely random sampling."""
    samples = []
    for _ in range(n):
        n_stages = rng.integers(1, MAX_STAGES + 1)
        freq = 10 ** rng.uniform(math.log10(FREQ_RANGE[0]), math.log10(FREQ_RANGE[1]))
        stages = []
        for _ in range(n_stages):
            tag = int(rng.choice(TAGS))
            comp_type = str(rng.choice(TYPES))
            u = rng.uniform()
            value = _sample_component_value(comp_type, u)
            stages.append(TopologicalComponent(tag=tag, type=comp_type, value=value))
        samples.append({"stages": stages, "frequency": freq, "vin": VIN, "n_stages": n_stages})
    return samples


def _add_edge_cases() -> list[dict]:
    """Add deterministic edge cases: single-stage, all-R, near-resonance."""
    cases = []
    # Single-stage circuits
    for comp_type in TYPES:
        for val in [1.0, 100.0, 10000.0]:
            cases.append({
                "stages": [TopologicalComponent(tag=1, type=comp_type, value=val)],
                "frequency": 1000.0, "vin": 1.0, "n_stages": 1,
            })
    # Near-resonance: series LC with f ≈ f_res
    L, C = 1e-3, 1e-6
    f_res = 1 / (2 * math.pi * math.sqrt(L * C))
    for f_mult in [0.9, 1.0, 1.1]:
        cases.append({
            "stages": [
                TopologicalComponent(tag=1, type="L", value=L),
                TopologicalComponent(tag=1, type="C", value=C),
            ],
            "frequency": f_res * f_mult, "vin": 1.0, "n_stages": 2,
        })
    # All-R, all-L, all-C circuits (3 stages each)
    for comp_type in TYPES:
        cases.append({
            "stages": [TopologicalComponent(tag=1, type=comp_type, value=100.0) for _ in range(3)],
            "frequency": 1000.0, "vin": 1.0, "n_stages": 3,
        })
    return cases


def _featurize(stages: list, freq: float) -> list[float]:
    feats = []
    for i in range(MAX_STAGES):
        if i < len(stages):
            s = stages[i]
            val = max(s.value, 1e-12)
            feats.extend([float(s.tag), float(_TYPE_CODE[s.type]), math.log10(val)])
        else:
            feats.extend([0.0, 0.0, -12.0])
    feats.append(math.log10(max(freq, 1.0)))
    return feats


def _solve_sample(sample: dict) -> dict | None:
    circuit = TopologicalCircuit(
        stages=sample["stages"], frequency=sample["frequency"], vin=sample["vin"]
    )
    try:
        vout, iin, eff = solve_topological(circuit)
        tr, ts, mp = get_transient_metrics_ode(circuit)
    except Exception:
        return None

    targets = [vout, iin / 1000, eff, tr / 1000, ts / 1000, mp / 100]
    if any(not math.isfinite(t) for t in targets):
        return None

    feats = _featurize(sample["stages"], sample["frequency"])
    row = feats + targets + [sample["n_stages"], sample["frequency"]]
    return row


def main():
    parser = argparse.ArgumentParser(description="Generate CircuitSim dataset v4")
    parser.add_argument("--samples", type=int, default=100_000)
    parser.add_argument("--out", default="sample_data/dataset_v4")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    rng = np.random.default_rng(args.seed)

    print(f"Generating {args.samples} samples...")
    t0 = time.time()

    gen_fn = _generate_samples_lhs if HAS_LHS else _generate_samples_random
    samples = gen_fn(args.samples, rng) + _add_edge_cases()

    rows = []
    failed = 0
    for i, s in enumerate(samples):
        r = _solve_sample(s)
        if r is None:
            failed += 1
        else:
            rows.append(r)
        if (i + 1) % 10000 == 0:
            print(f"  Processed {i + 1}/{len(samples)} ({failed} failed)")

    print(f"Done: {len(rows)} valid samples, {failed} failed in {time.time()-t0:.1f}s")

    feat_cols = [f"f{i}" for i in range(31)]
    target_cols = ["vout", "iin", "efficiency", "rise_time", "settling_time", "overshoot"]
    meta_cols = ["n_stages", "frequency"]
    df = pd.DataFrame(rows, columns=feat_cols + target_cols + meta_cols)

    # Data quality checks
    nan_count = df[target_cols].isna().sum().sum()
    print(f"NaN check: {nan_count} NaN values in targets")
    assert nan_count == 0, "Dataset contains NaN values!"

    csv_path = args.out + ".csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path} ({len(df)} rows)")

    try:
        parquet_path = args.out + ".parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"Saved Parquet: {parquet_path}")
    except ImportError:
        print("pyarrow not available; skipping Parquet export")


if __name__ == "__main__":
    main()
