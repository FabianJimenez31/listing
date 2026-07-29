# SEO Tecnico — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #13.

## Resumen

Esta es la **estrategia SEO tecnica** del catalogo. Cubre indexabilidad,
URLs amigables, metadatos (meta + Open Graph + JSON-LD), sitemap/robots
generados por backend, canonicals, redirects 301, paginas indexables por
localidad/tipo/operacion, schema.org y el manejo SEO de estados no publicados.
Las reglas normativas viven en la seccion **Reglas (SEO-R#)**.

> ⚠️ **CALLOUT — Limitacion estructural (CSR/SPA).** El frontend es **React 18
> SPA renderizado en cliente (CSR via Vite)**. El HTML inicial que recibe un
> crawler es practicamente vacio (`<div id="root"></div>` + bundle JS): el
> contenido real se pinta tras ejecutar JavaScript. Googlebot **si** renderiza
> JS (en dos fases, con cola y latencia), pero la mayoria de bots — Bingbot
> historicamente limitado, y crawlers sociales como **facebookexternalhit /
> Twitterbot / WhatsApp / LinkedIn** que **NO ejecutan JS** — solo leen el HTML
> servido. Esto degrada: indexacion rapida, presupuesto de rastreo (crawl
> budget), y previews al compartir (Open Graph). **Por eso este documento define
> mitigaciones realistas (SEO-R1..R24) y recomienda fuertemente una capa de
> prerender para bots (ver SEO-R23 y Open Questions).** Sin prerender, los meta
> inyectados en cliente NO seran vistos por bots sociales.

## Arquitectura SEO (responsabilidades backend vs cliente)

```
                 Crawler / Bot                     Usuario humano
                      |                                  |
            (User-Agent es bot?)                         |
                      |  si              no -------------> SPA CSR + react-helmet-async
            +---------+---------+                          (meta inyectados en cliente)
            | Prerender layer   |  (RECOMENDADO, SEO-R23)
            | snapshot HTML     |
            +---------+---------+
                      |
   Backend FastAPI (/api/v1) sirve SIEMPRE:
   - GET /sitemap.xml  (+ sitemap index por shard)      [SEO-R7]
   - GET /robots.txt                                     [SEO-R8]
   - GET /api/v1/seo/metadata?slug=...  (meta+OG+JSON-LD)[SEO-R3]
   - GET /api/v1/properties/{slug}  (estado -> 200/301/410/404) [SEO-R20..R22]
```

| Artefacto | Generado por | Mecanismo | Regla |
|---|---|---|---|
| `sitemap.xml` / sitemap index | Backend FastAPI | Dinamico desde DB (solo `PUBLISHED`) | SEO-R7 |
| `robots.txt` | Backend FastAPI | Dinamico (incluye URL del sitemap) | SEO-R8 |
| meta tags + Open Graph + JSON-LD | Cliente (`react-helmet-async`) | Alimentado por `GET /api/v1/seo/metadata` | SEO-R3, SEO-R4 |
| Slug unico por propiedad | Backend | `SeoMetadata.slug` + `Property.slug` | SEO-R5, SEO-R9 |
| Canonical | Cliente + endpoint | `SeoMetadata.canonical_url` | SEO-R12 |
| Redirect 301 al cambiar slug | Backend | `SeoMetadata.redirect_from[]` | SEO-R13 |
| Prerender para bots | Edge/proxy (RECOMENDADO) | Prerender.io / Rendertron / snapshot | SEO-R23 |

## 1. URLs amigables y patrones de slug indexables

Todas las URLs publicas usan slugs (regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`). Hay
cuatro familias de paginas indexables: **detalle de propiedad**, **localidad**,
**tipo de inmueble** y **tipo de operacion** (mas sus combinaciones).

| Tipo de pagina | Patron de ruta (frontend) | Fuente del slug | Indexable |
|---|---|---|---|
| Detalle propiedad | `/p/{property_slug}` | `Property.slug` = `{operation}-{kind}-{title-kebab}-{shortid}` | Solo si `PUBLISHED` |
| Localidad | `/{country}/{location_slug}` | `Location.slug` | Si (`Location.is_active`) |
| Tipo de inmueble | `/tipo/{property_type_slug}` | `PropertyType.slug` | Si (`PropertyType.is_active`) |
| Operacion | `/operacion/{operation_value}` | `OperationType` value (`sale`/`rent`/`temporary`) | Si |
| Operacion + tipo | `/operacion/{operation}/tipo/{kind}` | combinacion | Si (canonical autoreferente) |
| Operacion + localidad | `/operacion/{operation}/{location_slug}` | combinacion | Si |
| Operacion + tipo + localidad | `/operacion/{operation}/tipo/{kind}/{location_slug}` | combinacion (faceta canonica) | Si |

Ejemplo detalle: `/p/venta-apartamento-chapinero-a1b2c3`. Ejemplo faceta:
`/operacion/sale/tipo/apartment/co-bogota-chapinero`.

**Facetas no canonicas** (orden, paginas internas de filtro multi-valor, query
params de ordenamiento `?sort=`, busqueda libre `?q=`): se sirven con
`robots: "noindex,follow"` y `canonical` apuntando a la faceta canonica para
evitar contenido duplicado y dilucion del crawl budget (SEO-R14, SEO-R15).

## 2. Endpoint de metadata por slug

`react-helmet-async` inyecta en cliente los tags `<head>` por ruta, alimentado
por un unico endpoint de lectura publica:

```
GET /api/v1/seo/metadata?entity_type={property|location|property_type|operation}&slug={slug}
-> 200 {
  "data": {
    "meta_title": "...", "meta_description": "...",
    "canonical_url": "https://.../p/venta-apartamento-chapinero-a1b2c3",
    "robots": "index,follow",
    "og": {"og_title","og_description","og_image_url","og_type":"website"},
    "jsonld": { ... schema.org ... },
    "breadcrumbs": [ ... ]
  }
}
-> 301 si slug en redirect_from (envelope con Location target) [SEO-R13]
-> 410 si entidad SOLD/RENTED con politica gone [SEO-R21]
-> 404 si entidad inexistente o DRAFT/PENDING/PAUSED/REJECTED/DELETED [SEO-R22]
```

Los valores provienen de la entidad `SeoMetadata` (campos `meta_title`,
`meta_description`, `og_title`, `og_description`, `og_image_url`,
`canonical_url`, `jsonld`, `robots`, `redirect_from`). Cuando falten, el backend
deriva defaults desde `Property` (titulo, precio, localidad, imagen MAIN).

| Campo `<head>` | Origen | Default si vacio |
|---|---|---|
| `<title>` | `SeoMetadata.meta_title` | `{title} en {city} — {operation_label} {kind_label}` |
| `<meta name="description">` | `SeoMetadata.meta_description` | primeros ~155 chars de `Property.description` |
| `<link rel="canonical">` | `SeoMetadata.canonical_url` | URL absoluta autoreferente del slug actual |
| `<meta name="robots">` | `SeoMetadata.robots` | `index,follow` (estado `PUBLISHED`) |
| `og:title`/`og:description` | `SeoMetadata.og_*` | espejo de meta_title/description |
| `og:image` | `SeoMetadata.og_image_url` | `Property.main_image` (`PropertyImage.cdn_url`, role=MAIN) |
| `og:url` | canonical | igual a canonical |
| `og:type` | fijo | `website` (o `product` en detalle) |

## 3. Open Graph y Twitter Cards

Toda pagina compartible emite el set minimo: `og:title`, `og:description`,
`og:image` (1200x630, jpg/webp via CDN), `og:url`, `og:type`,
`og:site_name="Listing"`, `og:locale`. Twitter: `twitter:card="summary_large_image"`,
`twitter:title`, `twitter:description`, `twitter:image`. **Importante:** como
los bots sociales NO ejecutan JS, estos tags solo funcionan al compartir si hay
prerender (SEO-R23); sin el, las previews quedaran genericas (SEO-R17).

## 4. JSON-LD schema.org

Cada pagina inyecta JSON-LD via `react-helmet-async` (campo `SeoMetadata.jsonld`,
servido por el endpoint de metadata). Tipos por pagina:

| Pagina | Tipos schema.org |
|---|---|
| Detalle propiedad | `RealEstateListing` + anidado `Product` con `Offer` (precio) + `BreadcrumbList` |
| Localidad / tipo / operacion (listado) | `CollectionPage` + `BreadcrumbList` (+ `ItemList` de resultados) |
| Home | `WebSite` (+ `SearchAction` sitelinks searchbox) + `Organization` |

Ejemplo (detalle de propiedad):

```json
{
  "@context": "https://schema.org",
  "@type": "RealEstateListing",
  "name": "Apartamento en Chapinero",
  "url": "https://listing.example/p/venta-apartamento-chapinero-a1b2c3",
  "datePosted": "2026-06-01T00:00:00Z",
  "image": ["https://cdn.example/.../main.webp"],
  "address": {
    "@type": "PostalAddress",
    "addressCountry": "CO", "addressRegion": "Bogota D.C.",
    "addressLocality": "Chapinero"
  },
  "geo": {"@type": "GeoCoordinates", "latitude": 4.65, "longitude": -74.06},
  "numberOfRooms": 3,
  "floorSize": {"@type": "QuantitativeValue", "value": 85, "unitCode": "MTK"},
  "offers": {
    "@type": "Offer",
    "price": "3500000", "priceCurrency": "COP",
    "availability": "https://schema.org/InStock",
    "businessFunction": "http://purl.org/goodrelations/v1#Sell"
  }
}
```

> Nota dinero: `price_amount` es **BIGINT en minor units (centavos)**. El JSON-LD
> y los meta DEBEN convertir a unidades mayores con 2 decimales segun `currency`
> (ISO 4217). NUNCA exponer el valor en centavos como precio (SEO-R6).
> La `address` respeta `Property.address_is_public`: si es `false`, se omite
> `streetAddress` y solo se publica hasta el nivel de localidad (privacidad).
> `availability` mapea: `PUBLISHED`->`InStock`, `SOLD`->`SoldOut`,
> `RENTED`->`OutOfStock`.

`BreadcrumbList` refleja la jerarquia: Home > Operacion > Tipo > Localidad >
Propiedad, alineado con `Location.parent_id`.

## 5. sitemap.xml dinamico (backend FastAPI)

`GET /sitemap.xml` devuelve un **sitemap index** que apunta a sitemaps shardeados
(maximo 50.000 URLs / 50 MB por archivo). Shards: `sitemap-properties-{n}.xml`,
`sitemap-locations.xml`, `sitemap-types.xml`, `sitemap-operations.xml`.

- Solo se incluyen URLs **indexables** (propiedades `PUBLISHED`; `Location`,
  `PropertyType` con `is_active=true`). Excluye `DRAFT/PENDING/PAUSED/REJECTED/
  SOLD/RENTED/DELETED`.
- Cada `<url>` lleva `<loc>` (absoluta, canonical), `<lastmod>` (`updated_at` o
  `published_at` UTC), y opcional `<changefreq>`/`<priority>`.
- Generacion bajo demanda con cache (Redis) e invalidacion en transiciones de
  ciclo de vida (publish/unpublish/sold/rented/delete). Ver SEO-R7.

## 6. robots.txt dinamico (backend FastAPI)

`GET /robots.txt` (texto plano) emite:

```
User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin
Disallow: /panel
Disallow: /*?sort=
Disallow: /*?page=
Disallow: /*?q=
Sitemap: https://listing.example/sitemap.xml
```

`Disallow: /api/` evita rastreo del API (incluye endpoints autenticados). Las
rutas de panel/admin (no publicas) se bloquean. Query params de orden/paginacion/
busqueda se desincentivan via robots y se refuerzan con `noindex` (SEO-R8,
SEO-R15). En entornos no productivos (staging) el robots sirve `Disallow: /`
total (SEO-R16).

## 7. Canonicals

- Toda pagina indexable emite un `<link rel="canonical">` **absoluto**.
- Detalle: autoreferente a `/p/{property_slug}` actual.
- Facetas no canonicas (orden/paginacion/filtros multi-valor): canonical apunta
  a la faceta canonica (SEO-R14).
- Paginacion: cada pagina es autocanonica con `?page=n` y `noindex` en page>1
  para listados profundos; alternativamente canonical a la pagina 1 si el
  contenido es equivalente (decidir en SEO-R15 / Open Questions).

## 8. Redirects 301 al cambiar el slug

Al editar un campo que regenera el slug (`title`, `operation_type`,
`property_kind`), el backend:
1. Conserva el slug anterior en `SeoMetadata.redirect_from[]` (array de slugs
   viejos, FIFO con tope configurable).
2. `GET /api/v1/properties/{old_slug}` y `GET /api/v1/seo/metadata?slug={old_slug}`
   devuelven **301** con `Location` al slug nuevo (canonical).
3. La cadena de redirects se colapsa a un solo salto (old -> actual), nunca
   encadenada, para no perder PageRank. Ver SEO-R13.

## 9. Estados no publicados (noindex / 301 / 410)

Politica unica y exhaustiva por `PublicationStatus`. **Solo `PUBLISHED` es
visible publicamente (200, indexable).**

| Estado | HTTP detalle | robots | En sitemap | Politica |
|---|---|---|---|---|
| `PUBLISHED` | 200 | `index,follow` | Si | Indexable |
| `SOLD` | 301 o 410 | — | No | 301 a faceta de localidad/operacion si hay sustituto; si no, **410 Gone** (SEO-R21) |
| `RENTED` | 301 o 410 | — | No | Igual que SOLD (SEO-R21) |
| `PAUSED` | 404 | — | No | No publico (SEO-R22) |
| `REJECTED` | 404 | — | No | No publico |
| `DRAFT` | 404 | — | No | No publico |
| `PENDING` | 404 | — | No | No publico |
| `DELETED` (soft) | 410 | — | No | **410 Gone** permanente (SEO-R21) |

Criterio 301 vs 410 para `SOLD/RENTED`: preferir **301** hacia un recurso
equivalente vivo (misma localidad+operacion+tipo) para preservar valor SEO y UX;
usar **410** cuando no exista sustituto razonable. La eleccion concreta de la
heuristica es un Open Question.

## Reglas (SEO-R#)

| ID | Regla |
|---|---|
| SEO-R1 | El frontend CSR/SPA se reconoce como debil para SEO; toda indexabilidad critica depende de artefactos servidos por backend (sitemap/robots/metadata) y/o prerender. |
| SEO-R2 | Lecturas SEO (`/sitemap.xml`, `/robots.txt`, `/api/v1/seo/metadata`) son publicas, sin auth. |
| SEO-R3 | Los meta/OG/JSON-LD del cliente se obtienen SIEMPRE de `GET /api/v1/seo/metadata?slug=...`; no se hardcodean en el bundle. |
| SEO-R4 | El cliente usa `react-helmet-async` para inyectar `<title>`, meta description, robots, canonical, Open Graph, Twitter Card y JSON-LD por ruta. |
| SEO-R5 | Cada propiedad tiene `slug` unico inmutable-por-defecto con patron `{operation}-{kind}-{title-kebab}-{shortid}` y regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`. |
| SEO-R6 | Precios en meta/JSON-LD se convierten de `price_amount` (minor units) a unidades mayores con `currency` ISO 4217; nunca se exponen centavos crudos. |
| SEO-R7 | `GET /sitemap.xml` es un sitemap index dinamico desde DB; incluye SOLO recursos indexables (`PUBLISHED`, `is_active`), shardea a <=50k URLs/50MB, cachea en Redis e invalida en transiciones de ciclo de vida. |
| SEO-R8 | `GET /robots.txt` es dinamico, declara la URL del sitemap, bloquea `/api/`, panel/admin y query params de orden/paginacion/busqueda. |
| SEO-R9 | Existen paginas indexables por localidad (`Location.slug`), tipo de inmueble (`PropertyType.slug`) y operacion (`OperationType` value), con sus combinaciones canonicas. |
| SEO-R10 | Cada listado faceta canonica emite `index,follow` + `CollectionPage`/`ItemList` + `BreadcrumbList`. |
| SEO-R11 | El detalle de propiedad emite JSON-LD `RealEstateListing` + `Product`/`Offer` + `BreadcrumbList`. |
| SEO-R12 | Toda pagina indexable emite `<link rel="canonical">` absoluto; el detalle es autocanonico al slug vigente. |
| SEO-R13 | Al cambiar el slug, el viejo se guarda en `SeoMetadata.redirect_from[]` y el backend responde 301 (un solo salto) al slug nuevo. |
| SEO-R14 | Facetas no canonicas (orden, filtros multi-valor) llevan `noindex,follow` y canonical a la faceta canonica. |
| SEO-R15 | Query params `?sort=`, `?q=` => `noindex`; `?page=` => autocanonico con politica de paginacion (noindex en page>1 o canonical a page 1, ver Open Questions). |
| SEO-R16 | En entornos no productivos (staging/preview) `robots.txt` sirve `Disallow: /` total y todas las paginas emiten `noindex`. |
| SEO-R17 | Open Graph/Twitter solo garantizan preview correcta al compartir si hay prerender; sin el, los bots sociales reciben tags genericos. |
| SEO-R18 | `og:image` usa la imagen MAIN (`PropertyImage` role=MAIN) via CDN en 1200x630; fallback a imagen institucional si no hay MAIN. |
| SEO-R19 | La `address` en meta/JSON-LD respeta `Property.address_is_public`; si es `false`, se omite `streetAddress` y se publica solo hasta localidad. |
| SEO-R20 | Solo `PUBLISHED` retorna 200 indexable en el detalle publico. |
| SEO-R21 | `SOLD`/`RENTED` => 301 a recurso equivalente vivo o 410 si no hay sustituto; `DELETED` (soft) => 410 permanente. |
| SEO-R22 | `DRAFT`/`PENDING`/`PAUSED`/`REJECTED` => 404 (no publicos). |
| SEO-R23 | **(Recomendacion fuerte)** Implementar una capa de prerender para bots por User-Agent (Prerender.io / Rendertron / snapshot estatico) en el edge/proxy, o migrar a SSR a futuro; registrado como mejora prioritaria. |
| SEO-R24 | `lastmod` del sitemap y `dateModified` del JSON-LD usan timestamps UTC (`updated_at`/`published_at`); cambios de contenido material refrescan ambos. |

## Mejoras futuras (roadmap SEO)

- **Prerender / SSR (alta prioridad).** Edge prerender por User-Agent como paso 1
  (bajo costo, resuelve bots sociales y mejora crawl de Bing). Migracion a SSR
  (Next.js u SSR sobre la API FastAPI) como paso 2 a mediano plazo: elimina la
  dependencia de prerender y mejora Core Web Vitals (LCP).
- **hreflang** si se internacionaliza el catalogo (multi-pais/idioma).
- **AMP / web stories**: descartado por defecto; reevaluar segun trafico.
- **IndexNow / Google Indexing API** para notificar altas/cambios de propiedades.

## Open Questions

- Politica final 301-vs-410 para `SOLD`/`RENTED`: heuristica exacta de "recurso
  equivalente vivo" (misma localidad+operacion+tipo? umbral de resultados?).
- Paginacion de listados: `noindex` en `page>1` vs canonical a `page=1` vs
  `rel=prev/next` (deprecado por Google). Decidir politica unica.
- Prerender (SEO-R23): seleccion de proveedor/tecnologia (Prerender.io gestionado
  vs Rendertron self-hosted vs snapshot en build) y timeline de migracion a SSR.
- Ventana de retencion de `redirect_from[]` (cuantos slugs viejos se conservan y
  por cuanto tiempo antes de devolver 410).
- `og:locale` / multi-idioma: alcance de internacionalizacion y necesidad de
  `hreflang` desde el inicio.
- Direccion exacta: confirmar que con `address_is_public=false` el JSON-LD nunca
  exponga `streetAddress` ni el `geo` con precision de calle (ofuscar a centroide
  de localidad?).
