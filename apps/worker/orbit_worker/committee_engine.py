from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

from pydantic import Field, ValidationError

from .domain import RECOMMENDATION_ORDER, RECOMMENDATION_RANK, clamp_score, clamp_unit, dedupe_preserve_order
from .llm_provider import (
    AnthropicPlaceholderProvider,
    LLMProviderError,
    LocalPlaceholderProvider,
    OpenAIResponsesProvider,
    StructuredLLMProvider,
    resolve_api_key,
)
from .llm_specs import (
    DIMENSION_TO_CATEGORY,
    LLM_AGENT_REGISTRY,
    RISK_CATEGORIES,
    LLMCommitteeAgentSpec,
    LLMCommitteeResponse,
    allowed_evidence_refs,
    build_shared_portfolio_context,
)
from .reviewer import run_specialist_reviews
from .schemas import AgentReview, CanonicalPortfolio, DimensionScore, Finding, OrbitModel, ScoreImpact, validate_agent_review

RuntimeMode = Literal["deterministic", "llm"]
logger = logging.getLogger(__name__)

RECOMMENDATION_ALIASES = {
    "strong_proceed": "Strong Proceed",
    "strong proceed": "Strong Proceed",
    "proceed_with_conditions": "Proceed with Conditions",
    "proceed with conditions": "Proceed with Conditions",
    "pilot_only": "Pilot Only",
    "pilot only": "Pilot Only",
    "high_risk": "High Risk",
    "high risk": "High Risk",
    "do_not_proceed": "Do Not Proceed",
    "do not proceed": "Do Not Proceed",
}
SEVERITY_ALIASES = {
    "info": "informational",
    "informational": "informational",
    "minor": "minor",
    "moderate": "moderate",
    "medium": "moderate",
    "major": "major",
    "critical": "critical",
}
CATEGORY_ALIASES = {
    **{value.lower(): value for value in RISK_CATEGORIES},
    **{dimension.lower(): category for dimension, category in DIMENSION_TO_CATEGORY.items()},
}
SEVERITY_SCORE_CAPS = {
    "critical": 2.6,
    "major": 3.2,
    "moderate": 4.0,
    "minor": 4.4,
    "informational": 5.0,
}
RECOMMENDATION_SCORE_CAPS = {
    "Strong Proceed": 5.0,
    "Proceed with Conditions": 4.4,
    "Pilot Only": 3.6,
    "High Risk": 2.8,
    "Do Not Proceed": 2.0,
}
ADAPTIVE_ROUTING_VERSION = "m13-adaptive-v1"
CORE_AGENT_IDS = tuple(spec.id for spec in LLM_AGENT_REGISTRY if spec.activation_tier == "core")


class CommitteeRuntimeOptions(OrbitModel):
    runtime_mode: RuntimeMode = "deterministic"
    llm_provider: str = "openai"
    llm_max_concurrency: int = Field(default=6, ge=1)
    llm_request_timeout_seconds: int = Field(default=25, ge=1)
    llm_max_output_tokens: int = Field(default=700, ge=200)
    openai_api_key: str = ""
    openai_api_key_file: str = "/workspace/key.txt"
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = ""
    local_llm_base_url: str = ""
    local_llm_model: str = ""

    @classmethod
    def from_settings(cls, settings: Any) -> "CommitteeRuntimeOptions":
        return cls(
            runtime_mode=getattr(settings, "llm_runtime_mode", "llm"),
            llm_provider=getattr(settings, "llm_provider", "openai"),
            llm_max_concurrency=getattr(settings, "llm_max_concurrency", 6),
            llm_request_timeout_seconds=getattr(settings, "llm_request_timeout_seconds", 25),
            llm_max_output_tokens=getattr(settings, "llm_max_output_tokens", 700),
            openai_api_key=getattr(settings, "openai_api_key", ""),
            openai_api_key_file=getattr(settings, "openai_api_key_file", "/workspace/key.txt"),
            openai_model=getattr(settings, "openai_model", "gpt-4o-mini"),
            anthropic_api_key=getattr(settings, "anthropic_api_key", ""),
            anthropic_model=getattr(settings, "anthropic_model", ""),
            local_llm_base_url=getattr(settings, "local_llm_base_url", ""),
            local_llm_model=getattr(settings, "local_llm_model", ""),
        )


