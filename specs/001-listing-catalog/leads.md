# Leads y Estados — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #10.

## Resumen

Este documento especifica el **sistema de leads** (contactos comerciales generados por una `Property`): captura por canal (`LeadChannel`), maquina de estados (`LeadStatus`), asignacion automatica al responsable, notificacion asincrona, panel de gestion, historial de interacciones, antispam y consentimiento de tratamiento de datos.

Un `Lead` es la unidad de demanda capturada sobre una `Property` publicada. Solo se aceptan leads sobre propiedades en estado `PUBLISHED` (ver property-lifecycle.md). El endpoint de creacion es **publico** (no requiere auth) y esta **rate-limited**. La gestion (lectura, cambio de estado, asignacion) requiere auth y permisos (ver roles-permissions.md).

Mapa de IDs de requisito (en spec.md): captura y gestion de leads = **FR-080..089**. Reglas de este documento usan el prefijo **LEAD-R#**.

```
Visitante / Usuario              Sistema Listing                     Responsable
     |                                |                                   |
     | POST /properties/{id}/leads    |                                   |
     |  (FORM/WHATSAPP/CALL/VISIT)    |                                   |
     |------------------------------->| antispam (rate limit, honeypot,   |
     |                                |  validacion, reCAPTCHA opcional)  |
     |                                | -> persiste Lead status=NEW       |
     |                                | -> asigna owner_id = agente prop. |
     |                                | -> increment property.leads_count |
     |                                | -> encola notificacion (async) ---|--> email/push/webhook
     |<-- 201 {data:{id,status:new}}  |                                   |
     |                                |        panel de leads <---------- | (gestiona estado)
```

## Modelo de datos — Lead (leads)

Entidad `Lead` del CONTRATO. PK `id` UUID v4. Timestamps UTC `timestamptz`.

| Campo | Tipo | Null | Notas / Validacion |
|---|---|---|---|
| `id` | UUID (string) | no | PK, UUID v4 generado por servidor. |
| `property_id` | UUID -> Property | no | FK a la propiedad de origen. Debe existir y estar `PUBLISHED` al crear. |
| `owner_id` | UUID -> User | si* | Agente/usuario responsable asignado. Se rellena auto al crear (ver LEAD-R10). `nullable` solo durante una ventana transitoria si la propiedad no tiene owner valido (ver Open Questions OQ-3). |
| `name` | string(120) | si** | Nombre del prospecto. Obligatorio para `FORM` y `VISIT`. |
| `email` | string(254) | si** | Email del prospecto. Formato RFC 5322 simplificado. Obligatorio para `FORM` y `VISIT` salvo que se provea `phone`. |
| `phone` | string(32) | si** | Telefono E.164 normalizado. Obligatorio para `WHATSAPP`, `CALL`; al menos uno de `email`/`phone` para `FORM`/`VISIT`. |
| `message` | text | si | Mensaje libre del prospecto. Max 2000 chars. Sanitizado (anti XSS/HTML). |
| `channel` | `LeadChannel` | no | `form` \| `whatsapp` \| `call` \| `visit`. |
| `status` | `LeadStatus` | no | Default `new`. Maquina de estados (LEAD-R20..). |
| `consent_given` | bool | no | Default `false`. Obligatorio `true` para `FORM`/`VISIT` (LEAD-R40). |
| `consent_text` | text | si | Texto exacto del aviso de privacidad aceptado (snapshot inmutable). Obligatorio cuando `consent_given=true`. |
| `source_ip` | inet/string | si | IP de origen (cruda; politica de retencion/anonimizado en security.md). |
| `user_agent` | string(512) | si | UA del cliente. |
| `utm` | json | si | Parametros de atribucion: `{utm_source,utm_medium,utm_campaign,utm_term,utm_content}`. |
| `created_at` | timestamptz | no | UTC. |
| `updated_at` | timestamptz | no | UTC, se actualiza en cada cambio. |
| `contacted_at` | timestamptz | si | Se setea al primer paso a `CONTACTED` (LEAD-R23). |

\* `owner_id` se considera obligatorio en regimen normal; ver LEAD-R10 / OQ-3.
\** Obligatoriedad condicional por canal: ver tabla "Validacion por canal".

**Indices:** `(property_id)`, `(owner_id, status)`, `(status, created_at)`, `(created_at)`, `(email)` y `(phone)` para deduplicacion/busqueda, `(source_ip, created_at)` para antispam forense. Considerar indice parcial `WHERE status IN ('new','contacted','negotiating')` para el panel.

