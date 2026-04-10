from __future__ import annotations

from datetime import datetime

from orbit_worker.debate import run_bounded_debate
from orbit_worker.persistence import (
    AuditEventRecord,
    CommitteeReportRecord,
    ConflictPersistenceRecord,
    DebateConflictError,
    ConflictResolutionRecord,
    DebatePersistenceBundle,
    DebateSessionRecord,
    PersistenceRepository,
    PortfolioRecord,
    ReviewRunRecord,
    ScorecardRecord,
    build_debate_persistence_bundle,
)
from orbit_worker.schemas import OrbitModel


class DebateSummary(OrbitModel):
    debate_id: str
    run_id: str
    portfolio_id: str
    debate_status: str
    conflicts_considered: int
    score_change_required_count: int
    created_at: datetime


class DebateDetail(OrbitModel):
    portfolio: PortfolioRecord
    review_run: ReviewRunRecord
    conflicts: list[ConflictPersistenceRecord]
    scorecard: ScorecardRecord
    committee_report: CommitteeReportRecord
    debate_session: DebateSessionRecord
    conflict_resolutions: list[ConflictResolutionRecord]
    audit_events: list[AuditEventRecord]


class DebateListResponse(OrbitModel):
    items: list[DebateSummary]


class ReviewRunDebateNotFoundError(ValueError):
    pass


class DebateAlreadyExistsError(ValueError):
    pass


def build_debate_id(run_id: str) -> str:
    return f"debate-{run_id}"


def summarize_debate_bundle(bundle: DebatePersistenceBundle) -> DebateSummary:
    return DebateSummary(
        debate_id=bundle.debate_session.debate_id,
        run_id=bundle.review_run.run_id,
        portfolio_id=bundle.portfolio.portfolio_id,
        debate_status=bundle.debate_session.debate_status,
        conflicts_considered=bundle.debate_session.conflicts_considered,
        score_change_required_count=bundle.debate_session.score_change_required_count,
        created_at=bundle.debate_session.created_at,
    )


def bundle_to_detail(
    debate_bundle: DebatePersistenceBundle,
    conflicts: list[ConflictPersistenceRecord],
    scorecard: ScorecardRecord,
    committee_report: CommitteeReportRecord,
) -> DebateDetail:
    return DebateDetail(
        portfolio=debate_bundle.portfolio,
        review_run=debate_bundle.review_run,
        conflicts=conflicts,
        scorecard=scorecard,
        committee_report=committee_report,
        debate_session=debate_bundle.debate_session,
        conflict_resolutions=debate_bundle.conflict_resolutions,
        audit_events=debate_bundle.audit_events,
    )


class DebateService:
    def __init__(self, repository: PersistenceRepository) -> None:
        self._repository = repository

    def start_debate(self, run_id: str) -> DebateSummary:
        review_bundle = self._repository.get_review_run_bundle(run_id)
        if review_bundle is None:
            raise ReviewRunDebateNotFoundError(f"Review run '{run_id}' was not found.")

        debate = run_bounded_debate(
            run_id=review_bundle.review_run.run_id,
            portfolio_id=review_bundle.portfolio.portfolio_id,
            conflicts=[record.conflict_payload for record in review_bundle.conflicts],
            agent_reviews=[record.review_payload for record in review_bundle.agent_reviews],
            debate_id=build_debate_id(run_id),
        )
        bundle = build_debate_persistence_bundle(
            portfolio=review_bundle.portfolio,
            review_run=review_bundle.review_run,
            debate=debate,
        )
        try:
            self._repository.save_debate_bundle(bundle)
        except DebateConflictError as exc:
            raise DebateAlreadyExistsError(
                f"Review run '{run_id}' already has a persisted debate session."
            ) from exc
        return summarize_debate_bundle(bundle)

    def get_debate(self, debate_id: str) -> DebateDetail | None:
        debate_bundle = self._repository.get_debate_bundle(debate_id)
        if debate_bundle is None:
            return None

        review_bundle = self._repository.get_review_run_bundle(debate_bundle.review_run.run_id)
        if review_bundle is None:
            return None

        return bundle_to_detail(
            debate_bundle,
            conflicts=review_bundle.conflicts,
            scorecard=review_bundle.scorecard,
            committee_report=review_bundle.committee_report,
        )

    def list_debates(self, run_id: str | None = None) -> DebateListResponse:
        return DebateListResponse(
            items=[summarize_debate_bundle(bundle) for bundle in self._repository.list_debate_bundles(run_id=run_id)]
        )
