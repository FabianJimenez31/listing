# Roles y Permisos (RBAC) — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #3.

## Resumen

Listing implementa control de acceso basado en roles (RBAC) con jerarquia lineal y permisos granulares de tipo `resource:action`. Existen 5 roles: `VISITOR`, `REGISTERED_USER`, `AGENT`, `ADMIN`, `SUPERADMIN`. La jerarquia es acumulativa por convencion de diseno (cada rol superior hereda la intencion de los inferiores), pero la autorizacion efectiva se evalua **siempre** contra el set explicito de `permission_codes` asociados al `Role` del usuario via `role_permissions` (M2M), no por nivel numerico. La unica excepcion es `SUPERADMIN`, que tiene capacidades exclusivas de gobierno (asignacion de roles, gestion de permisos y configuracion global).

Conceptos clave:
- **Ownership (alcance propio):** muchos permisos de `AGENT` aplican **solo a sus propios recursos** (`*_own`). Un recurso es "propio" cuando `Property.owner_id == user.id` (y, en cascada, sus `PropertyImage`, `Lead` asignados, `FeaturedProperty`, `SeoMetadata`). `ADMIN`/`SUPERADMIN` usan las variantes `*_any` (cualquier recurso).
- **VISITOR** (no autenticado) **no es fila en `roles`**: es el estado por defecto sin token JWT valido. Solo posee permisos publicos implicitos de lectura (`property:read_public`) y operaciones publicas no autenticadas (crear `Lead`, registrar metricas `PropertyView`).
- Lecturas publicas (catalogo, detalle de propiedades `PUBLISHED`, banners activos, destacados) **no requieren auth**.
- Toda accion privilegiada se registra en `AuditLog` (`AuditAction`).

## Roles y jerarquia

```
VISITOR  <  REGISTERED_USER  <  AGENT  <  ADMIN  <  SUPERADMIN
(anonimo)   (registered_user)   (agent)   (admin)   (superadmin)
```

| Rol | RoleName semilla | Fila en `roles` | `is_system` | Descripcion |
|-----|------------------|-----------------|-------------|-------------|
| `VISITOR` | — (no aplica) | No | — | Usuario no autenticado. Navega catalogo publico, ve detalle de propiedades `PUBLISHED`, envia leads y dispara eventos de metricas. No tiene cuenta. |
| `REGISTERED_USER` | `registered_user` | Si | true | Usuario con cuenta. Gestiona su perfil, favoritos, comparte/reporta. **No** publica propiedades. Rol por defecto en auto-registro. |
| `AGENT` | `agent` | Si | true | Agente inmobiliario. CRUD de **sus** propiedades, sube imagenes de sus propiedades, solicita publicacion, gestiona leads de sus propiedades, ve metricas propias. Sujeto a ownership. |
| `ADMIN` | `admin` | Si | true | Moderador/operador. Aprueba/rechaza publicaciones, gestiona cualquier propiedad/imagen/lead, banners, destacados, taxonomias (locations, property_types, amenities), SEO, metricas globales y audit. **No** asigna roles ni cambia config global ni gestiona permisos. |
| `SUPERADMIN` | `superadmin` | Si | true | Gobierno total. Todo lo de `ADMIN` mas asignacion de roles, gestion de permisos, gestion de usuarios completa y configuracion global del sistema. |

Notas de jerarquia:
- La "herencia" es de **diseno de catalogo de permisos** (el set de `ADMIN` es superset del de `AGENT` salvo los `*_own` que se sustituyen por `*_any`). En runtime NO se hereda implicitamente: cada `Role` lleva su lista explicita en `role_permissions`.
- Un usuario tiene **exactamente un** `role_id` (User N:1 Role). No hay multi-rol.
- `is_system=true` protege a los roles semilla de borrado/renombrado (ver RBAC-R12).

## Matriz de permisos (filas = permisos del CONTRATO, columnas = roles)

Leyenda de celda: **Si** = permitido sobre cualquier recurso aplicable · **Solo-propio** = permitido solo si el recurso pertenece al usuario (ownership) · **No** = denegado · **(publico)** = disponible sin autenticacion (VISITOR y todo rol superior). VISITOR solo puede lo marcado **(publico)**.

