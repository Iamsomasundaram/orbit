from __future__ import annotations

from .domain import RECOMMENDATION_RANK, SCORE_DIMENSIONS, clamp_score, clamp_unit, dedupe_preserve_order
from .reporting import build_markdown, severity_rank
from .schemas import AgentReview, CanonicalPortfolio, CommitteeReport, ConflictRecord, ConflictResolution, ResynthesisSession, Scorecard, validate_committee_report, validate_resynthesis_session
from .scorecard import build_scorecard_conditions, calculate_aggregate_metrics, determine_final_recommendation, downgrade_recommendation

DIMENSION_TOPIC_MAP = {
    "problem_validity": "Problem Validity",
    "Problem Validity": "Problem Validity",
    "market_fit": "Market Fit",
    "Market Fit": "Market Fit",
    "product_quality": "Product Quality",
    "Product Quality": "Product Quality",
    "technical_feasibility": "Technical Feasibility",
    "Technical Feasibility": "Technical Feasibility",
    "ai_reliability": "AI Reliability",
    "AI Reliability": "AI Reliability",
    "economic_viability": "Economic Viability",
    "Economic Viability": "Economic Viability",
    "operational_resilience": "Operational Resilience",
    "Operational Resilience": "Operational Resilience",
    "security_and_compliance": "Security & Compliance",
    "Security & Compliance": "Security & Compliance",
}
CRITICAL_RECHECK_DIMENSIONS = {"AI Reliability", "Security & Compliance"}


def build_resynthesis_id(debate_id: str) -> str:
    return f"resynthesis-{debate_id}"


def flagged_resolutions(resolutions: list[ConflictResolution]) -> list[ConflictResolution]:
    return [resolution for resolution in resolutions if resolution.score_change_required]


def topic_dimension(topic: str) -> str | None:
    return DIMENSION_TOPIC_MAP.get(topic)


def adjusted_dimension_scores(
    original_scorecard: Scorecard,
    resolutions: list[ConflictResolution],
) -> list[dict[str, object]]:
    score_map = {
        entry.dimension: entry.model_dump(mode="python")
        for entry in original_scorecard.dimension_scores
    }
    for resolution in resolutions:
        dimension = topic_dimension(resolution.topic)
        if dimension is None or dimension not in score_map:
            continue

        entry = score_map[dimension]
        penalty = 0.35 if dimension in CRITICAL_RECHECK_DIMENSIONS else 0.25
        confidence_penalty = 0.08 if dimension in CRITICAL_RECHECK_DIMENSIONS else 0.05
        completeness_penalty = 0.06 if dimension in CRITICAL_RECHECK_DIMENSIONS else 0.04
        entry["score"] = clamp_score(float(entry["score"]) - penalty)
        entry["confidence"] = clamp_unit(float(entry["confidence"]) - confidence_penalty)
        entry["evidence_completeness"] = clamp_unit(float(entry["evidence_completeness"]) - completeness_penalty)
        slug = dimension.lower().replace(" & ", "_").replace(" ", "_")
        entry["severity_flags"] = sorted(
            dedupe_preserve_order([*list(entry["severity_flags"]), f"debate_recheck_{slug}"])
        )
        entry["rationale"] = (
            f"{entry['rationale']} Resynthesis applied {resolution.resolution_id} for {resolution.topic} "
            "after moderator-directed score recheck."
        )

    return [score_map[dimension] for dimension in SCORE_DIMENSIONS]


def resynthesized_scorecard(
    portfolio: CanonicalPortfolio,
    run_id: str,
    reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
    original_scorecard: Scorecard,
    resolutions: list[ConflictResolution],
) -> Scorecard:
    dimension_scores = adjusted_dimension_scores(original_scorecard, resolutions)
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
    if RECOMMENDATION_RANK[final_recommendation] > RECOMMENDATION_RANK["Pilot Only"]:
        final_recommendation = downgrade_recommendation(final_recommendation)

    conditions = dedupe_preserve_order(
        [
            *build_scorecard_conditions(findings, conflicts),
            *[
                condition
                for resolution in resolutions
                for condition in resolution.applied_conditions
            ],
        ]
    )[:10]

    return Scorecard.model_validate(
        {
            "portfolio_id": portfolio.portfolio_id,
            "run_id": run_id,
            "dimension_scores": dimension_scores,
            "weighted_composite_score": weighted_composite_score,
            "average_confidence": average_confidence,
            "average_evidence_completeness": average_evidence_completeness,
            "severity_flags": severity_flags,
            "final_recommendation": final_recommendation,
            "override_applied": override_applied or bool(resolutions),
            "conditions": conditions,
        }
    )


def ordered_conflicts(conflicts: list[ConflictRecord], resolutions: list[ConflictResolution]) -> list[ConflictRecord]:
    priority = {resolution.conflict_id: index for index, resolution in enumerate(resolutions)}
    return sorted(conflicts, key=lambda conflict: (priority.get(conflict.conflict_id, len(priority)), conflict.conflict_id))


