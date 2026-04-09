from __future__ import annotations

import re
from typing import Any

from .domain import AGENT_REGISTRY, RECOMMENDATION_ORDER, RECOMMENDATION_RANK, clamp_score, clamp_unit, dedupe_preserve_order
from .schemas import AgentReview, CanonicalPortfolio, DimensionScore, Finding, validate_agent_review

POSITIVE_SIGNAL_META = {
    "problem_strength": {"title": "Problem is concrete and tied to measurable pain", "category": "problem_validity", "severity": "minor", "action": "Carry the quantified business pain into pilot framing and scorecard rationale."},
    "buyer_clarity": {"title": "Initial buyer and adoption path are clearly identifiable", "category": "market_fit", "severity": "minor", "action": "Use the named buyer profile to constrain first-wave customer selection."},
    "monetization_clarity": {"title": "Commercial model shows early economic discipline", "category": "economic_viability", "severity": "minor", "action": "Translate margin and pricing assumptions into explicit launch conditions."},
    "market_story_strength": {"title": "Positioning is differentiated enough for a first GTM story", "category": "market_fit", "severity": "minor", "action": "Anchor the launch narrative on workflow acceleration and auditability."},
    "mvp_focus": {"title": "The MVP scope is focused enough for a thin-slice launch", "category": "product_quality", "severity": "minor", "action": "Protect the bounded workflow scope during the first release."},
    "workflow_traceability": {"title": "Traceability supports a defensible user workflow", "category": "product_quality", "severity": "minor", "action": "Retain traceability and approval export as non-negotiable product requirements."},
    "customer_value_clarity": {"title": "Customer value is easy to explain in operational terms", "category": "product_quality", "severity": "minor", "action": "Turn the value story into measurable onboarding outcomes."},
    "architecture_strength": {"title": "System design is coherent for an initial production slice", "category": "technical_feasibility", "severity": "minor", "action": "Preserve the current service separation and make deployment topology explicit."},
    "ai_controls": {"title": "Human approval and audit visibility improve AI control", "category": "ai_reliability", "severity": "minor", "action": "Keep human approval and output logging as hard launch constraints."},
    "ops_controls": {"title": "Operational controls are named early enough to shape launch criteria", "category": "operational_resilience", "severity": "minor", "action": "Convert the named controls into concrete runbooks and ownership assignments."},
    "security_controls": {"title": "Baseline governance controls are at least acknowledged", "category": "security_and_compliance", "severity": "minor", "action": "Carry redaction, auditability, and access control language into the first security review."},
}

RISK_SIGNAL_META = {
    "integration_risk": {"title": "Integration complexity remains a first-wave risk", "category": "technical_feasibility", "severity": "moderate", "action": "Scope integration commitments explicitly and treat them as launch conditions."},
    "resilience_gap": {"title": "Recovery and release posture is not yet strong enough", "category": "operational_resilience", "severity": "major", "action": "Define recovery objectives, rollback rules, and validation steps before broader rollout."},
    "ai_evaluation_gap": {"title": "AI evaluation evidence is still incomplete", "category": "ai_reliability", "severity": "major", "action": "Define offline evaluation benchmarks and acceptance thresholds before scale."},
    "support_gap": {"title": "Support and sustainment readiness lag the product ambition", "category": "operational_resilience", "severity": "major", "action": "Assign ownership for onboarding, support, and maintenance before expanding pilots."},
    "compliance_gap": {"title": "Compliance posture is directionally positive but incomplete", "category": "security_and_compliance", "severity": "major", "action": "Add retention, identity, incident, and jurisdiction controls before broad rollout."},
}


def mean(values: list[float]) -> float:
    return 0 if not values else sum(values) / len(values)


def collect_text(portfolio: CanonicalPortfolio, keys: list[str]) -> str:
    return "\n".join(
        f"{portfolio.sections[key].summary}\n{chr(10).join(portfolio.sections[key].key_points)}"
        for key in keys
    ).lower()


