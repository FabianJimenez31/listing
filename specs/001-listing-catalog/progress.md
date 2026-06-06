# Progreso de Implementación — Listing

> Documento de avance. Se actualiza al cerrar cada etapa.
> Referencia: [spec.md](spec.md) · [plan.md](plan.md) · [tasks.md](tasks.md)

---

## Estado global

| Fase | Estado | Última parada |
|------|--------|---------------|
| 1 — Foundation & Setup | ✅ ENTREGADA | Dominio + specs + 335 tests verdes |
| 2 — Core Backend Logic | ✅ ENTREGADA | FastAPI 48 rutas + SQLAlchemy ORM + 395 tests |
| 2.1 — Backend extras    | ✅ ENTREGADA | Alembic + seeds + image upload + SEO + rate limit |
| 3 — Frontend React SPA | ✅ ENTREGADA | Vite + React 18 + SPA completa |
| 4 — Safeguards & Quality | 🔄 Parcial | Harness activo; Sonar pendiente sobre código real |
| 5 — Verification & Tests | 🔄 Parcial | Solo dominio; integración API pendiente |

---

## FASE 1 — Foundation & Setup ✅

**Commit**: pendiente de push

**Entregables:**
- 20 documentos de spec en `specs/001-listing-catalog/`
  - spec.md, plan.md, tasks.md, architecture.md, roles-permissions.md, data-model.md,
    property-lifecycle.md, media-pipeline.md, search-filters.md, property-detail.md,
    leads.md, banners-featured.md, seo.md, security.md, performance.md, ux-ui.md,
    api-contracts.md, validations.md, metrics.md, acceptance-criteria.md
- 13 módulos de dominio en `src/`
  - property.py, property_image.py, location.py, property_type.py, amenity.py, user.py,
    lead.py, banner.py, featured_property.py, favorite.py, audit_log.py, seo_metadata.py,
    property_view.py
- 13 archivos de tests en `tests/`
  - test_property.py (53), test_lead.py (34), test_location.py (43), test_banner.py (24),
    test_featured_property.py (21), test_user.py (24), test_property_image.py (23),
    test_seo_metadata.py (23), test_property_type.py (28), test_audit_log.py (15),
    test_amenity.py (14), test_favorite.py (13), test_property_view.py (13)
- **335 tests passing**, cobertura 100% en capa de dominio

---

## FASE 2 — Core Backend Logic 🔄

**Objetivo**: FastAPI + SQLAlchemy + JWT + RBAC + endpoints `/api/v1`

### Decisiones de implementación (Phase 2)

| Decisión | Valor |
|----------|-------|
| SQLAlchemy | 2.x sync (Session) — simplifica tests con TestClient |
| DB driver tests | SQLite (`:memory:`) — sin necesidad de Postgres para CI local |
| Coordenadas geo | `Float` lat/lng en ORM; PostGIS `Geography` se agrega via Alembic migration |
| JWT | `python-jose` HS256; access 30min / refresh 7d |
| Password | `passlib[bcrypt]` |
| Tests API | `TestClient` (starlette sync) + SQLite override |
| Redis | Integrado via env var `REDIS_URL`; deshabilitado si no está presente |

### Estructura de directorios (Phase 2)

```
src/
  __init__.py
  db/
    __init__.py
    engine.py          # Base, engine factory, get_db()
    models/
      __init__.py
      user_models.py   # User, Role, Permission, UserRole
      property_models.py  # Property, PropertyImage
      location_models.py  # Location
      catalog_models.py   # PropertyType, Amenity, PropertyAmenity
      lead_models.py      # Lead
      promotion_models.py # Banner, FeaturedProperty
      engagement_models.py # Favorite, PropertyView, AuditLog
      seo_models.py       # SeoMetadata
  schemas/
    __init__.py
    common.py           # Pagination, error envelope, base response
    auth_schemas.py
    user_schemas.py
    property_schemas.py
    location_schemas.py
    lead_schemas.py
    banner_schemas.py
  repositories/
    __init__.py
    base.py
    user_repo.py
    property_repo.py
    lead_repo.py
    banner_repo.py
  auth/
    __init__.py
    jwt_handler.py
    password.py
  api/
    __init__.py
    app.py
    deps.py
    error_handler.py
    routers/
      __init__.py
      auth.py         (POST /register, /login, /refresh, /logout)
      users.py        (GET/PUT /users/me, PATCH /users/:id/role)
      properties.py   (CRUD + lifecycle: submit/approve/reject/pause/reactivate/sold/rented/delete/duplicate)
      search.py       (GET /properties con filtros, paginación, geo)
      leads.py        (POST /leads, GET /leads admin)
      banners.py      (CRUD banners + featured)
      favorites.py    (GET/POST/DELETE /favorites)
      locations.py    (GET /locations)
      amenities.py    (GET /amenities)
      admin.py        (moderación, roles, métricas admin)
      metrics.py      (POST /metrics/event)
```

### Progreso Phase 2

