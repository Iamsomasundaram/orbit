from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.validation import DecisionValidationService, HumanReviewSubmission  # noqa: E402
from orbit_api.review_runs import ReviewRunService  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.persistence import InMemoryPersistenceRepository, build_portfolio_ingestion_bundle  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"


def seed_portfolio(repository: InMemoryPersistenceRepository) -> str:
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))
    return canonical_portfolio.portfolio_id


def test_human_review_submission_generates_validation_metrics() -> None:
    repository = InMemoryPersistenceRepository()
    portfolio_id = seed_portfolio(repository)
    review_summary = ReviewRunService(repository=repository).start_review(portfolio_id)

    service = DecisionValidationService(repository=repository)
    detail = service.submit_human_review(
        portfolio_id,
        HumanReviewSubmission(
            reviewer_name="Milestone 15 Reviewer",
            final_recommendation="Pilot Only",
            score=2.8,
            identified_risks=["integration complexity", "adoption friction"],
            confidence="Medium",
            review_notes="Validation baseline for decision quality tests.",
        ),
    )

    assert detail.human_review.portfolio_id == portfolio_id

    run_validation = service.get_review_run_validation(review_summary.run_id)
    assert run_validation is not None
    assert run_validation.validations
    validation = run_validation.validations[0]
    assert 0.0 <= validation.agreement_score <= 1.0
    assert validation.review_run_id == review_summary.run_id

    summary = service.get_validation_summary()
    assert summary.summary.total_validations >= 1


def test_portfolio_validation_summary_tracks_human_reviews() -> None:
    repository = InMemoryPersistenceRepository()
    portfolio_id = seed_portfolio(repository)
    ReviewRunService(repository=repository).start_review(portfolio_id)

    service = DecisionValidationService(repository=repository)
    service.submit_human_review(
        portfolio_id,
        HumanReviewSubmission(
            reviewer_name="Milestone 15 Reviewer",
            final_recommendation="Proceed with Conditions",
            score=3.4,
            identified_risks=["security controls", "integration sequencing"],
            confidence="High",
            review_notes="Second validation baseline.",
        ),
    )

    detail = service.get_portfolio_validation(portfolio_id)
    assert detail is not None
    assert detail.human_review_count == 1
    assert detail.validation_count == 1
    assert detail.reasoning_consistency is not None
