# Criterios de Aceptacion — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #21, #22, #23.

## Resumen

Este documento es la **lista de verificacion de Definition of Done** del proyecto
Listing. Define 23 criterios de aceptacion verificables (`AC-01`..`AC-23`) mapeados
**1:1** con los 23 items de la Definition of Done del CONTRATO. Cada criterio fija:
*que* debe cumplirse, *como se verifica* (metodo objetivo y repetible) y *que
documento(s)/modulo(s)* del paquete `specs/001-listing-catalog/` lo cubren.

El alcance propio de este entregable son los items de meta-calidad de la
especificacion: **#21** (spec clara, modular, verificable, lista para backlog),
**#22** (sin ambiguedades criticas) y **#23** (output limpio, modular, listo para
produccion). Los demas criterios (`AC-01`..`AC-20`) se declaran cubiertos por sus
documentos de detalle ya presentes en el paquete; este archivo es el indice de
trazabilidad que lo demuestra.

Regla de lectura de la tabla:
- **ID**: identificador estable `AC-NN`. Corresponde exactamente al item `#NN` del DoD.
- **Criterio**: enunciado del item del DoD, redactado como condicion verificable.
- **Como se verifica**: prueba concreta (revision documental, conteo, ejecucion de
  comando del harness, o test) que decide pasa/no-pasa sin juicio subjetivo.
- **Documento(s)/modulo(s)**: archivo(s) de `specs/001-listing-catalog/` (y, cuando
  aplica, modulo de `src/`) que satisfacen el criterio.

Estado de cobertura: este entregable marca **los 23 AC como cubiertos** por el
paquete de especificacion, con un documento de detalle dedicado por capacidad
(incluidos `ux-ui.md` y `api-contracts.md`).

## Matriz de criterios de aceptacion (AC-01..AC-23)

