from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.debates import DebateService  # noqa: E402
from orbit_api.deliberations import DeliberationService  # noqa: E402
from orbit_api.review_runs import ReviewRunService  # noqa: E402
from orbit_api.review_workflow import ReviewWorkflowService  # noqa: E402
from orbit_api.resyntheses import ResynthesisService  # noqa: E402
from orbit_worker.committee_engine import CORE_AGENT_IDS, CommitteeRuntimeOptions  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.llm_specs import LLMCommitteeResponse, LLM_AGENT_REGISTRY  # noqa: E402
from orbit_worker.llm_provider import InferenceTelemetry  # noqa: E402
from orbit_worker.persistence import InMemoryPersistenceRepository, build_portfolio_ingestion_bundle  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"


class MockParallelLLMProvider:
    provider_name = "mock-openai"
    model_name = "gpt-4o-mini-mock"

    def __init__(self) -> None:
        self.active_requests = 0
        self.max_active_requests = 0
        self.started_agent_ids: list[str] = []

    async def infer_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model,
        timeout_seconds: int,
        max_output_tokens: int,
    ):
        del system_prompt, timeout_seconds, max_output_tokens
        marker = "Agent role: "
        start = user_prompt.index(marker) + len(marker)
        end = user_prompt.index("\n", start)
        agent_name = user_prompt[start:end].strip()
        spec = next(item for item in LLM_AGENT_REGISTRY if item.name == agent_name)
        self.started_agent_ids.append(spec.id)

        self.active_requests += 1
        self.max_active_requests = max(self.max_active_requests, self.active_requests)
        try:
            await asyncio.sleep(0.05)
            payload = self._payload_for_spec(spec.id, spec.owned_dimensions)
            return response_model.model_validate(payload), InferenceTelemetry(
                duration_ms=50,
                input_tokens=220,
                output_tokens=80,
                total_tokens=300,
                estimated_cost_usd=0.000081,
            )
        finally:
            self.active_requests -= 1

    def _payload_for_spec(self, agent_id: str, owned_dimensions: list[str]) -> dict[str, object]:
        default_score = {
            "stance": "Proceed with Conditions",
            "claim": f"{agent_id} sees a credible portfolio claim with bounded upside.",
            "evidence": [
                "Portfolio emphasizes a clear workflow narrative.",
                "Evidence points to measurable operational impact.",
            ],
            "risk": ["Execution sequencing still needs tighter controls."],
            "implication": "The evidence supports conditional progress with tightened execution gates.",
            "score": 3.6,
            "confidence": "Medium",
            "score_contributions": [
                {
                    "dimension": dimension,
                    "score": 3.7,
                    "confidence": 0.68,
                    "evidence_completeness": 0.72,
                    "rationale": f"{agent_id} sees credible evidence for {dimension} with manageable gaps.",
                    "evidence_refs": ["portfolio.product_vision", "portfolio.architecture_system_design"],
                    "severity_flags": [],
                }
                for dimension in owned_dimensions
            ],
            "identified_risks": [
                {
                    "title": f"{agent_id} sees an execution gap that still needs closure",
                    "category": "technical_feasibility",
                    "severity": "moderate",
                    "claim": f"{agent_id} believes the portfolio still needs bounded delivery controls before broader rollout.",
                    "evidence_refs": ["portfolio.architecture_system_design", "portfolio.mvp_roadmap"],
                    "assumptions": [],
                    "recommended_action": "Close the delivery sequencing gap before broader rollout.",
                }
            ],
            "disagreement_flags": [],
            "open_questions": [f"What missing evidence would make {agent_id} more confident?"],
            "evidence_gaps": ["Delivery sequencing evidence is still incomplete."],
            "assumption_register": [f"{agent_id}=bounded_pilot_scope_is_feasible"],
        }

        if agent_id == "security_compliance_agent":
            default_score["stance"] = "High Risk"
            default_score["claim"] = "Security and compliance controls are materially incomplete for broader rollout."
            default_score["evidence"] = [
                "Portfolio references limited retention and incident response detail.",
                "Compliance scope is acknowledged but not fully specified.",
            ]
            default_score["risk"] = ["Governance gaps could block regulated deployment."]
            default_score["implication"] = "The committee should constrain rollout to a tightly bounded pilot."
            default_score["score"] = 2.2
            default_score["confidence"] = "High"
            default_score["score_contributions"] = [
                {
                    "dimension": "Security & Compliance",
                    "score": 1.6,
                    "confidence": 0.86,
                    "evidence_completeness": 0.79,
                    "rationale": "Control posture is materially below the bar for broader rollout.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.operational_resilience"],
                    "severity_flags": ["compliance_gap"],
                },
                {
                    "dimension": "Operational Resilience",
                    "score": 2.2,
                    "confidence": 0.74,
                    "evidence_completeness": 0.66,
                    "rationale": "Operational controls are still too weak for regulated rollout.",
                    "evidence_refs": ["portfolio.operational_resilience", "portfolio.post_launch_strategy"],
                    "severity_flags": ["control_gap"],
                },
            ]
            default_score["identified_risks"] = [
                {
                    "title": "Compliance control posture is incomplete",
                    "category": "security_and_compliance",
                    "severity": "critical",
                    "claim": "Identity, retention, and incident response controls are not yet mature enough for broader rollout.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.operational_resilience"],
                    "assumptions": ["control_posture=insufficient_for_regulated_pilot"],
                    "recommended_action": "Close the compliance control gaps before expanding beyond pilot.",
                }
            ]
            default_score["assumption_register"] = ["control_posture=insufficient_for_regulated_pilot"]
        elif agent_id == "risk_governance_agent":
            default_score["stance"] = "Proceed with Conditions"
            default_score["confidence"] = "Medium"
            default_score["score_contributions"] = [
                {
                    "dimension": "Security & Compliance",
                    "score": 4.2,
                    "confidence": 0.62,
                    "evidence_completeness": 0.74,
                    "rationale": "Governance framing is directionally strong if explicit launch conditions are enforced.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.post_launch_strategy"],
                    "severity_flags": [],
                },
                {
                    "dimension": "AI Reliability",
                    "score": 4.0,
                    "confidence": 0.6,
                    "evidence_completeness": 0.7,
                    "rationale": "Human review steps improve governance resilience.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.product_requirements"],
                    "severity_flags": [],
                },
            ]
            default_score["identified_risks"] = [
                {
                    "title": "Governance structure is promising but incomplete",
                    "category": "security_and_compliance",
                    "severity": "minor",
                    "claim": "Governance structure is usable for a pilot but still lacks explicit approval boundaries.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.post_launch_strategy"],
                    "assumptions": ["control_posture=conditional_launch_gate_is_sufficient"],
                    "recommended_action": "Document explicit approval boundaries for the first pilot.",
                }
            ]
            default_score["assumption_register"] = ["control_posture=conditional_launch_gate_is_sufficient"]
        elif agent_id == "architecture_agent":
            default_score["confidence"] = "High"
            default_score["score_contributions"] = [
                {
                    "dimension": "Technical Feasibility",
                    "score": 4.4,
                    "confidence": 0.77,
                    "evidence_completeness": 0.86,
                    "rationale": "The service boundaries are coherent for an early production slice.",
                    "evidence_refs": ["portfolio.architecture_system_design", "portfolio.mvp_roadmap"],
                    "severity_flags": [],
                },
                {
                    "dimension": "Operational Resilience",
                    "score": 3.6,
                    "confidence": 0.69,
                    "evidence_completeness": 0.71,
                    "rationale": "Reliability posture is credible if rollout remains tightly bounded.",
                    "evidence_refs": ["portfolio.operational_resilience", "portfolio.architecture_system_design"],
                    "severity_flags": [],
                },
            ]
            default_score["assumption_register"] = ["integration_scope=single_connector_first"]
        elif agent_id == "implementation_feasibility_agent":
            default_score["stance"] = "Pilot Only"
            default_score["confidence"] = "Medium"
            default_score["score_contributions"] = [
                {
                    "dimension": "Technical Feasibility",
                    "score": 2.6,
                    "confidence": 0.73,
                    "evidence_completeness": 0.44,
                    "rationale": "The delivery plan is riskier than the architecture story suggests.",
                    "evidence_refs": ["portfolio.mvp_roadmap", "portfolio.product_requirements"],
                    "severity_flags": ["delivery_gap"],
                },
                {
                    "dimension": "Operational Resilience",
                    "score": 3.1,
                    "confidence": 0.58,
                    "evidence_completeness": 0.52,
                    "rationale": "Operational readiness depends on unresolved delivery sequencing.",
                    "evidence_refs": ["portfolio.mvp_roadmap", "portfolio.operational_resilience"],
                    "severity_flags": ["delivery_gap"],
                },
            ]
            default_score["identified_risks"] = [
                {
                    "title": "Delivery dependency risk is material",
                    "category": "technical_feasibility",
                    "severity": "major",
                    "claim": "The roadmap compresses multiple delivery dependencies into a single pilot window.",
                    "evidence_refs": ["portfolio.mvp_roadmap", "portfolio.product_requirements"],
                    "assumptions": ["integration_scope=dual_connector_first"],
                    "recommended_action": "Reduce delivery concurrency before broader rollout.",
                }
            ]
            default_score["assumption_register"] = ["integration_scope=dual_connector_first"]
        elif agent_id == "ai_systems_agent":
            default_score["stance"] = "Pilot Only"
            default_score["confidence"] = "Medium"
            default_score["score_contributions"] = [
                {
                    "dimension": "AI Reliability",
                    "score": 2.5,
                    "confidence": 0.67,
                    "evidence_completeness": 0.58,
                    "rationale": "The AI evaluation story is not yet strong enough for scaled deployment.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.success_metrics"],
                    "severity_flags": ["evaluation_gap"],
                },
                {
                    "dimension": "Technical Feasibility",
                    "score": 3.2,
                    "confidence": 0.6,
                    "evidence_completeness": 0.63,
                    "rationale": "System design is workable but still needs stronger evaluation instrumentation.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.architecture_system_design"],
                    "severity_flags": ["evaluation_gap"],
                },
            ]
            default_score["identified_risks"] = [
                {
                    "title": "AI evaluation evidence is incomplete",
                    "category": "ai_reliability",
                    "severity": "major",
                    "claim": "Offline evaluation thresholds are not yet explicit enough for broader rollout.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.success_metrics"],
                    "assumptions": ["model_quality=human_review_offsets_missing_benchmarks"],
                    "recommended_action": "Define explicit offline evaluation thresholds before scale.",
                }
            ]
        elif agent_id == "data_strategy_agent":
            default_score["confidence"] = "Medium"
            default_score["score_contributions"] = [
                {
                    "dimension": "AI Reliability",
                    "score": 4.1,
                    "confidence": 0.55,
                    "evidence_completeness": 0.83,
                    "rationale": "The data strategy is credible if measurement and governance stay tightly coupled.",
                    "evidence_refs": ["portfolio.ai_agents_ethical_framework", "portfolio.success_metrics"],
                    "severity_flags": [],
                },
                {
                    "dimension": "Economic Viability",
                    "score": 3.8,
                    "confidence": 0.58,
                    "evidence_completeness": 0.72,
                    "rationale": "Data reuse could create good operating leverage if the initial pilot is disciplined.",
                    "evidence_refs": ["portfolio.business_requirements", "portfolio.success_metrics"],
                    "severity_flags": [],
                },
            ]
        return default_score


