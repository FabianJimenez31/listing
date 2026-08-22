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
- [x] T-204 `TourViewer.jsx`: modo flecha unica — solo el enlace a la escena siguiente
      (posicion+1, wrap al inicio); llegada orientada via grafo completo (FR-407).
- [x] T-205 Cadena del tour demo completada: inserts Comedor→Cocina, Cocina→Hab principal,
      Baño→Hab auxiliar, Hab auxiliar→Terraza (solo existian retornos a Sala; por eso
      4 escenas quedaban sin flecha).
- [x] T-206 `TourViewer.jsx`: fallback anti-escena-sin-flecha — sin enlace al siguiente,
      se sintetiza "continuar derecho" (opuesto a la puerta de llegada).

## Fase 3 — Cierre

- [x] T-301 Suite pytest completa verde.
- [x] T-302 `npm run build` verde.
- [x] T-303 Deploy backend+frontend y verificacion de bundle.
- [ ] T-304 Validacion visual del usuario en produccion.
- [x] T-306 Flechas de Sala principal redistribuidas uniformemente (72 grados entre cada una) y linkOverlapAngle bajado a 22.5 para no desvanecer salidas legitimas; separacion minima del editor subida a 25 grados.
- [x] T-305 Hotfix validacion visual: `rotateTo` exige yaw+pitch completos en PSV
      (crasheaba cada transicion con "Position is missing 'yaw' or 'pitch'"); llegada
      ahora con pitch 0. Boton autorotate retirado del navbar (warning, plugin ausente).
      Aclarado: los 404 de `/tour` en consola son normales (fichas sin tour publicado,
      se manejan en silencio).
