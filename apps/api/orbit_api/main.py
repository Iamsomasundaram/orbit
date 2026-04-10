from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status

from orbit_worker.persistence import PersistenceSchemaCatalog, SqlAlchemyPersistenceRepository

from .config import get_settings
from .health import HealthResponse, ServiceInfo, live_response, readiness_response, service_info
from .portfolios import (
    InvalidPortfolioDocumentError,
    PortfolioAlreadyExistsError,
    PortfolioDetail,
    PortfolioDocumentSubmission,
    PortfolioIngestionService,
    PortfolioListResponse,
)
from .review_runs import (
    PortfolioReviewNotFoundError,
    ReviewRunDetail,
    ReviewRunListResponse,
    ReviewRunService,
    ReviewRunSummary,
)
from .persistence import PersistenceDdlResponse, persistence_ddl_response, persistence_schema_catalog

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = SqlAlchemyPersistenceRepository(settings.database_url)
    repository.ensure_schema()
    app.state.portfolio_ingestion_service = PortfolioIngestionService(
        repository=repository,
        storage_root=Path(settings.portfolio_storage_dir),
    )
    app.state.review_run_service = ReviewRunService(repository=repository)
    try:
        yield
    finally:
        repository.dispose()


app = FastAPI(title="ORBIT API", version="0.1.0", lifespan=lifespan)


def portfolio_service(request: Request) -> PortfolioIngestionService:
    return request.app.state.portfolio_ingestion_service


def review_run_service(request: Request) -> ReviewRunService:
    return request.app.state.review_run_service


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


@app.get("/api/v1/system/persistence/schema", response_model=PersistenceSchemaCatalog)
def persistence_schema() -> PersistenceSchemaCatalog:
    return persistence_schema_catalog()


@app.get("/api/v1/system/persistence/ddl", response_model=PersistenceDdlResponse)
def persistence_ddl() -> PersistenceDdlResponse:
    return persistence_ddl_response()


@app.post("/api/v1/portfolios", response_model=PortfolioDetail, status_code=status.HTTP_201_CREATED)
def submit_portfolio(request: Request, submission: PortfolioDocumentSubmission) -> PortfolioDetail:
    service = portfolio_service(request)
    try:
        return service.submit_document(submission)
    except PortfolioAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidPortfolioDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/api/v1/portfolios", response_model=PortfolioListResponse)
def list_portfolios(request: Request) -> PortfolioListResponse:
    return portfolio_service(request).list_portfolios()


@app.get("/api/v1/portfolios/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(request: Request, portfolio_id: str) -> PortfolioDetail:
    detail = portfolio_service(request).get_portfolio(portfolio_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Portfolio '{portfolio_id}' was not found.")
    return detail


@app.post("/api/v1/portfolios/{portfolio_id}/review-runs", response_model=ReviewRunSummary, status_code=status.HTTP_201_CREATED)
def start_review_run(request: Request, portfolio_id: str) -> ReviewRunSummary:
    service = review_run_service(request)
    try:
        return service.start_review(portfolio_id)
    except PortfolioReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.get("/api/v1/portfolios/{portfolio_id}/review-runs", response_model=ReviewRunListResponse)
def list_portfolio_review_runs(request: Request, portfolio_id: str) -> ReviewRunListResponse:
    if portfolio_service(request).get_portfolio(portfolio_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Portfolio '{portfolio_id}' was not found.")
    return review_run_service(request).list_review_runs(portfolio_id=portfolio_id)


@app.get("/api/v1/review-runs/{run_id}", response_model=ReviewRunDetail)
def get_review_run(request: Request, run_id: str) -> ReviewRunDetail:
    detail = review_run_service(request).get_review_run(run_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review run '{run_id}' was not found.")
    return detail