def has_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def analyze_portfolio(portfolio: CanonicalPortfolio) -> dict[str, Any]:
    problem_text = collect_text(portfolio, ["problem_discovery"])
    vision_text = collect_text(portfolio, ["product_vision"])
    competitive_text = collect_text(portfolio, ["competitive_landscape"])
    business_text = collect_text(portfolio, ["business_requirements"])
    product_text = collect_text(portfolio, ["product_requirements"])
    architecture_text = collect_text(portfolio, ["architecture_system_design"])
    ai_text = collect_text(portfolio, ["ai_agents_ethical_framework"])
    ops_text = collect_text(portfolio, ["operational_resilience"])
    roadmap_text = collect_text(portfolio, ["mvp_roadmap"])
    metrics_text = collect_text(portfolio, ["success_metrics"])
    post_launch_text = collect_text(portfolio, ["post_launch_strategy"])
    all_text = "\n".join(
        [
            problem_text,
            vision_text,
            competitive_text,
            business_text,
            product_text,
            architecture_text,
            ai_text,
            ops_text,
            roadmap_text,
            metrics_text,
            post_launch_text,
        ]
    )
    metric_count = len(re.findall(r"\b\d+(?:\.\d+)?\b", all_text))

    signals = {
        "problem_strength": has_any(problem_text, ["cycle-time", "hours", "manual", "auditability", "workflow"]),
        "buyer_clarity": has_any("\n".join([problem_text, vision_text, business_text]), ["vp procurement", "cfo", "buyer", "procurement leadership", "mid-market"]),
        "monetization_clarity": has_any("\n".join([business_text, metrics_text]), ["gross margin", "enterprise pricing", "roi", "pricing"]),
        "market_story_strength": has_any("\n".join([competitive_text, vision_text]), ["workflow acceleration", "differentiation", "incumbents", "time to value"]),
        "mvp_focus": has_any("\n".join([product_text, roadmap_text]), ["mvp", "phase 1", "approval packet", "workflow", "pilot customers"]),
        "workflow_traceability": has_any(product_text, ["traceability", "audit trail", "approval packet", "comment threads"]),
        "customer_value_clarity": has_any("\n".join([problem_text, metrics_text]), ["cycle-time", "throughput", "adoption", "retention", "roi"]),
        "architecture_strength": has_any(architecture_text, ["web app", "api", "worker", "event-driven", "tenant isolation", "data store"]),
        "ai_controls": has_any(ai_text, ["human approval", "logged", "redaction", "access policy", "visible to users"]),
        "ops_controls": has_any(ops_text, ["backup", "monitoring", "availability", "recovery", "staged rollout"]),
        "security_controls": has_any("\n".join([ai_text, ops_text]), ["redaction", "access policy", "audit", "logged"]),
        "integration_risk": has_any("\n".join([architecture_text, post_launch_text]), ["integration", "connector", "erp"]),
        "resilience_gap": has_any(ops_text, ["future enhancement", "regional failover"]) or not has_any(ops_text, ["rollback", "drill", "tested recovery"]),
        "ai_evaluation_gap": not has_any("\n".join([ai_text, metrics_text]), ["evaluation", "benchmark", "dataset", "threshold"]),
        "support_gap": not has_any("\n".join([ops_text, post_launch_text]), ["customer success", "support", "onboarding ownership"]),
        "compliance_gap": not has_any("\n".join([ai_text, ops_text, post_launch_text]), ["retention", "jurisdiction", "incident response", "identity", "key management", "regulatory"]),
        "metric_depth": metric_count >= 6,
    }

    base_scores = {
        "Problem Validity": clamp_score(3.2 + (0.6 if signals["problem_strength"] else 0) + (0.3 if signals["buyer_clarity"] else 0) + (0.15 if signals["metric_depth"] else 0)),
        "Market Fit": clamp_score(3.0 + (0.4 if signals["buyer_clarity"] else 0) + (0.35 if signals["market_story_strength"] else 0) - (0.1 if signals["integration_risk"] else 0)),
        "Product Quality": clamp_score(3.0 + (0.35 if signals["mvp_focus"] else 0) + (0.3 if signals["workflow_traceability"] else 0) + (0.15 if signals["customer_value_clarity"] else 0) - (0.1 if signals["ai_evaluation_gap"] else 0)),
        "Technical Feasibility": clamp_score(3.0 + (0.55 if signals["architecture_strength"] else 0) + (0.15 if signals["mvp_focus"] else 0) - (0.1 if signals["integration_risk"] else 0)),
        "AI Reliability": clamp_score(3.1 + (0.4 if signals["ai_controls"] else 0) - (0.2 if signals["ai_evaluation_gap"] else 0)),
        "Economic Viability": clamp_score(3.0 + (0.45 if signals["monetization_clarity"] else 0) + (0.2 if signals["customer_value_clarity"] else 0) - (0.15 if signals["integration_risk"] else 0)),
        "Operational Resilience": clamp_score(3.0 + (0.3 if signals["ops_controls"] else 0) + (0.2 if signals["architecture_strength"] else 0) - (0.25 if signals["resilience_gap"] else 0) - (0.12 if signals["support_gap"] else 0)),
        "Security & Compliance": clamp_score(3.15 + (0.25 if signals["security_controls"] else 0) + (0.15 if signals["ai_controls"] else 0) - (0.15 if signals["compliance_gap"] else 0) - (0.05 if signals["resilience_gap"] else 0)),
    }

    base_completeness = {
        "Problem Validity": clamp_unit(0.7 + (0.1 if signals["problem_strength"] else 0) + (0.08 if signals["metric_depth"] else 0)),
        "Market Fit": clamp_unit(0.66 + (0.08 if signals["buyer_clarity"] else 0) + (0.06 if signals["market_story_strength"] else 0)),
        "Product Quality": clamp_unit(0.64 + (0.08 if signals["mvp_focus"] else 0) + (0.08 if signals["workflow_traceability"] else 0)),
        "Technical Feasibility": clamp_unit(0.62 + (0.12 if signals["architecture_strength"] else 0) - (0.04 if signals["integration_risk"] else 0)),
        "AI Reliability": clamp_unit(0.56 + (0.14 if signals["ai_controls"] else 0) - (0.04 if signals["ai_evaluation_gap"] else 0)),
        "Economic Viability": clamp_unit(0.6 + (0.12 if signals["monetization_clarity"] else 0) - (0.03 if signals["integration_risk"] else 0)),
        "Operational Resilience": clamp_unit(0.6 + (0.12 if signals["ops_controls"] else 0) - (0.05 if signals["resilience_gap"] else 0) - (0.03 if signals["support_gap"] else 0)),
        "Security & Compliance": clamp_unit(0.58 + (0.08 if signals["security_controls"] else 0) + (0.08 if signals["ai_controls"] else 0) - (0.04 if signals["compliance_gap"] else 0)),
    }

    return {"signals": signals, "base_scores": base_scores, "base_completeness": base_completeness}


