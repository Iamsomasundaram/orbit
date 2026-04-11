from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from orbit_api.portfolios import (  # noqa: E402
    PortfolioAlreadyExistsError,
    PortfolioDocumentSubmission,
    PortfolioIdeaSubmission,
    PortfolioIngestionService,
    idea_portfolio_id,
)
from orbit_worker.persistence import InMemoryPersistenceRepository  # noqa: E402

INPUT_PATH = ROOT / "tests" / "fixtures" / "source-documents" / "procurepilot-thin-slice.md"


def test_submission_service_persists_canonical_portfolio_bundle(tmp_path: Path) -> None:
    repository = InMemoryPersistenceRepository()
    service = PortfolioIngestionService(repository=repository, storage_root=tmp_path / "submissions")

    detail = service.submit_document(
        PortfolioDocumentSubmission(
            document_title="procurepilot-thin-slice.md",
            content=INPUT_PATH.read_text(encoding="utf-8"),
        )
    )

    assert detail.portfolio.portfolio_id == "strong-ai-saas-001"
    assert detail.portfolio.portfolio_status == "canonicalized"
    assert detail.canonical_portfolio.section_count == 11
    assert len(detail.source_documents) == 1
    assert len(detail.audit_events) == 2

    stored = repository.get_portfolio_bundle("strong-ai-saas-001")
    assert stored is not None
    assert Path(stored.source_documents[0].path).exists()
    assert stored.canonical_portfolio.canonical_payload.portfolio_name == "ProcurePilot"


def test_submission_service_rejects_duplicate_portfolio_ids(tmp_path: Path) -> None:
    repository = InMemoryPersistenceRepository()
    service = PortfolioIngestionService(repository=repository, storage_root=tmp_path / "submissions")
    submission = PortfolioDocumentSubmission(
        document_title="procurepilot-thin-slice.md",
        content=INPUT_PATH.read_text(encoding="utf-8"),
    )

    service.submit_document(submission)

    with pytest.raises(PortfolioAlreadyExistsError):
        service.submit_document(submission)


def test_idea_submission_generates_canonical_portfolio_bundle(tmp_path: Path) -> None:
    repository = InMemoryPersistenceRepository()
    service = PortfolioIngestionService(repository=repository, storage_root=tmp_path / "submissions")
    submission = PortfolioIdeaSubmission(
        portfolio_name="LedgerPilot",
        portfolio_type="product",
        owner="Studio Delta",
        description=(
            "LedgerPilot helps finance teams reconcile subscription usage, invoice drift, "
            "and approval bottlenecks across disconnected tools."
        ),
        tags=["finops", "workflow", "finance"],
        metadata={"market": "mid-market", "delivery_model": "saas"},
    )

    detail = service.submit_idea(submission)

    assert detail.portfolio.portfolio_id == idea_portfolio_id(submission)
    assert detail.portfolio.portfolio_status == "canonicalized"
    assert detail.canonical_portfolio.section_count == 11
    assert detail.source_documents[0].title == "ledgerpilot-idea.md"
    assert Path(detail.source_documents[0].path).exists()
    assert (
        detail.canonical_portfolio.canonical_payload.sections["problem_discovery"].summary
        == "LedgerPilot helps finance teams reconcile subscription usage, invoice drift, and approval bottlenecks across disconnected tools."
    )
    assert "Working market cues: finops, workflow, finance" in (
        detail.canonical_portfolio.canonical_payload.sections["competitive_landscape"].raw_text
    )


def test_idea_submission_uses_bounded_identity_when_names_match(tmp_path: Path) -> None:
    repository = InMemoryPersistenceRepository()
    service = PortfolioIngestionService(repository=repository, storage_root=tmp_path / "submissions")

    first_detail = service.submit_idea(
        PortfolioIdeaSubmission(
            portfolio_name="Orbit Compare",
            portfolio_type="product",
            owner="Studio Alpha",
            description="First portfolio with the shared public name.",
            tags=["compare"],
        )
    )
    second_detail = service.submit_idea(
        PortfolioIdeaSubmission(
            portfolio_name="Orbit Compare",
            portfolio_type="product",
            owner="Studio Beta",
            description="Second portfolio with the same display name but different identity.",
            tags=["compare"],
        )
    )

    assert first_detail.portfolio.portfolio_id != second_detail.portfolio.portfolio_id
    assert first_detail.portfolio.portfolio_id.startswith("orbit-compare-")
    assert second_detail.portfolio.portfolio_id.startswith("orbit-compare-")


def test_idea_submission_parses_markdown_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = InMemoryPersistenceRepository()
    service = PortfolioIngestionService(repository=repository, storage_root=tmp_path / "submissions")
    parse_calls = 0

    from orbit_api import portfolios as portfolio_module  # noqa: WPS433

    original_parse_markdown = portfolio_module.parse_markdown

    def counting_parse_markdown(markdown: str, source_path: str):
        nonlocal parse_calls
        parse_calls += 1
        return original_parse_markdown(markdown, source_path)

    monkeypatch.setattr(portfolio_module, "parse_markdown", counting_parse_markdown)

    service.submit_idea(
        PortfolioIdeaSubmission(
            portfolio_name="Single Parse Check",
            portfolio_type="product",
            owner="Studio Gamma",
            description="Milestone 9 reduces parsing to one pass for JSON idea submissions.",
        )
    )

    assert parse_calls == 1
