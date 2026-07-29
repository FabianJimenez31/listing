# API Contracts — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #17.

## Resumen

Contratos de la API REST de Listing. Base: `/api/v1`. Todas las rutas cuelgan de ahi (p. ej. `POST /api/v1/auth/login`). FastAPI (Python 3.13) sirve JSON; React 18 SPA (CSR) consume estos endpoints. Las **lecturas publicas** (catalogo, detalle, busqueda, banners, destacados) no requieren auth; el resto exige **JWT Bearer**. Este documento define, por grupo, la **tabla completa de endpoints** y, para los principales, el detalle `Metodo | Ruta | Descripcion | Roles | Payload | Respuesta | Errores`.

Reglas de identificadores de codigo (entidades, campos, enums, permisos, estados) en INGLES exacto segun el CONTRATO. Las reglas de este documento usan prefijo `API-R#`.

### Convenciones transversales

- **Auth**: `Authorization: Bearer <access_token>` (JWT). El access token es de corta vida; se renueva con el refresh token via `POST /auth/refresh`. Lecturas publicas omiten el header.
- **Roles**: `VISITOR` (no autenticado) < `REGISTERED_USER` < `AGENT` < `ADMIN` < `SUPERADMIN`. La columna "Roles" lista el **minimo** requerido; un rol superior siempre puede. Cuando aplica `*_own` vs `*_any`, el owner usa `_own`, `ADMIN+` usa `_any`. Los permisos efectivos son los codigos `resource:action` del CONTRATO (ver `roles-permissions.md`).
- **Content-Type**: `application/json` salvo upload directo a S3 (presign) que va a object storage, no a la API.
- **IDs**: `id` UUID v4 (string) en path: `/properties/{property_id}`. Tambien se aceptan **slugs** en rutas publicas de detalle de propiedad (ver Search/Detail).
- **Timestamps**: ISO 8601 UTC en respuestas (`created_at`, `updated_at`, etc.).
- **Dinero**: `price_amount` BIGINT en minor units (centavos) + `currency` CHAR(3). Nunca float.
- **Idempotencia**: mutaciones de ciclo de vida son idempotentes salvo donde se indique (repetir `approve` sobre `PUBLISHED` -> 409).

### Error envelope (CONTRATO)

Todas las respuestas de error usan:

```json
{ "error": { "code": "string_machine", "message": "Mensaje legible", "details": { } } }
```

`code` es un slug estable maquina-legible; `message` legible (es); `details` opcional (p. ej. errores de validacion por campo). Codigos HTTP y `error.code` canonicos:

| HTTP | error.code               | Uso |
|------|--------------------------|-----|
| 400  | `validation_error`       | Body/query invalido. `details` = mapa campo->mensajes. |
| 401  | `unauthenticated`        | Falta/expira/invalido el Bearer. |
| 403  | `forbidden`              | Autenticado pero sin permiso/rol. |
| 404  | `not_found`              | Recurso inexistente o no visible publicamente. |
| 409  | `conflict`               | Estado/unicidad: slug/email duplicado, transicion invalida. |
| 410  | `gone`                   | Recurso retirado (propiedad `SOLD`/`RENTED` segun seo.md). |
| 413  | `payload_too_large`      | Imagen excede limite (ver media-pipeline.md). |
| 422  | `unprocessable_entity`   | Reglas de negocio (p. ej. faltan campos minimos para submit). |
| 429  | `rate_limited`           | Rate limit (Redis). Header `Retry-After`. |
| 500  | `internal_error`         | Error no controlado. |

### Paginacion (CONTRATO)

Listados aceptan `?page=` (default 1) y `?page_size=` (default 20, max 100). Respuesta:

```json
{ "data": [ /* ... */ ], "meta": { "page": 1, "page_size": 20, "total": 137, "total_pages": 7 } }
```

Errores comunes en listados: `400 validation_error` (page/page_size fuera de rango), `429 rate_limited`. No se repiten en cada fila de abajo salvo que sean especificos.

### Reglas (API-R#)

