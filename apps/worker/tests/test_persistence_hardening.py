from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.debates import DebateAlreadyExistsError, DebateService  # noqa: E402
from orbit_api.migrations import determine_migration_action  # noqa: E402
from orbit_api.portfolios import PortfolioAlreadyExistsError, PortfolioDocumentSubmission, PortfolioIngestionService  # noqa: E402
from orbit_api.resyntheses import ResynthesisAlreadyExistsError, ResynthesisService  # noqa: E402
from orbit_api.review_runs import ReviewRunService  # noqa: E402
from orbit_worker.debate import run_bounded_debate  # noqa: E402
from orbit_worker.ingestion import ingest_portfolio_document  # noqa: E402
from orbit_worker.persistence import (  # noqa: E402
    SqlAlchemyPersistenceRepository,
    build_debate_persistence_bundle,
    build_portfolio_ingestion_bundle,
    get_persistence_schema_catalog,
)
from orbit_worker.schemas import validate_debate_session  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"
DATABASE_URL = os.environ.get("DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith("postgresql"),
    reason="Milestone 6.1 persistence hardening tests require a PostgreSQL DATABASE_URL.",
)


def debate_with_forced_recheck(debate):
    payload = debate.model_dump(mode="json")
    for resolution in payload["resolutions"]:
        if resolution["topic"] != "security_and_compliance":
            continue
        resolution["outcome"] = "needs_score_revisit"
        resolution["score_change_required"] = True
        resolution["score_change_rationale"] = "Forced recheck for Milestone 6.1 persistence validation."
        resolution["status"] = "needs_review"
    payload["debate_status"] = "completed_with_escalations"
    payload["executive_summary"] = "Forced score recheck for Milestone 6.1 SQL persistence validation."
    return validate_debate_session(payload)


def _alembic_config(database_url: str) -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def _admin_database_url(database_url: str) -> str:
    return database_url


def _database_url_with_name(database_url: str, database_name: str) -> str:
    return make_url(database_url).set(database=database_name).render_as_string(hide_password=False)


@contextmanager
def migrated_repository() -> SqlAlchemyPersistenceRepository:
    database_name = f"orbit_test_{uuid4().hex[:12]}"
    admin_engine = create_engine(_admin_database_url(DATABASE_URL), future=True, isolation_level="AUTOCOMMIT")
    repository: SqlAlchemyPersistenceRepository | None = None
    database_url = _database_url_with_name(DATABASE_URL, database_name)

    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))

        command.upgrade(_alembic_config(database_url), "head")

        repository = SqlAlchemyPersistenceRepository(database_url)
        repository.assert_schema_ready()
        yield repository
    finally:
        if repository is not None:
            repository.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()


def test_alembic_baseline_creates_expected_tables() -> None:
    with migrated_repository() as repository:
        table_names = set(inspect(repository._engine).get_table_names())  # noqa: SLF001
        expected_tables = {table.table_name for table in get_persistence_schema_catalog().tables}

        assert "alembic_version" in table_names
        assert expected_tables.issubset(table_names)


def test_migration_bootstrap_classifies_existing_schema_states() -> None:
    expected_tables = {table.table_name for table in get_persistence_schema_catalog().tables}

    assert determine_migration_action(set()) == "upgrade"
    assert determine_migration_action({"alembic_version"}) == "upgrade"
    assert determine_migration_action(expected_tables) == "stamp_then_upgrade"


def test_portfolio_submission_uses_db_backed_duplicate_enforcement(tmp_path: Path) -> None:
    with migrated_repository() as repository:
        service = PortfolioIngestionService(repository=repository, storage_root=tmp_path / "submissions")
        submission = PortfolioDocumentSubmission(
            document_title="procurepilot-thin-slice.md",
            content=INPUT_PATH.read_text(encoding="utf-8"),
        )

        detail = service.submit_document(submission)
        assert detail.portfolio.portfolio_id == "strong-ai-saas-001"

        with pytest.raises(PortfolioAlreadyExistsError):
            service.submit_document(submission)


def test_db_backed_debate_and_resynthesis_uniqueness_is_enforced() -> None:
    with migrated_repository() as repository:
        canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
        repository.save_portfolio_bundle(
            build_portfolio_ingestion_bundle(
                canonical_portfolio,
                source_contents_by_document_id={"source-markdown-001": INPUT_PATH.read_bytes()},
            )
        )

        review_summary = ReviewRunService(repository=repository).start_review(canonical_portfolio.portfolio_id)
        debate_service = DebateService(repository=repository)
        debate_summary = debate_service.start_debate(review_summary.run_id)

        with pytest.raises(DebateAlreadyExistsError):
            debate_service.start_debate(review_summary.run_id)

        resynthesis_service = ResynthesisService(repository=repository)
        resynthesis_service.start_resynthesis(debate_summary.debate_id)

        with pytest.raises(ResynthesisAlreadyExistsError):
            resynthesis_service.start_resynthesis(debate_summary.debate_id)


def test_sql_persistence_preserves_original_and_resynthesized_artifact_selection() -> None:
    with migrated_repository() as repository:
        canonical_portfolio = ingest_portfolio_document(INPUT_PATH)
        repository.save_portfolio_bundle(
            build_portfolio_ingestion_bundle(
                canonical_portfolio,
                source_contents_by_document_id={"source-markdown-001": INPUT_PATH.read_bytes()},
            )
        )

        review_service = ReviewRunService(repository=repository)
        debate_service = DebateService(repository=repository)
        resynthesis_service = ResynthesisService(repository=repository)

        first_review = review_service.start_review(canonical_portfolio.portfolio_id)
        first_debate = debate_service.start_debate(first_review.run_id)
        first_resynthesis = resynthesis_service.start_resynthesis(first_debate.debate_id)
        first_detail = resynthesis_service.get_resynthesis(first_resynthesis.resynthesis_id)

        assert first_detail is not None
        assert first_detail.resynthesis_session.active_artifact_source == "original"
        assert first_detail.resynthesized_scorecard is None
        assert first_detail.active_scorecard.final_recommendation == "Proceed with Conditions"

        second_review = review_service.start_review(canonical_portfolio.portfolio_id)
        second_review_bundle = repository.get_review_run_bundle(second_review.run_id)
        assert second_review_bundle is not None

        forced_debate = debate_with_forced_recheck(
            run_bounded_debate(
                run_id=second_review_bundle.review_run.run_id,
                portfolio_id=second_review_bundle.portfolio.portfolio_id,
                conflicts=[record.conflict_payload for record in second_review_bundle.conflicts],
                agent_reviews=[record.review_payload for record in second_review_bundle.agent_reviews],
                debate_id=f"debate-{second_review_bundle.review_run.run_id}",
            )
        )
        repository.save_debate_bundle(
            build_debate_persistence_bundle(
                second_review_bundle.portfolio,
                second_review_bundle.review_run,
                forced_debate,
            )
        )

        second_resynthesis = resynthesis_service.start_resynthesis(forced_debate.debate_id)
        second_detail = resynthesis_service.get_resynthesis(second_resynthesis.resynthesis_id)

        assert second_detail is not None
        assert second_detail.resynthesis_session.active_artifact_source == "resynthesized"
        assert second_detail.resynthesized_scorecard is not None
        assert second_detail.resynthesized_committee_report is not None
        assert second_detail.active_scorecard.final_recommendation == "Pilot Only"
