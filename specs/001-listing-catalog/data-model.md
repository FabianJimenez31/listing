# Modelo de Datos — Listing

> Detalle de specs/001-listing-catalog/. Indice en spec.md. DoD: #4.

## Resumen

Modelo de datos relacional para el sistema de listing inmobiliario sobre **PostgreSQL 16 + PostGIS + pg_trgm**. Cubre las **16 entidades** del CONTRATO con sus campos, tipos Postgres, obligatoriedad, descripcion y restricciones; relaciones (FK/M2M y cardinalidad); indices recomendados (GiST geoespacial, btree para PK/FK/slug, btree compuestos para filtros, GIN/pg_trgm para busqueda de texto); y restricciones de integridad (unique, check, FK on delete, una sola MAIN por propiedad, unique(user_id, property_id) en favorites).

Convenciones transversales aplicadas a TODAS las tablas:

- **PK** `id UUID DEFAULT gen_random_uuid()` (UUID v4 string). **FK** `<entity>_id UUID`.
- **Timestamps** `timestamptz` en UTC: `created_at NOT NULL DEFAULT now()`, `updated_at NOT NULL DEFAULT now()` (trigger de actualizacion). **Soft delete**: `deleted_at timestamptz NULL` donde aplique.
- **Dinero**: `price_amount BIGINT` en *minor units* (centavos), NUNCA float; `currency CHAR(3)` ISO 4217.
- **Enums**: se modelan como `TEXT` + `CHECK (col IN (...))` con los valores string del CONTRATO (alternativa: tipos `ENUM` nativos de Postgres; se documenta el CHECK por portabilidad y para evitar bloqueos de `ALTER TYPE`).
- **Slug regex** (validado en app y opcionalmente `CHECK`): `^[a-z0-9]+(?:-[a-z0-9]+)*$`.
- **Geografia**: `geography(POINT,4326)` para puntos; indices **GiST**.

### Diagrama ASCII de relaciones

```
                            +------------------+
                            |   Permission     |
                            +------------------+
                                   ^  M2M (role_permissions)
                                   |
              +----------+    N:1  |     1:N
   role_id    |   Role   |<--------+--------+
   +--------->+----------+                  |
   |          +----------+                  |
   |                                        |
+--+----+  owner_id (N:1)            +------+-------+
| User  +<---------------------------+   Property   +----------------------------+
+---+---+                            +------+-------+                            |
    |  ^  ^                                 | 1:N        | 1:1        | 1:N       | M2M
    |  |  | user_id (favorites)            v            v            v           v
    |  |  +-----------------+        +-----------+ +-----------+ +-------+  +-------------+
    |  |    owner_id (leads) |       |  Property | |   Seo     | | Lead  |  |PropertyAmenity|
    |  |  (agente asignado)  |       |   Image   | | Metadata  | +-------+  +------+------+
    |  |                     |       +-----------+ +-----------+                  | N:1
    |  +---------------------+              |1:1 (featured)                       v
    |  actor_id (audit, nullable)          v                                +---------+
    |                               +---------------+                       | Amenity |
    v 1:N                          | FeaturedProp. |                        +---------+
+----------+                       +---------------+
| Favorite |
+----------+        Location (self-FK parent_id)  --< Property.locality_id (N:1)
                    PropertyType (code=PropertyKind, catalogo)
                    Banner (segmentacion: target_locality_id, target_operation, target_kind)
                    PropertyView (event store: property_id N:1)  --> contadores denormalizados
                    AuditLog (append-only; actor_id->User nullable; entity_type/entity_id polimorfico)
                    SeoMetadata (entity_type/entity_id polimorfico; 1:1 con Property)
```

Cardinalidades clave: User 1:N Property (owner), Property 1:N PropertyImage, Property 1:1 SeoMetadata, Property 1:1 FeaturedProperty, Property M:N Amenity (via PropertyAmenity), Property 1:N Lead, Property 1:N Favorite, Property 1:N PropertyView, User M:N Property (via Favorite), Role M:N Permission (via role_permissions), Location 1:N Location (jerarquia self), Location 1:N Property.

---

