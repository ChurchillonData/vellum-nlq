from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from `VELLUM_` environment variables."""

    model_config = SettingsConfigDict(env_prefix="VELLUM_", extra="ignore")

    app_name: str = "Vellum-NLQ"
    active_catalogue: str = "health-uk"
    catalogue_root: Path = Path(__file__).resolve().parents[1] / "catalogues"
    mapping_root: Path = Path(__file__).resolve().parents[1] / "mappings"
    database_url: str = "postgresql+psycopg://vellum_admin:vellum_admin@localhost:5432/vellum"
    seed_database_url: str = "postgresql+psycopg://vellum_seeder:vellum_seeder@localhost:5432/vellum"
    readonly_database_url: str = "postgresql+psycopg://vellum_readonly:vellum_readonly@localhost:5432/vellum"
    audit_database_url: str = "postgresql+psycopg://vellum_auditor:vellum_auditor@localhost:5432/vellum"
    audit_log_path: Path = Path(__file__).resolve().parents[1] / ".local" / "audit-log.jsonl"
    audit_backend: str = "jsonl"
    demo_member_count: int = 2_000
    demo_month_count: int = 18
    execution_backend: str = "local_demo"
    intent_provider: str = "deterministic"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    openai_timeout_seconds: float = 8.0
    openai_max_retries: int = 1
    openai_min_confidence: float = 0.70
    openai_fallback_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
