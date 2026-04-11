from __future__ import annotations

from .schemas import AgentReview, CanonicalPortfolio, CommitteeReport, ConflictRecord, Scorecard, validate_committee_report


def severity_rank(value: str) -> int:
    return {"critical": 5, "major": 4, "moderate": 3, "minor": 2, "informational": 1}.get(value, 0)


def review_runtime(reviews: list[AgentReview]) -> tuple[str, str]:
    if not reviews:
        return "unknown", "unknown"
    metadata = reviews[0].review_metadata
    return metadata.model_provider, metadata.prompt_contract_version


def build_markdown(portfolio: CanonicalPortfolio, scorecard: Scorecard, report: CommitteeReport) -> str:
    score_rows = "\n".join(
        f"| {entry.dimension} | {entry.score:.2f} | {entry.confidence:.2f} | {entry.evidence_completeness:.2f} |"
        for entry in scorecard.dimension_scores
    )
    findings = "\n".join(f"- {finding.title} ({finding.severity}): {finding.claim}" for finding in report.top_findings)
    conflicts = "\n".join(
        f"- {conflict.conflict_type} on {conflict.topic}: {conflict.trigger_reason}"
        for conflict in report.top_conflicts
    )
    conditions = "\n".join(f"- {condition}" for condition in report.conditions)
    audit_notes = "\n".join(f"- {note}" for note in report.audit_notes)

    return "\n".join(
        [
            f"# ORBIT Committee Report: {portfolio.portfolio_name}",
            "",
            f"Final recommendation: **{scorecard.final_recommendation}**",
            f"Weighted composite score: **{scorecard.weighted_composite_score:.2f} / 5.00**",
            f"Average confidence: **{scorecard.average_confidence:.2f}**",
            f"Average evidence completeness: **{scorecard.average_evidence_completeness:.2f}**",
            "",
            "## Executive Summary",
            report.executive_summary,
            "",
            "## Scorecard",
            "| Dimension | Score | Confidence | Evidence Completeness |",
            "| --- | ---: | ---: | ---: |",
            score_rows,
            "",
            "## Top Findings",
            findings,
            "",
            "## Top Conflicts",
            conflicts or "- No conflicts detected.",
            "",
            "## Conditions",
            conditions or "- No additional conditions.",
            "",
            "## Audit Notes",
            audit_notes,
            "",
        ]
    )


def build_committee_report(
    portfolio: CanonicalPortfolio,
    run_id: str,
    reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
    scorecard: Scorecard,
) -> CommitteeReport:
    top_findings = [
        {
            **finding.model_dump(mode="json"),
            "agent_id": review.agent_id,
        }
        for review in reviews
        for finding in review.findings
    ]
    top_findings.sort(key=lambda finding: (-severity_rank(finding["severity"]), finding["title"]))
    model_provider, prompt_contract_version = review_runtime(reviews)
    if model_provider == "deterministic-thin-slice":
        executive_summary = (
            f"{portfolio.portfolio_name} completes the Milestone 0.5 thin-slice review with {len(reviews)} specialist reviews, "
            f"{len(conflicts)} structured conflicts, and a final recommendation of {scorecard.final_recommendation}. "
            "The committee sees strong business and product potential, but it still requires explicit integration, resilience, "
            "and governance conditions before broader rollout."
        )
        audit_notes = [
            "Thin slice executed with deterministic structured reviewer logic for all 15 agents.",
            f"Conflict detector v1 evaluated {len(conflicts)} structured conflict records.",
            "Scorecard recommendation follows the Milestone 0 override rules for governance blockers.",
        ]
    else:
        executive_summary = (
            f"{portfolio.portfolio_name} completed an ORBIT llm-backed committee review with {len(reviews)} parallel specialist agents, "
            f"{len(conflicts)} structured conflicts, and a final recommendation of {scorecard.final_recommendation}. "
            "The committee outcome remains bounded by deterministic conflict detection, score aggregation, and governance overrides."
        )
        audit_notes = [
            f"Parallel llm committee execution completed under prompt contract {prompt_contract_version}.",
            f"Structured conflict detection evaluated {len(conflicts)} persisted reviewer artifacts after llm fan-out.",
            "Deterministic score aggregation and governance overrides remained the final committee control surface.",
        ]
    report = validate_committee_report(
        {
            "portfolio_id": portfolio.portfolio_id,
            "run_id": run_id,
            "executive_summary": executive_summary,
            "top_findings": top_findings[:8],
            "top_conflicts": [conflict.model_dump(mode="json") for conflict in conflicts[:5]],
            "conditions": scorecard.conditions,
            "audit_notes": audit_notes,
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
