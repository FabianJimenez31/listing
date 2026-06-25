"""property descriptive fields: stratum, balcony, view, age, admin fee, security

Revision ID: b7c2d4e6f8a0
Revises: a1c2e3f4b5d6
Create Date: 2026-06-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7c2d4e6f8a0"
down_revision: Union[str, Sequence[str], None] = "a1c2e3f4b5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("has_balcony", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(sa.Column("stratum", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("view_type", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("age_years", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("admin_fee_amount", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("security_type", sa.String(length=20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_column("security_type")
        batch_op.drop_column("admin_fee_amount")
        batch_op.drop_column("age_years")
        batch_op.drop_column("view_type")
        batch_op.drop_column("stratum")
        batch_op.drop_column("has_balcony")
