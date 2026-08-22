# Feature Specification: 002-virtual-tours

**Feature Branch**: `feature/002-virtual-tours`

**Created**: 2026-07-31

**Status**: Implemented — pending manual end-to-end validation and deployment

**Input**: User description: "Tomar las fotos de inmuebles y proyectos, unirlas con IA y hacer tours
virtuales seleccionables desde el admin; las imagenes de tipo tour deben poder recorrerse en 3D, con
control para avanzar, retroceder e ir entre lugares."

## Resumen

Tours virtuales 360 para inmuebles y proyectos. Cada tour es un conjunto ordenado de **escenas**
(una por ambiente: sala, cocina, alcoba...), donde cada escena es una imagen **equirectangular**
navegable con el mouse/dedo, y las escenas se conectan entre si mediante **hotspots** (puntos de
navegacion) que permiten avanzar, retroceder y saltar a cualquier ambiente.

La panoramica de cada escena se obtiene por dos vias, ambas soportadas:

1. **Subida directa** de una equirectangular ya existente (camara 360, o generada fuera del sistema).
   No cuesta nada y funciona sin dependencias externas.
2. **Generacion con IA** a partir de las fotos normales que ya tiene el inmueble/proyecto en la
   galeria, via un proveedor externo conectable (**OpenAI `gpt-image-2`**, con Gemini como segundo
   proveedor posible). Opt-in por inmueble, con costo por generacion, y con estado de borrador antes
   de publicar.

El visor es **Photo Sphere Viewer** (open source, MIT) con `VirtualTourPlugin`, `MarkersPlugin` y
`GalleryPlugin`, integrado como una pestana adicional en la ficha publica.

### Decisiones de producto ya tomadas

| Decision | Valor | Motivo |
|---|---|---|
| Formato del tour | Panoramicas 360 + hotspots (no Gaussian Splatting como entrega principal) | Visor gratis y liviano, corre sin GPU, navegacion explicita avanzar/retroceder, formato reconocible por el comprador |
| Flujo de creacion | Manual: el operador elige las fotos y dispara la generacion | Control del gasto y revision antes de publicar; nada se publica automaticamente |
| Alcance | Inmuebles **y** proyectos | Ambas entidades tienen galerias de fotos |
| Estado inicial | Borrador; publicacion explicita | Un tour con artefactos de IA no debe llegar al publico sin revision |
| Cobertura angular | Panoramica **parcial** (p. ej. 180x90) por defecto; 360 completa opcional | Elimina de raiz el problema de costura y de polos (ver RC-2); el visor soporta cobertura parcial declarada |
| Proveedor de generacion | OpenAI `gpt-image-2`, calidad `medium`, salida 2:1 | Unico de los evaluados con relacion 2:1 nativa y entrada de varias imagenes de referencia |

## Restricciones que condicionan el diseno

- **RC-1 — No hay GPU en el servidor de produccion** (24 vCPU, 92 GB RAM, sin NVIDIA). Auto-hospedar
  modelos de difusion (PanoDiffusion, DiT360, LayerPano3D) o entrenar Gaussian Splatting **no es
  viable en esta maquina**. La generacion con IA es necesariamente una llamada a un servicio externo.
- **RC-2 — Ningun modelo de imagen de proposito general garantiza el empalme 360.** Los modelos
  tratan la imagen como un rectangulo con bordes, no con condicion de frontera periodica: el borde
  izquierdo no empalma con el derecho y los polos (cenit/nadir) quedan deformados. Los modelos que si
  lo resuelven (DiT360, qwen-360-diffusion) usan *circular padding* durante la difusion y son
  auto-hospedados, lo que choca con RC-1. Consecuencias de diseno:
  - la cobertura angular por defecto es **parcial** (sin wraparound, sin polos → sin artefactos);
  - el 360 completo, cuando se quiera, se logra con **doble pasada**: generar 2:1, rotar la imagen
    50% horizontalmente (`numpy.roll`, CPU), repintar la costura resultante con una segunda llamada
    de `edits`, y rotar de vuelta. Duplica el costo por escena.
- **RC-3 — El contenido generado por IA es parcialmente inventado.** El modelo alucina paredes,
  ventanas, muebles y continuidad espacial que no estan en las fotos de origen. Un tour generado
  **no es evidencia del estado real del inmueble**.
- **RC-4 — La generacion requiere credenciales externas** (`OPENAI_API_KEY`). El sistema debe ser
  plenamente funcional en modo subida-directa cuando la credencial no existe.
- **RC-5 — Limite de 1000 lineas por archivo** (constitucion del proyecto). El dominio de tours se
  divide en modulos enfocados, no en un unico archivo.

## Requisitos funcionales

### Dominio y datos

