# Búsqueda y Filtros — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #8.

## Resumen

Especifica el motor de descubrimiento publico de propiedades: el endpoint principal
`GET /api/v1/properties` (alias `GET /api/v1/search`), el catalogo completo de
query params (texto full-text + `pg_trgm`, ubicacion, atributos, rango de precio,
amenities, geoespacial PostGIS, destacados), los modos de ordenamiento, la
paginacion `page`/`page_size` con `meta` y el cursor opcional para *infinite scroll*.
Todas las lecturas son publicas (sin auth) y fijan `status=published`. Los filtros
son *bookmarkables*: el estado del SPA (React 18 CSR) se serializa 1:1 a la query
string para que cualquier URL sea compartible y reproducible (SEO + UX).

Contrato de respuesta: envelope de paginacion estandar
`{"data":[...],"meta":{...}}`. Contrato de error: `{"error":{"code","message","details"}}`.

```
Cliente SPA  --query string-->  GET /api/v1/properties
                                      |
                                      v
              parse+validate -> normalizar -> construir filtros SQL
                                      |
                  full-text(q) + pg_trgm + PostGIS(ST_DWithin) + WHERE atributos
                                      |
                  ORDER BY (sort) -> paginar (page|cursor) -> contar total
                                      |
                                      v
                       {"data":[ListingCard...], "meta":{...}}
```

## Endpoint principal

| Aspecto | Valor |
|---|---|
| Metodo / Ruta | `GET /api/v1/properties` |
| Alias | `GET /api/v1/search` (mismo handler, mismos params, misma respuesta) |
| Auth | Publico, sin JWT. `status` siempre fijado a `published` por el servidor |
| Cache | Redis (clave = hash normalizado de query) TTL corto; `Cache-Control` publico |
| Rate limit | Por IP (Redis); ver SEC en seguridad |
| Idempotencia | GET puro, sin efectos secundarios (las metricas de vista NO se cuentan aqui) |

El alias `/api/v1/search` existe por semantica/SEO y para una eventual divergencia
futura (p. ej. agregaciones/facetas). Hoy ambos resuelven identico.

## Query params (catalogo completo)

Tipos: `str`, `int`, `enum`, `decimal`, `bool`, `csv` (lista separada por comas, repetible).
Todos opcionales salvo donde se indique. Valores invalidos -> `422` (ver Validaciones).

### Texto y ubicacion

| Param | Tipo | Descripcion | Notas |
|---|---|---|---|
| `q` | str | Busqueda libre sobre `title`, `description` y la jerarquia de ubicacion; tambien acepta el NID numerico con o sin `/` inicial | Insensible a mayusculas, acentos y puntuacion |
| `locality` | str | Slug de `Location` (locality). Filtra por `locality_id` resuelto | Acepta slug; resuelve a `locality_id` |
| `city` | str | Coincidencia exacta (normalizada) sobre `city` | Case/acentos-insensible |
| `neighborhood` | str | Coincidencia sobre `neighborhood` | Case/acentos-insensible |
| `country` | str | Pais (`country`) | |
| `state_province` | str | Estado/provincia (`state_province`) | |

### Atributos de la propiedad

| Param | Tipo | Mapea a | Validacion |
|---|---|---|---|
| `operation_type` | enum (csv) | `operation_type` ∈ `OperationType` | `sale`,`rent`,`temporary` |
| `property_kind` | enum (csv) | `property_kind` ∈ `PropertyKind` | `house`,`apartment`,`lot`,`office`,`commercial`,`farm`,`other` |
| `condition` | enum (csv) | `condition` ∈ `PropertyCondition` | `new`,`used`,`remodeled`,`under_construction` |
| `bedrooms_min` | int | `bedrooms >= n` | `>= 0` |
| `bathrooms_min` | int | `bathrooms >= n` | `>= 0` |
| `area_min` | decimal | `area_total >= n` | `>= 0` (m²) |
| `area_max` | decimal | `area_total <= n` | `>= area_min` |
| `amenities` | csv (multi) | M2M `PropertyAmenity` por `Amenity.code` | semantica AND (deben estar todas) |
| `is_featured` | bool | `is_featured = true` | `true`/`false`/`1`/`0` |

### Precio y moneda

