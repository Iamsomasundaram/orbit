from __future__ import annotations

import asyncio
from typing import Any, Literal

from pydantic import Field

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
            runtime_mode=getattr(settings, "llm_runtime_mode", "deterministic"),
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

        return validate_agent_review(
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
                    "prompt_contract_version": "m10-llm-v1",
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

    async def run_committee(self, portfolio: CanonicalPortfolio) -> list[AgentReview]:
        shared_context = build_shared_portfolio_context(portfolio)
        allowed_refs = set(allowed_evidence_refs())
        semaphore = asyncio.Semaphore(self._runtime_options.llm_max_concurrency)
        tasks = [
            self._run_agent(spec, portfolio, shared_context, allowed_refs, semaphore)
            for spec in LLM_AGENT_REGISTRY
        ]
        return await asyncio.gather(*tasks)


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
) -> list[AgentReview]:
    provider = llm_provider or build_llm_provider(runtime_options)
    service = AgentInferenceService(provider=provider, runtime_options=runtime_options)
    return await service.run_committee(portfolio)


def run_committee_reviews(
    portfolio: CanonicalPortfolio,
    *,
    runtime_options: CommitteeRuntimeOptions | None = None,
    llm_provider: StructuredLLMProvider | None = None,
) -> list[AgentReview]:
    resolved_runtime_options = runtime_options or CommitteeRuntimeOptions()
    if resolved_runtime_options.runtime_mode == "deterministic":
        return run_specialist_reviews(portfolio)
    if resolved_runtime_options.runtime_mode == "llm":
        return asyncio.run(
            run_llm_specialist_reviews_async(
                portfolio,
                runtime_options=resolved_runtime_options,
                llm_provider=llm_provider,
            )
        )
    raise LLMProviderError(f"Unsupported runtime mode '{resolved_runtime_options.runtime_mode}'.")