| Permiso (`resource:action`) | VISITOR | REGISTERED_USER | AGENT | ADMIN | SUPERADMIN |
|------------------------------|:-------:|:---------------:|:-----:|:-----:|:----------:|
| `property:read_public` | Si (publico) | Si | Si | Si | Si |
| `property:read_any` | No | No | Solo-propio¹ | Si | Si |
| `property:create` | No | No | Si | Si | Si |
| `property:update_own` | No | No | Solo-propio | Si² | Si² |
| `property:update_any` | No | No | No | Si | Si |
| `property:delete_own` | No | No | Solo-propio | Si² | Si² |
| `property:delete_any` | No | No | No | Si | Si |
| `property:pause_own` | No | No | Solo-propio | Si² | Si² |
| `property:publish_request` | No | No | Si (sobre propias) | Si | Si |
| `property:approve` | No | No | No | Si | Si |
| `property:reject` | No | No | No | Si | Si |
| `property:feature` | No | No | No | Si | Si |
| `image:upload_own` | No | No | Solo-propio | Si² | Si² |
| `image:manage_any` | No | No | No | Si | Si |
| `lead:read_own` | No | No | Solo-propio³ | Si² | Si² |
| `lead:read_any` | No | No | No | Si | Si |
| `lead:update_status` | No | No | Solo-propio³ | Si | Si |
| `lead:assign` | No | No | No | Si | Si |
| `favorite:manage_own` | No | Solo-propio | Solo-propio | Solo-propio | Solo-propio |
| `user:read` | No | Solo-propio⁴ | Solo-propio⁴ | Si | Si |
| `user:create` | No | No | No | Si⁵ | Si |
| `user:update` | No | Solo-propio⁴ | Solo-propio⁴ | Si | Si |
| `user:delete` | No | No | No | No⁶ | Si |
| `role:assign` | No | No | No | No | Si |
| `permission:manage` | No | No | No | No | Si |
| `banner:manage` | No | No | No | Si | Si |
| `featured:manage` | No | No | No | Si | Si |
| `location:manage` | No | No | No | Si | Si |
| `property_type:manage` | No | No | No | Si | Si |
| `amenity:manage` | No | No | No | Si | Si |
| `metrics:read_own` | No | No | Solo-propio | Si | Si |
| `metrics:read_global` | No | No | No | Si | Si |
| `audit:read` | No | No | No | Si | Si |
| `seo:manage` | No | No | Solo-propio⁷ | Si | Si |
| `config:manage` | No | No | No | No | Si |

Notas de la matriz:
1. `AGENT` lee el detalle administrativo (incluye estados no publicos como `DRAFT`/`PENDING`/`PAUSED`/`REJECTED`) **solo de sus propias** propiedades. Para propiedades ajenas, solo ve lo publico (`PUBLISHED`).
2. `ADMIN`/`SUPERADMIN` ejercen estas acciones sobre **cualquier** recurso via su variante `*_any` correspondiente (`property:update_any`, `property:delete_any`, `image:manage_any`, `lead:read_any`). La celda dice "Si²" para indicar que el efecto es total aunque el permiso `*_own` por si mismo seguiria limitado a lo propio.
3. "Propio" para leads = `Lead.property_id` pertenece a una `Property` cuyo `owner_id == user.id`, o `Lead.owner_id == user.id` (agente asignado). Ver RBAC-R6.
4. `user:read` / `user:update` en alcance propio = el usuario gestiona **su propio** perfil (`User.id == user.id`). No puede ver/editar perfiles de terceros.
5. `user:create` por `ADMIN` crea cuentas de roles **iguales o inferiores** a `AGENT` (no puede crear `ADMIN`/`SUPERADMIN`). Solo `SUPERADMIN` crea/eleva a `ADMIN`/`SUPERADMIN`. Ver RBAC-R9.
6. `user:delete` NO se concede a `ADMIN` (solo `SUPERADMIN`) para evitar que un admin elimine cuentas de pares o superiores. `ADMIN` puede **desactivar** (`is_active=false`) via `user:update`, no borrar.
7. `seo:manage` para `AGENT` = editar `SeoMetadata` 1:1 de **sus** propiedades. La gestion de SEO global (redirects, robots de site, SEO de banners/locations) es `ADMIN`+.