class CommitteeExecutionResult(OrbitModel):
    agent_reviews: list[AgentReview]
    requested_runtime_mode: RuntimeMode
    effective_runtime_mode: RuntimeMode
    requested_provider: str
    requested_model_name: str
    effective_provider: str
    effective_model_name: str
    fallback_applied: bool = False
    fallback_reason: str | None = None
    failure_category: str | None = None
    routing_strategy_version: str | None = None
    core_agent_ids: list[str] = Field(default_factory=list)
    activated_specialist_ids: list[str] = Field(default_factory=list)
    passive_specialist_ids: list[str] = Field(default_factory=list)
    routing_signals: list[str] = Field(default_factory=list)


class AdaptiveRoutingDecision(OrbitModel):
    routing_strategy_version: str = ADAPTIVE_ROUTING_VERSION
    core_agent_ids: list[str]
    activated_specialist_ids: list[str]
    passive_specialist_ids: list[str]
    activation_reasons: dict[str, str]
    routing_signals: list[str]


class RoutedCommitteeReviews(OrbitModel):
    agent_reviews: list[AgentReview]
    routing_decision: AdaptiveRoutingDecision


def _normalize_recommendation(value: str) -> str:
    normalized = RECOMMENDATION_ALIASES.get(value.strip().lower())
    if normalized:
        return normalized
    return "Pilot Only"


def _normalize_severity(value: str) -> str:
    return SEVERITY_ALIASES.get(value.strip().lower(), "moderate")


def _normalize_category(value: str, fallback_dimension: str) -> str:
    normalized = CATEGORY_ALIASES.get(value.strip().lower())
    if normalized:
        return normalized
    return DIMENSION_TO_CATEGORY.get(fallback_dimension, "governance")


def _sanitize_text(value: str, fallback: str, *, max_length: int = 280) -> str:
    candidate = " ".join((value or "").split())
    if not candidate:
        candidate = fallback
    return candidate[:max_length]


def _sanitize_text_list(values: list[str], *, limit: int, fallback: list[str] | None = None) -> list[str]:
    sanitized = [
        " ".join(value.split())[:220]
        for value in values
        if isinstance(value, str) and value.strip()
    ]
    if sanitized:
        return sanitized[:limit]
    return (fallback or [])[:limit]


def _portfolio_text(portfolio: CanonicalPortfolio, section_keys: list[str] | None = None) -> str:
    keys = section_keys or list(portfolio.sections.keys())
    fragments: list[str] = []
    for key in keys:
        section = portfolio.sections.get(key)
        if section is None:
            continue
        fragments.append(section.summary)
        fragments.extend(section.key_points)
        fragments.append(section.raw_text)
    return "\n".join(fragments).lower()


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _dimension_average(reviews: list[AgentReview], dimension: str) -> float:
    scores = [
        score.score
        for review in reviews
        for score in review.dimension_scores
        if score.dimension == dimension
    ]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def _has_high_severity_findings(reviews: list[AgentReview], categories: set[str]) -> bool:
    for review in reviews:
        for finding in review.findings:
            if finding.category in categories and finding.severity in {"major", "critical"}:
                return True
    return False


def _consensus_recommendation(reviews: list[AgentReview]) -> str:
    if not reviews:
        return "Pilot Only"
    rank_total = sum(RECOMMENDATION_RANK[review.recommendation] for review in reviews)
    consensus_rank = min(len(RECOMMENDATION_ORDER) - 1, max(0, int((rank_total / len(reviews)) + 0.5)))
    return RECOMMENDATION_ORDER[consensus_rank]


def _review_with_activation_metadata(
    review: AgentReview,
    spec: LLMCommitteeAgentSpec,
    *,
    activation_status: str,
    activation_reason: str,
) -> AgentReview:
    return review.model_copy(
        update={
            "review_metadata": review.review_metadata.model_copy(
                update={
                    "activation_tier": spec.activation_tier,
                    "activation_status": activation_status,
                    "activation_reason": activation_reason,
                    "routing_strategy_version": ADAPTIVE_ROUTING_VERSION,
                }
            )
        }
    )