class FailingLLMProvider:
    provider_name = "mock-openai"
    model_name = "gpt-4o-mini-mock"

    async def infer_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model,
        timeout_seconds: int,
        max_output_tokens: int,
    ):
        del system_prompt, user_prompt, response_model, timeout_seconds, max_output_tokens
        raise RuntimeError("provider timeout while requesting tokens")


def test_llm_review_workflow_runs_parallel_agents_and_triggers_resynthesis() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    provider = MockParallelLLMProvider()
    runtime_options = CommitteeRuntimeOptions(
        runtime_mode="llm",
        llm_provider="openai",
        openai_model=provider.model_name,
        llm_max_concurrency=8,
        llm_request_timeout_seconds=10,
        llm_max_output_tokens=600,
    )

    service = ReviewWorkflowService(
        review_runs=ReviewRunService(
            repository=repository,
            runtime_options=runtime_options,
            llm_provider=provider,
        ),
        debates=DebateService(repository=repository),
        resyntheses=ResynthesisService(repository=repository),
    )
    summary = service.start_review(canonical_portfolio.portfolio_id)

    assert summary.review_run.agent_review_count == 15
    assert summary.review_run.conflict_count >= 1
    assert summary.debate is not None
    assert summary.debate.conflicts_considered >= 1
    assert summary.resynthesis is not None
    assert summary.resynthesis.active_artifact_source == "resynthesized"
    assert provider.max_active_requests > 1

    review_bundle = repository.get_review_run_bundle(summary.review_run.run_id)
    assert review_bundle is not None
    assert len(review_bundle.agent_reviews) == 15
    assert review_bundle.review_run.prompt_contract_version == "m13-llm-adaptive-v1"
    active_reviews = [
        record for record in review_bundle.agent_reviews if record.review_payload.review_metadata.activation_status == "executed"
    ]
    passive_reviews = [
        record for record in review_bundle.agent_reviews if record.review_payload.review_metadata.activation_status == "passive_observer"
    ]
    assert len(active_reviews) < 15
    assert len(passive_reviews) > 0
    assert set(provider.started_agent_ids[: len(CORE_AGENT_IDS)]) == set(CORE_AGENT_IDS)
    assert set(provider.started_agent_ids) == {record.agent_id for record in active_reviews}
    assert all(record.review_payload.review_metadata.model_provider == provider.provider_name for record in review_bundle.agent_reviews)
    assert all(record.review_payload.review_metadata.total_tokens == 300 for record in active_reviews)
    assert all(record.review_payload.review_metadata.estimated_cost_usd > 0 for record in active_reviews)
    assert all(record.review_payload.review_metadata.total_tokens == 0 for record in passive_reviews)
    assert all(record.review_payload.review_metadata.estimated_cost_usd == 0 for record in passive_reviews)
    assert all(record.review_payload.reasoning is not None for record in review_bundle.agent_reviews)
    assert all(record.review_payload.reasoning.claim for record in review_bundle.agent_reviews)
    assert all(
        record.review_payload.reasoning.confidence in {"Low", "Medium", "High"}
        for record in review_bundle.agent_reviews
    )


