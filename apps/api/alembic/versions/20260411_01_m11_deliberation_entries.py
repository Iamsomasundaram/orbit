"""Milestone 11 deliberation entries.

Revision ID: 20260411_01
Revises: 20260410_01
Create Date: 2026-04-11 19:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260411_01"
down_revision = "20260410_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deliberation_entries",
        sa.Column("deliberation_entry_row_id", sa.String(length=192), nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=128), nullable=True),
        sa.Column("agent_role", sa.String(length=255), nullable=False),
        sa.Column("statement_type", sa.String(length=64), nullable=False),
        sa.Column("statement_text", sa.Text(), nullable=False),
        sa.Column("conflict_reference", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"], name=op.f("fk_deliberation_entries_portfolio_id_portfolios")),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.run_id"], name=op.f("fk_deliberation_entries_run_id_review_runs")),
        sa.PrimaryKeyConstraint("deliberation_entry_row_id", name=op.f("pk_deliberation_entries")),
        sa.UniqueConstraint("run_id", "sequence_number", name=op.f("uq_deliberation_entries_run_id")),
    )
    op.create_index("ix_deliberation_entries_run_id", "deliberation_entries", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_deliberation_entries_run_id", table_name="deliberation_entries")
    op.drop_table("deliberation_entries")