def build_finding(agent: Any, signal_key: str, kind: str, dimension_scores: list[DimensionScore]) -> Finding:
    meta = POSITIVE_SIGNAL_META[signal_key] if kind == "positive" else RISK_SIGNAL_META[signal_key]
    return Finding.model_validate(
        {
            "finding_id": f"{agent.id}-{kind}-{signal_key}",
            "title": meta["title"],
            "category": meta["category"],
            "severity": meta["severity"],
            "claim": f"{agent.name} notes that {meta['title'].lower()} for this portfolio based on the available source material.",
            "evidence_refs": agent.positive_refs if kind == "positive" else agent.risk_refs,
            "assumptions": [agent.assumption] if kind == "risk" else [],
            "recommended_action": meta["action"],
            "score_impacts": [
                {
                    "dimension": score.dimension,
                    "delta": 0.15 if kind == "positive" else -0.25,
                    "rationale": f"{agent.name} adjusts {score.dimension} through {signal_key}.",
                }
                for score in dimension_scores
            ],
        }
    )


def score_recommendation(score_average: float, completeness_average: float, bias: float) -> str:
    weighted = score_average + bias
    if weighted >= 4.15 and completeness_average >= 0.72:
        return "Strong Proceed"
    if weighted >= 3.3:
        return "Proceed with Conditions"
    if weighted >= 2.55:
        return "Pilot Only"
    if weighted >= 1.8:
        return "High Risk"
    return "Do Not Proceed"


