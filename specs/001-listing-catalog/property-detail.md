# Página de Detalle de Propiedad — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #9.

## Resumen

Define la estructura, datos, comportamiento por estado, eventos de métrica, CTAs y SEO de la página pública de detalle de una `Property`. Es una página renderizada en cliente (React 18 CSR) servida sobre el endpoint público `GET /api/v1/properties/{slug}`. Solo propiedades en estado `PUBLISHED` retornan HTTP 200 y se renderizan completas; el resto sigue la política de visibilidad (404/301/410). La página es mobile-first, prioriza la galería y el bloque de precio en el primer scroll, expone CTAs de contacto (formulario, WhatsApp, llamada, agendar visita) y dispara eventos `PropertyView` para métricas de engagement.

Audiencia principal: `VISITOR` (no autenticado) y `REGISTERED_USER`. Acciones que requieren auth (favorito) se degradan con prompt de login. La privacidad de la dirección depende de `address_is_public`. No se exponen datos sensibles del owner más allá de nombre, foto y canales de contacto habilitados.

Documentos relacionados: galería/media en `media-pipeline.md` (MEDIA-R#), búsqueda y "propiedades similares" en `search-filters.md` (SEARCH-R#), leads y formulario en `leads.md` (LEAD-R#), SEO y políticas 301/410 en `seo.md` (SEO-R#), métricas en `metrics.md`.

## Fuente de datos (payload de detalle)

El detalle hidrata desde `GET /api/v1/properties/{slug}` con la `Property` y sus relaciones expandidas. Campos consumidos por la página (subconjunto público):

| Bloque | Campos `Property` / relación | Notas de render |
|---|---|---|
| Galería | `images[]` (PropertyImage: `cdn_url`, `thumb_url`, `role`, `media_kind`, `position`, `alt_text`, `width`, `height`), `main_image_id` | Imagen `MAIN` primero; resto por `position`. Lazy load thumbnails. |
| Precio | `price_amount` (BIGINT minor units), `currency` (CHAR(3)), `hoa_fees_amount` (nullable) | Formatear minor->mayor en cliente. NUNCA float. Expensas solo si `hoa_fees_amount != null`. |
| Identidad | `title`, `operation_type` (OperationType), `property_kind` (PropertyKind), `condition` (PropertyCondition), `slug` | Badge de operación (Venta/Renta/Temporal). |
| Ubicación | `country`, `state_province`, `city`, `neighborhood`, `locality` (via `locality_id`->Location), `location_point` (geography POINT 4326), `address`, `address_is_public` | Dirección textual solo si `address_is_public=true`. Mapa siempre por `location_point`. |
| Características | `area_total` (numeric), `area_built` (nullable), `bedrooms`, `bathrooms`, `parking_spots`, `year_built` (nullable) | Ocultar fila si valor es null/0 según regla. |
| Amenities | `amenities[]` (via PropertyAmenity: `code`, `name`, `category`, `icon`, `value`) | Agrupar por `category`. |
| Agente/Owner | `owner` (User: `full_name`, `avatar_url`, `phone`, `whatsapp`) | Solo canales de contacto, sin `email` directo en UI. |
| Disponibilidad | `status` (PublicationStatus), `available_from` (date nullable), `published_at` | `available_from` solo en RENT/TEMPORARY. |
| Métricas (opcional) | `views_count` | Mostrar "X visitas" es opcional (UX-R, no PII). |
| CTA | `primary_cta` | CTA destacado configurable por propiedad. |
| SEO | `seo` (SeoMetadata 1:1: `meta_title`, `meta_description`, `og_*`, `canonical_url`, `jsonld`, `robots`) | Ver seo.md. |

## Estructura de la página (secciones, orden mobile-first)

Orden vertical en mobile (de arriba hacia abajo). En desktop se reorganiza a layout de dos columnas (contenido + sidebar de contacto sticky).

| # | Sección | Contenido | Datos | Lazy |
|---|---|---|---|---|
| 1 | Galería | Foto principal grande + tira de thumbnails; visor full-screen con swipe; soporta `media_kind` VIDEO/FLOOR_PLAN/VIRTUAL_TOUR | `images[]`, `main_image_id` | thumbnails y media no-MAIN |
| 2 | Cabecera | `title`, badge operación, badge `condition`, ubicación corta (ciudad · localidad), badge de estado si no disponible | `title`, `operation_type`, `condition`, `city`, `locality` | no |
| 3 | Precio | `price_amount`+`currency` formateado; expensas (`hoa_fees_amount`) si aplica; etiqueta operación | `price_amount`, `currency`, `hoa_fees_amount` | no |
| 4 | CTAs primarios | Contacto, WhatsApp, Llamar, Agendar visita (según canales disponibles) | `owner.phone`, `owner.whatsapp`, `primary_cta` | no |
| 5 | Características | Grid de iconos: área total/construida, hab, baños, parqueaderos, antigüedad, condición | `area_*`, `bedrooms`, `bathrooms`, `parking_spots`, `year_built`, `condition` | no |
| 6 | Descripción | Texto largo (`description`), con "ver más" colapsable | `description` | no |
| 7 | Amenities | Lista agrupada por `category` con iconos | `amenities[]` | no |
| 8 | Ubicación + Mapa | Ciudad/localidad/barrio; dirección si `address_is_public`; mapa interactivo por coordenadas | `location_point`, `city`, `locality`, `neighborhood`, `address`, `address_is_public` | mapa (cargar al entrar en viewport) |
| 9 | Agente/Owner | Foto, nombre, canales de contacto, formulario embebido o link a sección de contacto | `owner.full_name`, `owner.avatar_url`, `owner.phone`, `owner.whatsapp` | no |
| 10 | Formulario de contacto | Campos mínimos + consentimiento + honeypot (ver leads.md) | crea `Lead` | no |
| 11 | Acciones secundarias | Favorito (auth), Compartir (OG), Reportar publicación | `favorite`, share, report | no |
| 12 | Propiedades similares | Carrusel: mismo `property_kind` y/o `locality_id`, rango de precio cercano | `GET /api/v1/properties` (ver search-filters.md) | cargar al entrar en viewport |
| 13 | Footer SEO | Breadcrumbs, JSON-LD, enlaces internos | `seo.jsonld`, breadcrumbs | no |

## Galería (detalle)

- Imagen principal: el `PropertyImage` con `role=MAIN` (constraint: una sola MAIN por propiedad). Si no hay MAIN, usar la de menor `position`. Si no hay imágenes, placeholder neutro.
- Thumbnails: ordenados por `position`; usan `thumb_url`. La principal usa `cdn_url`.
- Lazy load: solo la imagen principal y el primer fold de thumbnails se cargan eager; el resto con `loading="lazy"` e `IntersectionObserver`. Reservar `width`/`height` para evitar CLS.
- Media no-imagen: `media_kind` VIDEO / FLOOR_PLAN / VIRTUAL_TOUR se muestran como entradas especiales en la tira con icono; abren en el visor.
- Visor full-screen: swipe en mobile, teclas/flechas en desktop, `alt_text` como caption accesible.
- Detalle exhaustivo de pipeline de media en `media-pipeline.md` (MEDIA-R#).

## Precio y moneda

- `price_amount` está en minor units (centavos). El cliente convierte a unidad mayor (división por exponente de la moneda) y formatea según `currency` (ISO 4217) y locale del usuario. NUNCA usar float para cálculos: la conversión visual es solo presentación.
- Expensas/HOA: si `hoa_fees_amount != null`, mostrar línea secundaria "Expensas: <monto> <currency> / mes" formateada igual. Si es null, ocultar.
- Etiqueta de operación junto al precio: SALE -> "Precio de venta"; RENT -> "Renta mensual"; TEMPORARY -> "Tarifa".

## Ubicación y mapa

- Texto: jerarquía `city` · `locality` (Location) · `neighborhood`. País/estado en breadcrumbs/SEO.
- Dirección: `address` se muestra SOLO si `address_is_public=true`. Si es false, mostrar ubicación aproximada (localidad/barrio) y mapa con marcador en `location_point` sin pin de dirección exacta.
- Mapa interactivo: render por `location_point` (geography POINT, SRID 4326 -> lat/lng). Carga diferida (al entrar en viewport) para no penalizar LCP. Marcador fijo; si `address_is_public=false`, usar área/círculo aproximado en vez de pin exacto.

## Características y amenities

- Características: grid de tarjetas con icono + valor: `area_total` (m2), `area_built` (m2, si no null), `bedrooms`, `bathrooms`, `parking_spots`, `year_built` -> antigüedad (año actual - `year_built`, si no null), `condition` (etiqueta legible de PropertyCondition).
- Reglas de visibilidad: ocultar tarjeta si el valor es `null`; para enteros, mostrar `0` solo cuando sea semánticamente válido (p.ej. `parking_spots=0` se muestra como "Sin parqueadero"; `bedrooms=0` se muestra como "Monoambiente/Estudio").
- Amenities: lista derivada de PropertyAmenity (M2M) agrupada por `Amenity.category`, con `icon` y `name`; si `value` no es null, anexarlo (p.ej. "Piscina: climatizada").

## Info del agente / propietario

- Mostrar `owner.full_name`, `owner.avatar_url` (o avatar placeholder). Canales de contacto habilitados: WhatsApp si `owner.whatsapp` presente, Llamar si `owner.phone` presente.
- NO exponer `owner.email` directamente en la UI pública; el correo del owner se usa server-side para notificar leads.
- En desktop, este bloque + CTAs viven en un sidebar sticky.

## CTAs y deep links

| CTA | Disponibilidad | Acción | Deep link / destino | Evento métrica |
|---|---|---|---|---|
| Contacto (formulario) | Siempre | Abre/enfoca formulario de contacto -> crea `Lead` (`channel=FORM`) | sección #10 | `CTA_CLICK` al abrir; `VIEW`/lead al enviar |
| WhatsApp | Si `owner.whatsapp` presente | Deep link wa.me con mensaje prellenado | `https://wa.me/<whatsapp_e164>?text=<msg>` | `WHATSAPP_CLICK` |
| Llamar | Si `owner.phone` presente | Marcado telefónico | `tel:<phone_e164>` | `CALL_CLICK` |
| Agendar visita | Siempre | Formulario/flujo de visita -> `Lead` (`channel=VISIT`) | modal de visita | `VISIT_REQUEST` |
| `primary_cta` | Si definido | Resalta el CTA configurado por la propiedad | según valor | evento del CTA resaltado |

Mensaje WhatsApp prellenado (template, URL-encoded): `Hola, me interesa la propiedad "{title}" ({url}). ¿Sigue disponible?`. El número `whatsapp` debe normalizarse a E.164 sin `+` para `wa.me`. `tel:` usa E.164 con `+`.

## Formulario de contacto

Crea un `Lead` vía endpoint público de leads (ver leads.md). Resumen de la pieza UI:

| Campo | Tipo | Requerido | Mapea a `Lead` |
|---|---|---|---|
| `name` | texto | sí | `name` |
| `email` | email | sí | `email` |
| `phone` | tel | sí | `phone` |
| `message` | textarea | sí | `message` |
| `consent_given` | checkbox | sí | `consent_given` + `consent_text` |
| `_hp` (honeypot) | hidden | debe ir vacío | descartar si lleno |

- Anti-spam: honeypot oculto + (opcional) rate limit por IP (Redis) gestionado server-side. El `channel` se fija según el CTA de origen (`FORM` para formulario, `VISIT` para agendar visita). Server captura `source_ip`, `user_agent`, `utm` y la `property_id`/`owner_id`.
- Consentimiento obligatorio: sin `consent_given=true` el submit se bloquea (client + server). Detalle de validaciones y estados del lead en leads.md (LEAD-R#).

## Acciones secundarias

- Favorito: requiere auth (`REGISTERED_USER`+, permiso `favorite:manage_own`). Para `VISITOR` el click abre prompt de login y, tras autenticar, persiste el favorito (`POST /api/v1/favorites`). Toggle visual optimista. Evento `FAVORITE`.
- Compartir: usa Web Share API en mobile; fallback a copiar `canonical_url` y botones de red social. Comparte la `canonical_url` (SeoMetadata) y metadatos OG. Evento `SHARE`.
- Reportar publicación: abre modal con motivo (contenido falso, vendida/alquilada, datos incorrectos, spam, otro). Crea un reporte de moderación (cola admin; ver api-contracts.md). No requiere auth, pero aplica honeypot + rate limit.

## Comportamiento por estado de publicación

La página solo se renderiza completa para `PUBLISHED`. La capa de API y el render aplican esta política (alineada con property-lifecycle.md y seo.md):

| `status` | HTTP | Render de la página |
|---|---|---|
| `PUBLISHED` | 200 | Página completa, todos los CTAs activos |
| `SOLD` | 200 (ó 301/410 según seo.md) | Vista de solo lectura con badge "Vendida — no disponible"; CTAs de contacto deshabilitados; mostrar similares |
| `RENTED` | 200 (ó 301/410 según seo.md) | Vista de solo lectura con badge "Alquilada — no disponible"; CTAs deshabilitados; mostrar similares |
| `PAUSED` | 404 | No visible públicamente |
| `REJECTED` | 404 | No visible públicamente |
| `DRAFT` | 404 | No visible públicamente |
| `DELETED` | 404 (ó 410 según seo.md) | No visible públicamente |

- Badge "no disponible" (SOLD/RENTED): banner prominente sobre la galería; oculta WhatsApp/Llamar/Visita/Formulario; mantiene Compartir y Propiedades similares para retener al usuario.
- La política exacta 200 vs 301 (a similar/listado) vs 410 (gone) para SOLD/RENTED/DELETED es responsabilidad de seo.md (SEO-R#); esta página respeta la decisión de esa capa.

## Propiedades similares

- Criterio: mismo `property_kind` y/o misma `locality_id`, dentro de un rango de precio cercano y misma `operation_type`; excluir la propiedad actual y solo `PUBLISHED`.
- Origen de datos y algoritmo de ranking exacto en search-filters.md (SEARCH-R#). La página consume el endpoint de listado público con filtros y muestra un carrusel (cards con imagen MAIN, precio, ubicación corta).
- Carga diferida al entrar en viewport para no afectar LCP del fold principal.

## Eventos de métrica (PropertyView)

Cada interacción relevante crea un `PropertyView` (almacén de eventos de engagement). Contadores denormalizados (`views_count`, `clicks_count`, `leads_count`) viven en `Property`. Campos del evento: `property_id`, `event_type` (MetricEventType), `source` (ViewSource), `session_hash`, `ip_hash`, `referrer`, `created_at`.

| Interacción en la página | `event_type` | Disparo |
|---|---|---|
| Carga/visualización de la página | `VIEW` | Una vez por vista (dedupe por `session_hash`); incrementa `views_count` |
| Click en CTA de contacto/formulario abierto | `CTA_CLICK` | Al abrir formulario o click en `primary_cta`; incrementa `clicks_count` |
| Click en WhatsApp | `WHATSAPP_CLICK` | Antes de abrir el deep link wa.me |
| Click en Llamar | `CALL_CLICK` | Antes de invocar `tel:` |
| Envío de "Agendar visita" | `VISIT_REQUEST` | Al enviar el flujo de visita (también crea `Lead`) |
| Click en Compartir | `SHARE` | Al confirmar compartir / copiar enlace |
| Marcar favorito | `FAVORITE` | Al togglear favorito a activo (auth) |

- `source` (ViewSource) se deriva del referrer/origen de navegación: ORGANIC, SEARCH, FEATURED, DIRECT, SHARE. `FEATURED` cuando se llega desde un slot de destacados; `SEARCH` desde resultados; `SHARE` desde enlace compartido con parámetro; `DIRECT` sin referrer; ORGANIC desde buscadores.
- Privacidad: `ip_hash` y `session_hash` son hashes, no PII en claro (ver NFR-040 / seguridad). Detalle de pipeline y dedupe en metrics.md.

## SEO de la página

Resumen; la fuente de verdad es seo.md (SEO-R#). La página hidrata `SeoMetadata` (1:1 con Property):

- `meta_title`, `meta_description`, `canonical_url` (siempre canónico al slug actual).
- Open Graph / Twitter Card: `og_title`, `og_description`, `og_image_url` (usar imagen MAIN si falta), para previews al compartir.
- JSON-LD: `jsonld` con esquema tipo `RealEstateListing`/`Product`+`Offer` (precio, moneda, disponibilidad, ubicación, imágenes).
- `robots` (default "index,follow"); SOLD/RENTED/DELETED ajustan robots y/o aplican 301/410 según seo.md. `redirect_from` mantiene slugs viejos -> 301 al canónico.
- Breadcrumbs y enlaces internos (país > estado > ciudad > localidad > propiedad) para crawlability.
- Como es CSR (React/Vite), el SEO requiere SSR/prerender o inyección de metadatos en el HTML inicial para crawlers; la estrategia técnica vive en seo.md (SEO-R#).

## Accesibilidad y rendimiento

- Mobile-first; objetivos de Core Web Vitals en NFR (performance.md): LCP rápido (galería principal eager + dimensiones reservadas), CLS ~0 (reservar espacio de imágenes/mapa), lazy load de mapa, similares y media secundaria.
- Accesibilidad: `alt_text` en imágenes, labels en formulario, foco gestionado en visor/modales, contraste suficiente, navegación por teclado en galería.

## Reglas (DETAIL-R#)

| ID | Regla |
|---|---|
| DETAIL-R1 | La página de detalle se hidrata desde `GET /api/v1/properties/{slug}` (lectura pública, sin auth). |
| DETAIL-R2 | Solo `status=PUBLISHED` retorna 200 con render completo y CTAs activos. |
| DETAIL-R3 | `SOLD`/`RENTED` se muestran en modo solo lectura con badge "no disponible" y CTAs de contacto deshabilitados; la elección 200/301/410 la define seo.md. |
| DETAIL-R4 | `PAUSED`/`REJECTED`/`DRAFT` -> 404; `DELETED` -> 404 o 410 según seo.md. |
| DETAIL-R5 | La galería usa el `PropertyImage` con `role=MAIN` como principal (única por propiedad); el resto por `position`; thumbnails con lazy load. |
| DETAIL-R6 | `price_amount` se interpreta como minor units y se formatea con `currency`; nunca se usa float. Expensas se muestran solo si `hoa_fees_amount != null`. |
| DETAIL-R7 | `address` se muestra solo si `address_is_public=true`; en caso contrario, ubicación aproximada y mapa sin pin exacto. |
| DETAIL-R8 | El mapa interactivo se renderiza por `location_point` (POINT 4326) con carga diferida. |
| DETAIL-R9 | Tarjetas de características con valor `null` se ocultan; enteros con `0` se rotulan semánticamente (p.ej. "Sin parqueadero"). |
| DETAIL-R10 | El bloque de contacto expone WhatsApp/Llamar solo si existen `owner.whatsapp`/`owner.phone`; nunca se expone `owner.email` en UI pública. |
| DETAIL-R11 | WhatsApp usa `https://wa.me/<e164>?text=<msg-encoded>` con mensaje prellenado; Llamar usa `tel:<e164>`. |
| DETAIL-R12 | El formulario de contacto exige `name`, `email`, `phone`, `message` y `consent_given=true`, incluye honeypot, y crea un `Lead` (detalle en leads.md). |
| DETAIL-R13 | El botón Favorito requiere auth (`favorite:manage_own`); para `VISITOR` abre login y persiste tras autenticar. |
| DETAIL-R14 | Compartir usa la `canonical_url` y metadatos OG; Reportar abre flujo de moderación con honeypot/rate limit. |
| DETAIL-R15 | Propiedades similares filtran por `property_kind`/`locality_id`/rango de precio/`operation_type`, excluyen la actual y solo `PUBLISHED` (algoritmo en search-filters.md). |
| DETAIL-R16 | Cada vista dispara `PropertyView` `event_type=VIEW` (dedupe por `session_hash`); las interacciones disparan `CTA_CLICK`/`WHATSAPP_CLICK`/`CALL_CLICK`/`VISIT_REQUEST`/`SHARE`/`FAVORITE`. |
| DETAIL-R17 | `source` del evento se deriva del origen de navegación (ORGANIC/SEARCH/FEATURED/DIRECT/SHARE). |
| DETAIL-R18 | El SEO (meta, OG, JSON-LD, canonical, robots, redirects) se sirve desde `SeoMetadata`; la estrategia CSR/SSR/prerender se define en seo.md. |
| DETAIL-R19 | La página es mobile-first; galería principal eager con dimensiones reservadas (LCP/CLS); mapa, similares y media secundaria con lazy load. |

## Open Questions

- Política exacta para SOLD/RENTED: ¿200 con badge, 301 a similar/listado, o 410? Decisión final en seo.md (esta página la respeta).
- ¿`views_count` se muestra públicamente en el detalle o es solo dato interno de panel? (definir en UX/metrics).
- Edición material de una propiedad `PUBLISHED`: si requiere re-revisión, ¿afecta visibilidad de la página durante la re-revisión? (depende de property-lifecycle.md).
- Detalle del flujo "Agendar visita": ¿campos extra (fecha/hora preferida) sobre el formulario base de lead? (coordinar con leads.md).
