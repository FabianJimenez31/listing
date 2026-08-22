# Implementation Plan: 003-tour-visor-matterport

**Branch**: `feature/003-tour-visor-matterport` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

## Summary

Precarga total de panoramicas en el visor y hotspots estilo Matterport (flechas de piso
separadas, editor sin distorsion). Cambios concentrados en el frontend (`TourViewer.jsx`,
`TourHotspotPicker.jsx`, `tour.css`) con una validacion defensiva nueva en el backend
(rangos angulares) y su test.

## Technical Context

- **Languages/Versions**: Python 3.13 (FastAPI), React 18 + Vite, PostgreSQL 16.
- **Primary Dependencies**: Photo Sphere Viewer v5 (`core`, `virtual-tour-plugin`, `markers-plugin`).
- **Storage/Databases**: Postgres (tablas de 002 sin cambios de schema).
- **Testing Frameworks**: pytest (unit/integration), build de Vite como gate de compile.

## Technical Design

### 1. Precarga total — `TourViewer.jsx`

PSV `VirtualTourPlugin` baja la textura de cada nodo al entrar (`setCurrentNode`). Dos capas:

1. **Calentamiento explicito**: al montar el visor, por cada escena se crea `new Image()`
   con `decoding='async'` apuntando a `pano_url`. El navegador guarda las respuestas en su
   cache HTTP; cuando PSV pide la misma URL la decodifica desde disco/memoria sin red.
   No bloquea la interaccion (NFR-301): es solo disparo de descargas en background.
2. **`preload: true` en cada link** del plugin: PSV mantiene listas las texturas vecinas,
   cubriendo el caso de cache deshabilitado (FR-302).

El chunk sigue siendo lazy via `TourTab.jsx` (React.lazy) — sin cambios (NFR-302).

### 2. Editor geometricamente fiel — `TourHotspotPicker.jsx`

Hoy `.hotspot-canvas img` usa `object-fit: fill` + `max-height: 420px`: si el ancho del panel
produce una altura natural mayor, la imagen se aplasta y los clics mapean mal (causa raiz del
desalineo percibido junto con la proyeccion libre). Solucion:

- El contenedor fija `aspect-ratio: width/height` de la escena (ya guardamos `width`/`height`
  en DB) y la imagen llena el contenedor al 100%. Sin recortes ni estiramientos.
- Los clics siguen mapeando lineal a (yaw, pitch) sobre hfov/vfov declarados — ahora coherentes
  porque el lienzo ya no se deforma.

### 3. Hotspots Matterport — picker + CSS

- **Banda de piso (FR-304)**: al colocar un hotspot, pitch se clampéa a [−85°, −60°]
  (constantes `FLOOR_PITCH_MAX/MIN`). En equirectangular eso es la franja inferior de la
  imagen; visualmente en la esfera queda "sobre el piso" como Matterport.
- **Separacion minima (FR-305)**: antes de agregar, se compara contra los existentes;
  si |Δyaw| < 10° y |Δpitch| < 15° se rechaza con aviso inline (sin alert).
- **Flecha visual**: `.hotspot-dot` pasa de circulo numerado a flecha/discos estilo
  Matterport (triangulo redondeado apuntando abajo + tooltip con destino). Numeracion
  retenida para accesibilidad.
- El visor no cambia como dibuja links (PSV arrows); con pitch de piso y separacion las
  flechas ya no se amontonan.

### 4. Validacion backend (FR-306)

`src/schemas/virtual_tour_schemas.py`: `HotspotInput.yaw/pitch` con `Field(ge=-pi, le=pi)`
y `(ge=-pi/2, le=pi/2)` → 422 automatico de Pydantic. Test unitario nuevo que ejercita el
rejection. Sin migraciones.

## Compatibility & Risks

- Tours ya publicados: hotspots viejos fuera de banda siguen renderizando igual (no se
  re-escriben); solo colocaciones nuevas usan la banda. Riesgo aceptado y documentado.
- Precarga de tours grandes (10+ escenas ~1–3 MB c/u): se dispara en paralelo; nginx ya
  sirve `/static/` cacheable. Si hiciera falta, limitar concurrencia es un follow-up.
- `aspect-ratio` CSS: soportado por todos los navegadores objetivo (2023+).

## Verification

- `npm run build` verde en `frontend/`.
- Suite pytest completa verde (unit + integration).
- Verificacion manual AC del spec con el tour demo publicado.
