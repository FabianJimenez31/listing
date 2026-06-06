# Métricas y Analítica — Listing

> Detalle de specs/001-listing-catalog/. Índice en spec.md. DoD: #19.

## Resumen

Este documento define **qué métricas mide Listing, cómo se capturan, dónde se almacenan y cómo se exponen** en dashboards. El modelo de captura es de **dos capas**:

1. **Capa de eventos (fuente de verdad)**: cada interacción relevante con una propiedad se escribe como una fila inmutable en `property_views` (entidad `PropertyView`), tipada por `MetricEventType` y atribuida por `ViewSource`. Es append-only y nunca se actualiza ni borra.
2. **Capa de contadores denormalizados (lectura rápida)**: agregados precomputados que viven en columnas de las entidades de negocio para servir listados y badges sin escanear eventos:
   - `Property.views_count`, `Property.clicks_count`, `Property.leads_count`.
   - `Banner.impressions_count`, `Banner.clicks_count`.
   - `FeaturedProperty.impressions_count`, `FeaturedProperty.clicks_count`.

Regla rectora: **los contadores son cache; los eventos son verdad**. Si divergen, los eventos (y los leads reales en `leads`) ganan; un job de reconciliación recalcula contadores desde eventos. Los `Lead` se cuentan desde la tabla `leads` (verdad transaccional), no desde eventos `VISIT_REQUEST`.

Privacidad transversal: **nunca se persiste IP ni identificador de sesión en claro**. Se almacenan `ip_hash` y `session_hash` (ver `## Reglas` SEC) — alineado con NFR-040 (privacidad/cumplimiento) y la política de `security.md`.

## Catálogo de métricas mínimas

| # | Métrica | Unidad | Fuente primaria | Fórmula / definición | Granularidad |
|---|---------|--------|-----------------|----------------------|--------------|
| M1 | Vistas de propiedad | conteo | `PropertyView` event_type=`VIEW` | COUNT(events VIEW) por property | property, día, localidad |
| M2 | Clics en CTA | conteo | `PropertyView` event_type=`CTA_CLICK` | COUNT(events CTA_CLICK) | property, día, primary_cta |
| M3 | Leads generados | conteo | `Lead` (tabla `leads`) | COUNT(leads) por property/agente/periodo | property, owner_id, día, channel |
| M4 | Clics en WhatsApp | conteo | `PropertyView` event_type=`WHATSAPP_CLICK` | COUNT(events WHATSAPP_CLICK) | property, día |
| M5 | Clics en llamada | conteo | `PropertyView` event_type=`CALL_CLICK` | COUNT(events CALL_CLICK) | property, día |
| M6 | Impresiones de banners | conteo | `Banner.impressions_count` ← evento impresión banner | COUNT(impresiones) por banner | banner, position, día |
| M7 | Clics en banners | conteo | `Banner.clicks_count` ← evento clic banner | COUNT(clics) por banner | banner, position, día |
| M8 | CTR de banners | ratio % | M7 / M6 | `clicks / impressions` (0 si impressions=0) | banner, position, día |
| M9 | CTR de destacados | ratio % | `FeaturedProperty.clicks_count / impressions_count` | `clicks / impressions` (0 si impressions=0) | featured, scope, día |
| M10 | Propiedades más vistas | ranking | M1 agregada | TOP-N por SUM(VIEW) en ventana | global, localidad, ventana |
| M11 | Localidades más buscadas | ranking | eventos de búsqueda (search) | TOP-N por COUNT(search) agrupado por `locality_id` | global, ventana (ver SEARCH) |
| M12 | Conversión visita→lead | ratio % | M3 / M1 | `leads / views` por property/periodo | property, owner_id, ventana |
| M13 | Engagement extra | conteo | `PropertyView` `SHARE`, `FAVORITE`, `VISIT_REQUEST` | COUNT por event_type | property, día |

Notas de definición:
- **Vista (VIEW)**: render efectivo de la página de detalle de una propiedad `PUBLISHED`. Solo cuenta el primer VIEW por (property, session_hash) dentro de la **ventana de deduplicación** (ver DEDUP). Reaperturas dentro de la ventana no incrementan M1.
- **Clic en CTA (CTA_CLICK)**: clic sobre el botón de acción principal de la propiedad (`Property.primary_cta`). `WHATSAPP_CLICK` y `CALL_CLICK` son CTAs especializados y se cuentan **aparte** de `CTA_CLICK` (no se suman doble; el frontend emite exactamente un event_type por interacción).
- **Lead**: creación de una fila en `leads` (cualquier `LeadChannel`), independiente de su `LeadStatus` posterior. El `VISIT_REQUEST` es señal de intención de engagement; el lead real es la fila en `leads`.
- **Conversión visita→lead (M12)**: usa M3 (leads reales) sobre M1 (vistas únicas) en la misma ventana. Si M1=0 → conversión=0.

