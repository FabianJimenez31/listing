# Banners y Destacados — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #11, #12.

## Resumen

Este documento especifica dos sistemas de promocion comercial 100% administrables desde el panel sin tocar codigo:

- **(A) Banners promocionales** (`Banner`): piezas graficas con CTA, ubicadas en posiciones fijas (`BannerPosition`), con segmentacion por contexto (localidad/ciudad/operacion/tipo), ventana de vigencia, prioridad y metricas de impresiones/clics/CTR.
- **(B) Inmuebles destacados** (`FeaturedProperty`): promocion temporal de una `Property` ya `PUBLISHED` en un alcance (`FeaturedScope`: `HOME`, `SEARCH_RESULTS`, `LOCALITY`), con prioridad, ventana de vigencia, limite por scope y metricas.

Ambos comparten un patron comun: una **regla de elegibilidad** (activo + dentro de ventana + segmentacion/contexto coincidente), un **orden determinista** (prioridad y desempates) y un **tracking** de impresiones/clics. Las lecturas publicas no requieren auth; la administracion requiere los permisos `banner:manage` y `featured:manage`.

Roles relevantes (de rbac): `banner:manage` y `featured:manage` los poseen `ADMIN` y `SUPERADMIN`. `AGENT`/`REGISTERED_USER`/`VISITOR` no administran banners ni destacados (un agente solicita destacar via flujo de aprobacion fuera de este alcance; el set se hace por admin con `property:feature`).

---

# (A) BANNERS PROMOCIONALES

## A.1 Modelo de datos — Banner (banners)

Tabla `banners` (ver data-model.md para indices canonicos). Campos:

| Campo | Tipo | Null | Default | Descripcion |
|---|---|---|---|---|
| `id` | UUID v4 (string) | no | gen | PK. |
| `title` | text | no | — | Titulo interno + posible overlay; no SEO. |
| `description` | text | si | null | Descripcion/subtitulo opcional. |
| `image_desktop_url` | text | no | — | URL CDN imagen desktop (obligatoria). |
| `image_mobile_url` | text | si | null | URL CDN imagen mobile; si null se usa desktop. |
| `cta_label` | text | si | null | Texto del boton CTA. |
| `cta_url` | text | si | null | Destino del CTA (URL absoluta o ruta interna). |
| `position` | `BannerPosition` | no | — | Slot de render: `home_hero`, `home_inline`, `listing_top`, `listing_inline`, `detail_sidebar`. |
| `priority` | int | no | 0 | Mayor = primero. Rango sugerido 0..1000. |
| `starts_at` | timestamptz | si | null | Inicio de vigencia (UTC). null = sin inicio. |
| `ends_at` | timestamptz | si | null | Fin de vigencia (UTC). null = sin fin. |
| `is_active` | bool | no | true | Interruptor manual on/off. |
| `target_locality_id` | UUID->Location | si | null | Segmenta a una localidad. |
| `target_city` | text | si | null | Segmenta por ciudad (cuando no hay locality_id). |
| `target_operation` | `OperationType` | si | null | Segmenta por operacion (`sale`/`rent`/`temporary`). |
| `target_kind` | `PropertyKind` | si | null | Segmenta por tipo de inmueble. |
| `impressions_count` | bigint | no | 0 | Contador denormalizado de impresiones. |
| `clicks_count` | bigint | no | 0 | Contador denormalizado de clics. |
| `created_at` | timestamptz | no | now() | UTC. |
| `updated_at` | timestamptz | no | now() | UTC. |

**Derivados (no persistidos):**
- `ctr` = `clicks_count / impressions_count` (0 si impresiones=0). Se expone como float redondeado a 4 decimales en respuestas admin.
- `is_live` (calculado) = `is_active AND (starts_at IS NULL OR starts_at <= now()) AND (ends_at IS NULL OR ends_at > now())`.

**Notas:**
- Un banner sin segmentacion (los 4 `target_*` en null) es **global** para su `position`.
- `target_locality_id` tiene prioridad sobre `target_city` para el calculo de especificidad (ver A.3).
- Contadores de impresiones/clics se denormalizan en `Banner`; el detalle de eventos de banner NO usa `PropertyView` (ese almacen es solo de engagement de `Property`). Si se requiere granularidad por evento se usa una tabla de eventos de banner fuera de este alcance (Open Question OQ-2).

