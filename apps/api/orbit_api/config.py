from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    orbit_env: str = Field(default="local", alias="ORBIT_ENV")
    service_name: str = "orbit-api"
    milestone: str = "6"
    api_internal_port: int = Field(default=8001, alias="API_INTERNAL_PORT")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_internal_port: int = Field(default=5432, alias="POSTGRES_INTERNAL_PORT")
    postgres_db: str = Field(default="orbit", alias="POSTGRES_DB")
    postgres_user: str = Field(default="orbit", alias="POSTGRES_USER")
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_internal_port: int = Field(default=6379, alias="REDIS_INTERNAL_PORT")
    database_url: str = Field(default="postgresql+psycopg://orbit:orbit@postgres:5432/orbit", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_model: str = Field(default="", alias="OPENAI_MODEL")
    js_baseline_archival_stage: str = Field(default="frozen-baseline", alias="JS_BASELINE_ARCHIVAL_STAGE")
    js_baseline_archival_target_milestone: str = Field(default="Milestone 7", alias="JS_BASELINE_ARCHIVAL_TARGET_MILESTONE")
    portfolio_storage_dir: str = Field(default="/workspace/.orbit-data/portfolio-submissions", alias="PORTFOLIO_STORAGE_DIR")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
