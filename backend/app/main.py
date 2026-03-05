"""FastAPI application factory with lifespan context manager."""
import pickle
import os
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.logging import LoggingMiddleware
from app.models.registry import registry
from app.ai.random_forest import RandomForestSurrogate
from app.ai.mlp import MLPSurrogate
from app.ai.pinn import PINNSurrogate
from app.ai.deeponet import DeepONetSurrogate
from app.ai.fno import FNOSurrogate
from app.ai.ensemble import EnsembleSurrogate
from app.routers import health, config, vision, benchmark, models as models_router

log = structlog.get_logger()


def _configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def _load_legacy_ai_model():
    """Load the legacy simple-circuit AI model (rlc_vout_model.pkl)."""
    path = settings.get_rf_model_path()
    # The legacy model is the plain RF trained on R/L/C scalars (not topological)
    plain_path = os.path.join(settings.get_sample_data_dir(), "rlc_vout_model.pkl")
    for p in [path, plain_path]:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    model = pickle.load(f)
                log.info("legacy_ai_model_loaded", path=p)
                return model
            except Exception as exc:
                log.warning("legacy_ai_model_load_failed", path=p, error=str(exc))
    log.warning("legacy_ai_model_not_found")
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialise resources on startup, clean up on shutdown."""
    _configure_logging()
    log.info("startup_begin", app=settings.app_name, version=settings.app_version)

    # Register all surrogate models
    rf = RandomForestSurrogate(settings.get_topo_v3_model_path())
    mlp = MLPSurrogate(settings.get_mlp_model_path())
    pinn = PINNSurrogate(settings.get_pinn_model_path())
    deeponet = DeepONetSurrogate(settings.get_deeponet_model_path())
    fno = FNOSurrogate(settings.get_fno_model_path())
    ens = EnsembleSurrogate()

    for m in [rf, mlp, pinn, deeponet, fno]:
        registry.register(m)

    # Ensemble needs registry reference (set before registering)
    ens.set_registry(registry)
    registry.register(ens)

    # Load all models (failures are non-fatal)
    registry.load_all()

    # Make registry available on app.state
    app.state.registry = registry
    app.state.remote_ai_url = settings.remote_ai_url

    # Also keep the legacy simple-circuit AI model for /benchmark/ (non-topological)
    app.state.ai_model = _load_legacy_ai_model()

    log.info("startup_complete", models_loaded=sum(
        1 for m in registry.list_models() if m["loaded"]
    ))
    yield

    log.info("shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(vision.router)
    app.include_router(benchmark.router)
    app.include_router(models_router.router)

    @app.get("/")
    def read_root():
        return {
            "status": f"{settings.app_name} V3",
            "version": settings.app_version,
            "models_loaded": sum(
                1 for m in app.state.registry.list_models() if m["loaded"]
            ),
            "assumptions": "LTI Linear Cascaded Stages only. No bridge/feedback support.",
        }

    return app


app = create_app()
