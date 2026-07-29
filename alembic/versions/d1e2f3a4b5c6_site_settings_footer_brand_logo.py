"""site_settings: footer brand logo (independent from the header logo)

Revision ID: d1e2f3a4b5c6
Revises: c8d9e0f1a2b3
Create Date: 2026-06-25 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("site_settings", sa.Column("footer_logo_url", sa.String(length=1000), nullable=True))
    op.add_column("site_settings", sa.Column("footer_logo_storage_key", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("site_settings", "footer_logo_storage_key")
    op.drop_column("site_settings", "footer_logo_url")
