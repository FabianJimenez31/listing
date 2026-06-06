# Ciclo de Vida de la Propiedad — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #5, #6.

## Resumen

Este documento define el ciclo de vida de `Property` como una **maquina de estados explicita** gobernada por el enum `PublicationStatus` y las operaciones permitidas sobre cada estado. Es la fuente de verdad para: estados validos, transiciones, roles autorizados, pre-condiciones, efectos secundarios (campos denormalizados, `published_at`, metricas, notificaciones, indice de busqueda, SEO/redirects) y la visibilidad publica HTTP por estado.

Alcance de los items del DoD: **#5** (ciclo de vida de propiedad) y **#6** (reglas de crear / editar / publicar / pausar / aprobar / rechazar / vender / alquilar / eliminar / duplicar).

Coordinacion entre documentos:
- **Permisos por accion**: ver `roles-permissions.md` (matriz de roles/permisos). Aqui se cita el permiso `resource:action` requerido por transicion; la definicion canonica de la matriz vive en `roles-permissions.md`.
- **SEO y redirects** (codigos 301/410, `redirect_from`, `robots`, JSON-LD, sitemap): ver `seo.md`. Aqui se referencia el efecto; los detalles del redirect viven en `seo.md`.
- **Indexacion, filtros y visibilidad en listados/busqueda**: ver `search-filters.md`. Aqui se referencia el efecto sobre el indice; las reglas de busqueda viven en `search-filters.md`.
- **Imagenes/multimedia** (la pre-condicion `>=1 imagen` y la regla "una sola MAIN"): ver `media-pipeline.md`.
- **Leads** (efecto del ciclo sobre captacion de leads): ver `leads.md`.
- **Validaciones de campos** (formato, rangos): ver `validations.md`.

Identificadores de requisitos funcionales relacionados (definidos en `spec.md`): rango **FR-020..FR-049** (Properties + lifecycle). Las reglas operativas de este documento usan el prefijo **LIFECYCLE-R#**.

## Estados (PublicationStatus)

| Estado | Valor | Descripcion | Visible publico | Terminal |
|--------|-------|-------------|-----------------|----------|
| `DRAFT` | `"draft"` | Borrador en edicion libre por el owner; nunca fue publicado o esta en re-trabajo. | No (404) | No |
| `PENDING` | `"pending"` | Enviado a revision; espera decision de moderacion. | No (404) | No |
| `PUBLISHED` | `"published"` | Aprobado y visible al publico. Unico estado servible (HTTP 200). | Si (200) | No |
| `PAUSED` | `"paused"` | Publicado previamente, ocultado temporalmente por owner/admin. | No (404) | No |
| `SOLD` | `"sold"` | Vendido (solo `operation_type=SALE`). Cerrado comercialmente. | No (301/410) | Cuasi-terminal |
| `RENTED` | `"rented"` | Alquilado (solo `operation_type in {RENT, TEMPORARY}`). | No (301/410) | Cuasi-terminal |
| `REJECTED` | `"rejected"` | Rechazado en moderacion; requiere correccion del owner. | No (404) | No |
| `DELETED` | `"deleted"` | Soft delete; `deleted_at` seteado. No reaparece nunca. | No (404; ver SEO 410) | Terminal |

Notas:
- `SOLD` y `RENTED` son **cuasi-terminales**: solo pueden moverse a `DELETED` (soft delete). No reabren a `PUBLISHED` (para volver al mercado se usa `duplicate`, ver LIFECYCLE-R12).
- `DELETED` es **terminal absoluto**. No hay restauracion via API publica/panel; recuperacion solo por procedimiento operativo (`make rollback`).
- El estado inicial siempre es `DRAFT` (LIFECYCLE-R01); `create` no admite estado distinto.

## Diagrama de transiciones (ASCII)

