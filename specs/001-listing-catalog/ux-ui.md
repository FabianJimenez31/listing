# UX/UI — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #16.

## Resumen

Lineamientos de experiencia e interfaz para el SPA React 18 (CSR, Vite) y los paneles de agente/admin. La filosofia es **mobile-first**: se disena primero para el viewport mas estrecho y se progresa hacia pantallas grandes. Los objetivos son: (1) que la **card de propiedad** comunique foto, precio, ubicacion y badges sin scroll ni interaccion; (2) que **filtrar sea trivial** en mobile (drawer) y permanente en desktop (panel), con chips de filtros activos y limpieza en un toque; (3) **CTAs jerarquizados** (un solo CTA primario por vista); (4) **formularios cortos** con campos minimos + consentimiento explicito; (5) **estados completos** (empty/loading/error/confirmacion) con microcopy en espanol; (6) **accesibilidad** WCAG 2.1 AA basica (contraste, foco visible, alt text, labels, teclado, ARIA). Este documento define tokens, breakpoints, anatomia de componentes y las reglas `UX-R#`. Identificadores de codigo (estados, enums, campos, endpoints) en ingles segun el CONTRATO; prosa en espanol. Performance y SEO se detallan en `performance.md` y `seo.md`; aqui solo se referencian sus implicaciones de UI.

## Breakpoints y grid (mobile-first)

Tailwind-compatible. `base` = sin prefijo (aplica a todo, mobile). Cada breakpoint es `min-width` (mobile-first, nunca `max-width` salvo excepcion documentada).

| Token  | min-width | Dispositivo objetivo        | Grid de resultados | Layout filtros          | Container max |
|--------|-----------|-----------------------------|--------------------|-------------------------|---------------|
| `base` | 0px       | Mobile vertical             | 1 columna          | Drawer (off-canvas)     | 100% (16px pad) |
| `sm`   | 640px     | Mobile horizontal / phablet | 2 columnas         | Drawer                  | 100% (24px pad) |
| `md`   | 768px     | Tablet vertical             | 2 columnas         | Drawer + barra de chips | 768px         |
| `lg`   | 1024px    | Tablet horizontal / laptop  | 3 columnas         | Panel lateral fijo (sticky) | 1024px    |
| `xl`   | 1280px    | Desktop                     | 3 columnas         | Panel lateral fijo      | 1200px        |
| `2xl`  | 1536px    | Desktop ancho               | 4 columnas         | Panel lateral fijo      | 1440px        |

- Grid fluido: cards con `min-width` de 280px; el numero de columnas anterior es el objetivo, no un hard-cap (auto-fill por encima de 280px).
- Touch targets >= 44x44px en `base`/`sm`/`md`. Espaciado vertical entre acciones >= 8px.
- Imagenes responsive con `srcset`/`sizes`; relacion de aspecto fija 4:3 (card) para evitar layout shift (CLS, ver `performance.md`).

## Sistema de diseno (tokens)

Tokens semanticos (no colores crudos en componentes). Valores de referencia; el branding final puede ajustarse manteniendo ratios de contraste.

### Color (semantico + contraste)

| Token                | Uso                                  | Ratio minimo |
|----------------------|--------------------------------------|--------------|
| `--color-text`       | Texto principal sobre fondo claro    | >= 4.5:1 (AA) |
| `--color-text-muted` | Texto secundario / metadatos         | >= 4.5:1     |
| `--color-bg`         | Fondo de pagina                      | n/a          |
| `--color-surface`    | Fondo de cards/paneles               | n/a          |
| `--color-primary`    | CTA primario, links activos          | texto sobre el >= 4.5:1 |
| `--color-on-primary` | Texto sobre `--color-primary`        | >= 4.5:1     |
| `--color-danger`     | Acciones destructivas, errores       | >= 4.5:1     |
| `--color-success`    | Confirmaciones, estado PUBLISHED     | >= 3:1 (UI)  |
| `--color-warning`    | Estados PENDING/PAUSED               | >= 3:1 (UI)  |
| `--color-focus`      | Anillo de foco (outline)             | >= 3:1 vs adyacente |

