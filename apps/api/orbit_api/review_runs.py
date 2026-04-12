from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from orbit_worker.committee_engine import CommitteeRuntimeOptions
from orbit_worker.persistence import (
    AgentReviewRecord,
    AuditEventRecord,
    CanonicalPortfolioRecord,
    CommitteeReportRecord,
    ConflictPersistenceRecord,
    PersistenceRepository,
    PortfolioRecord,
    ReviewPersistenceBundle,
    ReviewRunRecord,
    ScorecardRecord,
    build_review_persistence_bundle,
)
from orbit_worker.runner import run_review_pipeline_for_portfolio
from orbit_worker.schemas import OrbitModel


class ReviewRunSummary(OrbitModel):
    run_id: str
    portfolio_id: str
    review_status: str
    final_recommendation: str
    weighted_composite_score: float
    agent_review_count: int
    conflict_count: int
    created_at: datetime
    completed_at: datetime | None


class ReviewRunDetail(OrbitModel):
    portfolio: PortfolioRecord
    canonical_portfolio: CanonicalPortfolioRecord
    review_run: ReviewRunRecord
    agent_reviews: list[AgentReviewRecord]
    conflicts: list[ConflictPersistenceRecord]
    scorecard: ScorecardRecord
    committee_report: CommitteeReportRecord
    audit_events: list[AuditEventRecord]


class ReviewRunListResponse(OrbitModel):
    items: list[ReviewRunSummary]


class PortfolioReviewNotFoundError(ValueError):
    pass


def build_review_run_id(portfolio_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"review-{portfolio_id}-{timestamp}"


def summarize_review_bundle(bundle: ReviewPersistenceBundle) -> ReviewRunSummary:
    return ReviewRunSummary(
        run_id=bundle.review_run.run_id,
        portfolio_id=bundle.review_run.portfolio_id,
        review_status=bundle.review_run.review_status,
        final_recommendation=bundle.scorecard.final_recommendation,
        weighted_composite_score=bundle.scorecard.weighted_composite_score,
        agent_review_count=len(bundle.agent_reviews),
        conflict_count=len(bundle.conflicts),
        created_at=bundle.review_run.created_at,
        completed_at=bundle.review_run.completed_at,
    )


def bundle_to_detail(bundle: ReviewPersistenceBundle) -> ReviewRunDetail:
    return ReviewRunDetail(
        portfolio=bundle.portfolio,
        canonical_portfolio=bundle.canonical_portfolio,
        review_run=bundle.review_run,
        agent_reviews=bundle.agent_reviews,
        conflicts=bundle.conflicts,
        scorecard=bundle.scorecard,
        committee_report=bundle.committee_report,
        audit_events=bundle.audit_events,
    )


class ReviewRunService:
    def __init__(
        self,
        repository: PersistenceRepository,
        *,
        runtime_options: CommitteeRuntimeOptions | None = None,
        llm_provider: object | None = None,
        deliberation_refresher: Callable[[str], None] | None = None,
    ) -> None:
        self._repository = repository
        self._runtime_options = runtime_options or CommitteeRuntimeOptions()
        self._llm_provider = llm_provider
        self._deliberation_refresher = deliberation_refresher

    def start_review(self, portfolio_id: str) -> ReviewRunSummary:
        portfolio_bundle = self._repository.get_portfolio_bundle(portfolio_id)
        if portfolio_bundle is None:
            raise PortfolioReviewNotFoundError(
                f"Portfolio '{portfolio_id}' was not found in the canonical ingestion store."
            )

        run_id = build_review_run_id(portfolio_id)
        result = run_review_pipeline_for_portfolio(
            portfolio_bundle.canonical_portfolio.canonical_payload,
            run_id=run_id,
            runtime_options=self._runtime_options,
            llm_provider=self._llm_provider,
        )
        review_bundle = build_review_persistence_bundle(
            run_id,
            result["canonical_portfolio"],
            result["agent_reviews"],
            result["conflicts"],
            result["scorecard"],
            result["committee_report"],
            execution_metadata=result.get("execution"),
        )
        self._repository.save_review_bundle(review_bundle)
        if self._deliberation_refresher is not None:
            self._deliberation_refresher(run_id)
        return summarize_review_bundle(review_bundle)

    def get_review_run(self, run_id: str) -> ReviewRunDetail | None:
        bundle = self._repository.get_review_run_bundle(run_id)
        if bundle is None:
            return None
        return bundle_to_detail(bundle)

    def list_review_runs(self, portfolio_id: str | None = None) -> ReviewRunListResponse:
        return ReviewRunListResponse(
            items=[summarize_review_bundle(bundle) for bundle in self._repository.list_review_run_bundles(portfolio_id)]
        )