def _passive_observer_review(
    spec: LLMCommitteeAgentSpec,
    portfolio: CanonicalPortfolio,
    *,
    consensus_recommendation: str,
    provider_name: str,
    model_name: str,
    activation_reason: str,
) -> AgentReview:
    return validate_agent_review(
        {
            "agent_id": spec.id,
            "agent_name": spec.name,
            "portfolio_id": portfolio.portfolio_id,
            "review_summary": (
                f"Passive observer. {spec.name} was not deeply activated because {activation_reason.lower()} "
                f"The agent aligns with the core screening consensus of {consensus_recommendation}."
            ),
            "findings": [],
            "dimension_scores": [],
            "recommendation": consensus_recommendation,
            "open_questions": [],
            "evidence_gaps": [],
            "assumption_register": [],
            "review_metadata": {
                "prompt_contract_version": "m13-llm-adaptive-v1",
                "model_provider": provider_name,
                "model_name": model_name,
                "duration_ms": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "activation_tier": spec.activation_tier,
                "activation_status": "passive_observer",
                "activation_reason": activation_reason,
                "routing_strategy_version": ADAPTIVE_ROUTING_VERSION,
            },
        }
    )


def _normalize_evidence_refs(requested_refs: list[str], *, fallback_refs: list[str], allowed_refs: set[str]) -> list[str]:
    normalized = [value for value in requested_refs if value in allowed_refs]
    if normalized:
        return dedupe_preserve_order(normalized)[:6]
    return fallback_refs[:6]


def _default_assumption(spec: LLMCommitteeAgentSpec) -> str:
    return f"{spec.default_assumption_topic}=needs_validation"


def _normalize_assumptions(values: list[str], spec: LLMCommitteeAgentSpec) -> list[str]:
    normalized = []
    for value in values:
        candidate = " ".join(value.split())
        if "=" not in candidate:
            continue
        topic, assumption_value = candidate.split("=", 1)
        topic = topic.strip().lower().replace(" ", "_")
        assumption_value = assumption_value.strip().lower().replace(" ", "_")
        if not topic or not assumption_value:
            continue
        normalized.append(f"{topic}={assumption_value}")
    if normalized:
        return dedupe_preserve_order(normalized)[:3]
    return [_default_assumption(spec)]


def _default_dimension_score(spec: LLMCommitteeAgentSpec, dimension: str, fallback_refs: list[str]) -> DimensionScore:
    return DimensionScore.model_validate(
        {
            "dimension": dimension,
            "score": 3.0,
            "confidence": 0.45,
            "evidence_completeness": 0.45,
            "severity_flags": [],
            "rationale": f"{spec.name} fell back to a neutral placeholder because the llm response omitted a usable {dimension} contribution.",
            "evidence_refs": fallback_refs,
        }
    )


def _normalize_dimension_scores(
    spec: LLMCommitteeAgentSpec,
    response: LLMCommitteeResponse,
    *,
    fallback_refs: list[str],
    allowed_refs: set[str],
) -> list[DimensionScore]:
    by_dimension: dict[str, DimensionScore] = {}
    for score in response.score_contributions:
        if score.dimension not in spec.owned_dimensions or score.dimension in by_dimension:
            continue
        by_dimension[score.dimension] = DimensionScore.model_validate(
            {
                "dimension": score.dimension,
                "score": clamp_score(score.score),
                "confidence": clamp_unit(score.confidence),
                "evidence_completeness": clamp_unit(score.evidence_completeness),
                "severity_flags": _sanitize_text_list(score.severity_flags, limit=4),
                "rationale": _sanitize_text(
                    score.rationale,
                    f"{spec.name} provided a structured contribution for {score.dimension}.",
                ),
                "evidence_refs": _normalize_evidence_refs(
                    score.evidence_refs,
                    fallback_refs=fallback_refs,
                    allowed_refs=allowed_refs,
                ),
            }
        )

    for dimension in spec.owned_dimensions:
        if dimension not in by_dimension:
            by_dimension[dimension] = _default_dimension_score(spec, dimension, fallback_refs)
    return [by_dimension[dimension] for dimension in spec.owned_dimensions]


def _finding_dimensions(spec: LLMCommitteeAgentSpec, category: str) -> list[str]:
    matching = [
        dimension
        for dimension in spec.owned_dimensions
        if DIMENSION_TO_CATEGORY.get(dimension) == category
    ]
    if matching:
        return matching
    return spec.owned_dimensions[:1]


