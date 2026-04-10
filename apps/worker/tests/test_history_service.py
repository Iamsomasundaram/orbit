from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.debates import DebateService  # noqa: E402
from orbit_api.history import ReviewHistoryService  # noqa: E402
from orbit_api.resyntheses import ResynthesisService  # noqa: E402
from orbit_api.review_runs import ReviewRunService  # noqa: E402
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
        resolution["score_change_rationale"] = "Forced recheck for Milestone 7 lineage validation."
        resolution["status"] = "needs_review"
    payload["debate_status"] = "completed_with_escalations"
    payload["executive_summary"] = "Forced score recheck for Milestone 7 lineage validation."
    return validate_debate_session(payload)


def seed_portfolio(repository: InMemoryPersistenceRepository):
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))
    return canonical_portfolio


def test_portfolio_history_tracks_review_lineage_and_active_artifact_state() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    review_service = ReviewRunService(repository=repository)
    resynthesis_service = ResynthesisService(repository=repository)
    history_service = ReviewHistoryService(repository=repository)

    first_review = review_service.start_review(canonical_portfolio.portfolio_id)
    second_review = review_service.start_review(canonical_portfolio.portfolio_id)
    second_bundle = repository.get_review_run_bundle(second_review.run_id)
    assert second_bundle is not None

    forced_debate = debate_with_forced_recheck(
        run_bounded_debate(
            run_id=second_bundle.review_run.run_id,
            portfolio_id=second_bundle.portfolio.portfolio_id,
            conflicts=[record.conflict_payload for record in second_bundle.conflicts],
            agent_reviews=[record.review_payload for record in second_bundle.agent_reviews],
            debate_id=f"debate-{second_bundle.review_run.run_id}",
        )
    )
    repository.save_debate_bundle(
        build_debate_persistence_bundle(
            second_bundle.portfolio,
            second_bundle.review_run,
            forced_debate,
        )
    )
    resynthesis_service.start_resynthesis(forced_debate.debate_id)

    history = history_service.get_portfolio_history(canonical_portfolio.portfolio_id)
    assert history is not None
    assert history.review_run_count == 2
    assert history.debate_count == 1
    assert history.resynthesis_count == 1
    assert history.latest_review_run_id == second_review.run_id

    latest_item = history.items[0]
    assert latest_item.lineage.review_run_id == second_review.run_id
    assert latest_item.lineage.debate_id == forced_debate.debate_id
    assert latest_item.resynthesis is not None
    assert latest_item.artifact_selection.active_artifact_source == "resynthesized"
    assert latest_item.active_final_recommendation == "Pilot Only"

    earliest_item = history.items[1]
    assert earliest_item.review_run.run_id == first_review.run_id
    assert earliest_item.debate is None
    assert earliest_item.resynthesis is None
    assert earliest_item.artifact_selection.active_artifact_source == "original"
    assert earliest_item.active_final_recommendation == "Proceed with Conditions"
    assert {
        event.action
        for event in history.audit_events
    } >= {
        "portfolio.registered",
        "canonical_portfolio.materialized",
        "review_run.completed",
        "debate_session.completed",
        "resynthesis.completed",
    }


def test_review_run_artifacts_show_original_state_before_follow_up_sessions() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    review_service = ReviewRunService(repository=repository)
    history_service = ReviewHistoryService(repository=repository)

    review = review_service.start_review(canonical_portfolio.portfolio_id)
    detail = history_service.get_review_run_artifacts(review.run_id)

    assert detail is not None
    assert detail.anchor_type == "review_run"
    assert detail.lineage.review_run_id == review.run_id
    assert detail.debate_session is None
    assert detail.resynthesis_session is None
    assert detail.agent_review_count == 15
    assert detail.conflict_count == 5
    assert detail.artifact_selection.active_artifact_source == "original"
    assert detail.active_scorecard.final_recommendation == "Proceed with Conditions"
    assert detail.active_scorecard.weighted_composite_score == 3.61
    assert detail.resynthesized_scorecard is None
    assert detail.resynthesized_committee_report is None
    assert {event.action for event in detail.review_audit_events} == {
        "review_run.completed",
        "committee_report.materialized",
    }


def test_debate_artifacts_link_review_and_pending_resynthesis_state() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    review_service = ReviewRunService(repository=repository)
    debate_service = DebateService(repository=repository)
    history_service = ReviewHistoryService(repository=repository)

    review = review_service.start_review(canonical_portfolio.portfolio_id)
    debate = debate_service.start_debate(review.run_id)
    detail = history_service.get_debate_artifacts(debate.debate_id)

    assert detail is not None
    assert detail.anchor_type == "debate"
    assert detail.lineage.review_run_id == review.run_id
    assert detail.lineage.debate_id == debate.debate_id
    assert detail.lineage.resynthesis_id is None
    assert detail.agent_review_count == 15
    assert detail.conflict_count == 5
    assert detail.artifact_selection.active_artifact_source == "original"
    assert detail.resynthesis_session is None
    assert detail.resynthesized_scorecard is None
    assert len(detail.conflict_resolutions) == 5
    assert {event.action for event in detail.debate_audit_events} == {
        "debate_session.completed",
        "conflict_resolution.recorded",
    }


def test_resynthesis_artifacts_preserve_original_active_state_when_no_recheck_is_required() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    review_service = ReviewRunService(repository=repository)
    debate_service = DebateService(repository=repository)
    resynthesis_service = ResynthesisService(repository=repository)
    history_service = ReviewHistoryService(repository=repository)

    review = review_service.start_review(canonical_portfolio.portfolio_id)
    debate = debate_service.start_debate(review.run_id)
    resynthesis = resynthesis_service.start_resynthesis(debate.debate_id)
    detail = history_service.get_resynthesis_artifacts(resynthesis.resynthesis_id)

    assert detail is not None
    assert detail.anchor_type == "resynthesis"
    assert detail.lineage.review_run_id == review.run_id
    assert detail.lineage.debate_id == debate.debate_id
    assert detail.lineage.resynthesis_id == resynthesis.resynthesis_id
    assert detail.artifact_selection.active_artifact_source == "original"
    assert detail.active_scorecard.final_recommendation == "Proceed with Conditions"
    assert detail.resynthesized_scorecard is None
    assert detail.resynthesized_committee_report is None
    assert {event.action for event in detail.resynthesis_audit_events} == {"resynthesis.completed"}


def test_resynthesis_artifacts_switch_active_lineage_when_recheck_is_required() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = seed_portfolio(repository)
    review_service = ReviewRunService(repository=repository)
    resynthesis_service = ResynthesisService(repository=repository)
    history_service = ReviewHistoryService(repository=repository)

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

    resynthesis = resynthesis_service.start_resynthesis(forced_debate.debate_id)
    detail = history_service.get_resynthesis_artifacts(resynthesis.resynthesis_id)

    assert detail is not None
    assert detail.anchor_type == "resynthesis"
    assert detail.artifact_selection.active_artifact_source == "resynthesized"
    assert detail.resynthesized_scorecard is not None
    assert detail.resynthesized_committee_report is not None
    assert detail.active_scorecard.final_recommendation == "Pilot Only"
    assert {event.action for event in detail.resynthesis_audit_events} == {
        "resynthesis.completed",
        "scorecard.rechecked",
        "committee_report.resynthesized",
    }