| Param | Tipo | Mapea a | Validacion |
|---|---|---|---|
| `currency` | enum | `currency` (ISO 4217) | `USD,EUR,COP,MXN,ARS,CLP,PEN,BRL` |
| `price_min` | int (minor units) | `price_amount >= n` | `>= 0`; en centavos (BIGINT) |
| `price_max` | int (minor units) | `price_amount <= n` | `>= price_min` |

> Dinero SIEMPRE en *minor units* (centavos), nunca float. Comparar `price_min`/`price_max`
> contra `currency` distinta NO convierte divisas: si se envia `price_min`/`price_max`
> sin `currency`, se filtra por monto numerico crudo y se recomienda exigir `currency`
> (ver `SEARCH-R8`).

### Geoespacial (PostGIS)

| Param | Tipo | Descripcion | Validacion |
|---|---|---|---|
| `lat` | decimal | Latitud del centro de busqueda | `-90..90`; requiere `lng`+`radius_km` |
| `lng` | decimal | Longitud del centro | `-180..180`; requiere `lat`+`radius_km` |
| `radius_km` | decimal | Radio en km | `> 0` y `<= 100`; requiere `lat`+`lng` |

Filtro: `ST_DWithin(location_point, ST_MakePoint(lng, lat)::geography, radius_km*1000)`.
Los tres params forman un grupo atomico (todos o ninguno).

### Orden y paginacion

| Param | Tipo | Default | Valores |
|---|---|---|---|
| `sort` | enum | `date_desc` (o `relevance` si hay `q`) | `relevance,price_asc,price_desc,date_desc,featured,popularity` |
| `page` | int | `1` | `>= 1` |
| `page_size` | int | `20` | `1..50` (max duro `50`) |
| `cursor` | str (opaco) | — | base64 *keyset*; mutuamente excluyente con `page` |

## Ordenamiento

| `sort` | Criterio | ORDER BY (resumen) | Notas |
|---|---|---|---|
| `relevance` | Relevancia textual | `ts_rank(...) DESC, similarity(...) DESC, published_at DESC` | Solo util con `q`; si no hay `q`, degrada a `date_desc` |
| `price_asc` | Precio ascendente | `price_amount ASC, id ASC` | Sin conversion de divisa |
| `price_desc` | Precio descendente | `price_amount DESC, id ASC` | |
| `date_desc` | Mas recientes | `published_at DESC, id DESC` | Default global |
| `featured` | Destacados primero | `is_featured DESC, featured.priority DESC NULLS LAST, published_at DESC` | Mezcla destacados arriba |
| `popularity` | Mas vistos | `views_count DESC, published_at DESC` | Usa contador denormalizado en `Property` |

Empate siempre desempatado por `id` para orden total y estabilidad de cursor.

## Paginacion

Dos modos, excluyentes:

1. **Offset (`page`/`page_size`)** — default; devuelve `meta` completo con `total`.
   ```json
   "meta": { "page": 1, "page_size": 20, "total": 137, "total_pages": 7 }
   ```
2. **Cursor (`cursor`)** — *infinite scroll*; *keyset pagination* sobre las llaves del
   `sort` activo + `id`. No recalcula `total` (mas barato). `meta` incluye `next_cursor`
   (null cuando no hay mas) y opcionalmente `prev_cursor`.
   ```json
   "meta": { "page_size": 20, "next_cursor": "eyJwIjo...", "prev_cursor": null, "has_more": true }
   ```

`cursor` es opaco (base64 de JSON `{sort, keys:[...], id}`); si llega corrupto o su
`sort` no coincide con el `sort` de la peticion -> `400 invalid_cursor`.

## Sincronizacion URL <-> estado del SPA

El SPA mantiene los filtros en la URL (React Router `searchParams`). Reglas de mapeo:

| Regla | Detalle |
|---|---|
| 1:1 | Cada filtro activo = un query param; quitar filtro = quitar param |
| Omitir defaults | No serializar valores por defecto (`page=1`, `page_size=20`, `sort` default) |
| CSV | Multivalor (`operation_type`, `amenities`, etc.) como `a,b,c` (no repeticion de clave) |
| Orden estable | Serializar claves en orden canonico fijo (clave de cache + URLs deterministas) |
| Compartible | Pegar la URL reproduce exactamente el mismo resultado (sin estado oculto) |
| Historial | Cambios de filtro = `replace` (no apila); cambio de pagina = `push` |
| Restore | Al cargar, el SPA hidrata el estado desde la query string antes del primer fetch |

## Reglas (SEARCH-R#)

