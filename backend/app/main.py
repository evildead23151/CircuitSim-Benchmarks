import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.logging import StructuredLoggingMiddleware
from app.routers import benchmark, config, vision, models, health
from app.models import registry as model_registry
from app.ai.random_forest import RandomForestSurrogate
from app.ai.mlp_surrogate import MLPSurrogate
from app.ai.pinn import PINNSurrogate
from app.ai.deeponet import DeepONetSurrogate
from app.ai.fno import FNOSurrogate
from app.ai.ensemble import EnsembleSurrogate

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _register_models():
    rf = RandomForestSurrogate(model_dir=settings.model_dir)
    mlp = MLPSurrogate()
    pinn = PINNSurrogate()
    deep = DeepONetSurrogate()
    fno = FNOSurrogate()
    ens = EnsembleSurrogate([rf, mlp, pinn, deep, fno])

    for m in (rf, mlp, pinn, deep, fno, ens):
        model_registry.register(m.name, m)
    logger.info("All surrogate models registered.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up CircuitSim Benchmarks API v%s", settings.app_version)
    _register_models()
    yield
    logger.info("Shutting down CircuitSim Benchmarks API")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(StructuredLoggingMiddleware)

    app.include_router(health.router)
    app.include_router(benchmark.router)
    app.include_router(config.router)
    app.include_router(vision.router)
    app.include_router(models.router)

    @app.get("/")
    def read_root():
        rf = model_registry.get_model("random_forest")
        return {
            "status": f"CircuitSim Cascaded-Chain Framework V{settings.app_version}",
            "topo_v3_ready": rf.is_available if rf else False,
            "assumptions": "LTI Linear Cascaded Stages only. No bridge/feedback support.",
        }

    return app


app = create_app()
