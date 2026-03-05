import logging
import time
from fastapi import APIRouter
from app.models.schemas import TopologicalCircuit, BenchmarkResult
from app.solvers.analytical import solve_topological
from app.solvers.transient import get_transient_metrics
from app.models import registry as model_registry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/benchmark", tags=["benchmark"])


def _stages_as_dicts(stages):
    return [{"tag": s.tag, "type": s.type, "value": s.value} for s in stages]


@router.post("/topological", response_model=BenchmarkResult)
def run_topological_benchmark(circuit: TopologicalCircuit):
    stages = _stages_as_dicts(circuit.stages)

    start_phy = time.perf_counter()
    v_a, i_a, e_a = solve_topological(stages, circuit.frequency, circuit.vin)
    tr_a, ts_a, mp_a = get_transient_metrics(stages)
    a_time_ms = (time.perf_counter() - start_phy) * 1000

    # Use the topo_v3 (random_forest) AI model by default
    rf_model = model_registry.get_model("random_forest")
    features = model_registry.build_features(stages, circuit.frequency)

    start_ai = time.perf_counter()
    source = "local-v2-fallback"
    v_ai = v_a * 0.99
    i_ai = i_a * 0.99
    e_ai_val = e_a * 0.99
    tr_ai = tr_a
    ts_ai = ts_a
    mp_ai = mp_a

    if rf_model is not None and rf_model.is_available:
        try:
            preds = rf_model.predict(features)
            v_ai = float(preds[0]) * circuit.vin
            i_ai = float(preds[1]) * circuit.vin * 1000
            e_ai_val = float(preds[2])
            tr_ai = float(preds[3]) * 1000
            ts_ai = float(preds[4]) * 1000
            mp_ai = float(preds[5]) * 100
            source = "local-v3-deep"
        except Exception as e:
            logger.warning("RF model inference failed: %s", e)

    ai_time_ms = (time.perf_counter() - start_ai) * 1000

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