## 1. User (`users`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK UUID v4 | PK, DEFAULT gen_random_uuid() |
| email | citext / text | Si | Correo de acceso | UNIQUE, NOT NULL, CHECK formato email |
| password_hash | text | Si | Hash de contrasena (bcrypt/argon2) | NOT NULL; nunca exponer en API |
| full_name | text | Si | Nombre completo | NOT NULL |
| phone | text | No | Telefono de contacto | E.164 recomendado |
| whatsapp | text | No | Numero WhatsApp para CTA | E.164 recomendado |
| role_id | uuid | Si | Rol asignado | FK -> roles(id) ON DELETE RESTRICT |
| is_active | boolean | Si | Cuenta activa | NOT NULL DEFAULT true |
| email_verified | boolean | Si | Email verificado | NOT NULL DEFAULT false |
| avatar_url | text | No | URL de avatar (CDN) | |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |
| updated_at | timestamptz | Si | Modif. UTC | NOT NULL DEFAULT now() |
| deleted_at | timestamptz | No | Soft delete | NULL = activo |

**Relaciones**: `role_id` N:1 -> Role. 1:N -> Property (owner_id), Favorite (user_id), Lead (owner_id, agente asignado), AuditLog (actor_id, nullable).
**Indices**: `pk_users(id)`; UNIQUE `uq_users_email(lower(email))`; btree `ix_users_role_id(role_id)`; btree parcial `ix_users_active(is_active) WHERE deleted_at IS NULL`.
**Integridad**: UNIQUE(email) case-insensitive; FK role_id ON DELETE RESTRICT (no borrar un rol con usuarios); soft delete via `deleted_at`; `is_active=false` para suspension reversible.

---

## 2. Role (`roles`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| name | text | Si | Identificador (`registered_user`,`agent`,`admin`,`superadmin`) | UNIQUE, NOT NULL |
| description | text | No | Descripcion legible | |
| is_system | boolean | Si | Rol de sistema (no editable/eliminable) | NOT NULL DEFAULT false |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |
| updated_at | timestamptz | Si | Modif. UTC | NOT NULL DEFAULT now() |

**Relaciones**: M:N -> Permission via `role_permissions(role_id, permission_id)` (PK compuesta). 1:N -> User.
**Indices**: `pk_roles(id)`; UNIQUE `uq_roles_name(name)`.
**Integridad**: UNIQUE(name); `is_system=true` bloquea delete/rename a nivel de app; jerarquia VISITOR < REGISTERED_USER < AGENT < ADMIN < SUPERADMIN se resuelve por permisos, no por columna de orden.

### Tabla puente `role_permissions`

| Campo | Tipo | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| role_id | uuid | Si | FK rol | FK -> roles(id) ON DELETE CASCADE |
| permission_id | uuid | Si | FK permiso | FK -> permissions(id) ON DELETE CASCADE |

**Integridad**: PK compuesta `(role_id, permission_id)`; ambas FK CASCADE. Indice btree `ix_role_permissions_permission(permission_id)` para consultas inversas.

---

## 3. Permission (`permissions`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| code | text | Si | Codigo `resource:action` (ej. `property:read_public`) | UNIQUE, NOT NULL, CHECK formato `^[a-z_]+:[a-z_]+$` |
| description | text | No | Descripcion del permiso | |

**Relaciones**: M:N -> Role via `role_permissions`.
**Indices**: `pk_permissions(id)`; UNIQUE `uq_permissions_code(code)`.
**Integridad**: UNIQUE(code). Catalogo semilla (CONTRATO): `property:read_public, property:read_any, property:create, property:update_own, property:update_any, property:delete_own, property:delete_any, property:pause_own, property:publish_request, property:approve, property:reject, property:feature, image:upload_own, image:manage_any, lead:read_own, lead:read_any, lead:update_status, lead:assign, favorite:manage_own, user:read, user:create, user:update, user:delete, role:assign, permission:manage, banner:manage, featured:manage, location:manage, property_type:manage, amenity:manage, metrics:read_own, metrics:read_global, audit:read, seo:manage, config:manage`.

---

