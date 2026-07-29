# Feature Specification: 001-listing-catalog

**Feature Branch**: `001-listing-catalog`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "Sistema de listing inmobiliario web completo (frontend publico, panel agente, panel admin, API)"

## Resumen

**Listing** es una plataforma inmobiliaria web que permite publicar, buscar, descubrir y contactar propiedades en venta, renta y temporal. Se compone de cuatro modulos: **frontend publico** (CSR React 18/Vite, mobile-first, SEO-friendly), **panel agente** (gestion del ciclo de vida de propiedades, imagenes y leads propios), **panel admin** (moderacion, banners, destacados, usuarios, metricas globales, configuracion sin tocar codigo) y **API** (FastAPI Python 3.13 sobre PostgreSQL 16 + PostGIS + pg_trgm, Redis para cache y rate limit, almacenamiento S3-compatible + CDN). Auth via JWT Bearer (access+refresh); las lecturas publicas no requieren auth.

Este `spec.md` es el **indice maestro** y la fuente de los IDs `FR-###` / `NFR-###`. El detalle tecnico vive en los documentos enlazados en el Mapa de documentos; las reglas por dominio usan el prefijo `<PREFIJO>-R<n>` dentro de cada documento, y los criterios de aceptacion `AC-01..AC-23` viven en `acceptance-criteria.md`. Cubre los items de la Definition of Done: **#2 (modulos), #21 (spec lista para backlog), #22 (sin ambiguedades criticas)**.

### Modulos del sistema (DoD #2)

| Modulo | Audiencia | Responsabilidad principal | Detalle |
|---|---|---|---|
| Frontend publico | VISITOR, REGISTERED_USER | Busqueda, filtros, detalle, contacto (lead), favoritos, compartir | `search-filters.md`, `property-detail.md`, `ux-ui.md` |
| Panel agente | AGENT | Crear/editar/publicar/pausar/vender propiedades propias, subir media, gestionar leads propios | `property-lifecycle.md`, `media-pipeline.md`, `leads.md` |
| Panel admin | ADMIN, SUPERADMIN | Moderar (aprobar/rechazar), banners, destacados, usuarios, roles, metricas globales, audit, SEO, config | `roles-permissions.md`, `banners-featured.md`, `metrics.md` |
| API | Todos los modulos | Contratos REST `/api/v1`, auth JWT, RBAC, validaciones, envelope de error y paginacion | `api-contracts.md`, `validations.md`, `security.md` |

## Mapa de documentos

Todos los documentos viven en `specs/001-listing-catalog/`. Este `spec.md` es el indice; cada documento profundiza un dominio y declara sus reglas con su propio prefijo.

| Documento | DoD | Contenido (una linea) |
|---|---|---|
| `architecture.md` | 1,2,20 | Arquitectura general: capas FastAPI/PostGIS/Redis/S3+CDN, frontend CSR, despliegue y escalabilidad. |
| `roles-permissions.md` | 3 | Matriz RBAC: jerarquia de roles y permisos `resource:action`. Reglas `RBAC-R#`. |
| `data-model.md` | 4 | Modelo de datos: 16 entidades, campos, relaciones, validaciones e indices. Reglas `VALID-R#`. |
| `property-lifecycle.md` | 5,6 | Maquina de estados `PublicationStatus` y reglas de transicion. Reglas `LIFECYCLE-R#`. |
| `media-pipeline.md` | 7 | Imagenes y multimedia: roles, derivados CDN, restriccion MAIN unica. Reglas `MEDIA-R#`. |
| `search-filters.md` | 8 | Filtros, busqueda full-text/geo, orden y paginacion. Reglas `SEARCH-R#`. |
| `property-detail.md` | 9 | Pagina de detalle de propiedad y CTAs de contacto. Reglas `DETAIL-R#`. |
| `leads.md` | 10 | Captura y estados de leads, asignacion, consentimiento. Reglas `LEAD-R#`. |
| `banners-featured.md` | 11,12 | Banners promocionales y propiedades destacadas. Reglas `BANNER-R#`, `FEATURED-R#`. |
| `seo.md` | 13 | SEO: slugs, metadatos, jsonld, canonical, politica 301/410 de SOLD/RENTED. Reglas `SEO-R#`. |
| `security.md` | 14 | Seguridad: auth JWT, rate limit, hardening, OWASP. Reglas `SEC-R#`. |
| `performance.md` | 15 | Performance: presupuestos, cache Redis, CDN, indices. Reglas `PERF-R#`. |
| `ux-ui.md` | 16 | UX/UI mobile-first, accesibilidad, estados de carga/error. Reglas `UX-R#`. |
| `api-contracts.md` | 17 | Endpoints `/api/v1`, request/response, codigos de error, paginacion. |
| `validations.md` | 18 | Reglas de validacion de entrada por entidad y campo. Reglas `VALID-R#`. |
| `metrics.md` | 19 | Metricas de engagement (`PropertyView`), contadores denormalizados, audit. |
| `acceptance-criteria.md` | 21,22,23 | Criterios de aceptacion verificables `AC-01..AC-23` (mapeo a DoD). |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visitante busca y contacta una propiedad (Priority: P1)

