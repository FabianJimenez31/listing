# Performance — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #15.

## Resumen

Reglas de performance medibles para Listing (FastAPI + PostgreSQL 16/PostGIS + Redis + React 18 SPA en CSR, object storage S3 + CDN). El objetivo central es servir el catalogo publico (lecturas sin auth) de forma rapida, mobile-first y estable bajo carga, optimizando tres planos: (1) entrega de imagenes/media, (2) backend de busqueda/detalle/home/banners, (3) bundle del SPA y Core Web Vitals. Cada regla `PERF-R#` define un objetivo cuantificado, su metodo de medicion y la condicion de cumplimiento. Mapea a NFR-010.. (Performance) en spec.md.

Las medidas son percentiles (p50/p95/p99) sobre ventana movil de 5 min en horario pico, medidos server-side (latencia de respuesta API) y client-side (CWV via RUM / `web-vitals`). "Con cache" = key presente en Redis (cache hit). "Sin cache" = cache miss que ejecuta consulta a PostgreSQL.

## Objetivos cuantitativos (resumen)

| Plano | Metrica | Objetivo |
|---|---|---|
| Busqueda/listado | p95 latencia API con cache | < 300 ms |
| Busqueda/listado | p95 latencia API sin cache (cache miss) | < 600 ms |
| Detalle propiedad | p95 latencia API (GET por slug) | < 250 ms |
| Home | p95 latencia API (home payload) | < 250 ms |
| Resolucion banners/featured | p95 latencia API | < 120 ms |
| Autocompletado/typeahead | p95 latencia API | < 150 ms |
| Imagen LCP | descarga de variante main (CDN) | < 200 ms desde edge |
| SPA mobile | LCP (p75, 4G/mid-tier) | < 2.5 s |
| SPA mobile | INP (p75) | < 200 ms |
| SPA mobile | CLS (p75) | < 0.1 |
| SPA | bundle inicial (JS gzip, ruta home) | < 180 KB |
| Throughput | lecturas publicas sostenidas | >= 500 RPS sin degradar p95 |

## 1. Imagenes y multimedia

Las imagenes son el principal componente de peso de pagina y el LCP del detalle/listado. Reglas en `MEDIA`/data-model definen el modelo `PropertyImage` (campos `original_url`, `cdn_url`, `thumb_url`, `width`, `height`, `bytes`, `content_type`). Aqui se fijan los objetivos de entrega.

### Variantes y formatos

| Variante | Uso | Ancho objetivo | Formato preferente | Calidad |
|---|---|---|---|---|
| `thumb` | grids, listado, miniaturas galeria | 320 px | AVIF -> WebP -> JPEG | ~60 |
| `card` | tarjeta de resultado / featured | 640 px | AVIF -> WebP -> JPEG | ~65 |
| `detail` | imagen principal detalle (LCP) | 1024 px | AVIF -> WebP -> JPEG | ~72 |
| `full` | lightbox / zoom galeria | 1600 px | AVIF -> WebP -> JPEG | ~78 |
| `original` | archivo subido sin transformar | nativo | original | n/a |

- El `original` se conserva separado de las variantes derivadas (no se sirve al publico salvo descarga explicita por owner/admin). Las variantes derivadas se generan asincronamente al subir (pipeline fuera de la ruta de request del usuario).
- Negociacion de formato por `Accept` header (AVIF si soportado, fallback WebP, fallback JPEG) servida por el CDN/transformador. `content_type` y `bytes` se persisten por variante para diagnostico.

### Entrega responsive (frontend)

- Toda `<img>` de catalogo usa `srcset` + `sizes` apuntando a las variantes (`thumb`/`card`/`detail`/`full`) para que el navegador elija el ancho correcto segun viewport y DPR. Ej.: `srcset="...-320.avif 320w, ...-640.avif 640w, ...-1024.avif 1024w"`.
- `loading="lazy"` en todas las imagenes below-the-fold (grids, galeria secundaria). La imagen LCP (main del detalle / primera card above-the-fold) usa `loading="eager"` + `fetchpriority="high"` y NO se lazy-loadea.
- Fallback/refuerzo de lazy con `IntersectionObserver` para galerias y carruseles que montan dinamicamente.
- `width`/`height` (o `aspect-ratio` CSS) SIEMPRE presentes en el markup para reservar espacio y evitar reflow (contribuye a CLS objetivo < 0.1).
- Placeholder de baja resolucion (LQIP / blur o color dominante) mientras carga la variante final.

