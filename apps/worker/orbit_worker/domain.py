from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, TypeVar

PORTFOLIO_SECTIONS = [
    {"key": "problem_discovery", "title": "Problem Discovery"},
    {"key": "product_vision", "title": "Product Vision"},
    {"key": "competitive_landscape", "title": "Competitive Landscape"},
    {"key": "business_requirements", "title": "Business Requirements"},
    {"key": "product_requirements", "title": "Product Requirements"},
    {"key": "architecture_system_design", "title": "Architecture & System Design"},
    {"key": "ai_agents_ethical_framework", "title": "AI Agents & Ethical Framework"},
    {"key": "operational_resilience", "title": "Operational Resilience"},
    {"key": "mvp_roadmap", "title": "MVP Roadmap"},
    {"key": "success_metrics", "title": "Success Metrics"},
    {"key": "post_launch_strategy", "title": "Post Launch Strategy"},
]

SECTION_TITLE_TO_KEY: dict[str, str] = {}
for section in PORTFOLIO_SECTIONS:
    SECTION_TITLE_TO_KEY[section["title"].lower()] = section["key"]
    if section["title"] == "Architecture & System Design":
        SECTION_TITLE_TO_KEY["architecture and system design"] = section["key"]
    if section["title"] == "AI Agents & Ethical Framework":
        SECTION_TITLE_TO_KEY["ai agents and ethical framework"] = section["key"]

SCORE_DIMENSIONS = [
    "Problem Validity",
    "Market Fit",
    "Product Quality",
    "Technical Feasibility",
    "AI Reliability",
    "Economic Viability",
    "Operational Resilience",
    "Security & Compliance",
]

DIMENSION_WEIGHTS = {
    "Problem Validity": 10,
    "Market Fit": 15,
    "Product Quality": 10,
    "Technical Feasibility": 15,
    "AI Reliability": 15,
    "Economic Viability": 10,
    "Operational Resilience": 10,
    "Security & Compliance": 15,
}

RECOMMENDATION_ORDER = [
    "Do Not Proceed",
    "High Risk",
    "Pilot Only",
    "Proceed with Conditions",
    "Strong Proceed",
]
RECOMMENDATION_RANK = {value: index for index, value in enumerate(RECOMMENDATION_ORDER)}
SEVERITY_ORDER = ["informational", "minor", "moderate", "major", "critical"]
SEVERITY_RANK = {value: index for index, value in enumerate(SEVERITY_ORDER)}


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    domain: str
    dimensions: list[str]
    dimension_biases: dict[str, float]
    recommendation_bias: float
    strictness: float
    positive_signal: str
    risk_signal: str
    positive_refs: list[str]
    risk_refs: list[str]
    assumption: str
    open_question: str
    evidence_gap: str


