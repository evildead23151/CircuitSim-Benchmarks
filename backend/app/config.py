"""Application configuration via pydantic-settings."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "CircuitSim Benchmarks API"
    app_version: str = "3.0.0"

    # Model paths (relative to sample_data dir)
    sample_data_dir: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "..",
        "sample_data",
    )

    rf_model_path: str = ""
    topo_v3_model_path: str = ""
    mlp_model_path: str = ""
    pinn_model_path: str = ""
    deeponet_model_path: str = ""
    fno_model_path: str = ""

    # Remote AI URL (runtime-configurable)
    remote_ai_url: str = ""

    model_config = {"env_prefix": "CIRCUITSIM_", "case_sensitive": False}

    def get_sample_data_dir(self) -> str:
        return os.path.normpath(self.sample_data_dir)

    def get_rf_model_path(self) -> str:
        if self.rf_model_path:
            return self.rf_model_path
        return os.path.join(self.get_sample_data_dir(), "rlc_vout_model.pkl")

    def get_topo_v3_model_path(self) -> str:
        if self.topo_v3_model_path:
            return self.topo_v3_model_path
        return os.path.join(self.get_sample_data_dir(), "topological_v3_model.pkl")

    def get_mlp_model_path(self) -> str:
        if self.mlp_model_path:
            return self.mlp_model_path
        return os.path.join(self.get_sample_data_dir(), "models", "mlp_surrogate.pt")

    def get_pinn_model_path(self) -> str:
        if self.pinn_model_path:
            return self.pinn_model_path
        return os.path.join(self.get_sample_data_dir(), "models", "pinn_surrogate.pt")

    def get_deeponet_model_path(self) -> str:
        if self.deeponet_model_path:
            return self.deeponet_model_path
        return os.path.join(self.get_sample_data_dir(), "models", "deeponet_surrogate.pt")

    def get_fno_model_path(self) -> str:
        if self.fno_model_path:
            return self.fno_model_path
        return os.path.join(self.get_sample_data_dir(), "models", "fno_surrogate.pt")


settings = Settings()
