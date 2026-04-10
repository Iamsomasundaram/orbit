from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.review_runs import ReviewRunService  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.persistence import InMemoryPersistenceRepository, build_portfolio_ingestion_bundle  # noqa: E402
from orbit_worker.runner import run_review_pipeline, run_review_pipeline_for_portfolio  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"


def test_review_pipeline_for_portfolio_matches_path_based_execution() -> None:
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)

    path_result = run_review_pipeline(str(INPUT_PATH))
    canonical_result = run_review_pipeline_for_portfolio(
        canonical_portfolio,
        run_id=path_result["run_id"],
    )

    assert canonical_result["canonical_portfolio"] == path_result["canonical_portfolio"]
    assert canonical_result["agent_reviews"] == path_result["agent_reviews"]
    assert canonical_result["conflicts"] == path_result["conflicts"]
    assert canonical_result["scorecard"] == path_result["scorecard"]
    assert canonical_result["committee_report"] == path_result["committee_report"]


def test_review_run_service_persists_review_bundle_from_stored_canonical_portfolio() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    service = ReviewRunService(repository=repository)
    summary = service.start_review(canonical_portfolio.portfolio_id)

    assert summary.portfolio_id == canonical_portfolio.portfolio_id
    assert summary.review_status == "completed"
    assert summary.final_recommendation == "Proceed with Conditions"
    assert summary.weighted_composite_score == 3.61
    assert summary.agent_review_count == 15
    assert summary.conflict_count == 5

    detail = service.get_review_run(summary.run_id)
    assert detail is not None
    assert detail.review_run.run_id == summary.run_id
    assert detail.scorecard.final_recommendation == "Proceed with Conditions"
    assert len(detail.agent_reviews) == 15
    assert len(detail.conflicts) == 5

    listed = service.list_review_runs(portfolio_id=canonical_portfolio.portfolio_id)
    assert len(listed.items) == 1
    assert listed.items[0].run_id == summary.run_id