```
                                  create
                                    |
                                    v
                                +-------+
                  resubmit      | DRAFT |<-------------------+
              +---------------> +-------+                    |
              |                    | submit_for_review       | (duplicate: clona
              |                    v                         |  cualquier estado a
              |                +---------+                   |  un NUEVO DRAFT)
              |     reject     | PENDING |                   |
        +----------+ <---------+---------+                   |
        | REJECTED |               | approve                 |
        +----------+               v                         |
              |                +-----------+   pause    +--------+
              |     (404)      | PUBLISHED |---------- >| PAUSED |
              |                +-----------+ <----------+--------+
              |                  |   |  |   reactivate     | |
              |        mark_sold |   |  | mark_rented      | |
              |                  v   |  v                  | |
              |             +------+ | +--------+          | |
              |             | SOLD | | | RENTED |<---------+ | mark_rented
              |             +------+ | +--------+            | (RENT|TEMPORARY)
              |                |     |    |   ^--------------+
              |     mark_sold  |     |    |   mark_sold (SALE) desde PAUSED
              |     (SALE) <---+     |    |
              |    desde PAUSED      |    |
              v                      v    v
        +---------------------------------------------+
        |   soft_delete  (cualquier estado != DELETED) |
        +---------------------------------------------+
                              |
                              v
                         +---------+
                         | DELETED |  (terminal)
                         +---------+

  Auto-loop (mismo estado):  PUBLISHED --edit material--> PENDING   (re-revision; LIFECYCLE-R03)
                             DRAFT/REJECTED --edit libre--> (mismo estado)
```

Lectura del diagrama:
- `mark_sold` y `mark_rented` parten de `PUBLISHED` **o** `PAUSED`.
- `soft_delete` aplica desde cualquier estado excepto `DELETED` (caja inferior).
- La **edicion material** de `PUBLISHED` no es una caja nueva: devuelve la propiedad a `PENDING` (re-revision), ver LIFECYCLE-R03.
- `duplicate` no es una transicion del registro existente: crea un **nuevo** registro en `DRAFT` (ver LIFECYCLE-R12).

## Tabla de transiciones

Leyenda de efectos: PA=`published_at`; M=metricas/contadores; N=notificaciones; IDX=indice de busqueda; SEO=SEO/redirect; AUD=`AuditLog` (siempre se escribe una fila append-only). Permisos en formato `resource:action` (definicion en `roles-permissions.md`).