**Campos de consentimiento + timestamp:** el momento de aceptacion del consentimiento queda registrado por `created_at` del lead (el lead se crea con el consentimiento ya dado); el contenido aceptado se congela en `consent_text`. No se permite editar `consent_text`/`consent_given` despues de creado (append-only en lo que respecta a consentimiento, LEAD-R42).

### Validacion por canal (LEAD-R01..R06)

| LEAD-R | Canal | Campos requeridos | Consentimiento | Notas |
|---|---|---|---|---|
| **LEAD-R01** | `FORM` | `name`, (`email` o `phone`), `message` recomendado | `consent_given=true` + `consent_text` **obligatorio** | Formulario web; pasa por honeypot + rate limit + reCAPTCHA opcional. |
| **LEAD-R02** | `WHATSAPP` | `phone` (E.164) | No obligatorio (interaccion saldra de la plataforma) | Click-to-chat; se registra el evento y se redirige (deep link). |
| **LEAD-R03** | `CALL` | `phone` | No obligatorio | Click-to-call / solicitud de llamada; registra intencion. |
| **LEAD-R04** | `VISIT` | `name`, (`email` o `phone`) | `consent_given=true` + `consent_text` **obligatorio** | Solicitud de visita; puede incluir fecha preferida en `message`/`utm`. |
| **LEAD-R05** | todos | `property_id` valido y propiedad `PUBLISHED` | — | Si la propiedad no esta `PUBLISHED` -> `404` (no se revela existencia). |
| **LEAD-R06** | todos | `email` formato valido; `phone` normalizable a E.164 | — | Rechazo `422` con error envelope si falla validacion. |

> Relacion con `MetricEventType` (property_view.py): los clics `whatsapp_click` y `call_click` se registran ademas como eventos de engagement en `PropertyView` (ver metrics.md). Un lead `WHATSAPP`/`CALL` y su evento de metrica son registros complementarios (intencion + analitica), no se sustituyen.

## Maquina de estados — LeadStatus (LEAD-R20..R29)

Estados (`LeadStatus`): `NEW`, `CONTACTED`, `NEGOTIATING`, `CLOSED`, `DISCARDED`.

```
            +-----------+        contact         +-------------+
 create --> |    NEW    | ---------------------> |  CONTACTED  |
            +-----------+                        +-------------+
              |     |  \                            |    |   \
        discard|    | discard                 advance|    |    \ discard
              v     v                              v  |    v     v
         +-----------+                     +-------------+   +-----------+
         | DISCARDED | <-------------------| NEGOTIATING |-->|  CLOSED   |
         +-----------+        discard      +-------------+   +-----------+
              (terminal)                      |    ^            (terminal)
                                              | close
                                              +----+ reopen (NEGOTIATING<->CONTACTED)
```

| LEAD-R | Transicion | Desde -> Hasta | Quien | Efecto / Guard |
|---|---|---|---|
| **LEAD-R20** | `create` | (nuevo) -> `NEW` | Sistema (endpoint publico) | Estado inicial siempre `new`. |
| **LEAD-R21** | `contact` | `NEW` -> `CONTACTED` | responsable / admin | Setea `contacted_at = now()` si era null (LEAD-R23). |
| **LEAD-R22** | `advance` | `CONTACTED` -> `NEGOTIATING` | responsable / admin | Avance comercial. |
| **LEAD-R23** | `close` | `CONTACTED` \| `NEGOTIATING` -> `CLOSED` | responsable / admin | Cierre exitoso. Terminal. |
| **LEAD-R24** | `discard` | `NEW` \| `CONTACTED` \| `NEGOTIATING` -> `DISCARDED` | responsable / admin | Descarte (spam, duplicado, no cualifica). Terminal. Requiere motivo (ver OQ-1). |
| **LEAD-R25** | `reopen` | `NEGOTIATING` -> `CONTACTED` | responsable / admin | Retroceso permitido dentro de pipeline activo. |
| **LEAD-R26** | (bloqueo) | `CLOSED` \| `DISCARDED` -> * | nadie | Estados terminales: no admiten transicion. Cualquier intento -> `409 conflict`. |
| **LEAD-R27** | (skip) | `NEW` -> `NEGOTIATING`/`CLOSED` directo | — | **No permitido**: debe pasar por `CONTACTED` primero. -> `422`. |

**Reglas transversales de estado:**

- **LEAD-R28**: Toda transicion valida actualiza `updated_at` y emite un registro en `AuditLog` (`action=update`, `entity_type="lead"`, con `before`/`after` del campo `status`).
- **LEAD-R29**: La transicion es idempotente solo en sentido estricto: setear el mismo estado actual es no-op (`200`, sin auditar). Cambiar a un estado no alcanzable -> `422`/`409` segun el caso.

