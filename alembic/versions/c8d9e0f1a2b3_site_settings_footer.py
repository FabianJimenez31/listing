"""site_settings: footer config (tagline, copyright, social, legal, ally logos)

Revision ID: c8d9e0f1a2b3
Revises: b7c2d4e6f8a0
Create Date: 2026-06-25 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c2d4e6f8a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STR_COLS = (
    "copyright_text",
    "social_instagram",
    "social_linkedin",
    "social_youtube",
    "legal_privacy_url",
    "legal_terms_url",
    "legal_cookies_url",
)


def upgrade() -> None:
    op.add_column("site_settings", sa.Column("footer_tagline", sa.Text(), nullable=True))
    for col in _STR_COLS:
        op.add_column("site_settings", sa.Column(col, sa.String(length=500), nullable=True))
    # JSON list of ally logos; NOT NULL with an empty-list default so the existing
    # singleton row backfills cleanly on both Postgres and SQLite.
    op.add_column(
        "site_settings",
        sa.Column("footer_logos", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("site_settings", "footer_logos")
    for col in reversed(_STR_COLS):
        op.drop_column("site_settings", col)
    op.drop_column("site_settings", "footer_tagline")
