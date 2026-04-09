from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, MetaData, String, Table, Text, UniqueConstraint, create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.schema import Column, CreateIndex, CreateTable

from .schemas import AgentReview, CanonicalPortfolio, CommitteeReport, ConflictRecord, OrbitModel, Scorecard, SourceDocument

PERSISTENCE_SCHEMA_VERSION = "m2-v1"
SOURCE_OF_TRUTH_MODULE = "orbit_worker.schemas"
REFERENCE_RUNTIME_MODE = "js-baseline-only"
ACTIVE_BACKEND = "python"
SYSTEM_ACTOR_ID = "orbit-platform"
SYSTEM_ACTOR_NAME = "ORBIT Platform"


class PersistenceTableSpec(OrbitModel):
    table_name: str
    purpose: str
    primary_key: str
    source_contract: str | None
    json_payload_columns: list[str]
    queryable_columns: list[str]


class PersistenceSchemaCatalog(OrbitModel):
    schema_version: str
    source_of_truth_module: str
    active_backend: Literal["python"]
    reference_runtime: str
    tables: list[PersistenceTableSpec]


class PortfolioRecord(OrbitModel):
    portfolio_id: str
    portfolio_name: str
    portfolio_type: str
    owner: str
    submitted_at: str
    portfolio_status: Literal["registered", "canonicalized", "reviewed"]
    latest_review_run_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceDocumentRecord(OrbitModel):
    source_document_row_id: str
    source_document_id: str
    portfolio_id: str
    kind: str
    title: str
    path: str
    document_hash: str
    content_available: bool
    source_payload: SourceDocument
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CanonicalPortfolioRecord(OrbitModel):
    canonical_portfolio_row_id: str
    portfolio_id: str
    schema_version: str
    section_count: int
    portfolio_payload_hash: str
    canonical_payload: CanonicalPortfolio
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewRunRecord(OrbitModel):
    run_id: str
    portfolio_id: str
    review_status: Literal["running", "completed", "failed"]
    active_backend: Literal["python"]
    reference_runtime: str
    prompt_contract_version: str
    artifact_bundle_hash: str
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentReviewRecord(OrbitModel):
    agent_review_row_id: str
    run_id: str
    portfolio_id: str
    agent_id: str
    recommendation: str
    findings_count: int
    dimension_count: int
    review_payload_hash: str
    review_payload: AgentReview
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConflictPersistenceRecord(OrbitModel):
    conflict_row_id: str
    run_id: str
    portfolio_id: str
    conflict_id: str
    conflict_type: str
    topic: str
    severity: str
    conflict_payload_hash: str
    conflict_payload: ConflictRecord
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ScorecardRecord(OrbitModel):
    run_id: str
    portfolio_id: str
    final_recommendation: str
    weighted_composite_score: float
    scorecard_payload_hash: str
    scorecard_payload: Scorecard
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CommitteeReportRecord(OrbitModel):
    run_id: str
    portfolio_id: str
    final_recommendation: str
    report_payload_hash: str
    markdown_sha256: str
    markdown: str
    report_payload: CommitteeReport
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditActor(OrbitModel):
    actor_type: Literal["system", "user", "service"]
    actor_id: str
    display_name: str


class AuditEventRecord(OrbitModel):
    event_id: str
    portfolio_id: str | None = None
    run_id: str | None = None
    actor: AuditActor
    action: str
    entity_type: str
    entity_id: str
    event_payload: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewPersistenceBundle(OrbitModel):
    schema_version: str
    portfolio: PortfolioRecord
    source_documents: list[SourceDocumentRecord]
    canonical_portfolio: CanonicalPortfolioRecord
    review_run: ReviewRunRecord
    agent_reviews: list[AgentReviewRecord]
    conflicts: list[ConflictPersistenceRecord]
    scorecard: ScorecardRecord
    committee_report: CommitteeReportRecord
    audit_events: list[AuditEventRecord]


class PortfolioIngestionBundle(OrbitModel):
    schema_version: str
    portfolio: PortfolioRecord
    source_documents: list[SourceDocumentRecord]
    canonical_portfolio: CanonicalPortfolioRecord
    audit_events: list[AuditEventRecord]


class PersistenceRepository(Protocol):
    def save_portfolio_bundle(self, bundle: PortfolioIngestionBundle) -> None: ...

    def get_portfolio_bundle(self, portfolio_id: str) -> PortfolioIngestionBundle | None: ...

    def list_portfolio_bundles(self) -> list[PortfolioIngestionBundle]: ...

    def save_review_bundle(self, bundle: ReviewPersistenceBundle) -> None: ...

    def get_review_run_bundle(self, run_id: str) -> ReviewPersistenceBundle | None: ...

    def list_audit_events(self, portfolio_id: str | None = None, run_id: str | None = None) -> list[AuditEventRecord]: ...


