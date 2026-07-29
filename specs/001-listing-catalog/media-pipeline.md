# Pipeline de Imagenes y Multimedia — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #7.

## Resumen

Especifica la gestion de imagenes y multimedia de `Property`: subida multiple, foto principal unica (`ImageRole.MAIN`), ordenamiento manual de galeria (`position`), reemplazo y eliminacion, validaciones de archivo (formato/peso/dimensiones/MIME real/maximos), pipeline asincrono de optimizacion (thumbnails multi-tamano, conversion WebP/AVIF, compresion, separacion original vs derivados), almacenamiento seguro en object storage S3-compatible (ACL privada para originales, publica para derivados, nombres aleatorizados) y entrega por CDN (`cdn_url`, `thumb_url`, `srcset`). El soporte de `MediaKind` `VIDEO`/`FLOOR_PLAN`/`VIRTUAL_TOUR` es opcional pero modelado de extremo a extremo.

La entidad `PropertyImage` es el unico registro de cualquier medio de una propiedad (imagen y otros `MediaKind`). El campo denormalizado `Property.main_image_id` apunta al `PropertyImage` con `role=MAIN`. El detalle de endpoints (verbos, payloads, codigos) es referencia normativa de `api-contracts.md`; aqui se fijan las reglas de negocio y de procesamiento.

## Modelo de datos del medio (`PropertyImage`)

Tabla `property_images`. PK `id` UUID v4. Soft delete no aplica (eliminacion fisica del registro + objetos; ver MEDIA-R23).

| Campo | Tipo | Notas |
|---|---|---|
| id | UUID v4 (string) | PK |
| property_id | FK -> Property | indexado; `ON DELETE` cascada logica (ver MEDIA-R24) |
| media_kind | MediaKind | `image`, `video`, `floor_plan`, `virtual_tour` |
| role | ImageRole | `main` \| `gallery`; vive en `property_image.py` |
| original_url | text | objeto original en bucket privado (ACL privada) |
| cdn_url | text | derivado full-size servido por CDN (ACL publica) |
| thumb_url | text | derivado miniatura por CDN (ACL publica) |
| position | int | orden de galeria, 0-based, contiguo por propiedad |
| width | int | px del original (o del recurso embebido) |
| height | int | px del original |
| bytes | bigint | peso del original |
| content_type | CHAR/varchar | MIME real detectado (no la extension) |
| alt_text | text | texto alternativo accesible (SEO/a11y) |
| created_at | timestamptz UTC | |

Derivados (variantes de tamano/formato) NO son filas propias en MVP: se almacenan como objetos con clave derivable del `id` y se exponen via `cdn_url`/`thumb_url` + `srcset` calculado. Si una fase futura requiere variantes consultables, se introduce tabla `property_image_variant` (Open Question OQ-3); no se usa `utils.py`/`media.py` generico.

### Claves y constraints

- `UNIQUE(property_id) WHERE role='main'` (indice parcial): **una sola MAIN por propiedad** (MEDIA-R10).
- `UNIQUE(property_id, position)` para `media_kind='image'`: orden sin colisiones (MEDIA-R12).
- Indice `(property_id, position)` para lectura de galeria ordenada.
- `content_type` restringido por aplicacion al set permitido segun `media_kind` (MEDIA-R1).

## Flujo de subida

Dos modos soportados; **presigned URL es el modo por defecto y recomendado** para imagenes y, obligatorio, para video.

### Modo A — Presigned URL (directo a object storage, recomendado)

```
1. POST /api/v1/properties/{id}/media/presign   (auth; image:upload_own o image:manage_any)
   body: { media_kind, content_type, byte_size, filename, checksum_sha256 }
   -> valida cuota, content_type declarado, byte_size <= limite (pre-check)
   -> responde: { upload_id, upload_url, fields{}, object_key, expires_at }   (URL TTL 5 min)
2. PUT/POST (cliente -> storage) usando upload_url + fields (multipart o PUT firmado).
   El bucket aplica Content-Length-Range y Content-Type via policy firmada.
3. POST /api/v1/properties/{id}/media/confirm
   body: { upload_id }
   -> backend lee el objeto, valida MIME REAL (magic bytes), dimensiones, peso real,
      crea PropertyImage(status pendiente de derivados) y encola job de optimizacion.
   -> responde 202 con el PropertyImage (cdn_url/thumb_url aun nulos o placeholder).
```

