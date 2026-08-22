# Implementation Plan: 004-tour-llegada-piso

**Branch**: `feature/004-tour-llegada-piso` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

## Summary

Orientar la llegada entre escenas con la funcion `transitionOptions` del plugin (opuesto al
hotspot de retorno), proyectar los links del visor a pitch de piso fijo, normalizar angulos
en dominio+API y corregir data historica via migracion Alembic.

## Technical Context

- **Frontend**: Photo Sphere Viewer v5 — `VirtualTourPlugin.withConfig({ preload, transitionOptions })`.
- **Backend**: Python 3.13 / FastAPI; normalizacion en `src/virtual_tour.py` + router.
- **DB**: Postgres; migracion de datos con trig SQL (`atan2(sin(yaw), cos(yaw))`, clamp).

## Technical Design

### 1. Llegada orientada (FR-401)

El plugin, al navegar por un enlace, hace `rotateTo: fromLinkPosition` — llega mirando hacia
donde estaba el enlace en la escena anterior (o mantiene el yaw si no hubo enlace). Con panos
IA sin alineacion mundial eso aterriza siempre en el mismo contenido ("la terraza").

Solucion: `transitionOptions: (node, fromNode) => {...}`. Si la escena destino tiene hotspot
de retorno hacia `fromNode`, llegamos mirando su opuesto (`yaw_back + π`): entrada a la
espalda, interior enfrente. Sin retorno: `{}` conserva el default.

### 2. Piso en visor y editor (FR-402/403)

- Visor: `position: { yaw: spot.yaw, pitch: -72° }` constante para todos los links.
- Editor: los dots se dibujan con yaw envuelto a [−π,π] y pitch clampado a [−85°,−60°],
  usando las mismas constantes que el visor.

### 3. Normalizacion (FR-404/405)

- Dominio: `normalize_yaw()` (wrap via atan2) y `FLOOR_PITCH_LOW/HIGH` +
  `normalize_floor_pitch()` en `src/virtual_tour.py`; tests unitarios con los valores
  corruptos reales como casos.
- Router `replace_hotspots`: normaliza cada hotspot antes del ORM.
- Migracion Alembic (data-only):
  `UPDATE virtual_tour_hotspots SET yaw = atan2(sin(yaw), cos(yaw))`
  `UPDATE virtual_tour_hotspots SET pitch = greatest(radians(-85), least(radians(-60), pitch))`

### 4. Preload correcto (FR-406)

`preload: true` pasa al config del plugin (verificado en `index.d.ts`: opcion de config,
no de link). Se elimina el `preload:true` per-link anadido en 003. El warm-up `Image()`
se conserva.

## Verification

- pytest completo verde (tests nuevos de normalizacion incluidos).
- `npm run build` verde.
- Deploy y verificacion de bundle segun CLAUDE.md; validacion visual del usuario.
