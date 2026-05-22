from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from `VELLUM_` environment variables."""

    model_config = SettingsConfigDict(env_prefix="VELLUM_", extra="ignore")

    app_name: str = "Vellum-NLQ"
    active_catalogue: str = "health-uk"
    catalogue_root: Path = Path(__file__).resolve().parents[1] / "catalogues"
    database_url: str = "postgresql+psycopg://vellum_admin:vellum_admin@localhost:5432/vellum"
    openai_model: str = "gpt-5.4-mini"


@lru_cache
def get_settings() -> Settings:
    return Settings()