Validacion fuerte sucede en `confirm` (paso 3), no en `presign`: el `presign` solo hace pre-checks de cuota y limites declarados. Un objeto subido pero nunca confirmado expira como huerfano (MEDIA-R22).

### Modo B — Upload via API (multipart al backend)

```
POST /api/v1/properties/{id}/media   (multipart/form-data; auth)
  parts: file (binario), media_kind, alt_text?, role?
  -> backend recibe stream, valida peso/MIME real/dimensiones en linea,
     sube original al bucket privado, crea PropertyImage, encola optimizacion.
  -> 202 Accepted con el PropertyImage.
```

Uso: clientes simples / panel agente sin JS para firma directa. Sujeto a las mismas validaciones MEDIA-R1..R9. **VIDEO no se acepta por Modo B** (peso); se fuerza presigned (MEDIA-R30).

### Subida multiple

- El cliente repite `presign`/`confirm` (o multipart) por archivo; cada uno es un `PropertyImage` independiente.
- `POST .../media/presign-batch` acepta hasta N descriptores y devuelve N URLs firmadas en una llamada (N <= huecos disponibles de la cuota). Si la cuota se excede en el batch, responde 422 `media_quota_exceeded` sin firmar ninguna (atomico).
- El orden inicial `position` se asigna por orden de `confirm` exitoso, append al final de la galeria.

## Foto principal (`ImageRole.MAIN`)

- Toda propiedad publicable requiere **>=1 imagen** y exactamente **una** `MAIN` antes de pasar `DRAFT->PENDING` (regla compartida con lifecycle; ver property-lifecycle.md).
- La primera imagen `image` confirmada de una propiedad se marca `MAIN` automaticamente si aun no existe ninguna (MEDIA-R11).
- `PUT /api/v1/properties/{id}/media/{image_id}/main` promueve una imagen a `MAIN`: la anterior `MAIN` pasa a `GALLERY` en la **misma transaccion** (MEDIA-R10). Solo aplica a `media_kind='image'`.
- `Property.main_image_id` se actualiza en la misma transaccion al `id` de la nueva `MAIN`.
- No se puede eliminar la unica imagen si la propiedad esta `PUBLISHED`/`PENDING` y quedaria con 0 imagenes (MEDIA-R21); primero promover/agregar otra.

## Orden de galeria (`position`)

- `position` es 0-based, contiguo y unico por `property_id` dentro de `media_kind='image'`.
- `PUT /api/v1/properties/{id}/media/order` con `{ order: [image_id, ...] }` reordena en bloque (idempotente): el array debe contener exactamente los ids de imagenes de la propiedad; el backend reescribe `position` segun el indice del array (MEDIA-R12). Ids faltantes/extra -> 422 `media_order_mismatch`.
- Al eliminar una imagen se **recompactan** las posiciones siguientes para mantener contigüidad (MEDIA-R13).
- La `MAIN` no tiene `position` privilegiada (se ordena como cualquier galeria en su listado), pero la UI de detalle la muestra primero por `role`.

## Reemplazo y eliminacion

- **Reemplazo**: `PUT /api/v1/properties/{id}/media/{image_id}` con nuevo archivo (presign o multipart) crea un nuevo objeto original, regenera derivados y **conserva** `id`, `role` y `position`; el original viejo y sus derivados se eliminan tras exito del nuevo pipeline (swap atomico via job; MEDIA-R20).
- **Edicion de metadatos**: `PATCH .../media/{image_id}` permite cambiar `alt_text` (y `role` via endpoint dedicado de MAIN). No requiere re-procesamiento.
- **Eliminacion**: `DELETE .../media/{image_id}` borra fila + encola borrado de original y derivados del storage/CDN (purga de cache CDN incluida; MEDIA-R23). Recompacta `position` (MEDIA-R13). Sujeto a MEDIA-R21.
- **Cascada por propiedad**: al `soft_delete` de `Property` los medios NO se borran fisicamente de inmediato (permite restore); al borrado fisico/purga definitiva de la propiedad se purgan todos los objetos (MEDIA-R24).

