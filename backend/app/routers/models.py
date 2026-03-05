"""Models router — list, compare and select AI surrogate models."""
import math
import structlog
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import (
    ModelListResponse,
    ModelInfo,
    ModelSelectRequest,
    TopologicalCircuit,
    EnsemblePrediction,
)
from app.ai.random_forest import vectorize_circuit

log = structlog.get_logger()

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/list", response_model=ModelListResponse)
def list_models(request: Request):
    """Return all registered models with their loaded status and metadata."""
    reg = request.app.state.registry
    return ModelListResponse(
        models=[ModelInfo(**m) for m in reg.list_models()],
        active_model=reg.active_name,
    )


@router.post("/select")
def select_model(body: ModelSelectRequest, request: Request):
    """Set the active surrogate model for /benchmark/topological."""
    reg = request.app.state.registry
    if not reg.set_active(body.model_name):
        raise HTTPException(status_code=404, detail=f"Model '{body.model_name}' not found")
    return {"status": "ok", "active_model": body.model_name}


@router.post("/compare")
def compare_models(circuit: TopologicalCircuit, request: Request):
    """Run all loaded models on the same circuit and return a comparison table."""
    reg = request.app.state.registry
    features = vectorize_circuit(circuit)
    results = {}

    for entry in reg.list_models():
        name = entry["name"]
        model = reg.get(name)
        if model is None or not model.is_loaded():
            results[name] = {"status": "not_loaded"}
            continue
        try:
            preds = model.predict(features)
            results[name] = {
                "status": "ok",
                "vout": float(preds[0]),
                "iin": float(preds[1]),
                "efficiency": float(preds[2]),
                "rise_time": float(preds[3]),
                "settling_time": float(preds[4]),
                "overshoot": float(preds[5]),
            }
        except Exception as exc:
            results[name] = {"status": "error", "detail": str(exc)}

    return {"circuit_stages": len(circuit.stages), "models": results}


@router.post("/predict/ensemble", response_model=EnsemblePrediction)
def ensemble_predict(circuit: TopologicalCircuit, request: Request):
    """Run the ensemble model with uncertainty quantification."""
    reg = request.app.state.registry
    ens = reg.get("ensemble")
    if ens is None or not ens.is_loaded():
        raise HTTPException(status_code=503, detail="Ensemble model not available")

    features = vectorize_circuit(circuit)
    try:
        mean_pred, uncertainty = ens.predict_with_uncertainty(features)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Collect per-member predictions for transparency
    contributions = {}
    for member_name in ens._weights:
        m = reg.get(member_name)
        if m and m.is_loaded():
            try:
                p = m.predict(features)
                contributions[member_name] = float(p[0])  # vout
            except Exception:
                pass

    return EnsemblePrediction(
        vout=float(mean_pred[0]),
        iin=float(mean_pred[1]),
        efficiency=float(mean_pred[2]),
        rise_time=float(mean_pred[3]),
        settling_time=float(mean_pred[4]),
        overshoot=float(mean_pred[5]),
        uncertainty=uncertainty,
        model_contributions=contributions,
    )