## Modelo de captura

### PropertyView (almacén de eventos de propiedad)

Entidad `PropertyView` (tabla `property_views`). Campos (ver modelo de datos en `data-model.md`):

| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID v4 | PK |
| property_id | UUID → `Property` | FK obligatoria |
| event_type | `MetricEventType` | VIEW, CTA_CLICK, WHATSAPP_CLICK, CALL_CLICK, VISIT_REQUEST, SHARE, FAVORITE |
| source | `ViewSource` | ORGANIC, SEARCH, FEATURED, DIRECT, SHARE |
| session_hash | string | hash de sesión (ver SEC); usado para dedup |
| ip_hash | string | hash de IP (ver SEC); nunca IP en claro |
| referrer | string nullable | dominio/URL de origen normalizada |
| created_at | timestamptz UTC | momento del evento |

Reglas:
- `property_views` es **append-only** (sin UPDATE/DELETE; sin `updated_at`/`deleted_at`). Correcciones se hacen vía reconciliación de contadores, no editando eventos.
- Índices recomendados: `(property_id, event_type, created_at)`, `(event_type, created_at)`, `(created_at)` para particionado/retención por tiempo.
- Retención: eventos crudos se conservan **24 meses**; luego se compactan a agregados diarios (rollups) y se purgan (ver RETENTION). Los contadores denormalizados nunca se purgan.

### Eventos de banner y destacado

Las impresiones/clics de `Banner` y `FeaturedProperty` **no** viven en `property_views` (no son interacciones de detalle de propiedad). Se capturan vía sus endpoints de tracking dedicados e incrementan directamente los contadores denormalizados (`impressions_count`, `clicks_count`). Para análisis histórico fino se recomienda un rollup diario (tabla de agregados `banner_metrics_daily` / `featured_metrics_daily`); el detalle por evento es opcional y queda como Open Question si se requiere CTR por hora.

### Contadores denormalizados

| Entidad | Contador | Incrementado por | Reconciliable desde |
|---------|----------|------------------|---------------------|
| `Property` | `views_count` | evento `VIEW` (post-dedup) | COUNT distinct (property, session_hash) VIEW |
| `Property` | `clicks_count` | eventos `CTA_CLICK`+`WHATSAPP_CLICK`+`CALL_CLICK` | SUM de esos event_type |
| `Property` | `leads_count` | creación de `Lead` | COUNT(`leads` por property) |
| `Banner` | `impressions_count` | impresión de banner | rollup banner |
| `Banner` | `clicks_count` | clic de banner | rollup banner |
| `FeaturedProperty` | `impressions_count` | impresión de destacado | rollup featured |
| `FeaturedProperty` | `clicks_count` | clic de destacado | rollup featured |

- Incremento atómico (`UPDATE ... SET x = x + 1`), idealmente en la misma transacción que el INSERT del evento, o asíncrono vía Redis buffer con flush periódico (ver PERF).
- `Property.clicks_count` agrupa los tres tipos de clic accionable de la propiedad (CTA + WhatsApp + llamada) para el listado; los desgloses (M2/M4/M5) se obtienen de eventos.

## Endpoints de tracking

Base `/api/v1`. Lecturas públicas sin auth; los endpoints de tracking aceptan tráfico anónimo (VISITOR) y autenticado. Rate-limited por IP+sesión (Redis). Respuesta `202 Accepted` con cuerpo vacío o `{"accepted": true}` para minimizar payload; errores con el envelope estándar `{"error":{"code","message","details"}}`.

| Método | Ruta | Auth | Cuerpo | Efecto |
|--------|------|------|--------|--------|
| POST | `/api/v1/track/properties/{property_id}/events` | público (opcional JWT) | `{event_type, source, referrer?}` | INSERT en `property_views` (dedup) + incremento contador |
| POST | `/api/v1/track/banners/{banner_id}/impression` | público | `{position}` | `Banner.impressions_count += 1` |
| POST | `/api/v1/track/banners/{banner_id}/click` | público | `{position}` | `Banner.clicks_count += 1` |
| POST | `/api/v1/track/featured/{featured_id}/impression` | público | `{scope, locality_id?}` | `FeaturedProperty.impressions_count += 1` |
| POST | `/api/v1/track/featured/{featured_id}/click` | público | `{scope}` | `FeaturedProperty.clicks_count += 1` |
| POST | `/api/v1/track/search` | público | `{locality_id?, query?, filters?}` | registra evento de búsqueda para M11 |

Ejemplo de request de evento de propiedad:

```json
POST /api/v1/track/properties/{property_id}/events
{
  "event_type": "whatsapp_click",
  "source": "search",
  "referrer": "google.com"
}
```

Validaciones (ver `validations.md`):
- `event_type` ∈ `MetricEventType`; `source` ∈ `ViewSource`. Valor inválido → `400 VALIDATION_ERROR`.
- `property_id`/`banner_id`/`featured_id` deben existir; propiedad **no `PUBLISHED`** → el evento se **descarta silenciosamente** (`202`) sin incrementar contadores (no se mide engagement de no-públicas).
- `session_hash` e `ip_hash` los deriva el **backend** desde la cookie de sesión y la IP del request; el cliente **nunca** los envía.

## Deduplicación

| Evento | Clave de dedup | Ventana | Efecto duplicado |
|--------|----------------|---------|------------------|
| VIEW | (property_id, session_hash) | 30 min | no incrementa M1/`views_count`; sí puede registrarse como evento crudo pero excluido del conteo único |
| WHATSAPP_CLICK / CALL_CLICK / CTA_CLICK | (property_id, session_hash, event_type) | 5 min | ignorado dentro de ventana |
| Banner/Featured impresión | (entity_id, session_hash, position) | render único por carga de página | una impresión por viewport-visible por carga |

- Implementación: clave Redis `dedup:{event}:{entity}:{session_hash}` con TTL = ventana; primer evento setea la clave y cuenta, repetidos dentro del TTL no cuentan.
- La deduplicación de **leads** es por la lógica anti-spam de leads (ver `leads.md`), no por esta capa.

## Dashboards

### Panel de Agente (métricas propias)

Permiso requerido: `metrics:read_own`. Alcance: solo propiedades donde `owner_id = current_user` y leads asignados (`Lead.owner_id = current_user`).

| Widget | Métricas | Filtros |
|--------|----------|---------|
| Resumen | M1, M2, M3, M12 totales | rango de fechas |
| Por propiedad | M1, M3, M12 por property (tabla ordenable) | estado, localidad |
| Canales de contacto | M4 (WhatsApp), M5 (llamada), M2 (CTA) | rango de fechas |
| Embudo | M1 → clics → M3 (conversión) | property |
| Mis destacados | M9 (CTR destacados propios) | rango de fechas |

### Panel Admin (métricas globales)

Permiso requerido: `metrics:read_global`. Alcance: toda la plataforma.

| Widget | Métricas | Filtros |
|--------|----------|---------|
| KPIs globales | M1, M3, M12 agregados | rango, localidad, operation_type, kind |
| Top propiedades | M10 (más vistas TOP-N) | ventana, localidad |
| Top localidades | M11 (más buscadas TOP-N) | ventana |
| Banners | M6, M7, M8 (CTR) por banner/position | rango, position |
| Destacados | M9 (CTR) por scope | rango, scope |
| Salud de conversión | M12 distribución por localidad/agente | rango |

- Endpoints de lectura: `GET /api/v1/metrics/overview`, `GET /api/v1/metrics/properties/top`, `GET /api/v1/metrics/localities/top`, `GET /api/v1/metrics/banners`, `GET /api/v1/metrics/featured`, `GET /api/v1/metrics/me` (panel agente). Todos con `?from=&to=` (ISO date) y paginación estándar `?page=&page_size=` donde aplique.
- Ventana temporal por defecto: **últimos 30 días**; presets 7d / 30d / 90d / custom. Zona horaria de agregación: **UTC** (los timestamps son timestamptz UTC); el frontend puede reproyectar a zona local para visualización.

## Ventanas temporales y agregación

- **Eventos crudos**: timestamp exacto en UTC.
- **Rollups diarios**: job programado agrega `property_views` y eventos de banner/featured a granularidad de día (bucket por `date_trunc('day', created_at AT TIME ZONE 'UTC')`). Sirve dashboards rápidos y permite purga de crudos.
- **CTR**: siempre `clicks / impressions` en la misma ventana; se presenta como porcentaje con 2 decimales; división por cero → `0.00%` (no `null`, no error).
- **Conversión (M12)**: `leads / vistas_únicas` en la misma ventana; M1=0 → `0.00%`.
- **TOP-N (M10/M11)**: N por defecto = 10, configurable hasta 100 vía `?limit=`.

## Reglas (PERF-R#, SEC-R#, UX-R#, VALID-R#)

