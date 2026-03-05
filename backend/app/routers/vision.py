import logging
import requests
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.vision.extractor import extract_components
from app import state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/extract")
async def extract_parameters(file: UploadFile = File(...)):
    contents = await file.read()

    if state.remote_ai_url:
        try:
            target = f"{state.remote_ai_url.rstrip('/')}/vision"
            files = {"file": (file.filename, contents, file.content_type)}
            resp = requests.post(target, files=files, timeout=30)
            resp.raise_for_status()
            return {**resp.json(), "source": "research_remote", "caution": "Manual review required"}
        except Exception as e:
            logger.warning("Remote vision request failed: %s", e)

    try:
        detected = extract_components(contents)
        return {
            "source": "template_cv_engine_v1",
            "count": len(detected),
            "components": detected,
            "system_limitations": "Linear LTI components only, topology inference experimental",
        }
    except Exception as e:
        logger.exception("Vision extraction failed")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
