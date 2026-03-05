import logging
import time
import math
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

_registry: dict = {}


def register(name: str, model) -> None:
    _registry[name] = model
    logger.info("Registered model: %s", name)


def get_model(name: str):
    return _registry.get(name)


def list_models() -> list[dict]:
    result = []
    for name, model in _registry.items():
        result.append({
            "name": name,
            "available": getattr(model, "is_available", True),
            "description": getattr(model, "description", ""),
        })
    return result


def compare_models(stages: list, frequency: float, vin: float) -> list[dict]:
    """Run all registered models on the given circuit and return comparison."""
    features = build_features(stages, frequency)
    results = []
    for name, model in _registry.items():
        t0 = time.perf_counter()
        try:
            preds = model.predict(features)
            vout = float(preds[0]) if len(preds) > 0 else 0.0
        except Exception as e:
            logger.warning("Model %s predict failed: %s", name, e)
            vout = 0.0
        latency_ms = (time.perf_counter() - t0) * 1000
        results.append({
            "model_name": name,
            "vout": vout,
            "latency_ms": latency_ms,
            "source": name,
        })
    return results


def build_features(stages: list, frequency: float) -> np.ndarray:
    features = []
    for i in range(10):
        if i < len(stages):
            s = stages[i]
            tag = s.get("tag", 0) if isinstance(s, dict) else s.tag
            stype = s.get("type", "R") if isinstance(s, dict) else s.type
            value = s.get("value", 1.0) if isinstance(s, dict) else s.value
            t_num = 1 if stype == 'R' else (2 if stype == 'L' else 3)
            val = max(value, 1e-12)
            features.extend([tag, t_num, math.log10(val)])
        else:
            features.extend([0, 0, -12])
    features.append(math.log10(max(frequency, 1.0)))
    return np.array([features])
