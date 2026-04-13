from __future__ import annotations

from typing import Iterable

from .domain import SEVERITY_RANK, get_recommendation_distance
from .schemas import AgentReview, ConflictRecord, validate_conflict_record


def pairwise(items: list[AgentReview]) -> list[tuple[AgentReview, AgentReview]]:
    pairs: list[tuple[AgentReview, AgentReview]] = []
    for left in range(len(items)):
        for right in range(left + 1, len(items)):
            pairs.append((items[left], items[right]))
    return pairs


def assumption_map(review: AgentReview) -> dict[str, str]:
    return {topic: value for topic, value in (entry.split("=", 1) for entry in review.assumption_register)}


def create_conflict(
    conflict_id: str,
    conflict_type: str,
    topic: str,
    participants: Iterable[str],
    severity: str,
    conflict_category: str,
    conflict_reason: str,
    trigger_reason: str,
    routing_reason: str,
    *,
    conflicting_claims: list[str] | None = None,
    conflicting_evidence: list[str] | None = None,
) -> ConflictRecord:
    participant_list = sorted(set(participants))
    return validate_conflict_record(
        {
            "conflict_id": conflict_id,
            "conflict_type": conflict_type,
            "topic": topic,
            "participants": participant_list,
            "conflicting_agents": participant_list,
            "conflicting_claims": conflicting_claims or [],
            "conflicting_evidence": conflicting_evidence or [],
            "severity": severity,
            "conflict_category": conflict_category,
            "conflict_reason": conflict_reason,
            "trigger_reason": trigger_reason,
            "supporting_artifacts": [f"agent_review.{participant}" for participant in participant_list],
            "debate_required": severity == "high",
            "routing_reason": routing_reason,
            "status": "open",
        }
    )