class InMemoryPersistenceRepository:
    def __init__(self) -> None:
        self._portfolios: dict[str, PortfolioIngestionBundle] = {}
        self._review_runs: dict[str, ReviewPersistenceBundle] = {}
        self._audit_events: dict[str, AuditEventRecord] = {}

    def save_portfolio_bundle(self, bundle: PortfolioIngestionBundle) -> None:
        self._portfolios[bundle.portfolio.portfolio_id] = bundle
        for event in bundle.audit_events:
            self._audit_events[event.event_id] = event

    def get_portfolio_bundle(self, portfolio_id: str) -> PortfolioIngestionBundle | None:
        return self._portfolios.get(portfolio_id)

    def list_portfolio_bundles(self) -> list[PortfolioIngestionBundle]:
        return sorted(
            self._portfolios.values(),
            key=lambda bundle: (bundle.portfolio.created_at, bundle.portfolio.portfolio_id),
            reverse=True,
        )

    def save_review_bundle(self, bundle: ReviewPersistenceBundle) -> None:
        self._review_runs[bundle.review_run.run_id] = bundle
        self._portfolios[bundle.portfolio.portfolio_id] = PortfolioIngestionBundle(
            schema_version=bundle.schema_version,
            portfolio=bundle.portfolio,
            source_documents=bundle.source_documents,
            canonical_portfolio=bundle.canonical_portfolio,
            audit_events=bundle.audit_events,
        )
        for event in bundle.audit_events:
            self._audit_events[event.event_id] = event

    def get_review_run_bundle(self, run_id: str) -> ReviewPersistenceBundle | None:
        return self._review_runs.get(run_id)

    def list_audit_events(self, portfolio_id: str | None = None, run_id: str | None = None) -> list[AuditEventRecord]:
        events = list(self._audit_events.values())
        if portfolio_id is not None:
            events = [event for event in events if event.portfolio_id == portfolio_id]
        if run_id is not None:
            events = [event for event in events if event.run_id == run_id]
        return sorted(events, key=lambda event: (event.created_at, event.event_id))


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def payload_sha256(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _model_row(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="python")


def _source_document_hash(source_document: SourceDocument) -> tuple[str, bool]:
    source_path = Path(source_document.path)
    if source_path.exists() and source_path.is_file():
        return sha256(source_path.read_bytes()).hexdigest(), True
    return payload_sha256(source_document), False


def _portfolio_row_status(latest_review_run_id: str | None) -> Literal["registered", "canonicalized", "reviewed"]:
    return "reviewed" if latest_review_run_id else "canonicalized"


def _artifact_bundle_hash(
    canonical_portfolio: CanonicalPortfolio,
    agent_reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
    scorecard: Scorecard,
    committee_report: CommitteeReport,
) -> str:
    return payload_sha256(
        {
            "canonical_portfolio": canonical_portfolio,
            "agent_reviews": agent_reviews,
            "conflicts": conflicts,
            "scorecard": scorecard,
            "committee_report": committee_report,
        }
    )


def _default_prompt_contract_version(agent_reviews: list[AgentReview]) -> str:
    if not agent_reviews:
        return "unknown"
    return agent_reviews[0].review_metadata.prompt_contract_version


def _source_document_row_id(portfolio_id: str, source_document_id: str) -> str:
    return f"{portfolio_id}:{source_document_id}"


def _canonical_portfolio_row_id(portfolio_id: str) -> str:
    return f"{portfolio_id}:{PERSISTENCE_SCHEMA_VERSION}"


def _agent_review_row_id(run_id: str, agent_id: str) -> str:
    return f"{run_id}:{agent_id}"


def _conflict_row_id(run_id: str, conflict_id: str) -> str:
    return f"{run_id}:{conflict_id}"


def _audit_event_id(run_id: str | None, action: str, entity_id: str) -> str:
    seed = f"{run_id or 'no-run'}::{action}::{entity_id}"
    return f"audit-{sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def build_portfolio_record(canonical_portfolio: CanonicalPortfolio, latest_review_run_id: str | None = None, now: datetime | None = None) -> PortfolioRecord:
    timestamp = now or datetime.now(timezone.utc)
    return PortfolioRecord(
        portfolio_id=canonical_portfolio.portfolio_id,
        portfolio_name=canonical_portfolio.portfolio_name,
        portfolio_type=canonical_portfolio.portfolio_type,
        owner=canonical_portfolio.owner,
        submitted_at=canonical_portfolio.submitted_at,
        portfolio_status=_portfolio_row_status(latest_review_run_id),
        latest_review_run_id=latest_review_run_id,
        created_at=timestamp,
        updated_at=timestamp,
    )


def build_source_document_records(canonical_portfolio: CanonicalPortfolio, now: datetime | None = None) -> list[SourceDocumentRecord]:
    timestamp = now or datetime.now(timezone.utc)
    records: list[SourceDocumentRecord] = []
    for source_document in canonical_portfolio.source_documents:
        document_hash, content_available = _source_document_hash(source_document)
        records.append(
            SourceDocumentRecord(
                source_document_row_id=_source_document_row_id(canonical_portfolio.portfolio_id, source_document.id),
                source_document_id=source_document.id,
                portfolio_id=canonical_portfolio.portfolio_id,
                kind=source_document.kind,
                title=source_document.title,
                path=source_document.path,
                document_hash=document_hash,
                content_available=content_available,
                source_payload=source_document,
                created_at=timestamp,
            )
        )
    return records


def build_canonical_portfolio_record(canonical_portfolio: CanonicalPortfolio, now: datetime | None = None) -> CanonicalPortfolioRecord:
    timestamp = now or datetime.now(timezone.utc)
    return CanonicalPortfolioRecord(
        canonical_portfolio_row_id=_canonical_portfolio_row_id(canonical_portfolio.portfolio_id),
        portfolio_id=canonical_portfolio.portfolio_id,
        schema_version=PERSISTENCE_SCHEMA_VERSION,
        section_count=len(canonical_portfolio.sections),
        portfolio_payload_hash=payload_sha256(canonical_portfolio),
        canonical_payload=canonical_portfolio,
        created_at=timestamp,
    )


def build_review_run_record(
    run_id: str,
    canonical_portfolio: CanonicalPortfolio,
    agent_reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
    scorecard: Scorecard,
    committee_report: CommitteeReport,
    now: datetime | None = None,
) -> ReviewRunRecord:
    timestamp = now or datetime.now(timezone.utc)
    return ReviewRunRecord(
        run_id=run_id,
        portfolio_id=canonical_portfolio.portfolio_id,
        review_status="completed",
        active_backend="python",
        reference_runtime=REFERENCE_RUNTIME_MODE,
        prompt_contract_version=_default_prompt_contract_version(agent_reviews),
        artifact_bundle_hash=_artifact_bundle_hash(canonical_portfolio, agent_reviews, conflicts, scorecard, committee_report),
        started_at=timestamp,
        completed_at=timestamp,
        created_at=timestamp,
    )


def build_agent_review_records(
    run_id: str,
    canonical_portfolio: CanonicalPortfolio,
    agent_reviews: list[AgentReview],
    now: datetime | None = None,
) -> list[AgentReviewRecord]:
    timestamp = now or datetime.now(timezone.utc)
    return [
        AgentReviewRecord(
            agent_review_row_id=_agent_review_row_id(run_id, review.agent_id),
            run_id=run_id,
            portfolio_id=canonical_portfolio.portfolio_id,
            agent_id=review.agent_id,
            recommendation=review.recommendation,
            findings_count=len(review.findings),
            dimension_count=len(review.dimension_scores),
            review_payload_hash=payload_sha256(review),
            review_payload=review,
            created_at=timestamp,
        )
        for review in agent_reviews
    ]


def build_conflict_records(
    run_id: str,
    canonical_portfolio: CanonicalPortfolio,
    conflicts: list[ConflictRecord],
    now: datetime | None = None,
) -> list[ConflictPersistenceRecord]:
    timestamp = now or datetime.now(timezone.utc)
    return [
        ConflictPersistenceRecord(
            conflict_row_id=_conflict_row_id(run_id, conflict.conflict_id),
            run_id=run_id,
            portfolio_id=canonical_portfolio.portfolio_id,
            conflict_id=conflict.conflict_id,
            conflict_type=conflict.conflict_type,
            topic=conflict.topic,
            severity=conflict.severity,
            conflict_payload_hash=payload_sha256(conflict),
            conflict_payload=conflict,
            created_at=timestamp,
        )
        for conflict in conflicts
    ]


def build_scorecard_record(scorecard: Scorecard, now: datetime | None = None) -> ScorecardRecord:
    timestamp = now or datetime.now(timezone.utc)
    return ScorecardRecord(
        run_id=scorecard.run_id,
        portfolio_id=scorecard.portfolio_id,
        final_recommendation=scorecard.final_recommendation,
        weighted_composite_score=scorecard.weighted_composite_score,
        scorecard_payload_hash=payload_sha256(scorecard),
        scorecard_payload=scorecard,
        created_at=timestamp,
    )


def build_committee_report_record(committee_report: CommitteeReport, scorecard: Scorecard, now: datetime | None = None) -> CommitteeReportRecord:
    timestamp = now or datetime.now(timezone.utc)
    markdown_sha = sha256(committee_report.markdown.encode("utf-8")).hexdigest()
    return CommitteeReportRecord(
        run_id=committee_report.run_id,
        portfolio_id=committee_report.portfolio_id,
        final_recommendation=scorecard.final_recommendation,
        report_payload_hash=payload_sha256(committee_report),
        markdown_sha256=markdown_sha,
        markdown=committee_report.markdown,
        report_payload=committee_report,
        created_at=timestamp,
    )


def build_audit_event_records(
    canonical_portfolio: CanonicalPortfolio,
    review_run: ReviewRunRecord,
    scorecard: Scorecard,
    committee_report: CommitteeReport,
    now: datetime | None = None,
) -> list[AuditEventRecord]:
    timestamp = now or datetime.now(timezone.utc)
    actor = AuditActor(actor_type="system", actor_id=SYSTEM_ACTOR_ID, display_name=SYSTEM_ACTOR_NAME)
    return [
        AuditEventRecord(
            event_id=_audit_event_id(review_run.run_id, "portfolio.registered", canonical_portfolio.portfolio_id),
            portfolio_id=canonical_portfolio.portfolio_id,
            run_id=review_run.run_id,
            actor=actor,
            action="portfolio.registered",
            entity_type="portfolio",
            entity_id=canonical_portfolio.portfolio_id,
            event_payload={
                "portfolio_name": canonical_portfolio.portfolio_name,
                "portfolio_type": canonical_portfolio.portfolio_type,
            },
            created_at=timestamp,
        ),
        AuditEventRecord(
            event_id=_audit_event_id(review_run.run_id, "canonical_portfolio.materialized", canonical_portfolio.portfolio_id),
            portfolio_id=canonical_portfolio.portfolio_id,
            run_id=review_run.run_id,
            actor=actor,
            action="canonical_portfolio.materialized",
            entity_type="canonical_portfolio",
            entity_id=canonical_portfolio.portfolio_id,
            event_payload={
                "schema_version": PERSISTENCE_SCHEMA_VERSION,
                "section_count": len(canonical_portfolio.sections),
            },
            created_at=timestamp,
        ),
        AuditEventRecord(
            event_id=_audit_event_id(review_run.run_id, "review_run.completed", review_run.run_id),
            portfolio_id=canonical_portfolio.portfolio_id,
            run_id=review_run.run_id,
            actor=actor,
            action="review_run.completed",
            entity_type="review_run",
            entity_id=review_run.run_id,
            event_payload={
                "final_recommendation": scorecard.final_recommendation,
                "weighted_composite_score": scorecard.weighted_composite_score,
            },
            created_at=timestamp,
        ),
        AuditEventRecord(
            event_id=_audit_event_id(review_run.run_id, "committee_report.materialized", review_run.run_id),
            portfolio_id=canonical_portfolio.portfolio_id,
            run_id=review_run.run_id,
            actor=actor,
            action="committee_report.materialized",
            entity_type="committee_report",
            entity_id=review_run.run_id,
            event_payload={
                "markdown_sha256": sha256(committee_report.markdown.encode('utf-8')).hexdigest(),
                "top_conflicts": len(committee_report.top_conflicts),
            },
            created_at=timestamp,
        ),
    ]


def build_ingestion_audit_event_records(
    canonical_portfolio: CanonicalPortfolio,
    now: datetime | None = None,
) -> list[AuditEventRecord]:
    timestamp = now or datetime.now(timezone.utc)
    actor = AuditActor(actor_type="system", actor_id=SYSTEM_ACTOR_ID, display_name=SYSTEM_ACTOR_NAME)
    return [
        AuditEventRecord(
            event_id=_audit_event_id(None, "portfolio.registered", canonical_portfolio.portfolio_id),
            portfolio_id=canonical_portfolio.portfolio_id,
            run_id=None,
            actor=actor,
            action="portfolio.registered",
            entity_type="portfolio",
            entity_id=canonical_portfolio.portfolio_id,
            event_payload={
                "portfolio_name": canonical_portfolio.portfolio_name,
                "portfolio_type": canonical_portfolio.portfolio_type,
            },
            created_at=timestamp,
        ),
        AuditEventRecord(
            event_id=_audit_event_id(None, "canonical_portfolio.materialized", canonical_portfolio.portfolio_id),
            portfolio_id=canonical_portfolio.portfolio_id,
            run_id=None,
            actor=actor,
            action="canonical_portfolio.materialized",
            entity_type="canonical_portfolio",
            entity_id=canonical_portfolio.portfolio_id,
            event_payload={
                "schema_version": PERSISTENCE_SCHEMA_VERSION,
                "section_count": len(canonical_portfolio.sections),
            },
            created_at=timestamp,
        ),
    ]


def build_portfolio_ingestion_bundle(
    canonical_portfolio: CanonicalPortfolio,
    now: datetime | None = None,
) -> PortfolioIngestionBundle:
    timestamp = now or datetime.now(timezone.utc)
    return PortfolioIngestionBundle(
        schema_version=PERSISTENCE_SCHEMA_VERSION,
        portfolio=build_portfolio_record(canonical_portfolio, latest_review_run_id=None, now=timestamp),
        source_documents=build_source_document_records(canonical_portfolio, now=timestamp),
        canonical_portfolio=build_canonical_portfolio_record(canonical_portfolio, now=timestamp),
        audit_events=build_ingestion_audit_event_records(canonical_portfolio, now=timestamp),
    )


def build_review_persistence_bundle(
    run_id: str,
    canonical_portfolio: CanonicalPortfolio,
    agent_reviews: list[AgentReview],
    conflicts: list[ConflictRecord],
    scorecard: Scorecard,
    committee_report: CommitteeReport,
    now: datetime | None = None,
) -> ReviewPersistenceBundle:
    timestamp = now or datetime.now(timezone.utc)
    review_run = build_review_run_record(run_id, canonical_portfolio, agent_reviews, conflicts, scorecard, committee_report, timestamp)
    return ReviewPersistenceBundle(
        schema_version=PERSISTENCE_SCHEMA_VERSION,
        portfolio=build_portfolio_record(canonical_portfolio, latest_review_run_id=run_id, now=timestamp),
        source_documents=build_source_document_records(canonical_portfolio, now=timestamp),
        canonical_portfolio=build_canonical_portfolio_record(canonical_portfolio, now=timestamp),
        review_run=review_run,
        agent_reviews=build_agent_review_records(run_id, canonical_portfolio, agent_reviews, now=timestamp),
        conflicts=build_conflict_records(run_id, canonical_portfolio, conflicts, now=timestamp),
        scorecard=build_scorecard_record(scorecard, now=timestamp),
        committee_report=build_committee_report_record(committee_report, scorecard, now=timestamp),
        audit_events=build_audit_event_records(canonical_portfolio, review_run, scorecard, committee_report, now=timestamp),
    )


def portfolio_row_values(record: PortfolioRecord) -> dict[str, Any]:
    return _model_row(record)


def source_document_row_values(record: SourceDocumentRecord) -> dict[str, Any]:
    return _model_row(record)


def canonical_portfolio_row_values(record: CanonicalPortfolioRecord) -> dict[str, Any]:
    return _model_row(record)


def review_run_row_values(record: ReviewRunRecord) -> dict[str, Any]:
    return _model_row(record)


def agent_review_row_values(record: AgentReviewRecord) -> dict[str, Any]:
    return _model_row(record)


def conflict_row_values(record: ConflictPersistenceRecord) -> dict[str, Any]:
    return _model_row(record)


def scorecard_row_values(record: ScorecardRecord) -> dict[str, Any]:
    return _model_row(record)


def committee_report_row_values(record: CommitteeReportRecord) -> dict[str, Any]:
    return _model_row(record)


def audit_event_row_values(record: AuditEventRecord) -> dict[str, Any]:
    return {
        "event_id": record.event_id,
        "portfolio_id": record.portfolio_id,
        "run_id": record.run_id,
        "actor_type": record.actor.actor_type,
        "actor_id": record.actor.actor_id,
        "display_name": record.actor.display_name,
        "action": record.action,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "event_payload": _jsonable(record.event_payload),
        "created_at": record.created_at,
    }


def bundle_to_table_rows(bundle: ReviewPersistenceBundle) -> dict[str, list[dict[str, Any]]]:
    return {
        "portfolios": [portfolio_row_values(bundle.portfolio)],
        "source_documents": [source_document_row_values(record) for record in bundle.source_documents],
        "canonical_portfolios": [canonical_portfolio_row_values(bundle.canonical_portfolio)],
        "review_runs": [review_run_row_values(bundle.review_run)],
        "agent_reviews": [agent_review_row_values(record) for record in bundle.agent_reviews],
        "conflicts": [conflict_row_values(record) for record in bundle.conflicts],
        "scorecards": [scorecard_row_values(bundle.scorecard)],
        "committee_reports": [committee_report_row_values(bundle.committee_report)],
        "audit_events": [audit_event_row_values(record) for record in bundle.audit_events],
    }


def ingestion_bundle_to_table_rows(bundle: PortfolioIngestionBundle) -> dict[str, list[dict[str, Any]]]:
    return {
        "portfolios": [portfolio_row_values(bundle.portfolio)],
        "source_documents": [source_document_row_values(record) for record in bundle.source_documents],
        "canonical_portfolios": [canonical_portfolio_row_values(bundle.canonical_portfolio)],
        "audit_events": [audit_event_row_values(record) for record in bundle.audit_events],
    }


def _upsert_row(connection: Any, table: Table, row: dict[str, Any], conflict_columns: list[str]) -> None:
    statement = insert(table).values(**row)
    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if column.name not in conflict_columns
    }
    connection.execute(
        statement.on_conflict_do_update(
            index_elements=conflict_columns,
            set_=update_columns,
        )
    )