## 4. Property (`properties`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| owner_id | uuid | Si | Propietario/agente responsable | FK -> users(id) ON DELETE RESTRICT |
| title | text | Si | Titulo del aviso | NOT NULL, len 5..160 |
| slug | text | Si | `{operation}-{kind}-{title-kebab}-{shortid}` | UNIQUE, NOT NULL, CHECK regex slug |
| description | text | Si | Descripcion larga | NOT NULL, len >= 20 |
| operation_type | text | Si | OperationType (`sale`,`rent`,`temporary`) | CHECK IN enum |
| property_kind | text | Si | PropertyKind (`house`,`apartment`,`lot`,`office`,`commercial`,`farm`,`other`) | CHECK IN enum |
| condition | text | Si | PropertyCondition (`new`,`used`,`remodeled`,`under_construction`) | CHECK IN enum |
| price_amount | bigint | Si | Precio en minor units (centavos) | NOT NULL, CHECK >= 0 |
| currency | char(3) | Si | ISO 4217 (`USD`,`EUR`,`COP`,`MXN`,`ARS`,`CLP`,`PEN`,`BRL`) | NOT NULL, CHECK IN enum currency |
| hoa_fees_amount | bigint | No | Expensas/admin en minor units | NULL permitido; CHECK >= 0 |
| country | text | Si | Pais | NOT NULL |
| state_province | text | Si | Departamento/Estado/Provincia | NOT NULL |
| city | text | Si | Ciudad | NOT NULL |
| locality_id | uuid | No | Localidad normalizada | FK -> locations(id) ON DELETE SET NULL |
| neighborhood | text | No | Barrio (texto libre) | |
| address | text | No | Direccion exacta (privada) | Visible solo si address_is_public |
| address_is_public | boolean | Si | Mostrar direccion al publico | NOT NULL DEFAULT false |
| location_point | geography(POINT,4326) | No | Coordenadas lat/lng | SRID 4326; indice GiST |
| area_total | numeric(12,2) | Si | Area total (m2) | NOT NULL, CHECK > 0 |
| area_built | numeric(12,2) | No | Area construida (m2) | CHECK > 0; CHECK area_built <= area_total |
| bedrooms | integer | Si | Habitaciones | NOT NULL DEFAULT 0, CHECK >= 0 |
| bathrooms | integer | Si | Banos | NOT NULL DEFAULT 0, CHECK >= 0 |
| parking_spots | integer | Si | Parqueaderos/cocheras | NOT NULL DEFAULT 0, CHECK >= 0 |
| year_built | integer | No | Antiguedad (anio construccion) | CHECK 1800 <= year_built <= extract(year from now())+1 |
| status | text | Si | PublicationStatus | CHECK IN enum; DEFAULT `draft` |
| main_image_id | uuid | No | Foto principal | FK -> property_images(id) ON DELETE SET NULL (deferrable) |
| is_featured | boolean | Si | Destacado (flag denormalizado) | NOT NULL DEFAULT false |
| primary_cta | text | No | CTA principal del detalle (ej. `whatsapp`,`form`,`call`) | |
| available_from | date | No | Disponible desde | |
| views_count | bigint | Si | Contador vistas (denormalizado) | NOT NULL DEFAULT 0, CHECK >= 0 |
| clicks_count | bigint | Si | Contador clics CTA (denormalizado) | NOT NULL DEFAULT 0, CHECK >= 0 |
| leads_count | bigint | Si | Contador leads (denormalizado) | NOT NULL DEFAULT 0, CHECK >= 0 |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |
| updated_at | timestamptz | Si | Modif. UTC | NOT NULL DEFAULT now() |
| published_at | timestamptz | No | Fecha de publicacion (set en approve) | NULL hasta PUBLISHED |
| deleted_at | timestamptz | No | Soft delete | NULL = activo |

**Relaciones**:
- `owner_id` N:1 -> User. `locality_id` N:1 -> Location. `main_image_id` 1:1 (opcional) -> PropertyImage.
- 1:N -> PropertyImage (galeria/multimedia), Lead, Favorite, PropertyView.
- 1:1 -> SeoMetadata (via entity_type='property', entity_id), FeaturedProperty.
- M:N -> Amenity via PropertyAmenity.

**Amenities / multimedia (aclaracion de modelado)**: las amenities se modelan en `property_amenities` (entidad 9), NO como columna. La galeria, video, tour virtual y plano se modelan en `property_images` con `media_kind` (entidad 5); `main_image_id` apunta a la foto principal (rol MAIN).

