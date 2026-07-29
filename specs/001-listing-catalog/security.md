# Seguridad — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #14.

## Resumen

Modelo de seguridad obligatorio para **Listing**: portal inmobiliario con lecturas
publicas (sin auth) y operaciones de gestion protegidas por JWT + RBAC. Cubre
autenticacion (JWT access+refresh, hashing Argon2id), autorizacion por roles y
ownership, sanitizacion/validacion de entradas, defensas web (CSP, CSRF, XSS),
rate limiting y antispam con Redis, validacion de archivos, auditoria
(`AuditLog` append-only), soft delete (`deleted_at`), backups y proteccion de
PII de `User` y `Lead` (TLS, cifrado en reposo, minimizacion, consentimiento,
retencion, derecho de borrado) y gestion de secretos. Las reglas viven en
`## Reglas (SEC-R#)`. Referencias: `roles-permissions.md` (matriz RBAC),
`property-lifecycle.md` (transiciones), `media-pipeline.md` (pipeline de imagenes), `leads.md`
(captura), `seo.md` (politica 301/410), `data-model.md` (`User`, `Lead`,
`AuditLog`). FR de seguridad: ver `spec.md` rango **NFR-001..** (Seguridad) y
**NFR-040..** (Privacidad/Cumplimiento).

Principios transversales: defense-in-depth, deny-by-default, least-privilege,
fail-closed (ante duda, denegar y registrar), validar en el limite (API), nunca
confiar en el cliente.

---

## 1. Autenticacion

Auth basada en JWT Bearer (access + refresh). Las **lecturas publicas** de
contenido `PUBLISHED` no requieren auth (rol `VISITOR`). Toda operacion de
escritura o lectura de datos privados exige token valido.

### 1.1 Hashing de contrasenas

| Aspecto | Decision |
|---|---|
| Algoritmo primario | **Argon2id** (memory-hard) sobre `User.password_hash` |
| Parametros Argon2id | `time_cost>=3`, `memory_cost>=64 MiB`, `parallelism>=2` (calibrar a <=250 ms/hash en el hardware de produccion) |
| Fallback de verificacion | **bcrypt** (cost>=12) solo para validar hashes legacy; rehash a Argon2id en login exitoso |
| Salt | Aleatorio por usuario, gestionado por la libreria (passlib/argon2-cffi) |
| Almacenamiento | Solo el hash en `User.password_hash`; la contrasena en claro nunca se persiste ni se loguea |
| Politica de contrasena | Min 10 caracteres; rechazo contra lista de comprometidas (k-anonymity / HIBP opcional); sin maximo agresivo (<=128) |

### 1.2 Tokens JWT

| Token | Vida | Almacen recomendado (SPA CSR) | Contenido (claims) |
|---|---|---|---|
| **access** | 15 min | Memoria del cliente (no localStorage) | `sub`=`user.id`, `role`, `permissions[]` (o `role` y resolver permisos server-side), `iat`, `exp`, `jti`, `type="access"` |
| **refresh** | 7 dias (rotacion) | Cookie `HttpOnly; Secure; SameSite=Strict` | `sub`, `iat`, `exp`, `jti`, `type="refresh"`, `family_id` |

- **Firma**: HS256 con secreto fuerte (>=32 bytes) o RS256/EdDSA si hay multiples
  servicios; clave en `.env.local` (`JWT_SECRET` / par de claves).
- **Rotacion de refresh**: cada uso de `/api/v1/auth/refresh` emite un nuevo
  refresh e **invalida** el anterior (`jti` en denylist Redis). Reuso de un
  refresh ya consumido => revocar toda la `family_id` (deteccion de robo).
- **Expiracion/revocacion**: denylist de `jti` en Redis con TTL = vida restante
  del token. Logout invalida el refresh actual; `LOGOUT` se audita.
- **Email verification**: `User.email_verified` debe ser `true` para publicar
  (`property:publish_request`) y para recibir notificaciones de leads. Token de
  verificacion de un solo uso, expira en 24 h, firmado y ligado a `user.id`.
- **Reset de contrasena**: token de un solo uso, 30 min, invalida sesiones
  activas (rota `family_id`) al completarse.