Componentes de UI no textuales (bordes de inputs, iconos significativos, badges) >= 3:1 (WCAG 1.4.11). No usar color como UNICO portador de informacion (badges llevan texto/icono ademas de color — ver UX-R10).

### Tipografia

Escala fluida (`clamp`). Base 16px (nunca < 16px en inputs, evita zoom auto en iOS). Line-height cuerpo 1.5. Maximo 70 caracteres por linea en prosa.

| Rol          | Tamano (base→desktop) | Peso | Uso                          |
|--------------|-----------------------|------|------------------------------|
| `display`    | 28→40px               | 700  | Titulo pagina detalle        |
| `h1`/`h2`    | 22→32 / 18→24px       | 700  | Encabezados de seccion       |
| `body`       | 16px                  | 400  | Texto general                |
| `price`      | 18→22px               | 700  | Precio en card y detalle     |
| `caption`    | 13→14px               | 400  | Metadatos, badges, helper    |

### Espaciado, radio, sombra, motion

- Escala de espaciado: 4-8-12-16-24-32-48-64 px.
- Radios: `sm` 6px (inputs/chips), `md` 12px (cards), `full` (avatares/badges pill).
- Sombras: `card` (reposo), `card-hover` (elevacion en `:hover`/`:focus-visible` desde `lg`).
- Motion: transiciones 150–250ms `ease-out`. **Respetar `prefers-reduced-motion: reduce`** (desactivar animaciones no esenciales, skeletons sin shimmer animado).

## Navegacion (UX-R20..R24)

### Header global

Sticky en desktop, colapsable en mobile. Contenido por breakpoint:

| Elemento                 | base/sm           | md+                    |
|--------------------------|-------------------|------------------------|
| Logo (link a Home)       | Si                | Si                     |
| Buscador rapido          | Icono → overlay   | Input inline visible   |
| Menu principal           | Hamburguesa (drawer) | Links inline        |
| Acceso (login/avatar)    | Dentro del drawer | Boton/avatar visible   |
| CTA "Publicar" (AGENT+)  | En drawer         | Boton primario visible |

- VISITOR ve "Ingresar" + "Registrarse"; REGISTERED_USER+ ve avatar con menu (favoritos, perfil, salir); AGENT+/ADMIN+ ven acceso al panel correspondiente. La visibilidad de items respeta RBAC (ver `roles-permissions.md`); ocultar lo no permitido en vez de mostrarlo deshabilitado.
- El buscador rapido envia a `/api/v1/properties` (search) — ver `search-filters.md`.

### Breadcrumbs

Presentes en detalle y resultados con contexto de ubicacion. Patron:
`Inicio / {operation} / {city} / {neighborhood} / {title}`. Marcado con `<nav aria-label="breadcrumb">` y `<ol>`; ultimo item `aria-current="page"` y sin link. Generan tambien JSON-LD `BreadcrumbList` (coordinar con `seo.md`).

### Estructura de rutas (referencia UI)

| Vista              | Ruta SPA                         | Auth        |
|--------------------|----------------------------------|-------------|
| Home               | `/`                              | publica     |
| Resultados/busqueda| `/buscar` (+ query params)       | publica     |
| Detalle propiedad  | `/p/{slug}`                      | publica     |
| Login/Registro     | `/ingresar`, `/registro`         | publica     |
| Favoritos          | `/favoritos`                     | REGISTERED+ |
| Panel agente       | `/panel`                         | AGENT+      |
| Panel admin        | `/admin`                         | ADMIN+      |

## Card de propiedad (UX-R10..R14)

Componente mas critico del catalogo. Anatomia (de arriba a abajo) con elementos **siempre visibles** sin hover ni interaccion:

