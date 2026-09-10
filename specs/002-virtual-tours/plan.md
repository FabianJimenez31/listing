# Plan — 002-virtual-tours

> Estrategia tecnica de specs/002-virtual-tours/. Indice en [spec.md](spec.md).
> Checklist en [tasks.md](tasks.md).

**Branch**: `feature/002-virtual-tours`

## Estrategia general

Se construye de adentro hacia afuera y en orden de independencia de terceros, de modo que la funcion
sea util antes de tener credenciales del proveedor de IA:

```
Fase 1  Dominio + migracion        -> sin dependencias externas
Fase 2  API de tours (CRUD)        -> sin dependencias externas
Fase 3  Panel: composicion manual  -> tour completo funcionando con subida directa
Fase 4  Visor publico              -> AC-201 verificable end-to-end, gasto cero
Fase 5  Proveedor IA conectable    -> se activa con OPENAI_API_KEY
```

Las fases 1-4 entregan un producto completo sin gastar un peso en IA. La fase 5 agrega la
generacion automatica encima, sin modificar nada de lo anterior (FR-230).

## Modelo de datos

Dos tablas nuevas. Se evita colgar las escenas de `property_images` porque un tour pertenece tambien
a proyectos y porque una escena tiene atributos propios (yaw/pitch inicial, assets 3D, estado de
generacion) que no aplican a una foto de galeria.

### `virtual_tours`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `String(36)` PK | UUID v4, consistente con el resto del esquema |
| `property_id` | `String(36)` FK → `properties.id` `ON DELETE CASCADE`, nullable | |
| `project_id` | `String(36)` FK → `projects.id` `ON DELETE CASCADE`, nullable | |
| `status` | `String(20)` not null default `'draft'` | `draft` / `published` |
| `start_scene_id` | `String(36)` nullable | escena de entrada (FR-205) |
| `ai_disclaimer_ack` | `Boolean` not null default `false` | quedo aceptada la advertencia al publicar (FR-216) |
| `created_at` / `updated_at` | `DateTime(timezone=True)` | |

Restricciones:
- `CHECK` exactamente uno de (`property_id`, `project_id`) no nulo → un tour tiene un solo dueno (FR-201).
- Indice unico parcial sobre `property_id` y otro sobre `project_id` → maximo un tour por entidad (FR-201).

### `virtual_tour_scenes`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `String(36)` PK | |
| `tour_id` | `String(36)` FK → `virtual_tours.id` `ON DELETE CASCADE`, index | |
| `title` | `String(120)` not null | nombre del ambiente |
| `position` | `Integer` not null default 0 | orden para avanzar/retroceder (FR-222) |
| `source` | `String(10)` not null | `upload` / `ai` (FR-203) |
| `state` | `String(10)` not null default `'ready'` | `pending` / `ready` / `failed` (FR-213) |
| `error_message` | `String(500)` nullable | motivo legible del fallo (AC-205) |
| `storage_key` | `String(500)` nullable | key propia de la equirectangular; null mientras `pending` |
| `pano_url` | `String(1000)` nullable | absoluta (NFR-203) |
| `thumb_url` | `String(1000)` nullable | |
| `width` / `height` | `Integer` nullable | para validar ~2:1 (FR-211) |
| `initial_yaw` / `initial_pitch` | `Float` not null default 0 | orientacion de entrada |
| `hfov_deg` | `Float` not null default 360 | cobertura horizontal en grados (FR-208) |
| `vfov_deg` | `Float` not null default 180 | cobertura vertical en grados (FR-208) |
| `source_image_ids` | `Text` nullable | JSON con los ids de `property_images` usados como entrada (FR-231) |
| `provider` / `provider_model` | `String(60)` nullable | trazabilidad de la generacion |
| `cost_usd` | `Numeric(10, 5)` nullable | auditoria de gasto, incluye ambas pasadas (FR-231, FR-235) |
| `created_at` / `updated_at` | `DateTime(timezone=True)` | |

### `virtual_tour_hotspots`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `String(36)` PK | |
| `from_scene_id` | `String(36)` FK → `virtual_tour_scenes.id` `ON DELETE CASCADE`, index | |
| `to_scene_id` | `String(36)` FK → `virtual_tour_scenes.id` `ON DELETE CASCADE`, index | FR-206 via cascade |
| `yaw` / `pitch` | `Float` not null | posicion angular sobre la panoramica origen (FR-204) |
| `label` | `String(120)` nullable | texto del tooltip |

`ON DELETE CASCADE` en ambos FK resuelve FR-206/AC-206 a nivel de base de datos, sin logica de
aplicacion que se pueda olvidar.

### Modulos de codigo

