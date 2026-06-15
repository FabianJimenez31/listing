"""Seed portal data: USA + extra cities, agencies, partners, projects, posts.

Run after seed_data.py and seed_colombia.py:
    python3 scripts/seed_data.py
    python3 scripts/seed_colombia.py
    python3 scripts/seed_portal.py

Idempotent — re-running only fills in what is missing (upsert by slug / name).
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import src.db.models  # noqa: F401 — registers all ORM models
from src.auth.password import hash_password
from src.db.engine import SessionLocal, create_tables
from src.db.models.agency_models import AgencyORM
from src.db.models.blog_models import PostORM
from src.db.models.catalog_models import PropertyTypeORM
from src.db.models.location_models import LocationORM
from src.db.models.partner_models import PartnerORM
from src.db.models.project_models import ProjectImageORM, ProjectORM
from src.db.models.promotion_models import FeaturedPropertyORM
from src.db.models.property_models import PropertyImageORM, PropertyORM
from src.db.models.user_models import RoleORM, UserORM
from src.text.slug import slugify


def _img(photo_id: str, w: int = 1000) -> str:
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w={w}&q=80"


# ---------------------------------------------------------------------------
# Locations: USA tree + extra Colombian cities. City nodes carry a cover photo.
# ---------------------------------------------------------------------------
LOCATIONS: list[dict] = [
    # Colombia (country "colombia" already seeded by seed_colombia.py)
    {"slug": "antioquia", "name": "Antioquia", "level": "state", "parent": "colombia", "lat": 6.25, "lng": -75.56},
    {"slug": "medellin", "name": "Medellín", "level": "city", "parent": "antioquia", "lat": 6.2442, "lng": -75.5812, "img": "photo-1591147834150-b88f9fe0f0e1"},
    {"slug": "el-poblado", "name": "El Poblado", "level": "locality", "parent": "medellin", "lat": 6.2086, "lng": -75.5659},
    {"slug": "valle-del-cauca", "name": "Valle del Cauca", "level": "state", "parent": "colombia", "lat": 3.8, "lng": -76.5},
    {"slug": "cali", "name": "Cali", "level": "city", "parent": "valle-del-cauca", "lat": 3.4516, "lng": -76.5320, "img": "photo-1449034446853-66c86144b0ad"},
    {"slug": "ciudad-jardin", "name": "Ciudad Jardín", "level": "locality", "parent": "cali", "lat": 3.3725, "lng": -76.5360},
    # United States
    {"slug": "estados-unidos", "name": "Estados Unidos", "level": "country", "parent": None, "lat": 39.8, "lng": -98.6},
    {"slug": "florida", "name": "Florida", "level": "state", "parent": "estados-unidos", "lat": 27.99, "lng": -81.76},
    {"slug": "miami", "name": "Miami", "level": "city", "parent": "florida", "lat": 25.7617, "lng": -80.1918, "img": "photo-1535498730771-e735b998cd64"},
    {"slug": "brickell", "name": "Brickell", "level": "locality", "parent": "miami", "lat": 25.7617, "lng": -80.1918},
    {"slug": "texas", "name": "Texas", "level": "state", "parent": "estados-unidos", "lat": 31.0, "lng": -100.0},
    {"slug": "austin", "name": "Austin", "level": "city", "parent": "texas", "lat": 30.2672, "lng": -97.7431, "img": "photo-1531218150217-54595bc2b934"},
    {"slug": "downtown-austin", "name": "Downtown", "level": "locality", "parent": "austin", "lat": 30.2672, "lng": -97.7431},
    {"slug": "estado-nueva-york", "name": "Estado de Nueva York", "level": "state", "parent": "estados-unidos", "lat": 43.0, "lng": -75.0},
    {"slug": "nueva-york", "name": "Nueva York", "level": "city", "parent": "estado-nueva-york", "lat": 40.7128, "lng": -74.0060, "img": "photo-1496588152823-86ff7695e68f"},
]

# Cover photos for cities seeded by seed_colombia.py (set if currently empty)
EXISTING_CITY_IMAGES = {"bogota": "photo-1599933190147-3e9a01a44d5e"}

# ---------------------------------------------------------------------------
# Agencies (inmobiliarias) shown on each card's footer
# ---------------------------------------------------------------------------
AGENCIES: list[dict] = [
    {"slug": "engel-volkers-bogota", "name": "Engel & Völkers Bogotá", "initials": "EV", "city": "bogota", "verified": True, "phone": "+5715551234"},
    {"slug": "propiedad-raiz", "name": "Propiedad Raíz", "initials": "PR", "city": "bogota", "phone": "+5715559876"},
    {"slug": "grupo-arenas", "name": "Grupo Arenas", "initials": "GA", "city": "medellin", "verified": True, "phone": "+5745550000"},
    {"slug": "proppietario-usa", "name": "Proppietario USA", "initials": "PU", "city": "miami", "verified": True, "phone": "+13055551212"},
    {"slug": "proppietario-developments", "name": "Proppietario Developments", "initials": "PD", "city": "cali", "verified": True, "phone": "+5725554444"},
]

# ---------------------------------------------------------------------------
# Partners (allied agencies & developers) for the home strip
# ---------------------------------------------------------------------------
PARTNERS: list[dict] = [
    {"name": "ARENAS", "kind": "constructora", "priority": 60},
    {"name": "Engel & Völkers", "kind": "inmobiliaria", "priority": 55},
    {"name": "MARVAL", "kind": "constructora", "priority": 50},
    {"name": "COLPATRIA", "kind": "constructora", "priority": 45},
    {"name": "PROINTEGRAL", "kind": "constructora", "priority": 40},
    {"name": "AMARILO", "kind": "constructora", "priority": 35},
]

# ---------------------------------------------------------------------------
# Projects (developments / preventa) — price ranges in minor units
# ---------------------------------------------------------------------------
PROJECTS: list[dict] = [
    {
        "slug": "torres-verde-cali",
        "title": "Torres Verde — apartamentos sobre planos",
        "developer_name": "Proppietario Developments",
        "agency_slug": "proppietario-developments",
        "location_slug": "ciudad-jardin",
        "type_code": "apartment",
        "stage": "preventa",
        "description": "Apartamentos sobre planos en Ciudad Jardín, Cali. Zonas comunes con piscina, gimnasio y coworking. Entrega proyectada 2027.",
        "price_from": 29_000_000_000,  # 290.000.000 COP
        "price_to": 52_000_000_000,
        "currency": "COP",
        "bedrooms_min": 1, "bedrooms_max": 3,
        "bathrooms_min": 1, "bathrooms_max": 2,
        "area_min_m2": 52.0, "area_max_m2": 90.0,
        "total_units": 120, "available_units": 84,
        "cover": "photo-1460317442991-0ec209397118",
        "gallery": ["photo-1460317442991-0ec209397118", "photo-1545324418-cc1a3fa10c00"],
    },
    {
        "slug": "brickell-bay-residences",
        "title": "Brickell Bay Residences — condominios frente al mar",
        "developer_name": "Proppietario USA",
        "agency_slug": "proppietario-usa",
        "location_slug": "brickell",
        "type_code": "apartment",
        "stage": "preventa",
        "description": "Condominios de lujo en preventa frente a la bahía de Brickell, Miami. Amenidades resort y financiación para inversionistas extranjeros.",
        "price_from": 52_000_000,  # USD 520.000 (cents)
        "price_to": 145_000_000,
        "currency": "USD",
        "bedrooms_min": 1, "bedrooms_max": 3,
        "bathrooms_min": 1, "bathrooms_max": 3,
        "area_min_m2": 70.0, "area_max_m2": 160.0,
        "total_units": 240, "available_units": 160,
        "cover": "photo-1512917774080-9991f1c4c750",
        "gallery": ["photo-1512917774080-9991f1c4c750", "photo-1502672260266-1c1ef2d93688"],
    },
]

# ---------------------------------------------------------------------------
# Extra published properties (populate cities + USA market) linked to agencies
# ---------------------------------------------------------------------------
EXTRA_PROPERTIES: list[dict] = [
    {
        "slug": "venta-casa-poblado-001",
        "title": "Casa contemporánea con piscina",
        "description": "Espectacular casa contemporánea en El Poblado con piscina, domótica y acabados premium.",
        "operation_type": "sale", "property_kind": "house", "condition": "new",
        "price_amount": 125_000_000_000, "currency": "COP",  # 1.250.000.000 COP
        "bedrooms": 5, "bathrooms": 4, "parking_spots": 3, "total_area_m2": 340.0,
        "location_slug": "el-poblado", "type_code": "house",
        "agency_slug": "grupo-arenas", "image": "photo-1600596542815-ffad4c1539a9",
    },
    {
        "slug": "venta-apartamento-ciudad-jardin-001",
        "title": "Apartamento con vista en Ciudad Jardín",
        "description": "Apartamento luminoso en Ciudad Jardín, Cali, con balcón y vista abierta.",
        "operation_type": "sale", "property_kind": "apartment", "condition": "used",
        "price_amount": 48_000_000_000, "currency": "COP",
        "bedrooms": 3, "bathrooms": 2, "parking_spots": 1, "total_area_m2": 98.0,
        "location_slug": "ciudad-jardin", "type_code": "apartment",
        "agency_slug": "proppietario-developments", "image": "photo-1502672260266-1c1ef2d93688",
    },
    {
        "slug": "venta-condo-brickell-001",
        "title": "Condo con vista a la bahía en Brickell",
        "description": "Condominio amoblado con vista a la bahía, ideal para renta o inversión en dólares.",
        "operation_type": "sale", "property_kind": "apartment", "condition": "new",
        "price_amount": 52_000_000, "currency": "USD",  # USD 520.000
        "bedrooms": 2, "bathrooms": 2, "parking_spots": 1, "total_area_m2": 120.0,
        "location_slug": "brickell", "type_code": "apartment",
        "agency_slug": "proppietario-usa", "image": "photo-1512917774080-9991f1c4c750",
    },
    {
        "slug": "arriendo-loft-downtown-austin-001",
        "title": "Loft amoblado en zona financiera",
        "description": "Loft moderno amoblado en Downtown Austin, a pasos del distrito financiero.",
        "operation_type": "rent", "property_kind": "apartment", "condition": "remodeled",
        "price_amount": 320_000, "currency": "USD",  # USD 3.200/mes
        "bedrooms": 1, "bathrooms": 1, "parking_spots": 1, "total_area_m2": 64.0,
        "location_slug": "downtown-austin", "type_code": "apartment",
        "agency_slug": "proppietario-usa", "image": "photo-1502005229762-cf1b2da7c5d6",
    },
    {
        "slug": "venta-apartamento-manhattan-001",
        "title": "Apartamento en Manhattan",
        "description": "Apartamento de inversión en Nueva York, excelente ubicación y rentabilidad.",
        "operation_type": "sale", "property_kind": "apartment", "condition": "used",
        "price_amount": 98_000_000, "currency": "USD",
        "bedrooms": 2, "bathrooms": 2, "total_area_m2": 95.0,
        "location_slug": "nueva-york", "type_code": "apartment",
        "agency_slug": "proppietario-usa", "image": "photo-1496588152823-86ff7695e68f",
    },
]

# ---------------------------------------------------------------------------
# Blog posts
# ---------------------------------------------------------------------------
POSTS: list[dict] = [
    {
        "title": "Cómo invertir en Miami siendo extranjero",
        "excerpt": "Guía práctica para comprar propiedad en Florida con estructura LLC y financiación internacional.",
        "category": "Mercado USA",
        "cover": "photo-1535498730771-e735b998cd64",
        "content": "Invertir en Miami como extranjero es más accesible de lo que parece...",
    },
    {
        "title": "Preventa vs. usado: ¿qué conviene en 2026?",
        "excerpt": "Comparamos rentabilidad, riesgo y plazos entre comprar sobre planos y vivienda usada.",
        "category": "Inversión",
        "cover": "photo-1460317442991-0ec209397118",
        "content": "La preventa ofrece precios de entrada más bajos y valorización durante la construcción...",
    },
    {
        "title": "Las zonas con mayor valorización en Bogotá",
        "excerpt": "Usaquén, Chapinero y El Chico lideran la valorización; te contamos por qué.",
        "category": "Colombia",
        "cover": "photo-1599933190147-3e9a01a44d5e",
        "content": "El norte de Bogotá concentra la mayor demanda de vivienda de alto valor...",
    },
]


def _upsert_locations(db) -> dict[str, str]:
    existing = {loc.slug: loc for loc in db.query(LocationORM).all()}
    slug_to_id = {slug: loc.id for slug, loc in existing.items()}

    # Set cover images on already-seeded cities (e.g. Bogotá)
    for slug, photo in EXISTING_CITY_IMAGES.items():
        loc = existing.get(slug)
        if loc and not loc.image_url:
            loc.image_url = _img(photo)

    for spec in LOCATIONS:
        loc = existing.get(spec["slug"])
        if loc:
            if spec.get("img") and not loc.image_url:
                loc.image_url = _img(spec["img"])
            continue
        parent_id = slug_to_id.get(spec["parent"]) if spec["parent"] else None
        new_id = str(uuid.uuid4())
        db.add(LocationORM(
            id=new_id,
            name=spec["name"],
            slug=spec["slug"],
            level=spec["level"],
            parent_id=parent_id,
            center_lat=spec.get("lat"),
            center_lng=spec.get("lng"),
            image_url=_img(spec["img"]) if spec.get("img") else None,
            is_active=True,
        ))
        db.flush()
        slug_to_id[spec["slug"]] = new_id
        print(f"  + ubicación: {spec['name']}")
    return slug_to_id


def _upsert_agencies(db, loc_ids: dict[str, str]) -> dict[str, AgencyORM]:
    existing = {a.slug: a for a in db.query(AgencyORM).all()}
    for spec in AGENCIES:
        if spec["slug"] in existing:
            continue
        agency = AgencyORM(
            id=str(uuid.uuid4()),
            name=spec["name"],
            slug=spec["slug"],
            initials=spec.get("initials"),
            phone=spec.get("phone"),
            whatsapp=spec.get("phone"),
            location_id=loc_ids.get(spec.get("city")),
            is_verified=spec.get("verified", False),
            is_active=True,
        )
        db.add(agency)
        db.flush()
        existing[spec["slug"]] = agency
        print(f"  + inmobiliaria: {spec['name']}")
    return existing


def _upsert_partners(db) -> None:
    existing = {p.slug for p in db.query(PartnerORM.slug).all()}
    for spec in PARTNERS:
        slug = slugify(spec["name"])
        if slug in existing:
            continue
        db.add(PartnerORM(
            id=str(uuid.uuid4()),
            name=spec["name"],
            slug=slug,
            kind=spec["kind"],
            priority=spec.get("priority", 0),
            is_active=True,
        ))
        print(f"  + aliado: {spec['name']}")


def _get_or_create_agent(db) -> UserORM:
    agent = db.query(UserORM).filter_by(email="agente@listing.co").first()
    if agent:
        return agent
    role = db.query(RoleORM).filter_by(name="AGENT").first()
    agent = UserORM(
        id=str(uuid.uuid4()),
        email="agente@listing.co",
        hashed_password=hash_password("Demo1234!"),
        full_name="Agente Demo",
        phone="+573001234567",
        is_active=True,
        email_verified=True,
    )
    db.add(agent)
    db.flush()
    if role:
        agent.roles.append(role)
    return agent


def _attach_main_image(db, owner_type: str, owner_id: str, url: str, alt: str) -> None:
    if owner_type == "property":
        has = db.query(PropertyImageORM).filter_by(property_id=owner_id, role="main").first()
        if has:
            return
        db.add(PropertyImageORM(
            id=str(uuid.uuid4()), property_id=owner_id, role="main", media_kind="image",
            position=0, storage_key=f"seed/{owner_id}", cdn_url=url, thumb_url=url, alt_text=alt,
        ))


def _upsert_projects(db, agencies: dict[str, AgencyORM], loc_ids: dict[str, str], type_ids: dict[str, str], now) -> None:
    existing = {p.slug for p in db.query(ProjectORM.slug).all()}
    for spec in PROJECTS:
        if spec["slug"] in existing:
            continue
        agency = agencies.get(spec["agency_slug"])
        project_id = str(uuid.uuid4())
        db.add(ProjectORM(
            id=project_id,
            agency_id=agency.id if agency else None,
            location_id=loc_ids.get(spec["location_slug"]),
            property_type_id=type_ids.get(spec["type_code"]),
            developer_name=spec.get("developer_name"),
            title=spec["title"],
            slug=spec["slug"],
            description=spec.get("description"),
            stage=spec["stage"],
            status="published",
            price_from=spec.get("price_from"),
            price_to=spec.get("price_to"),
            currency=spec["currency"],
            bedrooms_min=spec.get("bedrooms_min"),
            bedrooms_max=spec.get("bedrooms_max"),
            bathrooms_min=spec.get("bathrooms_min"),
            bathrooms_max=spec.get("bathrooms_max"),
            area_min_m2=spec.get("area_min_m2"),
            area_max_m2=spec.get("area_max_m2"),
            total_units=spec.get("total_units"),
            available_units=spec.get("available_units"),
            cover_image_url=_img(spec["cover"]),
            published_at=now,
        ))
        db.flush()
        for i, photo in enumerate(spec.get("gallery", [])):
            db.add(ProjectImageORM(
                id=str(uuid.uuid4()), project_id=project_id,
                role="main" if i == 0 else "gallery", position=i,
                cdn_url=_img(photo, 1200), thumb_url=_img(photo), alt_text=spec["title"],
            ))
        print(f"  + proyecto: {spec['title']}")


def _upsert_extra_properties(db, agent: UserORM, agencies: dict[str, AgencyORM], loc_ids: dict[str, str], type_ids: dict[str, str], now) -> None:
    existing = {p.slug for p in db.query(PropertyORM.slug).all()}
    for spec in EXTRA_PROPERTIES:
        if spec["slug"] in existing:
            continue
        agency = agencies.get(spec.get("agency_slug"))
        prop_id = str(uuid.uuid4())
        db.add(PropertyORM(
            id=prop_id,
            owner_id=agent.id,
            agency_id=agency.id if agency else None,
            location_id=loc_ids.get(spec["location_slug"]),
            property_type_id=type_ids.get(spec["type_code"]),
            title=spec["title"],
            slug=spec["slug"],
            description=spec.get("description"),
            operation_type=spec["operation_type"],
            property_kind=spec["property_kind"],
            condition=spec.get("condition"),
            price_amount=spec["price_amount"],
            currency=spec["currency"],
            bedrooms=spec.get("bedrooms"),
            bathrooms=spec.get("bathrooms"),
            parking_spots=spec.get("parking_spots"),
            total_area_m2=spec.get("total_area_m2"),
            status="published",
            published_at=now,
        ))
        db.flush()
        if spec.get("image"):
            _attach_main_image(db, "property", prop_id, _img(spec["image"]), spec["title"])
        print(f"  + propiedad: {spec['title']}")


def _link_existing_properties(db, agencies: dict[str, AgencyORM]) -> None:
    """Attach an agency + cover photo to the seed_colombia.py demo properties."""
    photo_by_slug = {
        "venta-apartamento-chapinero-001": "photo-1502672260266-1c1ef2d93688",
        "venta-casa-usaquen-001": "photo-1568605114967-8130f3a36994",
        "arriendo-apartamento-chico-001": "photo-1545324418-cc1a3fa10c00",
    }
    agency_by_slug = {
        "venta-apartamento-chapinero-001": "propiedad-raiz",
        "venta-casa-usaquen-001": "engel-volkers-bogota",
        "arriendo-apartamento-chico-001": "propiedad-raiz",
    }
    for slug, photo in photo_by_slug.items():
        prop = db.query(PropertyORM).filter_by(slug=slug).first()
        if not prop:
            continue
        if prop.agency_id is None:
            agency = agencies.get(agency_by_slug.get(slug))
            if agency:
                prop.agency_id = agency.id
        _attach_main_image(db, "property", prop.id, _img(photo), prop.title)


def _upsert_posts(db, author_id: str | None, now) -> None:
    existing = {p.slug for p in db.query(PostORM.slug).all()}
    for spec in POSTS:
        slug = slugify(spec["title"])
        if slug in existing:
            continue
        db.add(PostORM(
            id=str(uuid.uuid4()),
            author_id=author_id,
            title=spec["title"],
            slug=slug,
            excerpt=spec.get("excerpt"),
            content=spec.get("content"),
            cover_image_url=_img(spec["cover"]),
            category=spec.get("category"),
            status="published",
            published_at=now,
        ))
        print(f"  + post: {spec['title']}")


def _upsert_featured(db, now) -> None:
    """Feature up to 6 published properties on the home grid."""
    existing_ids = {f.property_id for f in db.query(FeaturedPropertyORM.property_id).all()}
    published = (
        db.query(PropertyORM)
        .filter(PropertyORM.status == "published", PropertyORM.deleted_at.is_(None))
        .limit(6)
        .all()
    )
    for i, prop in enumerate(published):
        # The home grid is driven by Property.show_on_home
        prop.show_on_home = True
        if prop.id in existing_ids:
            continue
        db.add(FeaturedPropertyORM(
            id=str(uuid.uuid4()),
            property_id=prop.id,
            scope="home",
            priority=100 - i,
            starts_at=now,
            ends_at=now + timedelta(days=365 * 5),
        ))
    print(f"  + destacadas: {len(published)} propiedades en home")


def seed_portal(verbose: bool = True) -> None:
    create_tables()
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        type_ids = {pt.code: pt.id for pt in db.query(PropertyTypeORM).all()}

        if verbose:
            print("Sembrando ubicaciones (USA + ciudades)...")
        loc_ids = _upsert_locations(db)
        db.flush()

        if verbose:
            print("Sembrando inmobiliarias...")
        agencies = _upsert_agencies(db, loc_ids)
        db.flush()

        if verbose:
            print("Sembrando aliados...")
        _upsert_partners(db)

        agent = _get_or_create_agent(db)
        db.flush()

        if verbose:
            print("Sembrando proyectos...")
        _upsert_projects(db, agencies, loc_ids, type_ids, now)

        if verbose:
            print("Sembrando propiedades adicionales...")
        _upsert_extra_properties(db, agent, agencies, loc_ids, type_ids, now)
        _link_existing_properties(db, agencies)

        if verbose:
            print("Sembrando blog...")
        _upsert_posts(db, agent.id, now)
        db.flush()

        if verbose:
            print("Sembrando destacadas...")
        _upsert_featured(db, now)

        db.commit()
        if verbose:
            print("\n✅ Portal seed completo.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_portal()
