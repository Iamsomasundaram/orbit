"""Milestone 6.1 initial persistence baseline.

Revision ID: 20260410_01
Revises:
Create Date: 2026-04-10 18:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260410_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_name", sa.String(length=255), nullable=False),
        sa.Column("portfolio_type", sa.String(length=64), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("submitted_at", sa.String(length=64), nullable=False),
        sa.Column("portfolio_status", sa.String(length=32), nullable=False),
        sa.Column("latest_review_run_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("portfolio_id", name=op.f("pk_portfolios")),
    )

    op.create_table(
        "source_documents",
        sa.Column("source_document_row_id", sa.String(length=160), nullable=False),
        sa.Column("source_document_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("document_hash", sa.String(length=64), nullable=False),
        sa.Column("content_available", sa.Boolean(), nullable=False),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_source_documents_portfolio_id_portfolios")),
        sa.PrimaryKeyConstraint("source_document_row_id", name=op.f("pk_source_documents")),
        sa.UniqueConstraint("portfolio_id", "source_document_id", name=op.f("uq_source_documents_portfolio_id")),
    )

    op.create_table(
        "canonical_portfolios",
        sa.Column("canonical_portfolio_row_id", sa.String(length=160), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("section_count", sa.Integer(), nullable=False),
        sa.Column("portfolio_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("canonical_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_canonical_portfolios_portfolio_id_portfolios")),
        sa.PrimaryKeyConstraint("canonical_portfolio_row_id", name=op.f("pk_canonical_portfolios")),
        sa.UniqueConstraint("portfolio_id", "schema_version", name=op.f("uq_canonical_portfolios_portfolio_id")),
    )

    op.create_table(
        "review_runs",
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("active_backend", sa.String(length=32), nullable=False),
        sa.Column("reference_runtime", sa.String(length=64), nullable=False),
        sa.Column("prompt_contract_version", sa.String(length=64), nullable=False),
        sa.Column("artifact_bundle_hash", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_review_runs_portfolio_id_portfolios")),
        sa.PrimaryKeyConstraint("run_id", name=op.f("pk_review_runs")),
    )

    op.create_table(
        "agent_reviews",
        sa.Column("agent_review_row_id", sa.String(length=192), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("agent_id", sa.String(length=128), nullable=False),
        sa.Column("recommendation", sa.String(length=64), nullable=False),
        sa.Column("findings_count", sa.Integer(), nullable=False),
        sa.Column("dimension_count", sa.Integer(), nullable=False),
        sa.Column("review_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("review_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_agent_reviews_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_agent_reviews_run_id_review_runs")),
        sa.PrimaryKeyConstraint("agent_review_row_id", name=op.f("pk_agent_reviews")),
        sa.UniqueConstraint("run_id", "agent_id", name=op.f("uq_agent_reviews_run_id")),
    )

    op.create_table(
        "conflicts",
        sa.Column("conflict_row_id", sa.String(length=192), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("conflict_id", sa.String(length=128), nullable=False),
        sa.Column("conflict_type", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("conflict_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("conflict_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_conflicts_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_conflicts_run_id_review_runs")),
        sa.PrimaryKeyConstraint("conflict_row_id", name=op.f("pk_conflicts")),
        sa.UniqueConstraint("run_id", "conflict_id", name=op.f("uq_conflicts_run_id")),
    )

    op.create_table(
        "scorecards",
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("final_recommendation", sa.String(length=64), nullable=False),
        sa.Column("weighted_composite_score", sa.Float(), nullable=False),
        sa.Column("scorecard_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("scorecard_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_scorecards_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_scorecards_run_id_review_runs")),
        sa.PrimaryKeyConstraint("run_id", name=op.f("pk_scorecards")),
    )

    op.create_table(
        "committee_reports",
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("final_recommendation", sa.String(length=64), nullable=False),
        sa.Column("report_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("markdown_sha256", sa.String(length=64), nullable=False),
        sa.Column("report_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_committee_reports_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_committee_reports_run_id_review_runs")),
        sa.PrimaryKeyConstraint("run_id", name=op.f("pk_committee_reports")),
    )

    op.create_table(
        "debate_sessions",
        sa.Column("debate_id", sa.String(length=192), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("debate_status", sa.String(length=64), nullable=False),
        sa.Column("max_rounds", sa.Integer(), nullable=False),
        sa.Column("conflicts_considered", sa.Integer(), nullable=False),
        sa.Column("score_change_required_count", sa.Integer(), nullable=False),
        sa.Column("debate_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("debate_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_debate_sessions_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_debate_sessions_run_id_review_runs")),
        sa.PrimaryKeyConstraint("debate_id", name=op.f("pk_debate_sessions")),
        sa.UniqueConstraint("run_id", name=op.f("uq_debate_sessions_run_id")),
    )

    op.create_table(
        "conflict_resolutions",
        sa.Column("resolution_row_id", sa.String(length=256), nullable=False),
        sa.Column("debate_id", sa.String(length=192), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("conflict_id", sa.String(length=128), nullable=False),
        sa.Column("outcome", sa.String(length=64), nullable=False),
        sa.Column("score_change_required", sa.Boolean(), nullable=False),
        sa.Column("resolution_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("resolution_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["debate_id"], ["debate_sessions.debate_id"], name=op.f("fk_conflict_resolutions_debate_id_debate_sessions")),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_conflict_resolutions_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_conflict_resolutions_run_id_review_runs")),
        sa.PrimaryKeyConstraint("resolution_row_id", name=op.f("pk_conflict_resolutions")),
        sa.UniqueConstraint("debate_id", "conflict_id", name=op.f("uq_conflict_resolutions_debate_id")),
    )

    op.create_table(
        "resynthesis_sessions",
        sa.Column("resynthesis_id", sa.String(length=256), nullable=False),
        sa.Column("debate_id", sa.String(length=192), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("resynthesis_status", sa.String(length=64), nullable=False),
        sa.Column("score_change_required_count", sa.Integer(), nullable=False),
        sa.Column("reused_original_artifacts", sa.Boolean(), nullable=False),
        sa.Column("active_artifact_source", sa.String(length=32), nullable=False),
        sa.Column("session_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("session_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["debate_id"], ["debate_sessions.debate_id"], name=op.f("fk_resynthesis_sessions_debate_id_debate_sessions")),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_resynthesis_sessions_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_resynthesis_sessions_run_id_review_runs")),
        sa.PrimaryKeyConstraint("resynthesis_id", name=op.f("pk_resynthesis_sessions")),
        sa.UniqueConstraint("debate_id", name=op.f("uq_resynthesis_sessions_debate_id")),
    )

    op.create_table(
        "resynthesized_scorecards",
        sa.Column("resynthesis_id", sa.String(length=256), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("final_recommendation", sa.String(length=64), nullable=False),
        sa.Column("weighted_composite_score", sa.Float(), nullable=False),
        sa.Column("scorecard_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("scorecard_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_resynthesized_scorecards_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["resynthesis_id"], ["resynthesis_sessions.resynthesis_id"], name=op.f("fk_resynthesized_scorecards_resynthesis_id_resynthesis_sessions")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_resynthesized_scorecards_run_id_review_runs")),
        sa.PrimaryKeyConstraint("resynthesis_id", name=op.f("pk_resynthesized_scorecards")),
    )

    op.create_table(
        "resynthesized_committee_reports",
        sa.Column("resynthesis_id", sa.String(length=256), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("final_recommendation", sa.String(length=64), nullable=False),
        sa.Column("report_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("markdown_sha256", sa.String(length=64), nullable=False),
        sa.Column("report_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_resynthesized_committee_reports_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["resynthesis_id"], ["resynthesis_sessions.resynthesis_id"], name=op.f("fk_resynthesized_committee_reports_resynthesis_id_resynthesis_sessions")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_resynthesized_committee_reports_run_id_review_runs")),
        sa.PrimaryKeyConstraint("resynthesis_id", name=op.f("pk_resynthesized_committee_reports")),
    )

    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=True),
        sa.Column("run_id", sa.String(length=128), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=160), nullable=False),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_audit_events_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_audit_events_run_id_review_runs")),
        sa.PrimaryKeyConstraint("event_id", name=op.f("pk_audit_events")),
    )

    op.create_index("ix_review_runs_portfolio_id", "review_runs", ["portfolio_id"], unique=False)
    op.create_index("ix_agent_reviews_run_id", "agent_reviews", ["run_id"], unique=False)
    op.create_index("ix_agent_reviews_agent_id", "agent_reviews", ["agent_id"], unique=False)
    op.create_index("ix_conflicts_run_id", "conflicts", ["run_id"], unique=False)
    op.create_index("ix_debate_sessions_run_id", "debate_sessions", ["run_id"], unique=False)
    op.create_index("ix_conflict_resolutions_debate_id", "conflict_resolutions", ["debate_id"], unique=False)
    op.create_index("ix_conflict_resolutions_run_id", "conflict_resolutions", ["run_id"], unique=False)
    op.create_index("ix_resynthesis_sessions_debate_id", "resynthesis_sessions", ["debate_id"], unique=False)
    op.create_index("ix_resynthesis_sessions_run_id", "resynthesis_sessions", ["run_id"], unique=False)
    op.create_index("ix_resynthesized_scorecards_run_id", "resynthesized_scorecards", ["run_id"], unique=False)
    op.create_index("ix_resynthesized_committee_reports_run_id", "resynthesized_committee_reports", ["run_id"], unique=False)
    op.create_index("ix_audit_events_portfolio_id", "audit_events", ["portfolio_id"], unique=False)
    op.create_index("ix_audit_events_run_id", "audit_events", ["run_id"], unique=False)
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_entity_type", table_name="audit_events")
    op.drop_index("ix_audit_events_run_id", table_name="audit_events")
    op.drop_index("ix_audit_events_portfolio_id", table_name="audit_events")
    op.drop_index("ix_resynthesized_committee_reports_run_id", table_name="resynthesized_committee_reports")
    op.drop_index("ix_resynthesized_scorecards_run_id", table_name="resynthesized_scorecards")
    op.drop_index("ix_resynthesis_sessions_run_id", table_name="resynthesis_sessions")
    op.drop_index("ix_resynthesis_sessions_debate_id", table_name="resynthesis_sessions")
    op.drop_index("ix_conflict_resolutions_run_id", table_name="conflict_resolutions")
    op.drop_index("ix_conflict_resolutions_debate_id", table_name="conflict_resolutions")
    op.drop_index("ix_debate_sessions_run_id", table_name="debate_sessions")
    op.drop_index("ix_conflicts_run_id", table_name="conflicts")
    op.drop_index("ix_agent_reviews_agent_id", table_name="agent_reviews")
    op.drop_index("ix_agent_reviews_run_id", table_name="agent_reviews")
    op.drop_index("ix_review_runs_portfolio_id", table_name="review_runs")

    op.drop_table("audit_events")
    op.drop_table("resynthesized_committee_reports")
    op.drop_table("resynthesized_scorecards")
    op.drop_table("resynthesis_sessions")
    op.drop_table("conflict_resolutions")
    op.drop_table("debate_sessions")
    op.drop_table("committee_reports")
    op.drop_table("scorecards")
    op.drop_table("conflicts")
    op.drop_table("agent_reviews")
    op.drop_table("review_runs")
    op.drop_table("canonical_portfolios")
    op.drop_table("source_documents")
    op.drop_table("portfolios")
