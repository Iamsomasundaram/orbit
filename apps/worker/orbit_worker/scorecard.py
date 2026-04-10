from __future__ import annotations

from .domain import DIMENSION_WEIGHTS, RECOMMENDATION_ORDER, RECOMMENDATION_RANK, SCORE_DIMENSIONS, clamp_score, dedupe_preserve_order, round_half_up
from .schemas import AgentReview, CanonicalPortfolio, ConflictRecord, DimensionScore, Finding, Scorecard, validate_scorecard


def mean(values: list[float]) -> float:
    return 0 if not values else sum(values) / len(values)


def fixed_2(value: float) -> float:
    return round_half_up(value, 2)


def downgrade_recommendation(recommendation: str) -> str:
    index = max(0, RECOMMENDATION_RANK[recommendation] - 1)
    return RECOMMENDATION_ORDER[index]


def calculate_aggregate_metrics(dimension_scores: list[dict[str, object] | DimensionScore]) -> tuple[float, float, float, list[str]]:
    normalized_scores = [
        entry if isinstance(entry, dict) else entry.model_dump(mode="python")
        for entry in dimension_scores
    ]
    weighted_composite_score = fixed_2(
        sum(float(entry["score"]) * DIMENSION_WEIGHTS[str(entry["dimension"])] for entry in normalized_scores) / 100,
    )
    average_confidence = fixed_2(mean([float(entry["confidence"]) for entry in normalized_scores]))
    average_evidence_completeness = fixed_2(mean([float(entry["evidence_completeness"]) for entry in normalized_scores]))
    severity_flags = sorted(
        dedupe_preserve_order(
            flag
            for entry in normalized_scores
            for flag in list(entry["severity_flags"])
        )
    )
    return weighted_composite_score, average_confidence, average_evidence_completeness, severity_flags


def determine_final_recommendation(
    weighted_composite_score: float,
    average_confidence: float,
    average_evidence_completeness: float,
    findings: list[Finding],
    conflicts: list[ConflictRecord],
) -> tuple[str, bool]:
    critical_governance_finding = next(
        (
            finding
            for finding in findings
            if finding.severity == "critical" and finding.category in {"security_and_compliance", "ai_reliability"}
        ),
        None,
    )

    if weighted_composite_score >= 4.2 and average_confidence >= 0.7 and average_evidence_completeness >= 0.8 and not critical_governance_finding:
        final_recommendation = "Strong Proceed"
    elif weighted_composite_score >= 3.5 and not critical_governance_finding:
        final_recommendation = "Proceed with Conditions"
    elif weighted_composite_score >= 2.8:
        final_recommendation = "Pilot Only"
    elif weighted_composite_score >= 2.0:
        final_recommendation = "High Risk"
    else:
        final_recommendation = "Do Not Proceed"

    high_conflicts = len([conflict for conflict in conflicts if conflict.severity == "high"])
    if high_conflicts >= 4 and RECOMMENDATION_RANK[final_recommendation] > RECOMMENDATION_RANK["Pilot Only"]:
        final_recommendation = downgrade_recommendation(final_recommendation)
    if critical_governance_finding and RECOMMENDATION_RANK[final_recommendation] > RECOMMENDATION_RANK["High Risk"]:
        final_recommendation = "High Risk"

    return final_recommendation, bool(critical_governance_finding)


def build_scorecard_conditions(findings: list[Finding], conflicts: list[ConflictRecord]) -> list[str]:
    return dedupe_preserve_order(
        [
            *[
                finding.recommended_action
                for finding in findings
                if finding.severity in {"major", "critical"}
            ][:6],
            *[
                f"Resolve {conflict.conflict_type} on {conflict.topic} before broad rollout."
                for conflict in conflicts
                if conflict.severity == "high"
            ][:3],
        ]
    )[:8]


def build_committee_scorecard(
    portfolio: CanonicalPortfolio,
    run_id: str,
    reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
) -> Scorecard:
    dimension_scores = []
    for dimension in SCORE_DIMENSIONS:
        entries = [score for review in reviews for score in review.dimension_scores if score.dimension == dimension]
        dimension_scores.append(
            {
                "dimension": dimension,
                "score": clamp_score(mean([entry.score for entry in entries])),
                "confidence": fixed_2(mean([entry.confidence for entry in entries])),
                "evidence_completeness": fixed_2(mean([entry.evidence_completeness for entry in entries])),
                "severity_flags": sorted(dedupe_preserve_order(flag for entry in entries for flag in entry.severity_flags)),
                "rationale": f"Committee score derived from {len(entries)} structured reviewer dimension entries.",
                "evidence_refs": dedupe_preserve_order(ref for entry in entries for ref in entry.evidence_refs),
            }
        )

    weighted_composite_score, average_confidence, average_evidence_completeness, severity_flags = calculate_aggregate_metrics(
        dimension_scores
    )
    findings = [finding for review in reviews for finding in review.findings]
    final_recommendation, override_applied = determine_final_recommendation(
        weighted_composite_score,
        average_confidence,
        average_evidence_completeness,
        findings,
        conflicts,
    )
    conditions = build_scorecard_conditions(findings, conflicts)

    return validate_scorecard(
        {
            "portfolio_id": portfolio.portfolio_id,
            "run_id": run_id,
            "dimension_scores": dimension_scores,
            "weighted_composite_score": weighted_composite_score,
            "average_confidence": average_confidence,
            "average_evidence_completeness": average_evidence_completeness,
            "severity_flags": severity_flags,
            "final_recommendation": final_recommendation,
            "override_applied": override_applied,
            "conditions": conditions,
        }
    )

