"""Health check router."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok"}
