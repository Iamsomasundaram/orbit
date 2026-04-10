from __future__ import annotations

from pathlib import Path

from orbit_worker.persistence import (
    PERSISTENCE_SCHEMA_VERSION,
    InMemoryPersistenceRepository,
    build_debate_persistence_bundle,
    build_portfolio_ingestion_bundle,
    build_review_persistence_bundle,
    bundle_to_table_rows,
    debate_bundle_to_table_rows,
    get_persistence_schema_catalog,
    ingestion_bundle_to_table_rows,
    render_postgres_ddl,
)
from orbit_worker.debate import run_bounded_debate
from orbit_worker.runner import run_review_pipeline

ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"
REVIEW_EXPECTED_TABLES = {
    "portfolios",
    "source_documents",
    "canonical_portfolios",
    "review_runs",
    "agent_reviews",
    "conflicts",
    "scorecards",
    "committee_reports",
    "audit_events",
}
DEBATE_EXPECTED_TABLES = {"debate_sessions", "conflict_resolutions", "audit_events"}
CATALOG_EXPECTED_TABLES = REVIEW_EXPECTED_TABLES | {"debate_sessions", "conflict_resolutions"}


def test_portfolio_ingestion_bundle_captures_canonical_submission_state() -> None:
    result = run_review_pipeline(str(INPUT_PATH))
    bundle = build_portfolio_ingestion_bundle(result["canonical_portfolio"])

    assert bundle.schema_version == PERSISTENCE_SCHEMA_VERSION
    assert bundle.portfolio.portfolio_status == "canonicalized"
    assert bundle.portfolio.latest_review_run_id is None
    assert bundle.canonical_portfolio.portfolio_id == result["canonical_portfolio"].portfolio_id
    assert len(bundle.source_documents) == 1
    assert {event.action for event in bundle.audit_events} == {
        "portfolio.registered",
        "canonical_portfolio.materialized",
    }

    rows = ingestion_bundle_to_table_rows(bundle)
    assert set(rows) == {"portfolios", "source_documents", "canonical_portfolios", "audit_events"}
    assert rows["canonical_portfolios"][0]["portfolio_id"] == result["canonical_portfolio"].portfolio_id


def test_review_persistence_bundle_captures_all_m2_artifacts() -> None:
    result = run_review_pipeline(str(INPUT_PATH))
    bundle = build_review_persistence_bundle(
        result["run_id"],
        result["canonical_portfolio"],
        result["agent_reviews"],
        result["conflicts"],
        result["scorecard"],
        result["committee_report"],
    )

    assert bundle.schema_version == PERSISTENCE_SCHEMA_VERSION
    assert bundle.portfolio.latest_review_run_id == result["run_id"]
    assert bundle.canonical_portfolio.portfolio_id == result["canonical_portfolio"].portfolio_id
    assert len(bundle.source_documents) == len(result["canonical_portfolio"].source_documents)
    assert len(bundle.agent_reviews) == 15
    assert len(bundle.conflicts) >= 1
    assert bundle.scorecard.final_recommendation == "Proceed with Conditions"
    assert bundle.scorecard.weighted_composite_score == 3.61
    assert bundle.committee_report.markdown == result["committee_report"].markdown

    rows = bundle_to_table_rows(bundle)
    assert set(rows) == REVIEW_EXPECTED_TABLES
    assert rows["committee_reports"][0]["markdown"] == result["committee_report"].markdown
    assert rows["scorecards"][0]["weighted_composite_score"] == 3.61


