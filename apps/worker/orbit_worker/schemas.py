from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .domain import AGENT_REGISTRY, PORTFOLIO_SECTIONS, RECOMMENDATION_RANK, SCORE_DIMENSIONS, SEVERITY_RANK
from .llm_specs import LLM_AGENT_REGISTRY


class OrbitModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceDocument(OrbitModel):
    id: str
    kind: str
    title: str
    path: str


class PortfolioSection(OrbitModel):
    title: str
    summary: str
    key_points: list[str]
    raw_text: str
    evidence_ref: str


class CanonicalPortfolio(OrbitModel):
    portfolio_id: str
    portfolio_name: str
    portfolio_type: str
    owner: str
    submitted_at: str
    source_documents: list[SourceDocument]
    sections: dict[str, PortfolioSection]


class ScoreImpact(OrbitModel):
    dimension: str
    delta: float
    rationale: str


class Finding(OrbitModel):
    finding_id: str
    title: str
    category: str
    severity: str
    claim: str
    evidence_refs: list[str]
    assumptions: list[str]
    recommended_action: str
    score_impacts: list[ScoreImpact]


class ReportFinding(Finding):
    agent_id: str


class DimensionScore(OrbitModel):
    dimension: str
    score: float
    confidence: float
    evidence_completeness: float
    severity_flags: list[str]
    rationale: str
    evidence_refs: list[str]


class EvidenceReasoning(OrbitModel):
    claim: str
    evidence: list[str]
    risk: list[str]
    implication: str
    score: float
    confidence: Literal["Low", "Medium", "High"]


class HumanReview(OrbitModel):
    human_review_id: str
    portfolio_id: str
    reviewer_name: str
    final_recommendation: str
    score: float
    identified_risks: list[str]
    confidence: Literal["Low", "Medium", "High"]
    review_notes: str
    submitted_at: datetime


class DecisionValidation(OrbitModel):
    decision_validation_id: str
    portfolio_id: str
    review_run_id: str
    human_review_id: str
    orbit_recommendation: str
    orbit_score: float
    human_recommendation: str
    human_score: float
    recommendation_match: Literal["match", "partial", "mismatch"]
    score_difference: float
    risk_overlap: float
    risk_recall: float
    risk_precision: float
    confidence_alignment: float
    agreement_score: float
    validated_at: datetime


class ReviewMetadata(OrbitModel):
    prompt_contract_version: str
    model_provider: str
    model_name: str
    duration_ms: int
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)
    activation_tier: str = "specialist"
    activation_status: str = "executed"
    activation_reason: str = ""
    routing_strategy_version: str | None = None


class AgentReview(OrbitModel):
    agent_id: str
    agent_name: str
    portfolio_id: str
    review_summary: str
    reasoning: EvidenceReasoning | None = None
    findings: list[Finding]
    dimension_scores: list[DimensionScore]
    recommendation: str
    open_questions: list[str]
    evidence_gaps: list[str]
    assumption_register: list[str]
    review_metadata: ReviewMetadata


class ConflictRecord(OrbitModel):
    conflict_id: str
    conflict_type: str
    topic: str
    participants: list[str]
    conflicting_agents: list[str] = Field(default_factory=list)
    conflicting_claims: list[str] = Field(default_factory=list)
    conflicting_evidence: list[str] = Field(default_factory=list)
    severity: str
    conflict_category: str | None = None
    conflict_reason: str | None = None
    trigger_reason: str
    supporting_artifacts: list[str]
    debate_required: bool
    routing_reason: str
    status: str


class DebatePosition(OrbitModel):
    agent_id: str
    agent_name: str
    recommendation: str
    conflict_view: str
    cited_evidence_refs: list[str]
    dimension_focus: list[str]


class DebateRound(OrbitModel):
    round_index: int
    focus: str
    moderator_prompt: str
    participant_positions: list[DebatePosition]
    moderator_observation: str
    exit_criteria_met: bool


class ConflictResolution(OrbitModel):
    resolution_id: str
    conflict_id: str
    conflict_type: str
    topic: str
    outcome: str
    resolution_summary: str
    moderator_rationale: str
    applied_conditions: list[str]
    score_change_required: bool
    score_change_rationale: str | None = None
    follow_up_action: str
    status: str


class DebateSession(OrbitModel):
    debate_id: str
    run_id: str
    portfolio_id: str
    moderator_id: str
    moderator_name: str
    debate_status: str
    max_rounds: int
    rounds: list[DebateRound]
    resolutions: list[ConflictResolution]
    executive_summary: str
    audit_notes: list[str]


class ResynthesisSession(OrbitModel):
    resynthesis_id: str
    debate_id: str
    run_id: str
    portfolio_id: str
    resynthesis_status: Literal["completed_without_changes", "completed_with_recheck"]
    score_change_required_count: int
    reused_original_artifacts: bool
    active_artifact_source: Literal["original", "resynthesized"]
    applied_resolution_ids: list[str]
    executive_summary: str
    audit_notes: list[str]


