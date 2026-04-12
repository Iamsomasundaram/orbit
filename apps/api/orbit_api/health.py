from __future__ import annotations

import socket
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict

from orbit_worker.persistence import get_persistence_schema_catalog

from .config import Settings


class DependencyStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    host: str
    port: int
    status: Literal["ok", "error"]
    latency_ms: int | None = None
    detail: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str
    status: Literal["ok", "degraded"]
    milestone: str
    runtime: str
    timestamp_epoch_ms: int
    checks: list[DependencyStatus]


class ServiceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str
    status: Literal["ok"]
    milestone: str
    runtime_direction: str
    runtime_mode: str
    active_backend: str
    reference_runtime: str
    reference_runtime_stage: str
    reference_runtime_archival_target_milestone: str
    llm_max_concurrency: int
    persistence_schema_version: str
    persistence_tables: int
    environment: str
    llm_provider: str
    openai_model: str


def tcp_dependency(name: str, host: str, port: int, timeout: float = 0.5) -> DependencyStatus:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency_ms = int((time.perf_counter() - started) * 1000)
            return DependencyStatus(
                name=name,
                host=host,
                port=port,
                status="ok",
                latency_ms=latency_ms,
                detail="Connection succeeded.",
            )
    except OSError as exc:
        return DependencyStatus(
            name=name,
            host=host,
            port=port,
            status="error",
            latency_ms=None,
            detail=str(exc),
        )


def live_response(settings: Settings) -> HealthResponse:
    return HealthResponse(
        service=settings.service_name,
        status="ok",
        milestone=settings.milestone,
        runtime="python-fastapi",
        timestamp_epoch_ms=int(time.time() * 1000),
        checks=[],
    )


def readiness_response(settings: Settings) -> HealthResponse:
    checks = [
        tcp_dependency("postgres", settings.postgres_host, settings.postgres_internal_port),
        tcp_dependency("redis", settings.redis_host, settings.redis_internal_port),
    ]
    status = "ok" if all(check.status == "ok" for check in checks) else "degraded"
    return HealthResponse(
        service=settings.service_name,
        status=status,
        milestone=settings.milestone,
        runtime="python-fastapi",
        timestamp_epoch_ms=int(time.time() * 1000),
        checks=checks,
    )


def service_info(settings: Settings) -> ServiceInfo:
    catalog = get_persistence_schema_catalog()
    return ServiceInfo(
        service=settings.service_name,
        status="ok",
        milestone=settings.milestone,
        runtime_direction="adaptive-tiered-llm-committee-with-deterministic-fallback-and-observable-boardroom-playback",
        runtime_mode=settings.llm_runtime_mode,
        active_backend="python",
        reference_runtime="js-baseline-only",
        reference_runtime_stage=settings.js_baseline_archival_stage,
        reference_runtime_archival_target_milestone=settings.js_baseline_archival_target_milestone,
        llm_max_concurrency=settings.llm_max_concurrency,
        persistence_schema_version=catalog.schema_version,
        persistence_tables=len(catalog.tables),
        environment=settings.orbit_env,
        llm_provider=settings.llm_provider,
        openai_model=settings.openai_model,
    )
