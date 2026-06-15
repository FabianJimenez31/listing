"""property.show_on_home flag (home page visibility) + backfill from featured

Revision ID: c3a7d9e1f2b4
Revises: b1f2c3d4e5f6
Create Date: 2026-06-15 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a7d9e1f2b4"
down_revision: Union[str, Sequence[str], None] = "b1f2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("show_on_home", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.create_index(batch_op.f("ix_properties_show_on_home"), ["show_on_home"], unique=False)

    # Preserve current home selection: flag whatever was featured on the home.
    # Built with SQLAlchemy expressions so the boolean literal renders correctly
    # on every dialect (TRUE on Postgres, 1 on SQLite/MySQL).
    properties = sa.table("properties", sa.column("id", sa.String), sa.column("show_on_home", sa.Boolean))
    featured = sa.table("featured_properties", sa.column("property_id", sa.String), sa.column("scope", sa.String))
    op.execute(
        properties.update()
        .where(properties.c.id.in_(sa.select(featured.c.property_id).where(featured.c.scope == "home")))
        .values(show_on_home=True)
    )


def downgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_properties_show_on_home"))
        batch_op.drop_column("show_on_home")