```
+--------------------------------------+
| [IMG main_image 4:3]                 |
|   [badge operation]  [badge featured]|  <- overlay sup. izq / sup. der
|   [badge status]            [♥ fav]  |  <- status inf. izq; favorito inf. der
+--------------------------------------+
| $ price_amount currency      [kind]  |  <- precio prominente + chip property_kind
| city · neighborhood                  |  <- ubicacion
| 3 hab · 2 baños · 1 parq · 80 m²     |  <- specs compactos (iconos + label)
| [Ver detalle]                        |  <- CTA primario (toda la card es link)
+--------------------------------------+
```

Reglas de contenido de la card:

| Elemento     | Fuente (CONTRATO)                | Regla de presentacion |
|--------------|----------------------------------|-----------------------|
| Foto         | `main_image_id` → `cdn_url`/`thumb_url` | 4:3; `alt_text` obligatorio; placeholder si falta (nunca card rota) |
| Precio       | `price_amount` (minor) + `currency` | Formatear desde minor units, separador de miles local, sufijo `/mes` si `operation_type in {RENT,TEMPORARY}` |
| Ubicacion    | `city`, `neighborhood`           | `city · neighborhood`; sin direccion exacta en card |
| Badge operacion | `operation_type` (OperationType) | "Venta"/"Alquiler"/"Temporal"; SIEMPRE visible |
| Badge destacado | `is_featured`                  | "Destacado" solo si `true`; SIEMPRE visible si aplica |
| Badge estado | `status` (PublicationStatus)     | Visible siempre que != PUBLISHED en vistas de gestion; en catalogo publico solo se listan PUBLISHED (ver UX-R13) |
| Chip kind    | `property_kind` (PropertyKind)   | "Casa"/"Apartamento"/etc. |
| Specs        | `bedrooms`,`bathrooms`,`parking_spots`,`area_total` | Iconos con label textual; omitir el que sea 0/null para lotes |
| Favorito     | `favorite:manage_own`            | Toggle corazon; solo REGISTERED_USER+; VISITOR → invita a registrarse (no se oculta, se redirige a `/ingresar`) |

Etiquetas en espanol para enums (no se traducen los valores de codigo):

- OperationType: SALE→"Venta", RENT→"Alquiler", TEMPORARY→"Temporal".
- PropertyKind: HOUSE→"Casa", APARTMENT→"Apartamento", LOT→"Lote", OFFICE→"Oficina", COMMERCIAL→"Comercial", FARM→"Finca", OTHER→"Otro".
- PublicationStatus (paneles): DRAFT→"Borrador", PENDING→"En revision", PUBLISHED→"Publicado", PAUSED→"Pausado", SOLD→"Vendido", RENTED→"Alquilado", REJECTED→"Rechazado".
- Color de badge de estado: PUBLISHED=success, PENDING/PAUSED=warning, REJECTED/DELETED=danger, DRAFT=muted, SOLD/RENTED=info.

## Filtros (UX-R30..R36)

Objetivo: filtrar sin friccion. Patron responsive:

- **base/sm/md (Drawer):** boton "Filtros" sticky (con contador de filtros activos, ej. "Filtros · 3"). Abre un drawer off-canvas a pantalla completa o lateral. Acciones fijas al pie del drawer: **"Aplicar (N resultados)"** (primario) y **"Limpiar"** (secundario). Trap de foco activo mientras esta abierto; `Esc` y overlay cierran; al cerrar, el foco vuelve al boton "Filtros".
- **lg+ (Panel lateral fijo):** panel sticky a la izquierda; los filtros aplican al cambiar (debounced 300ms para rangos/texto) o con boton "Aplicar" segun seccion. Sin trap de foco (no es modal).

### Chips de filtros activos