### 1.3 Endpoints de auth (referencia)

`/api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `/verify-email`,
`/password/forgot`, `/password/reset`. Especificacion completa en `api-contracts.md`.
Errores con envelope `{"error":{"code","message","details"}}`; nunca revelar si
el email existe (respuesta uniforme en `register`/`forgot`).

---

## 2. Autorizacion (RBAC + ownership)

Jerarquia: `VISITOR < REGISTERED_USER < AGENT < ADMIN < SUPERADMIN`. La matriz
canonica de permisos `resource:action` y su asignacion por `Role` vive en
**`roles-permissions.md`**. Aqui se fijan las reglas de **aplicacion**.

### 2.1 Doble verificacion: permiso + ownership

Toda operacion sobre `Property`, `PropertyImage`, `Lead` y `Favorite` aplica
**dos** controles en orden:

1. **Permiso** (RBAC): el rol del actor incluye el codigo requerido.
2. **Ownership** (cuando el permiso es `*_own`): el recurso pertenece al actor.

| Operacion | Permiso `_own` (AGENT/owner) | Permiso `_any` (ADMIN+) | Chequeo ownership |
|---|---|---|---|
| Editar propiedad | `property:update_own` | `property:update_any` | `property.owner_id == actor.id` |
| Eliminar propiedad | `property:delete_own` | `property:delete_any` | idem |
| Pausar | `property:pause_own` | (incluido en `update_any`) | idem |
| Subir/gestionar imagen | `image:upload_own` | `image:manage_any` | `image.property.owner_id == actor.id` |
| Leer leads | `lead:read_own` | `lead:read_any` | `lead.owner_id == actor.id` |
| Gestionar favoritos | `favorite:manage_own` | — | `favorite.user_id == actor.id` |

- Aprobar/rechazar/destacar y publicacion final son **solo** `ADMIN+`
  (`property:approve`, `property:reject`, `property:feature`); ver `property-lifecycle.md`.
- **Object-level enforcement obligatorio**: nunca confiar en IDs del cliente;
  resolver el recurso desde la BD y comparar ownership antes de actuar (anti
  IDOR/BOLA).

### 2.2 Respuestas de denegacion (anti-enumeracion)

| Situacion | HTTP | `error.code` |
|---|---|---|
| Sin token / token invalido | 401 | `unauthorized` |
| Token valido, permiso insuficiente | 403 | `forbidden` |
| Permiso ok pero no es owner | 403 | `forbidden` |
| Recurso privado inexistente o ajeno (lectura) | 404 | `not_found` (evita revelar existencia) |
| Visibilidad publica de no-`PUBLISHED` | 404 (PAUSED/REJECTED/DRAFT/DELETED) / 410 (SOLD/RENTED segun `seo.md`) | `not_found` / `gone` |

---

## 3. Validacion, sanitizacion y XSS

### 3.1 Validacion/normalizacion de inputs

- **Schema-first**: todo body/query se valida con Pydantic v2 (tipos, longitudes,
  rangos, enums). Rechazo `422` con `error.details` por campo.
- **Enums**: `operation_type`, `property_kind`, `condition`, `status`, `currency`,
  `channel`, etc. se validan contra los enums del CONTRATO; valor fuera de enum =>
  `422`.
- **Dinero**: `price_amount` y `hoa_fees_amount` son `BIGINT` en minor units;
  rechazar negativos y floats. `currency` debe ser ISO 4217 de la lista permitida.
- **Slug**: regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`; generacion server-side, nunca
  aceptar slug arbitrario del cliente.
- **Geo**: `location_point` lat ∈ [-90,90], lng ∈ [-180,180].
- **Normalizacion**: trim de strings, lowercase de `email`, colapso de espacios;
  longitudes maximas por campo (p.ej. `title<=160`, `description<=20000`).
- **Mass-assignment**: allowlist explicita de campos por endpoint; campos
  controlados por el sistema (`status`, `owner_id`, `views_count`, `is_featured`,
  `slug`, `published_at`, contadores) **no** son escribibles via payload de
  usuario.

### 3.2 Sanitizacion de HTML (descripciones)

`Property.description` y campos rich-text de `Banner` permiten HTML limitado.

