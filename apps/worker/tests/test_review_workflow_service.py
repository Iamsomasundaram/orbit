from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.debates import DebateService, DebateSummary  # noqa: E402
from orbit_api.review_runs import ReviewRunService, ReviewRunSummary  # noqa: E402
from orbit_api.review_workflow import ReviewWorkflowService  # noqa: E402
from orbit_api.resyntheses import ResynthesisService, ResynthesisSummary  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.persistence import InMemoryPersistenceRepository, build_portfolio_ingestion_bundle  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"


def test_review_workflow_runs_review_then_debate_without_resynthesis_when_no_recheck_is_needed() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    service = ReviewWorkflowService(
        review_runs=ReviewRunService(repository=repository),
        debates=DebateService(repository=repository),
        resyntheses=ResynthesisService(repository=repository),
    )
    summary = service.start_review(canonical_portfolio.portfolio_id)

    assert summary.review_run.portfolio_id == canonical_portfolio.portfolio_id
    assert summary.review_run.review_status == "completed"
    assert summary.review_run.conflict_count == 5
    assert summary.debate is not None
    assert summary.debate.run_id == summary.review_run.run_id
    assert summary.debate.conflicts_considered == 5
    assert summary.debate.score_change_required_count == 0
    assert summary.resynthesis is None

    debates = repository.list_debate_bundles(run_id=summary.review_run.run_id)
    assert len(debates) == 1
    assert debates[0].debate_session.conflicts_considered == 5
    assert repository.list_resynthesis_bundles(debate_id=debates[0].debate_session.debate_id) == []


def test_review_workflow_triggers_resynthesis_when_debate_requests_recheck() -> None:
    review_run = ReviewRunSummary(
        run_id="review-demo-001",
        portfolio_id="portfolio-demo-001",
        review_status="completed",
        final_recommendation="Proceed with Conditions",
        weighted_composite_score=3.61,
        agent_review_count=15,
        conflict_count=5,
        created_at="2026-04-10T00:00:00Z",
        completed_at="2026-04-10T00:00:01Z",
    )
    debate = DebateSummary(
        debate_id="debate-review-demo-001",
        run_id="review-demo-001",
        portfolio_id="portfolio-demo-001",
        debate_status="completed_with_escalations",
        conflicts_considered=5,
        score_change_required_count=1,
        created_at="2026-04-10T00:00:02Z",
    )
    captured: list[str] = []

    class StubReviewRunService:
        def start_review(self, portfolio_id: str):
            assert portfolio_id == "portfolio-demo-001"
            return review_run

    class StubDebateService:
        def start_debate(self, run_id: str):
            assert run_id == review_run.run_id
            return debate

    class StubResynthesisService:
        def start_resynthesis(self, debate_id: str):
            captured.append(debate_id)
            return ResynthesisSummary(
                resynthesis_id=f"resynthesis-{debate_id}",
                debate_id=debate_id,
                run_id=review_run.run_id,
                portfolio_id=review_run.portfolio_id,
                resynthesis_status="completed_with_recheck",
                score_change_required_count=1,
                active_artifact_source="resynthesized",
                created_at="2026-04-10T00:00:03Z",
            )

    service = ReviewWorkflowService(
        review_runs=StubReviewRunService(),
        debates=StubDebateService(),
        resyntheses=StubResynthesisService(),
    )

    summary = service.start_review("portfolio-demo-001")

    assert summary.review_run is review_run
    assert summary.debate is debate
    assert summary.resynthesis is not None
    assert summary.resynthesis.resynthesis_id == "resynthesis-debate-review-demo-001"
    assert captured == [debate.debate_id]
