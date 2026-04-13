"""Milestone 15 decision validation and human review persistence.

Revision ID: 20260413_01
Revises: 20260412_01
Create Date: 2026-04-13 22:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260413_01"
down_revision = "20260412_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "human_reviews",
        sa.Column("human_review_id", sa.String(length=192), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("reviewer_name", sa.String(length=255), nullable=False),
        sa.Column("final_recommendation", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.String(length=32), nullable=False),
        sa.Column("review_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("review_payload", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("human_review_id"),
        sa.UniqueConstraint("portfolio_id", "human_review_id"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"]),
    )
    op.create_index("ix_human_reviews_portfolio_id", "human_reviews", ["portfolio_id"], unique=False)
    op.create_index("ix_human_reviews_portfolio_id_created_at", "human_reviews", ["portfolio_id", "created_at"], unique=False)

    op.create_table(
        "decision_validations",
        sa.Column("decision_validation_id", sa.String(length=256), nullable=False),
        sa.Column("portfolio_id", sa.String(length=128), nullable=False),
        sa.Column("review_run_id", sa.String(length=128), nullable=False),
        sa.Column("human_review_id", sa.String(length=192), nullable=False),
        sa.Column("agreement_score", sa.Float(), nullable=False),
        sa.Column("recommendation_match", sa.String(length=32), nullable=False),
        sa.Column("score_difference", sa.Float(), nullable=False),
        sa.Column("risk_overlap", sa.Float(), nullable=False),
        sa.Column("risk_recall", sa.Float(), nullable=False),
        sa.Column("risk_precision", sa.Float(), nullable=False),
        sa.Column("confidence_alignment", sa.Float(), nullable=False),
        sa.Column("validation_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("validation_payload", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("decision_validation_id"),
        sa.UniqueConstraint("review_run_id", "human_review_id"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.portfolio_id"]),
        sa.ForeignKeyConstraint(["review_run_id"], ["review_runs.run_id"]),
        sa.ForeignKeyConstraint(["human_review_id"], ["human_reviews.human_review_id"]),
    )
    op.create_index("ix_decision_validations_portfolio_id", "decision_validations", ["portfolio_id"], unique=False)
    op.create_index("ix_decision_validations_review_run_id", "decision_validations", ["review_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_decision_validations_review_run_id", table_name="decision_validations")
    op.drop_index("ix_decision_validations_portfolio_id", table_name="decision_validations")
    op.drop_table("decision_validations")

    op.drop_index("ix_human_reviews_portfolio_id_created_at", table_name="human_reviews")
    op.drop_index("ix_human_reviews_portfolio_id", table_name="human_reviews")
    op.drop_table("human_reviews")