- Barra horizontal de chips bajo el header de resultados, **siempre visible** cuando hay >= 1 filtro activo, en todos los breakpoints.
- Cada chip muestra el filtro legible (ej. "Apartamento", "Venta", "$200M–$400M", "Chapinero") y una **X** para removerlo individualmente (target >= 44px, `aria-label="Quitar filtro {nombre}"`).
- Al final, accion **"Limpiar todo"** que resetea todos los filtros y la URL.
- Los filtros se reflejan en la query string (`?operation=sale&kind=apartment&...`) para ser compartibles y back/forward-friendly (sincroniza con `search-filters.md`).

### Catalogo de filtros (UI ↔ campos/enums)

| Filtro UI            | Control            | Campo/enum (CONTRATO)                 |
|----------------------|--------------------|---------------------------------------|
| Operacion            | Segmented/tabs     | `operation_type` (OperationType)      |
| Tipo de inmueble     | Chips multiselect  | `property_kind` (PropertyKind)        |
| Ubicacion            | Autocomplete       | `locality_id` (Location) / `city`     |
| Rango de precio      | Dual slider + inputs | `price_amount` (minor) + `currency` |
| Habitaciones         | Stepper "1+,2+,3+" | `bedrooms`                            |
| Baños                | Stepper "1+,2+"    | `bathrooms`                           |
| Parqueaderos         | Stepper            | `parking_spots`                       |
| Area (m²)            | Rango              | `area_total`                          |
| Condicion            | Chips multiselect  | `condition` (PropertyCondition)       |
| Amenidades           | Checkbox list      | `amenities` (Amenity.code)            |
| Orden                | Select             | `sort` (relevancia/precio/recientes)  |

- Inputs de precio operan en unidades mayores, agrupan miles mientras se escribe y muestran la `currency` activa; envian/leen minor units. Si el usuario invierte minimo y maximo, la UI normaliza el rango antes de buscar.
- "Sin resultados" tras filtrar → estado vacio con sugerencias (ver UX-R41).

## CTAs y jerarquia de acciones (UX-R50..R54)

Un **unico CTA primario por vista**; el resto secundario/terciario.

| Vista            | CTA primario             | Secundario(s)                          |
|------------------|--------------------------|----------------------------------------|
| Card             | "Ver detalle"            | Favorito (icono)                       |
| Detalle (publico)| `primary_cta` de Property (ej. "Contactar") | "WhatsApp", "Llamar", "Compartir", "Favorito", "Agendar visita" |
| Login            | "Ingresar"               | "Crear cuenta", "Olvide mi contraseña" |
| Form de lead     | "Enviar"                 | "Cancelar"                             |
| Panel agente     | "Publicar propiedad"     | acciones por fila (editar/pausar/…)    |

- El CTA primario del detalle se define por `primary_cta` (campo de Property). Los canales `LeadChannel` (FORM, WHATSAPP, CALL, VISIT) se exponen como acciones; cada interaccion registra metrica `MetricEventType` (CTA_CLICK, WHATSAPP_CLICK, CALL_CLICK, VISIT_REQUEST, SHARE) — ver `metrics.md`.
- Botones con etiqueta-verbo clara (no "OK"/"Aceptar" genericos en acciones con consecuencia). Estado de carga inline (spinner + "Enviando…") y disabled durante el submit para evitar doble envio.
- Iconos de accion siempre acompanados de `aria-label`; los de solo-icono nunca dependen del tooltip para usuarios de teclado/lector.

## Pagina de detalle (UX-R60..R63)

Orden mobile-first (1 columna; desde `lg`, galeria/contenido a la izquierda y panel de contacto sticky a la derecha):

