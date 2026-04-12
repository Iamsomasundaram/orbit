"""Milestone 12.2 query and history hardening indexes.

Revision ID: 20260412_01
Revises: 20260411_01
Create Date: 2026-04-12 13:20:00
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260412_01"
down_revision = "20260411_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_review_runs_portfolio_id_created_at",
        "review_runs",
        ["portfolio_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_debate_sessions_run_id_created_at",
        "debate_sessions",
        ["run_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_resynthesis_sessions_debate_id_created_at",
        "resynthesis_sessions",
        ["debate_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_portfolio_id_created_at_event_id",
        "audit_events",
        ["portfolio_id", "created_at", "event_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_run_id_created_at_event_id",
        "audit_events",
        ["run_id", "created_at", "event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_run_id_created_at_event_id", table_name="audit_events")
    op.drop_index("ix_audit_events_portfolio_id_created_at_event_id", table_name="audit_events")
    op.drop_index("ix_resynthesis_sessions_debate_id_created_at", table_name="resynthesis_sessions")
    op.drop_index("ix_debate_sessions_run_id_created_at", table_name="debate_sessions")
    op.drop_index("ix_review_runs_portfolio_id_created_at", table_name="review_runs")