Un visitante no autenticado entra al frontend publico, busca propiedades por operacion/ubicacion/precio, abre el detalle de una propiedad publicada y envia un mensaje de contacto (lead) o pulsa el CTA de WhatsApp.

**Why this priority**: Es el flujo que genera valor de negocio (leads). Sin busqueda->detalle->contacto la plataforma no cumple su proposito comercial; constituye el MVP demostrable.

**Independent Test**: Sembrar >=1 propiedad en estado `PUBLISHED`, ejecutar busqueda con filtros, abrir el detalle por su slug y enviar el formulario de lead; verificar que se crea un `Lead` con `channel=FORM`, `status=NEW` y que `leads_count` de la propiedad se incrementa.

**Acceptance Scenarios**:

1. **Given** propiedades `PUBLISHED` que coinciden con `operation_type=sale` y `city`, **When** el visitante aplica esos filtros, **Then** el sistema devuelve resultados paginados (`{"data":[...],"meta":{...}}`) que solo incluyen propiedades `PUBLISHED`.
2. **Given** una propiedad `PUBLISHED` con slug valido, **When** el visitante abre `/<slug>`, **Then** el detalle responde HTTP 200 con galeria, precio (`price_amount`+`currency`), ubicacion y CTAs de contacto.
3. **Given** un visitante en el detalle, **When** envia el formulario con `consent_given=true`, **Then** se crea un `Lead` (`channel=form`, `status=new`) y se registra un evento `PropertyView` (`event_type=visit_request` o el CTA correspondiente).
4. **Given** un visitante que pulsa el boton de WhatsApp, **When** ocurre el clic, **Then** se registra `PropertyView` (`event_type=whatsapp_click`) y se incrementa `clicks_count`.

---

### User Story 2 - Agente publica una propiedad (Priority: P1)

Un agente autenticado crea una propiedad, sube fotos, completa los campos minimos y la envia a revision; tras aprobacion queda visible al publico.

**Why this priority**: Sin oferta publicable no hay catalogo; es la contraparte de la captacion de leads y parte del MVP.

**Independent Test**: Autenticarse como `AGENT`, crear una propiedad (queda `DRAFT`), subir >=1 imagen (1 `MAIN`), ejecutar `submit_for_review` (pasa a `PENDING`); verificar bloqueo si faltan campos minimos o imagenes.

**Acceptance Scenarios**:

1. **Given** un agente autenticado con permiso `property:create`, **When** crea una propiedad, **Then** se persiste en `status=draft` con `slug` unico `{operation}-{kind}-{title-kebab}-{shortid}` y contadores en 0.
2. **Given** una propiedad `DRAFT` con campos minimos y >=1 imagen, **When** el agente ejecuta `submit_for_review` (`property:publish_request`), **Then** pasa a `status=pending`.
3. **Given** una propiedad `DRAFT` sin imagenes o con campos minimos faltantes, **When** intenta `submit_for_review`, **Then** la API rechaza con error de validacion (envelope `{"error":{...}}`) y NO cambia de estado.
4. **Given** una propiedad `PENDING` aprobada por admin, **When** se aprueba, **Then** pasa a `status=published`, se fija `published_at` y queda visible (HTTP 200) en el frontend publico.

---

### User Story 3 - Admin modera el catalogo (Priority: P2)

Un administrador revisa la cola de propiedades `PENDING` y las aprueba o rechaza con motivo; el agente puede reenviar tras correccion.

**Why this priority**: Garantiza calidad del catalogo y cumplimiento. No bloquea el MVP de demo pero es necesario para operacion real.

**Independent Test**: Autenticarse como `ADMIN`, listar `PENDING`, aprobar una (`PUBLISHED`) y rechazar otra con `reason` (`REJECTED`); verificar registro en `AuditLog` (`action=approve`/`reject`).

**Acceptance Scenarios**:

1. **Given** una propiedad `PENDING` y un admin con `property:approve`, **When** aprueba, **Then** pasa a `PUBLISHED`, fija `published_at` y crea `AuditLog` con `action=approve`.
2. **Given** una propiedad `PENDING`, **When** el admin la rechaza con motivo (`property:reject`), **Then** pasa a `REJECTED`, se persiste el motivo y se crea `AuditLog` con `action=reject`.
3. **Given** una propiedad `REJECTED`, **When** el agente propietario corrige y reenvia (`resubmit`), **Then** vuelve a `PENDING`.

---

### User Story 4 - Banners y destacados administrables (Priority: P2)

Un administrador configura banners promocionales por posicion y propiedades destacadas por alcance, sin tocar codigo, con segmentacion y vigencia.

**Why this priority**: Habilita monetizacion y curaduria editorial; configurable desde el panel (DoD #20).

**Independent Test**: Como `ADMIN` con `banner:manage`/`featured:manage`, crear un banner activo (`position=home_hero`) y destacar una propiedad `PUBLISHED` (`scope=home`); verificar que aparecen en el frontend y que se registran impresiones/clics.

**Acceptance Scenarios**:

1. **Given** un admin con `banner:manage`, **When** crea un `Banner` activo con vigencia y posicion, **Then** el frontend lo muestra en su `BannerPosition` y suma `impressions_count`.
2. **Given** una propiedad `PUBLISHED`, **When** el admin la destaca (`FeaturedProperty`, `scope=home`), **Then** aparece priorizada en home y registra metricas; si `scope=locality` exige `locality_id`.
3. **Given** un banner con `ends_at` pasado, **When** el frontend renderiza, **Then** NO lo muestra.

---

### User Story 5 - Favoritos y compartir (Priority: P3)

Un usuario registrado guarda propiedades como favoritas y cualquier visitante comparte el detalle por enlace.

**Why this priority**: Mejora retencion y difusion; valor incremental no critico para el MVP.

**Independent Test**: Como `REGISTERED_USER` con `favorite:manage_own`, marcar y desmarcar una propiedad como favorita (unique por `user_id`+`property_id`); compartir el detalle y verificar evento `PropertyView` (`event_type=share`).

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, **When** marca una propiedad como favorita, **Then** se crea un `Favorite` unico por `(user_id, property_id)`; un segundo intento es idempotente.
2. **Given** un visitante en el detalle, **When** pulsa compartir, **Then** se registra `PropertyView` (`event_type=share`, `source=share`).

---

### Edge Cases

- **Publicar sin imagenes**: `submit_for_review` sobre una propiedad sin >=1 imagen (o sin `MAIN`) se rechaza con error de validacion; el estado permanece `DRAFT` (ver `property-lifecycle.md`, `media-pipeline.md`).
- **Slug duplicado**: al generar `slug` ya existente, el sistema reintenta con nuevo `shortid` hasta garantizar unicidad; nunca persiste un slug repetido (`seo.md`).
- **Propiedad vendida aun indexada**: una propiedad `SOLD`/`RENTED` deja de ser visible (HTTP 200) y aplica politica 301/410 segun `seo.md`; los buscadores deben recibir la senal correcta y no 200.
- **Lead spam**: envios masivos desde la misma IP/sesion se mitigan con rate limit (Redis) y `consent_given` obligatorio; los excedentes se rechazan (`leads.md`, `security.md`).
- **Permisos cruzados agente/agente**: un agente NO puede editar/eliminar/ver leads de propiedades de otro agente (`update_own` vs `update_any`); el intento responde 403 (`roles-permissions.md`).
- **Estado inconsistente**: transiciones invalidas (p. ej. `DRAFT->SOLD`, `mark_sold` sobre `operation_type!=sale`) se rechazan con 409/422 y no mutan el estado (`property-lifecycle.md`).
- **Edicion material de PUBLISHED**: cambios materiales pueden requerir re-revision (regla pendiente de cierre; ver Open Questions y `property-lifecycle.md`).
- **Direccion privada**: si `address_is_public=false`, la direccion exacta NO se expone en respuestas publicas; solo ubicacion aproximada (`property-detail.md`, `security.md`).

## Requirements *(mandatory)*

### Functional Requirements

#### Auth, Users, Roles y Permissions (FR-001..019)

- **FR-001**: El sistema MUST permitir registro de usuarios con `email` unico y `password_hash` (nunca en claro).
- **FR-002**: El sistema MUST autenticar via JWT Bearer emitiendo tokens `access` y `refresh`.
- **FR-003**: El sistema MUST permitir refrescar el `access` token mediante el `refresh` token y revocar sesiones.
- **FR-004**: El sistema MUST soportar verificacion de email (`email_verified`) y activacion/desactivacion (`is_active`).
- **FR-005**: El sistema MUST permitir a un usuario actualizar su perfil (`full_name`, `phone`, `whatsapp`, `avatar_url`).
- **FR-006**: El sistema MUST aplicar la jerarquia de roles VISITOR < REGISTERED_USER < AGENT < ADMIN < SUPERADMIN.
- **FR-007**: El sistema MUST modelar permisos como codigos `resource:action` y resolver autorizacion por permiso, no por rol embebido.
- **FR-008**: El sistema MUST permitir a SUPERADMIN/ADMIN gestionar usuarios (`user:read/create/update/delete`) segun permiso.
- **FR-009**: El sistema MUST permitir asignar roles (`role:assign`) y gestionar permisos (`permission:manage`) solo a roles autorizados.
- **FR-010**: El sistema MUST distinguir `update_own`/`delete_own` de `update_any`/`delete_any` para aislamiento entre agentes.
- **FR-011**: El sistema MUST permitir lecturas publicas (`property:read_public`) sin autenticacion.
- **FR-012**: El sistema MUST registrar acciones sensibles de cuenta (`login`, `logout`, `role_assign`, `permission_change`) en `AuditLog`.

#### Properties y ciclo de vida (FR-020..049)

- **FR-020**: El sistema MUST permitir crear una propiedad con permiso `property:create`, iniciando en `status=draft`.
- **FR-021**: El sistema MUST generar `slug` unico con formato `{operation}-{kind}-{title-kebab}-{shortid}` validado por la regex de slug.
- **FR-022**: El sistema MUST almacenar dinero como `price_amount` BIGINT en minor units + `currency` CHAR(3) ISO 4217 (nunca float).
- **FR-023**: El sistema MUST permitir editar propiedades propias (`property:update_own`) y cualquiera con `property:update_any`.
- **FR-024**: El sistema MUST implementar la transicion `DRAFT->PENDING` (`submit_for_review`) exigiendo campos minimos y >=1 imagen.
- **FR-025**: El sistema MUST implementar `PENDING->PUBLISHED` (`approve`, `property:approve`) fijando `published_at`.
- **FR-026**: El sistema MUST implementar `PENDING->REJECTED` (`reject` con `reason`, `property:reject`) y `REJECTED->PENDING` (`resubmit`).
- **FR-027**: El sistema MUST implementar `PUBLISHED->PAUSED` (`pause`) y `PAUSED->PUBLISHED` (`reactivate`) para owner/admin.
- **FR-028**: El sistema MUST implementar `mark_sold` solo si `operation_type=sale` y `mark_rented` solo si `operation_type in {rent, temporary}`, desde `PUBLISHED|PAUSED`.
- **FR-029**: El sistema MUST implementar soft delete (`->DELETED`, set `deleted_at`) para owner (propia) o admin (cualquiera).
- **FR-030**: El sistema MUST permitir `duplicate`, clonando a `DRAFT` con nuevo `id`+`slug` y metricas en 0.
- **FR-031**: El sistema MUST exponer publicamente (HTTP 200) SOLO propiedades `PUBLISHED`; `PAUSED/REJECTED/DRAFT/DELETED` responden 404 y `SOLD/RENTED` aplican politica 301/410.
- **FR-032**: El sistema MUST rechazar toda transicion no contemplada en la maquina de estados (`property-lifecycle.md`).
- **FR-033**: El sistema MUST registrar cada transicion relevante en `AuditLog` (`create/update/publish/approve/reject/pause/reactivate/mark_sold/mark_rented/duplicate/delete`).
- **FR-034**: El sistema MUST geolocalizar la propiedad (`location_point` geography POINT 4326) y vincular `locality_id->Location`.
- **FR-035**: El sistema MUST gestionar amenidades por propiedad (M2M `PropertyAmenity` con `value` opcional).

#### Imagenes y media (FR-050..059)

- **FR-050**: El sistema MUST permitir subir media propia (`image:upload_own`) y gestionar cualquiera (`image:manage_any`).
- **FR-051**: El sistema MUST soportar `MediaKind` (image, video, floor_plan, virtual_tour) y `ImageRole` (main, gallery).
- **FR-052**: El sistema MUST garantizar exactamente una imagen `MAIN` por propiedad.
- **FR-053**: El sistema MUST generar y servir derivados via CDN (`original_url`, `cdn_url`, `thumb_url`) con metadatos (`width`, `height`, `bytes`, `content_type`, `alt_text`).
- **FR-054**: El sistema MUST permitir ordenar imagenes mediante `position`.

#### Search, filtros y detalle (FR-060..079)

- **FR-060**: El sistema MUST permitir filtrar por `operation_type`, `property_kind`, `condition`, ubicacion, rango de precio, recamaras, banos y amenidades.
- **FR-061**: El sistema MUST soportar busqueda full-text (pg_trgm) sobre titulo/descripcion/ubicacion.
- **FR-062**: El sistema MUST soportar busqueda geoespacial (PostGIS) por radio/area.
- **FR-063**: El sistema MUST soportar ordenamiento (precio, recencia, relevancia, destacados primero) y paginacion `?page=&page_size=` con `meta`.
- **FR-064**: El sistema MUST devolver en busqueda y detalle SOLO propiedades `PUBLISHED`.
- **FR-065**: El sistema MUST exponer la pagina de detalle por `slug` con galeria, precio, ubicacion (respetando `address_is_public`), amenidades y CTAs.
- **FR-066**: El sistema MUST priorizar propiedades destacadas (`FeaturedProperty`) en los listados segun `scope` y `priority`.

#### Leads (FR-080..089)

- **FR-080**: El sistema MUST capturar leads desde el detalle con `channel` (form, whatsapp, call, visit) y `status=new` inicial.
- **FR-081**: El sistema MUST exigir `consent_given=true` y persistir `consent_text` al crear un lead.
- **FR-082**: El sistema MUST asignar el lead al agente propietario de la propiedad (`owner_id`) y permitir reasignacion (`lead:assign`).
- **FR-083**: El sistema MUST permitir transicionar `LeadStatus` (new->contacted->negotiating->closed/discarded) con `lead:update_status`.
- **FR-084**: El sistema MUST restringir lectura de leads a `lead:read_own` (propios) o `lead:read_any` (todos).
- **FR-085**: El sistema MUST capturar `source_ip`, `user_agent` y `utm` para atribucion, respetando privacidad.

#### Banners y destacados (FR-090..099)

- **FR-090**: El sistema MUST permitir gestionar banners (`banner:manage`) por `BannerPosition`, con `priority`, vigencia (`starts_at`/`ends_at`) e `is_active`.
- **FR-091**: El sistema MUST soportar segmentacion de banners por `target_locality_id`, `target_city`, `target_operation`, `target_kind`.
- **FR-092**: El sistema MUST contabilizar `impressions_count` y `clicks_count` de banners.
- **FR-093**: El sistema MUST permitir destacar propiedades (`featured:manage`) con `FeaturedScope` (home, search_results, locality) y `priority`, exigiendo `locality_id` cuando `scope=locality`.
- **FR-094**: El sistema MUST respetar vigencia de destacados y contabilizar sus impresiones/clics.

#### SEO (FR-100..109)

- **FR-100**: El sistema MUST mantener `SeoMetadata` por entidad (meta_title, meta_description, og_*, canonical_url, jsonld, robots).
- **FR-101**: El sistema MUST emitir canonical y jsonld de propiedad para indexacion correcta.
- **FR-102**: El sistema MUST aplicar politica 301/410 a slugs de propiedades `SOLD/RENTED` y soportar `redirect_from` (slugs viejos).
- **FR-103**: El sistema MUST emitir `robots` por defecto `index,follow` y permitir override por entidad.

#### Favoritos, compartir, reportar (FR-110..119)

- **FR-110**: El sistema MUST permitir a usuarios registrados gestionar favoritos (`favorite:manage_own`) con unicidad `(user_id, property_id)`.
- **FR-111**: El sistema MUST registrar eventos de compartir (`PropertyView` con `event_type=share`).
- **FR-112**: El sistema MUST permitir reportar contenido/propiedades para moderacion. [NEEDS CLARIFICATION: entidad de reporte no definida en el contrato]

#### Admin, moderacion, metricas y audit (FR-120..129)

- **FR-120**: El sistema MUST proveer cola de moderacion de propiedades `PENDING` para roles con `property:approve`/`property:reject`.
- **FR-121**: El sistema MUST registrar eventos de engagement en `PropertyView` (`MetricEventType` x `ViewSource`) y denormalizar contadores en `Property/Banner/FeaturedProperty`.
- **FR-122**: El sistema MUST exponer metricas propias (`metrics:read_own`) y globales (`metrics:read_global`) segun permiso.
- **FR-123**: El sistema MUST mantener `AuditLog` append-only de acciones sensibles (`AuditAction`) con `before/after`.
- **FR-124**: El sistema MUST permitir administrar catalogos (`location:manage`, `property_type:manage`, `amenity:manage`), SEO (`seo:manage`) y configuracion (`config:manage`) sin tocar codigo.
- **FR-125**: El sistema MUST usar el error envelope `{"error":{"code","message","details"}}` y la paginacion `{"data":[...],"meta":{...}}` en toda la API `/api/v1`.

### Non-Functional Requirements

#### Seguridad (NFR-001..)

- **NFR-001**: El sistema MUST proteger credenciales con hashing fuerte y nunca exponer `password_hash`.
- **NFR-002**: El sistema MUST aplicar JWT con expiracion corta de `access` y rotacion/revocacion de `refresh`.
- **NFR-003**: El sistema MUST aplicar RBAC por permiso en cada endpoint y devolver 403 ante acceso no autorizado.
- **NFR-004**: El sistema MUST aplicar rate limiting (Redis) en auth, leads y endpoints sensibles.
- **NFR-005**: El sistema MUST validar y sanear toda entrada y mitigar OWASP Top 10 (inyeccion, XSS, IDOR).
- **NFR-006**: El sistema MUST no exponer direccion exacta cuando `address_is_public=false`.

#### Performance (NFR-010..)

- **NFR-010**: La busqueda y el detalle publicos MUST responder con TTFB p95 < 500ms bajo carga nominal.
- **NFR-011**: El sistema MUST cachear en Redis listados y detalles calientes e invalidar al cambiar estado/datos.
- **NFR-012**: El sistema MUST servir media e imagenes via CDN con derivados optimizados.
- **NFR-013**: El sistema MUST disponer de indices adecuados (B-tree, GIST/PostGIS, GIN/pg_trgm) para filtros y busqueda.

#### Escalabilidad (NFR-020..)

- **NFR-020**: El sistema MUST ser stateless en la capa API para escalar horizontalmente.
- **NFR-021**: El sistema MUST soportar crecimiento del catalogo y trafico sin redisenar el modelo de datos.

#### SEO y Accesibilidad (NFR-030..)

- **NFR-030**: El frontend MUST exponer metadatos SEO, canonical y jsonld correctos por pagina.
- **NFR-031**: El frontend MUST ser mobile-first y cumplir accesibilidad WCAG 2.1 AA en flujos principales.
- **NFR-032**: El sistema MUST emitir las senales HTTP correctas (200/301/404/410) por estado de publicacion para SEO.

#### Privacidad y Cumplimiento (NFR-040..)

- **NFR-040**: El sistema MUST capturar y persistir consentimiento (`consent_given`, `consent_text`) en leads.
- **NFR-041**: El sistema MUST minimizar y proteger PII (hash de IP/sesion en metricas: `ip_hash`, `session_hash`).
- **NFR-042**: El sistema MUST soportar una politica de retencion/borrado de leads y PII. [NEEDS CLARIFICATION: ver Open Questions]

## Open Questions

- **Mapas**: usar Leaflet/OpenStreetMap (sin coste, autohospedable) vs Google Maps (mejor geocoding/POIs, con coste y T&C)?
- **WhatsApp**: enlaces `wa.me` (simple, sin onboarding) vs WhatsApp Business API (plantillas, automatizacion, coste/aprobacion)?
- **SEO para bots**: el frontend es CSR (React/Vite); se requiere prerender/SSR selectivo para bots (dynamic rendering) o basta con metadatos + jsonld inyectados?
- **Cumplimiento de datos**: alcance GDPR vs ley local (p. ej. Habeas Data CO / LFPDPPP MX); define retencion, derechos ARCO/borrado y bases legales.
- **Multipais/multimoneda**: alcance inicial uni-pais/uni-moneda vs soporte multi-`Currency` y multi-locale desde el dia 1 (impacta `Location`, formateo y SEO hreflang).
- **Retencion de leads**: cuanto tiempo se conservan leads y PII asociada antes de anonimizar/borrar (afecta NFR-042 y FR-085).
- **Edicion material de PUBLISHED**: que cambios disparan re-revision (precio? direccion? operation_type?) y cual es el flujo (auto a PENDING vs aprobacion ligera)?
- **Reportar contenido (FR-112)**: el contrato no define entidad de reporte; decidir si se modela o se delega a un canal externo.
