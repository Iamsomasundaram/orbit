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

    detail = service.submit_idea(
        PortfolioIdeaSubmission(
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
    )

    assert detail.portfolio.portfolio_id == "ledgerpilot"
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
