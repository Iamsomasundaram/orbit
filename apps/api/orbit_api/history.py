from __future__ import annotations

from typing import Literal

from orbit_worker.persistence import (
    AuditEventRecord,
    CanonicalPortfolioRecord,
    CommitteeReportRecord,
    ConflictResolutionRecord,
    DEBATE_AUDIT_ACTIONS,
    DebatePersistenceBundle,
    DebateSessionRecord,
    PersistenceRepository,
    PortfolioIngestionBundle,
    PortfolioRecord,
    RESYNTHESIS_AUDIT_ACTIONS,
    ResynthesisPersistenceBundle,
    ResynthesisSessionRecord,
    ResynthesizedCommitteeReportRecord,
    ResynthesizedScorecardRecord,
    ReviewPersistenceBundle,
    ReviewRunRecord,
    ScorecardRecord,
    SourceDocumentRecord,
)
from orbit_worker.schemas import OrbitModel

from .debates import DebateSummary, summarize_debate_bundle
from .review_runs import ReviewRunSummary, summarize_review_bundle
from .resyntheses import ResynthesisSummary, summarize_resynthesis_bundle

REVIEW_AUDIT_ACTIONS = (
    "review_run.completed",
    "committee_report.materialized",
)


class ArtifactOwnerReference(OrbitModel):
    owner_type: Literal["review_run", "resynthesis"]
    owner_id: str


class ArtifactSelectionState(OrbitModel):
    active_artifact_source: Literal["original", "resynthesized"]
    original_scorecard_owner: ArtifactOwnerReference
    original_committee_report_owner: ArtifactOwnerReference
    active_scorecard_owner: ArtifactOwnerReference
    active_committee_report_owner: ArtifactOwnerReference
    has_resynthesized_artifacts: bool
    score_change_required_count: int


class LineagePath(OrbitModel):
    portfolio_id: str
    review_run_id: str
    debate_id: str | None = None
    resynthesis_id: str | None = None


class ReviewHistoryItem(OrbitModel):
    lineage: LineagePath
    review_run: ReviewRunSummary
    debate: DebateSummary | None = None
    resynthesis: ResynthesisSummary | None = None
    artifact_selection: ArtifactSelectionState
    active_final_recommendation: str
    active_weighted_composite_score: float


class PortfolioHistoryDetail(OrbitModel):
    portfolio: PortfolioRecord
    canonical_portfolio: CanonicalPortfolioRecord
    source_documents: list[SourceDocumentRecord]
    latest_review_run_id: str | None = None
    review_run_count: int
    debate_count: int
    resynthesis_count: int
    items: list[ReviewHistoryItem]
    audit_events: list[AuditEventRecord]


class ArtifactInspectionDetail(OrbitModel):
    anchor_type: Literal["review_run", "debate", "resynthesis"]
    anchor_id: str
    lineage: LineagePath
    artifact_selection: ArtifactSelectionState
    portfolio: PortfolioRecord
    review_run: ReviewRunRecord
    debate_session: DebateSessionRecord | None = None
    resynthesis_session: ResynthesisSessionRecord | None = None
    original_scorecard: ScorecardRecord
    original_committee_report: CommitteeReportRecord
    active_scorecard: ScorecardRecord | ResynthesizedScorecardRecord
    active_committee_report: CommitteeReportRecord | ResynthesizedCommitteeReportRecord
    resynthesized_scorecard: ResynthesizedScorecardRecord | None = None
    resynthesized_committee_report: ResynthesizedCommitteeReportRecord | None = None
    review_audit_events: list[AuditEventRecord]
    debate_audit_events: list[AuditEventRecord] = []
    resynthesis_audit_events: list[AuditEventRecord] = []
    conflict_resolutions: list[ConflictResolutionRecord] = []


def _resolve_debate_bundle(
    repository: PersistenceRepository,
    review_bundle: ReviewPersistenceBundle,
) -> DebatePersistenceBundle | None:
    debates = repository.list_debate_bundles(run_id=review_bundle.review_run.run_id)
    return debates[0] if debates else None


def _resolve_resynthesis_bundle(
    repository: PersistenceRepository,
    debate_bundle: DebatePersistenceBundle | None,
) -> ResynthesisPersistenceBundle | None:
    if debate_bundle is None:
        return None
    resyntheses = repository.list_resynthesis_bundles(debate_id=debate_bundle.debate_session.debate_id)
    return resyntheses[0] if resyntheses else None


def _review_scope_audit_events(review_bundle: ReviewPersistenceBundle) -> list[AuditEventRecord]:
    allowed_actions = set(REVIEW_AUDIT_ACTIONS)
    return [event for event in review_bundle.audit_events if event.action in allowed_actions]


def _lineage_path(
    review_bundle: ReviewPersistenceBundle,
    debate_bundle: DebatePersistenceBundle | None = None,
    resynthesis_bundle: ResynthesisPersistenceBundle | None = None,
) -> LineagePath:
    return LineagePath(
        portfolio_id=review_bundle.portfolio.portfolio_id,
        review_run_id=review_bundle.review_run.run_id,
        debate_id=debate_bundle.debate_session.debate_id if debate_bundle is not None else None,
        resynthesis_id=(
            resynthesis_bundle.resynthesis_session.resynthesis_id
            if resynthesis_bundle is not None
            else None
        ),
    )


