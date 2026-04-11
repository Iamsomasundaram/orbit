from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.debates import DebateService  # noqa: E402
from orbit_api.deliberations import DeliberationService  # noqa: E402
from orbit_api.review_runs import ReviewRunService  # noqa: E402
from orbit_api.review_workflow import ReviewWorkflowService  # noqa: E402
from orbit_api.resyntheses import ResynthesisService  # noqa: E402
from orbit_worker.debate import run_bounded_debate  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.persistence import InMemoryPersistenceRepository, build_debate_persistence_bundle, build_portfolio_ingestion_bundle  # noqa: E402
from orbit_worker.schemas import validate_debate_session  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"


def debate_with_forced_recheck(debate):
    payload = debate.model_dump(mode="json")
    for resolution in payload["resolutions"]:
        if resolution["topic"] != "security_and_compliance":
            continue
        resolution["outcome"] = "needs_score_revisit"
        resolution["score_change_required"] = True
        resolution["score_change_rationale"] = "Forced recheck for Milestone 11 deliberation validation."
        resolution["status"] = "needs_review"
    payload["debate_status"] = "completed_with_escalations"
    payload["executive_summary"] = "Forced score recheck for Milestone 11 deliberation validation."
    return validate_debate_session(payload)


def seed_portfolio(repository: InMemoryPersistenceRepository):
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))
    return canonical_portfolio


def test_deliberation_is_materialized_after_review_run_even_before_debate() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    deliberation_service = DeliberationService(repository=repository)
    review_service = ReviewRunService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run)

    review = review_service.start_review(canonical_portfolio.portfolio_id)
    detail = deliberation_service.get_review_run_deliberation(review.run_id)

    assert detail is not None
    assert detail.entry_count == 23
    assert len([entry for entry in detail.entries if entry.phase == "opening_statements"]) == 15
    assert len([entry for entry in detail.entries if entry.phase == "conflict_identification"]) == 5
    assert len([entry for entry in detail.entries if entry.phase == "conflict_discussion"]) == 1
    assert len([entry for entry in detail.entries if entry.phase == "moderator_synthesis"]) == 1
    assert len([entry for entry in detail.entries if entry.phase == "final_verdict"]) == 1


def test_deliberation_summary_reflects_completed_workflow_with_bounded_debate() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    deliberation_service = DeliberationService(repository=repository)
    review_service = ReviewRunService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run)
    debate_service = DebateService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run)
    resynthesis_service = ResynthesisService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run)
    workflow_service = ReviewWorkflowService(
        review_runs=review_service,
        debates=debate_service,
        resyntheses=resynthesis_service,
    )

    summary = workflow_service.start_review(canonical_portfolio.portfolio_id)
    deliberation_summary = deliberation_service.get_review_run_deliberation_summary(summary.review_run.run_id)

    assert deliberation_summary is not None
    assert deliberation_summary.final_recommendation == "Proceed with Conditions"
    assert deliberation_summary.active_artifact_source == "original"
    phase_counts = {phase.phase: phase.entry_count for phase in deliberation_summary.phase_summaries}
    assert phase_counts["opening_statements"] == 15
    assert phase_counts["conflict_identification"] == 5
    assert phase_counts["conflict_discussion"] > 1
    assert phase_counts["moderator_synthesis"] == 5
    assert phase_counts["final_verdict"] == 1


def test_deliberation_final_verdict_updates_after_resynthesized_artifact_selection() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    deliberation_service = DeliberationService(repository=repository)
    review_service = ReviewRunService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run)
    resynthesis_service = ResynthesisService(repository=repository, deliberation_refresher=deliberation_service.refresh_review_run)

    review = review_service.start_review(canonical_portfolio.portfolio_id)
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
    deliberation_service.refresh_review_run(review.run_id)

    resynthesis = resynthesis_service.start_resynthesis(forced_debate.debate_id)
    detail = deliberation_service.get_review_run_deliberation(resynthesis.run_id)

    assert detail is not None
    assert detail.artifact_selection.active_artifact_source == "resynthesized"
    assert detail.final_recommendation == "Pilot Only"
    assert detail.entries[-1].phase == "final_verdict"
    assert "resynthesized artifacts" in detail.entries[-1].statement_text