## Validaciones de archivo

Aplicadas en `confirm` (Modo A) y en recepcion (Modo B). MIME real = deteccion por *magic bytes*, nunca por extension ni por `Content-Type` declarado (MEDIA-R5).

| Regla | Aplica a | Limite / criterio |
|---|---|---|
| Formatos imagen | image, floor_plan | `image/jpeg`, `image/png`, `image/webp` (entrada). AVIF de entrada opcional (OQ-2). |
| Formatos video | video | `video/mp4` (H.264/AAC) en MVP; otros -> rechazo |
| Tour virtual | virtual_tour | URL externa embebible (no upload de binario) o `mp4`; ver MEDIA-R31 |
| Peso maximo imagen | image, floor_plan | <= 10 MB (10 \* 1024 \* 1024 bytes) |
| Peso maximo video | video | <= 200 MB (MVP; OQ-4) |
| Dimensiones minimas | image | >= 800 x 600 px |
| Dimensiones maximas | image | <= 8000 x 8000 px (anti-DoS de decodificacion) |
| MIME real == declarado | todos | rechazo si `content_type` declarado != detectado |
| Maximo de medios | por Property | <= 30 imagenes; <= 5 video; <= 5 floor_plan; <= 1 virtual_tour |
| Doble extension / polyglot | todos | rechazo de archivos con firma ambigua/multiple |
| Nombre de objeto | todos | aleatorizado por backend; nunca el filename del cliente |

Respuestas de error usan el envelope estandar `{"error":{"code","message","details"}}`. Codigos de error de media: `media_invalid_format`, `media_too_large`, `media_dimensions_too_small`, `media_dimensions_too_large`, `media_mime_mismatch`, `media_quota_exceeded`, `media_order_mismatch`, `media_main_required`, `media_not_found`, `media_corrupt`.

## Pipeline de optimizacion (asincrono por cola)

El procesamiento NO bloquea la respuesta HTTP: `confirm`/upload responden 202 y el trabajo corre en worker via cola (Redis / broker). Idempotente por `(image_id, pipeline_version)`; reintentos con backoff exponencial; DLQ tras N=5 fallos (MEDIA-R40, MEDIA-R42).

```
[confirm] -> encolar job
worker:
  1. fetch original (bucket privado)
  2. validar/re-decodificar (defensa anti-payload) + strip de metadatos EXIF sensibles (GPS) [MEDIA-R51]
  3. autorotar segun EXIF orientation, luego strip EXIF
  4. generar variantes de tamano (resize, mantener aspect ratio, no upscalear)
  5. por cada tamano: emitir WebP (y AVIF si habilitado) + fallback JPEG
  6. comprimir (calidad objetivo) y optimizar
  7. subir derivados a bucket de derivados (ACL publica), clave derivable
  8. set cdn_url (full), thumb_url (mini), srcset (todos los anchos)
  9. UPDATE PropertyImage; emitir evento media.processed
on_error: reintento backoff; tras DLQ -> PropertyImage marcado degraded (sirve original via CDN como fallback) [MEDIA-R43]
```

### Variantes de tamano (anchos objetivo)

| Variante | Ancho objetivo (px) | Uso | Formatos emitidos |
|---|---|---|---|
| thumb | 320 | grids, listados, `thumb_url` | WebP, AVIF*, JPEG |
| small | 640 | mobile detail | WebP, AVIF*, JPEG |
| medium | 1024 | tablet / galeria | WebP, AVIF*, JPEG |
| large | 1600 | desktop detail, `cdn_url` | WebP, AVIF*, JPEG |
| xlarge | 2400 | zoom / retina | WebP, AVIF*, JPEG |

