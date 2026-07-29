# Arquitectura General — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #1, #2, #20.

## Resumen

**Listing** es una plataforma de listing inmobiliario multi-rol. Esta es la
vista de arquitectura de alto nivel: separa los cuatro frentes de producto
(Frontend publico, Panel usuario/agente, Panel admin, Backend/API), define la
capa de dominio framework-agnostica, fija la estrategia de escalabilidad
(stateless + read replicas + cache + CDN + colas async) y el enfoque
mobile-first, y describe entornos y tooling. Cierra con el indice de los
documentos de detalle.

Principios rectores:

- **CSR puro en cliente**: el frontend es una SPA React 18 (Vite) que consume
  la API REST `/api/v1`. No hay render en servidor; el SEO se resuelve con
  metadatos, sitemap y JSON-LD servidos por la API y por prerender selectivo
  (ver `seo.md`).
- **API stateless**: FastAPI no guarda estado de sesion en memoria; toda
  sesion vive en el JWT (access+refresh) y en Redis. Permite escalar
  horizontalmente tras un balanceador.
- **Dominio primero**: las reglas de negocio viven en `src/` como dataclasses y
  funciones puras, independientes de FastAPI y de SQLAlchemy. Se mapean a
  tablas Postgres y a schemas Pydantic en las capas externas.
- **Lecturas publicas sin auth**; escrituras y paneles requieren JWT Bearer.
- **Mobile-first**: el diseno parte del viewport movil y escala hacia
  desktop (ver `ux-ui.md`).

## Diagrama de capas (ASCII)

```
                         ┌───────────────────────────────────────────┐
                         │                 CLIENTES                    │
                         │   Navegador movil (mobile-first)  ·  Desktop │
                         └───────────────────────┬─────────────────────┘
                                                 │ HTTPS
                         ┌───────────────────────▼─────────────────────┐
                         │     React 18 SPA (Vite · CSR en cliente)     │
                         │  (a) Frontend publico                        │
                         │  (b) Panel usuario / agente                  │
                         │  (c) Panel admin                             │
                         │  Assets estaticos + media servidos via CDN   │
                         └───────────────────────┬─────────────────────┘
                                                 │ fetch JSON  /api/v1
                                                 │ JWT Bearer (access+refresh)
                  ┌──────────────────────────────▼──────────────────────────────┐
                  │              Balanceador de carga (HTTPS/TLS)                 │
                  │   rate limit perimetral · terminacion TLS · health checks    │
                  └──────────────────────────────┬──────────────────────────────┘
                                                 │
              ┌──────────────────────────────────┼──────────────────────────────────┐
              │            (d) BACKEND / API — FastAPI (Python 3.13) — STATELESS      │
              │  ┌────────────────────────────────────────────────────────────────┐ │
              │  │  Capa HTTP   : routers /api/v1 · Pydantic schemas · auth deps    │ │
              │  │  Capa app    : casos de uso · permisos (RBAC) · transacciones    │ │
              │  │  Capa dominio: dataclasses src/ (framework-agnostica)            │ │
              │  │  Capa infra  : repos SQLAlchemy · clientes Redis/S3 · publishers │ │
              │  └────────────────────────────────────────────────────────────────┘ │
              └───┬───────────────┬───────────────┬───────────────┬─────────────────┘
                  │               │               │               │
       ┌──────────▼───┐  ┌────────▼────────┐  ┌───▼──────────┐  ┌─▼────────────────┐
       │ PostgreSQL 16 │  │     Redis        │  │ Object store │  │  Cola async       │
       │ + PostGIS     │  │ cache +          │  │ S3-compat.   │  │ (workers)         │
       │ + pg_trgm     │  │ rate limit +     │  │   ──► CDN     │  │ - optimiz. imagen │
       │               │  │ sesiones/refresh │  │ (media/img)  │  │ - notif. de leads │
       │ primary +     │  │                  │  │              │  │ - reindex/SEO     │
       │ read replicas │  │                  │  │              │  │ - sitemap/metrics │
       └───────────────┘  └──────────────────┘  └──────────────┘  └───────────────────┘
            ▲   ▲
            │   └── lecturas (search/detalle/listados) ──► read replicas
            └────── escrituras (CRUD/lifecycle/leads) ───► primary
```