| ID | Criterio (item del DoD) | Como se verifica | Documento(s)/modulo(s) que lo cubren |
|---|---|---|---|
| **AC-01** | Arquitectura general definida (4 frentes de producto, capa de dominio framework-agnostica, escalabilidad stateless + read replicas + cache + CDN + colas async, entornos y tooling). | Revision documental: `architecture.md` contiene diagrama de capas ASCII, principios rectores (CSR, API stateless, dominio primero) y seccion de entornos/tooling. Pasa si los 4 frentes y la capa de dominio aparecen descritos. | `architecture.md` |
| **AC-02** | Modulos delimitados: Frontend publico, Panel usuario/agente, Panel admin, Backend/API; con responsabilidades y fronteras. | Revision documental: `architecture.md` enumera los 4 modulos con responsabilidades y limites de datos/permisos por modulo. Pasa si cada modulo tiene responsabilidad explicita y consumo de API descrito. | `architecture.md` |
| **AC-03** | Matriz de roles y permisos completa: 5 roles (`VISITOR`<`REGISTERED_USER`<`AGENT`<`ADMIN`<`SUPERADMIN`) y todos los permisos `resource:action` del CONTRATO, con ownership `*_own` vs `*_any`. | Revision cruzada con CONTRATO: cada permiso de la lista `resource:action` y cada rol aparece en la matriz de `roles-permissions.md`; reglas en seccion `RBAC-R#`. Pasa si no falta ningun permiso ni rol y la semantica ownership esta resuelta. | `roles-permissions.md`; `src/` (modulo RBAC futuro) |
| **AC-04** | Modelo de datos completo: 16 entidades con campos, tipos, relaciones, validaciones e indices, segun CONTRATO (UUID v4, timestamptz, soft delete, dinero en minor units BIGINT, geography 4326). | Conteo y revision: `data-model.md` documenta las 16 entidades del CONTRATO con sus campos, FKs, relaciones (1:N, M2M, 1:1), constraints (p.ej. una sola `MAIN` por propiedad) e indices. Pasa si las 16 entidades estan y los tipos coinciden con el CONTRATO. | `data-model.md`; `src/listing_catalog.py` |
| **AC-05** | Ciclo de vida de propiedad: maquina de estados con los 8 estados `PublicationStatus` y todas las transiciones del CONTRATO, mas politica de visibilidad publica. | Revision documental: `property-lifecycle.md` incluye diagrama de estados, tabla de transiciones (evento, rol, precondicion, efecto) y la regla "solo `PUBLISHED` visible (200); `SOLD`/`RENTED` 301/410; resto 404". Pasa si toda transicion del CONTRATO esta tipada con rol y precondicion. | `property-lifecycle.md` (`LIFECYCLE-R#`) |
| **AC-06** | Reglas de operacion: crear, editar, publicar (submit/approve/reject), pausar/reactivar, vender, alquilar, eliminar (soft) y duplicar; con quien puede y bajo que condiciones. | Revision documental: cada accion del CONTRATO tiene regla `LIFECYCLE-R#` con actor (rol), precondiciones (campos minimos, >=1 imagen para submit, `operation_type` para sold/rent) y efectos (set `published_at`, clon a `DRAFT`, metricas en 0). Pasa si las 10+ acciones estan cubiertas. | `property-lifecycle.md` (`LIFECYCLE-R#`); `roles-permissions.md` |
| **AC-07** | Imagenes y multimedia: subida multiple, foto principal unica (`ImageRole.MAIN`), orden de galeria (`position`), reemplazo/eliminacion, validaciones de archivo, pipeline async de optimizacion, storage S3 + CDN; soporte `MediaKind`. | Revision documental: `media-pipeline.md` define modelo `PropertyImage`, reglas `MEDIA-R#`, validaciones (formato/peso/dimensiones/MIME real), pipeline (thumbnails, WebP/AVIF), ACLs y `cdn_url`/`thumb_url`/`srcset`. Pasa si "una sola MAIN por propiedad" y el pipeline async estan especificados. | `media-pipeline.md` (`MEDIA-R#`); `src/property_image.py` (futuro) |
| **AC-08** | Busqueda y filtros: endpoint `GET /api/v1/properties` (alias `/search`), filtros (texto full-text + `pg_trgm`, ubicacion, atributos, precio, amenities, geoespacial PostGIS, destacados), ordenamiento y paginacion `page`/`page_size` con `meta`. | Revision documental + contrato de respuesta: `search-filters.md` lista todos los query params, modos de orden, el sobre de paginacion `{"data":[...],"meta":{...}}` y fija `status=published` para lecturas publicas. Reglas en `SEARCH-R#`. Pasa si el envelope de paginacion coincide con el CONTRATO. | `search-filters.md` (`SEARCH-R#`) |
| **AC-09** | Pagina de detalle: estructura, payload `GET /api/v1/properties/{slug}`, comportamiento por estado (200/301/410/404), CTAs (form, WhatsApp, llamada, visita), eventos de metrica y SEO. | Revision documental: `property-detail.md` define bloques de render, subconjunto publico de campos, politica de visibilidad por estado, CTAs y eventos `PropertyView`. Reglas en `DETAIL-R#`. Pasa si la pagina solo renderiza `PUBLISHED` y respeta `address_is_public`. | `property-detail.md` (`DETAIL-R#`) |
| **AC-10** | Leads y estados: captura (form, WhatsApp, llamada, visita), entidad `Lead`, maquina de estados `LeadStatus`, canales `LeadChannel`, consentimiento, asignacion a agente y privacidad (ip/ua/utm). | Revision documental: `leads.md` define modelo `Lead`, transiciones `LeadStatus` (`NEW`->...->`CLOSED`/`DISCARDED`), canales, `consent_given`/`consent_text` y reglas `LEAD-R#`. Pasa si todos los `LeadStatus`/`LeadChannel` del CONTRATO estan y el lead publico no requiere auth. | `leads.md` (`LEAD-R#`) |
| **AC-11** | Banners y promociones: entidad `Banner`, posiciones `BannerPosition`, segmentacion (locality/city/operation/kind), ventana `starts_at`/`ends_at`, prioridad, contadores de impresiones/clicks. | Revision documental: `banners-featured.md` define modelo `Banner`, las 5 `BannerPosition`, reglas de seleccion/segmentacion y contadores denormalizados. Reglas en `BANNER-R#`. Pasa si las 5 posiciones y la segmentacion del CONTRATO estan cubiertas. | `banners-featured.md` (`BANNER-R#`) |
| **AC-12** | Inmuebles destacados: entidad `FeaturedProperty`, `FeaturedScope` (`HOME`/`SEARCH_RESULTS`/`LOCALITY`), `locality_id` requerido si `scope=LOCALITY`, prioridad, ventana y contadores. | Revision documental: `banners-featured.md` define modelo `FeaturedProperty`, los 3 `FeaturedScope`, la regla condicional de `locality_id` y la integracion con busqueda/home. Reglas en `FEATURED-R#`. Pasa si la regla `LOCALITY` requiere `locality_id`. | `banners-featured.md` (`FEATURED-R#`) |
| **AC-13** | SEO tecnico: URLs amigables (slug), metadatos (meta + Open Graph + JSON-LD), sitemap/robots, canonicals, redirects 301, paginas indexables por localidad/tipo/operacion, manejo SEO de estados no publicados (301/410). | Revision documental: `seo.md` define estrategia de indexabilidad, `SeoMetadata`, sitemap/robots por backend, politica 301/410 para `SOLD`/`RENTED`. Reglas en `SEO-R#`. Pasa si la politica de estados no publicados es consistente con `property-lifecycle.md`. | `seo.md` (`SEO-R#`) |
| **AC-14** | Seguridad: auth JWT (access+refresh), RBAC efectivo por permisos, rate limit (Redis), proteccion de datos sensibles, hardening, auditoria (`AuditLog`/`AuditAction`). | Revision documental: `security.md` define modelo de amenazas, controles, rate limiting, manejo de secretos (`.env.local`) y reglas `SEC-R#` mapeadas a `NFR-001..`. Pasa si auth, rate limit y auditoria estan especificados. | `security.md` (`SEC-R#`); `roles-permissions.md` |
| **AC-15** | Performance: objetivos cuantificados (p50/p95/p99) para imagenes/media, backend (search/detail/home/banners) y bundle SPA/Core Web Vitals, con metodo de medicion. | Revision documental: `performance.md` fija objetivos numericos por plano, condiciones cache hit/miss y reglas `PERF-R#` mapeadas a `NFR-010..`. Pasa si cada `PERF-R#` tiene objetivo medible + metodo de medicion. | `performance.md` (`PERF-R#`) |
| **AC-16** | UX/UI: lineamientos mobile-first, jerarquia de informacion, estados (loading/empty/error), accesibilidad y degradacion de acciones que requieren auth. | Revision documental: `ux-ui.md` consolida los lineamientos `UX-R#` (mobile-first y breakpoints, design tokens, cards/filtros/CTAs, estados loading/empty/error, accesibilidad WCAG 2.1 AA, microcopy). Pasa si los estados de UI y la accesibilidad basica estan especificados. | `ux-ui.md` (`UX-R#`) |
| **AC-17** | Endpoints API: contrato `/api/v1` completo (verbos, paths, payloads, codigos, auth) para auth/users, properties+lifecycle, media, search/detail, leads, banners/featured, seo, admin/metricas. | Revision documental: `api-contracts.md` reune la tabla completa de endpoints `/api/v1/*` por grupo, con metodo, ruta, roles, payload, respuesta y errores, mas error envelope y paginacion. Pasa si cada grupo de capacidad tiene sus endpoints y el envelope coincide con el CONTRATO. | `api-contracts.md` |
| **AC-18** | Validaciones: reglas de integridad y de negocio para entrada de datos (campos requeridos, formatos, slug regex, dinero minor units, geografia, consentimiento, etc.). | Revision documental: `validations.md` agrupa reglas `VALID-R#` por entidad/flujo, incluyendo slug regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`, dinero BIGINT minor + currency ISO 4217, y campos minimos para publicar. Pasa si cada flujo de escritura tiene validaciones. | `validations.md` (`VALID-R#`) |
| **AC-19** | Metricas: modelo de captura de dos capas (eventos `PropertyView` append-only + contadores denormalizados), `MetricEventType`/`ViewSource`, exposicion en dashboards. | Revision documental: `metrics.md` define la capa de eventos (tipos `MetricEventType`, atribucion `ViewSource`) y los contadores (`views_count`/`clicks_count`/`leads_count`, banner/featured), mas privacidad (`ip_hash`/`session_hash`). Pasa si la fuente de verdad append-only esta clara. | `metrics.md`; `src/property_view.py` (futuro) |
| **AC-20** | Atributos transversales: mobile-first + escalabilidad + seguridad + SEO + administracion sin tocar codigo (config/datos en vez de despliegue). | Revision documental: `architecture.md` describe escalabilidad horizontal stateless, mobile-first y administracion data-driven (banners, destacados, localidades, SEO, tipos, amenities gestionables sin deploy). Pasa si "administrable sin tocar codigo" esta sustentado por entidades de configuracion. | `architecture.md`; transversal a `security.md`, `seo.md`, `banners-featured.md`, `data-model.md` |
| **AC-21** | Spec clara, modular, verificable y lista para backlog: un equipo puede convertir cada documento en tareas accionables. | Verificacion estructural: el paquete tiene 1 documento por capacidad; cada uno sigue el formato del CONTRATO (titulo + linea de indice/DoD + Resumen + Reglas `<PREFIJO>-R#`); requisitos `FR-###`/`NFR-###` solo en `spec.md`; este documento mapea AC->DoD->documento. Pasa si toda regla es atomica y trazable a un AC. | **Este documento** (`acceptance-criteria.md`); `spec.md`; todo el paquete |
| **AC-22** | Sin ambiguedades criticas: roles, estados de propiedad, permisos, publicacion, edicion, imagenes, leads, banners y destacados quedan unicamente determinados. | Verificacion de trazabilidad: la seccion "Trazabilidad de ausencia de ambiguedades" abajo enlaza cada tema critico al documento que lo resuelve de forma deterministica (un solo valor/regla por caso). Pasa si ningun tema critico tiene multiples interpretaciones abiertas. | **Este documento** (seccion AC-22); `roles-permissions.md`, `property-lifecycle.md`, `media-pipeline.md`, `leads.md`, `banners-featured.md` |
| **AC-23** | Output limpio, modular y listo para produccion: formato consistente, nomenclatura del CONTRATO en ingles, limite de lineas del harness respetado, sin archivos basura. | Verificacion automatizable: `make dev-check` (hooks) pasa; ningun documento excede 1000 lineas (limite duro) ni el objetivo de 800; nomenclatura de codigo coincide con el CONTRATO; sin `utils.py`/`helpers.py`/temp en root. Pasa si los hooks del harness no bloquean. | **Este documento**; harness (`.claude/hooks/`, `.pre-commit-config.yaml`); todo el paquete |

