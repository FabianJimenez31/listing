"""portal entities: agencies, projects, partners, posts + property.agency_id, location.image_url

Revision ID: b1f2c3d4e5f6
Revises: 0477b061366e
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1f2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "0477b061366e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- agencies ---------------------------------------------------------
    op.create_table(
        "agencies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False),
        sa.Column("initials", sa.String(length=8), nullable=True),
        sa.Column("logo_url", sa.String(length=1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("whatsapp", sa.String(length=50), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("location_id", sa.String(length=36), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("agencies", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_agencies_location_id"), ["location_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_agencies_slug"), ["slug"], unique=True)

    # --- projects ---------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agency_id", sa.String(length=36), nullable=True),
        sa.Column("location_id", sa.String(length=36), nullable=True),
        sa.Column("property_type_id", sa.String(length=36), nullable=True),
        sa.Column("developer_name", sa.String(length=200), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("price_from", sa.BigInteger(), nullable=True),
        sa.Column("price_to", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("bedrooms_min", sa.Integer(), nullable=True),
        sa.Column("bedrooms_max", sa.Integer(), nullable=True),
        sa.Column("bathrooms_min", sa.Integer(), nullable=True),
        sa.Column("bathrooms_max", sa.Integer(), nullable=True),
        sa.Column("area_min_m2", sa.Float(), nullable=True),
        sa.Column("area_max_m2", sa.Float(), nullable=True),
        sa.Column("total_units", sa.Integer(), nullable=True),
        sa.Column("available_units", sa.Integer(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("address_street", sa.String(length=500), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_whatsapp", sa.String(length=50), nullable=True),
        sa.Column("cover_image_url", sa.String(length=1000), nullable=True),
        sa.Column("views_count", sa.Integer(), nullable=False),
        sa.Column("leads_count", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["property_type_id"], ["property_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_projects_agency_id"), ["agency_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_projects_location_id"), ["location_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_projects_property_type_id"), ["property_type_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_projects_slug"), ["slug"], unique=True)
        batch_op.create_index(batch_op.f("ix_projects_stage"), ["stage"], unique=False)
        batch_op.create_index(batch_op.f("ix_projects_status"), ["status"], unique=False)

    # --- project_images ---------------------------------------------------
    op.create_table(
        "project_images",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("cdn_url", sa.String(length=1000), nullable=False),
        sa.Column("thumb_url", sa.String(length=1000), nullable=True),
        sa.Column("alt_text", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("project_images", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_project_images_project_id"), ["project_id"], unique=False)

    # --- partners ---------------------------------------------------------
    op.create_table(
        "partners",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False),
        sa.Column("logo_url", sa.String(length=1000), nullable=True),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("partners", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_partners_slug"), ["slug"], unique=True)

    # --- posts ------------------------------------------------------------
    op.create_table(
        "posts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("author_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False),
        sa.Column("excerpt", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=1000), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("posts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_posts_author_id"), ["author_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_posts_category"), ["category"], unique=False)
        batch_op.create_index(batch_op.f("ix_posts_slug"), ["slug"], unique=True)
        batch_op.create_index(batch_op.f("ix_posts_status"), ["status"], unique=False)

    # --- new columns on existing tables -----------------------------------
    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("image_url", sa.String(length=1000), nullable=True))

    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.add_column(sa.Column("agency_id", sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f("ix_properties_agency_id"), ["agency_id"], unique=False)
        batch_op.create_foreign_key("fk_properties_agency_id", "agencies", ["agency_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Dropping the column also removes its FK constraint (Postgres drops it
    # automatically; SQLite batch mode recreates the table without it).
    with op.batch_alter_table("properties", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_properties_agency_id"))
        batch_op.drop_column("agency_id")

    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.drop_column("image_url")

    op.drop_table("posts")
    op.drop_table("partners")
    op.drop_table("project_images")
    op.drop_table("projects")
    op.drop_table("agencies")
