# Feature Specification: 004-tour-llegada-piso

**Feature Branch**: `feature/004-tour-llegada-piso`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Cuando cambio de espacio la nueva foto queda mirando hacia la
terraza; no me parece bien. Los spots de direccion quedan todos pegados uno encima del otro;
mejor poner los spots en el piso."

## Resumen

Dos correcciones de recorrido sobre 002/003, mas la causa raiz descubierta en los datos:

1. **Llegada orientada**: al pasar de una escena a otra (hotspot o botones), la camara llega
   a la escena nueva mirando hacia adentro — la puerta por la que entro queda a mis espaldas,
   como en Matterport. Nunca mas "aterrizar" mirando un punto fijo arbitrario (la terraza).
2. **Hotspots en el piso**: todas las flechas de navegacion se proyectan a una banda del piso,
   repartidas horizontalmente. Ninguna flota a media pared ni se apila sobre otra.
3. **Datos normalizados**: el tour demo tiene hotspots con angulos imposibles (yaw ±10.000°,
   pitch −229°) que causan exactamente el amontonamiento; se corrigen en DB y se normaliza
   todo guardado futuro.

## User Scenarios & Testing

### User Story 1 - Llegar mirando hacia adentro (P1)

Como visitante, desde la cocina hago clic en el hotspot hacia la sala: llego a la sala viendo
su interior, con la puerta de entrada detras mio.

**Why this priority**: es la correccion principal de sensacion de recorrido continuo.

**Independent Test**: entrar al tour publicado y atravesar dos hotspots consecutivos; la vista
de llegada debe mostrar contenido nuevo distinto cada vez (no siempre el mismo encuadre).

**Acceptance Scenarios**:

1. **Given** A y B con hotspots recíprocos, **When** navego A→B, **Then** la camara queda
   orientada opuesta al hotspot B→A (entrada a mi espalda).
2. **Given** B sin hotspot de retorno, **When** navego A→B o con Anterior/Siguiente,
   **Then** se conserva el comportamiento por defecto sin error.

### User Story 2 - Flechas sobre el piso (P1)

Como visitante, veo las flechas de movimiento pegadas al piso y separadas entre si, nunca
flotando a media pared ni superpuestas.

**Why this priority**: el amontonamiento hace el tour inusable.

**Independent Test**: abrir cualquier escena del tour publicado: todas las flechas comparten
la misma altura (banda de piso) y difieren en yaw.

**Acceptance Scenarios**:

1. **Given** la data historica corrupta, **After** la migracion, **Then** yaw ∈ [−180°,180°]
   y pitch ∈ [−85°,−60°] para todos los hotspots.
2. **Given** hotspots nuevos colocados en el editor, **Then** se ven en el piso igual que en
   el visor (WYSIWYG).

## Requirements

- **FR-401**: La navegacion A→B DEBE orientar la llegada al opuesto del hotspot de retorno
  B→A cuando exista (`transitionOptions` del plugin); si no existe, comportamiento default.
- **FR-402**: El visor DEBE renderizar todos los links con pitch fijo de piso (−72°),
  conservando el yaw almacenado.
- **FR-403**: El editor DEBE previsualizar los hotspots con yaw normalizado y pitch clampado
  a la banda de piso.
- **FR-404**: Todo guardado de hotspots via API DEBE normalizar angulos (wrap de yaw a
  [−180°,180°], clamp de pitch a banda) antes de persistir.
- **FR-405**: Una migracion Alembic DEBE normalizar las filas existentes de
  `virtual_tour_hotspots`.
- **FR-406**: La precarga DEBE usar `preload` del config del plugin (el per-link no existe en
  PSV v5), ademas del calentamiento ya existente.
- **FR-407**: El visor DEBE mostrar **una sola flecha por escena**: la que conduce a la escena
  siguiente en el orden definido (posicion+1, con vuelta al inicio en la ultima). Las demas
  conexiones siguen navegables via botones Anterior/Siguiente y galeria. La orientacion de
  llegada sigue usando el grafo completo de hotspots, no el subconjunto mostrado.
- **FR-408**: La UI del visor DEBE renovarse (controles glassmorphism, contador de escena,
  pestañas tipo segmented control, scrim inferior) y el aviso publico "contenido generado por
  IA" se RETIRA. Esta decision de producto sustituye el aviso permanente de 002 (FR-223);
  el acuse interno previo a publicacion (FR-216 de 002) se mantiene.

## Open Questions

- Ninguna.