AGENT_REGISTRY = [
    AgentSpec("business_owner", "Business Owner", "Strategy & Finance", ["Problem Validity", "Economic Viability"], {"Problem Validity": 0.25, "Economic Viability": 0.15}, 0.25, 0.1, "problem_strength", "integration_risk", ["portfolio.problem_discovery", "portfolio.business_requirements", "portfolio.success_metrics"], ["portfolio.architecture_system_design", "portfolio.post_launch_strategy"], "value_realization=integration_sequence_is_managed", "Which integration path is required for the first three pilots to realize measurable ROI?", "The first-wave implementation cost model is not yet explicit."),
    AgentSpec("finance_lead", "Finance Lead", "Strategy & Finance", ["Economic Viability"], {"Economic Viability": -0.05}, -0.1, 0.2, "monetization_clarity", "integration_risk", ["portfolio.business_requirements"], ["portfolio.business_requirements", "portfolio.operational_resilience", "portfolio.post_launch_strategy"], "unit_economics=services_load_stays_bounded", "What services burden is assumed for the initial ERP-connected customers?", "The fixture does not include a ramped cost model or payback profile."),
    AgentSpec("sales_strategist", "Sales Strategist", "Strategy & Finance", ["Market Fit", "Economic Viability"], {"Market Fit": 0.35, "Economic Viability": 0.1}, 0.3, 0.05, "buyer_clarity", "integration_risk", ["portfolio.product_vision", "portfolio.business_requirements", "portfolio.post_launch_strategy"], ["portfolio.architecture_system_design", "portfolio.mvp_roadmap"], "launch_scope=single_region_mvp_is_sales_acceptable", "Which buyer objections are expected if ERP integrations land after the core workflow pilots?", "The fixture does not map integration depth to segment-specific sales cycles."),
    AgentSpec("marketing_strategist", "Marketing Strategist", "Strategy & Finance", ["Market Fit", "Product Quality"], {"Market Fit": 0.25, "Product Quality": 0.15}, 0.2, 0.1, "market_story_strength", "compliance_gap", ["portfolio.competitive_landscape", "portfolio.product_vision"], ["portfolio.ai_agents_ethical_framework", "portfolio.operational_resilience"], "trust_positioning=controls_are_marketable", "What proof points will marketing use to address buyer trust questions in regulated accounts?", "The fixture does not define external trust messaging artifacts or validation evidence."),
    AgentSpec("product_manager", "Product Manager", "Product & Experience", ["Product Quality", "Problem Validity"], {"Product Quality": 0.2, "Problem Validity": 0.15}, 0.15, 0.1, "mvp_focus", "integration_risk", ["portfolio.product_requirements", "portfolio.mvp_roadmap"], ["portfolio.architecture_system_design", "portfolio.ai_agents_ethical_framework", "portfolio.operational_resilience"], "enterprise_readiness=conditions_can_close_gaps_quickly", "Which product release gates define enterprise-ready versus pilot-ready use?", "The fixture does not define formal release gates for broader enterprise rollout."),
    AgentSpec("ux_ui_reviewer", "UX/UI Reviewer", "Product & Experience", ["Product Quality"], {"Product Quality": 0.1}, 0.05, 0.15, "workflow_traceability", "ai_evaluation_gap", ["portfolio.product_requirements"], ["portfolio.ai_agents_ethical_framework", "portfolio.product_requirements"], "user_trust=human_review_steps_are_visible", "How will users inspect why a supplier delta or approval suggestion was generated?", "No detailed interaction model is provided for AI explanation and correction flows."),
    AgentSpec("customer_success_lead", "Customer Success Lead", "Product & Experience", ["Product Quality", "Operational Resilience"], {"Product Quality": 0.05, "Operational Resilience": -0.02}, 0.0, 0.2, "customer_value_clarity", "support_gap", ["portfolio.problem_discovery", "portfolio.success_metrics"], ["portfolio.operational_resilience", "portfolio.post_launch_strategy"], "post_sale_model=lean_team_can_support_initial_customers", "Who owns onboarding, escalation, and success reviews during the first pilot wave?", "The fixture does not describe a staffed customer success or support operating model."),
    AgentSpec("system_architect", "System Architect", "Engineering", ["Technical Feasibility", "Operational Resilience"], {"Technical Feasibility": 0.2, "Operational Resilience": -0.05}, 0.0, 0.2, "architecture_strength", "resilience_gap", ["portfolio.architecture_system_design"], ["portfolio.operational_resilience", "portfolio.architecture_system_design"], "launch_scope=single_region_mvp_is_operationally_acceptable", "What are the target recovery objectives and how are they validated before general availability?", "The fixture mentions future failover work but does not define tested recovery objectives."),
    AgentSpec("ai_data_scientist", "AI/Data Scientist", "Engineering", ["AI Reliability", "Technical Feasibility"], {"AI Reliability": -0.05, "Technical Feasibility": 0.05}, -0.1, 0.25, "ai_controls", "ai_evaluation_gap", ["portfolio.ai_agents_ethical_framework"], ["portfolio.ai_agents_ethical_framework", "portfolio.success_metrics"], "model_quality=human_review_offsets_missing_benchmarks", "What benchmark set and quality threshold must the AI assistance layer clear before wider rollout?", "The fixture does not include an offline evaluation plan or benchmark dataset."),
    AgentSpec("developer", "Developer", "Engineering", ["Technical Feasibility"], {"Technical Feasibility": 0.15}, 0.05, 0.15, "mvp_focus", "integration_risk", ["portfolio.product_requirements", "portfolio.architecture_system_design", "portfolio.mvp_roadmap"], ["portfolio.architecture_system_design", "portfolio.mvp_roadmap"], "delivery_scope=single_connector_is_enough_for_first_wave", "Which engineering tasks are out of scope for the first pilot so that the roadmap remains credible?", "No explicit task decomposition is included for connector versus core platform work."),
    AgentSpec("devops_architect", "DevOps Architect", "Operations", ["Operational Resilience", "Technical Feasibility"], {"Operational Resilience": -0.08, "Technical Feasibility": 0.0}, -0.05, 0.25, "architecture_strength", "resilience_gap", ["portfolio.architecture_system_design", "portfolio.operational_resilience"], ["portfolio.operational_resilience", "portfolio.mvp_roadmap"], "ops_readiness=lightweight_controls_are_sufficient_for_pilots", "What release and rollback controls will exist before the first pilot reaches production data?", "The fixture does not define release gates or tested rollback procedures."),
    AgentSpec("system_maintenance_lead", "System Maintenance Lead", "Operations", ["Operational Resilience"], {"Operational Resilience": -0.12}, -0.1, 0.2, "ops_controls", "support_gap", ["portfolio.operational_resilience"], ["portfolio.operational_resilience", "portfolio.post_launch_strategy"], "sustainment=platform_team_can_absorb_operational_load", "Who owns maintenance windows, upgrades, and post-pilot debt retirement?", "There is no explicit maintenance ownership model or long-term operating cadence."),
    AgentSpec("qa_sdet", "QA/SDET", "Operations", ["Product Quality", "Operational Resilience"], {"Product Quality": -0.05, "Operational Resilience": -0.08}, -0.1, 0.25, "workflow_traceability", "ai_evaluation_gap", ["portfolio.product_requirements"], ["portfolio.ai_agents_ethical_framework", "portfolio.operational_resilience", "portfolio.success_metrics"], "quality_bar=manual_review_covers_early_regression_risk", "What regression and acceptance tests must pass before the first live pilot release?", "The fixture does not define a formal workflow or AI-related test strategy."),
    AgentSpec("infosec_architect", "InfoSec Architect", "Risk & Compliance", ["Security & Compliance", "Operational Resilience"], {"Security & Compliance": -0.18, "Operational Resilience": -0.08}, -0.18, 0.28, "security_controls", "compliance_gap", ["portfolio.ai_agents_ethical_framework"], ["portfolio.ai_agents_ethical_framework", "portfolio.operational_resilience", "portfolio.architecture_system_design"], "security_bar=pilot_scope_allows_partial_controls", "What identity, secrets, and incident response controls will be in place before the first enterprise pilot?", "No detailed security control matrix is present in the portfolio."),
    AgentSpec("legal_compliance_reviewer", "Legal & Compliance Reviewer", "Risk & Compliance", ["Security & Compliance"], {"Security & Compliance": -0.22}, -0.22, 0.28, "ai_controls", "compliance_gap", ["portfolio.product_requirements", "portfolio.ai_agents_ethical_framework"], ["portfolio.ai_agents_ethical_framework", "portfolio.operational_resilience", "portfolio.post_launch_strategy"], "compliance_bar=pilot_customers_accept_partial_controls", "Which legal and compliance commitments are required for the first regulated pilot customers?", "The fixture does not contain a compliance matrix, retention policy, or jurisdiction-specific control mapping."),
]


def round_half_up(value: float, digits: int = 2) -> float:
    quantum = Decimal("1") if digits == 0 else Decimal("1").scaleb(-digits)
    # Match the frozen JS baseline by rounding from the IEEE-754 float value,
    # not from Python's decimal string rendering of that value.
    return float(Decimal.from_float(value).quantize(quantum, rounding=ROUND_HALF_UP))


def clamp_score(value: float) -> float:
    return max(0.0, min(5.0, round_half_up(value, 2)))


def clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, round_half_up(value, 2)))


def get_recommendation_distance(left: str, right: str) -> int:
    return abs(RECOMMENDATION_RANK[left] - RECOMMENDATION_RANK[right])


T = TypeVar("T")


def dedupe_preserve_order(items: Iterable[T]) -> list[T]:
    seen: set[T] = set()
    values: list[T] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        values.append(item)
    return values