Respetando RC-5 y la regla de "no dump modules" de la constitucion:

| Archivo | Responsabilidad |
|---|---|
| `src/virtual_tour.py` | Dominio puro: enums `TourStatus`, `SceneSource`, `SceneState`; dataclasses `TourScene`, `TourHotspot`, `VirtualTour`; reglas de orden, escena inicial, validacion 2:1 y precondicion de publicacion. Solo stdlib. |
| `src/db/models/virtual_tour_models.py` | ORM de las tres tablas. |
| `src/repositories/virtual_tour_repo.py` | Consultas: tour por entidad, tour publicado, escenas ordenadas. |
| `src/schemas/virtual_tour_schemas.py` | Pydantic de request/response. |
| `src/api/routers/virtual_tours.py` | Endpoints. |
| `src/media/pano_provider.py` | Interfaz `PanoProvider` + resolucion del proveedor activo. |
| `src/media/openai_pano_provider.py` | Implementacion OpenAI `gpt-image-2`. |
| `src/media/pano_seam.py` | Rotacion horizontal y composicion de la mascara de costura (numpy/Pillow, CPU). |
| `alembic/versions/<rev>_virtual_tours.py` | Migracion. |

`src/property_image.py` no se toca: `MediaKind.VIRTUAL_TOUR` ya existe (FR-207) y el dominio nuevo
vive en su propio modulo.

## Contrato de la API

Prefijo comun con parametro de entidad para no duplicar el router entre inmuebles y proyectos:

| Metodo | Ruta | Auth | Descripcion |
|---|---|---|---|
| `GET` | `/{entity}/{id}/tour` | publica | Tour `published` con escenas y hotspots. 404 si no hay o esta en `draft`. AC-202 |
| `GET` | `/{entity}/{id}/tour/admin` | staff/dueno | Tour en cualquier estado, con estados de generacion |
| `POST` | `/{entity}/{id}/tour` | staff/dueno | Crea el tour vacio (idempotente: devuelve el existente) |
| `PATCH` | `/{entity}/{id}/tour` | staff/dueno | `status`, `start_scene_id`, `ai_disclaimer_ack` |
| `POST` | `/{entity}/{id}/tour/scenes` | staff/dueno | Sube una equirectangular (`multipart/form-data`). FR-211 |
| `POST` | `/{entity}/{id}/tour/scenes:generate` | staff/dueno | Genera desde `source_image_ids[]` + `model`. FR-212. 503 si no hay proveedor |
| `PATCH` | `/tour/scenes/{scene_id}` | staff/dueno | `title`, `position`, `initial_yaw`, `initial_pitch` |
| `DELETE` | `/tour/scenes/{scene_id}` | staff/dueno | |
| `PATCH` | `/{entity}/{id}/tour/scenes/reorder` | staff/dueno | Lista de ids, mismo patron que `images.py` |
| `PUT` | `/tour/scenes/{scene_id}/hotspots` | staff/dueno | Reemplaza los hotspots de la escena |
| `GET` | `/tour/scenes/{scene_id}/status` | staff/dueno | Poll de generacion. FR-213 |

`{entity}` ∈ `properties` | `projects`. El guard de permisos reutiliza el patron de
`_get_property_owned` de `src/api/routers/images.py`, extendido a proyectos.

Publicar (`PATCH status=published`) valida en el dominio:
- al menos una escena en `ready` con `pano_url` (FR-202);
- si alguna escena es `source='ai'`, exige `ai_disclaimer_ack=true` (FR-216);
- `start_scene_id` apunta a una escena `ready` del mismo tour, o se recalcula a la de menor posicion.

## Contrato del proveedor de panoramicas

```python
class PanoResult(NamedTuple):
    pano_bytes: bytes
    width: int
    height: int
    hfov_deg: float          # cobertura real de lo entregado (FR-208)
    vfov_deg: float
    provider: str
    provider_model: str
    cost_usd: Decimal | None

class PanoProvider(Protocol):
    name: str
    def is_available(self) -> bool: ...
    def estimate_cost_usd(self, image_count: int, seam_pass: bool) -> Decimal: ...
    def generate(
        self,
        reference_images: list[bytes],
        prompt: str,
        *,
        seam_pass: bool,
    ) -> PanoResult: ...
```

`resolve_provider()` devuelve `None` cuando no hay credencial → el endpoint responde 503 y el panel
deshabilita el boton (FR-217). Ese es el estado por defecto hoy.

### Implementacion OpenAI (`gpt-image-2`)

`POST https://api.openai.com/v1/images/edits`, `Authorization: Bearer $OPENAI_API_KEY`,
`multipart/form-data` con las fotos de referencia en `image[]`.

