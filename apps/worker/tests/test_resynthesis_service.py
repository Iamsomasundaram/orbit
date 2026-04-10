from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.debates import DebateService  # noqa: E402
from orbit_api.resyntheses import ResynthesisAlreadyExistsError, ResynthesisService  # noqa: E402
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
        resolution["score_change_rationale"] = "Forced recheck for bounded Milestone 6 service validation."
        resolution["status"] = "needs_review"
    payload["debate_status"] = "completed_with_escalations"
    payload["executive_summary"] = "Forced score recheck for Milestone 6 service validation."
    return validate_debate_session(payload)


def test_resynthesis_service_reuses_original_artifacts_when_no_recheck_is_required() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    review_summary = ReviewRunService(repository=repository).start_review(canonical_portfolio.portfolio_id)
    debate_summary = DebateService(repository=repository).start_debate(review_summary.run_id)
    service = ResynthesisService(repository=repository)
    summary = service.start_resynthesis(debate_summary.debate_id)

    assert summary.resynthesis_status == "completed_without_changes"
    assert summary.score_change_required_count == 0
    assert summary.active_artifact_source == "original"

    detail = service.get_resynthesis(summary.resynthesis_id)
    assert detail is not None
    assert detail.resynthesized_scorecard is None
    assert detail.resynthesized_committee_report is None
    assert detail.active_scorecard.final_recommendation == "Proceed with Conditions"
    assert detail.active_scorecard.weighted_composite_score == 3.61
    assert detail.active_committee_report.markdown == detail.original_committee_report.markdown
    assert {event.action for event in detail.audit_events} == {"resynthesis.completed"}


def test_resynthesis_service_persists_rechecked_artifacts_when_resolution_requires_it() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    review_summary = ReviewRunService(repository=repository).start_review(canonical_portfolio.portfolio_id)
    review_bundle = repository.get_review_run_bundle(review_summary.run_id)
    assert review_bundle is not None

    debate = debate_with_forced_recheck(
        run_bounded_debate(
            run_id=review_bundle.review_run.run_id,
            portfolio_id=review_bundle.portfolio.portfolio_id,
            conflicts=[record.conflict_payload for record in review_bundle.conflicts],
            agent_reviews=[record.review_payload for record in review_bundle.agent_reviews],
            debate_id=f"debate-{review_bundle.review_run.run_id}",
        )
    )
    repository.save_debate_bundle(build_debate_persistence_bundle(review_bundle.portfolio, review_bundle.review_run, debate))

    service = ResynthesisService(repository=repository)
    summary = service.start_resynthesis(debate.debate_id)

    assert summary.resynthesis_status == "completed_with_recheck"
    assert summary.score_change_required_count == 1
    assert summary.active_artifact_source == "resynthesized"

    detail = service.get_resynthesis(summary.resynthesis_id)
    assert detail is not None
    assert detail.resynthesized_scorecard is not None
    assert detail.resynthesized_committee_report is not None
    assert detail.original_scorecard.final_recommendation == "Proceed with Conditions"
    assert detail.active_scorecard.final_recommendation == "Pilot Only"
    assert detail.active_scorecard.weighted_composite_score < detail.original_scorecard.weighted_composite_score
    assert "Normalize risk handling expectations for security_and_compliance before broader rollout." in detail.active_scorecard.scorecard_payload.conditions
    assert {event.action for event in detail.audit_events} == {
        "resynthesis.completed",
        "scorecard.rechecked",
        "committee_report.resynthesized",
    }


def test_resynthesis_service_rejects_duplicate_resynthesis_for_debate() -> None:
    repository = InMemoryPersistenceRepository()
    canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
    repository.save_portfolio_bundle(build_portfolio_ingestion_bundle(canonical_portfolio))

    review_summary = ReviewRunService(repository=repository).start_review(canonical_portfolio.portfolio_id)
    debate_summary = DebateService(repository=repository).start_debate(review_summary.run_id)
    service = ResynthesisService(repository=repository)
    service.start_resynthesis(debate_summary.debate_id)

    try:
        service.start_resynthesis(debate_summary.debate_id)
    except ResynthesisAlreadyExistsError as exc:
        assert debate_summary.debate_id in str(exc)
    else:
        raise AssertionError("Expected ResynthesisAlreadyExistsError on duplicate re-synthesis creation.")