## A.2 Posiciones (BannerPosition) y contexto de resolucion

| Position | Pagina / slot | Contexto disponible para segmentar |
|---|---|---|
| `home_hero` | Home, hero superior (carrusel) | ninguno (solo global o por ciudad/localidad si el visitante tiene geo) |
| `home_inline` | Home, bloque intercalado en feed | ninguno / geo opcional |
| `listing_top` | Resultados de busqueda, banda superior | filtros activos: `operation`, `kind`, `city`, `locality_id` |
| `listing_inline` | Resultados de busqueda, intercalado entre cards | mismos filtros que `listing_top` |
| `detail_sidebar` | Pagina de detalle de propiedad, columna lateral | atributos de la `Property` vista: `operation_type`, `property_kind`, `city`, `locality_id` |

El cliente (SPA CSR) envia el contexto al endpoint de resolucion; el backend filtra y ordena.

## A.3 Reglas de seleccion (BANNER-R#)

- **BANNER-R1 (Elegibilidad / live):** Un banner es candidato para una `position` solo si `is_live` es verdadero, es decir `is_active = true` Y `now()` esta dentro de `[starts_at, ends_at)` (limites null = abiertos). El borde inferior es inclusivo (`starts_at <= now`) y el superior exclusivo (`now < ends_at`).
- **BANNER-R2 (Match de posicion):** Solo se consideran banners cuyo `position` coincide exactamente con la posicion solicitada. No hay herencia entre posiciones.
- **BANNER-R3 (Match de segmentacion):** Un banner es elegible para un contexto si **cada** `target_*` no nulo coincide con el contexto provisto; los `target_*` nulos actuan como comodin (coinciden con todo). Reglas por campo:
  - `target_locality_id` no nulo -> debe igualar `context.locality_id`.
  - `target_city` no nulo -> debe igualar (case-insensitive, trim) `context.city`. Si el banner tiene `target_locality_id`, `target_city` se ignora en el match (la localidad manda).
  - `target_operation` no nulo -> debe igualar `context.operation`.
  - `target_kind` no nulo -> debe igualar `context.kind`.
  - Si el contexto no aporta un atributo (p.ej. `home_hero` sin geo), un banner que segmenta por ese atributo **no** es elegible (un `target_*` no nulo sin contexto para compararlo = no-match).
- **BANNER-R4 (Especificidad):** A cada banner elegible se le calcula un `specificity_score` = numero de `target_*` no nulos que matchearon, con peso adicional por localidad:
  - `target_locality_id` matched = +3
  - `target_city` matched = +2
  - `target_operation` matched = +1
  - `target_kind` matched = +1
  - global (sin targets) = 0
  Mayor especificidad gana sobre menor (un banner segmentado a la localidad desplaza al global).
- **BANNER-R5 (Orden / desempates):** El orden final de candidatos es, en cascada:
  1. `specificity_score` DESC (BANNER-R4),
  2. `priority` DESC,
  3. `starts_at` DESC NULLS LAST (mas reciente primero; null = mas antiguo),
  4. `created_at` DESC,
  5. `id` ASC (determinista total).
- **BANNER-R6 (Cardinalidad por slot):** Cada `position` define cuantos banners devuelve el endpoint (`limit`, configurable por admin, default por position): `home_hero`=5 (carrusel), `home_inline`=1, `listing_top`=1, `listing_inline`=3, `detail_sidebar`=2. Se devuelven los primeros `limit` segun BANNER-R5.
- **BANNER-R7 (Rotacion):** Cuando `home_hero` devuelve varios, el cliente rota; el backend ya entrega ordenado por BANNER-R5. No hay rotacion ponderada por peso en v1 (Open Question OQ-3).
- **BANNER-R8 (Conteo de impresiones):** Una impresion se registra cuando un banner entra en viewport y es efectivamente mostrado al usuario (evento `impression` enviado por el cliente). Reglas anti-inflado:
  - Deduplicacion por `(banner_id, session_hash)` dentro de una **ventana de 30 minutos**: impresiones repetidas en esa ventana NO incrementan el contador.
  - `impressions_count` se incrementa de forma atomica (`UPDATE ... SET impressions_count = impressions_count + 1`).
  - Bots/crawlers detectados (user-agent o sin `session_hash`) NO cuentan.
