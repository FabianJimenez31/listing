# Tasks — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #21.

**Branch**: `feature/001-listing-catalog` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Resumen

Checklist por fases del proyecto inmobiliario **Listing** (FastAPI + PostgreSQL/PostGIS
+ React SPA). Cubre DoD #21 (especificacion clara, modular, verificable, lista para
backlog). Estado: la **Fase 1** (especificacion + esqueleto de dominio + tests) esta
ENTREGADA; las Fases 2-5 son trabajo futuro. Convencion: `[x]` hecho · `[/]` en curso
· `[ ]` pendiente. Cada item de Fase 2/3 mapea a reglas `<PREFIJO>-R#` y a `FR-###`
definidos en los documentos de spec.

---

## Phase 1: Foundation & Setup  `[x]`

Especificacion completa + esqueleto de dominio del harness + suite de dominio verde.

- [x] **Documentos de especificacion escritos** (17 docs, `specs/001-listing-catalog/`)
  - [x] `spec.md` — indice maestro, FR-###/NFR-###, AC-01..AC-23
  - [x] `plan.md` — estrategia tecnica y stack
  - [x] `architecture.md` — arquitectura general, modulos, escalabilidad (DoD #1, #2, #20)
  - [x] `data-model.md` — 16 entidades, campos, relaciones, indices, validaciones (DoD #4)
  - [x] `roles-permissions.md` — matriz roles/permisos, RBAC-R* (DoD #3)
  - [x] `property-lifecycle.md` — maquina de estados, LIFECYCLE-R* (DoD #5, #6)
  - [x] `media-pipeline.md` — imagenes/media, MEDIA-R* (DoD #7)
  - [x] `search-filters.md` — filtros/orden/paginacion, SEARCH-R* (DoD #8)
  - [x] `property-detail.md` — pagina de detalle, DETAIL-R* (DoD #9)
  - [x] `leads.md` — leads y estados, LEAD-R* (DoD #10)
  - [x] `banners-featured.md` — banners + destacados, BANNER-R*/FEATURED-R* (DoD #11, #12)
  - [x] `seo.md` — SEO/canonical/redirects/JSON-LD, SEO-R* (DoD #13)
  - [x] `security.md` — seguridad/RBAC/rate-limit, SEC-R* (DoD #14)
  - [x] `performance.md` — performance/cache/CDN, PERF-R* (DoD #15)
  - [x] `ux-ui.md` — UX/UI mobile-first, UX-R* (DoD #16)
  - [x] `api-contracts.md` — endpoints API, envelope, paginacion (DoD #17)
  - [x] `validations.md` — validaciones y codigos de error, VALID-R* (DoD #18)
  - [x] `metrics.md` — metricas/engagement/audit (DoD #19)
- [x] **Esqueleto de dominio (harness reference) + tests**
  - [x] `src/listing_catalog.py` — `Listing` + `ListingStatus` + `Catalog` (modulo de referencia)
  - [x] `tests/test_listing_catalog.py` — 7 tests de dominio, **verde** (`pytest -q` -> 7 passed)
  - [x] `pytest.ini` — markers `unit`/`integration`/`critical`
  - [x] Harness de calidad bootstrap (hooks, pre-commit, sonar helper, Makefile)
- [x] **16 entidades modeladas en 13 modulos de dominio** (capa framework-agnostica:
      dataclasses + enums + validaciones en `__post_init__`; agrupados por capacidad, sin shells
      genericos `models/`/`services/`). Cada modulo con su `tests/test_<modulo>.py` espejo. El
      reference module `listing_catalog.py` se conserva como sample del harness:
  - [x] `src/user.py` — `User` + `Role` + `Permission` (`PermissionCode`) (entidades 1, 2, 3) + RBAC
  - [x] `src/property.py` — `Property` + `Money` + enums operacion/tipo/condicion/estado/moneda + ciclo de vida (entidad 4)
  - [x] `src/property_image.py` — `PropertyImage` + enums `ImageRole`, `MediaKind` (entidad 5)
  - [x] `src/location.py` — `Location` + `Coordinates` (entidad 6)
  - [x] `src/property_type.py` — `PropertyType` (entidad 7)
  - [x] `src/amenity.py` — `Amenity` + `PropertyAmenity` M2M (entidades 8, 9)
  - [x] `src/lead.py` — `Lead` + enums `LeadStatus`, `LeadChannel` (entidad 10)
  - [x] `src/banner.py` — `Banner` + enum `BannerPosition` (entidad 11)
  - [x] `src/favorite.py` — `Favorite` + `FavoriteSet` (entidad 12)
  - [x] `src/featured_property.py` — `FeaturedProperty` + enum `FeaturedScope` (entidad 13)
  - [x] `src/audit_log.py` — `AuditLog` + enum `AuditAction` (entidad 14, append-only)
  - [x] `src/seo_metadata.py` — `SeoMetadata` (entidad 15)
  - [x] `src/property_view.py` — `PropertyView` + enums `MetricEventType`, `ViewSource` (entidad 16)
  - [x] **Suite de dominio completa verde:** `pytest -q` -> **335 passed** (13 modulos + reference)

---

## Phase 2: Core Backend Logic  `[ ]`

Backend FastAPI sobre PostgreSQL 16 + PostGIS + pg_trgm + Redis. Implementa FR-001..129.

- [ ] **Persistencia (SQLAlchemy + Alembic)**
  - [ ] Modelos ORM para las 16 entidades (UUID v4, timestamptz UTC, soft delete `deleted_at`)
  - [ ] `price_amount BIGINT` (minor units) + `currency CHAR(3)`; NUNCA float
  - [ ] Indices: B-tree FK/`slug`/`status`; GiST PostGIS en `location_point`; GIN/pg_trgm
        en `title`/`description`; parcial `status='published'` (ver data-model.md)
  - [ ] Migraciones Alembic + seeds (roles, permisos, property_types, amenities)
  - [ ] Repositorios por entidad (filtran siempre `deleted_at IS NULL`)
- [ ] **Auth & RBAC** (FR-001..019; RBAC-R*, SEC-R*)
  - [ ] JWT Bearer access+refresh; register/login/refresh/logout; password hash
  - [ ] Dependencia de permisos `resource:action`; lecturas publicas sin auth
  - [ ] Invariante ultimo SUPERADMIN (RBAC-R13) -> `409 last_superadmin`
- [ ] **Properties + lifecycle** (FR-020..049; LIFECYCLE-R*)
  - [ ] CRUD + generacion de slug `{operation}-{kind}-{title-kebab}-{shortid}`
  - [ ] Maquina de estados (create/submit/approve/reject/pause/reactivate/sold/rented/
        delete/duplicate); guards de permiso y de `operation_type`
  - [ ] Re-revision en edicion material de `PUBLISHED` (regla a definir, ver Open Questions)
- [ ] **Media / imagenes** (FR-050..059; MEDIA-R*)
  - [ ] Upload a S3-compatible + CDN; thumbnails async (workers); constraint 1 sola MAIN
  - [ ] Recompactar `position` tras borrar/reemplazar (MEDIA-R13)
- [ ] **Search / filtros / detalle** (FR-060..079; SEARCH-R*, DETAIL-R*)
  - [x] Hotfix filtros: NID desde `q`, texto sin tildes/puntuacion, ciudad por subarbol y precio formateado con moneda
  - [x] Autocompletado predictivo del buscador principal para propiedades y proyectos
  - [ ] Busqueda geoespacial PostGIS + full-text pg_trgm; filtros/orden/paginacion
        `?page=&page_size=`; params desconocidos ignorados (SEARCH-R13)
  - [ ] Endpoint de detalle publico (solo `PUBLISHED` -> 200; resto 404/301/410)
- [ ] **Leads** (FR-080..089; LEAD-R*): captura por canal, estados, consent, asignacion
- [ ] **Banners & Featured** (FR-090..099; BANNER-R*/FEATURED-R*): elegibilidad por
      `(position, context)`, fallback `data:[]` (BANNER-R13), limites por scope
- [ ] **SEO backend** (FR-100..109; SEO-R*): canonical, `redirect_from[]` 301 (SEO-R13),
      JSON-LD, sitemap; politica SOLD/RENTED 301/410
- [ ] **Favoritos / compartir / reportar** (FR-110..119)
  - [x] Compartir como accion secundaria fuera de la galeria en propiedades y proyectos
  - [x] Compartir directamente desde las cards destacadas del home sin interferir con su enlace
- [ ] **Admin / moderacion / metricas / audit** (FR-120..129)
  - [x] Alta idempotente de departamentos/estados y validacion de su padre en el arbol de ubicaciones
  - [ ] Almacen de eventos `PropertyView` (MetricEventType/ViewSource) + contadores
        denormalizados async; `AuditLog` append-only
- [ ] **Plataforma transversal**
  - [ ] Error envelope `{"error":{"code","message","details"}}` global
  - [ ] Rate limiting Redis (login/register/reset/lead/search/upload/metrics) -> 429
        + `Retry-After` (SEC-R13)
  - [ ] Cache Redis de lecturas (detalle, listados, banners/destacados) + invalidacion
  - [ ] Cola async + workers (resize imagenes, notif leads, reindex, sitemap)

---

## Phase 3: Frontend Integration  `[ ]`

React 18 SPA (Vite, CSR), mobile-first (DoD #16; UX-R*). Consume `/api/v1`.

- [ ] Setup Vite + router + cliente HTTP (manejo del error envelope) + estado/auth
- [ ] Home publica: hero, banners (`HOME_HERO`/`HOME_INLINE`), destacados (`HOME`)
- [ ] Listado/busqueda: filtros, orden, paginacion, mapa; estados vacios
- [ ] Detalle de propiedad: galeria/media, CTA (`primary_cta`), favorito, formulario de lead
- [ ] Panel de agente: alta/edicion, subida de imagenes, ciclo de vida, leads, metricas propias
- [ ] Panel de admin: moderacion (approve/reject), banners, destacados, roles/permisos,
      ubicaciones, metricas globales, audit (DoD #20: administrable sin tocar codigo)
- [ ] SEO en cliente: `react-helmet` (meta/OG/canonical), breadcrumbs + JSON-LD
- [ ] Imagenes responsivas (`thumb_url`/`cdn_url`), lazy-load, AVIF/WebP (PERF-R13)

---

## Phase 4: Safeguards & Quality  `[/]`

- [x] Hook de tamano de archivo activo (`check-file-size.sh`, limite 1000 / aviso 800)
- [x] `validate_structure.py` (sin `utils.py`/`helpers.py`/dump modules); pre-commit valido
- [x] Secret scanner en pre-commit; `.env.example` / `.env.local` git-ignored
- [x] Convencion de branch + gate spec-driven (spec/plan/tasks presentes)
- [x] Helper de servidor SonarQube local + `make sonar-up`/`sonar-check`
- [ ] Quality Gate SonarQube **verde** sobre codigo backend real (cobertura + duplicacion)
- [ ] CI `ci-quality-gate.yml` apuntando a SonarQube hosteado (secrets del repo)
- [ ] Re-activar gate `validate-enums` cuando exista esquema DB + enums de dominio

---

## Phase 5: Verification & Tests  `[/]`

- [x] Tests de dominio: 13 modulos + reference module — **335 passed** (`pytest -q`)
- [x] Tests unitarios por modulo de dominio (espejo de los 13 modulos de Fase 1)
- [ ] Tests de integracion / contrato de API (FastAPI TestClient): auth, lifecycle,
      search geoespacial, leads, banners/featured, SEO redirects, RBAC, rate limiting
- [ ] Tests de migraciones Alembic (up/down) + fixtures de DB (Postgres + PostGIS)
- [ ] Cobertura objetivo del Quality Gate (umbral SonarQube) + casos `critical`

---

## Progress Tracking

| Fase | Estado | Detalle |
|------|--------|---------|
| 1 — Foundation & Setup | `[x]` entregada | 17 docs de spec + capa de dominio (13 modulos, 16 entidades) + tests (**335 passed**) + harness activo |
| 2 — Core Backend Logic | `[ ]` pendiente | Modelado de las 16 entidades en backend FastAPI segun los docs |
| 3 — Frontend Integration | `[ ]` pendiente | SPA React aun no iniciada |
| 4 — Safeguards & Quality | `[/]` parcial | Harness local OK; falta gate Sonar sobre codigo real + CI hosteado |
| 5 — Verification & Tests | `[/]` parcial | Solo dominio cubierto; faltan integracion/API + cobertura objetivo |

**Estado actual:** especificacion DoD-completa (DoD #21) lista para backlog y **capa de
dominio entregada** — las 16 entidades del contrato modeladas en 13 modulos con validaciones
y tests (`pytest -q` -> **335 passed**). El reference module `listing_catalog.py` se conserva
como sample del harness. Siguiente paso accionable: Fase 2 (persistencia SQLAlchemy/Alembic + API FastAPI).

## Open Questions

- **Re-revision en edicion de `PUBLISHED`:** definir que cambios materiales (precio,
  ubicacion, operacion) fuerzan volver a `PENDING` vs edicion in-place (ver property-lifecycle.md).
- **Agrupacion de entidades en modulos:** `Role`+`Permission` viven en `user.py` y
  `Amenity`+`PropertyAmenity` en `amenity.py` (capacidad afin), por lo que no hay `role.py`
  separado. La persistencia (Fase 2) mapea 1 tabla por entidad, independientemente del modulo.
