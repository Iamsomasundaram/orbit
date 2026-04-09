from __future__ import annotations

from pathlib import Path

from orbit_worker.persistence import (
    PERSISTENCE_SCHEMA_VERSION,
    InMemoryPersistenceRepository,
    build_portfolio_ingestion_bundle,
    build_review_persistence_bundle,
    bundle_to_table_rows,
    get_persistence_schema_catalog,
    ingestion_bundle_to_table_rows,
    render_postgres_ddl,
)
from orbit_worker.runner import run_review_pipeline

ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"
EXPECTED_TABLES = {
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
    assert set(rows) == EXPECTED_TABLES
    assert rows["committee_reports"][0]["markdown"] == result["committee_report"].markdown
    assert rows["scorecards"][0]["weighted_composite_score"] == 3.61


def test_in_memory_repository_round_trip_and_audit_listing() -> None:
    result = run_review_pipeline(str(INPUT_PATH))
    bundle = build_review_persistence_bundle(
        result["run_id"],
        result["canonical_portfolio"],
        result["agent_reviews"],
        result["conflicts"],
        result["scorecard"],
        result["committee_report"],
    )
    repository = InMemoryPersistenceRepository()
    repository.save_review_bundle(bundle)

    stored = repository.get_review_run_bundle(result["run_id"])
    assert stored is not None
    assert stored.review_run.artifact_bundle_hash == bundle.review_run.artifact_bundle_hash
    assert stored.scorecard.final_recommendation == bundle.scorecard.final_recommendation

    portfolio_events = repository.list_audit_events(portfolio_id=result["canonical_portfolio"].portfolio_id)
    assert len(portfolio_events) == 4
    assert {event.action for event in portfolio_events} == {
        "portfolio.registered",
        "canonical_portfolio.materialized",
        "review_run.completed",
        "committee_report.materialized",
    }


def test_persistence_schema_catalog_and_ddl_cover_expected_tables() -> None:
    catalog = get_persistence_schema_catalog()

    assert catalog.schema_version == PERSISTENCE_SCHEMA_VERSION
    assert catalog.active_backend == "python"
    assert catalog.reference_runtime == "js-baseline-only"
    assert {table.table_name for table in catalog.tables} == EXPECTED_TABLES

    ddl = render_postgres_ddl()
    for table_name in EXPECTED_TABLES:
        assert f"CREATE TABLE {table_name}" in ddl
    assert "JSONB" in ddl
    assert "CREATE INDEX ix_agent_reviews_agent_id" in ddl
    assert "CREATE INDEX ix_conflicts_run_id" in ddl

