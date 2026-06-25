"""property.has_elevator (ascensor) + has_study (zona de estudio)

Revision ID: f6a0b3c5d7e9
Revises: e5f9a2b4c6d8
Create Date: 2026-06-17 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a0b3c5d7e9"
down_revision: Union[str, Sequence[str], None] = "e5f9a2b4c6d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("has_elevator", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(
            sa.Column("has_study", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_column("has_study")
        batch_op.drop_column("has_elevator")