def _artifact_selection(
    review_bundle: ReviewPersistenceBundle,
    debate_bundle: DebatePersistenceBundle | None = None,
    resynthesis_bundle: ResynthesisPersistenceBundle | None = None,
) -> ArtifactSelectionState:
    original_scorecard_owner = ArtifactOwnerReference(
        owner_type="review_run",
        owner_id=review_bundle.review_run.run_id,
    )
    original_committee_report_owner = ArtifactOwnerReference(
        owner_type="review_run",
        owner_id=review_bundle.review_run.run_id,
    )
    active_artifact_source: Literal["original", "resynthesized"] = "original"
    active_scorecard_owner = original_scorecard_owner
    active_committee_report_owner = original_committee_report_owner
    has_resynthesized_artifacts = False

    if (
        resynthesis_bundle is not None
        and resynthesis_bundle.resynthesis_session.active_artifact_source == "resynthesized"
        and resynthesis_bundle.resynthesized_scorecard is not None
        and resynthesis_bundle.resynthesized_committee_report is not None
    ):
        active_artifact_source = "resynthesized"
        active_scorecard_owner = ArtifactOwnerReference(
            owner_type="resynthesis",
            owner_id=resynthesis_bundle.resynthesis_session.resynthesis_id,
        )
        active_committee_report_owner = ArtifactOwnerReference(
            owner_type="resynthesis",
            owner_id=resynthesis_bundle.resynthesis_session.resynthesis_id,
        )
        has_resynthesized_artifacts = True
    elif resynthesis_bundle is not None:
        has_resynthesized_artifacts = (
            resynthesis_bundle.resynthesized_scorecard is not None
            or resynthesis_bundle.resynthesized_committee_report is not None
        )

    score_change_required_count = 0
    if resynthesis_bundle is not None:
        score_change_required_count = resynthesis_bundle.resynthesis_session.score_change_required_count
    elif debate_bundle is not None:
        score_change_required_count = debate_bundle.debate_session.score_change_required_count

    return ArtifactSelectionState(
        active_artifact_source=active_artifact_source,
        original_scorecard_owner=original_scorecard_owner,
        original_committee_report_owner=original_committee_report_owner,
        active_scorecard_owner=active_scorecard_owner,
        active_committee_report_owner=active_committee_report_owner,
        has_resynthesized_artifacts=has_resynthesized_artifacts,
        score_change_required_count=score_change_required_count,
    )


def _active_scorecard(
    review_bundle: ReviewPersistenceBundle,
    resynthesis_bundle: ResynthesisPersistenceBundle | None = None,
) -> ScorecardRecord | ResynthesizedScorecardRecord:
    if (
        resynthesis_bundle is not None
        and resynthesis_bundle.resynthesis_session.active_artifact_source == "resynthesized"
        and resynthesis_bundle.resynthesized_scorecard is not None
    ):
        return resynthesis_bundle.resynthesized_scorecard
    return review_bundle.scorecard


def _active_committee_report(
    review_bundle: ReviewPersistenceBundle,
    resynthesis_bundle: ResynthesisPersistenceBundle | None = None,
) -> CommitteeReportRecord | ResynthesizedCommitteeReportRecord:
    if (
        resynthesis_bundle is not None
        and resynthesis_bundle.resynthesis_session.active_artifact_source == "resynthesized"
        and resynthesis_bundle.resynthesized_committee_report is not None
    ):
        return resynthesis_bundle.resynthesized_committee_report
    return review_bundle.committee_report


def _build_artifact_detail(
    *,
    anchor_type: Literal["review_run", "debate", "resynthesis"],
    anchor_id: str,
    review_bundle: ReviewPersistenceBundle,
    debate_bundle: DebatePersistenceBundle | None = None,
    resynthesis_bundle: ResynthesisPersistenceBundle | None = None,
) -> ArtifactInspectionDetail:
    return ArtifactInspectionDetail(
        anchor_type=anchor_type,
        anchor_id=anchor_id,
        lineage=_lineage_path(review_bundle, debate_bundle=debate_bundle, resynthesis_bundle=resynthesis_bundle),
        artifact_selection=_artifact_selection(review_bundle, debate_bundle=debate_bundle, resynthesis_bundle=resynthesis_bundle),
        portfolio=review_bundle.portfolio,
        review_run=review_bundle.review_run,
        debate_session=debate_bundle.debate_session if debate_bundle is not None else None,
        resynthesis_session=(
            resynthesis_bundle.resynthesis_session
            if resynthesis_bundle is not None
            else None
        ),
        original_scorecard=review_bundle.scorecard,
        original_committee_report=review_bundle.committee_report,
        active_scorecard=_active_scorecard(review_bundle, resynthesis_bundle=resynthesis_bundle),
        active_committee_report=_active_committee_report(review_bundle, resynthesis_bundle=resynthesis_bundle),
        resynthesized_scorecard=(
            resynthesis_bundle.resynthesized_scorecard
            if resynthesis_bundle is not None
            else None
        ),
        resynthesized_committee_report=(
            resynthesis_bundle.resynthesized_committee_report
            if resynthesis_bundle is not None
            else None
        ),
        review_audit_events=_review_scope_audit_events(review_bundle),
        debate_audit_events=debate_bundle.audit_events if debate_bundle is not None else [],
        resynthesis_audit_events=(
            resynthesis_bundle.audit_events
            if resynthesis_bundle is not None
            else []
        ),
        conflict_resolutions=(
            debate_bundle.conflict_resolutions
            if debate_bundle is not None
            else []
        ),
    )