- **Allowlist** (servidor, libreria `bleach`/`nh3`): etiquetas `p, br, strong,
  em, ul, ol, li, a, h2, h3, blockquote`; atributos `a[href,title]` con `href`
  solo `http/https/mailto`; `rel="nofollow noopener"` forzado. Todo lo demas se
  elimina (no se escapa-y-conserva): nada de `script`, `style`, `iframe`,
  `on*=`, `javascript:`, `data:`.
- Sanitizar **al escribir** (persistir limpio) y escapar **al renderizar**.
- La SPA (React CSR) escapa por defecto; prohibido `dangerouslySetInnerHTML`
  salvo sobre contenido ya sanitizado server-side. JSON-LD de `seo.md` se
  serializa con escaping estricto.

### 3.3 Cabeceras de seguridad / CSP

Aplicadas en el edge/proxy y/o middleware FastAPI a respuestas HTML y API:

| Cabecera | Valor |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; img-src 'self' https://<cdn> data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://<api>; frame-ancestors 'none'; object-src 'none'; base-uri 'self'` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` (redundante con `frame-ancestors 'none'`) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` |
| `Cache-Control` (rutas privadas) | `no-store` |

### 3.4 CORS

Allowlist explicita de origenes (dominio SPA). `Access-Control-Allow-Credentials`
solo si se usan cookies; nunca `*` junto con credenciales.

---

## 4. CSRF

- **Default (Bearer en header)**: el access token viaja en `Authorization:
  Bearer`, no en cookie => las rutas con access token **no** son vulnerables a
  CSRF clasico.
- **Cookie de refresh (`HttpOnly`)**: el endpoint `/api/v1/auth/refresh` y
  cualquier flujo basado en cookie requiere defensa CSRF:
  - `SameSite=Strict` (o `Lax` minimo) en la cookie de refresh.
  - **Double-submit token** o token CSRF sincronizado para `refresh`/`logout`
    cuando se invoquen desde el navegador.
  - Validar `Origin`/`Referer` contra la allowlist en peticiones state-changing.
- Formularios publicos de `Lead` (POST sin auth): protegidos por
  honeypot + rate limit + validacion de `Origin` (ver seccion 5-6), no por token
  de sesion (el visitante no esta autenticado).

---

## 5. Rate limiting y antispam (Redis)

Contadores y ventanas en **Redis** (token-bucket / sliding window). Clave por
combinacion de IP + (cuando aplique) `user.id` + endpoint. Respuesta `429` con
`error.code="rate_limited"` y cabecera `Retry-After`.

### 5.1 Limites minimos

| Flujo | Limite | Clave | Notas |
|---|---|---|---|
| `POST /auth/login` | 5 / 5 min / IP+email; backoff exponencial | IP + email | Bloqueo temporal tras N fallos; respuesta uniforme (no revelar causa) |
| `POST /auth/register` | 5 / hora / IP | IP | + verificacion de email |
| `POST /auth/password/forgot` | 3 / hora / IP+email | IP + email | Respuesta uniforme |
| `POST /leads` (form publico) | 5 / hora / IP, 3 / hora / (IP+property) | IP, IP+property | Antispam reforzado |
| `GET` busqueda/listado | 60 / min / IP (anon), 120 / min / user | IP / user | Protege PostGIS/pg_trgm |
| Subida de imagen | 30 / hora / user | user | + limites de tamano (sec. 7) |
| Metricas/eventos (`PropertyView`) | 120 / min / session_hash | session_hash | Evita inflado de contadores |

### 5.2 Antispam en leads

- **Honeypot**: campo oculto en el form; si viene relleno => descartar como
  spam (no crear `Lead`, responder 200 neutro para no informar al bot).
- **Time-trap**: rechazar envios con render-to-submit < 2 s.
- **reCAPTCHA / hCaptcha (opcional, configurable)**: requerido cuando la IP
  supera umbral de envios o desde `config:manage`.
- **Consentimiento obligatorio**: `Lead.consent_given=true` + `Lead.consent_text`
  persistido; sin consentimiento => `422`.
- Registrar `source_ip`, `user_agent`, `utm` para correlacion antifraude
  (tratados como PII, ver sec. 9).