`*AVIF` solo si flag `media.avif_enabled` activo. No se hace upscaling: si el original es menor que un ancho objetivo, esa variante se omite (el `srcset` solo lista anchos realmente generados).

### Entrega y `srcset`

- `cdn_url` -> variante `large` en mejor formato negociable; `thumb_url` -> variante `thumb`.
- `srcset` se construye con los anchos generados: el cliente (`<img srcset sizes>` o `<picture>` con `<source type>` AVIF/WebP/JPEG) selecciona. Negociacion de formato preferentemente via `<picture>` (no via `Accept` server-side, dado CSR + CDN).
- Cache CDN: `Cache-Control: public, max-age=31536000, immutable` sobre derivados (clave inmutable). El reemplazo genera clave nueva (cache-busting natural) y purga la vieja.

## Almacenamiento seguro

- **Dos buckets logicos**: `originals` (ACL **privada**, sin acceso publico, solo backend/worker via credenciales) y `derivatives` (ACL **publica de lectura**, fronteado por CDN). Originales nunca se sirven directo al publico (MEDIA-R50).
- **Nombres aleatorizados**: clave de objeto = `properties/{property_id}/{image_id}/{random_token}.{ext}` con `random_token` no adivinable; nunca el filename del usuario (anti-enumeracion + anti-XSS por nombre) (MEDIA-R52).
- **EXIF**: strip de metadatos (incluida geolocalizacion GPS) en todos los derivados; el original conserva EXIF en bucket privado para auditoria (MEDIA-R51).
- **Cifrado**: SSE en reposo (server-side encryption del bucket) y TLS en transito.
- **Anti-abuso**: rate limit de `presign`/upload por usuario (Redis), validacion de cuota previa, y rechazo temprano por `byte_size` declarado.

## Reglas (MEDIA-R#)

| ID | Regla |
|---|---|
| MEDIA-R1 | Formatos de entrada permitidos por `media_kind` segun tabla de validaciones; cualquier otro -> `media_invalid_format`. |
| MEDIA-R2 | Peso imagen/floor_plan <= 10 MB; video <= 200 MB; exceso -> `media_too_large`. |
| MEDIA-R3 | Dimensiones imagen >= 800x600; menor -> `media_dimensions_too_small`. |
| MEDIA-R4 | Dimensiones imagen <= 8000x8000; mayor -> `media_dimensions_too_large`. |
| MEDIA-R5 | MIME se valida por magic bytes (real); debe coincidir con `content_type` declarado; mismatch -> `media_mime_mismatch`. |
| MEDIA-R6 | Maximo por Property: 30 image, 5 video, 5 floor_plan, 1 virtual_tour; exceso -> `media_quota_exceeded`. |
| MEDIA-R7 | Rechazo de archivos polyglot/doble firma o que no decodifican -> `media_corrupt`. |
| MEDIA-R8 | Validacion fuerte ocurre en `confirm` (Modo A) o en recepcion (Modo B); `presign` solo hace pre-checks declarados. |
| MEDIA-R9 | `content_type` persistido = MIME real detectado, no la extension. |
| MEDIA-R10 | Exactamente una `ImageRole.MAIN` por Property; promover MAIN degrada la anterior a GALLERY en la misma transaccion. |
| MEDIA-R11 | La primera imagen confirmada se auto-marca MAIN si no existe ninguna. |
| MEDIA-R12 | `position` 0-based, contiguo, unico por property dentro de `image`; reorden por bloque idempotente. |
| MEDIA-R13 | Tras eliminar/reemplazar, recompactar `position` para mantener contiguidad. |
| MEDIA-R20 | Reemplazo conserva `id`/`role`/`position`; swap de original+derivados atomico tras exito del nuevo pipeline. |
| MEDIA-R21 | No eliminar la unica imagen si la Property quedaria con 0 imagenes estando en `PENDING`/`PUBLISHED` -> `media_main_required`. |
| MEDIA-R22 | Objetos subidos por presign y no confirmados en TTL son huerfanos: barrido programado los purga. |
| MEDIA-R23 | `DELETE` de medio borra fila + original + derivados + purga de cache CDN. |
| MEDIA-R24 | `soft_delete` de Property no purga medios (permite restore); borrado fisico de Property purga todos los medios. |
| MEDIA-R30 | VIDEO solo por presigned URL (Modo A); rechazado por Modo B multipart. |
| MEDIA-R31 | `virtual_tour` admite URL externa embebible allowlisted o `mp4`; URLs no allowlisted -> `media_invalid_format`. |
| MEDIA-R40 | Optimizacion siempre asincrona por cola; `confirm`/upload responden 202. |
| MEDIA-R41 | Pipeline idempotente por `(image_id, pipeline_version)`; re-procesar no duplica derivados. |
| MEDIA-R42 | Reintentos con backoff exponencial; tras 5 fallos -> DLQ. |
| MEDIA-R43 | Medio en estado `degraded` sirve el original via CDN como fallback hasta reproceso manual. |
| MEDIA-R44 | No upscaling: variantes con ancho > original se omiten; `srcset` lista solo anchos generados. |
| MEDIA-R50 | Originales en bucket privado (ACL privada), nunca servidos al publico; derivados en bucket publico via CDN. |
| MEDIA-R51 | Strip de EXIF (incl. GPS) en todos los derivados; original conserva EXIF en privado. |
| MEDIA-R52 | Nombres de objeto aleatorizados/no adivinables; nunca el filename del cliente. |
| MEDIA-R53 | SSE en reposo + TLS en transito; rate limit de presign/upload por usuario via Redis. |

