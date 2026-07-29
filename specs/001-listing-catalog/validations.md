# Validaciones — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #18.

## Resumen

Catalogo unico de validaciones funcionales y tecnicas por entidad/campo del
sistema **Listing**. Cada regla declara su **capa de aplicacion** (cliente /
API / dominio / DB) bajo el principio de *defensa en profundidad*: el cliente
mejora la UX, la **API** (Pydantic v2 + FastAPI) es la frontera autoritativa,
el **dominio** aplica invariantes de negocio (incluido el esqueleto Python
`__post_init__`) y la **DB** (PostgreSQL 16 + PostGIS + pg_trgm) materializa
constraints duros. Mensajes de error se devuelven en el envelope canonico
`{"error":{"code","message","details"}}` con HTTP 422 para validacion de
entrada y 409 para conflictos de estado/unicidad.

Capas (notacion en tablas): **C**=cliente (React SPA), **A**=API (Pydantic),
**D**=dominio (`__post_init__`/state machine), **DB**=base de datos.

### Alineacion con el esqueleto Python (`__post_init__`)

El CONTRATO describe entidades como dataclasses con validacion en
`__post_init__`. Toda regla marcada con capa **D** DEBE implementarse en el
`__post_init__` (o metodo de transicion) de la dataclass correspondiente y
lanzar `ValueError` con el `message` indicado. Patron de referencia tomado de
`src/listing_catalog.py` (`Listing.__post_init__` levanta `ValueError` para
campos requeridos y no-negativos): se generaliza a todas las entidades. La API
captura estos `ValueError` de dominio y los re-emite como HTTP 422 con el
envelope de error; nunca se confia solo en el cliente.

### Codigos de error (envelope `error.code`)

| Codigo | Significado | HTTP |
|---|---|---|
| `validation_error` | Campo invalido (formato/rango/requerido) | 422 |
| `required_field` | Campo obligatorio ausente o vacio | 422 |
| `out_of_range` | Valor fuera de rango permitido | 422 |
| `invalid_format` | Formato/regex/MIME invalido | 422 |
| `invalid_enum` | Valor no pertenece al Enum | 422 |
| `duplicate` | Violacion de unicidad (slug/email/etc.) | 409 |
| `invalid_transition` | Transicion de estado no permitida | 409 |
| `precondition_failed` | Falta requisito (p.ej. >=1 imagen para publicar) | 422 |
| `forbidden` | Permiso/ownership insuficiente | 403 |
| `not_found` | Entidad referenciada inexistente | 404 |
| `payload_too_large` | Imagen excede tamano permitido | 413 |
| `unsupported_media_type` | MIME no soportado | 415 |

---