def _build_finding(
    spec: LLMCommitteeAgentSpec,
    index: int,
    risk: Any,
    *,
    fallback_refs: list[str],
    allowed_refs: set[str],
) -> Finding:
    category = _normalize_category(risk.category, spec.owned_dimensions[0])
    impacted_dimensions = _finding_dimensions(spec, category)
    return Finding.model_validate(
        {
            "finding_id": f"{spec.id}-risk-{index:02d}",
            "title": _sanitize_text(risk.title, f"{spec.name} identified a material portfolio risk.", max_length=120),
            "category": category,
            "severity": _normalize_severity(risk.severity),
            "claim": _sanitize_text(risk.claim, f"{spec.name} identified a material risk that requires committee attention."),
            "evidence_refs": _normalize_evidence_refs(
                risk.evidence_refs,
                fallback_refs=fallback_refs,
                allowed_refs=allowed_refs,
            ),
            "assumptions": _sanitize_text_list(risk.assumptions, limit=3),
            "recommended_action": _sanitize_text(
                risk.recommended_action,
                f"{spec.name} recommends closing this risk before broader rollout.",
                max_length=200,
            ),
            "score_impacts": [
                ScoreImpact.model_validate(
                    {
                        "dimension": dimension,
                        "delta": -0.2,
                        "rationale": f"{spec.name} associates the identified risk with {dimension}.",
                    }
                )
                for dimension in impacted_dimensions
            ],
        }
    )


def _evidence_score_cap(evidence_completeness: float) -> float:
    if evidence_completeness < 0.5:
        return 3.0
    if evidence_completeness < 0.65:
        return 3.6
    if evidence_completeness < 0.8:
        return 4.2
    return 5.0


def _finding_score_cap(dimension: str, findings: list[Finding]) -> float:
    relevant_categories = {DIMENSION_TO_CATEGORY.get(dimension, "")}
    if dimension in {"Security & Compliance", "AI Reliability"}:
        relevant_categories.add("governance")
    matching_findings = [finding for finding in findings if finding.category in relevant_categories]
    if not matching_findings:
        return 5.0
    highest_severity = max(
        matching_findings,
        key=lambda finding: ["informational", "minor", "moderate", "major", "critical"].index(finding.severity),
    ).severity
    return SEVERITY_SCORE_CAPS[highest_severity]


def _calibrate_dimension_scores(
    recommendation: str,
    dimension_scores: list[DimensionScore],
    findings: list[Finding],
) -> list[DimensionScore]:
    calibrated_scores: list[DimensionScore] = []
    recommendation_cap = RECOMMENDATION_SCORE_CAPS[recommendation]
    for score in dimension_scores:
        capped_score = min(
            score.score,
            recommendation_cap,
            _evidence_score_cap(score.evidence_completeness),
            _finding_score_cap(score.dimension, findings),
        )
        if capped_score == score.score:
            calibrated_scores.append(score)
            continue
        calibrated_scores.append(
            DimensionScore.model_validate(
                {
                    **score.model_dump(mode="json"),
                    "score": clamp_score(capped_score),
                    "rationale": f"{score.rationale} Committee normalization capped the score to preserve evidence and risk discipline.",
                }
            )
        )
    return calibrated_scores


def _system_prompt(spec: LLMCommitteeAgentSpec) -> str:
    dimensions = ", ".join(spec.owned_dimensions)
    return (
        f"You are the {spec.name} in ORBIT, an enterprise portfolio review committee. "
        "Evaluate only the supplied portfolio context. Do not invent evidence, do not expose chain-of-thought, "
        "and do not write markdown. Return compact structured JSON only. "
        f"Your owned score dimensions are: {dimensions}. "
        "Use recommendation values exactly from: Strong Proceed, Proceed with Conditions, Pilot Only, High Risk, Do Not Proceed. "
        "Use risk severity values exactly from: informational, minor, moderate, major, critical. "
        "Scoring rubric: 5 means exceptional and almost rollout-ready; 4 means strong but conditional; "
        "3 means pilot-feasible with material gaps; 2 means weak or heavily constrained; 1 means not credible. "
        "Do not use score 5 unless the evidence is unusually complete and there is no major governance blocker on that dimension. "
        "Use evidence references only from the allowed portfolio.<section_key> values provided in the context. "
        "Keep reasoning concise, keep risks to 1-3 items, and keep disagreement flags short."
    )


def _user_prompt(spec: LLMCommitteeAgentSpec, portfolio: CanonicalPortfolio, shared_context: str) -> str:
    focus_sections = ", ".join(spec.focus_sections)
    return (
        f"Portfolio under review: {portfolio.portfolio_name} ({portfolio.portfolio_id}).\n"
        f"Agent role: {spec.name}\n"
        f"Agent domain: {spec.domain}\n"
        f"Owned dimensions: {', '.join(spec.owned_dimensions)}\n"
        f"Primary focus instruction: {spec.focus_prompt}\n"
        f"Prioritize evidence from sections: {focus_sections}\n"
        f"Default open question if evidence is weak: {spec.default_open_question}\n\n"
        "Shared portfolio context:\n"
        f"{shared_context}\n\n"
        "Required response contract:\n"
        "- stance: one allowed recommendation string.\n"
        "- reasoning_summary: 1 short paragraph.\n"
        "- score_contributions: one object per owned dimension.\n"
        "- identified_risks: 1-3 concise risks.\n"
        "- disagreement_flags: 0-3 short items if another committee member is likely to disagree.\n"
        "- open_questions: 1-3 items.\n"
        "- evidence_gaps: 0-3 items.\n"
        "- assumption_register: 1-3 topic=value items.\n"
    )