## Mapeo accion -> permiso (capacidades clave de DoD #3)

| Capacidad de negocio | Permiso requerido | Quien (efectivo) |
|----------------------|-------------------|------------------|
| Ver catalogo/detalle publico | `property:read_public` | Todos (incl. VISITOR) |
| Crear propiedad (`->DRAFT`) | `property:create` | AGENT, ADMIN, SUPERADMIN |
| Editar propiedad | `property:update_own` (propia) / `property:update_any` | AGENT(propia), ADMIN, SUPERADMIN |
| Eliminar (soft delete) propiedad | `property:delete_own` / `property:delete_any` | AGENT(propia), ADMIN, SUPERADMIN |
| Pausar / reactivar propiedad | `property:pause_own` (propia) / `property:update_any` | AGENT(propia), ADMIN, SUPERADMIN |
| Solicitar publicacion (`DRAFT->PENDING`) | `property:publish_request` | AGENT(propia), ADMIN, SUPERADMIN |
| Aprobar publicacion (`PENDING->PUBLISHED`) | `property:approve` | ADMIN, SUPERADMIN |
| Rechazar publicacion (`PENDING->REJECTED`) | `property:reject` | ADMIN, SUPERADMIN |
| Marcar destacado | `property:feature` + `featured:manage` | ADMIN, SUPERADMIN |
| Subir/gestionar imagenes | `image:upload_own` / `image:manage_any` | AGENT(propia), ADMIN, SUPERADMIN |
| Gestionar banners | `banner:manage` | ADMIN, SUPERADMIN |
| Gestionar destacados | `featured:manage` | ADMIN, SUPERADMIN |
| Gestionar usuarios | `user:read/create/update/delete` | ADMIN (limitado⁵⁶), SUPERADMIN (total) |
| Leer leads | `lead:read_own` / `lead:read_any` | AGENT(propios), ADMIN, SUPERADMIN |
| Actualizar estado de lead | `lead:update_status` | AGENT(propios), ADMIN, SUPERADMIN |
| Asignar lead a agente | `lead:assign` | ADMIN, SUPERADMIN |
| Ver metricas | `metrics:read_own` / `metrics:read_global` | AGENT(propias), ADMIN, SUPERADMIN(global) |
| Leer audit log | `audit:read` | ADMIN, SUPERADMIN |
| Gestionar taxonomias (locations/property_types/amenities) | `location:manage`, `property_type:manage`, `amenity:manage` | ADMIN, SUPERADMIN |
| Gestionar SEO | `seo:manage` | AGENT(propia⁷), ADMIN, SUPERADMIN(global) |
| Asignar/elevar roles | `role:assign` | SUPERADMIN |
| Gestionar definicion de permisos | `permission:manage` | SUPERADMIN |
| Cambiar configuracion global | `config:manage` | SUPERADMIN |
| Enviar lead (formulario/whatsapp/etc.) | — (publico, no requiere permiso) | Todos (incl. VISITOR) |
| Gestionar favoritos | `favorite:manage_own` | REGISTERED_USER+ |

## Reglas (RBAC-R#)

- **RBAC-R1 (Autorizacion explicita):** El backend autoriza cada endpoint contra el set explicito de `permission_codes` del `Role` del usuario (resuelto via `role_permissions`). NO se infiere acceso por nivel jerarquico salvo el catalogo de seed definido en este documento. Falta de permiso -> `403` con error envelope `{"error":{"code":"forbidden",...}}`.

- **RBAC-R2 (Autenticacion vs autorizacion):** Endpoints publicos (lecturas, envio de lead, eventos de metrica) no requieren JWT. Endpoints privados requieren `Authorization: Bearer <access>` valido; token ausente/invalido/expirado -> `401` `{"error":{"code":"unauthorized",...}}`. Usuario con `is_active=false` o `deleted_at != null` -> `401` aunque el token sea valido.