### CDN y cache headers

- Variantes servidas exclusivamente via CDN (edge) sobre object storage S3-compatible. URLs versionadas/inmutables (hash o id en path) para permitir cache agresivo.
- `Cache-Control: public, max-age=31536000, immutable` para variantes derivadas (URL cambia si cambia el contenido).
- `original` (no publico): `Cache-Control: private, no-store` o acceso firmado de corta duracion.
- Compresion en transito gestionada por CDN; formatos ya comprimidos (AVIF/WebP/JPEG) no se re-comprimen con gzip.

## 2. Backend (consultas, paginacion, indices, cache)

### Paginacion obligatoria

- TODO endpoint de coleccion DEBE paginar con `?page=&page_size=` y devolver el envelope canonico `{"data":[...],"meta":{page,page_size,total,total_pages}}`. No existen endpoints que devuelvan colecciones sin limite.
- `page_size` por defecto = 20; maximo = 50 (valores > 50 se truncan a 50). `page` >= 1.
- `total`/`total_pages` se calculan con `COUNT(*)` filtrado; para resultados grandes el `COUNT` se cachea junto con la pagina (mismo cache key del filtro) para evitar recomputo por pagina.
- Orden estable garantizado (incluir `id` como desempate del `ORDER BY`) para paginacion consistente.

### Indices de DB (referencia data-model)

Los indices se definen en data-model; aqui se referencian por su uso de performance. El planner debe usar indice (no Seq Scan) en todas las rutas calientes.

| Tipo indice | Columna(s) / expresion | Sirve a |
|---|---|---|
| GiST (geography) | `properties.location_point` | filtros radio/bbox geoespaciales, ordenar por cercania |
| btree | `properties.status` | filtro visibilidad publica (solo PUBLISHED) |
| btree compuesto | `properties (status, operation_type, property_kind, city)` | filtros combinados frecuentes del buscador |
| btree | `properties.price_amount` | filtro/orden por precio (en minor units BIGINT) |
| btree | `properties (locality_id, status)` | listados por localidad |
| btree | `properties.published_at DESC` | orden por mas recientes |
| btree (parcial) | `properties (is_featured) WHERE is_featured` | resolucion de destacados |
| GIN + pg_trgm | `properties.title`, `properties.description` | busqueda textual fuzzy / ILIKE / similarity |
| btree unique | `properties.slug` | resolucion de detalle por slug |
| btree | `property_images (property_id, position)` | carga ordenada de galeria |
| btree | `leads (property_id, created_at)`, `leads (owner_id, status)` | bandeja de leads del agente |
| btree | `property_views (property_id, created_at)`, `(event_type)` | agregacion de metricas |
| btree | `favorites (user_id, property_id)` unique | favoritos del usuario |

- Soft delete: las consultas publicas filtran `deleted_at IS NULL` y `status = 'published'`; preferir indices parciales `WHERE deleted_at IS NULL` en columnas calientes.

### Consultas optimizadas

- Prohibido N+1: cargar relaciones con `JOIN`/eager loading explicito (p.ej. `selectinload`/`joinedload`) para `Property -> images (solo MAIN o primeras N)`, `-> amenities`, `-> seo`, `-> owner`. El listado NO debe disparar una query por fila.
- Seleccionar solo columnas necesarias por vista: el listado/card NO trae `description`, `jsonld`, ni galeria completa; solo campos de tarjeta (`id, slug, title, price_amount, currency, operation_type, property_kind, city, bedrooms, bathrooms, area_total, main_image_id` + thumb del MAIN). El detalle trae el set completo.
- Contadores denormalizados (`views_count`, `clicks_count`, `leads_count`, `impressions_count`) se leen de la fila, NO se calculan con `COUNT` sobre `property_views`/`leads` en la ruta de lectura.
- Filtro geoespacial usa `ST_DWithin(location_point, :point, :radius_m)` (sargable contra GiST), no `ST_Distance` en `WHERE`.
- Toda consulta de ruta caliente se valida con `EXPLAIN (ANALYZE, BUFFERS)` en CI/revision; criterio: uso de indice esperado y sin Seq Scan sobre `properties` en filtros publicos.
- Connection pooling configurado (pool reutilizado); sin abrir conexion por request.

### Cache Redis