- **BANNER-R9 (Conteo de clics):** Un clic se registra al activar el CTA. Incrementa `clicks_count` atomicamente. Deduplicacion por `(banner_id, session_hash)` en ventana de **5 minutos**. Todo clic registrado implica que hubo al menos una impresion previa de esa sesion (si no la hubo, se registra ademas una impresion implicita para mantener CTR consistente).
- **BANNER-R10 (CTR):** `ctr = clicks_count / impressions_count` con `impressions_count = 0 -> ctr = 0`. Se expone en respuestas admin y en el dashboard de metricas; nunca en respuestas publicas.
- **BANNER-R11 (Vigencia y expiracion):** Un banner con `ends_at <= now()` deja de servirse automaticamente (BANNER-R1) sin necesidad de tocar `is_active`. No se borra; queda en historico con sus metricas. Admin puede reactivarlo ajustando fechas o `is_active`.
- **BANNER-R12 (Validacion al crear/editar):** Ver A.6. `image_desktop_url` y `position` obligatorios; si `cta_url` esta presente `cta_label` debe estarlo; `ends_at` (si ambos no nulos) debe ser `> starts_at`; `target_locality_id` debe referenciar una `Location` activa; `priority >= 0`.
- **BANNER-R13 (Fallback):** Si ningun banner es elegible para `(position, context)`, el endpoint devuelve `data: []` (HTTP 200). El cliente colapsa el slot; nunca muestra placeholder roto.
- **BANNER-R14 (Aislamiento de metricas):** Los contadores de `Banner` son independientes de los de `Property`/`FeaturedProperty`. Un clic en un banner NO afecta `clicks_count` de ninguna propiedad.

### Pseudocodigo de resolucion (BANNER-R1..R6)

```
GET banners WHERE position = :pos
  AND is_active = true
  AND (starts_at IS NULL OR starts_at <= now())
  AND (ends_at   IS NULL OR ends_at   >  now())
filtrar en backend por BANNER-R3 (match de targets contra context)
calcular specificity_score (BANNER-R4) para cada elegible
ordenar por (specificity DESC, priority DESC, starts_at DESC NULLS LAST,
             created_at DESC, id ASC)        # BANNER-R5
tomar los primeros :limit (BANNER-R6/ default por position)  -> data
```

## A.4 Endpoints — Banner

Base: `/api/v1`. Errores con envelope `{"error":{"code","message","details"}}`. Paginacion estandar `?page=&page_size=`.

### Admin (auth JWT Bearer, permiso `banner:manage`)

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/admin/banners` | Lista paginada. Filtros: `?position=&is_active=&target_city=&target_operation=&target_kind=&live=true|false&q=`. Orden `?sort=priority|-priority|created_at|-created_at`. Devuelve `ctr` e `is_live` calculados. |
| `POST` | `/admin/banners` | Crea banner. Body = campos editables (A.5). 201 con recurso. |
| `GET` | `/admin/banners/{id}` | Detalle de un banner (incluye metricas). |
| `PATCH` | `/admin/banners/{id}` | Actualizacion parcial (incl. `is_active`, fechas, segmentacion, prioridad). |
| `DELETE` | `/admin/banners/{id}` | Soft archive: pone `is_active=false` y `ends_at=now()`; conserva metricas (no borrado fisico salvo `?hard=true` por `SUPERADMIN`). |
| `GET` | `/admin/banners/{id}/metrics` | Series de metricas: `impressions_count`, `clicks_count`, `ctr`, y opcional desglose temporal `?from=&to=&granularity=day|week`. |

### Publico (sin auth — lecturas publicas)

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/banners/resolve` | Resuelve banners para un slot+contexto. Query: `position` (obligatorio), `locality_id`, `city`, `operation`, `kind`, `limit` (acotado a max por position). Devuelve lista ordenada (BANNER-R5) sin metricas. |
| `POST` | `/banners/{id}/impression` | Registra impresion (BANNER-R8). Body: `{session_hash, source?}`. 204. Idempotente por ventana. |
| `POST` | `/banners/{id}/click` | Registra clic (BANNER-R9). Body: `{session_hash}`. Devuelve `{cta_url}` para redireccion (302 opcional). 200/204. |