| ID | Regla |
|---|---|
| SEARCH-R1 | El servidor SIEMPRE fija `status = published`. Cualquier `status` en la query se ignora. Solo propiedades `published` y con `deleted_at IS NULL` son visibles. |
| SEARCH-R2 | `q` usa full-text (tsvector ponderado: `title` peso A, `locality`/`neighborhood`/`city` peso B, `description` peso C) combinado con `pg_trgm` (`similarity`) para tolerancia a errores tipograficos; umbral minimo de similitud configurable (default `0.3`). |
| SEARCH-R3 | `q` solo busca en `address` cuando `address_is_public = true`; nunca expone direcciones privadas. |
| SEARCH-R4 | Filtros de igualdad/enum se combinan con AND. Valores multi (csv) de un MISMO enum se combinan con OR interno (p.ej. `property_kind=house,apartment` = casa O apartamento). |
| SEARCH-R5 | `amenities` se combina con AND: la propiedad debe tener TODAS las amenities solicitadas (match por `Amenity.code`). |
| SEARCH-R6 | Rangos: `price_min<=price_max`, `area_min<=area_max`. Si `min>max` -> `422 range_invalid`. Limites inclusivos (`>=`, `<=`). |
| SEARCH-R7 | El grupo geo (`lat`,`lng`,`radius_km`) es atomico: presencia parcial -> `422 geo_incomplete`. `radius_km` se *clampa*/valida a `<= 100`. |
| SEARCH-R8 | `price_min`/`price_max` no convierten divisas. Si se filtra por precio se RECOMIENDA enviar `currency`; sin `currency` se filtra por monto crudo (warning en `details`, no error). |
| SEARCH-R9 | `sort=relevance` requiere `q`; sin `q` degrada silenciosamente a `date_desc`. |
| SEARCH-R10 | `page_size` se *clampa* a `[1,50]`; valores fuera de rango se ajustan al limite (no error). `page>=1`; `page<1` -> `422`. |
| SEARCH-R11 | `cursor` y `page` son mutuamente excluyentes; enviar ambos -> `400 cursor_page_conflict`. El `sort` codificado en el cursor debe coincidir con el `sort` de la peticion. |
| SEARCH-R12 | Todo orden lleva desempate final por `id` para garantizar orden total estable (correctitud del *keyset*). |
| SEARCH-R13 | Params desconocidos se ignoran (forward-compat); no rompen la peticion. |
| SEARCH-R14 | Texto de ubicacion (`city`,`neighborhood`) compara de forma insensible a mayusculas y acentos (normalizacion `unaccent` + lower). |
| SEARCH-R15 | La respuesta NO incluye campos privados (`address` si `!address_is_public`, `owner` PII, contadores internos sensibles); devuelve la proyeccion *ListingCard*. |
| SEARCH-R16 | `featured` mezcla destacados arriba respetando `FeaturedProperty.priority`; un destacado vencido (`ends_at < now` o `is_active=false`) NO se trata como destacado. |
| SEARCH-R17 | El endpoint es de solo lectura: no incrementa `views_count` ni emite `PropertyView` (eso ocurre en el detalle). |
| SEARCH-R18 | Un `q` compuesto solo por NID, opcionalmente prefijado por `/`, `NID`, `ID` o `codigo`, se resuelve como coincidencia exacta de `Property.nid`. |
| SEARCH-R19 | Los accesos por ciudad serializan `location=<slug>`; `country` queda reservado para mercados/paises. Ambos incluyen el subarbol de la ubicacion seleccionada. |

## Indices necesarios

| Objetivo | Indice (resumen) |
|---|---|
| Full-text `q` | GIN sobre `to_tsvector('spanish', title||' '||description||' '||coalesce(locality...))` (columna generada `search_vector`) |
| Typo tolerance | GIN `gin_trgm_ops` sobre `title`, `neighborhood`, `city` (extension `pg_trgm`) |
| Geoespacial | GiST sobre `location_point` (geography) para `ST_DWithin` |
| Filtro publico base | `(status, published_at DESC)` parcial `WHERE status='published' AND deleted_at IS NULL` |
| Precio | `(currency, price_amount)` para rango + orden por precio |
| Atributos comunes | indices/compuestos sobre `operation_type`, `property_kind`, `condition`, `locality_id`, `bedrooms`, `bathrooms` |
| Destacados | `is_featured` parcial + join `FeaturedProperty(priority, is_active, ends_at)` |
| Popularidad | `views_count DESC` (parcial sobre publicadas) |
| Amenities | indice en `property_amenities(amenity_id, property_id)` para AND-match |