def resynthesized_committee_report(
    portfolio: CanonicalPortfolio,
    run_id: str,
    reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
    original_scorecard: Scorecard,
    original_report: CommitteeReport,
    scorecard: Scorecard,
    resolutions: list[ConflictResolution],
) -> CommitteeReport:
    findings = [
        {
            **finding.model_dump(mode="json"),
            "agent_id": review.agent_id,
        }
        for review in reviews
        for finding in review.findings
    ]
    findings.sort(key=lambda finding: (-severity_rank(finding["severity"]), finding["title"]))
    score_changed = scorecard.final_recommendation != original_scorecard.final_recommendation or (
        scorecard.weighted_composite_score != original_scorecard.weighted_composite_score
    )
    report = CommitteeReport.model_validate(
        {
            "portfolio_id": portfolio.portfolio_id,
            "run_id": run_id,
            "executive_summary": (
                f"Committee re-synthesis processed {len(resolutions)} debate resolution(s) that required score recheck "
                f"for run {run_id}. The final recommendation is {scorecard.final_recommendation}, "
                f"{'changed from' if score_changed else 'retained from'} the original committee result."
            ),
            "top_findings": findings[:8],
            "top_conflicts": [conflict.model_dump(mode="json") for conflict in ordered_conflicts(conflicts, resolutions)[:5]],
            "conditions": scorecard.conditions,
            "audit_notes": [
                *original_report.audit_notes,
                f"Milestone 6 re-synthesis evaluated {len(resolutions)} conflict resolution(s) marked score_change_required.",
                "Re-synthesis stayed bounded to persisted debate resolutions and existing structured reviewer artifacts.",
            ],
            "markdown": "",
        }
    )
    report = CommitteeReport.model_validate(
        {
            **report.model_dump(mode="json"),
            "markdown": build_markdown(portfolio, scorecard, report),
        }
    )
    return validate_committee_report(report)


def build_resynthesis_session(
    debate_id: str,
    run_id: str,
    portfolio_id: str,
    resolutions: list[ConflictResolution],
    active_artifact_source: str,
) -> ResynthesisSession:
    score_recheck_count = len(resolutions)
    reused_original_artifacts = active_artifact_source == "original"
    status = "completed_without_changes" if reused_original_artifacts else "completed_with_recheck"
    return validate_resynthesis_session(
        {
            "resynthesis_id": build_resynthesis_id(debate_id),
            "debate_id": debate_id,
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "resynthesis_status": status,
            "score_change_required_count": score_recheck_count,
            "reused_original_artifacts": reused_original_artifacts,
            "active_artifact_source": active_artifact_source,
            "applied_resolution_ids": [resolution.resolution_id for resolution in resolutions],
            "executive_summary": (
                f"Resynthesis {'reused the original committee artifacts' if reused_original_artifacts else 'produced a rechecked scorecard and committee report'} "
                f"for debate {debate_id}."
            ),
            "audit_notes": [
                "Resynthesis consumed persisted debate resolutions only.",
                "The path stays synchronous and bounded to one resynthesis session per debate.",
                "Original review artifacts remain preserved even when re-synthesized artifacts are produced.",
            ],
        }
    )


def run_score_recheck_and_resynthesis(
    debate_id: str,
    portfolio: CanonicalPortfolio,
    run_id: str,
    reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
    original_scorecard: Scorecard,
    original_report: CommitteeReport,
    resolutions: list[ConflictResolution],
) -> dict[str, object]:
    recheck_resolutions = flagged_resolutions(resolutions)
    if not recheck_resolutions:
        session = build_resynthesis_session(
            debate_id=debate_id,
            run_id=run_id,
            portfolio_id=portfolio.portfolio_id,
            resolutions=[],
            active_artifact_source="original",
        )
        return {
            "resynthesis_session": session,
            "resynthesized_scorecard": None,
            "resynthesized_committee_report": None,
        }

    scorecard = resynthesized_scorecard(
        portfolio=portfolio,
        run_id=run_id,
        reviews=reviews,
        conflicts=conflicts,
        original_scorecard=original_scorecard,
        resolutions=recheck_resolutions,
    )
    report = resynthesized_committee_report(
        portfolio=portfolio,
        run_id=run_id,
        reviews=reviews,
        conflicts=conflicts,
        original_scorecard=original_scorecard,
        original_report=original_report,
        scorecard=scorecard,
        resolutions=recheck_resolutions,
    )
    session = build_resynthesis_session(
        debate_id=debate_id,
        run_id=run_id,
        portfolio_id=portfolio.portfolio_id,
        resolutions=recheck_resolutions,
        active_artifact_source="resynthesized",
    )
    return {
        "resynthesis_session": session,
        "resynthesized_scorecard": scorecard,
        "resynthesized_committee_report": report,
    }
