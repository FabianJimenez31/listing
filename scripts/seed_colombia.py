"""Seed Colombia: jerarquía de ubicaciones Bogotá + propiedades demo publicadas.

Ejecutar después de seed_data.py (requiere roles y property_types ya sembrados):
    python3 scripts/seed_colombia.py
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import src.db.models  # noqa: F401
from src.db.engine import SessionLocal, create_tables
from src.db.models.location_models import LocationORM
from src.db.models.property_models import PropertyORM
from src.db.models.user_models import RoleORM, UserORM
from src.auth.password import hash_password

# ---------------------------------------------------------------------------
# Jerarquía de ubicaciones (nivel → slug → datos)
# ---------------------------------------------------------------------------
LOCATIONS: list[dict] = [
    # País
    {"slug": "colombia",     "name": "Colombia",       "level": "country",   "parent": None,        "lat": 4.5709,  "lng": -74.2973},
    # Departamento
    {"slug": "bogota-dc",    "name": "Bogotá D.C.",    "level": "state",     "parent": "colombia",  "lat": 4.7110,  "lng": -74.0721},
    # Ciudad
    {"slug": "bogota",       "name": "Bogotá",         "level": "city",      "parent": "bogota-dc", "lat": 4.7110,  "lng": -74.0721},
    # Localidades / barrios con coordenadas reales
    {"slug": "chapinero",    "name": "Chapinero",      "level": "locality",  "parent": "bogota",    "lat": 4.6432,  "lng": -74.0664},
    {"slug": "usaquen",      "name": "Usaquén",        "level": "locality",  "parent": "bogota",    "lat": 4.6941,  "lng": -74.0314},
    {"slug": "el-chico",     "name": "El Chico",       "level": "locality",  "parent": "bogota",    "lat": 4.6588,  "lng": -74.0557},
    {"slug": "la-candelaria","name": "La Candelaria",  "level": "locality",  "parent": "bogota",    "lat": 4.5981,  "lng": -74.0761},
    {"slug": "zona-rosa",    "name": "Zona Rosa",      "level": "locality",  "parent": "bogota",    "lat": 4.6669,  "lng": -74.0533},
    {"slug": "teusaquillo",  "name": "Teusaquillo",    "level": "locality",  "parent": "bogota",    "lat": 4.6379,  "lng": -74.0896},
]

# ---------------------------------------------------------------------------
# Usuario demo agente
# ---------------------------------------------------------------------------
DEMO_AGENT = {
    "email":      "agente@listing.co",
    "password":   "Demo1234!",
    "full_name":  "Agente Demo",
    "phone":      "+573001234567",
}

# ---------------------------------------------------------------------------
# Propiedades demo (precios en centavos COP)
# ---------------------------------------------------------------------------
# 1 COP = 100 centavos  →  350.000.000 COP = 35.000.000.000 centavos
DEMO_PROPERTIES: list[dict] = [
    {
        "slug":            "venta-apartamento-chapinero-001",
        "title":           "Apartamento moderno en Chapinero",
        "description":     (
            "Hermoso apartamento de 3 habitaciones en el corazón de Chapinero, "
            "a 5 minutos de la Zona Rosa. Acabados de lujo, cocina integral, "
            "balcón con vista a los cerros y parqueadero cubierto. "
            "Conjunto cerrado con portería 24h y gimnasio."
        ),
        "operation_type":  "sale",
        "property_kind":   "apartment",
        "condition":       "new",
        "price_amount":    35_000_000_000,   # 350.000.000 COP
        "currency":        "COP",
        "bedrooms":        3,
        "bathrooms":       2,
        "parking_spots":   1,
        "total_area_m2":   85.0,
        "built_area_m2":   80.0,
        "address_street":  "Cra 13 # 63-45, Chapinero, Bogotá",
        "contact_phone":   "+573001234567",
        "contact_whatsapp":"+573001234567",
        "location_slug":   "chapinero",
        "type_code":       "apartment",
    },
    {
        "slug":            "venta-casa-usaquen-001",
        "title":           "Casa colonial en Usaquén con jardín",
        "description":     (
            "Espectacular casa colonial de 4 habitaciones en el exclusivo barrio de Usaquén. "
            "Amplio jardín interior, sala de estar con chimenea, cocina gourmet y "
            "cuarto de servicio. Garaje para 2 vehículos. A metros del parque de Usaquén "
            "y la plaza de mercado."
        ),
        "operation_type":  "sale",
        "property_kind":   "house",
        "condition":       "used",
        "price_amount":    85_000_000_000,   # 850.000.000 COP
        "currency":        "COP",
        "bedrooms":        4,
        "bathrooms":       3,
        "parking_spots":   2,
        "total_area_m2":   220.0,
        "built_area_m2":   200.0,
        "address_street":  "Cll 119A # 6-20, Usaquén, Bogotá",
        "contact_phone":   "+573001234567",
        "contact_whatsapp":"+573001234567",
        "location_slug":   "usaquen",
        "type_code":       "house",
    },
    {
        "slug":            "arriendo-apartamento-chico-001",
        "title":           "Apartamento en arriendo - El Chico",
        "description":     (
            "Luminoso apartamento de 2 habitaciones en El Chico, uno de los sectores "
            "más cotizados de Bogotá. Piso alto con excelente iluminación natural, "
            "sala-comedor amplio, cocina abierta y closets empotrados. "
            "Edificio con portería, salón comunal y zona de BBQ."
        ),
        "operation_type":  "rent",
        "property_kind":   "apartment",
        "condition":       "remodeled",
        "price_amount":    350_000_000,      # 3.500.000 COP/mes
        "currency":        "COP",
        "bedrooms":        2,
        "bathrooms":       2,
        "parking_spots":   1,
        "total_area_m2":   65.0,
        "built_area_m2":   62.0,
        "address_street":  "Cra 9 # 97-25, El Chico, Bogotá",
        "contact_phone":   "+573001234567",
        "contact_whatsapp":"+573001234567",
        "location_slug":   "el-chico",
        "type_code":       "apartment",
    },
]


def _upsert_locations(db) -> dict[str, str]:
    """Insert locations, return slug→id mapping."""
    existing = {loc.slug: loc for loc in db.query(LocationORM).all()}
    slug_to_id: dict[str, str] = {slug: loc.id for slug, loc in existing.items()}

    for loc in LOCATIONS:
        if loc["slug"] in existing:
            continue
        parent_id = slug_to_id.get(loc["parent"]) if loc["parent"] else None
        new_id = str(uuid.uuid4())
        db.add(LocationORM(
            id=new_id,
            name=loc["name"],
            slug=loc["slug"],
            level=loc["level"],
            parent_id=parent_id,
            center_lat=loc.get("lat"),
            center_lng=loc.get("lng"),
            is_active=True,
        ))
        db.flush()
        slug_to_id[loc["slug"]] = new_id
        print(f"  + ubicación: {loc['name']}")

    return slug_to_id


def _upsert_demo_agent(db) -> UserORM:
    agent = db.query(UserORM).filter_by(email=DEMO_AGENT["email"]).first()
    if agent:
        return agent

    agent_role = db.query(RoleORM).filter_by(name="AGENT").first()
    new_id = str(uuid.uuid4())
    agent = UserORM(
        id=new_id,
        email=DEMO_AGENT["email"],
        hashed_password=hash_password(DEMO_AGENT["password"]),
        full_name=DEMO_AGENT["full_name"],
        phone=DEMO_AGENT["phone"],
        is_active=True,
        email_verified=True,
    )
    db.add(agent)
    db.flush()
    if agent_role:
        agent.roles.append(agent_role)
    print(f"  + agente demo: {DEMO_AGENT['email']} / {DEMO_AGENT['password']}")
    return agent


def _upsert_demo_properties(db, agent: UserORM, loc_ids: dict[str, str]) -> None:
    from src.db.models.catalog_models import PropertyTypeORM
    type_map = {pt.code: pt.id for pt in db.query(PropertyTypeORM).all()}
    now = datetime.now(timezone.utc)

    existing_slugs = {p.slug for p in db.query(PropertyORM.slug).all()}

    for prop in DEMO_PROPERTIES:
        if prop["slug"] in existing_slugs:
            continue
        location_id = loc_ids.get(prop["location_slug"])
        property_type_id = type_map.get(prop["type_code"])
        db.add(PropertyORM(
            id=str(uuid.uuid4()),
            owner_id=agent.id,
            location_id=location_id,
            property_type_id=property_type_id,
            title=prop["title"],
            slug=prop["slug"],
            description=prop["description"],
            operation_type=prop["operation_type"],
            property_kind=prop["property_kind"],
            condition=prop.get("condition"),
            price_amount=prop["price_amount"],
            currency=prop["currency"],
            bedrooms=prop.get("bedrooms"),
            bathrooms=prop.get("bathrooms"),
            parking_spots=prop.get("parking_spots"),
            total_area_m2=prop.get("total_area_m2"),
            built_area_m2=prop.get("built_area_m2"),
            address_street=prop.get("address_street"),
            contact_phone=prop.get("contact_phone"),
            contact_whatsapp=prop.get("contact_whatsapp"),
            status="published",
            published_at=now,
        ))
        print(f"  + propiedad: {prop['title']}")


def seed_colombia(verbose: bool = True) -> None:
    create_tables()
    db = SessionLocal()
    try:
        if verbose:
            print("Sembrando ubicaciones Colombia...")
        loc_ids = _upsert_locations(db)
        db.flush()

        if verbose:
            print("Sembrando agente demo...")
        agent = _upsert_demo_agent(db)
        db.flush()

        if verbose:
            print("Sembrando propiedades demo en Bogotá...")
        _upsert_demo_properties(db, agent, loc_ids)

        db.commit()
        if verbose:
            print(f"\n✅ Colombia seed completo.")
            print(f"   Agente: {DEMO_AGENT['email']} / {DEMO_AGENT['password']}")
            print(f"   Propiedades: {len(DEMO_PROPERTIES)} publicadas en Bogotá")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_colombia()
