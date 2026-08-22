"""Exports router: download the loaded inventory as a spreadsheet."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Response, status

from src.api.deps import CurrentUser, DB
from src.exports.property_export import (
    CSV_MEDIA_TYPE,
    XLSX_MEDIA_TYPE,
    build_rows,
    to_csv,
    to_xlsx,
)
from src.repositories.location_repo import LocationRepository
from src.repositories.property_repo import PropertyRepository

router = APIRouter(prefix="/exports", tags=["exports"])

# Upper bound for a single download: a spreadsheet is built in memory, and no
# real portal exports more than this in one click.
MAX_ROWS = 5000


@router.get("/properties")
def export_properties(
    db: DB,
    current_user: CurrentUser,
    file_format: str = Query("xlsx", alias="format", pattern="^(xlsx|csv)$"),
    all_: bool = Query(False, alias="all", description="Admins: every owner's properties"),
    status_filter: str | None = Query(None, alias="status", description="Only this publication status"),
    q: str | None = Query(None, description="Free-text search (title/description)"),
    nid: int | None = Query(None, description="Filter by numeric Record ID"),
):
    """Spreadsheet of the inventory the caller is allowed to see.

    Admins (`property:read_all`) pass ``all=true`` for the whole portal; everyone
    else gets their own listings, in every status. Mirrors the filters of the
    back-office properties table so the file matches what is on screen.
    """
    is_admin = current_user.has_permission("property:read_all")
    if all_ and not is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Permission required: property:read_all")

    owner_id = None if all_ else current_user.id
    properties, _ = PropertyRepository(db).search(
        status=status_filter,
        owner_id=owner_id,
        text=q,
        nid=nid,
        page=1,
        page_size=MAX_ROWS,
        load_owner=True,
    )

    rows = build_rows(
        properties,
        city_names=LocationRepository(db).city_name_by_location(),
        site_url=os.getenv("SITE_URL", ""),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if file_format == "csv":
        content, media_type = to_csv(rows), CSV_MEDIA_TYPE
    else:
        content, media_type = to_xlsx(rows), XLSX_MEDIA_TYPE

    filename = f"inventario-{stamp}.{file_format}"
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            # The browser only sees whitelisted headers on a cross-origin XHR.
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