- **RBAC-R3 (Ownership de propiedades):** `AGENT` ejerce `property:update_own`, `property:delete_own`, `property:pause_own`, `image:upload_own`, `metrics:read_own`, `seo:manage(own)` **unicamente** cuando `Property.owner_id == user.id`. Intento sobre recurso ajeno -> `403`. `ADMIN`/`SUPERADMIN` actuan sobre cualquiera via `*_any`.

- **RBAC-R4 (Visibilidad de estados no publicos):** Solo `PUBLISHED` es visible publicamente (`200`). El detalle administrativo de propiedades en `DRAFT/PENDING/PAUSED/REJECTED` es accesible por el **owner** (`AGENT` propietario) y por `ADMIN`/`SUPERADMIN` (`property:read_any`). Para cualquier otro solicitante esos estados responden `404` (no `403`, para no revelar existencia). `SOLD/RENTED` siguen politica SEO (301/410), `DELETED` -> `404`.

- **RBAC-R5 (Maquina de estados acotada por permiso):** Cada transicion de `PublicationStatus` requiere su permiso + rol del CONTRATO: `submit_for_review` (owner, `property:publish_request`), `approve`/`reject` (`property:approve`/`property:reject`, ADMIN+), `pause`/`reactivate` (owner via `property:pause_own` o ADMIN via `property:update_any`), `mark_sold`/`mark_rented` (owner o ADMIN), `soft_delete` (owner `property:delete_own` / ADMIN `property:delete_any`), `duplicate` (quien tenga `property:create` y acceso de lectura al origen). Transicion no permitida por estado -> `409` `{"error":{"code":"invalid_transition",...}}`; no permitida por rol -> `403`.

- **RBAC-R6 (Ownership de leads):** Un `Lead` es "propio" de un `AGENT` si `Lead.owner_id == user.id` (agente asignado) **o** la `Property` referida tiene `owner_id == user.id`. `lead:read_own` y `lead:update_status` aplican solo a leads propios. `lead:assign` (re/asignar `owner_id` del lead) y `lead:read_any` son exclusivos de `ADMIN`+. El envio de un lead nuevo es publico (sin permiso) y queda con `status=NEW`.

- **RBAC-R7 (Auto-registro -> REGISTERED_USER):** El registro publico (`POST /api/v1/auth/register`) crea siempre un `User` con `role_id` del rol semilla `registered_user`, `is_active=true`, `email_verified=false`. El cliente NO puede elegir rol en el registro; cualquier campo de rol enviado se ignora. Auto-asignarse `AGENT`/`ADMIN`/`SUPERADMIN` es imposible por esta via.

- **RBAC-R8 (Promocion a AGENT):** Un `REGISTERED_USER` se convierte en `AGENT` solo por accion de un usuario con `role:assign` (SUPERADMIN) o mediante un flujo de "solicitud de agente" que un `ADMIN` aprueba y un `SUPERADMIN` confirma la asignacion de rol (la asignacion final de `role_id` requiere `role:assign`). La elevacion queda en `AuditLog` con `action=ROLE_ASSIGN`.

- **RBAC-R9 (Escalado de privilegios prohibido / no exceder el propio nivel):** Nadie puede asignar un rol **igual o superior** al suyo. `ADMIN` (sin `role:assign`) no cambia roles; si se le habilitara crear cuentas (`user:create`), solo puede crear hasta `AGENT`. Solo `SUPERADMIN` (con `role:assign`) crea/eleva a `ADMIN`/`SUPERADMIN`. Intento de elevacion no autorizada -> `403` y evento `AuditLog`.

- **RBAC-R10 (Gestion de usuarios graduada):** `user:read`/`user:update` en alcance propio = autogestion de perfil (`User.id == self`). `ADMIN`+ leen/editan cualquier perfil. **Borrado** (`user:delete`) es exclusivo de `SUPERADMIN`; `ADMIN` solo desactiva (`is_active=false`) o aplica soft delete via update controlado. `SUPERADMIN` no puede borrarse a si mismo si es el ultimo `SUPERADMIN` activo (RBAC-R13).

