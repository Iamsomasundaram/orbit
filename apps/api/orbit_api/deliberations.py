from __future__ import annotations

from orbit_worker.deliberation import PHASE_ORDER, build_deliberation_entries
from orbit_worker.persistence import (
    ConflictPersistenceRecord,
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


class AgentRuntimeTelemetry(OrbitModel):
    agent_id: str
    agent_role: str
    recommendation: str
    model_provider: str
    model_name: str
    duration_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class CommitteeRuntimeMetadata(OrbitModel):
    requested_runtime_mode: str
    effective_runtime_mode: str
    requested_provider: str
    requested_model_name: str
    runtime_mode: str
    model_provider: str
    model_name: str
    prompt_contract_version: str
    agent_count: int
    total_duration_ms: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    fallback_applied: bool = False
    fallback_reason: str | None = None
    fallback_category: str | None = None
    agents: list[AgentRuntimeTelemetry]


class ReviewRunDeliberationDetail(OrbitModel):
    review_run_id: str
    portfolio_id: str
    lineage: LineagePath
    artifact_selection: ArtifactSelectionState
    final_recommendation: str
    weighted_composite_score: float
    entry_count: int
    runtime_metadata: CommitteeRuntimeMetadata
    conflicts: list[ConflictPersistenceRecord]
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


def _runtime_mode(model_provider: str) -> str:
    return "deterministic" if model_provider == "deterministic-thin-slice" else "llm"


def _runtime_metadata(review_bundle) -> CommitteeRuntimeMetadata:
    if not review_bundle.agent_reviews:
        return CommitteeRuntimeMetadata(
            requested_runtime_mode="deterministic",
            effective_runtime_mode="deterministic",
            requested_provider="deterministic-thin-slice",
            requested_model_name="deterministic-thin-slice-v1",
            runtime_mode="deterministic",
            model_provider="unknown",
            model_name="unknown",
            prompt_contract_version=review_bundle.review_run.prompt_contract_version,
            agent_count=0,
            total_duration_ms=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            estimated_cost_usd=0.0,
            fallback_applied=False,
            fallback_reason=None,
            fallback_category=None,
            agents=[],
        )

    agents = [
        AgentRuntimeTelemetry(
            agent_id=record.agent_id,
            agent_role=record.review_payload.agent_name,
            recommendation=record.review_payload.recommendation,
            model_provider=record.review_payload.review_metadata.model_provider,
            model_name=record.review_payload.review_metadata.model_name,
            duration_ms=record.review_payload.review_metadata.duration_ms,
            input_tokens=record.review_payload.review_metadata.input_tokens,
            output_tokens=record.review_payload.review_metadata.output_tokens,
            total_tokens=record.review_payload.review_metadata.total_tokens,
            estimated_cost_usd=record.review_payload.review_metadata.estimated_cost_usd,
        )
        for record in review_bundle.agent_reviews
    ]
    first = agents[0]
    effective_runtime_mode = _runtime_mode(first.model_provider)
    fallback_event = next(
        (event for event in review_bundle.audit_events if event.action == "review_run.runtime_fallback"),
        None,
    )
    created_event = next(
        (event for event in review_bundle.audit_events if event.action == "review_run.created"),
        None,
    )
    requested_runtime_mode = effective_runtime_mode
    requested_provider = first.model_provider
    requested_model_name = first.model_name
    fallback_applied = False
    fallback_reason = None
    fallback_category = None
    if created_event is not None:
        requested_runtime_mode = str(
            created_event.event_payload.get("requested_runtime_mode", effective_runtime_mode)
        )
        requested_provider = str(
            created_event.event_payload.get("requested_provider", first.model_provider)
        )
        requested_model_name = str(
            created_event.event_payload.get("requested_model_name", first.model_name)
        )
    if fallback_event is not None:
        fallback_applied = True
        fallback_reason = str(fallback_event.event_payload.get("fallback_reason", "")).strip() or None
        fallback_category = str(fallback_event.event_payload.get("failure_category", "")).strip() or None
        requested_runtime_mode = str(
            fallback_event.event_payload.get("requested_runtime_mode", requested_runtime_mode)
        )
        requested_provider = str(
            fallback_event.event_payload.get("requested_provider", requested_provider)
        )
        requested_model_name = str(
            fallback_event.event_payload.get("requested_model_name", requested_model_name)
        )
    return CommitteeRuntimeMetadata(
        requested_runtime_mode=requested_runtime_mode,
        effective_runtime_mode=effective_runtime_mode,
        requested_provider=requested_provider,
        requested_model_name=requested_model_name,
        runtime_mode=effective_runtime_mode,
        model_provider=first.model_provider,
        model_name=first.model_name,
        prompt_contract_version=review_bundle.review_run.prompt_contract_version,
        agent_count=len(agents),
        total_duration_ms=sum(agent.duration_ms for agent in agents),
        total_input_tokens=sum(agent.input_tokens for agent in agents),
        total_output_tokens=sum(agent.output_tokens for agent in agents),
        total_tokens=sum(agent.total_tokens for agent in agents),
        estimated_cost_usd=round(sum(agent.estimated_cost_usd for agent in agents), 8),
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason,
        fallback_category=fallback_category,
        agents=agents,
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
        review_bundle = self._repository.get_review_run_bundle(run_id)
        if review_bundle is None:
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
            runtime_metadata=_runtime_metadata(review_bundle),
            conflicts=review_bundle.conflicts,
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