| Regla | Descripcion |
|-------|-------------|
| API-R1 | Toda mutacion (POST/PUT/PATCH/DELETE) requiere Bearer salvo `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/verify-email`, `POST /leads` y `POST /banners/{id}/track*` y `POST /metrics/events` (publicos). |
| API-R2 | Lecturas de catalogo (`/search`, `/properties/{slug}` publico, `/banners/resolve`, `/featured`, `/locations`, `/property-types`, `/amenities`) son publicas (rol `VISITOR`). |
| API-R3 | Visibilidad publica de Property: solo `PUBLISHED` devuelve 200; `SOLD`/`RENTED` -> 301/410 (seo.md); `PAUSED`/`REJECTED`/`DRAFT`/`DELETED` -> 404. |
| API-R4 | Acciones de ciclo de vida son endpoints dedicados `POST /properties/{id}/<accion>`, no `PATCH` de `status`. El campo `status` es de solo lectura via API. |
| API-R5 | Endpoints `_own` resuelven ownership por `owner_id == current_user.id`; `ADMIN+` accede a cualquiera con el permiso `_any`. |
| API-R6 | Respuestas publicas de Property nunca exponen `address` si `address_is_public=false` ni PII de leads; `location_point` se devuelve difuminado si address no es publica. |
| API-R7 | Todas las mutaciones de moderacion/lifecycle generan un `AuditLog` (action segun AuditAction) de forma transaccional. |
| API-R8 | Rate limiting (Redis) en endpoints publicos sensibles: `POST /auth/login`, `POST /auth/register`, `POST /leads`, `POST /metrics/events`. Exceso -> 429. |
| API-R9 | Soft delete: `DELETE` de Property es logico (`deleted_at` set, status->`DELETED`); no borra fila. Hard delete solo `SUPERADMIN` via herramienta interna (fuera de esta API). |

---

## 1. Auth — `/auth`

| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| POST | `/auth/register` | Registra `REGISTERED_USER`, envia email de verificacion | VISITOR |
| POST | `/auth/login` | Login con email+password, emite access+refresh | VISITOR |
| POST | `/auth/refresh` | Renueva access token desde refresh token | VISITOR (con refresh) |
| POST | `/auth/logout` | Revoca el refresh token actual | REGISTERED_USER |
| POST | `/auth/verify-email` | Confirma email con token de verificacion | VISITOR |
| POST | `/auth/resend-verification` | Reenvia email de verificacion | REGISTERED_USER |
| POST | `/auth/forgot-password` | Inicia reset de password (envia token) | VISITOR |
| POST | `/auth/reset-password` | Aplica nuevo password con token | VISITOR |
| GET | `/auth/me` | Devuelve el usuario autenticado + roles/permisos | REGISTERED_USER |

### Detalle

**POST `/auth/register`** — Crea cuenta `REGISTERED_USER` (role semilla `registered_user`).
- Roles: VISITOR. Rate limited (API-R8).
- Payload: `{ "email", "password", "full_name", "phone"?, "whatsapp"? }`
- Respuesta `201`: `{ "id", "email", "full_name", "email_verified": false, "role": "registered_user", "created_at" }`
- Errores: `400 validation_error` (email/password debiles), `409 conflict` (`email` ya existe), `429 rate_limited`.

**POST `/auth/login`** — Autentica y emite tokens.
- Roles: VISITOR. Rate limited.
- Payload: `{ "email", "password" }`
- Respuesta `200`: `{ "access_token", "refresh_token", "token_type": "Bearer", "expires_in": 900, "user": { "id", "email", "full_name", "role", "permissions": ["property:read_public", ...] } }`
- Errores: `400 validation_error`, `401 unauthenticated` (credenciales invalidas), `403 forbidden` (`is_active=false` o email no verificado segun politica), `429 rate_limited`.

**POST `/auth/refresh`** — Rotacion de refresh token.
- Payload: `{ "refresh_token" }`
- Respuesta `200`: `{ "access_token", "refresh_token", "token_type": "Bearer", "expires_in": 900 }`
- Errores: `401 unauthenticated` (refresh invalido/expirado/revocado).

**POST `/auth/logout`** — Revoca el refresh token (logout). Audit `LOGOUT`.
- Roles: REGISTERED_USER (Bearer). Payload: `{ "refresh_token" }`
- Respuesta `204` (sin body). Errores: `401 unauthenticated`.

**POST `/auth/verify-email`** — Marca `email_verified=true`.
- Payload: `{ "token" }`. Respuesta `200`: `{ "email_verified": true }`.
- Errores: `400 validation_error`, `409 conflict` (ya verificado), `410 gone` (token expirado).

**GET `/auth/me`** — Perfil + RBAC del actor. Roles: REGISTERED_USER.
- Respuesta `200`: `{ "id","email","full_name","phone","whatsapp","avatar_url","role","permissions":[...],"email_verified","is_active","created_at" }`
- Errores: `401 unauthenticated`.

---

## 2. Users — `/users`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/users` | Lista paginada de usuarios (filtros: `role`, `is_active`, `q`) | ADMIN | `user:read` |
| POST | `/users` | Crea usuario (incluye AGENT) con rol asignado | ADMIN | `user:create` |
| GET | `/users/{user_id}` | Detalle de un usuario | ADMIN (o self) | `user:read` |
| PATCH | `/users/{user_id}` | Actualiza datos de perfil | ADMIN (o self) | `user:update` |
| PATCH | `/users/me` | Actualiza perfil propio (`full_name`,`phone`,`whatsapp`,`avatar_url`) | REGISTERED_USER | — |
| DELETE | `/users/{user_id}` | Soft delete de usuario (`deleted_at`, `is_active=false`) | ADMIN | `user:delete` |
| PATCH | `/users/{user_id}/role` | Asigna rol al usuario | ADMIN | `role:assign` |
| PATCH | `/users/{user_id}/activate` | Activa/desactiva (`is_active`) | ADMIN | `user:update` |