1. Galeria (main + GALLERY; soporta `MediaKind` VIDEO/FLOOR_PLAN/VIRTUAL_TOUR como pestañas/iconos). Lightbox accesible (teclado, `Esc`, foco atrapado, `alt_text`).
2. Titulo + precio + badges (operacion, destacado) + ubicacion (`city · neighborhood`; direccion solo si `address_is_public=true`).
3. Specs principales (hab/baños/parq/area_total/area_built/year_built/condition).
4. Descripcion.
5. Amenidades (agrupadas por `category`).
6. Mapa (`location_point`); si `address_is_public=false` mostrar area aproximada (circulo), nunca pin exacto.
7. Panel de contacto / lead (sticky en `lg+`, al pie en mobile) con `primary_cta` + canales.
8. Relacionadas / mas de la zona.

- Visibilidad: solo `PublicationStatus=PUBLISHED` renderiza la pagina (HTTP 200). SOLD/RENTED → politica 301/410 con UI de "ya no disponible" + relacionadas (ver `seo.md`). PAUSED/REJECTED/DRAFT/DELETED → pantalla 404 amigable.

## Formularios (UX-R70..R75)

Principio: **el formulario mas corto posible**. Lead publico = campos minimos + consentimiento.

### Formulario de lead (detalle)

Campos: `name`, `phone` (o `email`; al menos uno requerido), `message` (prellenado: "Hola, me interesa esta propiedad…", editable), `channel` (segun el CTA usado). Mas:

- **Consentimiento obligatorio** (`consent_given`): checkbox NO premarcado con `consent_text` visible y link a politica de privacidad. El boton "Enviar" permanece disabled hasta marcarlo. Se persiste `consent_text` mostrado (ver `leads.md`/`security.md`).
- Validacion inline en `blur` (no en cada tecla); resumen de errores accesible (`role="alert"`, foco al primer campo invalido).
- Labels visibles SIEMPRE (no placeholder-como-label). Placeholder solo como ejemplo. `autocomplete` correcto (`name`, `tel`, `email`). Teclados moviles adecuados (`inputmode`).
- Tras enviar: confirmacion (toast/inline) "Mensaje enviado. El agente te contactara pronto." y limpieza/cierre. Manejo de error con reintento (UX-R42).

### Formularios de gestion (agente/admin)

Crear/editar propiedad puede ser largo: dividir en **pasos** (wizard) o secciones colapsables con guardado de borrador (`DRAFT`). Indicador de progreso; validacion por paso; "Guardar borrador" siempre disponible. Campos minimos para `submit_for_review` (DRAFT→PENDING) claramente marcados con asterisco y resumen de faltantes (incluye >=1 imagen, ver `property-lifecycle.md`).

## Estados de UI (UX-R40..R44)

| Estado            | Patron UI                                                                 |
|-------------------|---------------------------------------------------------------------------|
| Loading           | **Skeletons** con la forma del contenido (cards, detalle, listas), no spinner de pagina completa salvo navegacion inicial. Sin shimmer si `prefers-reduced-motion`. `aria-busy="true"` en el contenedor. |
| Vacio (empty)     | Ilustracion/icono + titulo + **sugerencias accionables** + CTA. Nunca un area en blanco. |
| Error             | Mensaje **accionable** (que paso + que hacer) + boton **"Reintentar"**. Distinguir error de red, 4xx (entrada) y 5xx (servidor). Mapear `error.code` del envelope a microcopy amigable. |
| Confirmacion      | Toast/banner de exito tras crear/editar/enviar/publicar. Mensaje breve en pasado. |
| Destructivo       | **Modal de confirmacion** para eliminar/pausar/rechazar (ver UX-R44). |
| Parcial/paginado  | "Cargar mas" o paginacion `?page=&page_size=`; mostrar `meta.total`/`total_pages`. |
| Offline           | Banner no intrusivo "Sin conexion"; reintento automatico al volver. |

### Empty states por contexto (microcopy)

