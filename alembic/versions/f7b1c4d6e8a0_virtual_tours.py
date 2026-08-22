"""virtual tours, scenes, hotspots, and generation attempts

Revision ID: f7b1c4d6e8a0
Revises: e2f3a4b5c6d7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f7b1c4d6e8a0"
down_revision: Union[str, Sequence[str], None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "virtual_tours",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("property_id", sa.String(36), nullable=True),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("start_scene_id", sa.String(36), nullable=True),
        sa.Column("ai_disclaimer_ack", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(property_id IS NOT NULL AND project_id IS NULL) OR "
            "(property_id IS NULL AND project_id IS NOT NULL)",
            name="ck_virtual_tours_single_owner",
        ),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_virtual_tours_status", "virtual_tours", ["status"])
    op.create_index(
        "uq_virtual_tours_property_id", "virtual_tours", ["property_id"], unique=True,
        postgresql_where=sa.text("property_id IS NOT NULL"),
        sqlite_where=sa.text("property_id IS NOT NULL"),
    )
    op.create_index(
        "uq_virtual_tours_project_id", "virtual_tours", ["project_id"], unique=True,
        postgresql_where=sa.text("project_id IS NOT NULL"),
        sqlite_where=sa.text("project_id IS NOT NULL"),
    )

    op.create_table(
        "virtual_tour_scenes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tour_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("state", sa.String(10), nullable=False),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("thumb_storage_key", sa.String(500), nullable=True),
        sa.Column("pano_url", sa.String(1000), nullable=True),
        sa.Column("thumb_url", sa.String(1000), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("initial_yaw", sa.Float(), nullable=False),
        sa.Column("initial_pitch", sa.Float(), nullable=False),
        sa.Column("hfov_deg", sa.Float(), nullable=False),
        sa.Column("vfov_deg", sa.Float(), nullable=False),
        sa.Column("source_image_ids", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(60), nullable=True),
        sa.Column("provider_model", sa.String(80), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 5), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tour_id"], ["virtual_tours.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_virtual_tour_scenes_tour_id", "virtual_tour_scenes", ["tour_id"])
    op.create_index("ix_virtual_tour_scenes_state", "virtual_tour_scenes", ["state"])

    op.create_table(
        "virtual_tour_hotspots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("from_scene_id", sa.String(36), nullable=False),
        sa.Column("to_scene_id", sa.String(36), nullable=False),
        sa.Column("yaw", sa.Float(), nullable=False),
        sa.Column("pitch", sa.Float(), nullable=False),
        sa.Column("label", sa.String(120), nullable=True),
        sa.ForeignKeyConstraint(
            ["from_scene_id"], ["virtual_tour_scenes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["to_scene_id"], ["virtual_tour_scenes.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_virtual_tour_hotspots_from_scene_id", "virtual_tour_hotspots", ["from_scene_id"]
    )
    op.create_index(
        "ix_virtual_tour_hotspots_to_scene_id", "virtual_tour_hotspots", ["to_scene_id"]
    )

    op.create_table(
        "virtual_tour_generation_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scene_id", sa.String(36), nullable=False),
        sa.Column("input_image_ids", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(60), nullable=False),
        sa.Column("provider_model", sa.String(80), nullable=False),
        sa.Column("quality", sa.String(20), nullable=False),
        sa.Column("output_size", sa.String(30), nullable=False),
        sa.Column("seam_pass", sa.Boolean(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 5), nullable=True),
        sa.Column("actual_cost_usd", sa.Numeric(10, 5), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["scene_id"], ["virtual_tour_scenes.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_virtual_tour_generation_attempts_scene_id",
        "virtual_tour_generation_attempts", ["scene_id"],
    )
    op.create_index(
        "ix_virtual_tour_generation_attempts_state",
        "virtual_tour_generation_attempts", ["state"],
    )


def downgrade() -> None:
    op.drop_table("virtual_tour_generation_attempts")
    op.drop_table("virtual_tour_hotspots")
    op.drop_table("virtual_tour_scenes")
    op.drop_table("virtual_tours")
