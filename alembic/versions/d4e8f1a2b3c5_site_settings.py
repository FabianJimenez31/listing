"""site_settings singleton table (admin-editable brand logo)

Revision ID: d4e8f1a2b3c5
Revises: c3a7d9e1f2b4
Create Date: 2026-06-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e8f1a2b3c5"
down_revision: Union[str, Sequence[str], None] = "c3a7d9e1f2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("logo_url", sa.String(length=1000), nullable=True),
        sa.Column("logo_storage_key", sa.String(length=500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("site_settings")
