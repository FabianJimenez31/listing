"""SEO endpoints: sitemap.xml, robots.txt, slug redirects.

GET /sitemap.xml   — dynamic XML sitemap of published properties + static pages
GET /robots.txt    — robots configuration
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import Response

from src.api.deps import DB
from src.db.models.property_models import PropertyORM

router = APIRouter(tags=["seo"])

_SITE_URL = os.getenv("SITE_URL", "https://listing.example.com")
_ROBOTS_DISALLOW_PATHS = [
    "/api/",
    "/admin/",
    "/static/",
]


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------

@router.get("/robots.txt", include_in_schema=False)
def robots_txt():
    disallow_lines = "\n".join(f"Disallow: {p}" for p in _ROBOTS_DISALLOW_PATHS)
    body = f"""User-agent: *
Allow: /
{disallow_lines}

Sitemap: {_SITE_URL}/sitemap.xml
"""
    return Response(content=body.strip(), media_type="text/plain")


# ---------------------------------------------------------------------------
# sitemap.xml
# ---------------------------------------------------------------------------

def _xml_escape(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _url_entry(loc: str, lastmod: datetime | None = None, priority: str = "0.8") -> str:
    lastmod_tag = ""
    if lastmod:
        lastmod_tag = f"\n    <lastmod>{lastmod.strftime('%Y-%m-%d')}</lastmod>"
    return (
        f"  <url>\n"
        f"    <loc>{_xml_escape(loc)}</loc>{lastmod_tag}\n"
        f"    <priority>{priority}</priority>\n"
        f"  </url>"
    )


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml(db: DB):
    """Dynamic sitemap including all published properties and static pages."""
    entries: list[str] = []

    # Static pages
    static_pages = [
        ("/", "1.0"),
        ("/propiedades", "0.9"),
        ("/contacto", "0.5"),
    ]
    for path, priority in static_pages:
        entries.append(_url_entry(f"{_SITE_URL}{path}", priority=priority))

    # Published properties
    props = (
        db.query(PropertyORM)
        .filter(
            PropertyORM.status == "published",
            PropertyORM.deleted_at.is_(None),
        )
        .order_by(PropertyORM.updated_at.desc())
        .limit(50000)  # sitemap URL limit per spec
        .all()
    )
    for prop in props:
        # Canonical public URL is the numeric Record ID (NID), HubSpot-style.
        url = f"{_SITE_URL}/propiedades/{prop.nid}"
        entries.append(_url_entry(url, lastmod=prop.updated_at, priority="0.8"))

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>"
    )
    return Response(content=body, media_type="application/xml")
