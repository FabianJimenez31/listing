# Tasks: 003-tour-visor-matterport

**Branch**: `feature/003-tour-visor-matterport` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Convencion: `[x]` hecho · `[/]` en curso · `[ ]` pendiente.

## Fase 1 — Precarga total del visor

- [x] T-101 `TourViewer.jsx`: calentamiento explicito de todas las `pano_url` al montar
      (`new Image()`, `decoding='async'`), sin bloquear la interaccion (FR-301, NFR-301).
- [x] T-102 `TourViewer.jsx`: `preload: true` en cada link entre escenas (FR-302).

## Fase 2 — Editor fiel y hotspots Matterport

- [x] T-201 `TourHotspotPicker.jsx`: lienzo con aspect ratio real (`aspect-ratio` desde
      `scene.width/height`) y CSS sin `object-fit: fill` (FR-303).
- [x] T-202 `TourHotspotPicker.jsx`: clamp de pitch a la banda de piso [−85°, −60°] al
      colocar hotspots nuevos (FR-304).
- [x] T-203 `TourHotspotPicker.jsx`: rechazo con aviso inline si |Δyaw| < 10° y
      |Δpitch| < 15° respecto a un hotspot existente (FR-305).
- [x] T-204 `tour.css`: `.hotspot-dot` como flecha/discos estilo Matterport con tooltip
      del destino y numeracion accesible.

## Fase 3 — Backend defensivo

- [x] T-301 `virtual_tour_schemas.py`: rangos angulares en `HotspotInput`
      (yaw ∈ [−π, π], pitch ∈ [−π/2, π/2], 422 fuera de rango) (FR-306).
- [x] T-302 Test unitario del rejection de rango en el schema.

## Fase 4 — Cierre

- [x] T-401 `npm run build` verde en `frontend/`.
- [x] T-402 Suite pytest completa verde (unit + integration).
- [ ] T-403 Verificacion manual AC-1/AC-2 con el tour demo publicado.
- [x] T-404 Deploy: `docker compose build frontend backend` → `up -d frontend backend`.
- [x] T-405 Verificar el bundle servido segun CLAUDE.md.