### Privacidad y seguridad
- **SEC-R1**: `property_views` almacena **únicamente** `ip_hash` y `session_hash`; está **prohibido** persistir IP o session id en claro en cualquier tabla de métricas. Alineado con NFR-040.
- **SEC-R2**: `ip_hash = HMAC-SHA256(ip, server_secret)` y `session_hash = HMAC-SHA256(session_id, server_secret)` con `server_secret` fuera del repositorio (`.env.local`). HMAC con sal evita reversión por diccionario de IPs.
- **SEC-R3**: Los hashes los computa el backend; ningún campo de hash o IP llega del cliente. Cualquier `ip_hash`/`session_hash` recibido en el body se ignora.
- **SEC-R4**: Datos de métricas se exponen solo bajo `metrics:read_own` (propio) o `metrics:read_global` (global). VISITOR y REGISTERED_USER sin estos permisos no acceden a dashboards (ver `roles-permissions.md`).
- **SEC-R5**: Las acciones de configuración de métricas/retención que realice ADMIN/SUPERADMIN se registran en `audit_logs` con `AuditAction=config_change`.

### Performance y resiliencia
- **PERF-R1**: El tracking **no debe bloquear** la respuesta al usuario: el endpoint responde `202` rápido; el incremento de contador y/o INSERT pueden encolarse (buffer Redis) y aplicarse asíncronamente.
- **PERF-R2**: Rate limit por (`ip_hash`, ruta): por defecto 60 eventos/min por sesión; exceso → `429 RATE_LIMITED` (envelope estándar). Protege contra inflado artificial de métricas.
- **PERF-R3**: Lecturas de dashboard se sirven desde rollups/contadores y se cachean en Redis (TTL 60s para overview, 300s para rankings). Nunca se escanea `property_views` crudo en tiempo de request.
- **PERF-R4**: Contadores denormalizados se incrementan con operación atómica; reconciliación nocturna recalcula desde eventos/`leads` y corrige drift.

### Integridad de medición
- **VALID-R1**: Solo propiedades `PUBLISHED` generan métricas de engagement; eventos sobre otros estados se descartan (no se cuentan).
- **VALID-R2**: Un clic emite **exactamente un** `event_type` (CTA_CLICK | WHATSAPP_CLICK | CALL_CLICK); no se contabiliza doble.
- **VALID-R3**: M3 (leads) se cuenta desde la tabla `leads`, fuente transaccional, no desde eventos `VISIT_REQUEST`.
- **VALID-R4**: VIEW deduplicado por (property_id, session_hash) en ventana de 30 min para M1.
- **VALID-R5**: Tráfico identificado como bot (user_agent en lista de bots, o sin ejecución JS para VIEW) se excluye del conteo.

### UX de dashboards
- **UX-R1**: Toda métrica muestra su **ventana temporal activa** y permite cambiarla (7d/30d/90d/custom).
- **UX-R2**: CTR y conversión se muestran como `0.00%` cuando el denominador es 0, con tooltip explicativo (sin datos suficientes).
- **UX-R3**: Rankings (M10/M11) muestran como mínimo TOP-10 con enlace a ver más.
- **UX-R4**: El panel de agente nunca muestra datos de propiedades ajenas (aislamiento por `owner_id`).

## Objetivos (targets de referencia)

Valores guía para alertas e interpretación, no SLAs contractuales (ajustables por SUPERADMIN sin tocar código, ver DoD #20):

| Métrica | Objetivo de referencia |
|---------|------------------------|
| CTR de banners (M8) | ≥ 0.8% saludable; < 0.3% revisar creatividad/posición |
| CTR de destacados (M9) | ≥ 2.0% saludable |
| Conversión visita→lead (M12) | ≥ 2.5% saludable por propiedad publicada |
| Latencia endpoint de tracking | p95 < 50 ms (responde antes de persistir, PERF-R1) |
| Frescura de dashboard | datos ≤ 5 min de antigüedad (TTL caché + flush buffer) |

## Open Questions

- ¿Se requiere CTR de banners/destacados a granularidad **horaria**? Si sí, hay que persistir eventos individuales de banner/featured (tabla dedicada) en vez de solo contadores. Default propuesto: rollup diario.
- M11 "localidades más buscadas" depende de que `search-filters.md` defina el evento de búsqueda y su `locality_id`; confirmar si se mide por término escrito, por filtro de localidad seleccionado, o ambos.
- Ventana de dedup de VIEW (30 min) y de clics (5 min): confirmar con negocio; pueden requerir ser configurables por SUPERADMIN.
- Retención de eventos crudos (24 meses) y momento de compactación a rollups: validar contra requisitos legales/coste de almacenamiento (NFR-040).
- ¿`favorite:manage_own` (Favorite) ya cuenta como métrica `FAVORITE`, o el evento `FAVORITE` en `property_views` es independiente del registro persistente en `favorites`? Propuesta: `favorites` es verdad de favoritos; el evento `FAVORITE` solo alimenta métricas de engagement.