## Asignacion automatica (LEAD-R10..R14)

| LEAD-R | Regla |
|---|---|
| **LEAD-R10** | Al crear un lead, `owner_id` se asigna automaticamente al **agente/owner de la propiedad**: `lead.owner_id = property.owner_id`. |
| **LEAD-R11** | La reasignacion manual (`lead:assign`) la pueden hacer `ADMIN`/`SUPERADMIN` (y agentes con permiso `lead:assign`, ver roles-permissions.md). Cambia `owner_id` y audita el cambio. |
| **LEAD-R12** | Si la propiedad cambia de owner posteriormente, los leads **existentes** conservan su `owner_id` original (no se reasignan retroactivamente). Solo nuevos leads van al nuevo owner. |
| **LEAD-R13** | Reglas avanzadas de round-robin / balanceo entre varios agentes de una misma cuenta: **fuera de alcance v1** (ver OQ-2). v1 = asignacion 1:1 al owner de la propiedad. |
| **LEAD-R14** | Si `property.owner_id` es null o el usuario esta inactivo/eliminado, el lead se crea con `owner_id` apuntando al fallback configurado (admin de la cuenta) o queda en cola "sin asignar" visible solo a admins (ver OQ-3). El lead **nunca** se pierde. |

## Notificacion al responsable (LEAD-R30..R35)

La notificacion es **asincrona** (no bloquea la respuesta `201` al cliente publico). Se encola un job tras persistir el lead y commitear la transaccion.

| LEAD-R | Regla |
|---|---|
| **LEAD-R30** | Al crear un lead se encola un evento `lead.created` en cola/worker (Redis/queue). El POST responde sin esperar el envio. |
| **LEAD-R31** | Canales de notificacion: **email** (al `owner` y opcionalmente al prospecto como acuse), **push** (panel/web push si el agente tiene sesion/app), y **webhook** saliente (integraciones CRM externas). Configurables por cuenta/usuario. |
| **LEAD-R32** | El payload del webhook usa el mismo error/envelope de datos del API: `{ "event":"lead.created", "data": { ...lead sin PII innecesaria... } }`. Firmar con HMAC (secreto por suscripcion); ver security.md. |
| **LEAD-R33** | Reintentos con backoff exponencial (p.ej. 1m, 5m, 30m, 2h) y `max_attempts` configurable. Fallos definitivos van a dead-letter y se registran en `AuditLog`/log de errores. |
| **LEAD-R34** | Idempotencia: el job de notificacion usa `lead.id` como clave de idempotencia para evitar duplicados ante reintentos del worker. |
| **LEAD-R35** | Eventos adicionales notificables (config): `lead.assigned` (reasignacion), `lead.status_changed`. v1 garantiza al menos `lead.created`. |

> NFR aplicable: la latencia del POST publico no debe degradarse por el envio de notificaciones (todo async). Objetivo de entrega de notificacion: best-effort < 60s p95 (ver NFR de performance en spec.md, rango NFR-010..).

## Panel de leads (LEAD-R50..R54)

Interfaz autenticada para el responsable (panel agente) y administracion (ver ux-ui.md / api-contracts.md). Lecturas restringidas por permiso: `lead:read_own` (solo `owner_id == current_user`) vs `lead:read_any` (admins).

| LEAD-R | Regla |
|---|---|
| **LEAD-R50** | Listado paginado `?page=&page_size=` con envelope estandar `{"data":[...],"meta":{...}}`. |
| **LEAD-R51** | Filtros soportados: `property_id`, `status` (multi), `channel` (multi), `owner_id` (solo admins), rango de fecha `created_from`/`created_to`, busqueda `q` (sobre `name`/`email`/`phone`). |
| **LEAD-R52** | Orden: `sort` por `created_at` (default desc), `updated_at`, `status`. |
| **LEAD-R53** | Acciones en panel: ver detalle, cambiar `status` (transiciones LEAD-R20..R29), (re)asignar (`lead:assign`), agregar nota/interaccion (ver historial). |
| **LEAD-R54** | Scoping de seguridad: un agente con solo `lead:read_own`/`lead:update_status` jamas ve ni modifica leads de otros owners; el backend filtra por `owner_id` server-side (no confiar en el front). |

## Historial de interacciones (timeline) (LEAD-R60..R62)

