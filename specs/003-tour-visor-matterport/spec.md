# Feature Specification: 003-tour-visor-matterport

**Feature Branch**: `feature/003-tour-visor-matterport`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Cuando se pasa de una escena a otra (ej. cocina → sala) la foto
carga en vivo; mejor precargar todo el tour de una vez, nada armado en tiempo real. Los spots
quedaron mal amontonados: hacerlos como en Matterport."

## Resumen

Dos mejoras de experiencia sobre el visor y el editor de tours virtuales (002):

1. **Precarga total**: al abrir la pestana "Tour 360" se descargan **todas** las panoramicas
   del tour, no solo la escena inicial. Saltar de la cocina a la sala (o a cualquier escena)
   debe ser instantaneo: ninguna textura se baja ni se arma al vuelo durante la navegacion.
2. **Hotspots estilo Matterport**: las flechas de navegacion se ven y se comportan como en
   Matterport — discos/flechas pegados al piso, orientados hacia la escena destino, separados
   entre si — y el editor deja de deformar la panoramica para que el punto donde el operador
   hace clic sea exactamente el punto donde aparece la flecha.

## User Scenarios & Testing

### User Story 1 - Tour completamente precargado (Priority: P1)

Como visitante de la ficha publica, abro "Tour 360" y espero unos segundos mientras carga
el tour completo; despues recorro todas las escenas (avanzar/retroceder/hotspots) sin volver
a ver ningun indicador de carga.

**Why this priority**: es la queja principal — la carga en vivo por transicion rompe la
sensacion de recorrido continuo.

**Independent Test**: abrir un tour de N escenas con la pestana Network del navegador abierta;
tras la carga inicial, navegar por todas las escenas no debe disparar ninguna descarga nueva
de imagenes.

**Acceptance Scenarios**:

1. **Given** un tour publicado de 3 escenas, **When** se abre "Tour 360", **Then** el visor
   inicia la descarga de las 3 panoramicas inmediatamente.
2. **Given** la precarga inicial termino, **When** se navega cocina → sala → habitacion,
   **Then** cada transicion es inmediata y no aparece spinner de escena.

### User Story 2 - Hotspots como Matterport (Priority: P1)

Como operador, coloco hotspots en el editor y quedan como flechas de piso estilo Matterport:
cerca del horizonte inferior, apuntando hacia el destino, sin amontonarse unas sobre otras.
Como visitante, veo flechas limpias sobre el piso y entiendo hacia donde caminar.

**Why this priority**: los hotspots amontonados hacen el recorrido inusable.

**Independent Test**: colocar dos hotspots hacia destinos distintos en el editor; ambos deben
quedar visibles, separados y anclados a la banda del piso en el visor publico.

**Acceptance Scenarios**:

1. **Given** una escena lista, **When** el operador hace clic para agregar un hotspot,
   **Then** el pitch se ajusta a la banda de piso (como Matterport) y la flecha apunta al
   destino elegido.
2. **Given** un hotspot existente, **When** se intenta colocar otro a menos de ~10 grados,
   **Then** el editor lo rechaza con aviso en lugar de apilarlos.
3. **Given** el editor abierto, **When** se muestra la panoramica, **Then** el lienzo respeta
   el aspect ratio real (sin `object-fit` deformante): un clic en la puerta de la cocina cae
   en el yaw real de esa puerta.

## Requirements

### Functional Requirements

- **FR-301**: El visor DEBE iniciar la descarga de todas las panoramicas del tour al montarse
  (calentamiento explicito + `preload` de PSV), no al navegar.
- **FR-302**: Cada enlace entre escenas DEBE marcarse `preload` para que PSV mantenga las
  texturas vecinas listas incluso si falla el calentamiento inicial parcialmente.
- **FR-303**: El editor DEBE presentar la panoramica sin distorsion (aspect ratio real) de modo
  que clic ↔ (yaw, pitch) coincidan con la geometria del visor.
- **FR-304**: Al colocar un hotspot, su pitch DEBE ajustarse a la banda de piso configurable
  (por defecto −60°..−85°), imitando las flechas de Matterport.
- **FR-305**: El editor DEBE rechazar un nuevo hotspot cuya separacion angular con uno existente
  sea menor a un minimo configurable (por defecto 10° de yaw y 15° de pitch), con mensaje claro.
- **FR-306**: La API DEBE validar rangos defensivos (yaw ∈ [−180°, 180°], pitch ∈ [−90°, 90°])
  rechazando valores fuera de rango con 422.

### Non-Functional Requirements

- **NFR-301**: La precarga no debe bloquear la interaccion: el usuario puede moverse por la
  escena inicial mientras el resto descarga en segundo plano.
- **NFR-302**: El bundle del visor sigue siendo lazy (sin crecer el chunk inicial).

## Open Questions

- Ninguna pendiente: la banda de piso y los minimos de separacion son configurables y quedan
  como constantes en el editor.