def build_adaptive_routing_decision(
    portfolio: CanonicalPortfolio,
    core_reviews: list[AgentReview],
) -> AdaptiveRoutingDecision:
    all_text = _portfolio_text(portfolio)
    architecture_text = _portfolio_text(portfolio, ["architecture_system_design", "operational_resilience", "mvp_roadmap"])
    go_to_market_text = _portfolio_text(portfolio, ["competitive_landscape", "business_requirements", "post_launch_strategy"])
    ai_text = _portfolio_text(portfolio, ["ai_agents_ethical_framework", "architecture_system_design", "success_metrics"])

    ai_heavy = _contains_any(ai_text, [" ai ", "llm", "model", "machine learning", "assistant", "copilot", "prompt", "inference"])
    data_heavy = ai_heavy or _contains_any(all_text, ["dataset", "warehouse", "etl", "knowledge base", "data quality", "training data"])
    regulated = _contains_any(
        all_text,
        ["privacy", "security", "compliance", "regulat", "retention", "jurisdiction", "identity", "audit", "incident response"],
    )
    go_to_market_complex = _contains_any(
        go_to_market_text,
        ["go-to-market", "gtm", "channel", "segment", "enterprise", "partner", "marketplace", "sales cycle", "procurement"],
    )
    implementation_complex = _contains_any(
        architecture_text,
        ["integration", "connector", "erp", "migration", "orchestration", "event", "workflow", "multi-tenant", "service"],
    )
    competitive_pressure = _contains_any(go_to_market_text, ["competitive", "incumbent", "alternative", "differentiated", "positioning"])

    product_weak = _dimension_average(core_reviews, "Problem Validity") < 3.5 or _dimension_average(core_reviews, "Product Quality") < 3.5
    market_weak = _dimension_average(core_reviews, "Market Fit") < 3.5
    finance_weak = _dimension_average(core_reviews, "Economic Viability") < 3.4
    architecture_weak = (
        _dimension_average(core_reviews, "Technical Feasibility") < 3.5
        or _dimension_average(core_reviews, "Operational Resilience") < 3.4
    )
    governance_weak = (
        _dimension_average(core_reviews, "Security & Compliance") < 3.5
        or _dimension_average(core_reviews, "AI Reliability") < 3.4
        or _has_high_severity_findings(core_reviews, {"security_and_compliance", "governance", "ai_reliability"})
    )
    committee_uncertain = sum(
        1 for review in core_reviews if RECOMMENDATION_RANK[review.recommendation] <= RECOMMENDATION_RANK["Pilot Only"]
    ) >= 2

    activated_specialists: list[str] = []
    activation_reasons: dict[str, str] = {}
    routing_signals: list[str] = []

    def activate(agent_id: str, reason: str, signal_label: str) -> None:
        if agent_id not in activated_specialists:
            activated_specialists.append(agent_id)
        activation_reasons[agent_id] = reason
        if signal_label not in routing_signals:
            routing_signals.append(signal_label)

    if product_weak or market_weak:
        activate(
            "customer_value_agent",
            "core screening flagged customer-value ambiguity in problem framing or product quality.",
            "customer_value_uncertainty",
        )
    if finance_weak or market_weak:
        activate(
            "business_model_agent",
            "core screening flagged business-model or monetization uncertainty.",
            "business_model_uncertainty",
        )
    if competitive_pressure or market_weak:
        activate(
            "competitive_landscape_agent",
            "core screening needs a deeper differentiation and alternative analysis.",
            "competitive_pressure",
        )
    if go_to_market_complex or market_weak:
        activate(
            "growth_gtm_agent",
            "core screening identified go-to-market complexity or segment uncertainty.",
            "gtm_complexity",
        )
    if ai_heavy or governance_weak:
        activate(
            "ai_systems_agent",
            "portfolio content and core governance signals indicate deeper AI-system review is required.",
            "ai_system_risk",
        )
    if regulated or governance_weak:
        activate(
            "security_compliance_agent",
            "core governance screening surfaced security, privacy, or compliance escalation.",
            "security_compliance_risk",
        )
    if implementation_complex or architecture_weak:
        activate(
            "operations_reliability_agent",
            "architecture screening surfaced operational or resilience complexity.",
            "operations_complexity",
        )
    if data_heavy:
        activate(
            "data_strategy_agent",
            "portfolio data dependencies indicate deeper data-strategy review is required.",
            "data_dependency_complexity",
        )
    if implementation_complex or architecture_weak or product_weak:
        activate(
            "implementation_feasibility_agent",
            "core screening identified roadmap or implementation feasibility risk.",
            "implementation_feasibility_risk",
        )
    if finance_weak or governance_weak or committee_uncertain:
        activate(
            "investment_committee_agent",
            "core screening indicates the investment case needs explicit committee escalation.",
            "investment_case_uncertainty",
        )

    activation_reasons.update(
        {
            spec.id: "Tier-1 core screening agent executes on every review."
            for spec in LLM_AGENT_REGISTRY
            if spec.activation_tier == "core"
        }
    )

    passive_specialists = [
        spec.id
        for spec in LLM_AGENT_REGISTRY
        if spec.activation_tier == "specialist" and spec.id not in activated_specialists
    ]
    for spec in LLM_AGENT_REGISTRY:
        if spec.id in passive_specialists:
            activation_reasons[spec.id] = (
                "core screening did not surface enough domain-specific ambiguity to require deep specialist execution."
            )

    return AdaptiveRoutingDecision(
        core_agent_ids=list(CORE_AGENT_IDS),
        activated_specialist_ids=activated_specialists,
        passive_specialist_ids=passive_specialists,
        activation_reasons=activation_reasons,
        routing_signals=routing_signals,
    )


