import logging
from fastapi import APIRouter
from app.models.schemas import RemoteConfigRequest
from app import state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["config"])


@router.post("/remote")
def set_remote_url(config: RemoteConfigRequest):
    if not config.url or config.url.strip() == "":
        state.remote_ai_url = None
        logger.info("Switched to local mode")
        return {"status": "Switched to local mode"}

    url = config.url.strip()
    if not url.startswith("http"):
        url = f"https://{url}"

    state.remote_ai_url = url
    logger.info("Remote model connected: %s", url)
    return {"status": "Remote model connected", "url": state.remote_ai_url}