**Indices recomendados**:
- `pk_properties(id)`; UNIQUE `uq_properties_slug(slug)`.
- btree FKs: `ix_properties_owner(owner_id)`, `ix_properties_locality(locality_id)`, `ix_properties_main_image(main_image_id)`.
- **GiST** geoespacial: `ix_properties_location_gist USING gist(location_point)` (busqueda por radio/bounding box).
- **Compuesto de filtro frecuente**: `ix_properties_filter(operation_type, city, price_amount)` (operacion + ciudad + rango precio). Variante: `ix_properties_filter2(property_kind, operation_type, price_amount)`.
- **Parcial de publicados** (lo unico publico): `ix_properties_published(status, published_at DESC) WHERE status='published' AND deleted_at IS NULL`.
- **GIN / pg_trgm** texto: `ix_properties_title_trgm USING gin(title gin_trgm_ops)`, `ix_properties_desc_trgm USING gin(description gin_trgm_ops)` (busqueda fuzzy / ILIKE). Alternativa full-text: columna generada `tsvector` + GIN.
- Ordenamiento por destacados/metricas: `ix_properties_featured(is_featured, views_count DESC) WHERE status='published'`.

**Restricciones de integridad**:
- UNIQUE(slug); CHECKs de enums (`operation_type`, `property_kind`, `condition`, `status`, `currency`).
- CHECK monetarios: `price_amount >= 0`, `hoa_fees_amount >= 0`, `currency` valido.
- CHECK geometricos/areas: `area_total > 0`, `area_built <= area_total`.
- Coherencia operacion/estado terminal (regla de app + opcional CHECK/trigger): `status='sold'` solo si `operation_type='sale'`; `status='rented'` solo si `operation_type IN ('rent','temporary')`.
- FK owner_id ON DELETE RESTRICT (no borrar usuario con propiedades; usar soft delete). FK locality_id ON DELETE SET NULL. FK main_image_id ON DELETE SET NULL **deferrable initially deferred** (resuelve dependencia circular Property<->PropertyImage al insertar).
- Soft delete via `deleted_at`; visibilidad publica solo `status='published'` (ver property-lifecycle.md / seo.md).

---

## 5. PropertyImage (`property_images`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| property_id | uuid | Si | Propiedad dueña | FK -> properties(id) ON DELETE CASCADE |
| media_kind | text | Si | MediaKind (`image`,`video`,`floor_plan`,`virtual_tour`) | CHECK IN enum; DEFAULT `image` |
| role | text | Si | ImageRole (`main`,`gallery`) | CHECK IN enum; DEFAULT `gallery` |
| original_url | text | Si | URL original en object storage | NOT NULL |
| cdn_url | text | No | URL servida por CDN | |
| thumb_url | text | No | URL miniatura | |
| position | integer | Si | Orden en galeria | NOT NULL DEFAULT 0, CHECK >= 0 |
| width | integer | No | Ancho px | CHECK > 0 |
| height | integer | No | Alto px | CHECK > 0 |
| bytes | bigint | No | Tamano archivo | CHECK > 0 |
| content_type | text | No | MIME (`image/jpeg`,`video/mp4`...) | |
| alt_text | text | No | Texto alternativo (SEO/accesibilidad) | |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |

**Relaciones**: `property_id` N:1 -> Property. Referenciada 1:1 por `properties.main_image_id`.
**Indices**: `pk_property_images(id)`; btree `ix_property_images_property(property_id)`; btree `ix_property_images_order(property_id, position)`.
**Restricciones de integridad**:
- FK property_id ON DELETE CASCADE (borrar propiedad borra su multimedia).
- **Una sola MAIN por propiedad**: indice unico parcial
  `CREATE UNIQUE INDEX uq_property_one_main ON property_images(property_id) WHERE role='main';`
- CHECKs de enums (`media_kind`, `role`) y de dimensiones (`width`, `height`, `bytes` > 0).
- Coherencia: el `role='main'` deberia tener `media_kind='image'` (regla de app). `main_image_id` de Property debe apuntar a una fila con `role='main'` (regla de app / trigger).

---

## 6. Location (`locations`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| country | text | Si | Pais | NOT NULL |
| state_province | text | No | Departamento/Estado | |
| city | text | No | Ciudad | |
| locality | text | No | Localidad/Zona | |
| neighborhood | text | No | Barrio | |
| slug | text | Si | Slug navegable/SEO | UNIQUE, NOT NULL, CHECK regex slug |
| parent_id | uuid | No | Jerarquia (pais>estado>ciudad>localidad>barrio) | FK -> locations(id) ON DELETE SET NULL (self) |
| center_point | geography(POINT,4326) | No | Centro geografico | SRID 4326; indice GiST |
| is_active | boolean | Si | Activa para seleccion | NOT NULL DEFAULT true |

