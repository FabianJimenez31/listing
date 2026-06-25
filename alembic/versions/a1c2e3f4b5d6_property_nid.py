"""property.nid — HubSpot-style numeric Record ID

Adds a big, opaque, auto-generated public identifier to properties, backed by a
Postgres sequence (``property_nid_seq``). Existing rows are backfilled by
creation order. On non-Postgres engines (the SQLite test suite builds its
schema from the ORM via ``create_all``, not from migrations) we just add the
column so a stray ``alembic upgrade`` there stays harmless.

Revision ID: a1c2e3f4b5d6
Revises: f6a0b3c5d7e9
Create Date: 2026-06-18 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1c2e3f4b5d6"
down_revision: Union[str, Sequence[str], None] = "f6a0b3c5d7e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEQ_START = 1000000001


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        with op.batch_alter_table("properties", schema=None) as batch_op:
            batch_op.add_column(sa.Column("nid", sa.BigInteger(), nullable=True))
        op.create_index("ix_properties_nid", "properties", ["nid"], unique=True)
        return

    # --- Postgres: native sequence is the authoritative NID generator ---
    op.execute(
        f"CREATE SEQUENCE IF NOT EXISTS property_nid_seq START WITH {_SEQ_START} INCREMENT BY 1"
    )
    op.add_column("properties", sa.Column("nid", sa.BigInteger(), nullable=True))

    # Backfill existing rows deterministically by creation order.
    op.execute(
        """
        WITH ordered AS (
            SELECT id, row_number() OVER (ORDER BY created_at ASC, id ASC) AS rn
            FROM properties
        )
        UPDATE properties p
        SET nid = 1000000000 + ordered.rn
        FROM ordered
        WHERE p.id = ordered.id
        """
    )
    # Advance the sequence past the highest backfilled value.
    op.execute(
        "SELECT setval('property_nid_seq', "
        "GREATEST((SELECT COALESCE(MAX(nid), 1000000000) FROM properties), 1000000000), true)"
    )
    # Lock it down: NOT NULL, DB-level default (safety net for non-ORM inserts),
    # unique index, and tie the sequence's lifecycle to the column.
    op.alter_column(
        "properties",
        "nid",
        nullable=False,
        server_default=sa.text("nextval('property_nid_seq')"),
    )
    op.create_index("ix_properties_nid", "properties", ["nid"], unique=True)
    op.execute("ALTER SEQUENCE property_nid_seq OWNED BY properties.nid")


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_properties_nid", table_name="properties")
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_column("nid")
    if bind.dialect.name == "postgresql":
        op.execute("DROP SEQUENCE IF EXISTS property_nid_seq")