| # | Desde | Accion | Hacia | Rol autorizado (permiso) | Pre-condiciones | Efectos |
|---|-------|--------|-------|--------------------------|-----------------|---------|
| T1 | (none) | `create` | `DRAFT` | AGENT, ADMIN, SUPERADMIN (`property:create`) | Owner autenticado con permiso. Genera `id` UUID v4 y `slug` `{operation}-{kind}-{title-kebab}-{shortid}`. | PA=null. M: `views_count=clicks_count=leads_count=0`. N: ninguna. IDX: no indexa. SEO: no genera `SeoMetadata` publico. AUD: `CREATE`. |
| T2 | `DRAFT` | `submit_for_review` | `PENDING` | owner (`property:publish_request`) | Campos minimos completos (LIFECYCLE-R05) + `>=1 PropertyImage` con exactamente 1 `MAIN`. | PA sin cambio. N: notifica a moderadores (cola admin). IDX: sigue sin indexar. AUD: `PUBLISH` (intent submit). |
| T3 | `PENDING` | `approve` | `PUBLISHED` | ADMIN, SUPERADMIN (`property:approve`) | Estado actual `PENDING`. | **PA=now() si era null** (primera publicacion); si ya existia, se conserva. N: notifica al owner (aprobada). IDX: **indexa** (entra a search/sitemap). SEO: genera/activa `SeoMetadata` (`robots="index,follow"`). AUD: `APPROVE`. |
| T4 | `PENDING` | `reject(reason)` | `REJECTED` | ADMIN, SUPERADMIN (`property:reject`) | `reason` no vacio (motivo persistido para el owner). | N: notifica al owner con `reason`. IDX: no indexa. SEO: sin cambios (no publica). AUD: `REJECT` (con `reason` en `after`). |
| T5 | `REJECTED` | `resubmit` | `PENDING` | owner (`property:publish_request`) | Re-cumple campos minimos + `>=1 imagen` (LIFECYCLE-R05). | N: notifica a moderadores. IDX: sin cambio. AUD: `PUBLISH` (resubmit). |
| T6 | `PUBLISHED` | `pause` | `PAUSED` | owner (`property:pause_own`) o admin (`property:update_any`) | Estado actual `PUBLISHED`. | PA se conserva. N: opcional al owner. IDX: **des-indexa** (sale de search/sitemap). SEO: detalle responde 404 (ver visibilidad). AUD: `PAUSE`. |
| T7 | `PAUSED` | `reactivate` | `PUBLISHED` | owner (`property:pause_own`) o admin (`property:update_any`) | Estado actual `PAUSED`. **No** re-revision (el contenido ya fue aprobado). | PA se conserva (no se reescribe). IDX: **re-indexa**. SEO: detalle vuelve a 200. AUD: `REACTIVATE`. |
| T8 | `PUBLISHED` \| `PAUSED` | `mark_sold` | `SOLD` | owner (`property:update_own`) o admin (`property:update_any`) | `operation_type == SALE`. | IDX: **des-indexa**. SEO: aplica politica 301/410 (ver `seo.md`). N: opcional. AUD: `MARK_SOLD`. |
| T9 | `PUBLISHED` \| `PAUSED` | `mark_rented` | `RENTED` | owner (`property:update_own`) o admin (`property:update_any`) | `operation_type in {RENT, TEMPORARY}`. | IDX: **des-indexa**. SEO: politica 301/410 (`seo.md`). N: opcional. AUD: `MARK_RENTED`. |
| T10 | cualquiera != `DELETED` | `soft_delete` | `DELETED` | owner del recurso (`property:delete_own`) o admin (`property:delete_any`) | No estar ya en `DELETED`. | **`deleted_at=now()`**. IDX: **des-indexa** definitivamente. SEO: 404 (o 410 si tenia URL publica viva; ver `seo.md`). N: opcional. AUD: `DELETE`. |
| T11 | `PUBLISHED` | `edit (material)` | `PENDING` | owner (`property:update_own`) o admin (`property:update_any`) | Cambio en un campo **material** (LIFECYCLE-R03). | IDX: **des-indexa** mientras re-revisa. N: notifica a moderadores. PA conservado. AUD: `UPDATE` + transicion a re-revision. |
| T12 | `PUBLISHED` \| `PAUSED` \| etc. | `edit (no-material)` | (mismo) | owner (`property:update_own`) o admin (`property:update_any`) | Solo campos **no materiales** (LIFECYCLE-R03). | Sin re-revision. IDX: refresca documento (si `PUBLISHED`). AUD: `UPDATE`. |
| T13 | `DRAFT` \| `REJECTED` | `edit` | (mismo) | owner (`property:update_own`) | Edicion libre (no publicado). | Sin re-revision. IDX: no aplica. AUD: `UPDATE`. |
| T14 | cualquiera | `duplicate` | nuevo `DRAFT` | AGENT, ADMIN, SUPERADMIN (`property:create`) | Permiso de creacion; clona desde recurso existente. | **Nuevo `id` + nuevo `slug`**; M=0; PA=null; `is_featured=false`; `main_image_id` recalculado; sin `leads`/`favorites`/`featured`. AUD: `DUPLICATE`. |

Transiciones **no permitidas** (rechazo con error `409`/`422`, envelope `{"error":{...}}`, ver LIFECYCLE-R14): cualquier par (Desde, Accion) que no aparezca en la tabla; p.ej. `SOLD->PUBLISHED`, `DELETED->*`, `mark_sold` sobre `operation_type!=SALE`, `approve` sobre estado != `PENDING`.

## Reglas (LIFECYCLE-R#)

### Creacion y estado inicial

