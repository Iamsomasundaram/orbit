from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    orbit_env: str = Field(default="local", alias="ORBIT_ENV")
    service_name: str = "orbit-api"
    milestone: str = "12.1"
    api_internal_port: int = Field(default=8001, alias="API_INTERNAL_PORT")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_internal_port: int = Field(default=5432, alias="POSTGRES_INTERNAL_PORT")
    postgres_db: str = Field(default="orbit", alias="POSTGRES_DB")
    postgres_user: str = Field(default="orbit", alias="POSTGRES_USER")
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_internal_port: int = Field(default=6379, alias="REDIS_INTERNAL_PORT")
    database_url: str = Field(default="postgresql+psycopg://orbit:orbit@postgres:5432/orbit", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    llm_runtime_mode: str = Field(default="deterministic", alias="LLM_RUNTIME_MODE")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_max_concurrency: int = Field(default=6, alias="LLM_MAX_CONCURRENCY")
    llm_request_timeout_seconds: int = Field(default=25, alias="LLM_REQUEST_TIMEOUT_SECONDS")
    llm_max_output_tokens: int = Field(default=700, alias="LLM_MAX_OUTPUT_TOKENS")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_api_key_file: str = Field(default="/workspace/key.txt", alias="OPENAI_API_KEY_FILE")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="", alias="ANTHROPIC_MODEL")
    local_llm_base_url: str = Field(default="", alias="LOCAL_LLM_BASE_URL")
    local_llm_model: str = Field(default="", alias="LOCAL_LLM_MODEL")
    js_baseline_archival_stage: str = Field(default="archived-baseline", alias="JS_BASELINE_ARCHIVAL_STAGE")
    js_baseline_archival_target_milestone: str = Field(default="Milestone 7.1", alias="JS_BASELINE_ARCHIVAL_TARGET_MILESTONE")
    portfolio_storage_dir: str = Field(default="/workspace/.orbit-data/portfolio-submissions", alias="PORTFOLIO_STORAGE_DIR")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