def downgrade_recommendation(recommendation: str, steps: int) -> str:
    current = RECOMMENDATION_RANK[recommendation]
    next_index = max(0, current - steps)
    return RECOMMENDATION_ORDER[next_index]


def build_agent_review(agent: Any, portfolio: CanonicalPortfolio, analysis: dict[str, Any]) -> AgentReview:
    positive_active = analysis["signals"][agent.positive_signal]
    risk_active = analysis["signals"][agent.risk_signal]
    dimension_scores: list[DimensionScore] = []
    for dimension in agent.dimensions:
        score = analysis["base_scores"][dimension] + agent.dimension_biases.get(dimension, 0)
        if risk_active:
            score -= agent.strictness * 0.2
        if positive_active:
            score += 0.05
        completeness = analysis["base_completeness"][dimension] + (0.03 if positive_active else 0) - (agent.strictness * 0.12 if risk_active else 0)
        confidence = clamp_unit(0.55 + (0.12 if positive_active else 0) - (0.08 if risk_active else 0) + ((completeness - 0.6) * 0.5) - (agent.strictness * 0.05))
        completeness = clamp_unit(completeness)
        severity_flags: list[str] = []
        if risk_active:
            severity_flags.append(f"{agent.risk_signal}_{re.sub(r'[^a-z0-9]+', '_', dimension.lower())}")
        dimension_scores.append(
            DimensionScore.model_validate(
                {
                    "dimension": dimension,
                    "score": clamp_score(score),
                    "confidence": confidence,
                    "evidence_completeness": completeness,
                    "severity_flags": severity_flags,
                    "rationale": f"{agent.name} adjusts {dimension} using deterministic thin-slice heuristics for {agent.positive_signal} and {agent.risk_signal}.",
                    "evidence_refs": dedupe_preserve_order([*agent.positive_refs, *agent.risk_refs]),
                }
            )
        )

    score_average = mean([score.score for score in dimension_scores])
    completeness_average = mean([score.evidence_completeness for score in dimension_scores])
    recommendation = score_recommendation(score_average, completeness_average, agent.recommendation_bias)
    if risk_active and agent.strictness >= 0.35 and score_average < 3.2:
        recommendation = downgrade_recommendation(recommendation, 1)
    if agent.id == "legal_compliance_reviewer" and analysis["signals"]["compliance_gap"] and score_average < 3.2:
        recommendation = downgrade_recommendation(recommendation, 1)

    findings: list[Finding] = []
    if positive_active:
        findings.append(build_finding(agent, agent.positive_signal, "positive", dimension_scores))
    if risk_active:
        findings.append(build_finding(agent, agent.risk_signal, "risk", dimension_scores))

    return validate_agent_review(
        {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "portfolio_id": portfolio.portfolio_id,
            "review_summary": f"{agent.name} recommends {recommendation} with strongest support in {dimension_scores[0].dimension} and primary concern in {agent.risk_signal}.",
            "findings": [finding.model_dump(mode="json") for finding in findings],
            "dimension_scores": [score.model_dump(mode="json") for score in dimension_scores],
            "recommendation": recommendation,
            "open_questions": [agent.open_question],
            "evidence_gaps": [agent.evidence_gap] if risk_active else [],
            "assumption_register": [agent.assumption],
            "review_metadata": {
                "prompt_contract_version": "m0.5-deterministic-v1",
                "model_provider": "deterministic-thin-slice",
                "model_name": "heuristic-reviewer",
                "duration_ms": 0,
            },
        }
    )


def run_specialist_reviews(portfolio: CanonicalPortfolio) -> list[AgentReview]:
    analysis = analyze_portfolio(portfolio)
    return [build_agent_review(agent, portfolio, analysis) for agent in AGENT_REGISTRY]
