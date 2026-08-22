"""normalize legacy hotspot angles (yaw wrap, floor pitch band)

Revision ID: a9c3e7d1b5f2
Revises: f7b1c4d6e8a0

Legacy rows were written with raw pixel-math angles (yaws of thousands of
degrees, pitches beyond the poles), which collapses every arrow into the same
visual spot in the viewer. Wrap yaw into (-180, 180] and clamp pitch into the
floor band used by the viewer.

Row-by-row through Python instead of vendor trig SQL so the migration runs on
both Postgres (production) and SQLite (the migration test harness).
"""
import math
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a9c3e7d1b5f2"
down_revision: Union[str, Sequence[str], None] = "f7b1c4d6e8a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FLOOR_PITCH_LOW = math.radians(-85)
FLOOR_PITCH_HIGH = math.radians(-60)


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, yaw, pitch FROM virtual_tour_hotspots")
    ).fetchall()
    for row in rows:
        yaw = math.atan2(math.sin(row.yaw), math.cos(row.yaw))
        pitch = max(FLOOR_PITCH_LOW, min(FLOOR_PITCH_HIGH, row.pitch))
        conn.execute(
            sa.text("UPDATE virtual_tour_hotspots SET yaw = :yaw, pitch = :pitch WHERE id = :id"),
            {"yaw": yaw, "pitch": pitch, "id": row.id},
        )


def downgrade() -> None:
    # Data normalization is not reversible; original corrupt values are gone.
    pass