| Cache key | Contenido | TTL | Invalidacion |
|---|---|---|---|
| `search:{hash(filtros+orden+page+page_size)}` | pagina de resultados + meta (count) | 60 s | TTL + bust por evento publish/update/delete/price-change |
| `home:v1` | payload de home (destacados + secciones + banners home) | 120 s | TTL + bust al cambiar featured/banner |
| `banners:{position}:{ctx}` | banners activos resueltos por posicion/segmentacion | 120 s | TTL + bust en banner create/update/activate |
| `featured:{scope}:{locality?}` | propiedades destacadas resueltas y ordenadas | 120 s | TTL + bust en featured create/update/expire |
| `detail:{slug}` | payload de detalle (opcional, cache corta) | 30 s | bust en update/pause/sold/rented/delete de la propiedad |
| `typeahead:{prefix}` | sugerencias autocompletado | 300 s | TTL |

- `hash` del search key se calcula sobre filtros normalizados (orden canonico de parametros, valores casteados) para maximizar hit ratio.
- Objetivo de cache hit ratio en busquedas populares y home: >= 70% en pico.
- Estrategia ante miss: calcular, escribir en Redis con TTL, responder. Evitar "cache stampede" con lock/single-flight por key en recomputos costosos (home, featured).
- Contadores de engagement (`views`/`clicks`/`impressions`) se incrementan en Redis y se flushean en batch a PostgreSQL (no un `UPDATE` sincrono por evento) para no penalizar latencia ni generar contencion de filas.
- Redis tambien provee rate limiting (NFR seguridad) sin tocar la ruta de DB.

## 3. Frontend SPA (React 18 / Vite, CSR)

- Code-splitting por ruta: cada ruta del SPA (home, resultados de busqueda, detalle, panel agente, admin) se carga via `React.lazy` + `Suspense` / import dinamico, de modo que el panel agente/admin no entra en el bundle del catalogo publico.
- Bundle splitting de vendor: separar dependencias grandes (mapa, libreria de graficas del panel) en chunks propios para que el catalogo publico no las descargue.
- Prefetch inteligente: prefetch del chunk de detalle al hacer hover/focus sobre una card (o cuando entra al viewport) para que la navegacion a detalle sea instantanea. Prefetch de la siguiente pagina de resultados en idle.
- Tree-shaking y `import` granular (no importar librerias enteras por un helper).
- Assets estaticos del SPA con hash en nombre y `Cache-Control` largo (`immutable`); `index.html` con cache corto/validacion para permitir despliegues.
- Datos: cliente HTTP con cache en memoria/`stale-while-revalidate` para listados ya vistos; no re-fetch redundante al volver atras.
- Mobile-first: render del above-the-fold (cards/imagen LCP) priorizado; diferir widgets no criticos (mapa interactivo, recomendados) hasta interaccion/idle.

## 4. Core Web Vitals (objetivos)

Medidos en p75 de usuarios reales (RUM con `web-vitals`), perfil mobile mid-tier / red 4G.

| Metrica | Objetivo (good) | Palancas principales |
|---|---|---|
| LCP | < 2.5 s | imagen LCP `eager`+`fetchpriority=high`+AVIF/WebP desde CDN; payload API detalle < 250 ms p95; bundle inicial chico |
| CLS | < 0.1 | `width`/`height`/`aspect-ratio` en imagenes; reservar espacio de banners/anuncios; sin inyectar contenido que empuje layout; fuentes con `font-display: swap` |
| INP | < 200 ms | code-splitting (menos JS en main thread); diferir trabajo no critico; interacciones (filtros, favorito) optimistas y no bloqueantes |
| TTFB | < 200 ms (cache) | cache Redis para home/search/banners; CDN edge para estaticos |
| FCP | < 1.8 s | bundle home < 180 KB; CSS critico inline; preconnect a CDN/API |

## Reglas (PERF-R#)

