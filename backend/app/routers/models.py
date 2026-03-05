import logging
from fastapi import APIRouter
from app.models import registry as model_registry
from app.models.schemas import ModelCompareRequest, ModelCompareResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["models"])


@router.get("/list")
def list_models():
    return {"models": model_registry.list_models()}


@router.post("/compare", response_model=list[ModelCompareResult])
def compare_models(request: ModelCompareRequest):
    stages = [{"tag": s.tag, "type": s.type, "value": s.value} for s in request.stages]
    results = model_registry.compare_models(stages, request.frequency, request.vin)
    return [ModelCompareResult(**r) for r in results]