Flujo de lectura tipico (detalle de propiedad publica):

```
SPA ──GET /api/v1/properties/{slug}──► LB ──► FastAPI ──► Redis (hit?) ──► sirve
                                                   │ miss
                                                   └─► read replica (Postgres) ─► cachea ─► sirve
media (cdn_url/thumb_url) servida directo desde CDN, no toca FastAPI.
```

## Separacion de responsabilidades por frente

### (a) Frontend publico (SPA, sin auth para lectura)

Sitio cara al visitante (`VISITOR`) y al `REGISTERED_USER`. Render en cliente.

| Area | Responsabilidad | Endpoints/recursos principales |
|------|-----------------|-------------------------------|
| Home | hero, banners (`home_hero`/`home_inline`), destacados (`scope=home`), accesos a busqueda | `GET /banners`, `GET /featured`, `GET /properties` |
| Listado/Resultados | grilla de tarjetas, paginacion (`?page=&page_size=`), banners inline | `GET /properties` con filtros |
| Filtros y busqueda | operacion, tipo, ubicacion, precio, recamaras, banos, area, amenities, busqueda full-text (pg_trgm) | `GET /properties?...`, `GET /locations`, `GET /amenities` |
| Detalle | galeria (`PropertyImage`), descripcion, mapa (`location_point`), amenities, SEO/JSON-LD, similares | `GET /properties/{slug}`, `GET /properties/{id}/similar` |
| Banners | render por `BannerPosition`, registro de impresion/click | `GET /banners`, `POST /banners/{id}/click` |
| Destacados | bloque `FeaturedProperty` por `scope` y `locality` | `GET /featured` |
| Similares | propiedades afines por ubicacion/tipo/precio | `GET /properties/{id}/similar` |
| Contacto / CTAs | formulario de lead, CTAs WhatsApp/llamada/visita segun `primary_cta` | `POST /leads`, `POST /properties/{id}/events` |
| Favoritos | guardar/quitar (requiere `REGISTERED_USER`) | `GET/POST/DELETE /favorites` |
| Compartir | share nativo + open graph; registra evento `share` | `POST /properties/{id}/events` |
| Responsive | mobile-first; layout fluido; imagenes responsivas (thumb/cdn) | assets via CDN |

Reglas clave: solo propiedades en `PublicationStatus.PUBLISHED` son visibles
(HTTP 200). `SOLD`/`RENTED` aplican politica 301/410; el resto -> 404 (ver
`property-lifecycle.md` y `seo.md`). Los CTAs y vistas emiten eventos `PropertyView`
(`MetricEventType`) de forma asincrona, sin bloquear el render.

### (b) Panel usuario / agente (auth requerida)

Para `REGISTERED_USER` (favoritos, perfil) y `AGENT` (gestion de inventario
propio). Render en cliente, area privada tras login.

| Area | Responsabilidad | Endpoints / permisos |
|------|-----------------|----------------------|
| Auth | registro, login, refresh, verificacion de email | `POST /auth/register|login|refresh` |
| Perfil | datos de contacto (phone/whatsapp/avatar), preferencias | `GET/PATCH /users/me`; `user:read` |
| CRUD propiedad | crear/editar/duplicar/eliminar propias | `property:create`, `property:update_own`, `property:delete_own` |
| Fotos | subir/ordenar/eliminar imagenes, definir `MAIN` | `image:upload_own`; `POST /properties/{id}/images` |
| Estado/lifecycle | submit a revision, pausar, reactivar, marcar vendida/alquilada | `property:publish_request`, `property:pause_own` |
| Leads | bandeja de leads propios, cambio de `LeadStatus`, asignacion | `lead:read_own`, `lead:update_status` |
| Datos de contacto | exponer/ocultar `address` (`address_is_public`), canales | `property:update_own` |
| Historial | ver `AuditLog` y metricas propias (`views/clicks/leads`) | `metrics:read_own`, `audit:read` (propio) |

Reglas clave: `AGENT` solo opera sobre sus propias propiedades/leads
(`*_own`). Las transiciones de estado siguen la maquina de estados de
`property-lifecycle.md`. La publicacion no es directa: pasa por `PENDING` -> aprobacion
admin.