def test_llm_deliberation_runtime_metadata_exposes_agent_token_telemetry() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    provider = MockParallelLLMProvider()
    runtime_options = CommitteeRuntimeOptions(
        runtime_mode="llm",
        llm_provider="openai",
        openai_model=provider.model_name,
        llm_max_concurrency=8,
        llm_request_timeout_seconds=10,
        llm_max_output_tokens=600,
    )

    deliberation_service = DeliberationService(repository=repository)
    workflow_service = ReviewWorkflowService(
        review_runs=ReviewRunService(
            repository=repository,
            runtime_options=runtime_options,
            llm_provider=provider,
            deliberation_refresher=deliberation_service.refresh_review_run,
        ),
        debates=DebateService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run),
        resyntheses=ResynthesisService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run),
    )

    summary = workflow_service.start_review(canonical_portfolio.portfolio_id)
    detail = deliberation_service.get_review_run_deliberation(summary.review_run.run_id)

    assert detail is not None
    assert detail.runtime_metadata.runtime_mode == "llm"
    assert detail.runtime_metadata.model_provider == provider.provider_name
    assert detail.runtime_metadata.model_name == provider.model_name
    assert detail.runtime_metadata.agent_count == 15
    assert detail.runtime_metadata.core_executed_count == len(CORE_AGENT_IDS)
    assert detail.runtime_metadata.activated_specialist_count > 0
    assert detail.runtime_metadata.passive_observer_count > 0
    assert detail.runtime_metadata.total_tokens == 300 * (
        detail.runtime_metadata.core_executed_count + detail.runtime_metadata.activated_specialist_count
    )
    assert detail.runtime_metadata.total_input_tokens == 220 * (
        detail.runtime_metadata.core_executed_count + detail.runtime_metadata.activated_specialist_count
    )
    assert detail.runtime_metadata.total_output_tokens == 80 * (
        detail.runtime_metadata.core_executed_count + detail.runtime_metadata.activated_specialist_count
    )
    assert detail.runtime_metadata.estimated_cost_usd > 0
    assert len(detail.runtime_metadata.agents) == 15
    assert detail.runtime_metadata.routing_strategy_version == "m13-adaptive-v1"
    assert detail.runtime_metadata.routing_signals
    assert any(agent.activation_status == "passive_observer" for agent in detail.runtime_metadata.agents)
    assert any(agent.total_tokens == 0 for agent in detail.runtime_metadata.agents)
    assert any(agent.total_tokens == 300 for agent in detail.runtime_metadata.agents)
    assert detail.runtime_metadata.requested_runtime_mode == "llm"
    assert detail.runtime_metadata.effective_runtime_mode == "llm"
    assert detail.runtime_metadata.fallback_applied is False