### Detalle

**POST `/users`** — Alta de usuario administrativa (p. ej. crear AGENT).
- Roles: ADMIN. Permiso `user:create`.
- Payload: `{ "email","full_name","phone"?,"whatsapp"?,"role":"agent","is_active":true,"send_invite":true }`
- Respuesta `201`: objeto User (sin `password_hash`).
- Errores: `400 validation_error`, `403 forbidden`, `409 conflict` (`email` duplicado).

**PATCH `/users/{user_id}/role`** — Cambia `role_id`. Audit `ROLE_ASSIGN`.
- Roles: ADMIN (asignar `superadmin` -> solo SUPERADMIN). Permiso `role:assign`.
- Payload: `{ "role": "agent" }` (RoleName semilla).
- Respuesta `200`: User actualizado. Errores: `403 forbidden` (escalada de privilegio no permitida), `404 not_found`, `409 conflict`.

---

## 3. Roles & Permissions — `/roles`, `/permissions`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/roles` | Lista roles (con `permission_codes`) | ADMIN | `user:read` |
| POST | `/roles` | Crea rol no-sistema | SUPERADMIN | `permission:manage` |
| GET | `/roles/{role_id}` | Detalle de rol | ADMIN | `user:read` |
| PATCH | `/roles/{role_id}` | Edita `description` y permisos del rol | SUPERADMIN | `permission:manage` |
| DELETE | `/roles/{role_id}` | Elimina rol (bloqueado si `is_system=true`) | SUPERADMIN | `permission:manage` |
| PUT | `/roles/{role_id}/permissions` | Reemplaza set de permisos (M2M `role_permissions`) | SUPERADMIN | `permission:manage` |
| GET | `/permissions` | Catalogo de permisos `resource:action` | ADMIN | `user:read` |

### Detalle

**PUT `/roles/{role_id}/permissions`** — Establece los codigos de permiso de un rol.
- Roles: SUPERADMIN. Permiso `permission:manage`. Audit `PERMISSION_CHANGE`.
- Payload: `{ "permission_codes": ["property:approve","property:reject","banner:manage"] }`
- Respuesta `200`: Role con `permission_codes` resultantes.
- Errores: `400 validation_error` (codigo inexistente en `details`), `403 forbidden`, `404 not_found`, `409 conflict` (`is_system` inmutable).

---

## 4. Properties (CRUD) — `/properties`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/properties` | Lista propiedades del actor (panel agente) o todas (admin) | AGENT | `property:read_any`/own |
| POST | `/properties` | Crea propiedad en `DRAFT` | AGENT | `property:create` |
| GET | `/properties/{property_id}` | Detalle interno (cualquier status) para owner/admin | AGENT | `property:read_own`/`read_any` |
| PUT | `/properties/{property_id}` | Reemplazo completo de campos editables | AGENT (owner) | `property:update_own`/`update_any` |
| PATCH | `/properties/{property_id}` | Edicion parcial | AGENT (owner) | `property:update_own`/`update_any` |
| DELETE | `/properties/{property_id}` | Soft delete -> `DELETED` | AGENT (owner) | `property:delete_own`/`delete_any` |

### Detalle

**POST `/properties`** — Crea borrador. Genera `slug` `{operation}-{kind}-{title-kebab}-{shortid}`. status=`DRAFT`. Audit `CREATE`.
- Roles: AGENT. Permiso `property:create`.
- Payload (campos editables):
```json
{
  "title": "Apartamento luminoso en Chapinero",
  "description": "...",
  "operation_type": "sale",
  "property_kind": "apartment",
  "condition": "used",
  "price_amount": 35000000000,
  "currency": "COP",
  "hoa_fees_amount": 45000000,
  "country": "CO", "state_province": "Bogota DC", "city": "Bogota",
  "locality_id": "uuid", "neighborhood": "Chapinero",
  "address": "Cra 7 # 60-00", "address_is_public": false,
  "location_point": { "lat": 4.65, "lng": -74.06 },
  "area_total": 78.5, "area_built": 70.0,
  "bedrooms": 2, "bathrooms": 2, "parking_spots": 1,
  "year_built": 2015, "available_from": "2026-07-01",
  "primary_cta": "whatsapp",
  "amenity_codes": ["gym","pool"]
}
```
- Respuesta `201`: objeto Property completo con `id`, `slug`, `status":"draft"`, contadores en 0.
- Errores: `400 validation_error` (enum invalido, `price_amount` no entero/<0, slug regex), `401`, `403 forbidden`, `422 unprocessable_entity` (`currency` no ISO/`locality_id` inexistente).