- [x] Dependencias instaladas (`fastapi`, `sqlalchemy`, `alembic`, `python-jose`, `passlib`)
- [x] `requirements.txt` actualizado
- [x] `src/__init__.py`
- [x] `src/db/engine.py` — Base, engine, session factory
- [x] `src/db/models/` — 8 archivos ORM (16 entidades)
- [x] `src/auth/jwt_handler.py` + `src/auth/password.py`
- [x] `src/schemas/` — schemas Pydantic (common, auth, user, property, location, lead, banner)
- [x] `src/repositories/` — base + user + property + lead + banner repos
- [x] `src/api/app.py` + `deps.py` + `error_handler.py`
- [x] `src/api/routers/` — auth, users, properties, search, leads, banners, favorites, locations, amenities, admin, metrics
- [ ] Alembic migrations + seeds (roles, permissions, property_types, amenities)
- [ ] Tests de integración API (FastAPI TestClient)
- [ ] Redis rate limiting middleware
- [ ] Cola async workers (image resize, lead notifications)

### Última parada Phase 2

```
2026-06-06 — Phase 2 ENTREGADA y commiteada.
Commit: feat(001-listing-catalog): Phase 2 — backend FastAPI + SQLAlchemy + 41 API tests

Entregado:
  - 18 tablas ORM (SQLAlchemy 2.x sync)
  - 48 rutas /api/v1 operativas
  - JWT auth + bcrypt + RBAC dependency injection
  - 376 tests verdes (335 dominio + 41 API integración)

Pendiente para Phase 2.1 (próxima sesión):
  - Alembic: migraciones con up/down + seeds (roles, permisos, property_types, amenities)
  - Redis rate limiting middleware (SEC-R13)
  - Cola async workers (resize imágenes, notif leads)
  - Upload de imágenes a S3-compatible (endpoint POST /properties/:id/images)
  - Endpoint SEO: sitemap.xml, robots.txt, redirect_from[] → 301
  - Tests de migraciones Alembic (up/down)

Siguiente gran etapa: Phase 3 — Frontend React SPA (Vite, CSR).
```

---

## FASE 3 — Frontend React SPA ✅

**Commit**: `837183c feat(001-listing-catalog): Phase 3 — Frontend React SPA`

**Stack**: Vite 8 + React 18 + react-router-dom + react-helmet-async + axios

**Entregables:**
- `frontend/src/api/` — client.js (axios + auto-refresh interceptor), auth.js, properties.js, leads.js, admin.js
- `frontend/src/contexts/AuthContext.jsx` — sesión en localStorage, hasPermission/isAdmin
- `frontend/src/components/` — Header, Layout, PropertyCard, PropertyFilters, LeadForm, Spinner, Pagination
- Páginas públicas: HomePage (hero + búsqueda + destacados), SearchPage (filtros + grid + paginación), PropertyDetailPage (galería + specs + LeadForm + JSON-LD + OG), LoginPage, RegisterPage
- Panel agente: AgentDashboard (tabla con lifecycle), PropertyFormPage (CRUD + image upload), LeadsPage
- Panel admin: AdminDashboard (stats), ModerationPage (aprobar/rechazar)
- Vite proxy al backend + Build limpio (103 módulos, 337 KB JS)

### Última parada Phase 3

```
2026-06-06 — Phase 3 ENTREGADA y commiteada.
Commit: feat(001-listing-catalog): Phase 3 — Frontend React SPA (Vite + react-helmet-async)

Pendiente para Phase 4:
  - SonarQube Quality Gate verde sobre backend real (make sonar-check)
  - CI apuntando a SonarQube hosteado (ci-quality-gate.yml)
  - Gate validate-enums reactivado (cuando exista schema DB real en producción)

Pendiente para Phase 5 / mejoras:
  - Admin: páginas de banners, destacados, usuarios (banners.jsx, featured.jsx, users.jsx)
  - Frontend: página de favorites, compartir propiedad, reportar propiedad
  - Tests e2e frontend (Playwright o Cypress)
  - Deploy: Dockerfile + docker-compose (PostgreSQL + Redis + backend + frontend nginx)
```

---

## FASE 4 — Safeguards & Quality 🔄

- [x] Hook tamaño archivo activo (1000L límite)
- [x] validate_structure.py activo
- [x] Secret scanner en pre-commit
- [x] Branch convention gate
- [x] Spec gate (spec/plan/tasks >50B)
- [ ] SonarQube Quality Gate sobre código backend real
- [ ] CI apuntando a SonarQube hosteado
- [ ] Gate validate-enums reactivado (cuando exista schema DB real)

---

## FASE 5 — Verification & Tests 🔄

- [x] 335 tests unitarios dominio (pytest)
- [ ] Tests integración API (TestClient + SQLite)
- [ ] Tests migraciones Alembic (up/down)
- [ ] Tests cobertura objetivo SonarQube

---

## Cómo retomar

1. `git log --oneline -5` — ver último commit
2. `cat specs/001-listing-catalog/progress.md` — este archivo
3. `pytest -q` — verificar que la suite verde sigue verde
4. Continuar en la sección "Última parada" de la fase en curso
