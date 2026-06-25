"""Seed script: roles, permissions, property types, amenities.

Run once after `alembic upgrade head`:
    python3 scripts/seed_data.py
"""
from __future__ import annotations

import sys
import uuid
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db.engine import SessionLocal, create_tables
import src.db.models  # noqa: F401 — registers all ORM models
from src.db.models.user_models import PermissionORM, RoleORM
from src.db.models.catalog_models import PropertyTypeORM, AmenityORM


# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

PERMISSIONS: list[str] = [
    # Properties
    "property:create",
    "property:update_own",
    "property:delete_own",
    "property:read_all",
    "property:moderate",
    # Leads
    "lead:read",
    "lead:read_all",
    "lead:update_all",
    # Users & roles
    "user:read",
    "role:assign",
    # Banners & featured
    "banner:create",
    "banner:delete",
    "featured:create",
    "featured:delete",
    # Projects (developments)
    "project:create",
    "project:moderate",
    # Agencies (inmobiliarias)
    "agency:create",
    "agency:update",
    "agency:delete",
    # Partners (allies)
    "partner:create",
    "partner:delete",
    # Blog
    "post:create",
    "post:update",
    "post:delete",
    # Locations & amenities
    "location:create",
    "amenity:create",
    # Metrics & audit
    "metrics:read",
    "audit:read",
    # Site settings (branding / logo)
    "settings:manage",
]

ROLES: dict[str, list[str]] = {
    "VISITOR": [],
    "USER": ["lead:read"],
    "AGENT": [
        "property:create",
        "property:update_own",
        "property:delete_own",
        "project:create",
        "lead:read",
    ],
    "ADMIN": [
        "property:create",
        "property:update_own",
        "property:delete_own",
        "property:read_all",
        "property:moderate",
        "lead:read",
        "lead:read_all",
        "lead:update_all",
        "user:read",
        "role:assign",
        "banner:create",
        "banner:delete",
        "featured:create",
        "featured:delete",
        "project:create",
        "project:moderate",
        "agency:create",
        "agency:update",
        "agency:delete",
        "partner:create",
        "partner:delete",
        "post:create",
        "post:update",
        "post:delete",
        "location:create",
        "amenity:create",
        "metrics:read",
        "audit:read",
        "settings:manage",
    ],
    "SUPERADMIN": PERMISSIONS,  # all permissions
}

PROPERTY_TYPES: list[dict] = [
    {"code": "house",       "name": "Casa",             "slug": "casa"},
    {"code": "apartment",   "name": "Apartamento",      "slug": "apartamento"},
    {"code": "office",      "name": "Oficina",          "slug": "oficina"},
    {"code": "commercial",  "name": "Local comercial",  "slug": "local-comercial"},
    {"code": "lot",         "name": "Terreno",          "slug": "terreno"},
    {"code": "warehouse",   "name": "Bodega",           "slug": "bodega"},
    {"code": "industrial",  "name": "Nave industrial",  "slug": "nave-industrial"},
    {"code": "penthouse",   "name": "Penthouse",        "slug": "penthouse"},
    {"code": "villa",       "name": "Villa",            "slug": "villa"},
    {"code": "studio",      "name": "Departamento",     "slug": "departamento"},
]

AMENITIES: list[dict] = [
    # Servicios
    {"code": "piscina",          "name": "Piscina",            "category": "servicios"},
    {"code": "gimnasio",         "name": "Gimnasio",           "category": "servicios"},
    {"code": "spa",              "name": "Spa",                "category": "servicios"},
    {"code": "area-juegos",      "name": "Área de juegos",     "category": "servicios"},
    {"code": "salon-eventos",    "name": "Salón de eventos",   "category": "servicios"},
    {"code": "roof-garden",      "name": "Roof garden",        "category": "servicios"},
    # Seguridad
    {"code": "seguridad-24h",     "name": "Seguridad 24h",          "category": "seguridad"},
    {"code": "caseta-vigilancia", "name": "Caseta de vigilancia",   "category": "seguridad"},
    {"code": "camaras-cctv",      "name": "Cámaras CCTV",           "category": "seguridad"},
    {"code": "acceso-controlado", "name": "Acceso controlado",      "category": "seguridad"},
    # Infraestructura
    {"code": "estacionamiento",  "name": "Estacionamiento",    "category": "infraestructura"},
    {"code": "elevador",         "name": "Elevador",           "category": "infraestructura"},
    {"code": "jardin",           "name": "Jardín",             "category": "infraestructura"},
    {"code": "terraza",          "name": "Terraza",            "category": "infraestructura"},
    {"code": "bodega-extra",     "name": "Bodega extra",       "category": "infraestructura"},
    {"code": "cuarto-servicio",  "name": "Cuarto de servicio", "category": "infraestructura"},
    # Tecnología
    {"code": "fibra-optica",     "name": "Fibra óptica",       "category": "tecnologia"},
    {"code": "smart-home",       "name": "Smart home",         "category": "tecnologia"},
    {"code": "paneles-solares",  "name": "Paneles solares",    "category": "tecnologia"},
    # Bienestar
    {"code": "area-mascotas",    "name": "Área de mascotas",   "category": "bienestar"},
    {"code": "ciclopuerto",      "name": "Ciclopuerto",        "category": "bienestar"},
    {"code": "asador-bbq",       "name": "Asador / BBQ",       "category": "bienestar"},
]


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

def _upsert_permissions(db) -> dict[str, PermissionORM]:
    existing = {p.code: p for p in db.query(PermissionORM).all()}
    for code in PERMISSIONS:
        if code not in existing:
            perm = PermissionORM(id=str(uuid.uuid4()), code=code)
            db.add(perm)
            existing[code] = perm
    db.flush()
    return existing


def _upsert_roles(db, perms: dict[str, PermissionORM]) -> None:
    existing_roles = {r.name: r for r in db.query(RoleORM).all()}
    for role_name, perm_codes in ROLES.items():
        if role_name not in existing_roles:
            role = RoleORM(id=str(uuid.uuid4()), name=role_name)
            db.add(role)
            db.flush()
            existing_roles[role_name] = role
        role = existing_roles[role_name]
        existing_perm_codes = {p.code for p in role.permissions}
        for code in perm_codes:
            if code not in existing_perm_codes and code in perms:
                role.permissions.append(perms[code])


def _upsert_property_types(db) -> None:
    existing = {pt.code: pt for pt in db.query(PropertyTypeORM).all()}
    for pt in PROPERTY_TYPES:
        if pt["code"] not in existing:
            db.add(PropertyTypeORM(
                id=str(uuid.uuid4()),
                code=pt["code"],
                name=pt["name"],
                slug=pt["slug"],
            ))


def _upsert_amenities(db) -> None:
    existing = {a.code: a for a in db.query(AmenityORM).all()}
    for am in AMENITIES:
        if am["code"] not in existing:
            db.add(AmenityORM(
                id=str(uuid.uuid4()),
                code=am["code"],
                name=am["name"],
                category=am["category"],
            ))


def seed(verbose: bool = True) -> None:
    create_tables()
    db = SessionLocal()
    try:
        perms = _upsert_permissions(db)
        _upsert_roles(db, perms)
        _upsert_property_types(db)
        _upsert_amenities(db)
        db.commit()
        if verbose:
            print(f"Seeded: {len(PERMISSIONS)} perms, {len(ROLES)} roles, "
                  f"{len(PROPERTY_TYPES)} property types, {len(AMENITIES)} amenities")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