class ReviewHistoryService:
    def __init__(self, repository: PersistenceRepository) -> None:
        self._repository = repository

    def get_portfolio_history(self, portfolio_id: str) -> PortfolioHistoryDetail | None:
        portfolio_bundle = self._repository.get_portfolio_bundle(portfolio_id)
        if portfolio_bundle is None:
            return None

        review_bundles = self._repository.list_review_run_bundles(portfolio_id=portfolio_id)
        items: list[ReviewHistoryItem] = []
        debate_count = 0
        resynthesis_count = 0

        for review_bundle in review_bundles:
            debate_bundle = _resolve_debate_bundle(self._repository, review_bundle)
            resynthesis_bundle = _resolve_resynthesis_bundle(self._repository, debate_bundle)
            if debate_bundle is not None:
                debate_count += 1
            if resynthesis_bundle is not None:
                resynthesis_count += 1
            active_scorecard = _active_scorecard(review_bundle, resynthesis_bundle=resynthesis_bundle)
            items.append(
                ReviewHistoryItem(
                    lineage=_lineage_path(review_bundle, debate_bundle=debate_bundle, resynthesis_bundle=resynthesis_bundle),
                    review_run=summarize_review_bundle(review_bundle),
                    debate=(
                        summarize_debate_bundle(debate_bundle)
                        if debate_bundle is not None
                        else None
                    ),
                    resynthesis=(
                        summarize_resynthesis_bundle(resynthesis_bundle)
                        if resynthesis_bundle is not None
                        else None
                    ),
                    artifact_selection=_artifact_selection(
                        review_bundle,
                        debate_bundle=debate_bundle,
                        resynthesis_bundle=resynthesis_bundle,
                    ),
                    active_final_recommendation=active_scorecard.final_recommendation,
                    active_weighted_composite_score=active_scorecard.weighted_composite_score,
                )
            )

        return PortfolioHistoryDetail(
            portfolio=portfolio_bundle.portfolio,
            canonical_portfolio=portfolio_bundle.canonical_portfolio,
            source_documents=portfolio_bundle.source_documents,
            latest_review_run_id=portfolio_bundle.portfolio.latest_review_run_id,
            review_run_count=len(review_bundles),
            debate_count=debate_count,
            resynthesis_count=resynthesis_count,
            items=items,
            audit_events=self._repository.list_audit_events(portfolio_id=portfolio_id),
        )

    def get_review_run_artifacts(self, run_id: str) -> ArtifactInspectionDetail | None:
        review_bundle = self._repository.get_review_run_bundle(run_id)
        if review_bundle is None:
            return None
        debate_bundle = _resolve_debate_bundle(self._repository, review_bundle)
        resynthesis_bundle = _resolve_resynthesis_bundle(self._repository, debate_bundle)
        return _build_artifact_detail(
            anchor_type="review_run",
            anchor_id=run_id,
            review_bundle=review_bundle,
            debate_bundle=debate_bundle,
            resynthesis_bundle=resynthesis_bundle,
        )

    def get_debate_artifacts(self, debate_id: str) -> ArtifactInspectionDetail | None:
        debate_bundle = self._repository.get_debate_bundle(debate_id)
        if debate_bundle is None:
            return None
        review_bundle = self._repository.get_review_run_bundle(debate_bundle.review_run.run_id)
        if review_bundle is None:
            return None
        resynthesis_bundle = _resolve_resynthesis_bundle(self._repository, debate_bundle)
        return _build_artifact_detail(
            anchor_type="debate",
            anchor_id=debate_id,
            review_bundle=review_bundle,
            debate_bundle=debate_bundle,
            resynthesis_bundle=resynthesis_bundle,
        )

    def get_resynthesis_artifacts(self, resynthesis_id: str) -> ArtifactInspectionDetail | None:
        resynthesis_bundle = self._repository.get_resynthesis_bundle(resynthesis_id)
        if resynthesis_bundle is None:
            return None
        review_bundle = self._repository.get_review_run_bundle(resynthesis_bundle.review_run.run_id)
        debate_bundle = self._repository.get_debate_bundle(resynthesis_bundle.debate_session.debate_id)
        if review_bundle is None or debate_bundle is None:
            return None
        return _build_artifact_detail(
            anchor_type="resynthesis",
            anchor_id=resynthesis_id,
            review_bundle=review_bundle,
            debate_bundle=debate_bundle,
            resynthesis_bundle=resynthesis_bundle,
        )
