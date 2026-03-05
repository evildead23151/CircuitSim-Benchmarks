"""Model registry for managing AI surrogate models."""
import structlog
from typing import Optional
from app.ai.base import BaseSurrogate

log = structlog.get_logger()


class ModelRegistry:
    """Central registry for all AI surrogate models."""

    def __init__(self):
        self._models: dict[str, BaseSurrogate] = {}
        self._active: str = "random_forest"

    def register(self, model: BaseSurrogate) -> None:
        self._models[model.name()] = model
        log.info("model_registered", name=model.name(), loaded=model.is_loaded())

    def get(self, name: str) -> Optional[BaseSurrogate]:
        return self._models.get(name)

    def get_active(self) -> Optional[BaseSurrogate]:
        return self._models.get(self._active)

    def set_active(self, name: str) -> bool:
        if name in self._models:
            self._active = name
            return True
        return False

    @property
    def active_name(self) -> str:
        return self._active

    def list_models(self) -> list[dict]:
        return [
            {
                "name": m.name(),
                "loaded": m.is_loaded(),
                "metadata": m.metadata(),
            }
            for m in self._models.values()
        ]

    def load_all(self) -> None:
        """Attempt to load/initialize all registered models."""
        for name, model in self._models.items():
            try:
                model.load()
                log.info("model_loaded", name=name, loaded=model.is_loaded())
            except Exception as exc:
                log.warning("model_load_failed", name=name, error=str(exc))


# Global singleton registry
registry = ModelRegistry()