**PATCH `/properties/{property_id}`** — Edicion parcial de campos editables. status es read-only (API-R4).
- Roles: AGENT owner (`property:update_own`) o ADMIN (`property:update_any`).
- Payload: subset de los campos editables de POST. `status`, `slug`, contadores, `published_at`, `main_image_id` (via set-main) son ignorados/rechazados.
- Respuesta `200`: Property actualizado. Nota: edicion material de un `PUBLISHED` puede forzar re-revision (regla en property-lifecycle.md).
- Errores: `400`, `403 forbidden`, `404 not_found`, `409 conflict` (slug colision si se renombra), `422`.

**DELETE `/properties/{property_id}`** — Soft delete (API-R9). Audit `DELETE`.
- Roles: AGENT owner (`property:delete_own`) o ADMIN (`property:delete_any`).
- Respuesta `204`. Errores: `403`, `404`, `409 conflict` (ya `DELETED`).

### 4b. Property — Acciones de ciclo de vida (`POST /properties/{property_id}/<accion>`)

Endpoints dedicados (API-R4). Transiciones segun maquina de estados del CONTRATO. Todas generan AuditLog.

| Accion | Metodo/Ruta | Transicion | Roles | Permiso | Audit |
|--------|-------------|------------|-------|---------|-------|
| Submit | `POST /properties/{id}/submit` | DRAFT/REJECTED -> PENDING | AGENT owner | `property:publish_request` | (UPDATE) |
| Approve | `POST /properties/{id}/approve` | PENDING -> PUBLISHED (set `published_at`) | ADMIN | `property:approve` | `PUBLISH`/`APPROVE` |
| Reject | `POST /properties/{id}/reject` | PENDING -> REJECTED | ADMIN | `property:reject` | `REJECT` |
| Pause | `POST /properties/{id}/pause` | PUBLISHED -> PAUSED | AGENT owner/ADMIN | `property:pause_own` | `PAUSE` |
| Reactivate | `POST /properties/{id}/reactivate` | PAUSED -> PUBLISHED | AGENT owner/ADMIN | `property:pause_own`/`update_any` | `REACTIVATE` |
| Mark sold | `POST /properties/{id}/mark-sold` | PUBLISHED/PAUSED -> SOLD (solo `operation_type=sale`) | AGENT owner/ADMIN | `property:update_own`/`update_any` | `MARK_SOLD` |
| Mark rented | `POST /properties/{id}/mark-rented` | PUBLISHED/PAUSED -> RENTED (solo `operation_type in {rent,temporary}`) | AGENT owner/ADMIN | `property:update_own`/`update_any` | `MARK_RENTED` |
| Duplicate | `POST /properties/{id}/duplicate` | clona -> nuevo DRAFT (nuevo id+slug, metricas 0) | AGENT owner/ADMIN | `property:create` | `DUPLICATE` |

#### Detalle de las principales

**POST `/properties/{id}/submit`** — Envia a revision. Requiere campos minimos + >=1 imagen.
- Payload: `{}` (vacio). Respuesta `200`: Property con `status":"pending"`.
- Errores: `403 forbidden`, `404`, `409 conflict` (status no es DRAFT/REJECTED), `422 unprocessable_entity` (`details` lista campos faltantes o "min_images_required").

**POST `/properties/{id}/approve`** — Publica. Setea `published_at`. Audit `APPROVE`+`PUBLISH`.
- Roles: ADMIN. Permiso `property:approve`. Payload: `{ "note"? }`.
- Respuesta `200`: Property `status":"published"`, `published_at` no nulo.
- Errores: `403`, `404`, `409 conflict` (status != PENDING).

**POST `/properties/{id}/reject`** — Rechaza con motivo. Audit `REJECT`.
- Roles: ADMIN. Permiso `property:reject`. Payload: `{ "reason": "Fotos de baja calidad" }` (requerido).
- Respuesta `200`: Property `status":"rejected"`.
- Errores: `400 validation_error` (`reason` vacio), `403`, `404`, `409 conflict` (status != PENDING).

**POST `/properties/{id}/mark-sold`** — Marca vendida. Solo `operation_type=sale`.
- Respuesta `200`: Property `status":"sold"`. Errores: `403`, `404`, `409 conflict` (status no PUBLISHED/PAUSED), `422 unprocessable_entity` (`operation_type != sale`).

