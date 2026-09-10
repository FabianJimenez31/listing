# Tasks — 002-virtual-tours

> Checklist de specs/002-virtual-tours/. Indice en [spec.md](spec.md). Estrategia en [plan.md](plan.md).

**Branch**: `feature/002-virtual-tours`

Convencion: `[x]` hecho · `[/]` en curso · `[ ]` pendiente.

## Fase 0 — Verificaciones previas

- [x] T-000 Confirmar `client_max_body_size` en `nginx.conf` del contenedor frontend soporta
      equirectangulares (NFR-206). Ya hubo un 413 con fotos >1MB.
- [x] T-001 Confirmar que `src/storage/image_store.py` acepta el tamano de una equirectangular
      (hoy `MAX_BYTES = 10 MB`) y decidir si sube para panos.

## Fase 1 — Dominio y migracion

- [x] T-100 `src/virtual_tour.py`: enums `TourStatus`, `SceneSource`, `SceneState`.
- [x] T-101 `src/virtual_tour.py`: dataclasses `TourScene`, `TourHotspot`, `VirtualTour`.
- [x] T-102 Reglas de dominio: ordenar escenas, resolver escena inicial (FR-205), validar aspecto
      ~2:1 (FR-211), precondiciones de publicacion (FR-202, FR-216).
- [x] T-103 `src/db/models/virtual_tour_models.py`: ORM de `virtual_tours`,
      `virtual_tour_scenes`, `virtual_tour_hotspots` con `ON DELETE CASCADE` (FR-206).
- [x] T-104 Registrar los modelos nuevos en `src/db/models/__init__.py`.
- [x] T-105 Migracion Alembic: tablas, `CHECK` de dueno unico, indices unicos parciales por entidad.
- [x] T-106 `tests/test_virtual_tour.py`: tests unitarios del dominio (marcador `unit`).

## Fase 2 — API de tours

- [x] T-200 `src/schemas/virtual_tour_schemas.py`: request/response Pydantic.
- [x] T-201 `src/repositories/virtual_tour_repo.py`: tour por entidad, tour publicado, escenas
      ordenadas, hotspots por escena.
- [x] T-202 `src/api/routers/virtual_tours.py`: guard de permisos para inmueble y proyecto,
      reutilizando el patron de `src/api/routers/images.py`.
- [x] T-203 `GET /{entity}/{id}/tour` publico — 404 cuando el tour esta en `draft` (AC-202).
- [x] T-204 `GET /{entity}/{id}/tour/admin` para staff/dueno.
- [x] T-205 `POST` / `PATCH` del tour: crear, publicar, despublicar, escena inicial, acuse de IA.
- [x] T-206 `POST /{entity}/{id}/tour/scenes`: subida de equirectangular con validacion 2:1 (FR-211).
- [x] T-207 `PATCH` / `DELETE` de escena y `PATCH .../scenes/reorder`.
- [x] T-208 `PUT /tour/scenes/{id}/hotspots`: reemplazo del conjunto de hotspots.
- [x] T-209 Registrar el router en `src/api/app.py`.
- [x] T-210 `tests/test_api_virtual_tours.py`: AC-202, AC-206 (marcador `integration`).

## Fase 3 — Panel: composicion manual

- [x] T-300 `frontend/src/api/tours.js`: cliente HTTP.
- [x] T-301 `TourEditor.jsx`: lista de escenas con miniatura, titulo, origen y estado.
- [x] T-302 Subir panoramica desde el editor, con aviso cuando el aspecto no es ~2:1.
- [x] T-303 Reordenar escenas y elegir la escena inicial.
- [x] T-304 `TourHotspotPicker.jsx`: ubicar hotspots sobre la panoramica y elegir destino (FR-215).
- [x] T-305 Publicar / despublicar con el acuse de contenido IA cuando aplica (FR-216).
- [x] T-306 Integrar la seccion "Tour 360" en el formulario de inmueble y en
      `frontend/src/pages/agent/ProjectFormPage.jsx`.

## Fase 4 — Visor publico

