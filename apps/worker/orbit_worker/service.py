from __future__ import annotations

import socket
import time
from typing import Literal

from fastapi import FastAPI, Response, status
from pydantic import BaseModel, ConfigDict

from .config import get_settings
from .persistence import get_persistence_schema_catalog

settings = get_settings()
app = FastAPI(title="ORBIT Worker", version="0.1.0")


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


class WorkerInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: str
    status: Literal["ok"]
    milestone: str
    active_backend: str
    reference_runtime: str
    baseline_archival_stage: str
    baseline_archival_target_milestone: str
    persistence_schema_version: str
    persistence_tables: int
    persistence_boundary: str
    environment: str
    thin_slice_entrypoint: str


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


def worker_info() -> WorkerInfo:
    catalog = get_persistence_schema_catalog()
    return WorkerInfo(
        service=settings.service_name,
        status="ok",
        milestone=settings.milestone,
        active_backend="python",
        reference_runtime="js-baseline-only",
        baseline_archival_stage=settings.js_baseline_archival_stage,
        baseline_archival_target_milestone=settings.js_baseline_archival_target_milestone,
        persistence_schema_version=catalog.schema_version,
        persistence_tables=len(catalog.tables),
        persistence_boundary="alembic-migrated-sqlalchemy+repository-protocol",
        environment=settings.orbit_env,
        thin_slice_entrypoint="orbit_worker.runner.run_review_pipeline",
    )


def live_response() -> HealthResponse:
    return HealthResponse(
        service=settings.service_name,
        status="ok",
        milestone=settings.milestone,
        runtime="python-worker-service",
        timestamp_epoch_ms=int(time.time() * 1000),
        checks=[],
    )


def readiness_response() -> HealthResponse:
    checks = [
        tcp_dependency("postgres", settings.postgres_host, settings.postgres_internal_port),
        tcp_dependency("redis", settings.redis_host, settings.redis_internal_port),
    ]
    status_value = "ok" if all(check.status == "ok" for check in checks) else "degraded"
    return HealthResponse(
        service=settings.service_name,
        status=status_value,
        milestone=settings.milestone,
        runtime="python-worker-service",
        timestamp_epoch_ms=int(time.time() * 1000),
        checks=checks,
    )


@app.get("/", response_model=WorkerInfo)
def root() -> WorkerInfo:
    return worker_info()


@app.get("/health/live", response_model=HealthResponse)
def health_live() -> HealthResponse:
    return live_response()


@app.get("/health/ready", response_model=HealthResponse)
def health_ready(response: Response) -> HealthResponse:
    payload = readiness_response()
    if payload.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