**LIFECYCLE-R01 — Crear (`create`).** Toda propiedad nace en `DRAFT`. El cliente NO puede fijar `status`, `published_at`, ni contadores (`views_count`, `clicks_count`, `leads_count`) en la creacion; el servidor los inicializa (`DRAFT`, `null`, `0/0/0`). `owner_id` = usuario autenticado (un ADMIN/SUPERADMIN puede crear en nombre de otro AGENT segun `roles-permissions.md`). `slug` se genera `{operation_type}-{property_kind}-{title-kebab}-{shortid}` y debe cumplir el regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`; colisiones se resuelven con nuevo `shortid`. Permiso: `property:create`. Efecto AUD: `CREATE`.

### Edicion por estado y re-revision

**LIFECYCLE-R02 — Campos editables por estado.**

| Estado | Edicion permitida | Detalle |
|--------|-------------------|---------|
| `DRAFT` | Todos los campos del owner | Edicion libre; no dispara revision. |
| `REJECTED` | Todos los campos del owner | Edicion libre para corregir el motivo de rechazo. |
| `PENDING` | **Solo admin** (correcciones de moderacion) | El owner NO edita mientras esta en cola; debe esperar `approve`/`reject` (o el admin puede editar). |
| `PUBLISHED` | Campos materiales y no materiales (ver R03) | Material -> re-revision (`PENDING`); no material -> in situ. |
| `PAUSED` | Igual que `PUBLISHED` (R03) | Editar material en `PAUSED` deja la propiedad en `PENDING` al reactivar/aprobar. |
| `SOLD` / `RENTED` | Solo metadatos no comerciales menores (alt_text de imagen, notas internas) | No reabre el listado; cambios estructurales requieren `duplicate`. |
| `DELETED` | Ninguna | Inmutable. |

Campos del sistema **nunca** editables por cliente en ningun estado: `id`, `slug` (salvo regeneracion controlada en `duplicate`), `owner_id` (salvo `property:assign`/admin), `status`, `published_at`, `views_count`, `clicks_count`, `leads_count`, `created_at`, `updated_at`, `deleted_at`.

**LIFECYCLE-R03 — Edicion material de `PUBLISHED` requiere re-revision.** Editar un **campo material** de una propiedad `PUBLISHED` (o `PAUSED`) la devuelve a `PENDING` (transicion T11) y la **des-indexa** hasta nueva `approve`. `published_at` se conserva.

- **Campos materiales** (disparan re-revision): `title`, `description`, `operation_type`, `property_kind`, `condition`, `price_amount`, `currency`, `country`, `state_province`, `city`, `locality_id`, `neighborhood`, `address`, `address_is_public`, `location_point`, `area_total`, `area_built`, `bedrooms`, `bathrooms`, `parking_spots`, `year_built`, conjunto de `amenities`, y cambio de imagen `MAIN`.
- **Campos NO materiales** (edicion in situ, sin re-revision, T12): `primary_cta`, `available_from`, `hoa_fees_amount`, `alt_text`/`position` de imagenes de galeria (no la MAIN), orden de galeria, y campos de `SeoMetadata` editables por panel (ver `seo.md`).
- Cambiar `operation_type` entre familias incompatibles con un estado comercial futuro (p.ej. de `SALE` a `RENT`) es material y reinicia revision.

### Publicacion (submit / approve / reject / resubmit)

**LIFECYCLE-R04 — Enviar a revision (`submit_for_review`).** Solo desde `DRAFT` (T2) o `REJECTED` (T5, alias `resubmit`). Permiso owner `property:publish_request`. Verifica pre-condiciones de R05; si fallan, responde `422` con `details` enumerando campos faltantes; NO cambia de estado.

**LIFECYCLE-R05 — Campos minimos para revision (gate de `submit_for_review`/`resubmit`).** Para pasar a `PENDING` deben estar presentes y validos:
`title`, `description`, `operation_type`, `property_kind`, `condition`, `price_amount` (>0) + `currency`, `country`, `state_province`, `city`, `locality_id`, `area_total` (>0), `bedrooms`, `bathrooms`, `parking_spots`, y **`>=1 PropertyImage` con exactamente una `MAIN`**. La regla de imagen MAIN unica y la pre-condicion `>=1 imagen` se validan tambien en `media-pipeline.md`. Validaciones de formato/rango se detallan en `validations.md`.

**LIFECYCLE-R06 — Aprobar (`approve`).** Solo desde `PENDING` -> `PUBLISHED` (T3). Permiso `property:approve` (ADMIN/SUPERADMIN). Efectos: si `published_at` es `null`, se setea `now()` (primera publicacion); si ya tenia valor (re-revision), se **conserva** el original. Indexa en search/sitemap y activa `SeoMetadata` con `robots="index,follow"`. Notifica al owner. AUD: `APPROVE`.

**LIFECYCLE-R07 — Rechazar (`reject`).** Solo desde `PENDING` -> `REJECTED` (T4). Permiso `property:reject`. **`reason` obligatorio y no vacio** (texto persistido y enviado al owner). No indexa. AUD: `REJECT` con `reason` en `after`. Desde `REJECTED` el owner edita libremente y vuelve a enviar (`resubmit`, T5).

### Pausa y reactivacion

**LIFECYCLE-R08 — Pausar (`pause`).** Solo desde `PUBLISHED` -> `PAUSED` (T6). Permiso owner `property:pause_own` o admin `property:update_any`. Des-indexa de search/sitemap; el detalle publico pasa a 404 (ver visibilidad). `published_at` se conserva. Reversible via `reactivate`.

**LIFECYCLE-R09 — Reactivar (`reactivate`).** Solo desde `PAUSED` -> `PUBLISHED` (T7). Mismos permisos que pausar. **No** dispara re-revision (el contenido ya fue aprobado), salvo que durante la pausa se haya hecho una edicion material (R03), en cuyo caso la propiedad ya estaria en `PENDING` y la salida sera por `approve`. Re-indexa; detalle vuelve a 200; `published_at` no se reescribe.

### Cierre comercial (vender / alquilar)

**LIFECYCLE-R10 — Marcar vendida (`mark_sold`).** Desde `PUBLISHED` o `PAUSED` -> `SOLD` (T8). **Pre-condicion estricta: `operation_type == SALE`**; en cualquier otro caso, error `422` (`code: "operation_type_mismatch"`). Permiso owner `property:update_own` o admin `property:update_any`. Des-indexa; aplica politica SEO 301/410 (`seo.md`). `SOLD` es cuasi-terminal (solo -> `DELETED`). AUD: `MARK_SOLD`.

**LIFECYCLE-R11 — Marcar alquilada (`mark_rented`).** Desde `PUBLISHED` o `PAUSED` -> `RENTED` (T9). **Pre-condicion estricta: `operation_type in {RENT, TEMPORARY}`**; en otro caso `422` (`code: "operation_type_mismatch"`). Mismos permisos que R10. Des-indexa; politica SEO 301/410 (`seo.md`). `RENTED` cuasi-terminal (solo -> `DELETED`). AUD: `MARK_RENTED`.

### Eliminacion (soft delete)

**LIFECYCLE-R13 — Eliminar (`soft_delete`).** Desde cualquier estado != `DELETED` -> `DELETED` (T10). Permiso owner `property:delete_own` (propias) o admin `property:delete_any` (cualquiera). Efecto: setea **`deleted_at=now()`**, NO borra fisicamente la fila (preserva integridad de `leads`, `audit_logs`, metricas historicas). Des-indexa definitivamente. Visibilidad: 404 (o 410 si la URL publica estaba viva; ver `seo.md`). Toda consulta de lectura debe filtrar `deleted_at IS NULL`. `DELETED` es terminal: no hay transicion de salida via API. AUD: `DELETE`.

### Duplicacion

**LIFECYCLE-R12 — Duplicar (`duplicate`).** Clona una propiedad existente (cualquier estado) en un **nuevo registro `DRAFT`** (T14). Permiso `property:create`. Reglas del clon:
- **Nuevo `id`** (UUID v4) y **nuevo `slug`** (regenerado con nuevo `shortid`).
- `status="draft"`, `published_at=null`, `deleted_at=null`.
- **Metricas en 0**: `views_count=clicks_count=leads_count=0`; no copia `PropertyView`.
- `is_featured=false`; no copia `FeaturedProperty`.
- No copia `leads` ni `favorites` (pertenecen al registro original).
- Copia datos de contenido (title con sufijo opcional, description, ubicacion, precio, amenities) e **imagenes** (nuevos `PropertyImage` con su `MAIN`/`GALLERY`, `position` preservado; `created_at` nuevo).
- `owner_id` = quien duplica (o conservado si admin lo indica, segun `roles-permissions.md`).
- AUD: `DUPLICATE` (registra `entity_id` origen en `before` y nuevo en `after`).

Uso tipico: re-publicar un inmueble `SOLD`/`RENTED` similar sin reabrir el registro cerrado.

### Guardas generales de la maquina de estados

**LIFECYCLE-R14 — Transiciones invalidas.** Cualquier (Desde, Accion) ausente en la tabla de transiciones se rechaza con el error envelope `{"error":{"code","message","details"}}`:
- `409 Conflict` con `code: "invalid_transition"` cuando la accion no aplica al estado actual (p.ej. `approve` sobre `DRAFT`, `reactivate` sobre `PUBLISHED`, cualquier accion sobre `DELETED`).
- `422 Unprocessable Entity` cuando la transicion existe pero falla una pre-condicion de datos (campos minimos, imagen MAIN, `operation_type` incompatible).
- `403 Forbidden` con `code: "forbidden"` cuando el actor carece del permiso (ver `roles-permissions.md`).
La maquina es la unica autoridad: ningun endpoint debe permitir saltos de estado fuera de la tabla.

**LIFECYCLE-R15 — Atomicidad y auditoria.** Cada transicion es **atomica** (transaccion DB): cambia `status` (+ campos derivados), actualiza contadores/indice y escribe **exactamente una** fila en `AuditLog` (append-only) con `actor_id`, `action` (mapeo en la columna Efectos: `CREATE`/`APPROVE`/`REJECT`/`PAUSE`/`REACTIVATE`/`MARK_SOLD`/`MARK_RENTED`/`DELETE`/`DUPLICATE`/`UPDATE`/`PUBLISH`), `entity_type="Property"`, `entity_id`, `before`/`after` (snapshots), `ip`, `user_agent`. `updated_at` se refresca en toda transicion. Si la transaccion falla, no hay cambio de estado ni efectos parciales.

**LIFECYCLE-R16 — Idempotencia.** Re-ejecutar una accion que dejaria el mismo estado destino sin cambios materiales (p.ej. `pause` sobre `PAUSED`) responde `409 invalid_transition` (no es idempotente silenciosa) salvo que la accion sea naturalmente idempotente por diseno; el cliente debe consultar el estado antes de reintentar.

## Visibilidad publica por estado

Define la respuesta HTTP del **detalle publico** (`GET /api/v1/properties/{slug}`) sin autenticacion. Las lecturas publicas no requieren auth (solo `PUBLISHED` es servible). Detalle de redirects/410 en `seo.md`; inclusion en listados/busqueda en `search-filters.md`.

| Estado | HTTP detalle publico | En search/sitemap | SEO | Regla |
|--------|----------------------|-------------------|-----|-------|
| `PUBLISHED` | **200** (sirve la pagina) | Si (indexado) | `robots="index,follow"` | VISIBLE |
| `SOLD` | **301** (a similar/listado) o **410** Gone | No | `noindex`; `redirect_from` segun `seo.md` | Cerrado; politica configurable |
| `RENTED` | **301** o **410** | No | `noindex`; `redirect_from` | Cerrado; politica configurable |
| `PAUSED` | **404** | No | sin SEO publico | Oculto temporal |
| `REJECTED` | **404** | No | sin SEO publico | No publicado |
| `DRAFT` | **404** | No | sin SEO publico | No publicado |
| `DELETED` | **404** (o **410** si tenia URL viva) | No | `noindex` | Eliminado |

**LIFECYCLE-R17 — Solo `PUBLISHED` responde 200.** El detalle publico devuelve `200` exclusivamente para `PublicationStatus.PUBLISHED` y con `deleted_at IS NULL`. Para el owner/admin autenticado con `property:read_any` (o `property:read_public` propio), el panel puede ver estados no publicos via endpoint privado; eso NO altera la respuesta publica.

**LIFECYCLE-R18 — `SOLD`/`RENTED` -> 301/410.** Una propiedad cerrada comercialmente NO responde 200. Politica por defecto **301** hacia un listado/propiedad similar (preserva SEO y experiencia); **410 Gone** opcional cuando se decide retirar la URL. La eleccion (301 vs 410) y el destino del redirect se configuran en `seo.md` (`redirect_from`, `canonical_url`). El estado cerrado nunca reaparece como 200.

**LIFECYCLE-R19 — Resto -> 404.** `PAUSED`, `REJECTED`, `DRAFT` devuelven **404** al publico (no revelan existencia). `DELETED` devuelve **404**, o **410** si la URL estuvo publica antes del borrado (decision SEO). En ningun caso se filtra contenido no publico ni `address` privada (ver `address_is_public`).

## Matriz estado x accion (resumen de validez)

`OK` = permitido; `-` = invalido (LIFECYCLE-R14). `mark_sold`/`mark_rented` ademas validan `operation_type` (R10/R11).

| Estado \ Accion | submit | approve | reject | pause | reactivate | mark_sold | mark_rented | soft_delete | duplicate | edit |
|-----------------|:------:|:-------:|:------:|:-----:|:----------:|:---------:|:-----------:|:-----------:|:---------:|:----:|
| DRAFT | OK | - | - | - | - | - | - | OK | OK | OK |
| PENDING | - | OK | OK | - | - | - | - | OK | OK | OK (admin) |
| PUBLISHED | - | - | - | OK | - | OK* | OK* | OK | OK | OK (R03) |
| PAUSED | - | - | - | - | OK | OK* | OK* | OK | OK | OK (R03) |
| SOLD | - | - | - | - | - | - | - | OK | OK | menor |
| RENTED | - | - | - | - | - | - | - | OK | OK | menor |
| REJECTED | OK | - | - | - | - | - | - | OK | OK | OK |
| DELETED | - | - | - | - | - | - | - | - | - | - |

\* sujeto a `operation_type`: `mark_sold` solo `SALE`; `mark_rented` solo `RENT`/`TEMPORARY`.

## Open Questions

- **OQ-1 (edicion material — alcance):** R03 lista los campos materiales. ¿Se requiere re-revision tambien cuando cambia solo `price_amount` a la **baja** (descuento) o solo en cambios estructurales? Default propuesto: todo cambio de `price_amount` es material. Confirmar con negocio.
- **OQ-2 (SOLD/RENTED — 301 vs 410):** Politica por defecto propuesta = 301 a propiedad/listado similar; 410 opcional. La decision final y el destino canonico viven en `seo.md`. Confirmar el criterio (¿ventana temporal antes de 410?).
- **OQ-3 (DELETED — 410):** ¿`DELETED` debe responder 410 (no 404) cuando la URL estuvo indexada, para acelerar la des-indexacion en buscadores? Coordinar con `seo.md`.
- **OQ-4 (re-publicacion tras cierre):** El contrato indica usar `duplicate` para reabrir un inmueble `SOLD`/`RENTED`. ¿Se desea ademas una accion explicita `relist` (PAUSED<-SOLD)? Default: NO; solo `duplicate`.
- **OQ-5 (auto-pausa por expiracion):** ¿Las propiedades `PUBLISHED` expiran tras N dias sin actividad y pasan automaticamente a `PAUSED`? No esta en el contrato; default NO. Confirmar si se requiere job de housekeeping.