| LEAD-R | Regla |
|---|---|
| **LEAD-R60** | Cada lead muestra un **timeline** cronologico: creacion, cambios de estado, reasignaciones, notas del agente, intentos de notificacion. |
| **LEAD-R61** | **v1**: el timeline se deriva de `AuditLog` (filtrado por `entity_type="lead"`, `entity_id=lead.id`) + el propio `Lead` (created/contacted_at). No se introduce tabla nueva en v1. |
| **LEAD-R62** | **Futuro**: una tabla dedicada `LeadInteraction` para notas ricas, adjuntos, recordatorios y tipos de interaccion estructurados. Modelada como Open Question (OQ-4); **no** forma parte del CONTRATO de 16 entidades. |

## Antispam y abuso (LEAD-R70..R76)

Defensa en capas sobre el endpoint publico. Detalle de retencion/PII en security.md.

| LEAD-R | Mecanismo | Detalle |
|---|---|---|
| **LEAD-R70** | **Rate limiting por IP** (Redis) | Limite por ventana deslizante, p.ej. **5 leads / 10 min / IP** y **20 / hora / IP**. Excedido -> `429` con `Retry-After`. Contadores en Redis con TTL. |
| **LEAD-R71** | **Rate limiting por sesion/dispositivo** (Redis) | Clave por `session_hash`/cookie + `property_id`: evita flood al mismo anuncio (p.ej. 1 lead identico / 60s). |
| **LEAD-R72** | **Honeypot** | Campo oculto (p.ej. `website`/`company_url`) que un humano no rellena; si viene con valor -> descartar silenciosamente (responder `201` falso o `400`, ver OQ-5) y **no** persistir/notificar. |
| **LEAD-R73** | **Validacion email/telefono** | Formato (RFC/E.164), rechazo de dominios desechables (lista configurable), normalizacion. MX-check opcional async. |
| **LEAD-R74** | **reCAPTCHA opcional** | Verificacion server-side de token (v3 score o v2). Activable por config global/por-propiedad. Si esta activo y falta/invalido -> `403`. |
| **LEAD-R75** | **Deduplicacion** | Mismo `property_id`+`email`/`phone` dentro de ventana corta (p.ej. 24h) se marca como duplicado: no crea segundo lead activo (o lo crea como `DISCARDED`/merge, ver OQ-6). |
| **LEAD-R76** | **Sanitizacion** | `message`, `name` sanitizados contra XSS/inyeccion antes de persistir y de mostrar en panel. Longitudes maximas aplicadas (LEAD-R06). |

> Las claves Redis para rate limit deben ser namespaced (`lead:rl:ip:{ip}`, `lead:rl:sess:{hash}`) con TTL acorde a la ventana. El rate limiter es compartido por el subsistema general (ver performance.md/security.md).

## Consentimiento y privacidad (LEAD-R40..R45)

| LEAD-R | Regla |
|---|---|
| **LEAD-R40** | Para canales **`FORM`** y **`VISIT`** el consentimiento es **obligatorio**: `consent_given=true` y `consent_text` no vacio. Si falta -> `422` (`error.code="consent_required"`). |
| **LEAD-R41** | `consent_text` almacena el **texto exacto** mostrado al usuario (snapshot/version del aviso de privacidad), no una referencia mutable, para prueba legal. Incluir version del aviso si aplica. |
| **LEAD-R42** | Consentimiento es **inmutable** post-creacion: `consent_given`/`consent_text` no editables (LEAD-R28 audita cualquier intento bloqueado). El timestamp de consentimiento = `created_at`. |
| **LEAD-R43** | Para `WHATSAPP`/`CALL` el consentimiento formal no es obligatorio (la conversacion ocurre fuera de la plataforma), pero se registra el aviso de redireccion. |
| **LEAD-R44** | PII (`name`, `email`, `phone`, `source_ip`, `user_agent`) sujeta a politica de **retencion y minimizacion** definida en security.md: anonimizacion/borrado tras periodo configurable, soporte a derecho de supresion (DSR). |
| **LEAD-R45** | El acceso a PII de leads esta gobernado por RBAC (`lead:read_own`/`lead:read_any`); exportaciones y descargas se auditan. |

## Endpoint publico de creacion (LEAD-R80..R83)

Contrato API base `/api/v1`. Lectura/gestion en api-contracts.md; aqui el POST publico de captura.

**`POST /api/v1/properties/{property_id}/leads`** — publico, sin auth, rate-limited.

Request (FORM):
```json
{
  "name": "Maria Perez",
  "email": "maria@example.com",
  "phone": "+573001112233",
  "message": "Quisiera agendar una visita este sabado.",
  "channel": "form",
  "consent_given": true,
  "consent_text": "Autorizo el tratamiento de mis datos conforme al Aviso de Privacidad v3 (2026-01-01).",
  "utm": {"utm_source": "google", "utm_medium": "cpc", "utm_campaign": "chapinero"},
  "website": ""
}
```
- `website` = campo **honeypot** (LEAD-R72); debe llegar vacio.
- `channel` enum `LeadChannel`. `source_ip`/`user_agent` los deriva el servidor (no se confia en el body).
- Si reCAPTCHA esta activo, incluir `captcha_token` (verificado server-side, LEAD-R74).