---

## 6. Validacion de archivos (media)

Pipeline de subida de `PropertyImage` (detalle en `media-pipeline.md`). Reglas de
seguridad obligatorias:

| Control | Regla |
|---|---|
| **MIME real** | Validar por magic bytes / sniffing del contenido, **no** por extension ni por `Content-Type` del cliente. Allowlist: `image/jpeg`, `image/png`, `image/webp` (+ `video/mp4` si `media_kind=VIDEO`) |
| **Tamano** | Maximo por archivo (p.ej. imagen <= 10 MB, video <= 100 MB; valor en config) => `413` si excede |
| **Dimensiones** | Min/max px (p.ej. min 800x600, max 8000x8000); rechazo de imagenes malformadas |
| **Reprocesado** | Re-encode/transcode server-side (strip de metadatos EXIF con GPS/PII; elimina payloads embebidos) |
| **Nombres** | Nombre **aleatorizado** (UUID), nunca el nombre del cliente; sin path del usuario |
| **Almacenamiento** | Object storage S3-compatible **fuera del webroot**; servir via CDN con URLs no adivinables; no ejecutar nunca el bucket como contenido activo |
| **Antivirus (opcional)** | Escaneo (ClamAV/servicio) antes de publicar; cuarentena si falla |
| **Limite de cantidad** | Max N imagenes por `Property`; una sola `ImageRole.MAIN` (constraint en `data-model.md`) |
| **Polyglot/SVG** | SVG no permitido (riesgo XSS); rechazar archivos con doble extension o contenido mixto |

URLs (`original_url`, `cdn_url`, `thumb_url`) apuntan a CDN; el bucket no expone
listing publico. Subidas via URL prefirmada con expiracion corta o proxy
backend con validacion previa.

---

## 7. Auditoria (AuditLog)

`AuditLog` es **append-only** (sin update/delete a nivel de aplicacion; permisos
de BD revocan UPDATE/DELETE sobre la tabla). Cada accion sensible escribe una
fila con `actor_id` (nullable para sistema/anon), `action[AuditAction]`,
`entity_type`, `entity_id`, `before[json]`, `after[json]`, `ip`, `user_agent`,
`created_at`.

Acciones auditadas (subconjunto de `AuditAction`):
`CREATE, UPDATE, DELETE, PUBLISH, APPROVE, REJECT, PAUSE, REACTIVATE,
MARK_SOLD, MARK_RENTED, DUPLICATE, LOGIN, LOGOUT, ROLE_ASSIGN,
PERMISSION_CHANGE, CONFIG_CHANGE`.

- `before`/`after` **redactan** secretos y PII sensible (sin `password_hash`,
  sin tokens; emails/telefonos minimizados o hasheados segun politica).
- Lectura restringida a `audit:read` (`ADMIN+`).
- Integridad: considerar hash-chaining (`prev_hash`) para deteccion de
  manipulacion (mejora; ver Open Questions).

---

## 8. Soft delete

- Borrado logico via `deleted_at` (timestamptz nullable) en entidades con PII y
  contenido (`User`, `Property`, `Lead`, etc.). El estado `PublicationStatus.DELETED`
  marca propiedades borradas (ver `property-lifecycle.md`).
- **Todas** las consultas de lectura filtran `deleted_at IS NULL` por defecto
  (scope/base query global). Registros soft-deleted: invisibles publicamente
  (404; SOLD/RENTED segun `seo.md`).
- Restauracion solo por `ADMIN+`, auditada.
- El **derecho de borrado** (sec. 9) puede exigir **hard delete / anonimizacion**
  posterior, distinto del soft delete operativo.

---

## 9. Proteccion de datos personales (PII)

PII relevante: `User` (email, phone, whatsapp, full_name, avatar) y `Lead`
(name, email, phone, message, source_ip, user_agent, utm, consent).