- [x] T-400 Instalar las dependencias de Photo Sphere Viewer en `frontend/package.json`.
- [x] T-401 `TourViewer.jsx`: PSV + `VirtualTourPlugin` + `MarkersPlugin` + `GalleryPlugin`.
- [x] T-402 Controles explicitos de avanzar / retroceder por orden de escena (FR-222).
- [x] T-403 `TourAiNotice.jsx`: aviso no descartable, dentro del contenedor del visor para sobrevivir
      a pantalla completa (FR-223, AC-204).
- [x] T-404 `TourTab.jsx`: carga diferida con `React.lazy`, sin bundle en el chunk inicial
      (FR-224, AC-207).
- [x] T-405 Pestana "Tour 360" en `PropertyDetailPage.jsx` y `ProjectDetailPage.jsx`, oculta cuando
      no hay tour publicado (FR-220).
- [ ] T-406 Verificacion manual de AC-201: tour de 3 escenas por subida directa, publicado y
      recorrido en la ficha publica.

## Fase 5 — Generacion con IA

- [x] T-500 `src/media/pano_provider.py`: `PanoProvider`, `PanoResult`, `resolve_provider()`.
- [x] T-501 `src/media/openai_pano_provider.py`: edicion con referencias, salida 2:1 y pasada opcional
      de reparacion de costura.
- [x] T-502 Mapeo de errores del proveedor a `error_message` legible (AC-205).
- [x] T-503 Persistir el pano en almacenamiento propio bajo `tours/{tour_id}/{scene_id}` y construir
      `pano_url` absoluta (FR-232, NFR-203).
- [x] T-504 `POST /{entity}/{id}/tour/scenes:generate` con `BackgroundTasks`; 503 sin proveedor
      (FR-217).
- [x] T-505 `GET /tour/scenes/{id}/status` para el poll del panel (FR-213).
- [x] T-506 Marcar como `failed` las escenas `pending` vencidas por timeout.
- [x] T-507 Variables nuevas en `.env.example`: `OPENAI_API_KEY`, `TOUR_PANO_MODEL`, calidad,
      resolucion, timeout, costo estimado y pasada de costura.
- [x] T-508 Panel: seleccion multiple de fotos de galeria, costo estimado y confirmacion (FR-212,
      FR-214), estado de progreso, boton deshabilitado sin credencial.
- [x] T-509 `tests/test_openai_pano_provider.py` con transporte falso: exito y errores del proveedor.
- [x] T-510 Aclarar en el panel que las fotos seleccionadas son referencias de un solo ambiente y
      que los hotspots requieren al menos dos escenas generadas por separado.
- [x] T-511 Redisenar el panel como flujo plug-and-play de tres pasos, crear conexiones automaticas
      por orden y relegar la posicion de la flecha siguiente a un ajuste opcional (FR-218/FR-219).

## Fase 6 — Cierre

- [x] T-600 `make dev-check` verde; unitarias, migraciones y flujo de rutas verdes. El bloqueo
      historico (`anyio.to_thread.run_sync` colgaba la suite HTTP en este host) ya no se reproduce:
      re-ejecutada el 2026-08-22 con pytest-timeout, 307 unitarias y 240 de integracion pasaron.
- [x] T-601 `npm run build` en `frontend/` sin errores, antes de tocar Docker.
- [x] T-602 Deploy: `docker compose build frontend backend` → `up -d frontend backend`.
      Verificado el 2026-08-22: el contenedor frontend sirve este dist y el router de tours
      responde en el backend vivo (9 endpoints en /api/v1/tour/*).
- [x] T-603 Verificar el bundle servido segun el procedimiento de CLAUDE.md: el hash servido
      (`index-DbdzFL8S.js`) coincide con el dist local y contiene la pestana "Tour 360".
- [x] T-604 Actualizar `CLAUDE.md` con la funcion de tours y las variables nuevas.

## Bloqueos externos

La subida directa y el visor no tienen bloqueos externos. Para validar calidad y costo de la
generacion se necesita una `OPENAI_API_KEY` con facturacion activa; el sistema permanece funcional
cuando la variable esta vacia.
