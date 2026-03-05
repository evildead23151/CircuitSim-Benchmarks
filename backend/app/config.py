from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CIRCUITSIM_", case_sensitive=False)

    app_title: str = "CircuitSim Benchmarks API"
    app_version: str = "3.0.0"
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"
    model_dir: str = "../sample_data"
    remote_ai_url: str | None = None
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