**POST `/properties/{id}/duplicate`** — Clona como `DRAFT` nuevo (nuevo `id`+`slug`, contadores en 0, sin leads/featured/seo heredados salvo copia de imagenes segun media-pipeline.md).
- Respuesta `201`: nueva Property `DRAFT`. Errores: `403`, `404`.

---

## 5. Property Images / Media — `/properties/{property_id}/images`

Flujo: presign -> el cliente sube binario a S3 -> attach registra metadata -> set-main/reorder/replace/delete gestionan. Constraint: una sola `MAIN` por propiedad (ImageRole). Detalle en media-pipeline.md.

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| POST | `/properties/{id}/images/presign` | Devuelve URL firmada S3 para subir | AGENT owner | `image:upload_own` |
| POST | `/properties/{id}/images` | Attach: registra imagen subida (metadata) | AGENT owner | `image:upload_own` |
| GET | `/properties/{id}/images` | Lista imagenes de la propiedad (ordenadas) | AGENT owner/ADMIN | `image:upload_own`/`manage_any` |
| PATCH | `/properties/{id}/images/reorder` | Reordena (`position`) en lote | AGENT owner | `image:upload_own` |
| POST | `/properties/{id}/images/{image_id}/set-main` | Marca como `MAIN` (degrada la anterior) | AGENT owner | `image:upload_own` |
| PUT | `/properties/{id}/images/{image_id}` | Replace: reemplaza binario/metadata | AGENT owner | `image:upload_own` |
| PATCH | `/properties/{id}/images/{image_id}` | Edita `alt_text`/`role`/`media_kind` | AGENT owner | `image:upload_own` |
| DELETE | `/properties/{id}/images/{image_id}` | Elimina imagen | AGENT owner | `image:upload_own`/`manage_any` |

### Detalle

**POST `/properties/{id}/images/presign`** — Pide credenciales de subida directa a object storage.
- Payload: `{ "content_type": "image/webp", "bytes": 850000, "media_kind": "image" }`
- Respuesta `200`: `{ "upload_url", "fields": { /* form fields S3 */ }, "object_key", "expires_in": 600 }`
- Errores: `400 validation_error` (`content_type` no permitido), `403 forbidden`, `413 payload_too_large` (excede limite media-pipeline.md).

**POST `/properties/{id}/images`** (attach) — Registra la imagen ya subida.
- Payload: `{ "object_key", "media_kind":"image", "role":"gallery", "alt_text":"Sala", "width":1600, "height":900, "bytes":850000, "content_type":"image/webp", "position":3 }`
- Respuesta `201`: PropertyImage con `original_url`, `cdn_url`, `thumb_url`.
- Errores: `400`, `403`, `404` (property/object_key), `409 conflict` (segunda `MAIN` -> use set-main), `422`.

**POST `/properties/{id}/images/{image_id}/set-main`** — Garantiza unica `MAIN`; actualiza `Property.main_image_id`.
- Respuesta `200`: `{ "main_image_id": "uuid" }`. Errores: `403`, `404`, `409 conflict`.

---

## 6. Search & Public Detail — `/search`, `/properties/by-slug`

Lecturas publicas (API-R2, API-R3). PostGIS + pg_trgm para texto/geo. Detalle de filtros en search-filters.md.

| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/search` | Busqueda+filtros+orden+paginacion de propiedades `PUBLISHED` | VISITOR |
| GET | `/search/suggest` | Autocompletado (localidades, texto) | VISITOR |
| GET | `/properties/by-slug/{slug}` | Detalle publico por slug (solo `PUBLISHED`) | VISITOR |
| GET | `/properties/by-slug/{slug}/similar` | Propiedades similares | VISITOR |

### Detalle

**GET `/search`** — Resultado de catalogo.
- Query params: `q` (texto, pg_trgm), `operation_type`, `property_kind`, `condition`, `city`, `locality_id`, `neighborhood`, `currency`, `price_min`, `price_max` (minor units), `bedrooms_min`, `bathrooms_min`, `parking_min`, `area_min`, `area_max`, `amenity_codes` (csv), `bbox` (`minLng,minLat,maxLng,maxLat`) o `near=lat,lng&radius_m`, `is_featured`, `sort` (`relevance|price_asc|price_desc|newest|most_viewed`), `page`, `page_size`.
- Respuesta `200`: envelope de paginacion; cada `data[]` = tarjeta publica de Property (sin `address` privada — API-R6): `{ "id","slug","title","operation_type","property_kind","price_amount","currency","city","neighborhood","bedrooms","bathrooms","parking_spots","area_total","main_image":{ "cdn_url","thumb_url","alt_text" },"is_featured","location_point_public" }`.
- Errores: `400 validation_error` (filtro/sort invalido, `price_min>price_max`), `429 rate_limited`.

**GET `/properties/by-slug/{slug}`** — Pagina de detalle (DoD #9). Visibilidad API-R3.
- Respuesta `200`: Property publica completa: campos descriptivos + `images[]` ordenadas + `amenities[]` + `seo` (meta) + agente publico (`full_name`, `whatsapp`, `phone` segun consentimiento) + `available_from`. Emite evento `VIEW` (async, ver metrics) o el cliente llama `POST /metrics/events`.
- Errores: `301`/`410 gone` (SOLD/RENTED, header `Location` a canonical/seo.md), `404 not_found` (DRAFT/PENDING/PAUSED/REJECTED/DELETED/slug inexistente).

---

## 7. Locations — `/locations`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/locations` | Arbol/lista de localidades activas (filtros: `parent_id`,`city`,`q`) | VISITOR | — |
| GET | `/locations/{location_id}` | Detalle de localidad | VISITOR | — |
| POST | `/locations` | Crea localidad | ADMIN | `location:manage` |
| PATCH | `/locations/{location_id}` | Edita localidad | ADMIN | `location:manage` |
| DELETE | `/locations/{location_id}` | Desactiva localidad (`is_active=false`) | ADMIN | `location:manage` |

