"""FastAPI application factory.

Usage:
  uvicorn src.api.app:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.error_handler import register_error_handlers
from src.api.routers import (
    admin,
    agencies,
    amenities,
    auth,
    banners,
    blog,
    catalog,
    exports,
    favorites,
    images,
    leads,
    locations,
    metrics,
    partners,
    projects,
    properties,
    search,
    seo,
    settings,
    users,
    tour_billing,
    virtual_tours,
)
from src.middleware.rate_limit import RateLimitMiddleware

_API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Listing API",
        version="1.0.0",
        description="Real estate listing platform API",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production via ALLOWED_ORIGINS env var
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)

    register_error_handlers(app)

    # Auth & users
    app.include_router(auth.router, prefix=_API_PREFIX)
    app.include_router(users.router, prefix=_API_PREFIX)

    # Properties: search router MUST be mounted before properties router
    # so GET /api/v1/properties matches search, not a literal {property_id} param.
    app.include_router(search.router, prefix=_API_PREFIX)
    app.include_router(properties.router, prefix=_API_PREFIX)

    # Projects (developments / preventa)
    app.include_router(projects.router, prefix=_API_PREFIX)

    # Catalog
    app.include_router(locations.router, prefix=_API_PREFIX)
    app.include_router(amenities.router, prefix=_API_PREFIX)
    app.include_router(catalog.router, prefix=_API_PREFIX)

    # Directory
    app.include_router(agencies.router, prefix=_API_PREFIX)
    app.include_router(partners.router, prefix=_API_PREFIX)

    # Content
    app.include_router(blog.router, prefix=_API_PREFIX)

    # Engagement
    app.include_router(leads.router, prefix=_API_PREFIX)
    app.include_router(favorites.router, prefix=_API_PREFIX)

    # Promotions
    app.include_router(banners.router, prefix=_API_PREFIX)

    # Images
    app.include_router(images.router, prefix=_API_PREFIX)
    app.include_router(virtual_tours.router, prefix=_API_PREFIX)

    # Admin & metrics
    app.include_router(admin.router, prefix=_API_PREFIX)
    app.include_router(metrics.router, prefix=_API_PREFIX)
    app.include_router(exports.router, prefix=_API_PREFIX)
    app.include_router(tour_billing.router, prefix=_API_PREFIX)

    app.include_router(settings.router, prefix=_API_PREFIX)

    # SEO (no prefix — served at root: /sitemap.xml, /robots.txt)
    app.include_router(seo.router)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "listing-api"}

    return app


# Module-level instance for ASGI server (uvicorn src.api.app:app)
app = create_app()