class AgentInferenceService:
    def __init__(self, *, provider: StructuredLLMProvider, runtime_options: CommitteeRuntimeOptions) -> None:
        self._provider = provider
        self._runtime_options = runtime_options

    async def _run_agent(
        self,
        spec: LLMCommitteeAgentSpec,
        portfolio: CanonicalPortfolio,
        shared_context: str,
        allowed_refs: set[str],
        semaphore: asyncio.Semaphore,
        activation_reason: str,
    ) -> AgentReview:
        fallback_refs = [f"portfolio.{section}" for section in spec.focus_sections]
        async with semaphore:
            response, telemetry = await self._provider.infer_structured(
                system_prompt=_system_prompt(spec),
                user_prompt=_user_prompt(spec, portfolio, shared_context),
                response_model=LLMCommitteeResponse,
                timeout_seconds=self._runtime_options.llm_request_timeout_seconds,
                max_output_tokens=self._runtime_options.llm_max_output_tokens,
            )

        dimension_scores = _normalize_dimension_scores(
            spec,
            response,
            fallback_refs=fallback_refs,
            allowed_refs=allowed_refs,
        )
        findings = [
            _build_finding(
                spec,
                index,
                risk,
                fallback_refs=fallback_refs,
                allowed_refs=allowed_refs,
            )
            for index, risk in enumerate(response.identified_risks[:3], start=1)
        ]
        recommendation = _normalize_recommendation(response.stance)
        dimension_scores = _calibrate_dimension_scores(recommendation, dimension_scores, findings)

        disagreement_notes = [
            f"Disagreement flag: {item}"
            for item in _sanitize_text_list(response.disagreement_flags, limit=3)
        ]
        open_questions = _sanitize_text_list(
            response.open_questions,
            limit=3,
            fallback=[spec.default_open_question],
        )
        evidence_gaps = _sanitize_text_list(response.evidence_gaps, limit=3)

        review = validate_agent_review(
            {
                "agent_id": spec.id,
                "agent_name": spec.name,
                "portfolio_id": portfolio.portfolio_id,
                "review_summary": _sanitize_text(
                    response.reasoning_summary,
                    f"{spec.name} recommends {recommendation} based on the available portfolio evidence.",
                ),
                "findings": [finding.model_dump(mode="json") for finding in findings],
                "dimension_scores": [score.model_dump(mode="json") for score in dimension_scores],
                "recommendation": recommendation,
                "open_questions": dedupe_preserve_order([*open_questions, *disagreement_notes])[:6],
                "evidence_gaps": evidence_gaps,
                "assumption_register": _normalize_assumptions(response.assumption_register, spec),
                "review_metadata": {
                    "prompt_contract_version": "m13-llm-adaptive-v1",
                    "model_provider": self._provider.provider_name,
                    "model_name": self._provider.model_name,
                    "duration_ms": telemetry.duration_ms,
                    "input_tokens": telemetry.input_tokens,
                    "output_tokens": telemetry.output_tokens,
                    "total_tokens": telemetry.total_tokens,
                    "estimated_cost_usd": telemetry.estimated_cost_usd,
                },
            }
        )
        return _review_with_activation_metadata(
            review,
            spec,
            activation_status="executed",
            activation_reason=activation_reason,
        )

    async def _run_specs(
        self,
        specs: list[LLMCommitteeAgentSpec],
        portfolio: CanonicalPortfolio,
        shared_context: str,
        allowed_refs: set[str],
        semaphore: asyncio.Semaphore,
        activation_reasons: dict[str, str],
    ) -> list[AgentReview]:
        tasks = [
            self._run_agent(
                spec,
                portfolio,
                shared_context,
                allowed_refs,
                semaphore,
                activation_reasons.get(spec.id, "Adaptive router selected this specialist for execution."),
            )
            for spec in specs
        ]
        if not tasks:
            return []
        return await asyncio.gather(*tasks)

    async def run_committee(self, portfolio: CanonicalPortfolio) -> RoutedCommitteeReviews:
        shared_context = build_shared_portfolio_context(portfolio)
        allowed_refs = set(allowed_evidence_refs())
        semaphore = asyncio.Semaphore(self._runtime_options.llm_max_concurrency)
        core_specs = [spec for spec in LLM_AGENT_REGISTRY if spec.activation_tier == "core"]
        core_reviews = await self._run_specs(
            core_specs,
            portfolio,
            shared_context,
            allowed_refs,
            semaphore,
            {
                spec.id: "Tier-1 core screening agent executes on every review."
                for spec in core_specs
            },
        )
        routing_decision = build_adaptive_routing_decision(portfolio, core_reviews)
        specialist_specs = [spec for spec in LLM_AGENT_REGISTRY if spec.id in routing_decision.activated_specialist_ids]
        specialist_reviews = await self._run_specs(
            specialist_specs,
            portfolio,
            shared_context,
            allowed_refs,
            semaphore,
            routing_decision.activation_reasons,
        )
        consensus_recommendation = _consensus_recommendation(core_reviews)
        passive_reviews = [
            _passive_observer_review(
                spec,
                portfolio,
                consensus_recommendation=consensus_recommendation,
                provider_name=self._provider.provider_name,
                model_name=self._provider.model_name,
                activation_reason=routing_decision.activation_reasons[spec.id],
            )
            for spec in LLM_AGENT_REGISTRY
            if spec.id in routing_decision.passive_specialist_ids
        ]

        review_map = {
            review.agent_id: review
            for review in [*core_reviews, *specialist_reviews, *passive_reviews]
        }
        ordered_reviews = [review_map[spec.id] for spec in LLM_AGENT_REGISTRY if spec.id in review_map]
        return RoutedCommitteeReviews(
            agent_reviews=ordered_reviews,
            routing_decision=routing_decision,
        )


