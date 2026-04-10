from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from orbit_worker.ingestion import parse_markdown, slugify
from orbit_worker.persistence import (
    AuditEventRecord,
    CanonicalPortfolioRecord,
    PortfolioConflictError,
    PersistenceRepository,
    PortfolioIngestionBundle,
    PortfolioRecord,
    SourceDocumentRecord,
    build_portfolio_ingestion_bundle,
)
from orbit_worker.schemas import OrbitModel


class PortfolioDocumentSubmission(OrbitModel):
    document_title: str
    content: str
    document_kind: Literal["markdown"] = "markdown"


class PortfolioSummary(OrbitModel):
    portfolio_id: str
    portfolio_name: str
    portfolio_type: str
    owner: str
    submitted_at: str
    portfolio_status: str
    source_document_count: int
    canonical_schema_version: str
    created_at: datetime
    updated_at: datetime


class PortfolioDetail(OrbitModel):
    portfolio: PortfolioRecord
    source_documents: list[SourceDocumentRecord]
    canonical_portfolio: CanonicalPortfolioRecord
    audit_events: list[AuditEventRecord]


class PortfolioListResponse(OrbitModel):
    items: list[PortfolioSummary]


class PortfolioAlreadyExistsError(ValueError):
    pass


class InvalidPortfolioDocumentError(ValueError):
    pass


def sanitize_filename(value: str) -> str:
    candidate = Path(value or "portfolio.md").name
    stem = slugify(Path(candidate).stem) or "portfolio"
    suffix = Path(candidate).suffix.lower() or ".md"
    return f"{stem}{suffix}"


def summarize_portfolio(bundle: PortfolioIngestionBundle) -> PortfolioSummary:
    return PortfolioSummary(
        portfolio_id=bundle.portfolio.portfolio_id,
        portfolio_name=bundle.portfolio.portfolio_name,
        portfolio_type=bundle.portfolio.portfolio_type,
        owner=bundle.portfolio.owner,
        submitted_at=bundle.portfolio.submitted_at,
        portfolio_status=bundle.portfolio.portfolio_status,
        source_document_count=len(bundle.source_documents),
        canonical_schema_version=bundle.canonical_portfolio.schema_version,
        created_at=bundle.portfolio.created_at,
        updated_at=bundle.portfolio.updated_at,
    )


def bundle_to_detail(bundle: PortfolioIngestionBundle) -> PortfolioDetail:
    return PortfolioDetail(
        portfolio=bundle.portfolio,
        source_documents=bundle.source_documents,
        canonical_portfolio=bundle.canonical_portfolio,
        audit_events=bundle.audit_events,
    )


class PortfolioIngestionService:
    def __init__(self, repository: PersistenceRepository, storage_root: Path) -> None:
        self._repository = repository
        self._storage_root = storage_root
        self._storage_root.mkdir(parents=True, exist_ok=True)

    def submit_document(self, submission: PortfolioDocumentSubmission) -> PortfolioDetail:
        normalized_content = submission.content.replace("\r\n", "\n").strip()
        if not normalized_content:
            raise InvalidPortfolioDocumentError("Portfolio document content must not be empty.")
        if submission.document_kind != "markdown":
            raise InvalidPortfolioDocumentError("Milestone 3 only accepts markdown portfolio documents.")

        provisional_filename = sanitize_filename(submission.document_title)
        provisional_portfolio = parse_markdown(normalized_content, provisional_filename)
        target_directory = (self._storage_root / provisional_portfolio.portfolio_id).resolve()
        target_path = target_directory / provisional_filename
        canonical_portfolio = parse_markdown(normalized_content, str(target_path))
        bundle = build_portfolio_ingestion_bundle(
            canonical_portfolio,
            source_contents_by_document_id={"source-markdown-001": f"{normalized_content}\n".encode("utf-8")},
        )
        try:
            self._repository.save_portfolio_bundle(bundle)
        except PortfolioConflictError as exc:
            raise PortfolioAlreadyExistsError(
                f"Portfolio '{provisional_portfolio.portfolio_id}' already exists in the ingestion store."
            ) from exc

        target_directory.mkdir(parents=True, exist_ok=True)
        target_path.write_text(f"{normalized_content}\n", encoding="utf-8")
        return bundle_to_detail(bundle)

    def get_portfolio(self, portfolio_id: str) -> PortfolioDetail | None:
        bundle = self._repository.get_portfolio_bundle(portfolio_id)
        if bundle is None:
            return None
        return bundle_to_detail(bundle)

    def list_portfolios(self) -> PortfolioListResponse:
        return PortfolioListResponse(
            items=[summarize_portfolio(bundle) for bundle in self._repository.list_portfolio_bundles()]
        )