**Relaciones**: self-FK `parent_id` (jerarquia 1:N consigo misma). 1:N -> Property (`locality_id`). Referenciada por Banner (`target_locality_id`) y FeaturedProperty (`locality_id`).
**Indices**: `pk_locations(id)`; UNIQUE `uq_locations_slug(slug)`; btree `ix_locations_parent(parent_id)`; btree `ix_locations_active(is_active)`; **GiST** `ix_locations_center_gist USING gist(center_point)`; btree compuesto `ix_locations_geo(country, state_province, city)`.
**Restricciones de integridad**: UNIQUE(slug); self-FK parent_id ON DELETE SET NULL; CHECK regex slug; evitar ciclos en jerarquia (validacion de app).

---

## 7. PropertyType (`property_types`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| code | text | Si | PropertyKind (`house`,`apartment`,...) | UNIQUE, NOT NULL, CHECK IN enum PropertyKind |
| name | text | Si | Nombre legible | NOT NULL |
| slug | text | Si | Slug navegable | UNIQUE, NOT NULL, CHECK regex slug |
| icon | text | No | Identificador de icono | |
| is_active | boolean | Si | Activo en filtros/UI | NOT NULL DEFAULT true |

**Relaciones**: catalogo de referencia para `property.property_kind` (acoplado por valor de enum, no por FK rigida; el match es `property_types.code = properties.property_kind`).
**Indices**: `pk_property_types(id)`; UNIQUE `uq_property_types_code(code)`; UNIQUE `uq_property_types_slug(slug)`.
**Restricciones de integridad**: UNIQUE(code), UNIQUE(slug); CHECK code IN enum PropertyKind; CHECK regex slug.

---

## 8. Amenity (`amenities`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| code | text | Si | Codigo unico (ej. `pool`,`gym`) | UNIQUE, NOT NULL |
| name | text | Si | Nombre legible | NOT NULL |
| category | text | No | Agrupacion (ej. `interior`,`edificio`,`exterior`) | |
| icon | text | No | Identificador de icono | |
| is_active | boolean | Si | Activa en filtros/UI | NOT NULL DEFAULT true |

**Relaciones**: M:N -> Property via PropertyAmenity.
**Indices**: `pk_amenities(id)`; UNIQUE `uq_amenities_code(code)`; btree `ix_amenities_category(category)`.
**Restricciones de integridad**: UNIQUE(code).

---

## 9. PropertyAmenity (`property_amenities`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| property_id | uuid | Si | Propiedad | FK -> properties(id) ON DELETE CASCADE |
| amenity_id | uuid | Si | Amenity | FK -> amenities(id) ON DELETE CASCADE |
| value | text | No | Valor opcional (ej. cantidad, detalle) | NULL permitido |

**Relaciones**: tabla puente M:N entre Property y Amenity.
**Indices**: PK compuesta `pk_property_amenities(property_id, amenity_id)`; btree `ix_property_amenities_amenity(amenity_id)` (consulta inversa: propiedades por amenity).
**Restricciones de integridad**: **PK compuesta `(property_id, amenity_id)`** (evita duplicados); ambas FK ON DELETE CASCADE.

---

## 10. Lead (`leads`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| property_id | uuid | Si | Propiedad del interes | FK -> properties(id) ON DELETE CASCADE |
| owner_id | uuid | No | Agente asignado | FK -> users(id) ON DELETE SET NULL |
| name | text | Si | Nombre del prospecto | NOT NULL |
| email | text | No | Email del prospecto | CHECK formato email |
| phone | text | No | Telefono del prospecto | |
| message | text | No | Mensaje libre | |
| channel | text | Si | LeadChannel (`form`,`whatsapp`,`call`,`visit`) | CHECK IN enum |
| status | text | Si | LeadStatus (`new`,`contacted`,`negotiating`,`closed`,`discarded`) | CHECK IN enum; DEFAULT `new` |
| consent_given | boolean | Si | Consentimiento de datos (GDPR/habeas data) | NOT NULL DEFAULT false |
| consent_text | text | No | Texto de consentimiento aceptado | |
| source_ip | inet | No | IP origen | |
| user_agent | text | No | User-Agent del navegador | |
| utm | jsonb | No | Parametros UTM de campana | DEFAULT '{}'::jsonb |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |
| updated_at | timestamptz | Si | Modif. UTC | NOT NULL DEFAULT now() |
| contacted_at | timestamptz | No | Primer contacto | NULL hasta `contacted` |

