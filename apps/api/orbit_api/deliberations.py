from __future__ import annotations

from orbit_worker.deliberation import PHASE_ORDER, build_deliberation_entries
from orbit_worker.persistence import (
    DeliberationEntryRecord,
    PersistenceRepository,
    build_deliberation_persistence_bundle,
)
from orbit_worker.schemas import OrbitModel

from .history import ArtifactSelectionState, LineagePath, ReviewHistoryService

PHASE_LABELS = {
    "opening_statements": "Opening Statements",
    "conflict_identification": "Conflict Identification",
    "conflict_discussion": "Conflict Discussion",
    "moderator_synthesis": "Moderator Synthesis",
    "final_verdict": "Final Verdict",
}


class DeliberationPhaseSummary(OrbitModel):
    phase: str
    label: str
    entry_count: int
    representative_statement: str
    conflict_references: list[str]


class ReviewRunDeliberationDetail(OrbitModel):
    review_run_id: str
    portfolio_id: str
    lineage: LineagePath
    artifact_selection: ArtifactSelectionState
    final_recommendation: str
    weighted_composite_score: float
    entry_count: int
    entries: list[DeliberationEntryRecord]


class ReviewRunDeliberationSummary(OrbitModel):
    review_run_id: str
    portfolio_id: str
    final_recommendation: str
    weighted_composite_score: float
    active_artifact_source: str
    phase_summaries: list[DeliberationPhaseSummary]


def _resolve_debate_bundle(repository: PersistenceRepository, run_id: str):
    bundles = repository.list_debate_bundles(run_id=run_id)
    return bundles[0] if bundles else None


def _resolve_resynthesis_bundle(repository: PersistenceRepository, debate_bundle):
    if debate_bundle is None:
        return None
    bundles = repository.list_resynthesis_bundles(debate_id=debate_bundle.debate_session.debate_id)
    return bundles[0] if bundles else None


def _phase_summary(entries: list[DeliberationEntryRecord], phase: str) -> DeliberationPhaseSummary:
    conflict_references = []
    for entry in entries:
        if entry.conflict_reference and entry.conflict_reference not in conflict_references:
            conflict_references.append(entry.conflict_reference)
    return DeliberationPhaseSummary(
        phase=phase,
        label=PHASE_LABELS[phase],
        entry_count=len(entries),
        representative_statement=entries[0].statement_text if entries else "No persisted statements were recorded for this phase.",
        conflict_references=conflict_references,
    )


class DeliberationService:
    def __init__(self, repository: PersistenceRepository) -> None:
        self._repository = repository
        self._history = ReviewHistoryService(repository=repository)

    def refresh_review_run(self, run_id: str) -> None:
        review_bundle = self._repository.get_review_run_bundle(run_id)
        if review_bundle is None:
            return
        debate_bundle = _resolve_debate_bundle(self._repository, run_id)
        resynthesis_bundle = _resolve_resynthesis_bundle(self._repository, debate_bundle)
        entries = build_deliberation_entries(
            review_bundle,
            debate_bundle=debate_bundle,
            resynthesis_bundle=resynthesis_bundle,
        )
        bundle = build_deliberation_persistence_bundle(
            portfolio=review_bundle.portfolio,
            review_run=review_bundle.review_run,
            entries=entries,
        )
        self._repository.replace_deliberation_bundle(bundle)

    def get_review_run_deliberation(self, run_id: str) -> ReviewRunDeliberationDetail | None:
        bundle = self._repository.get_deliberation_bundle(run_id)
        if bundle is None:
            return None
        artifacts = self._history.get_review_run_artifacts(run_id)
        if artifacts is None:
            return None
        return ReviewRunDeliberationDetail(
            review_run_id=bundle.review_run.run_id,
            portfolio_id=bundle.portfolio.portfolio_id,
            lineage=artifacts.lineage,
            artifact_selection=artifacts.artifact_selection,
            final_recommendation=artifacts.active_scorecard.final_recommendation,
            weighted_composite_score=artifacts.active_scorecard.weighted_composite_score,
            entry_count=len(bundle.entries),
            entries=bundle.entries,
        )

    def get_review_run_deliberation_summary(self, run_id: str) -> ReviewRunDeliberationSummary | None:
        detail = self.get_review_run_deliberation(run_id)
        if detail is None:
            return None

        phase_summaries: list[DeliberationPhaseSummary] = []
        for phase in PHASE_ORDER:
            phase_entries = [entry for entry in detail.entries if entry.phase == phase]
            phase_summaries.append(_phase_summary(phase_entries, phase))

        return ReviewRunDeliberationSummary(
            review_run_id=detail.review_run_id,
            portfolio_id=detail.portfolio_id,
            final_recommendation=detail.final_recommendation,
            weighted_composite_score=detail.weighted_composite_score,
            active_artifact_source=detail.artifact_selection.active_artifact_source,
            phase_summaries=phase_summaries,
        )