Respuesta de item: `{ "id","country","state_province","city","locality","neighborhood","slug","parent_id","center_point","is_active" }`. Errores CRUD: `400`,`403`,`404`,`409 conflict` (`slug` duplicado).

---

## 8. Property Types — `/property-types`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/property-types` | Lista tipos activos (mapea `PropertyKind`) | VISITOR | — |
| POST | `/property-types` | Crea tipo | ADMIN | `property_type:manage` |
| PATCH | `/property-types/{id}` | Edita (`name`,`icon`,`is_active`) | ADMIN | `property_type:manage` |
| DELETE | `/property-types/{id}` | Desactiva | ADMIN | `property_type:manage` |

Item: `{ "id","code":"apartment","name","slug","icon","is_active" }`. Errores: `400`,`403`,`404`,`409 conflict` (`slug`/`code` duplicado).

---

## 9. Amenities — `/amenities`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/amenities` | Lista amenities activas (filtro `category`) | VISITOR | — |
| POST | `/amenities` | Crea amenity | ADMIN | `amenity:manage` |
| PATCH | `/amenities/{id}` | Edita | ADMIN | `amenity:manage` |
| DELETE | `/amenities/{id}` | Desactiva | ADMIN | `amenity:manage` |

Item: `{ "id","code","name","category","icon","is_active" }`. Errores: `400`,`403`,`404`,`409 conflict` (`code` duplicado).

---

## 10. Leads — `/leads`, `/properties/{id}/leads`

Captura publica + gestion agente/admin. Detalle de estados/SLA en leads.md.

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| POST | `/leads` | Crea lead (publico, formulario detalle) | VISITOR | — |
| GET | `/leads` | Lista leads del agente (own) o todos (admin) | AGENT | `lead:read_own`/`read_any` |
| GET | `/leads/{lead_id}` | Detalle de lead | AGENT (asignado)/ADMIN | `lead:read_own`/`read_any` |
| GET | `/properties/{id}/leads` | Leads de una propiedad | AGENT owner/ADMIN | `lead:read_own`/`read_any` |
| PATCH | `/leads/{lead_id}/status` | Cambia `status` (LeadStatus) | AGENT (asignado)/ADMIN | `lead:update_status` |
| PATCH | `/leads/{lead_id}/assign` | Asigna `owner_id` (agente) | ADMIN | `lead:assign` |

### Detalle

**POST `/leads`** — Captura de contacto desde el detalle. Publico, rate limited (API-R8).
- Payload:
```json
{
  "property_id": "uuid",
  "name": "Ana Perez",
  "email": "ana@example.com",
  "phone": "+57300...",
  "message": "Quiero agendar visita",
  "channel": "form",
  "consent_given": true,
  "consent_text": "Acepto politica de datos v3",
  "utm": { "utm_source": "google", "utm_campaign": "remarketing" }
}
```
- Server captura `source_ip`, `user_agent`; status inicial `new`; `owner_id` = agente de la propiedad. Incrementa `Property.leads_count`.
- Respuesta `201`: `{ "id", "status": "new", "created_at" }` (sin PII de vuelta mas que lo enviado).
- Errores: `400 validation_error`, `404 not_found` (propiedad inexistente/no publicada), `422 unprocessable_entity` (`consent_given=false`), `429 rate_limited`.

**PATCH `/leads/{lead_id}/status`** — Avanza el embudo. Audit `UPDATE`.
- Payload: `{ "status": "contacted", "note"? }`. Al pasar a `contacted` setea `contacted_at`.
- Respuesta `200`: Lead actualizado. Errores: `400` (LeadStatus invalido), `403 forbidden` (no asignado), `404`, `409 conflict` (transicion no permitida).