| ID | Regla | Objetivo medible | Como se mide |
|---|---|---|---|
| PERF-R1 | Busqueda/listado responde rapido con cache | p95 < 300 ms (cache hit) | latencia server-side endpoint `GET /api/v1/properties` (search) |
| PERF-R2 | Busqueda tolera cache miss | p95 < 600 ms (miss a PostgreSQL) | latencia server-side en miss |
| PERF-R3 | Detalle por slug rapido | p95 < 250 ms | latencia `GET /api/v1/properties/{slug}` |
| PERF-R4 | Home rapido | p95 < 250 ms | latencia endpoint de home |
| PERF-R5 | Banners y destacados se resuelven rapido | p95 < 120 ms | latencia resolucion banners/featured |
| PERF-R6 | Autocompletado fluido | p95 < 150 ms | latencia typeahead |
| PERF-R7 | Paginacion obligatoria | 100% de endpoints de coleccion paginados; `page_size` <= 50 | revision de contrato + test de API |
| PERF-R8 | Sin N+1 ni Seq Scan en rutas publicas | 0 Seq Scan sobre `properties` en filtros publicos; 0 query-por-fila | `EXPLAIN (ANALYZE, BUFFERS)` en CI sobre queries calientes |
| PERF-R9 | Indices presentes y usados | todos los indices del data-model creados; planner usa indice esperado | migracion + `EXPLAIN` |
| PERF-R10 | Cache hit ratio en pico | >= 70% en search/home | metrica Redis (hits/(hits+misses)) |
| PERF-R11 | Contadores no sincronos | engagement (`views/clicks/impressions`) via Redis + flush batch; 0 `UPDATE` sincrono por evento en ruta de lectura | revision de codigo + APM |
| PERF-R12 | Imagenes con variantes responsive | toda `<img>` de catalogo con `srcset`+`sizes`; variantes thumb/card/detail/full generadas | auditoria DOM + storage |
| PERF-R13 | Formatos modernos | AVIF/WebP servidos con fallback por `Accept` | inspeccion respuesta CDN |
| PERF-R14 | Lazy loading correcto | below-the-fold con `loading=lazy`/IntersectionObserver; LCP `eager`+`fetchpriority=high` | auditoria DOM / Lighthouse |
| PERF-R15 | CDN con cache largo e inmutable | variantes con `Cache-Control: public, max-age=31536000, immutable`; original no publico | inspeccion headers |
| PERF-R16 | Original separado de variantes | `original` no servido al publico; variantes derivadas distintas | revision storage + data-model |
| PERF-R17 | Code/bundle splitting del SPA | rutas via lazy import; panel admin/agente fuera del bundle publico | analisis de bundle (rollup-visualizer) |
| PERF-R18 | Bundle inicial acotado | JS inicial ruta home < 180 KB gzip | build report / CI budget |
| PERF-R19 | Prefetch de navegacion | prefetch de chunk de detalle on hover/viewport; next page en idle | revision de implementacion |
| PERF-R20 | LCP objetivo | p75 < 2.5 s (mobile) | RUM `web-vitals` |
| PERF-R21 | CLS objetivo | p75 < 0.1 | RUM `web-vitals`; dimensiones reservadas en imagenes/banners |
| PERF-R22 | INP objetivo | p75 < 200 ms | RUM `web-vitals` |
| PERF-R23 | Throughput sostenido | >= 500 RPS de lecturas publicas sin violar p95 | prueba de carga (k6/Locust) |
| PERF-R24 | Connection pooling | pool de conexiones reutilizado; 0 conexion-por-request | config + APM |
| PERF-R25 | Anti-stampede en cache | single-flight/lock por key en recomputo de home/featured | revision de codigo + prueba de concurrencia |

## Presupuestos de performance (CI budgets)

| Recurso | Budget | Gate |
|---|---|---|
| JS inicial (home, gzip) | <= 180 KB | falla build si excede |
| CSS inicial (gzip) | <= 50 KB | falla build si excede |
| Peso total above-the-fold (home, mobile) | <= 600 KB | warning/falla |
| Imagen LCP (variante detail) | <= 120 KB (AVIF) | auditoria |
| Lighthouse Performance (mobile) | >= 90 | gate CI |

## Open Questions

- OQ-PERF-1: Confirmar el transformador de imagenes (CDN nativo tipo Cloudflare/Imgix vs. pipeline propio con worker) que genera AVIF/WebP y variantes; define quien aplica `Accept`-negotiation y la nomenclatura final de URLs versionadas.
- OQ-PERF-2: Definir herramienta oficial de RUM/CWV (web-vitals propio + endpoint, o proveedor) y la ruta de ingesta de metricas client-side.
- OQ-PERF-3: Confirmar si el detalle se cachea en Redis (`detail:{slug}`, TTL 30 s) o se sirve siempre fresco desde DB dada su baja cardinalidad y la necesidad de exactitud de contadores.
- OQ-PERF-4: Fijar el SLA de propagacion de invalidacion de cache tras publish/update (cuanto tarda en reflejarse un cambio en search/home: aceptable <= TTL o se requiere bust inmediato).
- OQ-PERF-5: Confirmar objetivo de throughput pico (RPS) real esperado para dimensionar replicas de read y tamano de Redis.