| Dimension | Medida |
|---|---|
| **En transito** | TLS 1.2+ obligatorio extremo a extremo; HSTS (sec. 3.3); redirigir HTTP->HTTPS |
| **En reposo** | Cifrado de volumen/BD (PostgreSQL at-rest, KMS), backups cifrados, bucket S3 con SSE |
| **Minimizacion** | Capturar solo lo necesario; no almacenar PAN/tarjetas; `ip`/`source_ip` hasheable (`ip_hash` ya usado en `PropertyView`) |
| **Consentimiento** | `Lead.consent_given` + `Lead.consent_text` versionado y timestamp; sin consentimiento, no se procesa el lead |
| **Retencion** | Politica por entidad: leads cerrados/descartados (`LeadStatus.CLOSED/DISCARDED`) purgados/anonimizados tras N meses; `PropertyView` agregado y purgado de PII tras ventana corta; logs de acceso con TTL |
| **Derecho de borrado / acceso** | Endpoint/proceso (ADMIN) para exportar y para borrar/anonimizar PII de un `User`/`Lead` a peticion; conservar `AuditLog` minimizado por obligacion legal |
| **Acceso interno** | `lead:read_own`/`read_any`, `user:read` restringen visibilidad; PII nunca en logs de aplicacion ni en `error.details` |
| **Transferencia** | Procesadores (CDN, email, captcha) bajo acuerdo de tratamiento; data residency segun jurisdiccion |

---

## 10. Backups y recuperacion

| Aspecto | Decision |
|---|---|
| **Alcance** | PostgreSQL (datos+PostGIS), object storage (media), secretos (vault aparte) |
| **Estrategia** | Backup completo diario + WAL/PITR continuo (point-in-time recovery) para Postgres; versionado/replicacion del bucket |
| **Cifrado** | Backups cifrados en reposo y en transito (KMS) |
| **Retencion** | Diarios 30 dias, semanales 12 semanas, mensuales 12 meses (ajustable por cumplimiento) |
| **Aislamiento** | Copias off-site / cuenta separada (proteccion ante ransomware/borrado) |
| **Prueba de restore** | Restore de prueba **trimestral** documentado; objetivo RPO <= 24 h (PITR reduce a minutos), RTO <= 4 h |
| **Acceso** | Restauracion solo por operadores autorizados; cada restore auditado (`CONFIG_CHANGE`) |

---

## 11. Gestion de secretos

- Secretos (JWT keys, DB DSN, Redis, S3 keys, captcha keys, SMTP) en
  `.env.local` (git-ignored) en dev; en produccion via secret manager
  (Vault/SSM/Secrets Manager), nunca en el repo ni en imagenes.
- `.env.example` documenta las variables **sin** valores reales.
- El secret scanner del harness bloquea commits con credenciales (regla del
  proyecto: *No Hardcoded Secrets*).
- Rotacion periodica de claves JWT/DB/S3; rotacion inmediata ante incidente.
- Principio de menor privilegio en credenciales de servicio (IAM scoped al
  bucket/prefijo; usuario de BD sin permisos DDL en runtime).

---

## Reglas (SEC-R#)

