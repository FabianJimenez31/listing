# Tasks: 004-tour-llegada-piso

**Branch**: `feature/004-tour-llegada-piso` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Convencion: `[x]` hecho · `[/]` en curso · `[ ]` pendiente.

## Fase 1 — Dominio y datos

- [x] T-101 `src/virtual_tour.py`: `normalize_yaw()` + banda de piso + `normalize_floor_pitch()`.
- [x] T-102 Tests unitarios con los valores corruptos reales (yaw 10.313°, pitch −229°).
- [x] T-103 Router `replace_hotspots`: normalizar antes de persistir (FR-404).
- [x] T-104 Migracion Alembic data-only que normaliza `virtual_tour_hotspots` (FR-405).

## Fase 2 — Visor y editor

- [x] T-201 `TourViewer.jsx`: `transitionOptions` con llegada opuesta al hotspot de retorno (FR-401).
- [x] T-202 `TourViewer.jsx`: links proyectados a pitch de piso −72°; `preload: true` en config
      del plugin; quitar preload per-link (FR-402, FR-406).
- [x] T-203 `TourHotspotPicker.jsx`: preview WYSIWYG (yaw envuelto, pitch clampado) (FR-403).

## Fase 3 — Cierre

- [x] T-301 Suite pytest completa verde.
- [x] T-302 `npm run build` verde.
- [x] T-303 Deploy backend+frontend y verificacion de bundle.
- [ ] T-304 Validacion visual del usuario en produccion.
- [x] T-305 Hotfix validacion visual: `rotateTo` exige yaw+pitch completos en PSV
      (crasheaba cada transicion con "Position is missing 'yaw' or 'pitch'"); llegada
      ahora con pitch 0. Boton autorotate retirado del navbar (warning, plugin ausente).
      Aclarado: los 404 de `/tour` en consola son normales (fichas sin tour publicado,
      se manejan en silencio).