def build_llm_provider(runtime_options: CommitteeRuntimeOptions) -> StructuredLLMProvider:
    provider_name = runtime_options.llm_provider.strip().lower()
    if provider_name == "openai":
        return OpenAIResponsesProvider(
            api_key=resolve_api_key(runtime_options.openai_api_key, runtime_options.openai_api_key_file),
            model_name=runtime_options.openai_model,
        )
    if provider_name == "anthropic":
        return AnthropicPlaceholderProvider(model_name=runtime_options.anthropic_model or "anthropic-placeholder")
    if provider_name == "local":
        return LocalPlaceholderProvider(model_name=runtime_options.local_llm_model or "local-placeholder")
    raise LLMProviderError(f"Unsupported LLM_PROVIDER '{runtime_options.llm_provider}'.")


async def run_llm_specialist_reviews_async(
    portfolio: CanonicalPortfolio,
    *,
    runtime_options: CommitteeRuntimeOptions,
    llm_provider: StructuredLLMProvider | None = None,
) -> RoutedCommitteeReviews:
    provider = llm_provider or build_llm_provider(runtime_options)
    service = AgentInferenceService(provider=provider, runtime_options=runtime_options)
    return await service.run_committee(portfolio)


def _deterministic_execution_result(
    portfolio: CanonicalPortfolio,
    *,
    requested_runtime_mode: RuntimeMode,
    requested_provider: str,
    requested_model_name: str,
    fallback_applied: bool = False,
    fallback_reason: str | None = None,
    failure_category: str | None = None,
) -> CommitteeExecutionResult:
    return CommitteeExecutionResult(
        agent_reviews=run_specialist_reviews(portfolio),
        requested_runtime_mode=requested_runtime_mode,
        effective_runtime_mode="deterministic",
        requested_provider=requested_provider,
        requested_model_name=requested_model_name,
        effective_provider="deterministic-thin-slice",
        effective_model_name="deterministic-thin-slice-v1",
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason,
        failure_category=failure_category,
        routing_strategy_version=None,
        core_agent_ids=[],
        activated_specialist_ids=[],
        passive_specialist_ids=[],
        routing_signals=[],
    )