### (c) Panel admin (auth + rol elevado)

Para `ADMIN` y `SUPERADMIN`. Administracion sin tocar codigo (DoD #20):
banners, destacados, localidades, tipos, amenities, SEO y moderacion se
gestionan por datos.

| Area | Responsabilidad | Permisos |
|------|-----------------|----------|
| Usuarios | alta/edicion/baja, activar/verificar | `user:create|update|delete` |
| Roles y permisos | asignar roles, gestionar permisos | `role:assign`, `permission:manage` |
| Moderacion | aprobar/rechazar (con motivo), pausar cualquiera | `property:approve|reject`, `property:update_any` |
| Banners | CRUD de `Banner`, segmentacion y vigencia | `banner:manage` |
| Destacados | CRUD de `FeaturedProperty`, `scope`/`priority`/vigencia | `featured:manage` |
| Localidades | arbol de `Location` (parent_id, center_point) | `location:manage` |
| Tipos | `PropertyType` (mapeado a `PropertyKind`) | `property_type:manage` |
| Amenities | catalogo de `Amenity` por categoria | `amenity:manage` |
| Leads | ver/asignar todos los leads | `lead:read_any`, `lead:assign` |
| Reportes/metricas | metricas globales, denormalizados y eventos | `metrics:read_global` |
| SEO | metadatos, canonical, redirects, robots | `seo:manage` |
| Logs / auditoria | `AuditLog` append-only, global | `audit:read` |
| Config | parametros operativos del sistema | `config:manage` |

Reglas clave: toda accion sensible (publicar, aprobar, rechazar, asignar rol,
cambiar permisos/config) genera un registro en `AuditLog` (`AuditAction`).
`ADMIN` gestiona contenido y moderacion; `SUPERADMIN` ademas gobierna roles,
permisos y configuracion (jerarquia en `roles-permissions.md`).

### (d) Backend / API (FastAPI)

API REST stateless bajo `/api/v1`. Cuatro capas internas, dependencia
unidireccional (HTTP -> app -> dominio <- infra):

| Capa | Contenido | Tecnologia |
|------|-----------|------------|
| HTTP | routers, validacion de entrada/salida, auth deps, paginacion, error envelope | FastAPI + Pydantic |
| Aplicacion | casos de uso, orquestacion de transacciones, chequeo RBAC, publicacion de eventos a la cola | Python puro |
| Dominio | entidades, enums, invariantes y maquina de estados | dataclasses en `src/` |
| Infraestructura | repositorios, ORM, clientes Redis/S3, workers/publishers | SQLAlchemy, redis-py, boto3 |

Convenciones transversales (del contrato): error envelope
`{"error":{"code","message","details"}}`; paginacion
`?page=&page_size=` -> `{"data":[...],"meta":{...}}`; IDs UUID v4; dinero en
`BIGINT` minor units + `currency` CHAR(3); timestamps UTC `timestamptz`; soft
delete via `deleted_at`. Detalle de contrato HTTP en `api-contracts.md`.

## Capa de dominio framework-agnostica

El nucleo de negocio vive en `src/` como **dataclasses Python sin dependencias
de framework**. Esto permite testear reglas con `pytest` sin levantar API ni
base de datos, y reutilizar el dominio si cambia el transporte o el ORM.

```
                 ┌────────────────────────────────────────────┐
                 │            DOMINIO (src/, puro)              │
                 │  @dataclass Property, User, Lead, Banner ... │
                 │  Enums: OperationType, PublicationStatus ... │
                 │  Invariantes + maquina de estados (lifecycle)│
                 └───────┬───────────────────────────┬──────────┘
          mapeo persistencia                    mapeo transporte
                 │                                     │
        ┌────────▼─────────┐                 ┌─────────▼──────────┐
        │ Tablas Postgres   │                 │ Schemas Pydantic    │
        │ (SQLAlchemy ORM)  │                 │ (request/response)  │
        │ properties, users │                 │ PropertyOut, LeadIn │
        │ leads, banners... │                 │ paginacion, errores │
        └───────────────────┘                 └─────────────────────┘
```

Mapeos:

- **Dominio -> Postgres**: cada dataclass corresponde a una tabla (las 16
  entidades). El ORM traduce tipos: `OperationType` -> columna string;
  `location_point` -> `geography(POINT,4326)` (PostGIS); `price_amount` ->
  `BIGINT`. Detalle de campos/indices/relaciones en `data-model.md`.
- **Dominio -> Pydantic**: schemas de entrada validan payloads (VALID-R*);
  schemas de salida serializan respuestas publicas (ocultan campos privados
  como `address` cuando `address_is_public=false`, `source_ip`, hashes).
- **Enums unicos**: los valores de enum del contrato son la fuente de verdad
  en dominio, persistencia y transporte. El gate `make validate-enums` (hoy
  demo, ver CLAUDE.md) verificara la sincronia DB vs codigo cuando el esquema
  este definido.

El estado inicial de `src/listing_catalog.py` es un reference module del
harness; sera reemplazado por modulos de dominio por capacidad (`catalog/`,
`pricing/`, `inventory/`, etc.) conforme se implementen las entidades, sin
introducir shells genericos `models/`/`services/` vacios.

## Escalabilidad

| Palanca | Como aplica en Listing |
|---------|------------------------|
| API stateless tras balanceador | FastAPI no guarda estado local; N replicas identicas detras del LB; estado de sesion en JWT + Redis; escalado horizontal por CPU/RPS |
| Read replicas Postgres | escrituras (CRUD, lifecycle, leads) al primary; lecturas pesadas (search, listados, detalle) a replicas; el router de DB enruta por tipo de operacion |
| Indices | B-tree en FKs/`slug`/`status`; GiST en `location_point` (PostGIS) para busqueda geoespacial; GIN/pg_trgm para full-text en `title`/`description`/ubicacion; indices parciales para `status='published'` (ver `data-model.md`/`search-filters.md`) |
| CDN | imagenes y media (`cdn_url`/`thumb_url`) y assets de la SPA servidos desde CDN; descarga la API de trafico estatico; cache-control por inmutabilidad de URLs versionadas |
| Colas async (workers) | tareas fuera del request: optimizacion/redimension de imagenes al subir, generacion de thumbnails, notificaciones de leads (email/whatsapp), reindex de busqueda, recalculo de denormalizados, generacion de sitemap/SEO |
| Cache Redis | respuestas de lectura cacheables (detalle publico, listados frecuentes, banners/destacados activos), resultados de filtros, y rate limiting por IP/usuario; invalidacion por evento de escritura |
| Contadores denormalizados | `views_count`/`clicks_count`/`leads_count`/`impressions_count` se actualizan async desde eventos (`PropertyView`) para no penalizar lecturas |

Patron de eventos: las acciones de usuario que generan engagement
(`PropertyView` con `MetricEventType`) y las tareas costosas se publican a la
cola y se procesan por workers; la API responde rapido y la consistencia de
contadores es eventual.

## Mobile-first

- Diseno desde el viewport movil hacia desktop (breakpoints progresivos).
- Imagenes responsivas: `thumb_url` para listados, `cdn_url` para detalle;
  carga diferida (lazy) y formatos modernos servidos por CDN.
- CTAs criticos (WhatsApp/llamada/visita) prominentes y accesibles en movil
  (segun `primary_cta`).
- Presupuesto de performance orientado a movil (ver `performance.md`):
  payloads paginados, cache agresiva de lecturas, JS de la SPA fragmentado por
  ruta (code-splitting de Vite).
- Detalle de patrones de interfaz y accesibilidad en `ux-ui.md`.

## Entornos y tooling

### Entornos

| Entorno | Proposito | Notas |
|---------|-----------|-------|
| dev | desarrollo local | Postgres/Redis/MinIO en Docker; `.env.local` (git-ignored); SonarQube local opcional (`make sonar-up`) |
| staging | validacion pre-produccion | replica de prod a menor escala; datos de prueba; CI Quality Gate contra SonarQube hosted |
| prod | produccion | API tras LB, read replicas, CDN, object storage gestionado, secretos en gestor seguro (no en repo) |

CI no alcanza un SonarQube en `localhost`; en CI se apunta a una instancia
hosted (SonarQube/SonarCloud) via secrets `SONAR_HOST_URL`/`SONAR_TOKEN` (ver
CLAUDE.md y `.github/workflows/ci-quality-gate.yml`).

### Tooling del repositorio

| Herramienta | Uso |
|-------------|-----|
| pytest | suite de pruebas; markers `unit`/`integration`/`critical` (`pytest.ini`); tests espejan modulos de `src/` |
| coverage | cobertura de pruebas; alimenta el Quality Gate |
| SonarQube | Quality Gate local (`make sonar-check`, Docker) y remoto (CI); `sonar-project.properties` (`projectKey=listing`) |
| pre-commit / hooks | `.pre-commit-config.yaml` + `.claude/hooks/` (limite 1000 lineas/archivo, sin archivos temporales en raiz, branch convention, spec-driven gate, sin secretos, sin modulos dump) |
| Makefile | `make spec-new`, `make dev-check`, `make test`, `make sonar-*`, `make hotfix`, `make rollback` |

Flujo: rama `feature/<NNN-slug>` -> specs completos -> codigo+tests ->
`make dev-check` + `make test` -> push (pre-push corre tests) -> PR ->
CI verde -> merge a `main`.

## Indice de documentos de detalle

Documentos de `specs/001-listing-catalog/` (este es la vista de arquitectura;
el indice maestro vive en `spec.md`):

| Documento | Contenido | DoD |
|-----------|-----------|-----|
| `spec.md` | indice maestro, FR-###/NFR-###, criterios de aceptacion AC-01..AC-23 | 21, 22 |
| `architecture.md` (este) | arquitectura general, 4 frentes, dominio, escalabilidad, mobile-first, tooling | 1, 2, 20 |
| `roles-permissions.md` | roles, jerarquia, matriz de permisos (RBAC-R*) | 3, 14 |
| `data-model.md` | 16 entidades, campos, relaciones, validaciones, indices | 4 |
| `property-lifecycle.md` | maquina de estados de Property y reglas de transicion (LIFECYCLE-R*) | 5, 6 |
| `media-pipeline.md` | imagenes y multimedia, roles `MAIN`/`GALLERY`, `MediaKind` (MEDIA-R*) | 7 |
| `search-filters.md` | filtros, busqueda full-text, orden, paginacion (SEARCH-R*) | 8 |
| `property-detail.md` | pagina de detalle y similares (DETAIL-R*) | 9 |
| `leads.md` | leads, canales, estados, consentimiento (LEAD-R*) | 10 |
| `banners-featured.md` | banners y promociones, segmentacion (BANNER-R*) | 11 |
| `banners-featured.md` | inmuebles destacados por scope (FEATURED-R*) | 12 |
| `seo.md` | SEO, canonical, redirects, JSON-LD, politica SOLD/RENTED (SEO-R*) | 13 |
| `security.md` | seguridad, auth JWT, rate limit, privacidad (SEC-R*) | 14 |
| `performance.md` | presupuestos de performance, cache, indices (PERF-R*) | 15 |
| `ux-ui.md` | UX/UI mobile-first, accesibilidad (UX-R*) | 16 |
| `api-contracts.md` | endpoints `/api/v1`, contratos, errores, paginacion | 17 |
| `validation.md` | validaciones de entrada y reglas de datos (VALID-R*) | 18 |
| `metrics.md` | metricas, eventos `PropertyView`, denormalizados, auditoria | 19 |

## Open Questions

- **Re-revision por edicion material**: el contrato deja abierta la regla de
  cuando una edicion de una propiedad `PUBLISHED` exige volver a `PENDING`.
  Se define en `property-lifecycle.md`; la arquitectura asume que la cola async puede
  disparar el flujo de moderacion si se activa.
- **Prerender/SEO para CSR**: el alcance del prerender selectivo (paginas de
  detalle/listado) frente a servir solo metadatos por API queda por acordar
  con el equipo de SEO (`seo.md`).
- **Estrategia exacta de routing primary/replica**: si se hace a nivel de
  aplicacion o via proxy de base de datos (pgbouncer/pgpool) se decide en
  `performance.md`.
