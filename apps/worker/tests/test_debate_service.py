from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.debates import DebateAlreadyExistsError, DebateService  # noqa: E402
from orbit_api.review_runs import ReviewRunService  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.persistence import InMemoryPersistenceRepository, build_portfolio_ingestion_bundle  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"


def test_debate_service_persists_bounded_resolution_for_review_run() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    review_summary = ReviewRunService(repository=repository).start_review(canonical_portfolio.portfolio_id)
    service = DebateService(repository=repository)
    summary = service.start_debate(review_summary.run_id)

    assert summary.run_id == review_summary.run_id
    assert summary.portfolio_id == canonical_portfolio.portfolio_id
    assert summary.conflicts_considered == 5
    assert summary.score_change_required_count == 0

    detail = service.get_debate(summary.debate_id)
    assert detail is not None
    assert detail.review_run.run_id == review_summary.run_id
    assert detail.scorecard.final_recommendation == "Proceed with Conditions"
    assert detail.scorecard.weighted_composite_score == 3.61
    assert len(detail.conflicts) == 5
    assert len(detail.conflict_resolutions) == 5
    assert {event.action for event in detail.audit_events} == {
        "debate_session.completed",
        "conflict_resolution.recorded",
    }

    listed = service.list_debates(run_id=review_summary.run_id)
    assert len(listed.items) == 1
    assert listed.items[0].debate_id == summary.debate_id


def test_debate_service_rejects_duplicate_debate_for_run() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    review_summary = ReviewRunService(repository=repository).start_review(canonical_portfolio.portfolio_id)
    service = DebateService(repository=repository)
    service.start_debate(review_summary.run_id)

    try:
        service.start_debate(review_summary.run_id)
    except DebateAlreadyExistsError as exc:
        assert review_summary.run_id in str(exc)
    else:
        raise AssertionError("Expected DebateAlreadyExistsError on duplicate debate creation.")