Response `201 Created`:
```json
{ "data": { "id": "a1b2c3d4-...", "status": "new", "created_at": "2026-06-06T12:00:00Z" } }
```

| LEAD-R | Regla del endpoint |
|---|---|
| **LEAD-R80** | Solo crea lead si `property.status == PUBLISHED`; de lo contrario `404` (no revela DRAFT/PAUSED/etc.). |
| **LEAD-R81** | Aplica en orden: honeypot -> rate limit (IP/sesion) -> reCAPTCHA (si activo) -> validacion de campos/consentimiento -> persistir -> asignar owner -> incrementar `property.leads_count` -> encolar notificacion. |
| **LEAD-R82** | Respuesta minimal (solo `id`,`status`,`created_at`); **no** se filtra `owner_id`, PII de la propiedad ni datos internos. |
| **LEAD-R83** | Errores con envelope `{"error":{"code","message","details"}}`. Codigos: `404` propiedad no publicada; `422` validacion/`consent_required`; `429` rate limit (con `Retry-After`); `403` captcha invalido. |

### Gestion (resumen; detalle en api-contracts.md)

| Metodo | Ruta | Permiso | Descripcion |
|---|---|---|---|
| GET | `/api/v1/leads` | `lead:read_own` / `lead:read_any` | Listado paginado + filtros (LEAD-R50..R52). |
| GET | `/api/v1/leads/{id}` | `lead:read_own` / `lead:read_any` | Detalle + timeline (LEAD-R60). |
| PATCH | `/api/v1/leads/{id}/status` | `lead:update_status` | Transicion de estado (LEAD-R20..R29). |
| PATCH | `/api/v1/leads/{id}/assign` | `lead:assign` | Reasignacion de `owner_id` (LEAD-R11). |

## Criterios de aceptacion (mapeo)

Este documento satisface **DoD #10** (Leads y estados). Criterios verificables relacionados: **AC-10** (leads y estados implementados y verificables). Trazabilidad de requisitos: **FR-080..089** en spec.md.

- Un POST publico valido sobre propiedad `PUBLISHED` crea un `Lead` `status=new`, asignado al owner, e incrementa `leads_count` y encola notificacion. (LEAD-R05, R10, R20, R30, R81)
- Las transiciones de estado respetan la maquina (sin saltos, terminales bloqueados) y se auditan. (LEAD-R20..R29)
- `FORM`/`VISIT` sin consentimiento son rechazados `422`. (LEAD-R40)
- Antispam: honeypot, rate limit por IP/sesion, reCAPTCHA opcional operativos. (LEAD-R70..R76)
- Panel filtra por propiedad/estado/fecha con scoping de seguridad por owner. (LEAD-R50..R54)

## Open Questions

- **OQ-1**: Descarte (`DISCARDED`) — ¿se requiere un campo/motivo estructurado (`discard_reason` enum) o basta una nota en el timeline? El CONTRATO no define `discard_reason`; v1 propone capturarlo como nota auditada hasta decidir.
- **OQ-2**: Asignacion avanzada (round-robin / balanceo entre multiples agentes de una cuenta) — fuera de v1 (LEAD-R13). Definir reglas y configuracion cuando exista el concepto de "cuenta/equipo".
- **OQ-3**: Comportamiento exacto cuando `property.owner_id` es null/inactivo: ¿fallback a admin configurado vs cola "sin asignar" con `owner_id=null`? El CONTRATO marca `owner_id` como FK; confirmar si admite null transitorio (LEAD-R14).
- **OQ-4**: Tabla futura **`LeadInteraction`** (timeline rico: notas, adjuntos, recordatorios, tipos de interaccion). No esta en las 16 entidades del CONTRATO; requiere ampliacion formal del modelo antes de implementarse (LEAD-R62).
- **OQ-5**: Respuesta ante honeypot positivo: ¿`201` silencioso (engañar al bot) vs `400`? Recomendado `201` silencioso sin persistir; confirmar politica.
- **OQ-6**: Estrategia de deduplicacion (LEAD-R75): ¿ignorar duplicado, crear como `DISCARDED`, o "merge" con incremento de contador de intentos? Definir ventana y comportamiento exacto.
- **OQ-7**: Acuse de recibo al prospecto (email automatico de "hemos recibido tu solicitud") — ¿incluido en v1 o configurable por cuenta? (relacionado LEAD-R31).