Parametros: `model=gpt-image-2`, `size` en relacion **2:1**, `quality=medium`. Restricciones oficiales
del tamano que la implementacion debe respetar y validar antes de llamar:

- lado mayor ≤ 3840 px;
- ancho y alto multiplos de 16;
- relacion de aspecto ≤ 3:1;
- pixeles totales entre 655.360 y 8.294.400.

`3840x1920` (7,37 MP) cumple los cuatro y es el tamano objetivo; `2048x1024` (2,10 MP) es la opcion
barata. El prompt se compone del tipo de inmueble, el nombre del ambiente y una instruccion explicita
de proyeccion equirectangular con horizonte a media altura.

**Cobertura angular declarada.** Por defecto la escena se registra como panoramica parcial
(`hfov_deg=180`, `vfov_deg=90`) porque el modelo no garantiza wraparound ni polos correctos (RC-2).
El visor la renderiza con esa geometria y limita el rango de mirada, en vez de estirar la imagen
sobre la esfera completa.

**Doble pasada de costura** (solo cuando `TOUR_SEAM_PASS=1`, para 360 completo — FR-235):

1. primera llamada → imagen 2:1;
2. `numpy.roll(img, width // 2, axis=1)` — rotar 50% horizontal, CPU;
3. segunda llamada a `/v1/images/edits` con una mascara vertical estrecha en el centro, para que el
   modelo repinte la discontinuidad;
4. `numpy.roll` inverso. La escena queda con `hfov_deg=360`.

**Persistencia.** La imagen devuelta se guarda con `src/storage/image_store.store()` bajo
`tours/{tour_id}/{scene_id}.jpg` y `pano_url` se construye absoluta desde `CDN_BASE_URL` (FR-232,
NFR-203). Nunca se persiste una URL del proveedor.

**Errores** mapeados a `error_message` legible: `401` → "Credencial del proveedor invalida";
`429` → "Limite de tasa del proveedor, reintentar"; `400` con `content_policy` → "El proveedor rechazo
la imagen de entrada"; timeout → "La generacion excedio el tiempo limite"; `5xx` → "El proveedor no
esta disponible".

Costo por imagen segun tarifario oficial (para FR-214). Los precios publicados cubren
1024x1024 / 1024x1536 / 1536x1024; **el costo a 2:1 no esta publicado y debe medirse leyendo el
`usage` de una llamada real** antes de fijar el estimador:

| Modelo | Calidad | USD/imagen (1536x1024) |
|---|---|---|
| `gpt-image-2` | low | 0,005 |
| `gpt-image-2` | medium | 0,041 |
| `gpt-image-2` | high | 0,165 |
| `gpt-image-1-mini` | low | 0,005 |

Con doble pasada el costo por escena se duplica. Referencia de escala: 119 inmuebles x ~5 ambientes
≈ 595 escenas → ~USD 25 en `medium` a una pasada, ~USD 49 con doble pasada.

Segundo proveedor posible (`src/media/gemini_provider.py`, no en v1): Gemini 3.1 Flash Image, USD
0,101/imagen a 2K. **No soporta 2:1** — su maximo apaisado es 21:9 (2,33:1), asi que esa
implementacion tendria que recortar a 2:1 y declarar la cobertura resultante (FR-233).

Configuracion nueva en `.env` / `.env.example`:

```
OPENAI_API_KEY=                    # vacio => generacion deshabilitada, subida directa sigue activa
TOUR_PANO_MODEL=gpt-image-2
TOUR_PANO_QUALITY=medium
TOUR_PANO_SIZE=3840x1920           # 2:1; respetar las 4 restricciones de tamano
TOUR_SEAM_PASS=0                   # 1 => 360 completo con doble pasada (duplica el costo)
TOUR_PANO_TIMEOUT_SECONDS=300
```

### Ejecucion asincrona

Una generacion tarda decenas de segundos, y con doble pasada son dos llamadas encadenadas — por
encima de lo razonable para un request HTTP. Se resuelve con `BackgroundTasks` de FastAPI: el
endpoint crea la escena en `pending` y responde de inmediato; la tarea de fondo llama al proveedor,
aplica la costura si corresponde, persiste la imagen y actualiza a `ready`/`failed`. El panel consulta
`GET /tour/scenes/{id}/status`.
No se introduce Celery: hay un solo worker de uvicorn y el volumen es de unas pocas generaciones por
dia. Si el proceso se reinicia a mitad de una generacion, la escena queda en `pending` y se marca
`failed` por antiguedad al consultarla — es aceptable para v1 y se documenta.

## Frontend

### Dependencias nuevas

