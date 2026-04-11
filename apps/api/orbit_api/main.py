from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response, status

from orbit_worker.persistence import PersistenceSchemaCatalog, SqlAlchemyPersistenceRepository
from orbit_worker.committee_engine import CommitteeRuntimeOptions

from .config import get_settings
from .debates import (
    DebateAlreadyExistsError,
    DebateDetail,
    DebateListResponse,
    DebateService,
    DebateSummary,
    ReviewRunDebateNotFoundError,
)
from .health import HealthResponse, ServiceInfo, live_response, readiness_response, service_info
from .history import ArtifactInspectionDetail, PortfolioHistoryDetail, ReviewHistoryService
from .portfolios import (
    InvalidPortfolioDocumentError,
    PortfolioAlreadyExistsError,
    PortfolioDetail,
    PortfolioDocumentSubmission,
    PortfolioIdeaSubmission,
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
from .review_workflow import ReviewWorkflowService
from .resyntheses import (
    DebateResynthesisNotFoundError,
    ResynthesisAlreadyExistsError,
    ResynthesisDetail,
    ResynthesisListResponse,
    ResynthesisService,
    ResynthesisSummary,
)
from .persistence import PersistenceDdlResponse, persistence_ddl_response, persistence_schema_catalog
from .workspace import (
    PortfolioComparisonResponse,
    PortfolioRankingResponse,
    PortfolioWorkspaceNotFoundError,
    PortfolioWorkspaceService,
    PortfolioWorkspaceSummaryResponse,
    PortfolioWorkspaceValidationError,
    PortfolioWorkspaceRankingField,
    PortfolioWorkspaceSortField,
    SortDirection,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = SqlAlchemyPersistenceRepository(settings.database_url)
    repository.assert_schema_ready()
    runtime_options = CommitteeRuntimeOptions.from_settings(settings)
    review_run_service = ReviewRunService(repository=repository, runtime_options=runtime_options)
    debate_service = DebateService(repository=repository)
    resynthesis_service = ResynthesisService(repository=repository)
    app.state.portfolio_ingestion_service = PortfolioIngestionService(
        repository=repository,
        storage_root=Path(settings.portfolio_storage_dir),
    )
    app.state.review_run_service = review_run_service
    app.state.debate_service = debate_service
    app.state.resynthesis_service = resynthesis_service
    app.state.review_workflow_service = ReviewWorkflowService(
        review_runs=review_run_service,
        debates=debate_service,
        resyntheses=resynthesis_service,
    )
    app.state.review_history_service = ReviewHistoryService(repository=repository)
    app.state.portfolio_workspace_service = PortfolioWorkspaceService(repository=repository)
    try:
        yield
    finally:
        repository.dispose()


app = FastAPI(title="ORBIT API", version="0.1.0", lifespan=lifespan)


def portfolio_service(request: Request) -> PortfolioIngestionService:
    return request.app.state.portfolio_ingestion_service


def review_run_service(request: Request) -> ReviewRunService:
    return request.app.state.review_run_service


def review_workflow_service(request: Request) -> ReviewWorkflowService:
    return request.app.state.review_workflow_service


def debate_service(request: Request) -> DebateService:
    return request.app.state.debate_service


def resynthesis_service(request: Request) -> ResynthesisService:
    return request.app.state.resynthesis_service


def review_history_service(request: Request) -> ReviewHistoryService:
    return request.app.state.review_history_service


def portfolio_workspace_service(request: Request) -> PortfolioWorkspaceService:
    return request.app.state.portfolio_workspace_service


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
def submit_portfolio(
    request: Request,
    submission: PortfolioDocumentSubmission | PortfolioIdeaSubmission,
) -> PortfolioDetail:
    service = portfolio_service(request)
    try:
        return service.submit_submission(submission)
    except PortfolioAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidPortfolioDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/api/v1/portfolios", response_model=PortfolioListResponse)
def list_portfolios(request: Request) -> PortfolioListResponse:
    return portfolio_service(request).list_portfolios()


@app.get("/api/v1/portfolios/summary", response_model=PortfolioWorkspaceSummaryResponse)
def portfolio_workspace_summary(
    request: Request,
    sort_by: PortfolioWorkspaceSortField = Query(default="latest_updated_at"),
    direction: SortDirection = Query(default="desc"),
) -> PortfolioWorkspaceSummaryResponse:
    return portfolio_workspace_service(request).list_summary(sort_by=sort_by, direction=direction)


@app.get("/api/v1/portfolios/compare", response_model=PortfolioComparisonResponse)
def compare_portfolios(
    request: Request,
    portfolio_id: list[str] = Query(default_factory=list),
) -> PortfolioComparisonResponse:
    try:
        return portfolio_workspace_service(request).compare(portfolio_id)
    except PortfolioWorkspaceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PortfolioWorkspaceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.get("/api/v1/portfolios/ranking", response_model=PortfolioRankingResponse)
def rank_portfolios(
    request: Request,
    sort_by: PortfolioWorkspaceRankingField = Query(default="weighted_composite_score"),
    direction: SortDirection = Query(default="desc"),
) -> PortfolioRankingResponse:
    return portfolio_workspace_service(request).rank(sort_by=sort_by, direction=direction)


@app.get("/api/v1/portfolios/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(request: Request, portfolio_id: str) -> PortfolioDetail:
    detail = portfolio_service(request).get_portfolio(portfolio_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Portfolio '{portfolio_id}' was not found.")
    return detail


@app.get("/api/v1/portfolios/{portfolio_id}/history", response_model=PortfolioHistoryDetail)
def get_portfolio_history(request: Request, portfolio_id: str) -> PortfolioHistoryDetail:
    detail = review_history_service(request).get_portfolio_history(portfolio_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Portfolio '{portfolio_id}' was not found.")
    return detail


@app.post("/api/v1/portfolios/{portfolio_id}/review-runs", response_model=ReviewRunSummary, status_code=status.HTTP_201_CREATED)
def start_review_run(request: Request, portfolio_id: str) -> ReviewRunSummary:
    service = review_workflow_service(request)
    try:
        return service.start_review(portfolio_id).review_run
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


@app.get("/api/v1/review-runs/{run_id}/artifacts", response_model=ArtifactInspectionDetail)
def get_review_run_artifacts(request: Request, run_id: str) -> ArtifactInspectionDetail:
    detail = review_history_service(request).get_review_run_artifacts(run_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review run '{run_id}' was not found.")
    return detail


@app.post("/api/v1/review-runs/{run_id}/debates", response_model=DebateSummary, status_code=status.HTTP_201_CREATED)
def start_debate(request: Request, run_id: str) -> DebateSummary:
    service = debate_service(request)
    try:
        return service.start_debate(run_id)
    except ReviewRunDebateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DebateAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.get("/api/v1/review-runs/{run_id}/debates", response_model=DebateListResponse)
def list_review_run_debates(request: Request, run_id: str) -> DebateListResponse:
    if review_run_service(request).get_review_run(run_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review run '{run_id}' was not found.")
    return debate_service(request).list_debates(run_id=run_id)


@app.get("/api/v1/debates/{debate_id}", response_model=DebateDetail)
def get_debate(request: Request, debate_id: str) -> DebateDetail:
    detail = debate_service(request).get_debate(debate_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Debate session '{debate_id}' was not found.")
    return detail


@app.get("/api/v1/debates/{debate_id}/artifacts", response_model=ArtifactInspectionDetail)
def get_debate_artifacts(request: Request, debate_id: str) -> ArtifactInspectionDetail:
    detail = review_history_service(request).get_debate_artifacts(debate_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Debate session '{debate_id}' was not found.")
    return detail


@app.post("/api/v1/debates/{debate_id}/re-synthesis", response_model=ResynthesisSummary, status_code=status.HTTP_201_CREATED)
def start_resynthesis(request: Request, debate_id: str) -> ResynthesisSummary:
    service = resynthesis_service(request)
    try:
        return service.start_resynthesis(debate_id)
    except DebateResynthesisNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ResynthesisAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.get("/api/v1/debates/{debate_id}/re-synthesis", response_model=ResynthesisListResponse)
def list_debate_resyntheses(request: Request, debate_id: str) -> ResynthesisListResponse:
    if debate_service(request).get_debate(debate_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Debate session '{debate_id}' was not found.")
    return resynthesis_service(request).list_resyntheses(debate_id=debate_id)


@app.get("/api/v1/re-syntheses/{resynthesis_id}", response_model=ResynthesisDetail)
def get_resynthesis(request: Request, resynthesis_id: str) -> ResynthesisDetail:
    detail = resynthesis_service(request).get_resynthesis(resynthesis_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Re-synthesis session '{resynthesis_id}' was not found.")
    return detail


@app.get("/api/v1/re-syntheses/{resynthesis_id}/artifacts", response_model=ArtifactInspectionDetail)
def get_resynthesis_artifacts(request: Request, resynthesis_id: str) -> ArtifactInspectionDetail:
    detail = review_history_service(request).get_resynthesis_artifacts(resynthesis_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Re-synthesis session '{resynthesis_id}' was not found.")
    return detail
