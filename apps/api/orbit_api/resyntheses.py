from __future__ import annotations

from datetime import datetime

from orbit_worker.persistence import (
    AuditEventRecord,
    CommitteeReportRecord,
    ConflictResolutionRecord,
    DebateSessionRecord,
    PersistenceRepository,
    PortfolioRecord,
    ResynthesisConflictError,
    ResynthesisPersistenceBundle,
    ResynthesisSessionRecord,
    ResynthesizedCommitteeReportRecord,
    ResynthesizedScorecardRecord,
    ReviewRunRecord,
    ScorecardRecord,
    build_resynthesis_persistence_bundle,
)
from orbit_worker.resynthesis import run_score_recheck_and_resynthesis
from orbit_worker.schemas import OrbitModel


class ResynthesisSummary(OrbitModel):
    resynthesis_id: str
    debate_id: str
    run_id: str
    portfolio_id: str
    resynthesis_status: str
    score_change_required_count: int
    active_artifact_source: str
    created_at: datetime


class ResynthesisDetail(OrbitModel):
    portfolio: PortfolioRecord
    review_run: ReviewRunRecord
    debate_session: DebateSessionRecord
    conflict_resolutions: list[ConflictResolutionRecord]
    original_scorecard: ScorecardRecord
    original_committee_report: CommitteeReportRecord
    active_scorecard: ScorecardRecord | ResynthesizedScorecardRecord
    active_committee_report: CommitteeReportRecord | ResynthesizedCommitteeReportRecord
    resynthesis_session: ResynthesisSessionRecord
    resynthesized_scorecard: ResynthesizedScorecardRecord | None = None
    resynthesized_committee_report: ResynthesizedCommitteeReportRecord | None = None
    audit_events: list[AuditEventRecord]


class ResynthesisListResponse(OrbitModel):
    items: list[ResynthesisSummary]


class DebateResynthesisNotFoundError(ValueError):
    pass


class ResynthesisAlreadyExistsError(ValueError):
    pass


def summarize_resynthesis_bundle(bundle: ResynthesisPersistenceBundle) -> ResynthesisSummary:
    return ResynthesisSummary(
        resynthesis_id=bundle.resynthesis_session.resynthesis_id,
        debate_id=bundle.resynthesis_session.debate_id,
        run_id=bundle.review_run.run_id,
        portfolio_id=bundle.portfolio.portfolio_id,
        resynthesis_status=bundle.resynthesis_session.resynthesis_status,
        score_change_required_count=bundle.resynthesis_session.score_change_required_count,
        active_artifact_source=bundle.resynthesis_session.active_artifact_source,
        created_at=bundle.resynthesis_session.created_at,
    )


def bundle_to_detail(
    bundle: ResynthesisPersistenceBundle,
    conflict_resolutions: list[ConflictResolutionRecord],
    original_scorecard: ScorecardRecord,
    original_committee_report: CommitteeReportRecord,
) -> ResynthesisDetail:
    return ResynthesisDetail(
        portfolio=bundle.portfolio,
        review_run=bundle.review_run,
        debate_session=bundle.debate_session,
        conflict_resolutions=conflict_resolutions,
        original_scorecard=original_scorecard,
        original_committee_report=original_committee_report,
        active_scorecard=bundle.resynthesized_scorecard or original_scorecard,
        active_committee_report=bundle.resynthesized_committee_report or original_committee_report,
        resynthesis_session=bundle.resynthesis_session,
        resynthesized_scorecard=bundle.resynthesized_scorecard,
        resynthesized_committee_report=bundle.resynthesized_committee_report,
        audit_events=bundle.audit_events,
    )


class ResynthesisService:
    def __init__(self, repository: PersistenceRepository) -> None:
        self._repository = repository

    def start_resynthesis(self, debate_id: str) -> ResynthesisSummary:
        debate_bundle = self._repository.get_debate_bundle(debate_id)
        if debate_bundle is None:
            raise DebateResynthesisNotFoundError(f"Debate session '{debate_id}' was not found.")

        review_bundle = self._repository.get_review_run_bundle(debate_bundle.review_run.run_id)
        if review_bundle is None:
            raise DebateResynthesisNotFoundError(
                f"Review run '{debate_bundle.review_run.run_id}' for debate '{debate_id}' was not found."
            )

        result = run_score_recheck_and_resynthesis(
            debate_id=debate_bundle.debate_session.debate_id,
            portfolio=review_bundle.canonical_portfolio.canonical_payload,
            run_id=review_bundle.review_run.run_id,
            reviews=[record.review_payload for record in review_bundle.agent_reviews],
            conflicts=[record.conflict_payload for record in review_bundle.conflicts],
            original_scorecard=review_bundle.scorecard.scorecard_payload,
            original_report=review_bundle.committee_report.report_payload,
            resolutions=[record.resolution_payload for record in debate_bundle.conflict_resolutions],
        )
        bundle = build_resynthesis_persistence_bundle(
            portfolio=review_bundle.portfolio,
            review_run=review_bundle.review_run,
            debate_session=debate_bundle.debate_session,
            session=result["resynthesis_session"],
            scorecard=result["resynthesized_scorecard"],
            committee_report=result["resynthesized_committee_report"],
        )
        try:
            self._repository.save_resynthesis_bundle(bundle)
        except ResynthesisConflictError as exc:
            raise ResynthesisAlreadyExistsError(
                f"Debate session '{debate_id}' already has a persisted re-synthesis session."
            ) from exc
        return summarize_resynthesis_bundle(bundle)

    def get_resynthesis(self, resynthesis_id: str) -> ResynthesisDetail | None:
        bundle = self._repository.get_resynthesis_bundle(resynthesis_id)
        if bundle is None:
            return None

        review_bundle = self._repository.get_review_run_bundle(bundle.review_run.run_id)
        debate_bundle = self._repository.get_debate_bundle(bundle.debate_session.debate_id)
        if review_bundle is None or debate_bundle is None:
            return None

        return bundle_to_detail(
            bundle,
            conflict_resolutions=debate_bundle.conflict_resolutions,
            original_scorecard=review_bundle.scorecard,
            original_committee_report=review_bundle.committee_report,
        )

    def list_resyntheses(self, debate_id: str | None = None) -> ResynthesisListResponse:
        return ResynthesisListResponse(
            items=[summarize_resynthesis_bundle(bundle) for bundle in self._repository.list_resynthesis_bundles(debate_id=debate_id)]
        )