## Permisos (referencia)

| Accion | Permiso requerido |
|---|---|
| Subir/confirmar/editar/eliminar medios propios | `image:upload_own` (sobre Property cuyo `owner_id` = actor) |
| Gestionar medios de cualquier Property | `image:manage_any` (ADMIN/SUPERADMIN) |

VISITOR y REGISTERED_USER sin propiedad no pueden subir. AGENT gestiona solo lo propio salvo `image:manage_any`.

## Endpoints (resumen; normativo en api-contracts.md)

| Metodo | Ruta | Proposito |
|---|---|---|
| POST | /api/v1/properties/{id}/media/presign | Solicitar URL firmada (Modo A) |
| POST | /api/v1/properties/{id}/media/presign-batch | N URLs firmadas (subida multiple) |
| POST | /api/v1/properties/{id}/media/confirm | Confirmar subida -> crea PropertyImage + encola |
| POST | /api/v1/properties/{id}/media | Upload multipart directo (Modo B) |
| GET | /api/v1/properties/{id}/media | Listar medios ordenados por `position` |
| PATCH | /api/v1/properties/{id}/media/{image_id} | Editar metadatos (`alt_text`) |
| PUT | /api/v1/properties/{id}/media/{image_id} | Reemplazar binario (conserva id/role/position) |
| PUT | /api/v1/properties/{id}/media/{image_id}/main | Promover a `MAIN` |
| PUT | /api/v1/properties/{id}/media/order | Reordenar galeria en bloque |
| DELETE | /api/v1/properties/{id}/media/{image_id} | Eliminar medio + purga |

## Open Questions

- **OQ-1**: Confirmar el broker/cola exacto para el pipeline (Redis Streams vs RabbitMQ vs SQS). El contrato fija Redis para cache/rate-limit; reutilizarlo para la cola o introducir broker dedicado.
- **OQ-2**: Aceptar AVIF de **entrada** (ademas de salida) — requiere decoder confiable en el worker.
- **OQ-3**: Introducir tabla `property_image_variant` para variantes consultables si analytics/SEO necesitan URLs de derivados como filas; en MVP se derivan por convencion de clave.
- **OQ-4**: Limites definitivos de VIDEO (peso 200 MB, formatos, transcodificacion/HLS) — confirmar con producto si VIDEO entra en MVP o es fase 2.
- **OQ-5**: Politica de watermark sobre derivados (branding del portal) — fuera de alcance del MVP salvo decision contraria.