Extensiones requeridas: `postgis`, `pg_trgm`, `unaccent`.

## Ejemplo de request

```
GET /api/v1/properties?q=apartamento+chapinero&operation_type=sale,rent
    &property_kind=apartment&city=bogota&locality=chapinero
    &price_min=15000000000&price_max=60000000000&currency=COP
    &bedrooms_min=2&bathrooms_min=2&area_min=60&amenities=pool,gym
    &is_featured=true&lat=4.6533&lng=-74.0628&radius_km=3
    &sort=relevance&page=1&page_size=20
```

## Ejemplo de response (offset)

```json
{
  "data": [
    {
      "id": "a1b2c3d4-0000-4000-8000-000000000001",
      "slug": "venta-apartamento-chapinero-a1b2c3",
      "title": "Apartamento en Chapinero con vista",
      "operation_type": "sale",
      "property_kind": "apartment",
      "condition": "used",
      "price_amount": 42000000000,
      "currency": "COP",
      "city": "Bogota",
      "neighborhood": "Chapinero Alto",
      "bedrooms": 3,
      "bathrooms": 2,
      "parking_spots": 1,
      "area_total": 95,
      "is_featured": true,
      "main_image": {
        "thumb_url": "https://cdn.example.com/p/a1b2c3/thumb.webp",
        "cdn_url": "https://cdn.example.com/p/a1b2c3/main.webp",
        "alt_text": "Sala con balcon"
      },
      "location_point": { "lat": 4.6533, "lng": -74.0628 },
      "published_at": "2026-05-30T14:02:11Z",
      "relevance": 0.87
    }
  ],
  "meta": { "page": 1, "page_size": 20, "total": 137, "total_pages": 7 }
}
```

## Ejemplo de response (cursor / infinite scroll)

```
GET /api/v1/properties?city=bogota&sort=date_desc&page_size=20&cursor=eyJzb3J0...
```

```json
{
  "data": [ /* ...20 ListingCard... */ ],
  "meta": {
    "page_size": 20,
    "next_cursor": "eyJzb3J0IjoiZGF0ZV9kZXNjIiwia2V5cyI6WyIyMDI2LTA1LTI4VDA5OjEwOjAwWiJdLCJpZCI6Ii4uLiJ9",
    "prev_cursor": null,
    "has_more": true
  }
}
```

## Validaciones y errores

| Caso | HTTP | `error.code` |
|---|---|---|
| enum fuera de dominio (`operation_type`, etc.) | 422 | `validation_error` |
| `price_min>price_max` / `area_min>area_max` | 422 | `range_invalid` |
| geo incompleto (solo 1 o 2 de lat/lng/radius_km) | 422 | `geo_incomplete` |
| `lat`/`lng`/`radius_km` fuera de rango | 422 | `validation_error` |
| `page<1` | 422 | `validation_error` |
| `cursor` corrupto o `sort` no coincide | 400 | `invalid_cursor` |
| `cursor` + `page` juntos | 400 | `cursor_page_conflict` |
| `sort` no soportado | 422 | `validation_error` |

Ejemplo de envelope de error:

```json
{ "error": { "code": "range_invalid",
  "message": "price_min no puede ser mayor que price_max",
  "details": { "price_min": 60000000000, "price_max": 15000000000 } } }
```

## Trazabilidad

Cubre DoD #8 (filtros/busqueda/orden/paginacion). Requisitos funcionales asociados:
rango `FR-060..079` (search/filtros/detalle) en spec.md. Performance del endpoint:
ver NFR-010.. en spec.md y reglas PERF en performance.md.

## Open Questions

- OQ-1: Conversion de divisas para `price_min`/`price_max` cuando se mezclan
  `currency` distintas — ¿requerir `currency` obligatoria al filtrar por precio
  (endurecer `SEARCH-R8`) o introducir conversion server-side con tasas? (Pendiente
  de negocio.)
- OQ-2: ¿Exponer facetas/agregados (conteos por `property_kind`, rango de precio)
  en `meta` para construir filtros dinamicos en el SPA? Candidato para el alias
  `/api/v1/search`.
- OQ-3: Limite duro de `radius_km` (`100`) y `page_size` (`50`) — confirmar con
  capacidad/PERF antes de fijar definitivo.
