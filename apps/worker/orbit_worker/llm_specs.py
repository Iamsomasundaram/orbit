from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from .domain import PORTFOLIO_SECTIONS, SCORE_DIMENSIONS

if TYPE_CHECKING:
    from .schemas import CanonicalPortfolio

RISK_CATEGORIES = [
    "problem_validity",
    "market_fit",
    "product_quality",
    "technical_feasibility",
    "ai_reliability",
    "economic_viability",
    "operational_resilience",
    "security_and_compliance",
    "governance",
]

DIMENSION_TO_CATEGORY = {
    "Problem Validity": "problem_validity",
    "Market Fit": "market_fit",
    "Product Quality": "product_quality",
    "Technical Feasibility": "technical_feasibility",
    "AI Reliability": "ai_reliability",
    "Economic Viability": "economic_viability",
    "Operational Resilience": "operational_resilience",
    "Security & Compliance": "security_and_compliance",
}


@dataclass(frozen=True)
class LLMCommitteeAgentSpec:
    id: str
    name: str
    domain: str
    owned_dimensions: list[str]
    focus_prompt: str
    focus_sections: list[str]
    default_assumption_topic: str
    default_open_question: str


LLM_AGENT_REGISTRY = [
    LLMCommitteeAgentSpec(
        "product_strategy_agent",
        "Product Strategy Agent",
        "Strategy",
        ["Problem Validity", "Product Quality"],
        "Judge whether the portfolio has a coherent product strategy, a bounded first release, and a credible sequence from problem framing to product shape.",
        ["problem_discovery", "product_vision", "product_requirements", "mvp_roadmap"],
        "product_scope",
        "Which product boundaries must remain fixed for the first pilot to stay strategic and credible?",
    ),
    LLMCommitteeAgentSpec(
        "market_opportunity_agent",
        "Market Opportunity Agent",
        "Strategy",
        ["Market Fit", "Economic Viability"],
        "Judge whether the market timing, buyer urgency, and segment selection support meaningful commercial opportunity.",
        ["problem_discovery", "competitive_landscape", "business_requirements", "post_launch_strategy"],
        "market_entry",
        "Which buyer segment is most credible for the first revenue-bearing launch?",
    ),
    LLMCommitteeAgentSpec(
        "customer_value_agent",
        "Customer Value Agent",
        "Product",
        ["Problem Validity", "Product Quality"],
        "Judge whether the portfolio solves a painful customer problem and whether the expected value is concrete enough for a pilot.",
        ["problem_discovery", "product_vision", "product_requirements", "success_metrics"],
        "customer_adoption",
        "What evidence would prove that the proposed workflow creates durable customer value?",
    ),
    LLMCommitteeAgentSpec(
        "business_model_agent",
        "Business Model Agent",
        "Business",
        ["Economic Viability", "Market Fit"],
        "Judge whether the business model, monetization path, and commercial packaging are credible for an early-stage launch.",
        ["business_requirements", "competitive_landscape", "success_metrics", "post_launch_strategy"],
        "pricing_model",
        "What commercial packaging assumptions must be validated before scaling beyond pilot customers?",
    ),
    LLMCommitteeAgentSpec(
        "finance_agent",
        "Finance Agent",
        "Business",
        ["Economic Viability"],
        "Judge whether the economics, cost exposure, and operating leverage are plausible enough to justify further investment.",
        ["business_requirements", "mvp_roadmap", "success_metrics", "post_launch_strategy"],
        "cost_structure",
        "Which cost assumption is most likely to undermine the portfolio if left unvalidated?",
    ),
    LLMCommitteeAgentSpec(
        "competitive_landscape_agent",
        "Competitive Landscape Agent",
        "Strategy",
        ["Market Fit", "Product Quality"],
        "Judge whether the portfolio is differentiated enough against alternatives and whether the competitive story will hold up under scrutiny.",
        ["competitive_landscape", "product_vision", "product_requirements", "post_launch_strategy"],
        "differentiation",
        "Which competitive claim must be validated to defend the first pilot narrative?",
    ),
    LLMCommitteeAgentSpec(
        "growth_gtm_agent",
        "Growth / GTM Agent",
        "Growth",
        ["Market Fit", "Economic Viability"],
        "Judge whether the launch path, channel assumptions, and expansion path support an efficient first go-to-market motion.",
        ["product_vision", "business_requirements", "mvp_roadmap", "post_launch_strategy"],
        "gtm_motion",
        "What go-to-market constraint is most likely to delay meaningful adoption?",
    ),
    LLMCommitteeAgentSpec(
        "architecture_agent",
        "Architecture Agent",
        "Engineering",
        ["Technical Feasibility", "Operational Resilience"],
        "Judge whether the proposed system shape, service boundaries, and integration model are technically coherent enough for an initial release.",
        ["architecture_system_design", "operational_resilience", "mvp_roadmap"],
        "integration_scope",
        "Which architectural boundary must stay fixed to preserve delivery credibility?",
    ),
    LLMCommitteeAgentSpec(
        "ai_systems_agent",
        "AI Systems Agent",
        "Engineering",
        ["AI Reliability", "Technical Feasibility"],
        "Judge whether the AI system design, evaluation plan, and human-in-the-loop controls are credible enough for safe deployment.",
        ["ai_agents_ethical_framework", "architecture_system_design", "success_metrics"],
        "model_quality",
        "Which AI quality signal must be demonstrated before the system can move beyond pilot use?",
    ),
    LLMCommitteeAgentSpec(
        "security_compliance_agent",
        "Security & Compliance Agent",
        "Risk",
        ["Security & Compliance", "Operational Resilience"],
        "Judge whether privacy, security, identity, retention, and compliance controls are sufficient for the proposed rollout.",
        ["ai_agents_ethical_framework", "operational_resilience", "architecture_system_design", "post_launch_strategy"],
        "control_posture",
        "Which security or compliance gap is the strongest blocker for broader rollout?",
    ),
    LLMCommitteeAgentSpec(
        "operations_reliability_agent",
        "Operations / Reliability Agent",
        "Operations",
        ["Operational Resilience", "Technical Feasibility"],
        "Judge whether the operating model, deployment safety, support ownership, and recovery posture are sufficient for production use.",
        ["operational_resilience", "architecture_system_design", "mvp_roadmap", "post_launch_strategy"],
        "operating_model",
        "What operational commitment is still missing for a reliable pilot launch?",
    ),
    LLMCommitteeAgentSpec(
        "data_strategy_agent",
        "Data Strategy Agent",
        "Data",
        ["AI Reliability", "Economic Viability"],
        "Judge whether the portfolio has a credible data acquisition, quality, governance, and measurement strategy.",
        ["ai_agents_ethical_framework", "business_requirements", "success_metrics", "post_launch_strategy"],
        "data_quality",
        "Which data dependency most threatens model quality or economic viability?",
    ),
    LLMCommitteeAgentSpec(
        "risk_governance_agent",
        "Risk & Governance Agent",
        "Risk",
        ["Security & Compliance", "AI Reliability"],
        "Judge whether governance, escalation, accountability, and control mechanisms are sufficient for bounded AI decision support.",
        ["ai_agents_ethical_framework", "operational_resilience", "post_launch_strategy"],
        "governance_model",
        "Which governance decision right is not yet explicit enough for safe launch approval?",
    ),
    LLMCommitteeAgentSpec(
        "implementation_feasibility_agent",
        "Implementation Feasibility Agent",
        "Engineering",
        ["Technical Feasibility", "Operational Resilience"],
        "Judge whether the delivery plan, implementation sequence, and dependency assumptions are realistic for the proposed MVP.",
        ["product_requirements", "architecture_system_design", "mvp_roadmap", "operational_resilience"],
        "delivery_plan",
        "Which implementation dependency is most likely to make the roadmap slip?",
    ),
    LLMCommitteeAgentSpec(
        "investment_committee_agent",
        "Investment Committee Agent",
        "Committee",
        ["Economic Viability", "Problem Validity", "Security & Compliance"],
        "Judge the overall investability of the portfolio by balancing strategic upside, execution risk, and governance exposure.",
        ["problem_discovery", "business_requirements", "operational_resilience", "post_launch_strategy", "success_metrics"],
        "investment_case",
        "What single unknown most weakens the investment case today?",
    ),
]


class LLMCommitteeDimensionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: str
    score: float
    confidence: float
    evidence_completeness: float
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    severity_flags: list[str] = Field(default_factory=list)


class LLMCommitteeRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    category: str
    severity: str
    claim: str
    evidence_refs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    recommended_action: str


class LLMCommitteeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stance: str
    reasoning_summary: str
    score_contributions: list[LLMCommitteeDimensionScore]
    identified_risks: list[LLMCommitteeRisk] = Field(default_factory=list)
    disagreement_flags: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    assumption_register: list[str] = Field(default_factory=list)


def allowed_evidence_refs() -> list[str]:
    return [f"portfolio.{section['key']}" for section in PORTFOLIO_SECTIONS]


def build_shared_portfolio_context(portfolio: CanonicalPortfolio) -> str:
    sections = [
        {
            "section_key": section["key"],
            "section_title": section["title"],
            "summary": portfolio.sections[section["key"]].summary,
            "key_points": portfolio.sections[section["key"]].key_points[:4],
        }
        for section in PORTFOLIO_SECTIONS
    ]
    payload = {
        "portfolio": {
            "portfolio_id": portfolio.portfolio_id,
            "portfolio_name": portfolio.portfolio_name,
            "portfolio_type": portfolio.portfolio_type,
            "owner": portfolio.owner,
            "submitted_at": portfolio.submitted_at,
        },
        "allowed_dimensions": SCORE_DIMENSIONS,
        "allowed_evidence_refs": allowed_evidence_refs(),
        "sections": sections,
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=True)