def test_debate_persistence_bundle_captures_bounded_resolution_artifacts() -> None:
    result = run_review_pipeline(str(INPUT_PATH))
    review_bundle = build_review_persistence_bundle(
        result["run_id"],
        result["canonical_portfolio"],
        result["agent_reviews"],
        result["conflicts"],
        result["scorecard"],
        result["committee_report"],
    )
    debate = run_bounded_debate(
        run_id=review_bundle.review_run.run_id,
        portfolio_id=review_bundle.portfolio.portfolio_id,
        conflicts=[record.conflict_payload for record in review_bundle.conflicts],
        agent_reviews=[record.review_payload for record in review_bundle.agent_reviews],
        debate_id=f"debate-{review_bundle.review_run.run_id}",
    )
    bundle = build_debate_persistence_bundle(review_bundle.portfolio, review_bundle.review_run, debate)

    assert bundle.schema_version == PERSISTENCE_SCHEMA_VERSION
    assert bundle.debate_session.conflicts_considered == len(result["conflicts"])
    assert len(bundle.conflict_resolutions) == len(result["conflicts"])
    assert bundle.debate_session.max_rounds == 2

    rows = debate_bundle_to_table_rows(bundle)
    assert set(rows) == DEBATE_EXPECTED_TABLES
    assert rows["debate_sessions"][0]["debate_id"] == f"debate-{review_bundle.review_run.run_id}"
    assert len(rows["conflict_resolutions"]) == len(result["conflicts"])


def test_in_memory_repository_round_trip_and_audit_listing() -> None:
    result = run_review_pipeline(str(INPUT_PATH))
    review_bundle = build_review_persistence_bundle(
        result["run_id"],
        result["canonical_portfolio"],
        result["agent_reviews"],
        result["conflicts"],
        result["scorecard"],
        result["committee_report"],
    )
    debate = run_bounded_debate(
        run_id=review_bundle.review_run.run_id,
        portfolio_id=review_bundle.portfolio.portfolio_id,
        conflicts=[record.conflict_payload for record in review_bundle.conflicts],
        agent_reviews=[record.review_payload for record in review_bundle.agent_reviews],
        debate_id=f"debate-{review_bundle.review_run.run_id}",
    )
    debate_bundle = build_debate_persistence_bundle(review_bundle.portfolio, review_bundle.review_run, debate)

    repository = InMemoryPersistenceRepository()
    repository.save_review_bundle(review_bundle)
    repository.save_debate_bundle(debate_bundle)

    stored = repository.get_review_run_bundle(result["run_id"])
    assert stored is not None
    assert stored.review_run.artifact_bundle_hash == review_bundle.review_run.artifact_bundle_hash
    assert stored.scorecard.final_recommendation == review_bundle.scorecard.final_recommendation

    stored_debate = repository.get_debate_bundle(debate_bundle.debate_session.debate_id)
    assert stored_debate is not None
    assert stored_debate.debate_session.debate_status == debate_bundle.debate_session.debate_status
    assert len(stored_debate.conflict_resolutions) == len(debate_bundle.conflict_resolutions)

    listed_debates = repository.list_debate_bundles(run_id=result["run_id"])
    assert len(listed_debates) == 1
    assert listed_debates[0].debate_session.debate_id == debate_bundle.debate_session.debate_id

    portfolio_events = repository.list_audit_events(portfolio_id=result["canonical_portfolio"].portfolio_id)
    assert len(portfolio_events) == 10
    assert {event.action for event in portfolio_events} == {
        "portfolio.registered",
        "canonical_portfolio.materialized",
        "review_run.completed",
        "committee_report.materialized",
        "debate_session.completed",
        "conflict_resolution.recorded",
    }


def test_persistence_schema_catalog_and_ddl_cover_expected_tables() -> None:
    catalog = get_persistence_schema_catalog()

    assert catalog.schema_version == PERSISTENCE_SCHEMA_VERSION
    assert catalog.active_backend == "python"
    assert catalog.reference_runtime == "js-baseline-only"
    assert {table.table_name for table in catalog.tables} == CATALOG_EXPECTED_TABLES

    ddl = render_postgres_ddl()
    for table_name in CATALOG_EXPECTED_TABLES:
        assert f"CREATE TABLE {table_name}" in ddl
    assert "JSONB" in ddl
    assert "CREATE INDEX ix_agent_reviews_agent_id" in ddl
    assert "CREATE INDEX ix_conflicts_run_id" in ddl
    assert "CREATE INDEX ix_debate_sessions_run_id" in ddl
    assert "CREATE INDEX ix_conflict_resolutions_debate_id" in ddl