| Contexto                    | Titulo                          | Sugerencia/CTA                                   |
|-----------------------------|---------------------------------|--------------------------------------------------|
| Busqueda sin resultados     | "No encontramos propiedades"    | "Prueba ampliar el rango de precio, quitar filtros o cambiar de zona." + "Limpiar filtros" |
| Favoritos vacios            | "Aun no tienes favoritos"       | "Guarda propiedades con el corazon ♥ para verlas aqui." + "Explorar" |
| Panel agente sin listings   | "Aun no has publicado nada"     | "Crea tu primera propiedad." + "Publicar propiedad" |
| Leads vacios                | "Todavia no hay contactos"      | "Cuando alguien te escriba, aparecera aqui." |

### Confirmaciones destructivas (UX-R44)

Acciones que requieren confirmacion modal explicita (titulo + consecuencia + boton danger con verbo + cancelar): `soft_delete` (eliminar), `pause`, `reject` (con campo de motivo obligatorio), `mark_sold`/`mark_rented` (irreversibles de cara al publico). El boton destructivo usa `--color-danger`; el foco inicial cae en "Cancelar" (no en el destructivo). Modal con `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, trap de foco, `Esc` cancela.

## Accesibilidad (UX-R80..R86) — WCAG 2.1 AA basico

| Area              | Regla                                                                        |
|-------------------|------------------------------------------------------------------------------|
| Contraste         | Texto >= 4.5:1 (>=3:1 para texto grande >=24px/19px-bold); UI no textual >=3:1. |
| Foco visible      | `:focus-visible` con anillo >=2px y >=3:1 de contraste; NUNCA `outline:none` sin reemplazo. |
| Teclado           | Todo operable por teclado en orden logico (DOM = visual). Sin trampas (excepto modales/drawers, que se liberan al cerrar). Skip-link "Saltar al contenido" al inicio. |
| Texto alternativo | `alt_text` obligatorio en imagenes de contenido; `alt=""` en decorativas. |
| Labels            | Todo control con `<label>` asociado o `aria-label`/`aria-labelledby`. Inputs nunca solo placeholder. |
| ARIA / semantica  | HTML semantico primero; ARIA solo donde falte (drawer/modal=`dialog`, chips removibles, `aria-live` para resultados/toasts, `aria-current` en nav). |
| Movimiento        | Respetar `prefers-reduced-motion`. Sin autoplay de carruseles/video con sonido. |
| Touch/tamano      | Targets >= 44x44px en mobile; texto reescalable hasta 200% sin perdida de contenido; viewport sin `maximum-scale=1`. |
| Idioma            | `<html lang="es">`; cambios de idioma marcados con `lang`. |

## Microcopy (espanol) — guia

- Tono: cercano, claro, sin tecnicismos. Trato de "tu". Frases cortas.
- Botones = verbo + objeto cuando aporta ("Enviar mensaje", "Ver detalle", "Guardar borrador").
- Errores = que paso + como resolver, sin culpar ("No pudimos enviar tu mensaje. Revisa tu conexion e intenta de nuevo.").
- Precios sin decimales si son enteros; con separador de miles local y `currency` explicita.
- Fechas en formato local legible ("disponible desde 1 jul 2026").
- Evitar mayusculas sostenidas y signos de exclamacion excesivos.

## Reglas (UX-R#)

| ID       | Regla |
|----------|-------|
| UX-R01   | Diseno **mobile-first**: estilos base para mobile y progresion con `min-width` (sm/md/lg/xl/2xl de la tabla de breakpoints). |
| UX-R02   | Container con `max-width` y padding por breakpoint; grid de resultados fluido (cards `min-width` 280px) — 1/2/3/4 columnas segun breakpoint. |
| UX-R03   | Touch targets >= 44x44px y texto base >= 16px en inputs (evitar zoom iOS) en mobile. |
| UX-R04   | Usar tokens semanticos de color/tipografia/espaciado; prohibido hardcodear colores en componentes. |
| UX-R05   | Respetar `prefers-reduced-motion: reduce` (sin animaciones no esenciales ni shimmer). |
| UX-R10   | La **card** muestra SIEMPRE (sin hover/interaccion): foto principal, precio, ubicacion y badges de operacion y (si aplica) destacado. |
| UX-R11   | Precio formateado desde `price_amount` (minor units) + `currency`; sufijo `/mes` para RENT/TEMPORARY; nunca float ni redondeos erroneos. |
| UX-R12   | Toda imagen de propiedad lleva `alt_text`; si falta `main_image_id` se usa placeholder (la card nunca se rompe). |
| UX-R13   | El catalogo publico lista SOLO `PublicationStatus=PUBLISHED`. En paneles de gestion el **badge de estado** es siempre visible con su color semantico. |
| UX-R14   | El badge no depende solo del color: incluye texto/icono (no usar color como unico portador de informacion). |
| UX-R15   | Toggle de **favorito** visible para REGISTERED_USER+; VISITOR es redirigido a `/ingresar` (no se oculta el control). |
| UX-R16   | Las cards destacadas del home ofrecen compartir con un boton de 44x44 independiente del enlace que abre el detalle; usa Web Share y copia el enlace como fallback. |
| UX-R20   | Navegacion simple y persistente: header (logo, buscador, menu, acceso/CTA segun RBAC) en todas las vistas publicas. |
| UX-R21   | **Breadcrumbs** en detalle y resultados con `<nav aria-label="breadcrumb">`, `<ol>` y `aria-current="page"` en el ultimo item. |
| UX-R22   | Buscador accesible desde el header en todos los breakpoints (inline en md+, overlay en mobile). |
| UX-R25   | El buscador principal muestra sugerencias contextuales desde 2 caracteres, con debounce, resultados acordes a la pestaña activa y navegacion por teclado (`ArrowUp`, `ArrowDown`, `Enter`, `Esc`). La lista muestra hasta 3 filas y permite scroll interno; "Ver todos" permanece fijo al pie. |
| UX-R23   | Items de navegacion no permitidos por RBAC se ocultan (no se muestran deshabilitados). |
| UX-R24   | Filtros y orden se reflejan en la query string (compartible, back/forward-friendly). |
| UX-R30   | Mobile/tablet: filtros en **drawer** off-canvas con foco atrapado, cierre por `Esc`/overlay y retorno de foco al disparador. |
| UX-R31   | Desktop (lg+): **panel lateral fijo** sticky de filtros, no modal. |
| UX-R32   | Boton/disparador de filtros muestra **contador de filtros activos**. |
| UX-R33   | **Chips de filtros activos** siempre visibles cuando hay >=1 filtro; cada chip removible individualmente con `aria-label` claro. |
| UX-R34   | Accion **"Limpiar filtros" / "Limpiar todo"** siempre disponible para resetear filtros y URL. |
| UX-R35   | Inputs de precio operan en unidades mayores en pantalla pero leen/escriben `price_amount` en minor units, con `currency` visible. |
| UX-R36   | El boton "Aplicar" del drawer muestra el **conteo de resultados** previo a aplicar cuando sea viable. |
| UX-R40   | **Loading** con skeletons que imitan el contenido; `aria-busy` en el contenedor; sin spinner de pagina completa salvo carga inicial. |
| UX-R41   | **Empty state** con titulo + sugerencias accionables + CTA (nunca area en blanco); busqueda vacia ofrece ampliar/limpiar filtros. |
| UX-R42   | **Error state** accionable con boton **"Reintentar"**; mapear `error.code` del envelope a microcopy amigable; distinguir red/4xx/5xx. |
| UX-R43   | **Confirmacion** de exito tras crear/editar/enviar/publicar (toast/inline, mensaje breve). |
| UX-R44   | Acciones destructivas (`soft_delete`, `pause`, `reject`, `mark_sold`, `mark_rented`) requieren **modal de confirmacion** (`role="dialog"`, `aria-modal`, foco inicial en "Cancelar", boton danger con verbo, motivo obligatorio en `reject`). |
| UX-R50   | **Un solo CTA primario por vista**; el resto secundario/terciario, con jerarquia visual clara. |
| UX-R51   | Botones de accion con etiqueta-verbo; durante submit muestran estado de carga y quedan disabled (no doble envio). |
| UX-R52   | El CTA del detalle usa `primary_cta`; cada canal (`LeadChannel`) y su clic registra el `MetricEventType` correspondiente. |
| UX-R53   | Botones solo-icono llevan `aria-label`; nunca dependen del tooltip para teclado/lectores. |
| UX-R60   | Detalle solo renderiza `PublicationStatus=PUBLISHED` (200); SOLD/RENTED → 301/410 con UI "no disponible"; otros estados → 404 amigable. |
| UX-R61   | Direccion exacta y pin de mapa solo si `address_is_public=true`; si no, area aproximada (sin pin exacto). |
| UX-R62   | Galeria/lightbox accesible: teclado, `Esc`, foco atrapado, `alt_text`; soporta `MediaKind` IMAGE/VIDEO/FLOOR_PLAN/VIRTUAL_TOUR. |
| UX-R63   | Panel de contacto sticky en lg+ y al pie en mobile, con `primary_cta` y canales de contacto. |
| UX-R70   | Formularios cortos: lead publico = campos minimos (`name`, `phone`/`email`, `message`) + consentimiento. |
| UX-R71   | **Consentimiento** (`consent_given`) obligatorio, checkbox NO premarcado, con `consent_text` visible; "Enviar" disabled hasta marcarlo. |
| UX-R72   | Labels visibles SIEMPRE; placeholder no sustituye al label; `autocomplete`/`inputmode` correctos. |
| UX-R73   | Validacion inline en `blur` con resumen accesible (`role="alert"`) y foco al primer campo invalido. |
| UX-R74   | Crear/editar propiedad en pasos/secciones con **guardar borrador** (DRAFT); marcar campos minimos para `submit_for_review` y faltantes. |
| UX-R75   | Tras enviar lead: confirmacion clara y manejo de error con reintento. |
| UX-R80   | Contraste AA: texto >=4.5:1 (>=3:1 grande), UI no textual >=3:1. |
| UX-R81   | **Foco visible** (`:focus-visible`, anillo >=2px, >=3:1); prohibido `outline:none` sin reemplazo equivalente. |
| UX-R82   | Operabilidad **total por teclado** en orden logico; skip-link al contenido; modales/drawers liberan el foco al cerrar. |
| UX-R83   | `alt_text` en imagenes de contenido; `alt=""` en decorativas. |
| UX-R84   | Todo control con label asociado o `aria-label`/`aria-labelledby`. |
| UX-R85   | HTML semantico + ARIA solo donde falte; `aria-live` para resultados/toasts; `<html lang="es">`. |
| UX-R86   | Texto reescalable hasta 200% sin perdida de contenido; viewport sin `maximum-scale=1`. |
| UX-R90   | **Microcopy en espanol**, tono cercano, trato de "tu", errores accionables; no usar color/icono ambiguo sin texto. |

## Open Questions

- **OQ-UX-01:** Branding final (paleta, logo, tipografia de marca) pendiente; los tokens de color son de referencia y deben validarse contra contraste AA al definir la marca.
- **OQ-UX-02:** Idioma unico (es) en MVP o i18n multi-idioma desde el inicio (afecta microcopy, `lang`, formato de moneda/fecha). Default asumido: es-only en MVP.
- **OQ-UX-03:** Politica visual para SOLD/RENTED (301 a relacionada vs 410 "ya no disponible") a confirmar junto con `seo.md`.
- **OQ-UX-04:** Texto exacto de `consent_text` (legal) y link a politica de privacidad pendientes de legal/`security.md`.
- **OQ-UX-05:** Soporte de modo oscuro (dark mode) en MVP — no asumido; los tokens semanticos lo habilitan a futuro sin rediseno.
