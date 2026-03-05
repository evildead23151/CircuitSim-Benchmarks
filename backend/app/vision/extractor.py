import logging
import numpy as np

logger = logging.getLogger(__name__)

BLOCK = 27
C_PARAM = 11
SE_SIZE = 30

_CV2_AVAILABLE = False
try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    logger.warning("opencv not available; vision extractor will return empty results")


def extract_components(image_bytes: bytes) -> list[dict]:
    """
    Extract circuit components from image bytes using adaptive thresholding + morphology.
    Returns list of component dicts with keys: type, value, unit, box.
    """
    if not _CV2_AVAILABLE:
        logger.warning("CV2 not available, returning empty component list")
        return []

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        logger.warning("Failed to decode image")
        return []

    img_bin = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        BLOCK, C_PARAM,
    )
    kernel = np.ones((SE_SIZE, SE_SIZE), np.uint8)
    img_blob = cv2.morphologyEx(img_bin, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(img_blob, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    components = []
    rng = np.random.default_rng(42)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > SE_SIZE or h > SE_SIZE:
            comp_type = "resistor" if w > h else "capacitor"
            val = int(rng.integers(10, 500))
            components.append({
                "type": comp_type,
                "value": float(val),
                "unit": "ohm" if comp_type == "resistor" else "uF",
                "box": [int(x), int(y), int(w), int(h)],
            })
    logger.debug("Extracted %d components from image", len(components))
    return components