- **FR-201** — Un tour pertenece a exactamente un inmueble (`property`) o un proyecto (`project`), y
  una entidad tiene como maximo un tour.
- **FR-202** — Un tour tiene un estado: `draft` (solo visible para staff) o `published` (visible al
  publico). Un tour sin al menos una escena con panoramica valida no puede pasar a `published`.
- **FR-203** — Una escena tiene: titulo (nombre del ambiente), posicion (orden), URL de la
  panoramica, URL de miniatura, origen (`upload` o `ai`), **cobertura angular** (horizontal y
  vertical, en grados), y opcionalmente las fotos de la galeria que la originaron y el yaw/pitch
  inicial de camara.
- **FR-208** — La cobertura angular de la escena se persiste y se pasa al visor, de modo que una
  panoramica parcial se renderice con la geometria correcta y el visor limite el rango de mirada en
  vez de estirar la imagen sobre la esfera completa (RC-2).
- **FR-204** — Un hotspot conecta una escena origen con una escena destino en una posicion angular
  (yaw, pitch) sobre la panoramica de origen, con una etiqueta visible.
- **FR-205** — La escena marcada como inicial es el punto de entrada del tour; por defecto es la de
  posicion menor.
- **FR-206** — Borrar una escena elimina los hotspots que la referencian como origen o destino.
- **FR-207** — El `MediaKind.VIRTUAL_TOUR` existente se reutiliza para marcar los assets de tour en
  la galeria; no se introduce un enum paralelo.

### Panel (staff)

- **FR-210** — El formulario de inmueble y el de proyecto exponen una seccion "Tour 360" que lista
  las escenas del tour con su miniatura, titulo y origen.
- **FR-211** — El operador puede crear una escena subiendo una imagen equirectangular. El sistema
  valida que la relacion de aspecto sea aproximadamente 2:1 y advierte si no lo es.
- **FR-212** — El operador puede crear una escena seleccionando **una o varias fotos de la galeria
  existente** del mismo ambiente y disparando la generacion con IA. Las fotos se envian como imagenes
  de referencia al endpoint de edicion del proveedor.
- **FR-213** — La generacion es asincrona: la escena queda en estado `pending`, el panel refleja el
  progreso, y pasa a `ready` o `failed` sin bloquear la interfaz.
- **FR-214** — Antes de generar, la interfaz muestra el costo estimado de la operacion, el modelo, la
  calidad y si habra doble pasada de costura. La generacion requiere confirmacion explicita.
- **FR-215** — El operador puede reordenar escenas, renombrarlas, elegir la escena inicial, borrarlas
  y ubicar hotspots sobre la panoramica indicando la escena destino.
- **FR-216** — El operador publica o despublica el tour explicitamente. Publicar exige que se haya
  aceptado la advertencia de contenido generado con IA cuando el tour contiene escenas de origen `ai`.
- **FR-217** — Si `OPENAI_API_KEY` no esta configurada, la accion de generar aparece deshabilitada
  con una explicacion, y la subida directa sigue disponible.

### Ficha publica

- **FR-220** — Cuando existe un tour `published`, la ficha del inmueble/proyecto muestra una pestana
  "Tour 360" junto a Fotos y Plano. Si no existe, la pestana no se renderiza.
- **FR-221** — El visor permite: arrastrar para mirar en 360, zoom, pantalla completa, saltar entre
  ambientes por hotspot, y una galeria de miniaturas al pie para ir a cualquier ambiente directo.
- **FR-222** — El visor ofrece control explicito de **avanzar** y **retroceder** que recorre las
  escenas en el orden definido, independiente de los hotspots.
- **FR-223** — Toda escena de origen `ai` muestra de forma **permanente y visible** el aviso
  "Recreacion generada con IA — no representa medidas ni acabados reales" (ver NFR-204).
- **FR-224** — El visor carga de forma diferida: el bundle del visor y las panoramicas solo se
  descargan cuando el usuario abre la pestana del tour.

### Generacion con IA

- **FR-230** — La integracion con el proveedor esta detras de una interfaz de proveedor. Agregar otro
  proveedor no debe requerir tocar el dominio ni el panel.
- **FR-231** — Cada intento de generacion se registra con: entidad, escena, fotos de entrada, modelo,
  creditos consumidos, estado y error si aplica. Sin registro no hay forma de auditar el gasto.
- **FR-232** — La panoramica devuelta por el proveedor se **descarga y se persiste en el
  almacenamiento propio**; nunca se sirve desde la URL del proveedor (puede caducar).
- **FR-233** — La salida se pide en relacion **2:1** (`gpt-image-2` la soporta de forma nativa). Si un
  proveedor no soporta 2:1, la implementacion de ese proveedor es responsable de entregar 2:1 sin
  deformar el contenido, o de declarar la cobertura angular real de lo que entrego (FR-208).