def _audit_event_from_row(row: dict[str, Any]) -> AuditEventRecord:
    return AuditEventRecord.model_validate(
        {
            "event_id": row["event_id"],
            "portfolio_id": row["portfolio_id"],
            "run_id": row["run_id"],
            "actor": {
                "actor_type": row["actor_type"],
                "actor_id": row["actor_id"],
                "display_name": row["display_name"],
            },
            "action": row["action"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "event_payload": row["event_payload"],
            "created_at": row["created_at"],
        }
    )


class SqlAlchemyPersistenceRepository:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def ensure_schema(self) -> None:
        persistence_metadata.create_all(self._engine)

    def dispose(self) -> None:
        self._engine.dispose()

    def save_portfolio_bundle(self, bundle: PortfolioIngestionBundle) -> None:
        rows = ingestion_bundle_to_table_rows(bundle)
        with self._engine.begin() as connection:
            _upsert_row(connection, portfolios_table, rows["portfolios"][0], ["portfolio_id"])
            for row in rows["source_documents"]:
                _upsert_row(connection, source_documents_table, row, ["source_document_row_id"])
            _upsert_row(connection, canonical_portfolios_table, rows["canonical_portfolios"][0], ["canonical_portfolio_row_id"])
            for row in rows["audit_events"]:
                _upsert_row(connection, audit_events_table, row, ["event_id"])

    def get_portfolio_bundle(self, portfolio_id: str) -> PortfolioIngestionBundle | None:
        with self._engine.connect() as connection:
            portfolio_row = connection.execute(
                select(portfolios_table).where(portfolios_table.c.portfolio_id == portfolio_id)
            ).mappings().first()
            if portfolio_row is None:
                return None

            source_document_rows = connection.execute(
                select(source_documents_table)
                .where(source_documents_table.c.portfolio_id == portfolio_id)
                .order_by(source_documents_table.c.source_document_row_id)
            ).mappings().all()
            canonical_row = connection.execute(
                select(canonical_portfolios_table)
                .where(canonical_portfolios_table.c.portfolio_id == portfolio_id)
                .order_by(canonical_portfolios_table.c.created_at.desc())
            ).mappings().first()
            audit_rows = connection.execute(
                select(audit_events_table)
                .where(audit_events_table.c.portfolio_id == portfolio_id)
                .order_by(audit_events_table.c.created_at, audit_events_table.c.event_id)
            ).mappings().all()

        if canonical_row is None:
            return None

        return PortfolioIngestionBundle(
            schema_version=PERSISTENCE_SCHEMA_VERSION,
            portfolio=PortfolioRecord.model_validate(dict(portfolio_row)),
            source_documents=[SourceDocumentRecord.model_validate(dict(row)) for row in source_document_rows],
            canonical_portfolio=CanonicalPortfolioRecord.model_validate(dict(canonical_row)),
            audit_events=[_audit_event_from_row(dict(row)) for row in audit_rows],
        )

    def list_portfolio_bundles(self) -> list[PortfolioIngestionBundle]:
        with self._engine.connect() as connection:
            portfolio_ids = [
                row["portfolio_id"]
                for row in connection.execute(
                    select(portfolios_table.c.portfolio_id).order_by(
                        portfolios_table.c.created_at.desc(),
                        portfolios_table.c.portfolio_id.desc(),
                    )
                ).mappings().all()
            ]
        return [bundle for portfolio_id in portfolio_ids if (bundle := self.get_portfolio_bundle(portfolio_id)) is not None]

    def save_review_bundle(self, bundle: ReviewPersistenceBundle) -> None:
        rows = bundle_to_table_rows(bundle)
        with self._engine.begin() as connection:
            _upsert_row(connection, portfolios_table, rows["portfolios"][0], ["portfolio_id"])
            for row in rows["source_documents"]:
                _upsert_row(connection, source_documents_table, row, ["source_document_row_id"])
            _upsert_row(connection, canonical_portfolios_table, rows["canonical_portfolios"][0], ["canonical_portfolio_row_id"])
            _upsert_row(connection, review_runs_table, rows["review_runs"][0], ["run_id"])
            for row in rows["agent_reviews"]:
                _upsert_row(connection, agent_reviews_table, row, ["agent_review_row_id"])
            for row in rows["conflicts"]:
                _upsert_row(connection, conflicts_table, row, ["conflict_row_id"])
            _upsert_row(connection, scorecards_table, rows["scorecards"][0], ["run_id"])
            _upsert_row(connection, committee_reports_table, rows["committee_reports"][0], ["run_id"])
            for row in rows["audit_events"]:
                _upsert_row(connection, audit_events_table, row, ["event_id"])

    def get_review_run_bundle(self, run_id: str) -> ReviewPersistenceBundle | None:
        with self._engine.connect() as connection:
            review_run_row = connection.execute(
                select(review_runs_table).where(review_runs_table.c.run_id == run_id)
            ).mappings().first()
            if review_run_row is None:
                return None

            portfolio_id = review_run_row["portfolio_id"]
            portfolio_bundle = self.get_portfolio_bundle(portfolio_id)
            if portfolio_bundle is None:
                return None

            agent_rows = connection.execute(
                select(agent_reviews_table)
                .where(agent_reviews_table.c.run_id == run_id)
                .order_by(agent_reviews_table.c.agent_review_row_id)
            ).mappings().all()
            conflict_rows = connection.execute(
                select(conflicts_table)
                .where(conflicts_table.c.run_id == run_id)
                .order_by(conflicts_table.c.conflict_row_id)
            ).mappings().all()
            scorecard_row = connection.execute(
                select(scorecards_table).where(scorecards_table.c.run_id == run_id)
            ).mappings().first()
            committee_report_row = connection.execute(
                select(committee_reports_table).where(committee_reports_table.c.run_id == run_id)
            ).mappings().first()
            audit_rows = connection.execute(
                select(audit_events_table)
                .where(audit_events_table.c.run_id == run_id)
                .order_by(audit_events_table.c.created_at, audit_events_table.c.event_id)
            ).mappings().all()

        if scorecard_row is None or committee_report_row is None:
            return None

        return ReviewPersistenceBundle(
            schema_version=PERSISTENCE_SCHEMA_VERSION,
            portfolio=portfolio_bundle.portfolio,
            source_documents=portfolio_bundle.source_documents,
            canonical_portfolio=portfolio_bundle.canonical_portfolio,
            review_run=ReviewRunRecord.model_validate(dict(review_run_row)),
            agent_reviews=[AgentReviewRecord.model_validate(dict(row)) for row in agent_rows],
            conflicts=[ConflictPersistenceRecord.model_validate(dict(row)) for row in conflict_rows],
            scorecard=ScorecardRecord.model_validate(dict(scorecard_row)),
            committee_report=CommitteeReportRecord.model_validate(dict(committee_report_row)),
            audit_events=[_audit_event_from_row(dict(row)) for row in audit_rows],
        )

    def list_audit_events(self, portfolio_id: str | None = None, run_id: str | None = None) -> list[AuditEventRecord]:
        statement = select(audit_events_table)
        if portfolio_id is not None:
            statement = statement.where(audit_events_table.c.portfolio_id == portfolio_id)
        if run_id is not None:
            statement = statement.where(audit_events_table.c.run_id == run_id)
        statement = statement.order_by(audit_events_table.c.created_at, audit_events_table.c.event_id)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_audit_event_from_row(dict(row)) for row in rows]


NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

persistence_metadata = MetaData(naming_convention=NAMING_CONVENTION)

portfolios_table = Table(
    "portfolios",
    persistence_metadata,
    Column("portfolio_id", String(128), primary_key=True),
    Column("portfolio_name", String(255), nullable=False),
    Column("portfolio_type", String(64), nullable=False),
    Column("owner", String(255), nullable=False),
    Column("submitted_at", String(64), nullable=False),
    Column("portfolio_status", String(32), nullable=False),
    Column("latest_review_run_id", String(128), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

source_documents_table = Table(
    "source_documents",
    persistence_metadata,
    Column("source_document_row_id", String(160), primary_key=True),
    Column("source_document_id", String(128), nullable=False),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=False),
    Column("kind", String(64), nullable=False),
    Column("title", String(255), nullable=False),
    Column("path", Text, nullable=False),
    Column("document_hash", String(64), nullable=False),
    Column("content_available", Boolean, nullable=False),
    Column("source_payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("portfolio_id", "source_document_id"),
)

canonical_portfolios_table = Table(
    "canonical_portfolios",
    persistence_metadata,
    Column("canonical_portfolio_row_id", String(160), primary_key=True),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=False),
    Column("schema_version", String(32), nullable=False),
    Column("section_count", Integer, nullable=False),
    Column("portfolio_payload_hash", String(64), nullable=False),
    Column("canonical_payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("portfolio_id", "schema_version"),
)

review_runs_table = Table(
    "review_runs",
    persistence_metadata,
    Column("run_id", String(128), primary_key=True),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=False),
    Column("review_status", String(32), nullable=False),
    Column("active_backend", String(32), nullable=False),
    Column("reference_runtime", String(64), nullable=False),
    Column("prompt_contract_version", String(64), nullable=False),
    Column("artifact_bundle_hash", String(64), nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

agent_reviews_table = Table(
    "agent_reviews",
    persistence_metadata,
    Column("agent_review_row_id", String(192), primary_key=True),
    Column("run_id", String(128), ForeignKey("review_runs.run_id"), nullable=False),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=False),
    Column("agent_id", String(128), nullable=False),
    Column("recommendation", String(64), nullable=False),
    Column("findings_count", Integer, nullable=False),
    Column("dimension_count", Integer, nullable=False),
    Column("review_payload_hash", String(64), nullable=False),
    Column("review_payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("run_id", "agent_id"),
)

conflicts_table = Table(
    "conflicts",
    persistence_metadata,
    Column("conflict_row_id", String(192), primary_key=True),
    Column("run_id", String(128), ForeignKey("review_runs.run_id"), nullable=False),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=False),
    Column("conflict_id", String(128), nullable=False),
    Column("conflict_type", String(64), nullable=False),
    Column("topic", String(255), nullable=False),
    Column("severity", String(32), nullable=False),
    Column("conflict_payload_hash", String(64), nullable=False),
    Column("conflict_payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("run_id", "conflict_id"),
)

scorecards_table = Table(
    "scorecards",
    persistence_metadata,
    Column("run_id", String(128), ForeignKey("review_runs.run_id"), primary_key=True),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=False),
    Column("final_recommendation", String(64), nullable=False),
    Column("weighted_composite_score", Float, nullable=False),
    Column("scorecard_payload_hash", String(64), nullable=False),
    Column("scorecard_payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

committee_reports_table = Table(
    "committee_reports",
    persistence_metadata,
    Column("run_id", String(128), ForeignKey("review_runs.run_id"), primary_key=True),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=False),
    Column("final_recommendation", String(64), nullable=False),
    Column("report_payload_hash", String(64), nullable=False),
    Column("markdown_sha256", String(64), nullable=False),
    Column("report_payload", JSONB, nullable=False),
    Column("markdown", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

audit_events_table = Table(
    "audit_events",
    persistence_metadata,
    Column("event_id", String(128), primary_key=True),
    Column("portfolio_id", String(128), ForeignKey("portfolios.portfolio_id"), nullable=True),
    Column("run_id", String(128), ForeignKey("review_runs.run_id"), nullable=True),
    Column("actor_type", String(32), nullable=False),
    Column("actor_id", String(128), nullable=False),
    Column("display_name", String(255), nullable=False),
    Column("action", String(128), nullable=False),
    Column("entity_type", String(64), nullable=False),
    Column("entity_id", String(160), nullable=False),
    Column("event_payload", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

Index("ix_review_runs_portfolio_id", review_runs_table.c.portfolio_id)
Index("ix_agent_reviews_run_id", agent_reviews_table.c.run_id)
Index("ix_agent_reviews_agent_id", agent_reviews_table.c.agent_id)
Index("ix_conflicts_run_id", conflicts_table.c.run_id)
Index("ix_audit_events_portfolio_id", audit_events_table.c.portfolio_id)
Index("ix_audit_events_run_id", audit_events_table.c.run_id)
Index("ix_audit_events_entity_type", audit_events_table.c.entity_type)


PERSISTENCE_TABLE_SPECS = [
    PersistenceTableSpec(
        table_name="portfolios",
        purpose="Portfolio submission envelope and top-level lifecycle state.",
        primary_key="portfolio_id",
        source_contract="orbit_worker.schemas.CanonicalPortfolio",
        json_payload_columns=[],
        queryable_columns=["portfolio_name", "portfolio_type", "owner", "submitted_at", "portfolio_status", "latest_review_run_id"],
    ),
    PersistenceTableSpec(
        table_name="source_documents",
        purpose="Durable record for original source documents attached to a portfolio.",
        primary_key="source_document_row_id",
        source_contract="orbit_worker.schemas.SourceDocument",
        json_payload_columns=["source_payload"],
        queryable_columns=["portfolio_id", "source_document_id", "kind", "title", "path", "document_hash", "content_available"],
    ),
    PersistenceTableSpec(
        table_name="canonical_portfolios",
        purpose="Canonical ORBIT portfolio payload keyed by persistence schema version.",
        primary_key="canonical_portfolio_row_id",
        source_contract="orbit_worker.schemas.CanonicalPortfolio",
        json_payload_columns=["canonical_payload"],
        queryable_columns=["portfolio_id", "schema_version", "section_count", "portfolio_payload_hash"],
    ),
    PersistenceTableSpec(
        table_name="review_runs",
        purpose="Run-level execution envelope for one committee review cycle.",
        primary_key="run_id",
        source_contract=None,
        json_payload_columns=[],
        queryable_columns=["portfolio_id", "review_status", "active_backend", "reference_runtime", "prompt_contract_version", "artifact_bundle_hash", "started_at", "completed_at"],
    ),
    PersistenceTableSpec(
        table_name="agent_reviews",
        purpose="Structured review output for each specialist agent within a run.",
        primary_key="agent_review_row_id",
        source_contract="orbit_worker.schemas.AgentReview",
        json_payload_columns=["review_payload"],
        queryable_columns=["run_id", "portfolio_id", "agent_id", "recommendation", "findings_count", "dimension_count", "review_payload_hash"],
    ),
    PersistenceTableSpec(
        table_name="conflicts",
        purpose="Structured conflict records generated from agent review outputs.",
        primary_key="conflict_row_id",
        source_contract="orbit_worker.schemas.ConflictRecord",
        json_payload_columns=["conflict_payload"],
        queryable_columns=["run_id", "portfolio_id", "conflict_id", "conflict_type", "topic", "severity", "conflict_payload_hash"],
    ),
    PersistenceTableSpec(
        table_name="scorecards",
        purpose="Committee scorecard summary for a completed run.",
        primary_key="run_id",
        source_contract="orbit_worker.schemas.Scorecard",
        json_payload_columns=["scorecard_payload"],
        queryable_columns=["portfolio_id", "final_recommendation", "weighted_composite_score", "scorecard_payload_hash"],
    ),
    PersistenceTableSpec(
        table_name="committee_reports",
        purpose="Committee report payload and markdown artifact for a completed run.",
        primary_key="run_id",
        source_contract="orbit_worker.schemas.CommitteeReport",
        json_payload_columns=["report_payload"],
        queryable_columns=["portfolio_id", "final_recommendation", "report_payload_hash", "markdown_sha256"],
    ),
    PersistenceTableSpec(
        table_name="audit_events",
        purpose="Append-only audit trail for portfolio and review lifecycle events.",
        primary_key="event_id",
        source_contract=None,
        json_payload_columns=["event_payload"],
        queryable_columns=["portfolio_id", "run_id", "actor_type", "actor_id", "action", "entity_type", "entity_id", "created_at"],
    ),
]


def get_persistence_schema_catalog() -> PersistenceSchemaCatalog:
    return PersistenceSchemaCatalog(
        schema_version=PERSISTENCE_SCHEMA_VERSION,
        source_of_truth_module=SOURCE_OF_TRUTH_MODULE,
        active_backend="python",
        reference_runtime=REFERENCE_RUNTIME_MODE,
        tables=PERSISTENCE_TABLE_SPECS,
    )


def render_postgres_ddl() -> str:
    dialect = postgresql.dialect()
    statements: list[str] = []
    for table in persistence_metadata.sorted_tables:
        statements.append(f"{CreateTable(table).compile(dialect=dialect)};")
    for table in persistence_metadata.sorted_tables:
        for index in sorted(table.indexes, key=lambda item: item.name or ""):
            statements.append(f"{CreateIndex(index).compile(dialect=dialect)};")
    return "\n\n".join(statements)




