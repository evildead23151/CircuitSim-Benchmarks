import logging
import os
import pickle
import numpy as np
from .base import BaseSurrogate

logger = logging.getLogger(__name__)

_MODEL_FILENAME = "topological_v3_model.pkl"


class RandomForestSurrogate(BaseSurrogate):
    def __init__(self, model_dir: str = "../sample_data"):
        self._model = None
        self._loaded = False
        path = os.path.join(model_dir, _MODEL_FILENAME)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    self._model = pickle.load(f)
                self._loaded = True
                logger.info("RandomForest: loaded model from %s", path)
            except Exception as e:
                logger.warning("RandomForest: failed to load model: %s", e)
        else:
            logger.info("RandomForest: no model file at %s, using stub", path)

    @property
    def name(self) -> str:
        return "random_forest"

    @property
    def description(self) -> str:
        return "Gradient-boosted random forest (scikit-learn). Trained on topological V3 dataset."

    @property
    def is_available(self) -> bool:
        return self._loaded

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self._model is None:
            return np.zeros(6)
        try:
            return np.array(self._model.predict(features)[0], dtype=float)
        except Exception as e:
            logger.warning("RandomForest predict error: %s", e)
            return np.zeros(6)