```
@photo-sphere-viewer/core
@photo-sphere-viewer/virtual-tour-plugin
@photo-sphere-viewer/markers-plugin
@photo-sphere-viewer/gallery-plugin
react-photo-sphere-viewer
```

Se cargan con `React.lazy` + import dinamico dentro del componente del tour, de modo que ni el
bundle del visor ni su CSS entren en el chunk inicial de la ficha (FR-224, NFR-201, AC-207).

### Componentes

| Archivo | Rol |
|---|---|
| `frontend/src/components/tour/TourViewer.jsx` | Visor: PSV + VirtualTour + Markers + Gallery, controles avanzar/retroceder (FR-222), aviso IA fijo (FR-223), cobertura parcial via `panoData` con los grados de `hfov_deg`/`vfov_deg` (FR-208) |
| `frontend/src/components/tour/TourAiNotice.jsx` | Banda de aviso no descartable, sobrevive a fullscreen (AC-204) |
| `frontend/src/components/tour/TourTab.jsx` | Carga diferida + estado vacio |
| `frontend/src/components/panel/TourEditor.jsx` | Seccion "Tour 360" del formulario: lista de escenas, subir pano, generar con IA, reordenar, elegir inicial, publicar |
| `frontend/src/components/panel/TourHotspotPicker.jsx` | Ubicar hotspots haciendo clic sobre la panoramica y elegir destino |

### Flujo guiado del panel

El editor se presenta como un asistente de tres pasos. Las escenas `ready` forman por orden un
recorrido circular que el visor ya puede sintetizar sin filas de hotspot. La lista comunica cada
conexion como `Ambiente A -> Ambiente B`; subir/bajar una escena cambia ese recorrido. La edicion
angular queda bajo `Ajustar flecha (opcional)` y solo modifica la salida hacia el siguiente ambiente,
eliminando la seleccion manual de destinos que podia divergir del visor publico.
| `frontend/src/api/tours.js` | Cliente HTTP |

El aviso de IA se renderiza **dentro del contenedor del visor**, no como hermano, porque la API de
pantalla completa promueve solo el nodo del visor: un aviso hermano desaparece en fullscreen y eso
violaria AC-204.

Puntos de integracion: pestana en `PropertyDetailPage.jsx` y `ProjectDetailPage.jsx` (FR-220);
seccion nueva en `frontend/src/pages/agent/ProjectFormPage.jsx` y en el formulario de inmueble.

## Riesgos y mitigaciones

| Riesgo | Mitigacion |
|---|---|
| **La calidad puede no alcanzar para publicar.** Un modelo de imagen general no esta entrenado para proyeccion equirectangular: puede entregar una foto apaisada bonita que se vea deformada en el visor | Prueba de calidad barata antes de cablear el flujo: comparar `low` / `medium` / `high` a 2:1 sobre fotos reales del catalogo (~USD 2 en total) y mirar el resultado dentro del visor, no como imagen plana. Es el criterio de continuidad de la Fase 5 |
| El costo a 2:1 no esta publicado | Medirlo con una llamada real leyendo `usage` (T-510) antes de mostrar estimados al operador (FR-214) |
| Costura y polos incorrectos (RC-2) | Cobertura parcial declarada por defecto (FR-208); doble pasada opcional para 360 real (FR-235) |
| La IA inventa espacios que no existen (RC-3) | Aviso permanente (FR-223/NFR-204), estado `draft` por defecto, publicacion explicita con acuse |
| Panoramicas grandes → 413 en el nginx del contenedor | Verificar `client_max_body_size` antes de la Fase 3 (NFR-206); ya hubo un incidente identico con fotos >1MB |
| Peso de las equirectangulares en la ficha | Carga diferida (FR-224) + WebP + cache larga (NFR-202) |
| Dependencia de un proveedor unico | Interfaz `PanoProvider` (FR-230); el modo subida-directa nunca depende de terceros (NFR-205) |
| Gasto descontrolado | Confirmacion con costo estimado (FR-214) + registro de `cost_usd` por escena (FR-231) + `medium` a una pasada como configuracion por defecto |

## Verificacion

- Tests unitarios del dominio (`tests/test_virtual_tour.py`): orden, escena inicial, validacion 2:1,
  precondiciones de publicacion, cascada de hotspots. Marcador `unit`.
- Tests de integracion del router con proveedor falso (`tests/test_virtual_tours_api.py`): AC-202,
  AC-205, AC-206. Marcador `integration`.
- Verificacion manual end-to-end de AC-201 (tour de 3 escenas por subida directa) antes de la Fase 5.
- `make dev-check` y `make test` verdes; `npm run build` en `frontend/` antes de cualquier rebuild de
  Docker, para no pagar el ciclo completo por un error de compilacion.
