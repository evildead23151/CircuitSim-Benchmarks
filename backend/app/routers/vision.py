"""Vision router — circuit image component extraction."""
import cv2
import numpy as np
import structlog
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

log = structlog.get_logger()

router = APIRouter(prefix="/vision", tags=["vision"])

BLOCK = 27
C_PARAM = 11
SE_SIZE = 30

# Aspect ratio thresholds for component type heuristic
_AR_INDUCTOR_MIN = 0.25   # tall, thin → coil
_AR_INDUCTOR_MAX = 0.5
_AR_RESISTOR_MIN = 1.5    # wide, flat → resistor body

# Default value lookup table (deterministic, aspect-ratio based)
_DEFAULT_VALUES = {
    "resistor": {"value": 100.0, "unit": "ohm"},
    "inductor": {"value": 1.0,   "unit": "mH"},
    "capacitor": {"value": 10.0, "unit": "uF"},
}


def _classify_component(w: int, h: int) -> str:
    """Classify a detected bounding-box into R/L/C using aspect ratio."""
    ar = w / h if h > 0 else 1.0
    if ar < _AR_INDUCTOR_MAX:
        return "inductor"
    if ar > _AR_RESISTOR_MIN:
        return "resistor"
    return "capacitor"


def _estimate_value(comp_type: str, w: int, h: int) -> tuple[float, str]:
    """Return a deterministic (value, unit) estimate based on bounding-box size.

    The heuristic scales a baseline value linearly with the larger dimension
    of the bounding box, acting as a rough proxy for component size.
    """
    base = _DEFAULT_VALUES[comp_type]
    scale = max(w, h) / SE_SIZE  # SE_SIZE is our reference blob size
    value = round(base["value"] * scale, 2)
    return value, base["unit"]


def get_actual_components(image_bytes: bytes) -> list[dict]:
    """Extract components from a circuit image using morphological analysis.

    Uses aspect-ratio-based heuristics for component type and size estimation.
    No random values are assigned.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return []

    img_bin = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, BLOCK, C_PARAM
    )
    kernel = np.ones((SE_SIZE, SE_SIZE), np.uint8)
    img_blob = cv2.morphologyEx(img_bin, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(img_blob, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    components = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > SE_SIZE or h > SE_SIZE:
            comp_type = _classify_component(w, h)
            value, unit = _estimate_value(comp_type, w, h)
            components.append(
                {
                    "type": comp_type,
                    "value": value,
                    "unit": unit,
                    "box": [int(x), int(y), int(w), int(h)],
                }
            )
    return components


@router.post("/extract")
async def extract_parameters(file: UploadFile = File(...), request: Request = None):
    """Extract circuit component parameters from an uploaded image."""
    contents = await file.read()
    state = request.app.state if request else None
    remote_ai_url = getattr(state, "remote_ai_url", "") if state else ""

    if remote_ai_url:
        import requests as http_requests

        try:
            target = f"{remote_ai_url.rstrip('/')}/vision"
            files = {"file": (file.filename, contents, file.content_type)}
            resp = http_requests.post(target, files=files, timeout=30)
            resp.raise_for_status()
            return {**resp.json(), "source": "research_remote", "caution": "Manual review required"}
        except Exception as exc:
            log.warning("remote_vision_failed", error=str(exc))

    try:
        detected = get_actual_components(contents)
        return {
            "source": "template_cv_engine_v1",
            "count": len(detected),
            "components": detected,
            "system_limitations": "Linear LTI components only, topology inference experimental",
        }
    except Exception as exc:
        log.error("vision_extract_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(exc)}")
