from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field
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


class PortfolioIdeaSubmission(OrbitModel):
    portfolio_name: str
    portfolio_type: str
    owner: str
    description: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


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


def submission_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def normalize_tags(tags: list[str]) -> list[str]:
    return [tag.strip() for tag in tags if tag.strip()]


def normalize_metadata(metadata: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in metadata.items():
        normalized_key = key.strip()
        normalized_value = value.strip()
        if not normalized_key or not normalized_value:
            continue
        normalized[normalized_key] = normalized_value
    return normalized


def idea_document_title(portfolio_name: str) -> str:
    return sanitize_filename(f"{slugify(portfolio_name) or 'portfolio'}-idea.md")


def render_idea_markdown(submission: PortfolioIdeaSubmission, *, submitted_at: str) -> str:
    normalized_description = submission.description.replace("\r\n", "\n").strip()
    portfolio_id = slugify(submission.portfolio_name) or "portfolio"
    normalized_tags = normalize_tags(submission.tags)
    normalized_metadata = normalize_metadata(submission.metadata)
    tag_text = ", ".join(normalized_tags) if normalized_tags else "No tags provided yet."
    metadata_text = (
        "; ".join(f"{key}={value}" for key, value in normalized_metadata.items())
        if normalized_metadata
        else "No structured metadata provided yet."
    )

    sections = {
        "Problem Discovery": (
            f"{normalized_description}\n"
            f"- Portfolio owner: {submission.owner}\n"
            f"- Working tags: {tag_text}\n"
            "- The first ORBIT review should test whether this problem is concrete, urgent, and investable."
        ),
        "Product Vision": (
            f"{submission.portfolio_name} is proposed as a {submission.portfolio_type} initiative owned by {submission.owner}.\n"
            f"- Core idea: {normalized_description.splitlines()[0]}\n"
            "- The first milestone is to turn the concept into a bounded reviewable portfolio."
        ),
        "Competitive Landscape": (
            "Competitive context is still early and should be validated through ORBIT review.\n"
            f"- Working market cues: {tag_text}\n"
            f"- Known structured metadata: {metadata_text}"
        ),
        "Business Requirements": (
            "The initial business requirement is to prove sponsor value, ownership, and delivery viability before expansion.\n"
            f"- Accountable owner: {submission.owner}\n"
            "- The committee should test commercial demand, operating cost, and launch conditions."
        ),
        "Product Requirements": (
            "The first product requirements are derived directly from the submitted idea description.\n"
            f"- Submitted description: {normalized_description.splitlines()[0]}\n"
            "- The first cut should stay narrow enough for a bounded pilot."
        ),
        "Architecture & System Design": (
            "Initial architecture assumptions should stay lightweight until the committee confirms feasibility.\n"
            "- A web, API, worker, and persistence path is enough for the first scoped build.\n"
            f"- Structured metadata for implementation planning: {metadata_text}"
        ),
        "AI Agents & Ethical Framework": (
            "If AI capabilities are involved, all high-impact actions should remain human-approved and auditable.\n"
            "- Review outputs should stay evidence-backed from day one.\n"
            "- Sensitive workflows should be traceable, reviewable, and reversible."
        ),
        "Operational Resilience": (
            "The first operating model should assume bounded pilots with explicit rollback and ownership controls.\n"
            "- Monitoring, backups, and incident ownership must be defined before scale.\n"
            "- The committee should identify whether resilience gaps block broader rollout."
        ),
        "MVP Roadmap": (
            "The first milestone is to validate the idea through committee review and a bounded pilot plan.\n"
            "- Phase 1 clarifies canonical scope, risks, and ownership.\n"
            "- Phase 2 validates implementation readiness and launch conditions."
        ),
        "Success Metrics": (
            "Success should be measured through sponsor adoption, workflow impact, and risk closure.\n"
            "- The committee should define leading indicators before broader rollout.\n"
            "- Review outputs should remain inspectable through ORBIT history and artifact APIs."
        ),
        "Post Launch Strategy": (
            "Post-launch expansion should wait until the first review validates readiness.\n"
            "- Expansion should be tied to measurable value and operating ownership.\n"
            "- Later go-to-market work should follow only after committee conditions are closed."
        ),
    }

    section_markdown = "\n\n".join(
        f"## {title}\n{body}"
        for title, body in sections.items()
    )
    return (
        f"# {submission.portfolio_name} Portfolio\n\n"
        f"Portfolio ID: {portfolio_id}\n"
        f"Portfolio Name: {submission.portfolio_name}\n"
        f"Portfolio Type: {submission.portfolio_type}\n"
        f"Owner: {submission.owner}\n"
        f"Submitted At: {submitted_at}\n"
        f"Idea Tags: {tag_text}\n"
        f"Idea Metadata: {metadata_text}\n\n"
        f"{section_markdown}\n"
    )


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

    def submit_idea(self, submission: PortfolioIdeaSubmission) -> PortfolioDetail:
        if not submission.portfolio_name.strip():
            raise InvalidPortfolioDocumentError("Portfolio idea name must not be empty.")
        if not submission.owner.strip():
            raise InvalidPortfolioDocumentError("Portfolio idea owner must not be empty.")
        if not submission.description.strip():
            raise InvalidPortfolioDocumentError("Portfolio idea description must not be empty.")
        if not submission.portfolio_type.strip():
            raise InvalidPortfolioDocumentError("Portfolio idea type must not be empty.")

        submitted_at = submission_date()
        document_title = idea_document_title(submission.portfolio_name)
        markdown = render_idea_markdown(submission, submitted_at=submitted_at)
        return self.submit_document(
            PortfolioDocumentSubmission(
                document_title=document_title,
                content=markdown,
            )
        )

    def submit_submission(
        self,
        submission: PortfolioDocumentSubmission | PortfolioIdeaSubmission,
    ) -> PortfolioDetail:
        if isinstance(submission, PortfolioDocumentSubmission):
            return self.submit_document(submission)
        return self.submit_idea(submission)

    def get_portfolio(self, portfolio_id: str) -> PortfolioDetail | None:
        bundle = self._repository.get_portfolio_bundle(portfolio_id)
        if bundle is None:
            return None
        return bundle_to_detail(bundle)

    def list_portfolios(self) -> PortfolioListResponse:
        return PortfolioListResponse(
            items=[summarize_portfolio(bundle) for bundle in self._repository.list_portfolio_bundles()]
        )
