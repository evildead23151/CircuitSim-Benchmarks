"""Config router — manage remote AI URL at runtime."""
from fastapi import APIRouter, Request
from app.models.schemas import RemoteConfigRequest

router = APIRouter(prefix="/config", tags=["config"])


@router.post("/remote")
def set_remote_url(config: RemoteConfigRequest, request: Request):
    """Set or clear the remote AI endpoint URL."""
    state = request.app.state
    if not config.url or config.url.strip() == "":
        state.remote_ai_url = ""
        return {"status": "Switched to local mode"}

    url = config.url.strip()
    if not url.startswith("http"):
        url = f"https://{url}"

    state.remote_ai_url = url
    return {"status": "Remote model connected", "url": url}
