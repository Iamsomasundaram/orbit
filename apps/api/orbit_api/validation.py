from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from orbit_worker.decision_validation import ReasoningConsistencyMetrics, compute_decision_validation, compute_reasoning_consistency
from orbit_worker.domain import RECOMMENDATION_RANK, clamp_unit, round_half_up
from orbit_worker.persistence import (
    AuditActor,
    AuditEventRecord,
    DecisionValidationConflictError,
    DecisionValidationRecord,
    HumanReviewConflictError,
    HumanReviewRecord,
    PersistenceRepository,
    PortfolioRecord,
    ReviewPersistenceBundle,
    build_decision_validation_record,
    build_human_review_record,
)
from orbit_worker.schemas import HumanReview, OrbitModel

from .history import ReviewHistoryService


class HumanReviewSubmission(OrbitModel):
    reviewer_name: str = "Human Reviewer"
    final_recommendation: str
    score: float
    identified_risks: list[str]
    confidence: Literal["Low", "Medium", "High"]
    review_notes: str


class HumanReviewDetail(OrbitModel):
    human_review: HumanReviewRecord


class HumanReviewListResponse(OrbitModel):
    items: list[HumanReviewRecord]


class DecisionValidationDetail(OrbitModel):
    validation: DecisionValidationRecord


class DecisionValidationListResponse(OrbitModel):
    items: list[DecisionValidationRecord]


class ReviewRunValidationDetail(OrbitModel):
    review_run_id: str
    portfolio_id: str
    orbit_final_recommendation: str
    orbit_weighted_composite_score: float
    human_reviews: list[HumanReviewRecord]
    validations: list[DecisionValidationRecord]
    reasoning_consistency: ReasoningConsistencyMetrics | None = None


class PortfolioValidationDetail(OrbitModel):
    portfolio: PortfolioRecord
    latest_review_run_id: str | None
    human_review_count: int
    validation_count: int
    human_reviews: list[HumanReviewRecord]
    validations: list[DecisionValidationRecord]
    reasoning_consistency: ReasoningConsistencyMetrics | None = None


class DecisionValidationSummary(OrbitModel):
    total_validations: int
    recommendation_alignment_rate: float
    average_agreement_score: float
    average_score_difference: float
    average_risk_overlap: float
    average_risk_recall: float
    average_risk_precision: float
    average_confidence_alignment: float


class DecisionValidationSummaryResponse(OrbitModel):
    summary: DecisionValidationSummary
    updated_at: datetime


class HumanReviewAlreadyExistsError(ValueError):
    pass


class DecisionValidationAlreadyExistsError(ValueError):
    pass


class ValidationNotFoundError(ValueError):
    pass


