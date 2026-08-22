# Tasks: 004-tour-llegada-piso

**Branch**: `feature/004-tour-llegada-piso` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Convencion: `[x]` hecho · `[/]` en curso · `[ ]` pendiente.

## Fase 1 — Dominio y datos

- [ ] T-101 `src/virtual_tour.py`: `normalize_yaw()` + banda de piso + `normalize_floor_pitch()`.
- [ ] T-102 Tests unitarios con los valores corruptos reales (yaw 10.313°, pitch −229°).
- [ ] T-103 Router `replace_hotspots`: normalizar antes de persistir (FR-404).
- [ ] T-104 Migracion Alembic data-only que normaliza `virtual_tour_hotspots` (FR-405).

## Fase 2 — Visor y editor

- [ ] T-201 `TourViewer.jsx`: `transitionOptions` con llegada opuesta al hotspot de retorno (FR-401).
- [ ] T-202 `TourViewer.jsx`: links proyectados a pitch de piso −72°; `preload: true` en config
      del plugin; quitar preload per-link (FR-402, FR-406).
- [ ] T-203 `TourHotspotPicker.jsx`: preview WYSIWYG (yaw envuelto, pitch clampado) (FR-403).

## Fase 3 — Cierre

- [ ] T-301 Suite pytest completa verde.
- [ ] T-302 `npm run build` verde.
- [ ] T-303 Deploy backend+frontend y verificacion de bundle.
- [ ] T-304 Validacion visual del usuario en produccion.