**Respuesta `GET /banners/resolve` (ejemplo):**

```json
{
  "data": [
    {
      "id": "b1a2c3d4-...",
      "title": "Apartamentos nuevos en Chapinero",
      "image_desktop_url": "https://cdn.example.com/banners/b1-desktop.webp",
      "image_mobile_url": "https://cdn.example.com/banners/b1-mobile.webp",
      "cta_label": "Ver ofertas",
      "cta_url": "/buscar?operation=sale&locality=chapinero",
      "position": "listing_top"
    }
  ],
  "meta": { "position": "listing_top", "count": 1 }
}
```

## A.5 Campos editables desde el panel (sin tocar codigo)

Todo lo siguiente se administra via `/admin/banners` (DoD #20, "administracion sin tocar codigo"):
`title`, `description`, `image_desktop_url`, `image_mobile_url`, `cta_label`, `cta_url`, `position`, `priority`, `starts_at`, `ends_at`, `is_active`, `target_locality_id`, `target_city`, `target_operation`, `target_kind`. Las imagenes se suben via el flujo de media (S3 + CDN) y el panel guarda la `cdn_url` resultante.

## A.6 Validaciones (BANNER-R12)

| Regla | Validacion | Error code |
|---|---|---|
| Obligatorios | `title`, `image_desktop_url`, `position` no vacios | `validation_required` |
| Position valida | `position` in `BannerPosition` | `validation_enum` |
| CTA consistente | si `cta_url` -> `cta_label` requerido; `cta_url` debe ser URL/ruta valida | `validation_cta` |
| Ventana | si `starts_at` y `ends_at` no nulos -> `ends_at > starts_at` | `validation_date_range` |
| Localidad | `target_locality_id` referencia `Location` con `is_active=true` | `validation_fk_inactive` |
| Operacion/Tipo | `target_operation` in `OperationType`; `target_kind` in `PropertyKind` | `validation_enum` |
| Prioridad | `priority` entero `>= 0` | `validation_range` |
| Imagenes | URLs deben pertenecer al CDN/dominio permitido (anti-SSRF/hotlink) | `validation_image_host` |

---

# (B) INMUEBLES DESTACADOS

## B.1 Modelo de datos — FeaturedProperty (featured_properties)

Promociona una `Property` (que debe estar `PUBLISHED`) elevandola en un alcance. Relacion 1:1 con `Property` (`property_id` unico).

| Campo | Tipo | Null | Default | Descripcion |
|---|---|---|---|---|
| `id` | UUID v4 (string) | no | gen | PK. |
| `property_id` | UUID->Property | no | — | **unique**. La propiedad destacada. |
| `scope` | `FeaturedScope` | no | — | `home`, `search_results`, `locality`. |
| `priority` | int | no | 0 | Mayor = primero dentro del scope. |
| `locality_id` | UUID->Location | si | null | **Requerido si `scope=LOCALITY`**, prohibido en otros scopes. |
| `starts_at` | timestamptz | si | null | Inicio de vigencia (UTC). null = inmediato. |
| `ends_at` | timestamptz | si | null | Fin de vigencia (UTC). null = indefinido. |
| `is_active` | bool | no | true | Interruptor manual. |
| `impressions_count` | bigint | no | 0 | Veces que la card destacada se mostro. |
| `clicks_count` | bigint | no | 0 | Clics hacia el detalle desde el slot destacado. |
| `created_at` | timestamptz | no | now() | UTC. |

**Derivados (no persistidos):** `ctr` (igual a BANNER-R10); `is_live` = `is_active AND ventana vigente AND property.status = 'published'`.

**Notas:**
- `property_id` es unico: una propiedad no puede tener dos registros `FeaturedProperty` simultaneos. Para destacar la misma propiedad en otro scope se requiere cambiar `scope` (o gestionar varios scopes con multiples registros => ver Open Question OQ-4; en v1 **un destacado activo por propiedad**, su `scope` determina donde aparece).
- El set/quita de destacado lo realiza un admin con permiso `property:feature` (set) y `featured:manage` (administracion CRUD del registro). El flag denormalizado `Property.is_featured` se mantiene en sync (B.3 FEATURED-R8).

## B.2 Alcances (FeaturedScope)

| Scope | Donde aparece | locality_id |
|---|---|---|
| `home` | Carrusel/bloque "Destacados" en Home | debe ser null |
| `search_results` | Sembrado al tope de resultados de busqueda (todas las busquedas o las que matcheen filtros, ver FEATURED-R5) | debe ser null |
| `locality` | Resultados/landing de una localidad especifica | **requerido** |

## B.3 Reglas (FEATURED-R#)

- **FEATURED-R1 (Destacado manual y temporal):** Un destacado se crea manualmente por admin sobre una `Property` ya `PUBLISHED`. Puede ser permanente (`ends_at = null`) o temporal (`ends_at` definido). No existe destacado automatico por algoritmo en v1.
- **FEATURED-R2 (Precondicion de estado):** Solo se puede crear/servir un destacado si la propiedad esta `PUBLISHED`. Si la propiedad pasa a `PAUSED`/`SOLD`/`RENTED`/`DELETED`/etc., el destacado deja de servirse (`is_live=false`) aunque su registro siga activo; al reactivarse (`PUBLISHED`) vuelve a servir si la ventana sigue vigente.
- **FEATURED-R3 (Elegibilidad / live):** Un destacado es candidato si `is_active=true` Y dentro de `[starts_at, ends_at)` (bordes como BANNER-R1) Y `property.status='published'`.
- **FEATURED-R4 (Limite maximo por scope):** Numero maximo de destacados **activos y vigentes** por scope (configurable por admin, defaults):
  - `home` = 12
  - `search_results` = 6
  - `locality` = 8 **por cada `locality_id`**
  Al intentar crear/activar uno que exceda el limite, el sistema rechaza con `featured_limit_reached` (HTTP 409) e informa el limite y el conteo actual. Admin debe expirar/desactivar otro o aumentar el limite en configuracion.
- **FEATURED-R5 (Match de contexto):**
  - `home` -> aparece en Home siempre que sea live.
  - `search_results` -> se inyecta al tope de cualquier pagina de resultados; opcionalmente acotado si en el futuro se agregan targets (no en v1: aplica a todas las busquedas).
  - `locality` -> aparece solo cuando `context.locality_id == featured.locality_id` (en busquedas filtradas por esa localidad y en la landing de la localidad).
- **FEATURED-R6 (Orden por prioridad / desempates):** Dentro de un scope (y localidad cuando aplica), el orden es:
  1. `priority` DESC,
  2. `starts_at` DESC NULLS LAST,
  3. `created_at` DESC,
  4. `id` ASC.
  Los destacados se muestran **antes** que los resultados organicos del listado, marcados visualmente como "Destacado" (badge). No se mezclan ni alteran el ranking organico subyacente (ver search-filters.md para integracion).
- **FEATURED-R7 (Expiracion automatica):** Un destacado con `ends_at <= now()` deja de servirse automaticamente (FEATURED-R3) sin tocar `is_active`. Un job/barrido nocturno (o lazy en lectura) puede normalizar `Property.is_featured=false` cuando ya no hay destacado live para esa propiedad (FEATURED-R8). El registro se conserva con metricas.
- **FEATURED-R8 (Sync de flag denormalizado):** `Property.is_featured` = existe al menos un `FeaturedProperty` live para esa propiedad. Se actualiza en cada create/activate/deactivate/expire del destacado, dentro de la misma transaccion cuando es por accion admin, o por el barrido para expiraciones por tiempo.
- **FEATURED-R9 (Unicidad):** `property_id` unico en `featured_properties`. Un segundo intento de destacar la misma propiedad responde `featured_already_exists` (HTTP 409) con el id del registro existente; el admin edita ese registro (cambia scope/ventana/priority) en lugar de crear otro.
- **FEATURED-R10 (locality_id condicional):** `scope=locality` exige `locality_id` no nulo y referenciando `Location` activa; `scope in {home, search_results}` exige `locality_id` null. Violacion -> `validation_locality_scope` (HTTP 422).
- **FEATURED-R11 (Conteo de impresiones/clics):** Identico patron que BANNER-R8/R9: impresion al mostrarse la card destacada (dedupe `(featured_id, session_hash)` 30 min), clic al navegar al detalle desde el slot destacado (dedupe 5 min). Incrementos atomicos sobre `FeaturedProperty.impressions_count`/`clicks_count`. Estas metricas son **independientes** de `Property.views_count`/`clicks_count` y de `PropertyView`: una vista de detalle alcanzada via destacado tambien genera su `PropertyView` con `source='featured'` (ver metrics.md), pero el conteo del slot vive en `FeaturedProperty`.
- **FEATURED-R12 (CTR):** Igual a BANNER-R10 (`clicks_count/impressions_count`, 0 si sin impresiones). Solo en respuestas admin/metricas.
- **FEATURED-R13 (Administrable sin codigo):** Crear, editar (scope, priority, ventana, locality), activar/desactivar y consultar metricas se hace 100% desde el panel admin; los limites por scope (FEATURED-R4) y los defaults de cardinalidad son configuracion editable (config:manage), no constantes hardcodeadas.
- **FEATURED-R14 (Aislamiento de scopes):** Los limites y el orden se calculan por scope de forma independiente; `locality` se cuenta y ordena por cada `locality_id` por separado.

### Pseudocodigo de resolucion de destacados

```
# Home / search / locality
SELECT fp.* FROM featured_properties fp
JOIN properties p ON p.id = fp.property_id
WHERE fp.scope = :scope
  AND fp.is_active = true
  AND (fp.starts_at IS NULL OR fp.starts_at <= now())
  AND (fp.ends_at   IS NULL OR fp.ends_at   >  now())
  AND p.status = 'published'
  AND (:scope <> 'locality' OR fp.locality_id = :context_locality_id)   # FEATURED-R5/R10
ORDER BY fp.priority DESC, fp.starts_at DESC NULLS LAST,
         fp.created_at DESC, fp.id ASC                                   # FEATURED-R6
LIMIT :max_for_scope                                                     # FEATURED-R4
```

## B.4 Endpoints — FeaturedProperty

Base: `/api/v1`.

### Admin (auth JWT Bearer)

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| `GET` | `/admin/featured` | `featured:manage` | Lista paginada. Filtros `?scope=&locality_id=&is_active=&live=&property_id=`. Devuelve `ctr`, `is_live`, datos basicos de la propiedad. |
| `POST` | `/admin/featured` | `property:feature` + `featured:manage` | Crea destacado. Body: `property_id`, `scope`, `priority?`, `locality_id?`, `starts_at?`, `ends_at?`, `is_active?`. Valida FEATURED-R2/R4/R9/R10. 201. |
| `GET` | `/admin/featured/{id}` | `featured:manage` | Detalle con metricas. |
| `PATCH` | `/admin/featured/{id}` | `featured:manage` | Edita scope/priority/ventana/locality/is_active. Re-valida limites. |
| `DELETE` | `/admin/featured/{id}` | `featured:manage` | Quita el destacado: `is_active=false` (o borrado fisico con `?hard=true` SUPERADMIN). Recalcula `Property.is_featured` (FEATURED-R8). |
| `GET` | `/admin/featured/{id}/metrics` | `metrics:read_global` | Impresiones/clics/CTR (+ desglose `?from=&to=&granularity=`). |

Atajo opcional sobre la propiedad (semantica equivalente, usa los mismos permisos/reglas):
`POST /admin/properties/{property_id}/feature` (set) y `DELETE /admin/properties/{property_id}/feature` (unset).

### Publico (sin auth)

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/featured?scope=home` | Destacados live para Home (ordenados FEATURED-R6). |
| `GET` | `/featured?scope=locality&locality_id=...` | Destacados live de una localidad. |
| `GET` | `/search?...` | El buscador inyecta `scope=search_results` (y `locality` si hay filtro de localidad) al tope; el contrato de respuesta de busqueda marca `is_featured=true` y orden (ver search-filters.md). |
| `POST` | `/featured/{id}/impression` | Registra impresion del slot (FEATURED-R11). Body `{session_hash, source?}`. 204. |
| `POST` | `/featured/{id}/click` | Registra clic del slot (FEATURED-R11). Body `{session_hash}`. 204. |

**Respuesta `GET /featured?scope=home` (ejemplo):**

```json
{
  "data": [
    {
      "featured_id": "f1a2b3c4-...",
      "scope": "home",
      "priority": 100,
      "property": {
        "id": "p9z8y7x6-...",
        "slug": "venta-apartamento-chapinero-a1b2c3",
        "title": "Apartamento en Chapinero",
        "operation_type": "sale",
        "property_kind": "apartment",
        "price_amount": 45000000000,
        "currency": "COP",
        "city": "Bogota",
        "main_image_url": "https://cdn.example.com/p/9z-main.webp",
        "is_featured": true
      }
    }
  ],
  "meta": { "scope": "home", "count": 1 }
}
```

## B.5 Validaciones (FeaturedProperty)

| Regla | Validacion | Error code | HTTP |
|---|---|---|---|
| Propiedad publicada | `property.status = 'published'` al crear/activar | `featured_property_not_published` | 422 |
| Scope valido | `scope` in `FeaturedScope` | `validation_enum` | 422 |
| locality condicional | `scope=locality` -> `locality_id` req. y `Location` activa; otros -> null | `validation_locality_scope` | 422 |
| Unicidad | `property_id` no duplicado | `featured_already_exists` | 409 |
| Limite por scope | conteo live < limite (FEATURED-R4) | `featured_limit_reached` | 409 |
| Ventana | si ambos no nulos -> `ends_at > starts_at` | `validation_date_range` | 422 |
| Prioridad | entero `>= 0` | `validation_range` | 422 |

---

## Metricas, dashboard y configuracion (A + B)

- **Dashboard admin** (`metrics:read_global`): por banner y por destacado muestra `impressions_count`, `clicks_count`, `ctr`, vigencia y estado live; agregados por `position`/`scope`/`locality`; ranking por CTR; alertas de baja performance (CTR bajo) y de proximos a expirar.
- **Configuracion editable** (`config:manage`): limites por scope (FEATURED-R4), `limit` por `position` (BANNER-R6), ventanas de dedupe de impresion/clic, dominios CDN permitidos para imagenes de banner. Cambios sin redeploy.
- **Privacidad:** el tracking usa `session_hash`/`ip_hash` (hashing), nunca PII directa, alineado con privacidad de `PropertyView`.

## Trazabilidad DoD

| DoD | Cubierto por |
|---|---|
| #11 Banners y promociones | Seccion (A): modelo Banner, posiciones, BANNER-R1..R14, endpoints admin+publico+tracking, validaciones, metricas/CTR, administrable sin codigo. |
| #12 Inmuebles destacados | Seccion (B): modelo FeaturedProperty, scopes, FEATURED-R1..R14 (manual/temporal, limite por scope, orden por prioridad, expiracion automatica, metricas), endpoints, validaciones. |

## Open Questions

- **OQ-1:** Rotacion ponderada de banners en `home_hero` (pesos por banner) vs orden estricto por BANNER-R5. v1 usa orden estricto; pendiente confirmar si se requiere ponderacion/airtime equitativo.
- **OQ-2:** Granularidad de eventos de banner: bastan los contadores denormalizados o se necesita una tabla de eventos `banner_events` para series temporales finas. v1 asume desglose temporal derivado de snapshots periodicos.
- **OQ-3:** Frecuencia/cap de impresiones por usuario (frequency capping) por banner/sesion mas alla del dedupe de conteo.
- **OQ-4:** Permitir que una misma propiedad este destacada en multiples scopes simultaneos (relajar la unicidad `property_id`) vs un unico destacado activo por propiedad (v1).
- **OQ-5:** Defaults exactos de limites por scope (FEATURED-R4) y de `limit` por position (BANNER-R6) — propuestos arriba, pendiente validacion de negocio.
- **OQ-6:** Politica de `search_results` segmentado por filtros (agregar `target_*` al destacado) en una version futura.