def _failure_category(exc: Exception) -> str:
    if isinstance(exc, asyncio.TimeoutError):
        return "timeout"
    if isinstance(exc, ValidationError):
        return "invalid_response"
    message = str(exc).lower()
    if "token" in message and ("limit" in message or "exhaust" in message):
        return "token_exhaustion"
    if isinstance(exc, LLMProviderError):
        return "provider_error"
    return "unknown"


def _effective_llm_execution_result(
    review_set: RoutedCommitteeReviews,
    *,
    runtime_options: CommitteeRuntimeOptions,
    provider: StructuredLLMProvider,
) -> CommitteeExecutionResult:
    return CommitteeExecutionResult(
        agent_reviews=review_set.agent_reviews,
        requested_runtime_mode="llm",
        effective_runtime_mode="llm",
        requested_provider=runtime_options.llm_provider,
        requested_model_name=provider.model_name,
        effective_provider=provider.provider_name,
        effective_model_name=provider.model_name,
        fallback_applied=False,
        fallback_reason=None,
        failure_category=None,
        routing_strategy_version=review_set.routing_decision.routing_strategy_version,
        core_agent_ids=review_set.routing_decision.core_agent_ids,
        activated_specialist_ids=review_set.routing_decision.activated_specialist_ids,
        passive_specialist_ids=review_set.routing_decision.passive_specialist_ids,
        routing_signals=review_set.routing_decision.routing_signals,
    )


def _requested_model_name(runtime_options: CommitteeRuntimeOptions) -> str:
    provider = runtime_options.llm_provider.strip().lower()
    if provider == "anthropic":
        return runtime_options.anthropic_model or "anthropic-placeholder"
    if provider == "local":
        return runtime_options.local_llm_model or "local-placeholder"
    return runtime_options.openai_model


def run_committee_reviews(
    portfolio: CanonicalPortfolio,
    *,
    runtime_options: CommitteeRuntimeOptions | None = None,
    llm_provider: StructuredLLMProvider | None = None,
) -> CommitteeExecutionResult:
    resolved_runtime_options = runtime_options or CommitteeRuntimeOptions()
    if resolved_runtime_options.runtime_mode == "deterministic":
        return _deterministic_execution_result(
            portfolio,
            requested_runtime_mode="deterministic",
            requested_provider="deterministic-thin-slice",
            requested_model_name="deterministic-thin-slice-v1",
        )
    if resolved_runtime_options.runtime_mode == "llm":
        provider = llm_provider
        try:
            provider = provider or build_llm_provider(resolved_runtime_options)
            review_set = asyncio.run(
                run_llm_specialist_reviews_async(
                    portfolio,
                    runtime_options=resolved_runtime_options,
                    llm_provider=provider,
                )
            )
            return _effective_llm_execution_result(
                review_set,
                runtime_options=resolved_runtime_options,
                provider=provider,
            )
        except Exception as exc:
            failure_category = _failure_category(exc)
            fallback_reason = str(exc).strip() or "Unknown llm runtime failure."
            logger.warning(
                "LLM committee execution failed for portfolio %s and fell back to deterministic mode: %s",
                portfolio.portfolio_id,
                fallback_reason,
            )
            return _deterministic_execution_result(
                portfolio,
                requested_runtime_mode="llm",
                requested_provider=resolved_runtime_options.llm_provider,
                requested_model_name=_requested_model_name(resolved_runtime_options),
                fallback_applied=True,
                fallback_reason=fallback_reason[:320],
                failure_category=failure_category,
            )
    raise LLMProviderError(f"Unsupported runtime mode '{resolved_runtime_options.runtime_mode}'.")