**Relaciones**: `property_id` N:1 -> Property; `owner_id` N:1 -> User (agente asignado).
**Indices**: `pk_leads(id)`; btree `ix_leads_property(property_id)`; btree `ix_leads_owner(owner_id)`; btree `ix_leads_status(status)`; btree `ix_leads_created(created_at DESC)`; GIN `ix_leads_utm USING gin(utm)`.
**Restricciones de integridad**: FK property_id ON DELETE CASCADE; FK owner_id ON DELETE SET NULL; CHECKs de enums (`channel`, `status`); al menos un canal de contacto (regla de app: `email IS NOT NULL OR phone IS NOT NULL`); incrementa `properties.leads_count` (denormalizado).

---

## 11. Banner (`banners`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| title | text | Si | Titulo del banner | NOT NULL |
| description | text | No | Descripcion | |
| image_desktop_url | text | Si | Imagen escritorio (CDN) | NOT NULL |
| image_mobile_url | text | No | Imagen movil (mobile-first) | |
| cta_label | text | No | Texto del boton CTA | |
| cta_url | text | No | URL destino del CTA | |
| position | text | Si | BannerPosition (`home_hero`,`home_inline`,`listing_top`,`listing_inline`,`detail_sidebar`) | CHECK IN enum |
| priority | integer | Si | Prioridad/orden (mayor = primero) | NOT NULL DEFAULT 0 |
| starts_at | timestamptz | No | Inicio de vigencia | |
| ends_at | timestamptz | No | Fin de vigencia | CHECK ends_at > starts_at |
| is_active | boolean | Si | Activo | NOT NULL DEFAULT true |
| target_locality_id | uuid | No | Segmentacion por localidad | FK -> locations(id) ON DELETE SET NULL |
| target_city | text | No | Segmentacion por ciudad | |
| target_operation | text | No | Segmentacion OperationType | CHECK IN enum OperationType OR NULL |
| target_kind | text | No | Segmentacion PropertyKind | CHECK IN enum PropertyKind OR NULL |
| impressions_count | bigint | Si | Contador impresiones | NOT NULL DEFAULT 0, CHECK >= 0 |
| clicks_count | bigint | Si | Contador clics | NOT NULL DEFAULT 0, CHECK >= 0 |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |
| updated_at | timestamptz | Si | Modif. UTC | NOT NULL DEFAULT now() |

**Relaciones**: `target_locality_id` N:1 -> Location (opcional). Segmentacion adicional por valor: `target_operation` (OperationType), `target_kind` (PropertyKind), `target_city`.
**Indices**: `pk_banners(id)`; btree compuesto de seleccion activa: `ix_banners_active(position, is_active, priority DESC, starts_at, ends_at)`; btree `ix_banners_target_locality(target_locality_id)`.
**Restricciones de integridad**: CHECK enum `position`; CHECK `ends_at > starts_at` cuando ambos no nulos; CHECKs nullable de enums target; FK target_locality_id ON DELETE SET NULL. Vigencia efectiva (app): `is_active AND (starts_at IS NULL OR now()>=starts_at) AND (ends_at IS NULL OR now()<=ends_at)`.

---

## 12. Favorite (`favorites`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| user_id | uuid | Si | Usuario | FK -> users(id) ON DELETE CASCADE |
| property_id | uuid | Si | Propiedad favorita | FK -> properties(id) ON DELETE CASCADE |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |

**Relaciones**: `user_id` N:1 -> User; `property_id` N:1 -> Property. Forma el M:N User<->Property "favoritos".
**Indices**: `pk_favorites(id)`; UNIQUE `uq_favorites_user_property(user_id, property_id)`; btree `ix_favorites_user(user_id)`; btree `ix_favorites_property(property_id)`.
**Restricciones de integridad**: **UNIQUE(user_id, property_id)** (un favorito por par); ambas FK ON DELETE CASCADE.

---

## 13. FeaturedProperty (`featured_properties`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| property_id | uuid | Si | Propiedad destacada | UNIQUE, FK -> properties(id) ON DELETE CASCADE |
| scope | text | Si | FeaturedScope (`home`,`search_results`,`locality`) | CHECK IN enum |
| priority | integer | Si | Orden dentro del scope (mayor = primero) | NOT NULL DEFAULT 0 |
| locality_id | uuid | Cond. | Localidad (requerido si scope=`locality`) | FK -> locations(id) ON DELETE SET NULL |
| starts_at | timestamptz | No | Inicio de vigencia | |
| ends_at | timestamptz | No | Fin de vigencia | CHECK ends_at > starts_at |
| is_active | boolean | Si | Activo | NOT NULL DEFAULT true |
| impressions_count | bigint | Si | Contador impresiones | NOT NULL DEFAULT 0, CHECK >= 0 |
| clicks_count | bigint | Si | Contador clics | NOT NULL DEFAULT 0, CHECK >= 0 |
| created_at | timestamptz | Si | Alta UTC | NOT NULL DEFAULT now() |

