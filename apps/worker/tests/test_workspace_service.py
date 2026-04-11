from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.resyntheses import ResynthesisService  # noqa: E402
from orbit_api.review_runs import ReviewRunService  # noqa: E402
from orbit_api.workspace import PortfolioWorkspaceService  # noqa: E402
from orbit_worker.debate import run_bounded_debate  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.persistence import (  # noqa: E402
    InMemoryPersistenceRepository,
    build_debate_persistence_bundle,
    build_portfolio_ingestion_bundle,
)
from orbit_worker.schemas import validate_debate_session  # noqa: E402

STRONG_INPUT = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"
PROMISING_INPUT = ROOT / "tests" / "fixtures" / "source-documents" / "traceforge-thin-slice.md"
WEAK_INPUT = ROOT / "tests" / "fixtures" / "source-documents" / "moodmesh-thin-slice.md"


def seed_portfolio(repository: InMemoryPersistenceRepository, source_path: Path) -> str:
    canonical_portfolio = ingest_portfolio_document(source_path)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))
    return canonical_portfolio.portfolio_id


def debate_with_forced_recheck(debate):
    payload = debate.model_dump(mode="json")
    for resolution in payload["resolutions"]:
        if resolution["topic"] != "security_and_compliance":
            continue
        resolution["outcome"] = "needs_score_revisit"
        resolution["score_change_required"] = True
        resolution["score_change_rationale"] = "Forced recheck for Milestone 9 workspace validation."
        resolution["status"] = "needs_review"
    payload["debate_status"] = "completed_with_escalations"
    payload["executive_summary"] = "Forced score recheck for Milestone 9 workspace validation."
    return validate_debate_session(payload)


def test_workspace_summary_and_ranking_sort_multiple_portfolios() -> None:
    repository = InMemoryPersistenceRepository()
    strong_portfolio_id = seed_portfolio(repository, STRONG_INPUT)
    promising_portfolio_id = seed_portfolio(repository, PROMISING_INPUT)
    weak_portfolio_id = seed_portfolio(repository, WEAK_INPUT)
    review_service = ReviewRunService(repository=repository)
    workspace_service = PortfolioWorkspaceService(repository=repository)

    review_service.start_review(strong_portfolio_id)
    review_service.start_review(promising_portfolio_id)
    review_service.start_review(weak_portfolio_id)

    summary = workspace_service.list_summary(sort_by="weighted_composite_score", direction="desc")
    assert [item.portfolio.portfolio_id for item in summary.items[:3]] == [
        strong_portfolio_id,
        promising_portfolio_id,
        weak_portfolio_id,
    ]
    assert summary.items[0].latest_final_recommendation == "Proceed with Conditions"
    assert summary.items[1].latest_final_recommendation == "Pilot Only"
    assert summary.items[0].agent_review_count == 15
    assert summary.items[0].conflict_count == 5

    ranking = workspace_service.rank(sort_by="weighted_composite_score", direction="desc")
    assert ranking.items[0].rank == 1
    assert ranking.items[0].portfolio.portfolio_id == strong_portfolio_id
    assert ranking.items[1].portfolio.portfolio_id == promising_portfolio_id
    assert ranking.items[2].portfolio.portfolio_id == weak_portfolio_id


def test_workspace_compare_preserves_requested_order_and_lineage() -> None:
    repository = InMemoryPersistenceRepository()
    strong_portfolio_id = seed_portfolio(repository, STRONG_INPUT)
    weak_portfolio_id = seed_portfolio(repository, WEAK_INPUT)
    review_service = ReviewRunService(repository=repository)
    workspace_service = PortfolioWorkspaceService(repository=repository)

    review_service.start_review(strong_portfolio_id)
    review_service.start_review(weak_portfolio_id)

    comparison = workspace_service.compare([weak_portfolio_id, strong_portfolio_id])

    assert comparison.requested_portfolio_ids == [weak_portfolio_id, strong_portfolio_id]
    assert [item.portfolio.portfolio_id for item in comparison.items] == [
        weak_portfolio_id,
        strong_portfolio_id,
    ]
    assert comparison.items[0].latest_lineage is not None
    assert comparison.items[0].latest_lineage.review_run_id.startswith(f"review-{weak_portfolio_id}-")
    assert comparison.items[0].agent_review_count == 15
    assert comparison.items[1].conflict_count == 5


def test_workspace_uses_latest_resynthesized_artifact_when_present() -> None:
    repository = InMemoryPersistenceRepository()
    portfolio_id = seed_portfolio(repository, STRONG_INPUT)
    review_service = ReviewRunService(repository=repository)
    resynthesis_service = ResynthesisService(repository=repository)
    workspace_service = PortfolioWorkspaceService(repository=repository)

    review = review_service.start_review(portfolio_id)
    review_bundle = repository.get_review_run_bundle(review.run_id)
    assert review_bundle is not None

    forced_debate = debate_with_forced_recheck(
        run_bounded_debate(
            run_id=review_bundle.review_run.run_id,
            portfolio_id=review_bundle.portfolio.portfolio_id,
            conflicts=[record.conflict_payload for record in review_bundle.conflicts],
            agent_reviews=[record.review_payload for record in review_bundle.agent_reviews],
            debate_id=f"debate-{review_bundle.review_run.run_id}",
        )
    )
    repository.save_debate_bundle(
        build_debate_persistence_bundle(
            review_bundle.portfolio,
            review_bundle.review_run,
            forced_debate,
        )
    )
    resynthesis = resynthesis_service.start_resynthesis(forced_debate.debate_id)

    comparison = workspace_service.compare([portfolio_id])
    entry = comparison.items[0]

    assert entry.active_artifact_source == "resynthesized"
    assert entry.score_change_required_count == 1
    assert entry.latest_lineage is not None
    assert entry.latest_lineage.debate_id == forced_debate.debate_id
    assert entry.latest_lineage.resynthesis_id == resynthesis.resynthesis_id
    assert entry.latest_final_recommendation == "Pilot Only"
