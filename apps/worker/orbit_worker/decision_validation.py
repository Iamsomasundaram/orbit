from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev, pvariance
from typing import Iterable

from .domain import RECOMMENDATION_RANK, clamp_unit, get_recommendation_distance, round_half_up
from .schemas import AgentReview, DecisionValidation, HumanReview, OrbitModel


class DecisionValidationMetrics(OrbitModel):
    recommendation_match: str
    score_difference: float
    risk_overlap: float
    risk_recall: float
    risk_precision: float
    confidence_alignment: float
    agreement_score: float


class ReasoningConsistencyMetrics(OrbitModel):
    agent_claim_overlap: float
    confidence_dispersion: float
    conflict_frequency: float
    score_variance: float
    dominant_claims: list[str]


CONFIDENCE_SCALE = {
    "Low": 0.0,
    "Medium": 0.5,
    "High": 1.0,
}


def _normalize_tokens(items: Iterable[str]) -> list[str]:
    return [item.strip().casefold() for item in items if isinstance(item, str) and item.strip()]


def _risk_overlap(orbit_risks: Iterable[str], human_risks: Iterable[str]) -> tuple[float, float, float]:
    orbit_set = set(_normalize_tokens(orbit_risks))
    human_set = set(_normalize_tokens(human_risks))
    if not orbit_set and not human_set:
        return 0.0, 0.0, 0.0
    overlap = orbit_set & human_set
    union = orbit_set | human_set
    risk_overlap = len(overlap) / len(union) if union else 0.0
    risk_recall = len(overlap) / len(human_set) if human_set else 0.0
    risk_precision = len(overlap) / len(orbit_set) if orbit_set else 0.0
    return (
        clamp_unit(round_half_up(risk_overlap, 2)),
        clamp_unit(round_half_up(risk_recall, 2)),
        clamp_unit(round_half_up(risk_precision, 2)),
    )


def _recommendation_match(left: str, right: str) -> tuple[str, float]:
    if left not in RECOMMENDATION_RANK or right not in RECOMMENDATION_RANK:
        return "mismatch", 0.0
    distance = get_recommendation_distance(left, right)
    if distance == 0:
        return "match", 1.0
    if distance == 1:
        return "partial", 0.5
    return "mismatch", 0.0


def _confidence_to_unit(value: str | None) -> float:
    if not value:
        return 0.5
    return CONFIDENCE_SCALE.get(value, 0.5)


def _score_alignment(score_difference: float) -> float:
    return clamp_unit(1.0 - min(score_difference / 4.0, 1.0))


def _aggregate_orbit_risks(agent_reviews: Iterable[AgentReview]) -> list[str]:
    risks: list[str] = []
    for review in agent_reviews:
        for finding in review.findings:
            risks.append(finding.title)
    return risks


def _orbit_confidence(agent_reviews: Iterable[AgentReview]) -> float:
    values = [
        _confidence_to_unit(review.reasoning.confidence)
        for review in agent_reviews
        if review.reasoning is not None
    ]
    if not values:
        return 0.5
    return clamp_unit(round_half_up(mean(values), 2))


def compute_decision_validation(
    *,
    orbit_recommendation: str,
    orbit_score: float,
    agent_reviews: Iterable[AgentReview],
    human_review: HumanReview,
    validated_at,
) -> DecisionValidation:
    review_items = list(agent_reviews)
    recommendation_match, match_score = _recommendation_match(orbit_recommendation, human_review.final_recommendation)
    score_difference = round_half_up(abs(orbit_score - human_review.score), 2)
    score_alignment = _score_alignment(score_difference)
    risk_overlap, risk_recall, risk_precision = _risk_overlap(
        _aggregate_orbit_risks(review_items),
        human_review.identified_risks,
    )
    confidence_alignment = clamp_unit(
        round_half_up(
            1.0 - abs(_orbit_confidence(review_items) - _confidence_to_unit(human_review.confidence)),
            2,
        )
    )
    agreement_score = clamp_unit(
        round_half_up(
            (match_score * 0.5) + (score_alignment * 0.3) + (risk_overlap * 0.2),
            2,
        )
    )

    return DecisionValidation(
        decision_validation_id="",
        portfolio_id=human_review.portfolio_id,
        review_run_id="",
        human_review_id=human_review.human_review_id,
        orbit_recommendation=orbit_recommendation,
        orbit_score=orbit_score,
        human_recommendation=human_review.final_recommendation,
        human_score=human_review.score,
        recommendation_match=recommendation_match,
        score_difference=score_difference,
        risk_overlap=risk_overlap,
        risk_recall=risk_recall,
        risk_precision=risk_precision,
        confidence_alignment=confidence_alignment,
        agreement_score=agreement_score,
        validated_at=validated_at,
    )


def compute_reasoning_consistency(
    agent_reviews: Iterable[AgentReview],
    conflict_count: int,
) -> ReasoningConsistencyMetrics:
    review_items = list(agent_reviews)
    claims = [
        review.reasoning.claim.strip()
        for review in review_items
        if review.reasoning is not None and review.reasoning.claim.strip()
    ]
    normalized_claims = _normalize_tokens(claims)
    total_claims = len(normalized_claims)
    unique_claims = len(set(normalized_claims))
    overlap_ratio = 1.0 - (unique_claims / total_claims) if total_claims else 0.0

    confidence_values = [
        _confidence_to_unit(review.reasoning.confidence)
        for review in review_items
        if review.reasoning is not None
    ]
    confidence_dispersion = pstdev(confidence_values) if len(confidence_values) > 1 else 0.0

    score_samples = []
    for review in review_items:
        if not review.dimension_scores:
            continue
        score_samples.append(mean(score.score for score in review.dimension_scores))
    score_variance = pvariance(score_samples) if len(score_samples) > 1 else 0.0

    dominant_claims = [
        claim for claim, _ in Counter(normalized_claims).most_common(3)
    ]

    agent_count = max(len(review_items), 1)
    conflict_frequency = conflict_count / agent_count

    return ReasoningConsistencyMetrics(
        agent_claim_overlap=clamp_unit(round_half_up(overlap_ratio, 2)),
        confidence_dispersion=clamp_unit(round_half_up(confidence_dispersion, 2)),
        conflict_frequency=clamp_unit(round_half_up(conflict_frequency, 2)),
        score_variance=round_half_up(score_variance, 2),
        dominant_claims=dominant_claims,
    )