**Relaciones**: `property_id` 1:1 (UNIQUE) -> Property; `locality_id` N:1 -> Location (requerido si `scope='locality'`).
**Indices**: `pk_featured_properties(id)`; UNIQUE `uq_featured_property(property_id)`; btree de seleccion: `ix_featured_scope(scope, is_active, priority DESC)`; btree `ix_featured_locality(locality_id)`.
**Restricciones de integridad**: **UNIQUE(property_id)** (una sola fila de destacado por propiedad, relacion 1:1); CHECK enum `scope`; **CHECK condicional**: `scope <> 'locality' OR locality_id IS NOT NULL`; CHECK `ends_at > starts_at`; FK property_id CASCADE, locality_id SET NULL. Mantiene `properties.is_featured` en sync (trigger/app).

---

## 14. AuditLog (`audit_logs`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| actor_id | uuid | No | Usuario que ejecuta (nullable = sistema) | FK -> users(id) ON DELETE SET NULL |
| action | text | Si | AuditAction (`create`,`update`,...,`config_change`) | CHECK IN enum |
| entity_type | text | Si | Tipo de entidad afectada (ej. `property`) | NOT NULL |
| entity_id | uuid | No | Id de la entidad afectada | |
| before | jsonb | No | Snapshot previo | DEFAULT NULL |
| after | jsonb | No | Snapshot posterior | DEFAULT NULL |
| ip | inet | No | IP origen | |
| user_agent | text | No | User-Agent | |
| created_at | timestamptz | Si | Momento del evento UTC | NOT NULL DEFAULT now() |

**Relaciones**: `actor_id` N:1 -> User (nullable). Referencia polimorfica logica via `(entity_type, entity_id)` (sin FK rigida, por ser multi-entidad y append-only).
**Indices**: `pk_audit_logs(id)`; btree `ix_audit_actor(actor_id)`; btree compuesto `ix_audit_entity(entity_type, entity_id)`; btree `ix_audit_created(created_at DESC)`; btree `ix_audit_action(action)`. GIN opcional sobre `before`/`after` si se consulta el contenido.
**Restricciones de integridad**: **Append-only** (sin UPDATE/DELETE; aplicar a nivel de permisos/trigger que rechace mutaciones); CHECK enum `action`; FK actor_id ON DELETE SET NULL (conservar el log aunque se borre el usuario). Estrategia de retencion/particionado por `created_at` (mensual) recomendada.

---

## 15. SeoMetadata (`seo_metadata`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| entity_type | text | Si | Tipo de entidad (ej. `property`,`location`) | NOT NULL |
| entity_id | uuid | Si | Id de la entidad | NOT NULL |
| slug | text | Si | Slug canonico | UNIQUE, NOT NULL, CHECK regex slug |
| meta_title | text | No | `<title>` SEO | len <= 70 recomendado |
| meta_description | text | No | meta description | len <= 160 recomendado |
| og_title | text | No | Open Graph title | |
| og_description | text | No | Open Graph description | |
| og_image_url | text | No | Open Graph image (CDN) | |
| canonical_url | text | No | URL canonica | |
| jsonld | jsonb | No | JSON-LD (schema.org) | DEFAULT '{}'::jsonb |
| robots | text | Si | Directiva robots | NOT NULL DEFAULT 'index,follow' |
| redirect_from | jsonb | No | Array de slugs viejos (301) | DEFAULT '[]'::jsonb |
| updated_at | timestamptz | Si | Modif. UTC | NOT NULL DEFAULT now() |

**Relaciones**: referencia polimorfica `(entity_type, entity_id)`; **1:1 con Property** cuando `entity_type='property'`.
**Indices**: `pk_seo_metadata(id)`; UNIQUE `uq_seo_slug(slug)`; UNIQUE `uq_seo_entity(entity_type, entity_id)`; GIN `ix_seo_redirect_from USING gin(redirect_from)` (resolver 301 por slug viejo); GIN opcional sobre `jsonld`.
**Restricciones de integridad**: UNIQUE(slug); UNIQUE(entity_type, entity_id) (un registro SEO por entidad); CHECK regex slug. `redirect_from` permite resolver redirecciones 301 desde slugs historicos (ver seo.md).

