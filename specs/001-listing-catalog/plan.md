# Implementation Plan: 001-listing-catalog

**Branch**: `001-listing-catalog` | **Date**: 2026-06-06 | **Spec**: specs/001-listing-catalog/spec.md

## Summary

Este plan define la estrategia tecnica para construir **Listing**, un sistema de
publicacion inmobiliaria multi-rol con catalogo publico, panel de agente, panel de
administracion y backend API. El enfoque es **incremental por capas**, priorizando
una base de dominio solida y verificable antes de exponer superficie de red o UI.

Orden de construccion:

1. **Capa de dominio (framework-agnostica) primero.** Las 16 entidades del CONTRATO
   se modelan como modulos Python puros en `src/`: dataclasses/enums + reglas de
   negocio (maquina de estados de `Property`, validaciones, invariantes como "una
   sola MAIN por propiedad"). Esta capa no depende de FastAPI, SQLAlchemy ni de la
   base de datos, lo que la hace 100% testeable con `pytest` y la convierte en la
   fuente de verdad de las reglas (`LIFECYCLE-R#`, `VALID-R#`, `RBAC-R#`).
2. **Capa de API (FastAPI) despues.** Una vez estabilizado el dominio, se añade la
   persistencia (SQLAlchemy + Alembic + PostGIS), el mapeo Pydantic (request/response
   schemas, error envelope, paginacion), autenticacion JWT y los endpoints
   `/api/v1/*`. Esta capa **adapta** el dominio: no reimplementa reglas.
3. **Frontend React SPA al final.** SPA con render en cliente (CSR) sobre Vite,
   `react-helmet-async` para SEO en el detalle, consumiendo la API publica sin auth
   para lecturas y JWT Bearer para paneles.

Este documento (DoD #1 Arquitectura general, #23 Output limpio/modular/produccion)
fija el alcance del **paso 1**: entregar la capa de dominio y la especificacion
completa. La API y el frontend quedan **documentados como trabajo futuro** dentro de
las specs y se implementaran en branches posteriores.

## Technical Context

- **Languages/Versions**: Python 3.13 (dominio + API), React 18 (SPA), Node.js 20 (toolchain Vite/Vitest).
- **Primary Dependencies**:
  - Dominio/API: FastAPI, SQLAlchemy 2.x, Pydantic 2.x, Alembic (migraciones), geoalchemy2 (geography/PostGIS), redis-py (cache + rate limit), boto3 (object storage S3-compatible + CDN).
  - Frontend: Vite, React 18, react-helmet-async (meta/OG/JSON-LD por ruta).
  - Calidad/test: pytest, pytest-cov.
- **Storage/Databases**: PostgreSQL 16 + PostGIS (geografia, `location_point geography(POINT,4326)`) + pg_trgm (busqueda fuzzy de texto); Redis (cache de listados y rate limiting); almacenamiento de objetos S3-compatible servido via CDN para imagenes/media.
- **Testing Frameworks**: pytest (dominio Python + futura API), Vitest (frontend React).
- **Target Platforms**: servidor Linux (API + workers); navegadores web modernos, diseño **mobile-first** (SPA responsive).

## Proposed Changes

Los cambios se agrupan por capa. El alcance **implementado en este branch** es la
capa de dominio y los artefactos de especificacion; la capa API y el frontend se
listan como trabajo futuro al final de esta seccion.

### Capa de dominio (src/)

Se añaden **13 modulos nuevos**, uno por entidad/familia de entidades del CONTRATO.
Cada modulo es un archivo enfocado y de responsabilidad unica (PascalCase para
clases, snake_case para campos, enums con valores string). El modulo existente
`src/listing_catalog.py` (referencia del harness) se conserva como demo del pipeline
de calidad y **convive** con estos modulos de dominio (no se elimina).

#### [NEW] property.py — [file:///root/listing/src/property.py](file:///root/listing/src/property.py)
Entidad central `Property` + enums `OperationType`, `PropertyKind`, `PropertyCondition`, `PublicationStatus`. Implementa la **maquina de estados** (DRAFT→PENDING→PUBLISHED→PAUSED→SOLD/RENTED, REJECTED, DELETED soft) con sus transiciones (`submit_for_review`, `approve`, `reject`, `pause`, `reactivate`, `mark_sold`, `mark_rented`, `soft_delete`, `duplicate`), reglas de visibilidad publica (solo PUBLISHED=200) y dinero en `price_amount` BIGINT minor units + `currency`.

#### [NEW] property_image.py — [file:///root/listing/src/property_image.py](file:///root/listing/src/property_image.py)
`PropertyImage` + enums `ImageRole` (MAIN/GALLERY) y `MediaKind` (IMAGE/VIDEO/FLOOR_PLAN/VIRTUAL_TOUR). Invariante "una sola MAIN por propiedad", orden por `position`, metadatos (`cdn_url`, `thumb_url`, `width`, `height`, `bytes`, `content_type`, `alt_text`).

#### [NEW] location.py — [file:///root/listing/src/location.py](file:///root/listing/src/location.py)
`Location` jerarquica (`parent_id` self-ref) con pais/estado/ciudad/localidad/barrio, `slug` unico (regex del CONTRATO), `center_point` geografico e `is_active`.

#### [NEW] property_type.py — [file:///root/listing/src/property_type.py](file:///root/listing/src/property_type.py)
`PropertyType` catalogo administrable (`code` = `PropertyKind`, `name`, `slug`, `icon`, `is_active`) para gestion "sin tocar codigo".

#### [NEW] amenity.py — [file:///root/listing/src/amenity.py](file:///root/listing/src/amenity.py)
`Amenity` (`code` unico, `name`, `category`, `icon`, `is_active`) y la relacion M2M `PropertyAmenity` (PK compuesta property_id+amenity_id, `value` opcional).

#### [NEW] user.py — [file:///root/listing/src/user.py](file:///root/listing/src/user.py)
`User`, `Role`, `Permission` y el RBAC: jerarquia VISITOR<REGISTERED_USER<AGENT<ADMIN<SUPERADMIN, codigos de permiso `resource:action` y resolucion de permisos efectivos (`RBAC-R#`).

#### [NEW] lead.py — [file:///root/listing/src/lead.py](file:///root/listing/src/lead.py)
`Lead` + enums `LeadStatus` (NEW/CONTACTED/NEGOTIATING/CLOSED/DISCARDED) y `LeadChannel` (FORM/WHATSAPP/CALL/VISIT). Estados del lead, consentimiento (`consent_given`/`consent_text`) y datos de origen (utm, source_ip, user_agent).

#### [NEW] banner.py — [file:///root/listing/src/banner.py](file:///root/listing/src/banner.py)
`Banner` + enum `BannerPosition`. Segmentacion por localidad/ciudad/operacion/kind, ventana `starts_at`/`ends_at`, `priority`, `is_active` y contadores denormalizados (`impressions_count`, `clicks_count`).

#### [NEW] featured_property.py — [file:///root/listing/src/featured_property.py](file:///root/listing/src/featured_property.py)
`FeaturedProperty` + enum `FeaturedScope` (HOME/SEARCH_RESULTS/LOCALITY). Regla: `locality_id` requerido si `scope=LOCALITY`; unicidad por propiedad; ventana de vigencia y prioridad.

#### [NEW] favorite.py — [file:///root/listing/src/favorite.py](file:///root/listing/src/favorite.py)
`Favorite` (user_id, property_id, created_at) con restriccion `Unique(user_id, property_id)` para gestion de guardados del usuario registrado.

#### [NEW] audit_log.py — [file:///root/listing/src/audit_log.py](file:///root/listing/src/audit_log.py)
`AuditLog` append-only + enum `AuditAction` (create/update/.../config_change). Captura `actor_id`, `entity_type`, `entity_id`, `before`/`after` (json), ip y user_agent para trazabilidad y moderacion.

#### [NEW] seo_metadata.py — [file:///root/listing/src/seo_metadata.py](file:///root/listing/src/seo_metadata.py)
`SeoMetadata` polimorfica (`entity_type`/`entity_id`): meta/OG, `canonical_url`, `jsonld`, `robots` (default "index,follow") y `redirect_from` (slugs viejos) para politica 301/410.

#### [NEW] property_view.py — [file:///root/listing/src/property_view.py](file:///root/listing/src/property_view.py)
`PropertyView` (almacen de eventos de engagement) + enums `MetricEventType` (VIEW/CTA_CLICK/WHATSAPP_CLICK/CALL_CLICK/VISIT_REQUEST/SHARE/FAVORITE) y `ViewSource` (ORGANIC/SEARCH/FEATURED/DIRECT/SHARE). Base de las metricas; contadores denormalizados viven en Property/Banner/FeaturedProperty.

### Especificacion (specs/001-listing-catalog/)

Artefactos de diseño que definen el sistema completo de extremo a extremo y sirven
como contrato para implementar API y frontend en branches futuros. Documentos
existentes/nuevos en esta carpeta (cada uno [NEW] como artefacto versionado):

- [NEW] `spec.md` — indice maestro, FR-###/NFR-### y mapa de la Definition of Done.
- [NEW] `plan.md` — este documento (estrategia tecnica y cambios propuestos).
- [NEW] `tasks.md` — backlog accionable derivado de spec/plan.
- [NEW] `architecture.md` — arquitectura general, modulos (frontend/panel-agente/admin/backend), modelo de datos.
- [NEW] `roles-permissions.md` — matriz de roles y permisos (`RBAC-R#`).
- [NEW] `media-pipeline.md` — imagenes y multimedia (`MEDIA-R#`).
- [NEW] `search-filters.md` — filtros, busqueda, orden y paginacion (`SEARCH-R#`).
- [NEW] `property-detail.md` — pagina de detalle y ciclo de vida visible (`DETAIL-R#`).
- [NEW] `leads.md` — leads y estados (`LEAD-R#`).
- [NEW] `metrics.md` — metricas y eventos de engagement (`PERF-R#`/metricas).
- [NEW] `performance.md` — performance, cache y rate limiting (`PERF-R#`).
- [NEW] `seo.md` — SEO, canonicals, JSON-LD y politica 301/410 (`SEO-R#`).
- [NEW] `data-model.md` — 16 entidades: campos, tipos, relaciones, indices y restricciones (DoD #4).
- [NEW] `property-lifecycle.md` — maquina de estados y reglas de transicion (`LIFECYCLE-R#`).
- [NEW] `banners-featured.md` — banners promocionales + inmuebles destacados (`BANNER-R#`/`FEATURED-R#`).
- [NEW] `security.md` — autenticacion, autorizacion, antispam, proteccion de PII (`SEC-R#`).
- [NEW] `ux-ui.md` — lineamientos UX/UI mobile-first (`UX-R#`).
- [NEW] `api-contracts.md` — endpoints REST `/api/v1/*`, error envelope y paginacion (DoD #17).
- [NEW] `validations.md` — validaciones funcionales y tecnicas por entidad (`VALID-R#`).
- [NEW] `acceptance-criteria.md` — AC-01..AC-23 mapeados 1:1 a la Definition of Done.

> **Nota de alcance:** la **capa API (FastAPI + SQLAlchemy/Alembic + PostGIS/Redis/S3)**
> y el **frontend React SPA** NO se implementan en este branch. Quedan completamente
> **documentados** en los artefactos de spec anteriores (endpoints `/api/v1/*`,
> schemas, validaciones, error envelope, paginacion, SEO de cliente) y se desarrollaran
> en branches posteriores apoyandose en la capa de dominio entregada aqui.

## Verification & Rollback Plan

### Automated Verification
- **Suite de tests**: `pytest tests/` (cada modulo de dominio tiene su `tests/test_<modulo>.py` espejo; markers `unit`/`integration`/`critical`). Cobertura sobre reglas de la maquina de estados, invariantes y RBAC.
- **Quality gate local**: `make dev-check` ejecuta los hooks del harness (estructura, tamaño, secretos, convencion de branch, presencia de specs).
- **Limite de tamaño**: `.claude/hooks/check-file-size.sh` bloquea cualquier archivo > 1000 lineas; los modulos de dominio se mantienen pequeños y enfocados (objetivo < 300 lineas c/u).
- **Validacion de estructura**: `scripts/validation/validate_structure.py` impide modulos genericos (`utils.py`/`helpers.py`/`common.py`/...) y verifica nomenclatura por capacidad.
- **Quality Gate SonarQube (opcional/CI)**: `make sonar-check` contra el server local en Docker; en CI via `.github/workflows/ci-quality-gate.yml`.

### Manual Verification
- Revisar que cada modulo de `src/` use EXACTAMENTE los nombres del CONTRATO (entidades, campos, enums, valores) — comparacion 1:1 contra esta seccion.
- Recorrer manualmente la maquina de estados de `Property` (DRAFT→PENDING→PUBLISHED→PAUSED→SOLD/RENTED y caminos REJECTED/DELETED) y confirmar que transiciones invalidas lanzan error.
- Confirmar invariantes clave: una sola MAIN por propiedad, `Unique(user_id, property_id)` en favoritos, `locality_id` requerido cuando `FeaturedScope=LOCALITY`.
- Verificar que `spec.md` enlaza todos los documentos y cubre AC-01..AC-23.

### Rollback Plan
- Trabajo aislado en el branch `feature/001-listing-catalog`; nada toca `main` salvo via Pull Request revisado.
- Revertir un cambio puntual: `git revert <sha>`; descartar todo el branch antes del merge: `git checkout main && git branch -D feature/001-listing-catalog`.
- Recuperacion asistida: `make rollback` lista tags/parches de seguridad; `scripts/deployment/rollback.sh apply <target>` restaura el estado.
- Al ser capa de dominio en memoria (sin migraciones aplicadas en este branch), no hay estado de base de datos que revertir; el rollback es puramente de codigo via Git.