| ID | Regla |
|---|---|
| SEC-R1 | Contrasenas hasheadas con **Argon2id** (`time>=3`, `mem>=64MiB`, `par>=2`); bcrypt (cost>=12) solo para verificar legacy con rehash a Argon2id en login. Jamas persistir/loguear contrasena en claro. |
| SEC-R2 | Access token JWT vida 15 min; refresh 7 dias con **rotacion** y deteccion de reuso (revocar `family_id`). Denylist de `jti` en Redis con TTL. |
| SEC-R3 | Refresh token solo en cookie `HttpOnly; Secure; SameSite=Strict`; access token nunca en `localStorage`. |
| SEC-R4 | `email_verified=true` requerido para `property:publish_request` y para entrega de notificaciones de leads. |
| SEC-R5 | Toda operacion aplica **RBAC + ownership**: permiso `*_own` exige `resource.owner_id == actor.id` resuelto desde BD (anti IDOR/BOLA). |
| SEC-R6 | Deny-by-default: 401 sin auth, 403 con permiso/ownership insuficiente, 404 para recursos privados ajenos (anti-enumeracion). Visibilidad publica solo `PUBLISHED`. |
| SEC-R7 | Todo input validado server-side (Pydantic): enums, longitudes, rangos, `price_amount` BIGINT minor (no float/negativo), `currency` ISO 4217, slug por regex generado en servidor. |
| SEC-R8 | Allowlist explicita de campos por endpoint; campos de sistema (`status`, `owner_id`, contadores, `slug`, `published_at`, `is_featured`) no escribibles via payload de usuario (anti mass-assignment). |
| SEC-R9 | `Property.description` y rich-text sanitizados server-side con **allowlist** de tags/atributos; sin `script/style/iframe/on*/javascript:/data:`; SVG prohibido. |
| SEC-R10 | Render seguro en SPA: escaping por defecto, sin `dangerouslySetInnerHTML` salvo contenido ya sanitizado; JSON-LD serializado con escaping estricto. |
| SEC-R11 | Cabeceras de seguridad obligatorias: CSP restrictiva, HSTS, `X-Content-Type-Options:nosniff`, `frame-ancestors 'none'`, `Referrer-Policy`, `Cache-Control:no-store` en rutas privadas. CORS por allowlist (sin `*` con credenciales). |
| SEC-R12 | Flujos basados en cookie (`refresh`/`logout`) protegidos con `SameSite` + double-submit/token CSRF + validacion de `Origin`/`Referer`. |
| SEC-R13 | Rate limiting con Redis en login, register, password reset, formularios de lead, busqueda, subida y metricas; respuesta `429` + `Retry-After`. |
| SEC-R14 | Antispam en `POST /leads`: honeypot + time-trap + reCAPTCHA opcional; `consent_given` obligatorio; envios spam responden 200 neutro sin crear `Lead`. |
| SEC-R15 | Archivos validados por **MIME real** (magic bytes), tamano y dimensiones; re-encode con strip de EXIF; nombre aleatorizado (UUID); almacenamiento S3 fuera del webroot servido por CDN; SVG/polyglot rechazados. |
| SEC-R16 | Acciones sensibles escriben `AuditLog` **append-only** (UPDATE/DELETE revocados en BD); `before/after` redactan secretos y PII; lectura solo con `audit:read`. |
| SEC-R17 | Soft delete via `deleted_at`; todas las lecturas filtran `deleted_at IS NULL`; restauracion solo `ADMIN+` y auditada. |
| SEC-R18 | PII de `User`/`Lead`: TLS en transito, cifrado en reposo, minimizacion, consentimiento versionado, retencion por politica y derecho de borrado/anonimizacion; PII nunca en logs ni en `error.details`. |
| SEC-R19 | Backups cifrados con PITR (Postgres) + versionado de bucket, retencion definida, copias off-site y **prueba de restore trimestral** documentada (RPO<=24h, RTO<=4h). |
| SEC-R20 | Secretos solo en `.env.local`/secret manager (nunca en repo); `.env.example` sin valores reales; secret scanner activo; rotacion periodica y ante incidente; credenciales de servicio con menor privilegio. |
| SEC-R21 | Errores con envelope `{"error":{"code","message","details"}}` que **no** filtran stack traces, existencia de cuentas, ni PII; mensajes uniformes en login/register/forgot. |
| SEC-R22 | TLS 1.2+ obligatorio; redireccion HTTP->HTTPS; HSTS con `preload`. |

---

## Open Questions

- ¿reCAPTCHA/hCaptcha siempre activo en `POST /leads` o solo bajo umbral
  configurable via `config:manage`? (afecta UX vs antispam).
- ¿Hash-chaining (`prev_hash`) en `AuditLog` para integridad criptografica
  verificable, o basta con permisos append-only de BD?
- Ventanas exactas de **retencion** por entidad (leads, `PropertyView`, logs)
  pendientes de definicion legal/jurisdiccion (CDMX/MX por defecto?).
- ¿Firma JWT HS256 (monolito) o RS256/EdDSA (preparado para multi-servicio)?
- ¿Antivirus de archivos obligatorio en produccion o opcional segun plan/coste?
- Politica fina **301 vs 410** para `SOLD`/`RENTED` se define en `seo.md`; aqui
  solo se referencia el impacto en visibilidad/seguridad.
- ¿`access` token incluye `permissions[]` (rapido, riesgo de staleness al
  revocar permisos) o solo `role` con resolucion server-side (mas consultas)?
