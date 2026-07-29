"""Seed operating areas: Proppia coverage outside Bogotá city + Bogotá's
20 official localidades.

Idempotent — upserts by slug, so it is safe to re-run. Adds:
  · Departamentos (state): Cundinamarca, Quindío, Risaralda
  · Municipios (city): Sabana norte/occidente + Eje Cafetero
  · Bogotá: the 20 official localidades (level=locality)

Run:
    python3 scripts/seed_operating_areas.py
"""
from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import src.db.models  # noqa: F401
from src.db.engine import SessionLocal
from src.db.models.location_models import LocationORM

# slug → (name, level, parent_slug, lat, lng). Ordered so every parent is
# created/looked up before its children (state → city → locality).
LOCATIONS: list[dict] = [
    # ── Departamentos ───────────────────────────────────────────────────────
    {"slug": "cundinamarca", "name": "Cundinamarca", "level": "state", "parent": "colombia", "lat": 5.026, "lng": -74.030},
    {"slug": "quindio",      "name": "Quindío",      "level": "state", "parent": "colombia", "lat": 4.533, "lng": -75.681},
    {"slug": "risaralda",    "name": "Risaralda",    "level": "state", "parent": "colombia", "lat": 4.814, "lng": -75.694},

    # ── Sabana norte (Cundinamarca) ─────────────────────────────────────────
    {"slug": "cota",      "name": "Cota",      "level": "city", "parent": "cundinamarca", "lat": 4.809, "lng": -74.098},
    {"slug": "chia",      "name": "Chía",      "level": "city", "parent": "cundinamarca", "lat": 4.861, "lng": -74.058},
    {"slug": "cajica",    "name": "Cajicá",    "level": "city", "parent": "cundinamarca", "lat": 4.918, "lng": -74.025},
    {"slug": "sopo",      "name": "Sopó",      "level": "city", "parent": "cundinamarca", "lat": 4.908, "lng": -73.940},
    {"slug": "la-calera", "name": "La Calera", "level": "city", "parent": "cundinamarca", "lat": 4.721, "lng": -73.969},
    {"slug": "guasca",    "name": "Guasca",    "level": "city", "parent": "cundinamarca", "lat": 4.866, "lng": -73.877},
    {"slug": "tabio",     "name": "Tabio",     "level": "city", "parent": "cundinamarca", "lat": 4.917, "lng": -74.097},

    # ── Sabana occidente (Cundinamarca) ─────────────────────────────────────
    {"slug": "funza",    "name": "Funza",    "level": "city", "parent": "cundinamarca", "lat": 4.717, "lng": -74.211},
    {"slug": "madrid",   "name": "Madrid",   "level": "city", "parent": "cundinamarca", "lat": 4.733, "lng": -74.267},
    {"slug": "mosquera", "name": "Mosquera", "level": "city", "parent": "cundinamarca", "lat": 4.706, "lng": -74.230},

    # ── Eje Cafetero ────────────────────────────────────────────────────────
    {"slug": "armenia", "name": "Armenia", "level": "city", "parent": "quindio",   "lat": 4.533, "lng": -75.681},
    {"slug": "calarca", "name": "Calarcá", "level": "city", "parent": "quindio",   "lat": 4.527, "lng": -75.644},
    {"slug": "pereira", "name": "Pereira", "level": "city", "parent": "risaralda", "lat": 4.814, "lng": -75.694},

    # ── Bogotá: 20 localidades oficiales (existentes se omiten por slug) ─────
    {"slug": "usaquen",            "name": "Usaquén",            "level": "locality", "parent": "bogota", "lat": 4.703, "lng": -74.030},
    {"slug": "chapinero",          "name": "Chapinero",          "level": "locality", "parent": "bogota", "lat": 4.643, "lng": -74.066},
    {"slug": "santa-fe",           "name": "Santa Fe",           "level": "locality", "parent": "bogota", "lat": 4.604, "lng": -74.073},
    {"slug": "san-cristobal",      "name": "San Cristóbal",      "level": "locality", "parent": "bogota", "lat": 4.557, "lng": -74.083},
    {"slug": "usme",               "name": "Usme",               "level": "locality", "parent": "bogota", "lat": 4.479, "lng": -74.126},
    {"slug": "tunjuelito",         "name": "Tunjuelito",         "level": "locality", "parent": "bogota", "lat": 4.572, "lng": -74.132},
    {"slug": "bosa",               "name": "Bosa",               "level": "locality", "parent": "bogota", "lat": 4.618, "lng": -74.190},
    {"slug": "kennedy",            "name": "Kennedy",            "level": "locality", "parent": "bogota", "lat": 4.628, "lng": -74.157},
    {"slug": "fontibon",           "name": "Fontibón",           "level": "locality", "parent": "bogota", "lat": 4.673, "lng": -74.143},
    {"slug": "engativa",           "name": "Engativá",           "level": "locality", "parent": "bogota", "lat": 4.717, "lng": -74.115},
    {"slug": "suba",               "name": "Suba",               "level": "locality", "parent": "bogota", "lat": 4.745, "lng": -74.083},
    {"slug": "barrios-unidos",     "name": "Barrios Unidos",     "level": "locality", "parent": "bogota", "lat": 4.667, "lng": -74.084},
    {"slug": "teusaquillo",        "name": "Teusaquillo",        "level": "locality", "parent": "bogota", "lat": 4.638, "lng": -74.090},
    {"slug": "los-martires",       "name": "Los Mártires",       "level": "locality", "parent": "bogota", "lat": 4.604, "lng": -74.090},
    {"slug": "antonio-narino",     "name": "Antonio Nariño",     "level": "locality", "parent": "bogota", "lat": 4.590, "lng": -74.099},
    {"slug": "puente-aranda",      "name": "Puente Aranda",      "level": "locality", "parent": "bogota", "lat": 4.617, "lng": -74.114},
    {"slug": "la-candelaria",      "name": "La Candelaria",      "level": "locality", "parent": "bogota", "lat": 4.597, "lng": -74.075},
    {"slug": "rafael-uribe-uribe", "name": "Rafael Uribe Uribe", "level": "locality", "parent": "bogota", "lat": 4.558, "lng": -74.107},
    {"slug": "ciudad-bolivar",     "name": "Ciudad Bolívar",     "level": "locality", "parent": "bogota", "lat": 4.494, "lng": -74.143},
    {"slug": "sumapaz",            "name": "Sumapaz",            "level": "locality", "parent": "bogota", "lat": 4.050, "lng": -74.350},
]


def seed() -> None:
    db = SessionLocal()
    try:
        slug_to_id = {loc.slug: loc.id for loc in db.query(LocationORM).all()}
        added = 0
        for loc in LOCATIONS:
            if loc["slug"] in slug_to_id:
                continue
            parent_id = slug_to_id.get(loc["parent"]) if loc["parent"] else None
            if loc["parent"] and parent_id is None:
                print(f"  ! omito {loc['name']}: falta el padre '{loc['parent']}'")
                continue
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
            added += 1
            print(f"  + {loc['level']}: {loc['name']}")
        db.commit()
        print(f"\nListo: {added} ubicaciones nuevas, {len(LOCATIONS) - added} ya existían.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