- **FR-234** — Modelo, calidad, resolucion y activacion de la doble pasada de costura son
  configurables por variable de entorno, para poder abaratar pruebas sin cambiar codigo.
- **FR-235** — Cuando la doble pasada esta activa, la rotacion horizontal y el repintado de la costura
  ocurren en el servidor con operaciones de CPU (sin GPU, RC-1) y se registran como parte del mismo
  intento de generacion para que el costo quede atribuido a la escena (FR-231).

## Requisitos no funcionales

- **NFR-201** — El visor no debe cargarse en la ficha si el usuario no abre el tour; el peso inicial
  de la ficha no puede aumentar mas de 5 KB gzip.
- **NFR-202** — Las panoramicas se sirven optimizadas (WebP cuando el navegador lo soporta) y con
  cache de larga duracion, igual que el resto de `/static/`.
- **NFR-203** — Las URLs de panoramicas se almacenan **absolutas**, consistente con la practica
  vigente en `property_images.cdn_url` (ver aviso de migracion de dominio en CLAUDE.md).
- **NFR-204** — **Transparencia sobre contenido sintetico.** El aviso de FR-223 es un requisito
  legal-comercial, no cosmetico: presentar una recreacion de IA como si fuera el inmueble real es
  publicidad potencialmente enganosa frente al consumidor. El aviso no puede ser descartable ni
  quedar oculto tras una interaccion.
- **NFR-205** — Un fallo del proveedor externo no puede degradar la ficha publica ni el panel: los
  tours existentes siguen sirviendose y la subida directa sigue funcionando.
- **NFR-206** — La subida de panoramicas respeta el limite de tamano del nginx del contenedor
  frontend; las equirectangulares son grandes, por lo que el limite debe verificarse explicitamente
  (ver memoria: fotos >1MB dieron 413 por falta de `client_max_body_size`).

## Fuera de alcance en v1

- Recorrido 3D libre con Gaussian Splatting: descartado en v1 por RC-1 (sin GPU) y porque ningun
  proveedor de imagen entrega assets 3D.
- Generacion automatica al publicar, sin intervencion humana.
- Deteccion automatica de que fotos pertenecen al mismo ambiente.
- Medicion de distancias o generacion de planos a partir del tour.
- Backfill masivo del catalogo completo.

## Criterios de aceptacion

- **AC-201** — Con `OPENAI_API_KEY` ausente: se puede crear un tour completo de 3 escenas por
  subida directa, conectarlas con hotspots, publicarlo, y recorrerlo en la ficha publica avanzando y
  retrocediendo entre las 3 escenas.
- **AC-202** — Un tour en `draft` no es visible en la ficha publica ni expone sus panoramicas en la
  API publica.
- **AC-203** — Con la credencial configurada: seleccionar 2 fotos de galeria del mismo ambiente y
  generar produce una escena `ready` cuya panoramica esta servida desde el dominio propio, no desde
  el proveedor.
- **AC-204** — Toda escena de origen `ai` muestra el aviso de FR-223 en el visor publico, y el aviso
  sobrevive a recargar, cambiar de escena y entrar en pantalla completa.
- **AC-205** — Un fallo del proveedor (timeout, 402 sin creditos, 5xx) deja la escena en `failed` con
  el motivo legible en el panel, sin romper el tour ni perder las escenas ya generadas.
- **AC-206** — Borrar una escena intermedia no deja hotspots huerfanos apuntando a ella.
- **AC-207** — La ficha de un inmueble sin tour no descarga el bundle del visor.

## Mapa de documentos

| Documento | Contenido |
|---|---|
| [plan.md](plan.md) | Estrategia tecnica, modelo de datos, contrato del proveedor, fases |
| [tasks.md](tasks.md) | Checklist ejecutable por fases |

## Referencias externas

- Photo Sphere Viewer — VirtualTourPlugin: https://photo-sphere-viewer.js.org/plugins/virtual-tour.html
- Wrapper React: https://www.npmjs.com/package/react-photo-sphere-viewer
- OpenAI, guia de generacion de imagenes (tamanos, calidades, precios por imagen):
  https://developers.openai.com/api/docs/guides/image-generation
- Gemini, relaciones de aspecto y modelos: https://ai.google.dev/gemini-api/docs/image-generation
- Gemini, tarifario: https://ai.google.dev/gemini-api/docs/pricing
- Alternativas open source evaluadas y descartadas por RC-1 (requieren GPU): DiT360, PanoDiffusion,
  LayerPano3D, qwen-360-diffusion
- World Labs Marble: **descartado**. Su documentacion publica describe una API que no se pudo
  confirmar como accesible; validacion hecha por el usuario el 2026-07-31.
