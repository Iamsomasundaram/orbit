from __future__ import annotations

from fastapi import FastAPI, Response, status

from .config import get_settings
from .health import HealthResponse, ServiceInfo, live_response, readiness_response, service_info

settings = get_settings()
app = FastAPI(title="ORBIT API", version="0.1.0")


@app.get("/", response_model=ServiceInfo)
def root() -> ServiceInfo:
    return service_info(settings)


@app.get("/health/live", response_model=HealthResponse)
def health_live() -> HealthResponse:
    return live_response(settings)


@app.get("/health/ready", response_model=HealthResponse)
def health_ready(response: Response) -> HealthResponse:
    payload = readiness_response(settings)
    if payload.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload


@app.get("/api/v1/system/info", response_model=ServiceInfo)
def system_info() -> ServiceInfo:
    return service_info(settings)