---

## 11. Banners — `/banners`

CRUD admin + resolucion publica segmentada + tracking de impresion/clic. Detalle en banners-featured.md.

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/banners` | Lista admin (todos, filtros: `position`,`is_active`) | ADMIN | `banner:manage` |
| POST | `/banners` | Crea banner | ADMIN | `banner:manage` |
| GET | `/banners/{banner_id}` | Detalle admin | ADMIN | `banner:manage` |
| PATCH | `/banners/{banner_id}` | Edita banner | ADMIN | `banner:manage` |
| DELETE | `/banners/{banner_id}` | Elimina banner | ADMIN | `banner:manage` |
| GET | `/banners/resolve` | Banners activos para un contexto (publico) | VISITOR | — |
| POST | `/banners/{banner_id}/track-impression` | Registra impresion (publico) | VISITOR | — |
| POST | `/banners/{banner_id}/track-click` | Registra clic (publico) | VISITOR | — |

### Detalle

**POST `/banners`** — Crea banner segmentado.
- Payload: `{ "title","description"?,"image_desktop_url","image_mobile_url","cta_label","cta_url","position":"home_hero","priority":10,"starts_at","ends_at","is_active":true,"target_locality_id"?,"target_city"?,"target_operation"?,"target_kind"? }`
- Respuesta `201`: Banner. Errores: `400 validation_error` (`position` no en BannerPosition, `ends_at<starts_at`), `403`.

**GET `/banners/resolve`** — Devuelve banners a renderizar segun contexto y `priority`.
- Query: `position` (requerido, BannerPosition), `city`?, `locality_id`?, `operation_type`?, `property_kind`?.
- Respuesta `200`: `{ "data": [ { "id","image_desktop_url","image_mobile_url","cta_label","cta_url","priority" } ] }` (solo activos en ventana `starts_at`..`ends_at` y matching de targeting).
- Errores: `400 validation_error` (`position` invalido).

**POST `/banners/{id}/track-click`** — Incrementa `clicks_count`. Publico, idempotencia best-effort por `session_hash`.
- Payload: `{ "session_hash"? }`. Respuesta `204`. Errores: `404`, `429`.

---

## 12. Featured Properties — `/featured`, `/featured-admin`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/featured` | Lista publica de destacados por scope | VISITOR | — |
| GET | `/featured-admin` | Lista admin de destacados | ADMIN | `featured:manage` |
| POST | `/featured-admin` | Marca propiedad como destacada | ADMIN | `featured:manage` |
| PATCH | `/featured-admin/{id}` | Edita (`scope`,`priority`,ventana,`is_active`) | ADMIN | `featured:manage` |
| DELETE | `/featured-admin/{id}` | Quita destacado | ADMIN | `featured:manage` |
| POST | `/featured/{id}/track-impression` | Registra impresion (publico) | VISITOR | — |
| POST | `/featured/{id}/track-click` | Registra clic (publico) | VISITOR | — |

### Detalle

**GET `/featured`** — Destacados publicos. Query: `scope` (FeaturedScope: `home|search_results|locality`), `locality_id` (requerido si `scope=locality`), `limit`.
- Respuesta `200`: `{ "data": [ { "property": { /* tarjeta publica */ }, "priority","scope" } ] }` (solo `is_active` en ventana y cuya Property este `PUBLISHED`).
- Errores: `400 validation_error` (`scope=locality` sin `locality_id`).

**POST `/featured-admin`** — Destaca una propiedad (1:1 con Property).
- Payload: `{ "property_id","scope":"home","priority":5,"locality_id"?,"starts_at","ends_at","is_active":true }`
- Respuesta `201`: FeaturedProperty. Errores: `400`, `403`, `404` (property), `409 conflict` (ya destacada/`property_id` unique), `422 unprocessable_entity` (`scope=locality` requiere `locality_id`; property no `PUBLISHED`).

---