## Trazabilidad de ausencia de ambiguedades (AC-22)

Para `AC-22` se confirma que cada tema critico del DoD #22 queda **sin ambiguedad**:
existe exactamente **un** documento normativo que fija su valor/regla, y ese
documento usa la nomenclatura exacta del CONTRATO (sin alternativas inventadas).
Cualquier consumidor (frontend, backend, QA) obtiene la misma interpretacion.

| Tema critico | Resolucion deterministica | Documento que lo resuelve |
|---|---|---|
| **Roles** | 5 roles fijos `VISITOR` < `REGISTERED_USER` < `AGENT` < `ADMIN` < `SUPERADMIN`; `VISITOR` no es fila en `roles`; autorizacion por set explicito de `permission_codes`, no por nivel numerico. | `roles-permissions.md` (`RBAC-R#`) |
| **Permisos** | Catalogo cerrado de codigos `resource:action` del CONTRATO; semantica `*_own` (ownership por `Property.owner_id == user.id` y cascada) vs `*_any` resuelta sin solapamiento. | `roles-permissions.md` (`RBAC-R#`) |
| **Estados de propiedad** | 8 estados `PublicationStatus` y conjunto cerrado de transiciones; cada transicion tiene actor (rol) y precondicion unica; no hay transiciones implicitas. | `property-lifecycle.md` (`LIFECYCLE-R#`) |
| **Publicacion** | Flujo unico `DRAFT -> PENDING (submit) -> PUBLISHED (approve, set published_at)` con `REJECTED`/resubmit; "solo `PUBLISHED` visible (200)"; `SOLD`/`RENTED` -> 301/410; `PAUSED`/`REJECTED`/`DRAFT`/`DELETED` -> 404. | `property-lifecycle.md` (`LIFECYCLE-R#`); visibilidad SEO en `seo.md` (`SEO-R#`) |
| **Edicion** | Reglas de edicion por estado y rol; criterio explicito de cuando una edicion material de `PUBLISHED` exige re-revision (regla determinada, no "a definir"). | `property-lifecycle.md` (`LIFECYCLE-R#`) |
| **Imagenes** | `PropertyImage` es el unico registro de medio; **una sola `MAIN` por propiedad** (constraint); orden por `position`; `main_image_id` denormalizado apunta a la `MAIN`; validaciones y pipeline async unicos. | `media-pipeline.md` (`MEDIA-R#`) |
| **Leads** | Maquina de estados `LeadStatus` cerrada, canales `LeadChannel` fijos, captura publica sin auth, consentimiento obligatorio y asignacion a `owner_id` (agente) deterministica. | `leads.md` (`LEAD-R#`) |
| **Banners** | 5 `BannerPosition` fijas, segmentacion por locality/city/operation/kind, seleccion por `priority` + ventana `starts_at`/`ends_at` + `is_active`; sin reglas de seleccion ambiguas. | `banners-featured.md` (`BANNER-R#`) |
| **Destacados** | `FeaturedScope` cerrado (`HOME`/`SEARCH_RESULTS`/`LOCALITY`); `locality_id` **requerido si y solo si** `scope=LOCALITY`; orden por `priority` + ventana; 1:1 con `Property`. | `banners-featured.md` (`FEATURED-R#`) |

