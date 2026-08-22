"""tour_payments table for Wompi-based tour purchases

Revision ID: c4e8f2a6b9d3
Revises: a9c3e7d1b5f2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c4e8f2a6b9d3"
down_revision: Union[str, Sequence[str], None] = "a9c3e7d1b5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tour_payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("amount_in_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reference", sa.String(120), nullable=False, unique=True),
        sa.Column("wompi_transaction_id", sa.String(80), nullable=True, index=True),
        sa.Column(
            "tour_id", sa.String(36), sa.ForeignKey("virtual_tours.id"), nullable=True
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "entity_type IN ('properties','projects')", name="ck_tour_payments_entity"
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','declined','voided')",
            name="ck_tour_payments_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("tour_payments")