def test_llm_review_workflow_falls_back_to_deterministic_runtime_when_provider_fails() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    runtime_options = CommitteeRuntimeOptions(
        runtime_mode="llm",
        llm_provider="openai",
        openai_model="gpt-4o-mini-mock",
        llm_max_concurrency=8,
        llm_request_timeout_seconds=1,
        llm_max_output_tokens=600,
    )

    deliberation_service = DeliberationService(repository=repository)
    workflow_service = ReviewWorkflowService(
        review_runs=ReviewRunService(
            repository=repository,
            runtime_options=runtime_options,
            llm_provider=FailingLLMProvider(),
            deliberation_refresher=deliberation_service.refresh_review_run,
        ),
        debates=DebateService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run),
        resyntheses=ResynthesisService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run),
    )

    summary = workflow_service.start_review(canonical_portfolio.portfolio_id)
    detail = deliberation_service.get_review_run_deliberation(summary.review_run.run_id)
    review_bundle = repository.get_review_run_bundle(summary.review_run.run_id)

    assert detail is not None
    assert review_bundle is not None
    assert detail.runtime_metadata.requested_runtime_mode == "llm"
    assert detail.runtime_metadata.effective_runtime_mode == "deterministic"
    assert detail.runtime_metadata.runtime_mode == "deterministic"
    assert detail.runtime_metadata.fallback_applied is True
    assert detail.runtime_metadata.fallback_category == "unknown"
    assert detail.runtime_metadata.total_tokens == 0
    assert detail.runtime_metadata.estimated_cost_usd == 0.0
    assert all(record.review_payload.review_metadata.model_provider == "deterministic-thin-slice" for record in review_bundle.agent_reviews)
    assert all(record.review_payload.reasoning is not None for record in review_bundle.agent_reviews)
    assert all(record.review_payload.reasoning.claim for record in review_bundle.agent_reviews)
    assert all(
        record.review_payload.reasoning.confidence in {"Low", "Medium", "High"}
        for record in review_bundle.agent_reviews
    )
    assert {event.action for event in review_bundle.audit_events} >= {
        "review_run.created",
        "review_run.runtime_fallback",
        "review_run.completed",
    }