def _build_human_review_id(portfolio_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"human-{portfolio_id}-{timestamp}"


def _build_decision_validation_id(run_id: str, human_review_id: str) -> str:
    return f"validation-{run_id}-{human_review_id}"


def _audit_event_for_human_review(record: HumanReviewRecord) -> AuditEventRecord:
    return AuditEventRecord(
        event_id=f"audit-human-review-{record.human_review_id}",
        portfolio_id=record.portfolio_id,
        actor=AuditActor(actor_type="user", actor_id="human-reviewer", display_name=record.reviewer_name),
        action="human_review.submitted",
        entity_type="human_review",
        entity_id=record.human_review_id,
        event_payload={
            "final_recommendation": record.final_recommendation,
            "score": record.score,
            "confidence": record.confidence,
        },
        created_at=record.created_at,
    )


def _review_bundle_for_portfolio(repository: PersistenceRepository, portfolio_id: str) -> ReviewPersistenceBundle | None:
    bundles = repository.list_review_run_bundles(portfolio_id=portfolio_id)
    return bundles[0] if bundles else None


def _summary_from_validations(validations: list[DecisionValidationRecord]) -> DecisionValidationSummary:
    if not validations:
        return DecisionValidationSummary(
            total_validations=0,
            recommendation_alignment_rate=0.0,
            average_agreement_score=0.0,
            average_score_difference=0.0,
            average_risk_overlap=0.0,
            average_risk_recall=0.0,
            average_risk_precision=0.0,
            average_confidence_alignment=0.0,
        )

    def avg(values: list[float]) -> float:
        return round_half_up(sum(values) / len(values), 2) if values else 0.0

    alignment_rate = sum(1 for record in validations if record.recommendation_match == "match") / len(validations)

    return DecisionValidationSummary(
        total_validations=len(validations),
        recommendation_alignment_rate=clamp_unit(round_half_up(alignment_rate, 2)),
        average_agreement_score=avg([record.agreement_score for record in validations]),
        average_score_difference=avg([record.score_difference for record in validations]),
        average_risk_overlap=avg([record.risk_overlap for record in validations]),
        average_risk_recall=avg([record.risk_recall for record in validations]),
        average_risk_precision=avg([record.risk_precision for record in validations]),
        average_confidence_alignment=avg([record.confidence_alignment for record in validations]),
    )


class DecisionValidationService:
    def __init__(self, repository: PersistenceRepository) -> None:
        self._repository = repository
        self._history_service = ReviewHistoryService(repository)

    def submit_human_review(self, portfolio_id: str, submission: HumanReviewSubmission) -> HumanReviewDetail:
        portfolio_bundle = self._repository.get_portfolio_bundle(portfolio_id)
        if portfolio_bundle is None:
            raise ValidationNotFoundError(f"Portfolio '{portfolio_id}' was not found.")
        if submission.final_recommendation not in RECOMMENDATION_RANK:
            raise ValueError(f"Unsupported recommendation '{submission.final_recommendation}'.")

        human_review = HumanReview(
            human_review_id=_build_human_review_id(portfolio_id),
            portfolio_id=portfolio_id,
            reviewer_name=submission.reviewer_name,
            final_recommendation=submission.final_recommendation,
            score=submission.score,
            identified_risks=submission.identified_risks,
            confidence=submission.confidence,
            review_notes=submission.review_notes,
            submitted_at=datetime.now(timezone.utc),
        )
        record = build_human_review_record(human_review)
        audit_event = _audit_event_for_human_review(record)
        try:
            self._repository.save_human_review(record, audit_event=audit_event)
        except HumanReviewConflictError as exc:
            raise HumanReviewAlreadyExistsError(str(exc)) from exc

        review_bundle = _review_bundle_for_portfolio(self._repository, portfolio_id)
        if review_bundle is not None:
            self._ensure_validation_for_run(review_bundle, human_review)

        return HumanReviewDetail(human_review=record)

    def list_human_reviews(self, portfolio_id: str) -> HumanReviewListResponse:
        return HumanReviewListResponse(items=self._repository.list_human_reviews(portfolio_id=portfolio_id))

    def get_human_review(self, human_review_id: str) -> HumanReviewDetail | None:
        record = self._repository.get_human_review(human_review_id)
        if record is None:
            return None
        return HumanReviewDetail(human_review=record)

    def get_portfolio_validation(self, portfolio_id: str) -> PortfolioValidationDetail | None:
        portfolio_bundle = self._repository.get_portfolio_bundle(portfolio_id)
        if portfolio_bundle is None:
            return None

        review_bundle = _review_bundle_for_portfolio(self._repository, portfolio_id)
        validations: list[DecisionValidationRecord] = []
        consistency: ReasoningConsistencyMetrics | None = None
        human_reviews = self._repository.list_human_reviews(portfolio_id=portfolio_id)
        if review_bundle is not None:
            for human_review in human_reviews:
                validation = self._ensure_validation_for_run(review_bundle, human_review.review_payload)
                if validation is not None:
                    validations.append(validation)
            validations = sorted(validations, key=lambda record: record.created_at, reverse=True)
            consistency = compute_reasoning_consistency(
                [record.review_payload for record in review_bundle.agent_reviews],
                len(review_bundle.conflicts),
            )

        return PortfolioValidationDetail(
            portfolio=portfolio_bundle.portfolio,
            latest_review_run_id=portfolio_bundle.portfolio.latest_review_run_id,
            human_review_count=len(human_reviews),
            validation_count=len(validations),
            human_reviews=human_reviews,
            validations=validations,
            reasoning_consistency=consistency,
        )

    def get_review_run_validation(self, run_id: str) -> ReviewRunValidationDetail | None:
        review_bundle = self._repository.get_review_run_bundle(run_id)
        if review_bundle is None:
            return None

        human_reviews = self._repository.list_human_reviews(portfolio_id=review_bundle.portfolio.portfolio_id)
        validations: list[DecisionValidationRecord] = []
        for human_review in human_reviews:
            validation = self._ensure_validation_for_run(review_bundle, human_review.review_payload)
            if validation is not None:
                validations.append(validation)
        validations = sorted(validations, key=lambda record: record.created_at, reverse=True)

        artifact_detail = self._history_service.get_review_run_artifacts(run_id)
        if artifact_detail is None:
            return None

        consistency = compute_reasoning_consistency(
            [record.review_payload for record in review_bundle.agent_reviews],
            len(review_bundle.conflicts),
        )

        return ReviewRunValidationDetail(
            review_run_id=review_bundle.review_run.run_id,
            portfolio_id=review_bundle.portfolio.portfolio_id,
            orbit_final_recommendation=artifact_detail.active_scorecard.final_recommendation,
            orbit_weighted_composite_score=artifact_detail.active_scorecard.weighted_composite_score,
            human_reviews=human_reviews,
            validations=validations,
            reasoning_consistency=consistency,
        )

    def get_validation_summary(self) -> DecisionValidationSummaryResponse:
        validations = self._repository.list_decision_validations()
        return DecisionValidationSummaryResponse(
            summary=_summary_from_validations(validations),
            updated_at=datetime.now(timezone.utc),
        )

    def _ensure_validation_for_run(
        self,
        review_bundle: ReviewPersistenceBundle,
        human_review: HumanReview,
    ) -> DecisionValidationRecord | None:
        artifact_detail = self._history_service.get_review_run_artifacts(review_bundle.review_run.run_id)
        if artifact_detail is None:
            return None

        validation_id = _build_decision_validation_id(review_bundle.review_run.run_id, human_review.human_review_id)
        existing = self._repository.get_decision_validation(validation_id)
        if existing is not None:
            return existing

        decision_validation = compute_decision_validation(
            orbit_recommendation=artifact_detail.active_scorecard.final_recommendation,
            orbit_score=artifact_detail.active_scorecard.weighted_composite_score,
            agent_reviews=[record.review_payload for record in review_bundle.agent_reviews],
            human_review=human_review,
            validated_at=datetime.now(timezone.utc),
        )
        decision_validation = decision_validation.model_copy(
            update={
                "decision_validation_id": validation_id,
                "review_run_id": review_bundle.review_run.run_id,
            }
        )
        record = build_decision_validation_record(decision_validation)

        try:
            self._repository.save_decision_validation(record)
        except DecisionValidationConflictError as exc:
            raise DecisionValidationAlreadyExistsError(str(exc)) from exc
        return record