---

## 16. PropertyView (`property_views`)

| Campo | Tipo (Postgres) | Obligatorio | Descripcion | Restricciones |
|---|---|---|---|---|
| id | uuid | Si | PK | PK, DEFAULT gen_random_uuid() |
| property_id | uuid | Si | Propiedad del evento | FK -> properties(id) ON DELETE CASCADE |
| event_type | text | Si | MetricEventType (`view`,`cta_click`,`whatsapp_click`,`call_click`,`visit_request`,`share`,`favorite`) | CHECK IN enum |
| source | text | Si | ViewSource (`organic`,`search`,`featured`,`direct`,`share`) | CHECK IN enum; DEFAULT `direct` |
| session_hash | text | No | Hash de sesion (dedupe vistas) | |
| ip_hash | text | No | Hash de IP (privacidad; no IP cruda) | |
| referrer | text | No | Referrer HTTP | |
| created_at | timestamptz | Si | Momento del evento UTC | NOT NULL DEFAULT now() |

**Relaciones**: `property_id` N:1 -> Property. Es el **event store de engagement** (vistas y clics); los contadores denormalizados viven en `properties` (`views_count`, `clicks_count`, `leads_count`), `banners` y `featured_properties`.
**Indices**: `pk_property_views(id)`; btree compuesto `ix_property_views_prop_event(property_id, event_type, created_at DESC)`; btree `ix_property_views_created(created_at DESC)`; btree `ix_property_views_source(source)`. Particionado por rango de `created_at` (mensual) recomendado por volumen.
**Restricciones de integridad**: FK property_id ON DELETE CASCADE; CHECKs de enums (`event_type`, `source`); privacidad: almacenar `ip_hash`/`session_hash` (hash), nunca IP cruda (ver NFR-040). Agregacion periodica (job) actualiza contadores denormalizados.

---

## Resumen de indices geoespaciales, texto y compuestos

| Proposito | Indice | Tipo |
|---|---|---|
| Busqueda por radio/mapa de propiedades | `properties(location_point)` | GiST |
| Centro geografico de localidades | `locations(center_point)` | GiST |
| Filtro operacion+ciudad+precio | `properties(operation_type, city, price_amount)` | btree compuesto |
| Filtro tipo+operacion+precio | `properties(property_kind, operation_type, price_amount)` | btree compuesto |
| Solo publicados (visibilidad publica) | `properties(status, published_at DESC) WHERE status='published'` | btree parcial |
| Busqueda texto titulo | `properties(title gin_trgm_ops)` | GIN/pg_trgm |
| Busqueda texto descripcion | `properties(description gin_trgm_ops)` | GIN/pg_trgm |
| Unicidad de slug | `properties(slug)`, `locations(slug)`, `property_types(slug)`, `seo_metadata(slug)` | btree UNIQUE |
| Una sola MAIN por propiedad | `property_images(property_id) WHERE role='main'` | btree UNIQUE parcial |
| Un favorito por usuario+propiedad | `favorites(user_id, property_id)` | btree UNIQUE |
| Un destacado por propiedad | `featured_properties(property_id)` | btree UNIQUE |
| Resolver 301 por slug viejo | `seo_metadata(redirect_from)` | GIN |

Extensiones requeridas: `CREATE EXTENSION IF NOT EXISTS postgis; pg_trgm; citext; pgcrypto` (esta ultima para `gen_random_uuid()`; en PG16 tambien disponible nativamente).

## Open Questions

- **OQ-1 (re-revision por edicion material)**: el CONTRATO indica que "edicion material de PUBLISHED puede requerir re-revision (regla a definir en doc)". Definir que campos cuentan como material (precio, operacion, ubicacion) y si disparan transicion automatica a PENDING. Pendiente en property-lifecycle.md.
- **OQ-2 (enums nativos vs CHECK)**: se documentan enums como `TEXT + CHECK`. Confirmar si se prefieren tipos `ENUM` nativos de Postgres (mejor validacion, peor evolucion). No bloqueante para el modelo.
- **OQ-3 (FK property_kind)**: `property_types.code` se relaciona por valor con `properties.property_kind` (enum), sin FK rigida. Confirmar si se desea normalizar a FK contra `property_types(id)` en vez de enum embebido.