- **RBAC-R11 (Capacidades exclusivas de SUPERADMIN):** `role:assign`, `permission:manage`, `config:manage` y `user:delete` son privativos de `SUPERADMIN`. La modificacion de `role_permissions` (que permiso lleva cada rol) requiere `permission:manage`. La configuracion global (banners por defecto, parametros SEO de site, flags de feature, rate limits) requiere `config:manage` (DoD #20: administracion sin tocar codigo).

- **RBAC-R12 (Roles de sistema protegidos):** Los roles con `is_system=true` (`registered_user`, `agent`, `admin`, `superadmin`) no pueden renombrarse ni eliminarse; su set de permisos solo lo edita `SUPERADMIN` via `permission:manage`. Crear roles personalizados adicionales (no-sistema) tambien requiere `permission:manage`.

- **RBAC-R13 (Invariante del ultimo SUPERADMIN):** Debe existir siempre >=1 `SUPERADMIN` activo. Operaciones que dejarian el sistema sin ningun `SUPERADMIN` activo (degradar, desactivar o borrar al ultimo) se rechazan con `409` `{"error":{"code":"last_superadmin",...}}`.

- **RBAC-R14 (Auditoria obligatoria):** Toda accion privilegiada genera un `AuditLog` (append-only) con `actor_id`, `action` (`AuditAction`), `entity_type`, `entity_id`, `before`/`after`, `ip`, `user_agent`. Eventos minimos: `ROLE_ASSIGN`, `PERMISSION_CHANGE`, `CONFIG_CHANGE`, `APPROVE`, `REJECT`, `PUBLISH`, `DELETE`, `LOGIN`, `LOGOUT`. `audit:read` (ADMIN+) permite consultarlo; nadie puede mutarlo.

- **RBAC-R15 (Default deny):** Cualquier recurso/accion no cubierto explicitamente por un `permission_code` en el `Role` del usuario se **deniega** por defecto. Endpoints nuevos deben declarar su permiso requerido; sin declaracion explicita, solo `SUPERADMIN` accede.

## Seeds de role_permissions (resumen)

Set explicito por rol que la migracion/seed debe materializar en `role_permissions` (M2M). VISITOR no es fila; sus capacidades son publicas implicitas (`property:read_public` + endpoints publicos de lead/metrica).

| Rol | Permisos asignados (codigos) |
|-----|------------------------------|
| `registered_user` | `property:read_public`, `favorite:manage_own`, `user:read`(self), `user:update`(self) |
| `agent` | todo lo de `registered_user` + `property:read_any`(own), `property:create`, `property:update_own`, `property:delete_own`, `property:pause_own`, `property:publish_request`, `image:upload_own`, `lead:read_own`, `lead:update_status`(own), `metrics:read_own`, `seo:manage`(own) |
| `admin` | `property:read_public`, `property:read_any`, `property:create`, `property:update_any`, `property:delete_any`, `property:pause_own`, `property:publish_request`, `property:approve`, `property:reject`, `property:feature`, `image:manage_any`, `lead:read_any`, `lead:update_status`, `lead:assign`, `favorite:manage_own`, `user:read`, `user:create`(<=agent), `user:update`, `banner:manage`, `featured:manage`, `location:manage`, `property_type:manage`, `amenity:manage`, `metrics:read_own`, `metrics:read_global`, `audit:read`, `seo:manage` |
| `superadmin` | **todos** los permisos del CONTRATO (superset de `admin` + `user:delete`, `role:assign`, `permission:manage`, `config:manage`) |

## Open Questions

- ¿La promocion `REGISTERED_USER -> AGENT` requiere verificacion documental (KYC/licencia inmobiliaria) antes de que `SUPERADMIN` ejecute `role:assign`? (afecta flujo de RBAC-R8). Asuncion actual: aprobacion manual por `ADMIN` + asignacion por `SUPERADMIN`, sin KYC formal en MVP.
- ¿Se permite delegar `role:assign` parcial a `ADMIN` solo para crear/promover `AGENT` (sin tocar `ADMIN`/`SUPERADMIN`)? Hoy queda en `SUPERADMIN` por RBAC-R9; si se delega, requiere un permiso nuevo tipo `role:assign_agent` fuera del CONTRATO actual.
- ¿`ADMIN` debe poder ver leads ajenos de otros agentes por defecto (`lead:read_any`) o solo bajo escalamiento? Asuncion actual: `lead:read_any` activo para `ADMIN` (moderacion/soporte).
