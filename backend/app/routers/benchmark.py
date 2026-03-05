"""Benchmark router — analytical vs AI surrogate performance comparison."""
import time
import math
import structlog
import requests as http_requests
from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import CircuitParams, TopologicalCircuit, BenchmarkResult
from app.solvers.analytical import analytical_solver, solve_topological
from app.solvers.transient import get_transient_metrics, get_transient_metrics_ode
from app.ai.random_forest import vectorize_circuit

log = structlog.get_logger()

router = APIRouter(prefix="/benchmark", tags=["benchmark"])

_ITERATIONS = 10  # warm-start averaging


def _ai_solver_simple(params: CircuitParams, remote_ai_url: str, ai_model):
    """Run the simple (non-topological) AI surrogate for /benchmark."""
    if remote_ai_url:
        try:
            payload = {"features": [params.R, params.L, params.C]}
            target = f"{remote_ai_url.rstrip('/')}/predict"
            resp = http_requests.post(target, json=payload, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            pred = data.get("prediction")
            vout = pred[0] if isinstance(pred, list) else pred
            return float(vout), "remote"
        except Exception as exc:
            log.error("remote_ai_failed", error=str(exc))
            raise HTTPException(status_code=502, detail=f"Remote Colab model failed: {exc}")

    if ai_model is None:
        raise HTTPException(status_code=503, detail="Local AI Model not loaded")

    import numpy as np

    X = np.array([[params.R, params.L, params.C]])
    try:
        if isinstance(ai_model, dict):
            predictor = ai_model["model"]
            scaler = ai_model.get("scaler")
            if scaler:
                X = scaler.transform(X)
        else:
            predictor = ai_model
        log_vout = predictor.predict(X)[0]
        return float(10**log_vout), "local"
    except Exception as exc:
        log.error("local_ai_inference_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Local inference failed: {exc}")


@router.post("/", response_model=BenchmarkResult)
def run_benchmark(params: CircuitParams, request: Request):
    """Run analytical vs AI benchmark for a simple series-RLC circuit."""
    state = request.app.state
    remote_ai_url = getattr(state, "remote_ai_url", "")
    ai_model = getattr(state, "ai_model", None)

    start_phy = time.perf_counter()
    for _ in range(_ITERATIONS):
        a_vout, a_iin, is_ood = analytical_solver(params)
    a_time_avg = (time.perf_counter() - start_phy) * 1000 / _ITERATIONS

    start_ai = time.perf_counter()
    ai_vout, source = _ai_solver_simple(params, remote_ai_url, ai_model)
    ai_time = (time.perf_counter() - start_ai) * 1000

    err_abs = abs(a_vout - ai_vout)
    err_pct = (err_abs / a_vout * 100) if a_vout != 0 else 0.0
    speedup = a_time_avg / ai_time if ai_time > 0 else 0.0

    return BenchmarkResult(
        solver_vout=a_vout,
        solver_time_ms=a_time_avg,
        ai_vout=ai_vout,
        ai_time_ms=ai_time,
        error_abs=err_abs,
        error_percent=err_pct,
        speed_factor=speedup,
        iin_ma=a_iin,
        ai_source=source,
        is_ood=is_ood,
        hardware="x64-Host-CPU",
    )


def _topo_ai_predict(circuit: TopologicalCircuit, registry) -> tuple[list, str]:
    """Run the active AI surrogate for topological benchmark."""
    model = registry.get_active()
    if model is None or not model.is_loaded():
        # Fallback to analytical
        v, i, e = solve_topological(circuit)
        tr, ts, mp = get_transient_metrics(circuit)
        return [v, i / 1000, e, tr / 1000, ts / 1000, mp / 100], "analytical-fallback"

    features = vectorize_circuit(circuit)
    try:
        preds = model.predict(features)
        vout = float(preds[0]) * circuit.vin
        iin = float(preds[1]) * circuit.vin
        return [vout, iin, preds[2], preds[3], preds[4], preds[5]], f"ai-{model.name()}"
    except Exception as exc:
        log.warning("topo_ai_inference_failed", error=str(exc))
        v, i, e = solve_topological(circuit)
        tr, ts, mp = get_transient_metrics(circuit)
        return [v, i / 1000, e, tr / 1000, ts / 1000, mp / 100], "error-fallback"


@router.post("/topological", response_model=BenchmarkResult)
def run_topological_benchmark(circuit: TopologicalCircuit, request: Request):
    """Run analytical vs AI surrogate benchmark for a topological circuit."""
    registry = request.app.state.registry

    start_phy = time.perf_counter()
    v_a, i_a, e_a = solve_topological(circuit)
    tr_a, ts_a, mp_a = get_transient_metrics_ode(circuit)
    a_time_ms = (time.perf_counter() - start_phy) * 1000

    start_ai = time.perf_counter()
    results_ai, source = _topo_ai_predict(circuit, registry)
    ai_time_ms = (time.perf_counter() - start_ai) * 1000

    v_ai, i_ai_raw, e_ai, tr_ai_raw, ts_ai_raw, mp_ai_raw = results_ai
    i_ai = i_ai_raw * 1000
    tr_ai, ts_ai, mp_ai = tr_ai_raw * 1000, ts_ai_raw * 1000, mp_ai_raw * 100

    err_abs = abs(v_a - v_ai)
    err_pct = (err_abs / v_a * 100) if v_a != 0 else 0.0
    speedup = a_time_ms / ai_time_ms if ai_time_ms > 0 else 0.0

    return BenchmarkResult(
        solver_vout=v_a,
        solver_time_ms=a_time_ms,
        ai_vout=v_ai,
        ai_time_ms=ai_time_ms,
        error_abs=err_abs,
        error_percent=err_pct,
        speed_factor=speedup,
        iin_ma=i_a,
        efficiency=e_a,
        rise_time_ms=tr_a,
        settling_time_ms=ts_a,
        overshoot_pct=mp_a,
        ai_source=source,
        is_ood=len(circuit.stages) > 10,
        hardware="x64-Host-CPU-Research-Node",
    )