## Convenciones transversales de campo

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `id` | UUID v4 string; generado por servidor, nunca aceptado del cliente en create | `id is server-generated` | A, DB |
| `created_at`/`updated_at` | timestamptz UTC; gestionados por servidor (no editables) | `timestamps are read-only` | A, DB |
| `deleted_at` | nullable; solo set via soft delete; registros con `deleted_at` excluidos de lecturas publicas | `record is deleted` | D, DB |
| `currency` | CHAR(3) ISO 4217; uno de {USD,EUR,COP,MXN,ARS,CLP,PEN,BRL} | `currency must be a valid ISO 4217 code` | A, D, DB |
| Montos `*_amount` | BIGINT en minor units (centavos); entero >=0; NUNCA float | `amount must be an integer in minor units` | A, D, DB |
| `slug` | regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`; unico por entidad | `slug must match ^[a-z0-9]+(?:-[a-z0-9]+)*$` | A, D, DB |
| `email` (cualquiera) | RFC 5322 simplificado; normalizado a minusculas + trim | `invalid email format` | A, D |
| `phone`/`whatsapp` | E.164 `^\+[1-9]\d{7,14}$` | `phone must be in E.164 format (+<country><number>)` | A, D |
| Texto libre | sanitizado (strip HTML peligroso); trim de extremos; sin caracteres de control | `text contains disallowed content` | A, D |
| FKs `<entity>_id` | UUID existente y no soft-deleted | `referenced <entity> does not exist` | A, DB |

---

## Property (`properties`)

### Campos requeridos y de negocio

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `title` | requerido; trim; longitud 5..160; sanitizado | `title is required (5-160 chars)` | C, A, D |
| `slug` | requerido; patron `{operation}-{kind}-{title-kebab}-{shortid}`; cumple slug regex; unico | `slug must be unique and match the slug pattern` | A, D, DB |
| `description` | requerido para PENDING/PUBLISHED; longitud 30..5000; sanitizada (sin `<script>`, sin HTML activo) | `description is required (30-5000 chars)` | C, A, D |
| `operation_type` | requerido; OperationType in {sale,rent,temporary} | `operation_type must be one of sale, rent, temporary` | A, D, DB |
| `property_kind` | requerido; PropertyKind in {house,apartment,lot,office,commercial,farm,other} | `property_kind is invalid` | A, D, DB |
| `condition` | requerido; PropertyCondition in {new,used,remodeled,under_construction} | `condition is invalid` | A, D, DB |
| `price_amount` | requerido; BIGINT minor units; entero; **>0** | `price_amount must be a positive integer in minor units` | C, A, D, DB |
| `currency` | requerido; ISO 4217 valida (ver transversales) | `currency must be a valid ISO 4217 code` | A, D, DB |
| `hoa_fees_amount` | nullable; si presente BIGINT minor units entero >=0 | `hoa_fees_amount must be a non-negative integer in minor units` | A, D, DB |
| `country` | requerido; ISO 3166-1 alpha-2 (mayusculas) | `country must be an ISO 3166-1 alpha-2 code` | A, D |
| `state_province` | requerido; 2..120 chars | `state_province is required` | C, A, D |
| `city` | requerido; 2..120 chars | `city is required` | C, A, D |
| `locality_id` | requerido; FK a Location existente, `is_active=true` | `locality must reference an active Location` | A, DB |
| `neighborhood` | nullable; <=120 chars | `neighborhood must be <= 120 chars` | A, D |
| `address` | nullable; <=255 chars; privado salvo `address_is_public=true` | `address must be <= 255 chars` | A, D |
| `address_is_public` | boolean; default false | `address_is_public must be boolean` | A, D |
| `location_point` | requerido; geography(POINT,4326); lat ∈ [-90,90], lng ∈ [-180,180] | `coordinates out of range (lat -90..90, lng -180..180)` | C, A, D, DB |
| `area_total` | requerido; numeric > 0 | `area_total must be greater than 0` | C, A, D, DB |
| `area_built` | nullable; numeric > 0 si presente; `area_built <= area_total` | `area_built must be > 0 and <= area_total` | A, D |
| `bedrooms` | requerido; int >=0; <=50 (cordura) | `bedrooms must be an integer 0..50` | C, A, D, DB |
| `bathrooms` | requerido; int >=0; <=50 | `bathrooms must be an integer 0..50` | C, A, D, DB |
| `parking_spots` | requerido; int >=0; <=50 | `parking_spots must be an integer 0..50` | C, A, D, DB |
| `year_built` | nullable; int 1800..(año_actual+5) si presente | `year_built must be between 1800 and current year + 5` | A, D |
| `status` | PublicationStatus; default DRAFT en create; transiciones via state machine | `status transition is not allowed` | A, D, DB |
| `main_image_id` | nullable; debe referenciar PropertyImage de la MISMA propiedad con `role=main` | `main_image_id must reference a MAIN image of this property` | A, D, DB |
| `is_featured` | boolean; gestionado via FeaturedProperty (no editable directo por owner) | `is_featured is managed by featured module` | A, D |
| `primary_cta` | requerido; valor en CTA permitido (whatsapp/call/form/visit); ver Lead | `primary_cta is invalid` | A, D |
| `available_from` | nullable; date; no anterior a today para RENT/TEMPORARY (advertencia, no bloqueo) | `available_from should not be in the past` | C, A |
| `views_count`/`clicks_count`/`leads_count` | enteros >=0; denormalizados; read-only para clientes | `counters are read-only` | A, DB |
| `published_at` | nullable; set por sistema al aprobar; read-only | `published_at is set on approval` | D, DB |

### Precondiciones de publicacion (DRAFT -> PENDING -> PUBLISHED)

| Requisito | Regla | Mensaje de error | Capa |
|---|---|---|---|
| Campos minimos | title, description, operation_type, property_kind, condition, price_amount, currency, country, state_province, city, locality_id, location_point, area_total, bedrooms, bathrooms, parking_spots todos validos | `cannot submit for review: required fields missing` | A, D |
| Imagenes | **>=1 imagen** asociada y exactamente **una con `role=main`** | `at least one image with a MAIN image is required to publish` | A, D, DB |
| SEO minimo | SeoMetadata 1:1 con meta_title y meta_description presentes (ver seo.md) | `SEO metadata is required to publish` | A, D |

### Reglas (VALID-R#)

- **VALID-R1**: Property en create nace en `status=DRAFT`; el cliente NO puede
  fijar `status`, `published_at`, contadores ni `is_featured`.
- **VALID-R2**: `price_amount` es entero estricto en minor units y **>0**
  (alineado al patron `price_cents < 0 -> ValueError` del esqueleto, endurecido
  a `<=0`). Float o decimal con parte fraccionaria => 422.
- **VALID-R3**: Coordenadas validadas en rango WGS84 en capa A y D; PostGIS
  rechaza geometrias fuera de SRID 4326 en DB.
- **VALID-R4**: `submit_for_review` (DRAFT->PENDING) exige campos minimos +
  >=1 imagen + 1 MAIN; falla con `precondition_failed`.
- **VALID-R5**: `mark_sold` requiere `operation_type=sale`; `mark_rented`
  requiere `operation_type in {rent,temporary}` (ver property-lifecycle.md).
- **VALID-R6**: `slug` se autogenera con patron
  `{operation}-{kind}-{title-kebab}-{shortid}` y es inmutable tras PUBLISHED
  (cambios crean `redirect_from` en SEO, no rompen el slug vivo).
- **VALID-R7**: `area_built <= area_total` cuando ambos presentes.
- **VALID-R8**: `main_image_id` debe pertenecer a la propiedad y tener
  `role=main`; consistencia garantizada por constraint DB (ver PropertyImage).

---

## PropertyImage / media (`property_images`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `property_id` | requerido; FK a Property existente, no soft-deleted | `property does not exist` | A, DB |
| `media_kind` | MediaKind in {image,video,floor_plan,virtual_tour} | `media_kind is invalid` | A, D, DB |
| `role` | ImageRole in {main,gallery}; **una sola `main` por property** | `only one MAIN image is allowed per property` | A, D, DB |
| `content_type` (MIME) | imagenes: `image/jpeg`, `image/png`, `image/webp`; rechazar otros | `unsupported image type (jpeg, png, webp only)` | C, A, D |
| Tamano (`bytes`) | imagen <= **8 MB** (8_388_608 bytes); >0 | `image must be <= 8 MB` | C, A, D |
| Dimensiones (`width`/`height`) | min 800x600 px; max 8000x8000 px | `image dimensions must be between 800x600 and 8000x8000` | C, A, D |
| `original_url`/`cdn_url`/`thumb_url` | URLs https validas; generadas por pipeline tras upload | `media URLs must be valid https URLs` | A, D |
| `position` | int >=0; unico por property (orden de galeria) | `position must be a unique non-negative integer` | A, D, DB |
| `alt_text` | requerido para `role=main`; <=160 chars (accesibilidad/SEO) | `alt_text is required for the MAIN image (<=160 chars)` | C, A, D |
| Cantidad por property | min 1 para publicar; **max 30** imagenes | `a property can have at most 30 images` | A, D |
| Video/virtual_tour | URL externa validada; no cuenta en limite de 30 imagenes | `invalid media URL` | A, D |

### Reglas (VALID-R#)

- **VALID-R9**: Constraint DB (unique parcial) garantiza **una sola** fila con
  `role=main` por `property_id`.
- **VALID-R10**: Validacion de MIME real por *magic bytes* en capa A (no solo
  por extension ni header `Content-Type` del cliente). MIME no permitido => 415.
- **VALID-R11**: Limite de peso => HTTP 413 (`payload_too_large`); dimensiones
  fuera de rango => 422.
- **VALID-R12**: `position` reindexado de forma estable; el sistema impide
  huecos/duplicados al reordenar.

---

## Location (`locations`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `country`/`state_province`/`city`/`locality` | requeridos no vacios; trim | `location fields are required` | A, D |
| `slug` | requerido; slug regex; unico | `location slug must be unique` | A, D, DB |
| `parent_id` | nullable; FK a Location; no auto-referencia; sin ciclos | `parent_id cannot create a cycle` | A, D |
| `center_point` | geography; lat ∈ [-90,90], lng ∈ [-180,180] | `coordinates out of range` | A, D, DB |
| `is_active` | boolean; localities inactivas no seleccionables en alta de Property | `inactive location cannot be selected` | A, D |

---

## User (`users`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `email` | requerido; formato valido; normalizado minusculas+trim; unico | `email is required and must be unique` | C, A, D, DB |
| `password` (entrada) | min 10 chars; >=1 mayus, >=1 minus, >=1 digito; nunca persistido en claro | `password must be >= 10 chars with mixed case and a digit` | C, A, D |
| `password_hash` | bcrypt/argon2; nunca aceptado del cliente | `password_hash is server-managed` | A, D |
| `full_name` | requerido; 2..120 chars; sanitizado | `full_name is required (2-120 chars)` | C, A, D |
| `phone`/`whatsapp` | nullable; E.164 si presentes | `phone must be in E.164 format` | C, A, D |
| `role_id` | FK a Role; default `registered_user`; solo ADMIN+ puede asignar AGENT/ADMIN/SUPERADMIN | `insufficient privilege to assign this role` | A, D, DB |
| `is_active`/`email_verified` | boolean; gestionados por sistema | `flag is server-managed` | A, D |
| `avatar_url` | nullable; https valida | `avatar_url must be a valid https URL` | A, D |

### Reglas (VALID-R#)

- **VALID-R13**: Email normalizado (lowercase+trim) ANTES de verificar
  unicidad; colision => 409 `duplicate`.
- **VALID-R14**: Asignacion de rol respeta jerarquia (ver roles-permissions.md): nadie puede
  asignar un rol >= al propio salvo SUPERADMIN.

---

## Lead (`leads`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `property_id` | requerido; FK a Property **PUBLISHED** | `lead must target a published property` | A, D, DB |
| `name` | requerido; 2..120 chars; sanitizado | `name is required (2-120 chars)` | C, A, D |
| `email` | requerido si `channel=form`; formato valido + normalizado | `a valid email is required` | C, A, D |
| `phone` | requerido si `channel in {whatsapp,call,visit}`; E.164 | `a valid phone (E.164) is required for this channel` | C, A, D |
| `message` | requerido para `channel=form`; 5..1000 chars; sanitizado | `message is required (5-1000 chars)` | C, A, D |
| `channel` | LeadChannel in {form,whatsapp,call,visit} | `channel is invalid` | A, D, DB |
| `status` | LeadStatus; default `new`; transiciones via leads.md | `lead status transition is not allowed` | A, D, DB |
| `consent_given` | requerido **true** para crear lead | `consent is required to submit a lead` | C, A, D |
| `consent_text` | requerido no vacio cuando `consent_given=true` (texto mostrado al usuario) | `consent_text must be recorded` | A, D |
| `owner_id` | nullable al crear; asignado a un AGENT; FK valida | `assigned agent does not exist` | A, DB |
| `source_ip`/`user_agent` | capturados por servidor; no del cliente | `source metadata is server-captured` | A |
| `utm` | json; claves whitelisted (utm_source/medium/campaign/term/content) | `invalid utm payload` | A, D |
| `contacted_at` | nullable; set al pasar a `contacted` | `contacted_at is set on status change` | D |

### Reglas (VALID-R#)

- **VALID-R15**: `consent_given=true` es obligatorio (cumplimiento privacidad,
  ver security.md); sin consentimiento => 422 `precondition_failed`.
- **VALID-R16**: Requisito de email/phone es condicional al `channel`.
- **VALID-R17**: Anti-abuso: rate limit por `ip_hash`/`session` aplicado antes
  de la validacion de negocio (ver performance/security); exceso => 429.

---

## Banner (`banners`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `title` | requerido; 3..120 chars | `title is required (3-120 chars)` | C, A, D |
| `description` | nullable; <=255 chars; sanitizada | `description must be <= 255 chars` | A, D |
| `image_desktop_url` | **requerido**; https valida; imagen accesible | `image_desktop_url is required` | C, A, D |
| `image_mobile_url` | **requerido**; https valida | `image_mobile_url is required` | C, A, D |
| `cta_label` | requerido; 2..40 chars | `cta_label is required (2-40 chars)` | C, A, D |
| `cta_url` | requerido; URL https valida (esquema http/https, host valido) | `cta_url must be a valid URL` | C, A, D |
| `position` | BannerPosition in {home_hero,home_inline,listing_top,listing_inline,detail_sidebar} | `position is invalid` | A, D, DB |
| `priority` | entero **>=0**; mayor = mas prioritario | `priority must be a non-negative integer` | C, A, D, DB |
| `starts_at`/`ends_at` | timestamptz; **`starts_at < ends_at`** | `starts_at must be before ends_at` | C, A, D, DB |
| `is_active` | boolean; default true | `is_active must be boolean` | A, D |
| `target_locality_id` | nullable; FK Location valida si presente | `target locality does not exist` | A, DB |
| `target_city` | nullable; <=120 chars | `target_city must be <= 120 chars` | A, D |
| `target_operation` | nullable; OperationType valido si presente | `target_operation is invalid` | A, D |
| `target_kind` | nullable; PropertyKind valido si presente | `target_kind is invalid` | A, D |
| `impressions_count`/`clicks_count` | enteros >=0; read-only | `counters are read-only` | A, DB |

### Reglas (VALID-R#)

- **VALID-R18**: `starts_at < ends_at` validado en A, D y constraint CHECK en DB.
- **VALID-R19**: `priority` entero >=0 (CHECK en DB). Empates resueltos por
  `created_at` mas reciente.
- **VALID-R20**: Ambas imagenes (desktop y mobile) son requeridas; faltante =>
  422 `required_field`.

---

## FeaturedProperty (`featured_properties`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `property_id` | requerido; **unico** (1:1 con Property); Property debe estar PUBLISHED | `only a published property can be featured, once` | A, D, DB |
| `scope` | FeaturedScope in {home,search_results,locality} | `scope is invalid` | A, D, DB |
| `priority` | entero >=0 | `priority must be a non-negative integer` | A, D, DB |
| `locality_id` | nullable; **requerido si `scope=locality`**; FK Location valida | `locality_id is required when scope is locality` | A, D, DB |
| `starts_at`/`ends_at` | timestamptz; `starts_at < ends_at` | `starts_at must be before ends_at` | C, A, D, DB |
| `is_active` | boolean; default true | `is_active must be boolean` | A, D |

### Reglas (VALID-R#)

- **VALID-R21**: Constraint condicional: `scope=locality => locality_id NOT
  NULL` (CHECK en DB + validacion D).
- **VALID-R22**: Una Property destacada sincroniza `Property.is_featured`; no se
  edita `is_featured` directamente (ver VALID-R1).

---

## SeoMetadata (`seo_metadata`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `entity_type`/`entity_id` | requeridos; par valido y existente | `seo target does not exist` | A, DB |
| `slug` | requerido; slug regex; unico global | `seo slug must be unique` | A, D, DB |
| `meta_title` | requerido; 10..70 chars (limite SERP) | `meta_title is required (10-70 chars)` | A, D |
| `meta_description` | requerido; 50..160 chars | `meta_description is required (50-160 chars)` | A, D |
| `og_image_url` | nullable; https valida | `og_image_url must be a valid https URL` | A, D |
| `canonical_url` | nullable; URL absoluta https valida | `canonical_url must be a valid absolute URL` | A, D |
| `robots` | default `index,follow`; valor de directivas valido | `invalid robots directive` | A, D |
| `redirect_from` | json array de slugs viejos; cada uno cumple slug regex; sin duplicar el slug actual | `redirect_from must be valid distinct slugs` | A, D |
| `jsonld` | json valido; schema.org coherente | `jsonld must be valid JSON-LD` | A, D |

---

## Favorite (`favorites`)

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `user_id` | requerido; FK User; usuario autenticado | `authentication required` | A, DB |
| `property_id` | requerido; FK Property PUBLISHED | `property does not exist or is not public` | A, D, DB |
| Unicidad | `unique(user_id, property_id)` | `property is already in favorites` | A, DB |

---

## PropertyView (`property_views`) — eventos de engagement

| Campo | Regla | Mensaje de error | Capa |
|---|---|---|---|
| `property_id` | requerido; FK Property | `property does not exist` | A, DB |
| `event_type` | MetricEventType in {view,cta_click,whatsapp_click,call_click,visit_request,share,favorite} | `event_type is invalid` | A, D, DB |
| `source` | ViewSource in {organic,search,featured,direct,share} | `source is invalid` | A, D, DB |
| `session_hash`/`ip_hash` | hash anonimizado (sin PII en claro); generado por servidor | `tracking identifiers are server-generated` | A |
| `referrer` | nullable; <=500 chars | `referrer must be <= 500 chars` | A, D |

### Reglas (VALID-R#)

- **VALID-R23**: PII (IP, sesion) se almacena **hasheada**; nunca en claro
  (ver privacidad/security.md). Deduplicacion de `view` por
  `session_hash`+ventana para no inflar contadores.

---

## Validaciones de transicion de estado (Property)

Las transiciones de `status` se validan en la **state machine de dominio**
(capa D) y se referencian en property-lifecycle.md. Toda transicion no listada
es invalida y responde 409 `invalid_transition`.

| Transicion | Precondicion clave | Mensaje de error | Capa |
|---|---|---|---|
| create -> DRAFT | owner/agent autenticado | `forbidden` | A, D |
| DRAFT -> PENDING | campos minimos + >=1 imagen + 1 MAIN + SEO minimo | `cannot submit for review: requirements not met` | A, D |
| PENDING -> PUBLISHED | actor con `property:approve`; set `published_at` | `only approvers can publish` | A, D |
| PENDING -> REJECTED | actor con `property:reject`; `reason` requerido | `rejection reason is required` | A, D |
| REJECTED -> PENDING | owner (resubmit); requisitos de DRAFT->PENDING | `cannot resubmit: requirements not met` | A, D |
| PUBLISHED -> PAUSED | owner/admin | `forbidden` | A, D |
| PAUSED -> PUBLISHED | owner/admin | `forbidden` | A, D |
| PUBLISHED\|PAUSED -> SOLD | `operation_type=sale` | `mark_sold requires operation_type=sale` | A, D |
| PUBLISHED\|PAUSED -> RENTED | `operation_type in {rent,temporary}` | `mark_rented requires operation_type rent/temporary` | A, D |
| cualquiera(no DELETED) -> DELETED | owner propio / admin cualquiera | `forbidden` | A, D |
| duplicate | clona a DRAFT, nuevo id+slug, metricas en 0 | `duplicate failed: source not found` | A, D |

### Reglas (VALID-R#)

- **VALID-R24**: La validez de la transicion se evalua ANTES que permisos no es
  cierto: primero se verifica autenticacion+permiso (403), luego la legalidad de
  la transicion (409). Orden: 401 -> 403 -> 404 -> 422/409.
- **VALID-R25**: La state machine es la unica autorizada a mutar `status`,
  `published_at` y contadores derivados; mutacion directa via API => rechazada.

---

## Permisos y ownership (resumen, detalle en roles-permissions.md)

| Operacion | Regla de ownership/permiso | Mensaje de error | Capa |
|---|---|---|---|
| `property:update_own` | actor == `owner_id` o tiene `property:update_any` | `you can only edit your own listings` | A, D |
| `property:delete_own` | actor == `owner_id` o `property:delete_any` | `you can only delete your own listings` | A, D |
| `property:pause_own` | actor == `owner_id` o admin | `forbidden` | A, D |
| `image:upload_own` | sobre Property propia o `image:manage_any` | `you can only manage images of your own listings` | A, D |
| `lead:read_own` | lead.owner_id == actor o `lead:read_any` | `you can only read your assigned leads` | A, D |
| `favorite:manage_own` | favorite.user_id == actor | `forbidden` | A, D |
| `property:approve`/`reject`/`feature` | rol ADMIN+ con permiso explicito | `requires moderation privileges` | A, D |
| `banner:manage`/`featured:manage`/`seo:manage`/`config:manage` | ADMIN/SUPERADMIN | `requires admin privileges` | A, D |

### Reglas (VALID-R#)

- **VALID-R26**: Ownership se valida en cada mutacion sobre recurso propio
  (`*_own`) comparando `actor.id` contra el campo owner del recurso; el bypass
  solo via permiso `*_any`. Fallo => 403 `forbidden`.
- **VALID-R27**: Lecturas publicas (`property:read_public`) no requieren auth y
  solo exponen Property `status=PUBLISHED` y campos publicos (address oculto si
  `address_is_public=false`).

---

## Resumen de capa (defensa en profundidad)

| Capa | Responsabilidad de validacion | Tecnologia |
|---|---|---|
| **C** Cliente | UX inmediata: requeridos, longitudes, rangos, formato visible | React 18 SPA |
| **A** API | Frontera autoritativa: tipos, enums, formato, FK existence, MIME magic-bytes, normalizacion, rate limit | FastAPI + Pydantic v2 |
| **D** Dominio | Invariantes de negocio + state machine en `__post_init__`/metodos; `ValueError` -> 422 | dataclasses (CONTRATO) |
| **DB** Base de datos | Constraints duros: NOT NULL, UNIQUE, CHECK, FK, parcial-unique (MAIN), SRID 4326 | PostgreSQL 16 + PostGIS |

> Regla global: nunca confiar solo en el cliente. Toda regla con capa **C**
> DEBE estar tambien en **A**. Toda invariante de negocio DEBE estar en **D**.
> Toda regla de integridad/unicidad DEBE tener respaldo en **DB**.

## Open Questions

- Limites exactos de peso (8 MB) y dimensiones de imagen: confirmar con equipo
  de media/CDN si se desea sobreescribir por `media_kind`.
- `available_from` en el pasado: ¿bloqueo duro (422) o solo advertencia? Aqui
  se modela como advertencia no bloqueante; confirmar con producto.
- Politica de re-revision tras edicion material de una Property PUBLISHED:
  definir que campos disparan PUBLISHED->PENDING (pendiente en
  property-lifecycle.md).
- Longitud minima de `password` (10 chars) y politica de complejidad: alinear
  con security.md si difiere.