def detect_conflicts(reviews: list[AgentReview]) -> list[ConflictRecord]:
    review_map = {review.agent_id: review for review in reviews}
    recommendation_participants: set[str] = set()
    assumption_clusters: dict[str, dict[str, object]] = {}
    score_clusters: dict[str, dict[str, object]] = {}
    completeness_clusters: dict[str, dict[str, object]] = {}
    severity_clusters: dict[str, dict[str, object]] = {}

    for left, right in pairwise(reviews):
        recommendation_distance = get_recommendation_distance(left.recommendation, right.recommendation)
        if recommendation_distance >= 2:
            recommendation_participants.add(left.agent_id)
            recommendation_participants.add(right.agent_id)

        left_assumptions = assumption_map(left)
        right_assumptions = assumption_map(right)
        for topic, value in left_assumptions.items():
            if topic in right_assumptions and right_assumptions[topic] != value:
                cluster = assumption_clusters.get(topic, {"participants": set(), "examples": []})
                cluster["participants"].add(left.agent_id)
                cluster["participants"].add(right.agent_id)
                example = f"{value} vs {right_assumptions[topic]}"
                if example not in cluster["examples"]:
                    cluster["examples"].append(example)
                assumption_clusters[topic] = cluster

        for left_score in left.dimension_scores:
            right_score = next((candidate for candidate in right.dimension_scores if candidate.dimension == left_score.dimension), None)
            if right_score is None:
                continue
            score_delta = abs(left_score.score - right_score.score)
            if score_delta >= 1.5:
                cluster = score_clusters.get(left_score.dimension, {"participants": set(), "max_delta": 0.0})
                cluster["participants"].add(left.agent_id)
                cluster["participants"].add(right.agent_id)
                cluster["max_delta"] = max(cluster["max_delta"], score_delta)
                score_clusters[left_score.dimension] = cluster
            completeness_delta = abs(left_score.evidence_completeness - right_score.evidence_completeness)
            if completeness_delta >= 0.35:
                cluster = completeness_clusters.get(left_score.dimension, {"participants": set(), "max_delta": 0.0})
                cluster["participants"].add(left.agent_id)
                cluster["participants"].add(right.agent_id)
                cluster["max_delta"] = max(cluster["max_delta"], completeness_delta)
                completeness_clusters[left_score.dimension] = cluster

        left_categories = {finding.category: finding for finding in left.findings}
        for finding in right.findings:
            matching = left_categories.get(finding.category)
            if matching is None:
                continue
            severity_delta = abs(SEVERITY_RANK[matching.severity] - SEVERITY_RANK[finding.severity])
            if severity_delta >= 2:
                cluster = severity_clusters.get(finding.category, {"participants": set(), "max_delta": 0})
                cluster["participants"].add(left.agent_id)
                cluster["participants"].add(right.agent_id)
                cluster["max_delta"] = max(cluster["max_delta"], severity_delta)
                severity_clusters[finding.category] = cluster

    conflicts: list[ConflictRecord] = []
    index = 1
    if recommendation_participants:
        claims, evidence = _collect_reasoning(review_map, recommendation_participants)
        conflicts.append(
            create_conflict(
                f"conflict-{index:03d}",
                "recommendation_conflict",
                "rollout_timing",
                recommendation_participants,
                "high",
                "recommendation",
                "Committee members disagree materially on the rollout recommendation and timing.",
                f"{len(recommendation_participants)} reviewers are separated by at least two recommendation tiers on rollout timing.",
                "Recommendation polarity differs enough to alter rollout guidance.",
                conflicting_claims=claims,
                conflicting_evidence=evidence,
            )
        )
        index += 1

    for topic, cluster in assumption_clusters.items():
        claims, evidence = _collect_reasoning(review_map, cluster["participants"])
        conflicts.append(
            create_conflict(
                f"conflict-{index:03d}",
                "assumption_mismatch",
                topic,
                cluster["participants"],
                "medium",
                "assumption",
                f"Agents are using incompatible assumptions for {topic}.",
                f"Assumption topic {topic} contains incompatible values including {'; '.join(cluster['examples'])}.",
                "Different assumptions could distort committee synthesis.",
                conflicting_claims=claims,
                conflicting_evidence=evidence,
            )
        )
        index += 1

    for dimension, cluster in score_clusters.items():
        claims, evidence = _collect_reasoning(review_map, cluster["participants"])
        conflicts.append(
            create_conflict(
                f"conflict-{index:03d}",
                "score_divergence",
                dimension,
                cluster["participants"],
                "high",
                "scoring",
                f"Agent score contributions for {dimension} diverge beyond the bounded committee threshold.",
                f"Maximum score delta {cluster['max_delta']:.2f} exceeds the 1.50 threshold on {dimension}.",
                "Committee scoring could shift materially after reconciliation.",
                conflicting_claims=claims,
                conflicting_evidence=evidence,
            )
        )
        index += 1

    for dimension, cluster in completeness_clusters.items():
        claims, evidence = _collect_reasoning(review_map, cluster["participants"])
        conflicts.append(
            create_conflict(
                f"conflict-{index:03d}",
                "evidence_completeness_mismatch",
                dimension,
                cluster["participants"],
                "high",
                "evidence",
                f"Agents disagree on whether the evidence for {dimension} is complete enough to support the score.",
                f"Maximum completeness delta {cluster['max_delta']:.2f} exceeds the 0.35 threshold on {dimension}.",
                "Evidence sufficiency differs materially across reviewers.",
                conflicting_claims=claims,
                conflicting_evidence=evidence,
            )
        )
        index += 1

    for category, cluster in severity_clusters.items():
        claims, evidence = _collect_reasoning(review_map, cluster["participants"])
        conflicts.append(
            create_conflict(
                f"conflict-{index:03d}",
                "risk_severity_mismatch",
                category,
                cluster["participants"],
                "medium",
                "risk",
                f"Agents assign materially different risk severity to the {category} category.",
                f"Maximum severity delta {cluster['max_delta']} exceeds the structured threshold on {category}.",
                "Risk handling guidance differs enough to require committee attention.",
                conflicting_claims=claims,
                conflicting_evidence=evidence,
            )
        )
        index += 1

    severity_order = {"high": 3, "medium": 2, "low": 1}
    return sorted(conflicts, key=lambda conflict: (-severity_order[conflict.severity], conflict.conflict_id))


def _collect_reasoning(
    review_map: dict[str, AgentReview],
    participants: Iterable[str],
) -> tuple[list[str], list[str]]:
    claims: list[str] = []
    evidence: list[str] = []
    for agent_id in participants:
        review = review_map.get(agent_id)
        if review is None or review.reasoning is None:
            continue
        if review.reasoning.claim and review.reasoning.claim not in claims:
            claims.append(review.reasoning.claim)
        for item in review.reasoning.evidence:
            if item not in evidence:
                evidence.append(item)
    return claims, evidence