class DeliberationEntry(OrbitModel):
    run_id: str
    portfolio_id: str
    sequence_number: int = Field(ge=1)
    phase: Literal[
        "opening_statements",
        "conflict_identification",
        "conflict_discussion",
        "moderator_synthesis",
        "final_verdict",
    ]
    agent_id: str | None = None
    agent_role: str
    statement_type: Literal[
        "opening_statement",
        "conflict_identified",
        "conflict_argument",
        "moderator_synthesis",
        "final_verdict",
        "phase_note",
    ]
    statement_text: str
    conflict_reference: str | None = None
    created_at: datetime


class Scorecard(OrbitModel):
    portfolio_id: str
    run_id: str
    dimension_scores: list[DimensionScore]
    weighted_composite_score: float
    average_confidence: float
    average_evidence_completeness: float
    severity_flags: list[str]
    final_recommendation: str
    override_applied: bool
    conditions: list[str]


class CommitteeReport(OrbitModel):
    portfolio_id: str
    run_id: str
    executive_summary: str
    top_findings: list[ReportFinding]
    top_conflicts: list[ConflictRecord]
    conditions: list[str]
    audit_notes: list[str]
    markdown: str


def _require_non_empty(value: Any, message: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(message)


def validate_canonical_portfolio(portfolio: Any) -> CanonicalPortfolio:
    model = CanonicalPortfolio.model_validate(portfolio)
    _require_non_empty(model.portfolio_id, "Canonical portfolio requires portfolio_id.")
    _require_non_empty(model.portfolio_name, "Canonical portfolio requires portfolio_name.")
    _require_non_empty(model.portfolio_type, "Canonical portfolio requires portfolio_type.")
    _require_non_empty(model.owner, "Canonical portfolio requires owner.")
    _require_non_empty(model.submitted_at, "Canonical portfolio requires submitted_at.")
    for section in PORTFOLIO_SECTIONS:
        value = model.sections.get(section["key"])
        if value is None:
            raise ValueError(f"Missing section {section['key']}.")
        _require_non_empty(value.title, f"Section {section['key']} requires title.")
        _require_non_empty(value.summary, f"Section {section['key']} requires summary.")
        if not isinstance(value.key_points, list):
            raise ValueError(f"Section {section['key']} requires key_points.")
    return model


def validate_finding(finding: Any) -> Finding:
    model = Finding.model_validate(finding)
    if model.severity not in SEVERITY_RANK:
        raise ValueError(f"Unsupported severity {model.severity}.")
    return model


def validate_dimension_score(score: Any) -> DimensionScore:
    model = DimensionScore.model_validate(score)
    if model.dimension not in SCORE_DIMENSIONS:
        raise ValueError(f"Unsupported dimension {model.dimension}.")
    return model


def validate_agent_review(review: Any) -> AgentReview:
    model = AgentReview.model_validate(review)
    known_agent_ids = {agent.id for agent in AGENT_REGISTRY} | {agent.id for agent in LLM_AGENT_REGISTRY}
    if model.agent_id not in known_agent_ids:
        raise ValueError(f"Unknown agent_id {model.agent_id}.")
    if model.recommendation not in RECOMMENDATION_RANK:
        raise ValueError(f"Unsupported recommendation {model.recommendation}.")
    for finding in model.findings:
        validate_finding(finding)
    for score in model.dimension_scores:
        validate_dimension_score(score)
    return model


def validate_conflict_record(conflict: Any) -> ConflictRecord:
    return ConflictRecord.model_validate(conflict)


def validate_conflict_resolution(resolution: Any) -> ConflictResolution:
    return ConflictResolution.model_validate(resolution)


def validate_debate_session(session: Any) -> DebateSession:
    model = DebateSession.model_validate(session)
    for resolution in model.resolutions:
        validate_conflict_resolution(resolution)
    return model


def validate_resynthesis_session(session: Any) -> ResynthesisSession:
    return ResynthesisSession.model_validate(session)


def validate_deliberation_entry(entry: Any) -> DeliberationEntry:
    model = DeliberationEntry.model_validate(entry)
    _require_non_empty(model.run_id, "Deliberation entry requires run_id.")
    _require_non_empty(model.portfolio_id, "Deliberation entry requires portfolio_id.")
    _require_non_empty(model.agent_role, "Deliberation entry requires agent_role.")
    _require_non_empty(model.statement_text, "Deliberation entry requires statement_text.")
    return model


def validate_scorecard(scorecard: Any) -> Scorecard:
    model = Scorecard.model_validate(scorecard)
    if model.final_recommendation not in RECOMMENDATION_RANK:
        raise ValueError(f"Unsupported final recommendation {model.final_recommendation}.")
    for score in model.dimension_scores:
        validate_dimension_score(score)
    return model


def validate_committee_report(report: Any) -> CommitteeReport:
    model = CommitteeReport.model_validate(report)
    for finding in model.top_findings:
        validate_finding(finding.model_dump(mode="json", exclude={"agent_id"}))
    for conflict in model.top_conflicts:
        validate_conflict_record(conflict)
    return model