## 13. Favorites — `/favorites`

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/favorites` | Lista favoritos del usuario | REGISTERED_USER | `favorite:manage_own` |
| POST | `/favorites` | Agrega favorito | REGISTERED_USER | `favorite:manage_own` |
| DELETE | `/favorites/{property_id}` | Quita favorito | REGISTERED_USER | `favorite:manage_own` |

**POST `/favorites`** — Payload: `{ "property_id" }`. Respuesta `201`: `{ "id","property_id","created_at" }`. Idempotente. Errores: `400`, `401`, `404` (property), `409 conflict` (`Unique(user_id,property_id)` ya existe -> tambien aceptable 200). **DELETE** Respuesta `204`; `404` si no existe.

---

## 14. Metrics — `/metrics`, `/metrics/events`

Eventos de engagement (PropertyView) + agregados. Contadores denormalizados viven en Property/Banner/FeaturedProperty. Detalle en metrics.md.

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| POST | `/metrics/events` | Ingesta de evento (VIEW/CTA/etc.) publico | VISITOR | — |
| GET | `/metrics/properties/{id}` | Metricas de una propiedad (own) | AGENT owner | `metrics:read_own` |
| GET | `/metrics/me` | Resumen del agente (sus propiedades) | AGENT | `metrics:read_own` |
| GET | `/metrics/global` | Dashboard global | ADMIN | `metrics:read_global` |

### Detalle

**POST `/metrics/events`** — Registra evento en `property_views`. Publico, rate limited.
- Payload: `{ "property_id","event_type":"view","source":"organic","session_hash","referrer"? }` (`event_type` MetricEventType, `source` ViewSource). Server hashea IP (`ip_hash`). Incrementa contador denormalizado correspondiente (`views_count`/`clicks_count`).
- Respuesta `202` (accepted, async). Errores: `400 validation_error` (enum invalido), `404` (property), `429 rate_limited`.

**GET `/metrics/global`** — Roles: ADMIN, `metrics:read_global`.
- Query: `date_from`,`date_to`,`group_by` (`day|week|month`), `event_type`?.
- Respuesta `200`: `{ "totals": { "views","clicks","leads","favorites" }, "series": [ { "bucket","views","clicks","leads" } ], "top_properties": [...] }`.
- Errores: `400`, `403`.

---

## 15. Admin Moderation — `/admin/moderation`

Cola de revision (DoD #6, #22). Reusa acciones de lifecycle (seccion 4b) o atajos batch.

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/admin/moderation/queue` | Cola de propiedades `PENDING` (filtros, orden FIFO) | ADMIN | `property:approve` |
| POST | `/admin/moderation/{property_id}/approve` | Aprueba (alias de lifecycle approve) | ADMIN | `property:approve` |
| POST | `/admin/moderation/{property_id}/reject` | Rechaza con motivo (alias de lifecycle reject) | ADMIN | `property:reject` |

### Detalle

**GET `/admin/moderation/queue`** — Lista `PENDING` priorizada.
- Query: `page`,`page_size`,`sort` (`oldest_first` default), `owner_id`?, `city`?.
- Respuesta `200`: envelope paginado; cada item = Property resumida + `submitted_at` + flags de validacion (`has_main_image`, `min_fields_ok`).
- Errores: `401`, `403 forbidden`.

**POST `/admin/moderation/{property_id}/reject`** — Igual a `POST /properties/{id}/reject` (PENDING->REJECTED, `reason` requerido, Audit `REJECT`). Errores: `400`,`403`,`404`,`409 conflict`.

---

## 16. Audit Logs — `/audit-logs`

Append-only (CONTRATO). Solo lectura.

| Metodo | Ruta | Descripcion | Roles | Permiso |
|--------|------|-------------|-------|---------|
| GET | `/audit-logs` | Lista paginada de eventos de auditoria | ADMIN | `audit:read` |
| GET | `/audit-logs/{audit_id}` | Detalle de un evento (con `before`/`after`) | ADMIN | `audit:read` |

**GET `/audit-logs`** — Query: `actor_id`?, `action`? (AuditAction), `entity_type`?, `entity_id`?, `date_from`?, `date_to`?, `page`, `page_size`.
- Respuesta `200`: envelope paginado; item = `{ "id","actor_id","action","entity_type","entity_id","ip","user_agent","created_at" }` (resumen; `before`/`after` solo en detalle).
- Errores: `401`, `403 forbidden`, `400 validation_error` (`action`/`entity_type` invalido).

No existen POST/PATCH/DELETE: la API nunca escribe `AuditLog` directamente; los crea el backend de forma transaccional (API-R7).

---

## 17. SEO (referencia)

Endpoints de SEO (`/seo/*`, sitemap, redirects de `SeoMetadata`) y la politica 301/410 para `SOLD`/`RENTED` se detallan en **seo.md** (DoD #13). Aqui solo se referencia su impacto en visibilidad (API-R3) y en el detalle publico (seccion 6).

## Open Questions

- OQ-1: Politica fina de edicion material de `PUBLISHED` (que campos disparan re-revision PENDING vs edicion en caliente) -> definir en property-lifecycle.md y reflejar el `409`/`200` de `PATCH /properties/{id}`.
- OQ-2: Endpoints de "reportar propiedad" (FR-110..119) — se decidio que `report` vive como evento/lead especial; confirmar si requiere endpoint dedicado `POST /properties/{id}/report` (publico) en vez de reusar `/leads`.
- OQ-3: ¿`POST /metrics/events` cubre el tracking de banners/featured o se mantienen los `track-*` dedicados? (actual: dedicados para contadores denormalizados, eventos genericos solo para Property).