Conclusion `AC-22`: los nueve temas criticos tienen resolucion unica y trazable.
No quedan ambiguedades criticas abiertas en el paquete de especificacion; cada tema
critico se resuelve en exactamente un documento normativo con la nomenclatura del
CONTRATO.

## Estado de cobertura por este entregable

Este documento (`acceptance-criteria.md`) **marca los 23 criterios `AC-01`..`AC-23`
como cubiertos** por el paquete `specs/001-listing-catalog/`:

- `AC-01`..`AC-20`: cubiertos por sus documentos de capacidad dedicados ya presentes
  (ver columna "Documento(s)/modulo(s)"), incluidos `ux-ui.md` (AC-16) y
  `api-contracts.md` (AC-17).
- `AC-21`, `AC-22`, `AC-23`: cubiertos **por este entregable** (estructura,
  trazabilidad de ausencia de ambiguedad y conformidad de formato/harness).

## Open Questions

- **Contrato API (AC-17):** `api-contracts.md` define el contrato `/api/v1` de forma
  manual; cuando exista el backend FastAPI conviene regenerarlo/validarlo contra el
  OpenAPI real para evitar deriva entre spec y codigo.
- **Admin sin tocar codigo (AC-20):** confirmar el alcance exacto de
  administracion data-driven (que entidades de configuracion son editables por
  panel admin: banners, destacados, localidades, tipos, amenities, SEO) frente a
  lo que requiere despliegue, para cerrar el item #20 sin ambiguedad operativa.
