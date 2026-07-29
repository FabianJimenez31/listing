"""Seed Bogotá barrios (neighborhood level) under each of the 20 localidades.

Curated set of the best-known/most-searched barrios per localidad — NOT the full
~1,900 catastral list. Idempotent: upserts by slug. Slugs are prefixed with the
localidad slug so duplicate barrio names across localidades don't collide
(e.g. "Galán" exists in both Kennedy and Puente Aranda).

Run after seed_operating_areas.py (needs the localidades to exist):
    python3 scripts/seed_bogota_barrios.py
"""
from __future__ import annotations

import os
import sys
import unicodedata
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import src.db.models  # noqa: F401
from src.db.engine import SessionLocal
from src.db.models.location_models import LocationORM

# localidad slug -> list of barrio display names
BARRIOS: dict[str, list[str]] = {
    "usaquen": [
        "Cedritos", "Santa Bárbara", "Santa Ana", "Country Club", "La Carolina",
        "Bella Suiza", "Cedro Golf", "San Patricio", "Los Cedros", "Verbenal",
        "Toberín", "San Cristóbal Norte", "Barrancas", "La Pradera", "Usaquén Centro",
    ],
    "chapinero": [
        "Chicó", "Chicó Norte", "El Nogal", "La Cabrera", "Rosales", "El Refugio",
        "Chapinero Alto", "El Retiro", "Quinta Camacho", "Marly", "Lago Gaitán",
        "Antiguo Country", "Granada", "La Salle",
    ],
    "santa-fe": [
        "La Macarena", "La Perseverancia", "Las Nieves", "Bosque Izquierdo",
        "Las Aguas", "Veracruz", "San Bernardo", "Las Cruces", "La Alameda",
    ],
    "san-cristobal": [
        "20 de Julio", "La Victoria", "Sosiego", "La Gloria", "San Blas",
        "Bello Horizonte", "La Sierra", "Los Libertadores", "Villa Javier",
    ],
    "usme": [
        "Santa Librada", "La Aurora", "Yomasa", "Usme Centro", "Alfonso López",
        "Marichuela", "El Virrey", "Comuneros", "Danubio Azul",
    ],
    "tunjuelito": [
        "Venecia", "El Tunal", "San Carlos", "Tunjuelito", "San Benito",
        "Abraham Lincoln", "Fátima", "Nuevo Muzú",
    ],
    "bosa": [
        "Bosa Centro", "El Recreo", "La Libertad", "San Bernardino", "El Porvenir",
        "Carbonell", "Piamonte", "La Independencia", "Brasil", "Laureles",
    ],
    "kennedy": [
        "Castilla", "Kennedy Central", "Patio Bonito", "Timiza", "Carvajal",
        "Class Roma", "El Tintal", "Américas", "Marsella", "Mandalay", "Banderas",
        "Bavaria", "Corabastos", "Galán",
    ],
    "fontibon": [
        "Fontibón Centro", "Modelia", "Hayuelos", "Capellanía", "Versalles",
        "Belén", "Zona Franca", "Villemar", "La Felicidad", "San Pablo", "Salitre",
    ],
    "engativa": [
        "Normandía", "La Granja", "Boyacá Real", "Las Ferias", "Bonanza",
        "Santa Helenita", "La Estrada", "Villa Luz", "Garcés Navas",
        "Villas de Granada", "Bachué", "Quirigua", "Minuto de Dios", "Álamos",
        "Santa María del Lago",
    ],
    "suba": [
        "Niza", "La Alhambra", "Prado Veraniego", "Pasadena", "Mazurén",
        "San José de Bavaria", "Britalia", "Villa del Prado", "Suba Centro",
        "El Rincón", "Córdoba", "Puente Largo", "Iberia", "La Gaitana",
        "Lisboa", "Aures", "Tibabuyes",
    ],
    "barrios-unidos": [
        "Los Andes", "La Castellana", "Polo Club", "Rionegro", "San Felipe",
        "Alcázares", "Metrópolis", "Entre Ríos", "Once de Noviembre",
        "Simón Bolívar", "Doce de Octubre", "Colombia",
    ],
    "teusaquillo": [
        "La Soledad", "Palermo", "Galerías", "Quinta Paredes",
        "Ciudad Salitre Oriental", "La Esmeralda", "Pablo VI",
        "Nicolás de Federmán", "Belalcázar", "La Magdalena", "Armenia",
        "Santa Teresita", "Gran América",
    ],
    "los-martires": [
        "La Sabana", "Santa Isabel", "Ricaurte", "Veraguas", "Eduardo Santos",
        "El Listón", "San Victorino", "Voto Nacional", "Paloquemao", "La Pepita",
    ],
    "antonio-narino": [
        "Restrepo", "Ciudad Jardín Sur", "Santander", "La Fragua", "San Antonio",
        "Policarpa", "Luna Park", "La Hortúa", "Caracas",
    ],
    "puente-aranda": [
        "Puente Aranda", "Ciudad Montes", "San Rafael", "Alquería", "Muzú",
        "Santa Matilde", "Trinidad", "Primavera", "La Asunción", "Pensilvania",
        "Brasilia", "Galán",
    ],
    "la-candelaria": [
        "Centro Histórico", "La Concordia", "Egipto", "Belén",
        "Santa Bárbara", "La Catedral",
    ],
    "rafael-uribe-uribe": [
        "Quiroga", "El Inglés", "Olaya", "Santa Lucía", "El Claret", "San José",
        "Bravo Páez", "Marco Fidel Suárez", "Diana Turbay", "Granjas de San Pablo",
        "Molinos",
    ],
    "ciudad-bolivar": [
        "El Ensueño", "Lucero", "Meissen", "San Francisco", "Arborizadora Alta",
        "Arborizadora Baja", "Candelaria La Nueva", "Perdomo", "Sierra Morena",
        "Madelena", "El Tesoro", "Jerusalén",
    ],
    "sumapaz": ["Nazareth", "San Juan", "Betania"],
}


def _slugify(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    out = "".join(c if c.isalnum() else "-" for c in norm.lower())
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def seed() -> None:
    db = SessionLocal()
    try:
        by_slug = {loc.slug: loc for loc in db.query(LocationORM).all()}
        added = 0
        for loc_slug, names in BARRIOS.items():
            parent = by_slug.get(loc_slug)
            if parent is None:
                print(f"  ! omito localidad ausente: {loc_slug}")
                continue
            for name in names:
                slug = f"{loc_slug}-{_slugify(name)}"
                if slug in by_slug:
                    continue
                loc = LocationORM(
                    id=str(uuid.uuid4()), name=name, slug=slug,
                    level="neighborhood", parent_id=parent.id, is_active=True,
                )
                db.add(loc)
                db.flush()
                by_slug[slug] = loc
                added += 1
        db.commit()
        total = sum(len(v) for v in BARRIOS.values())
        print(f"Listo: {added} barrios nuevos ({total - added} ya existían) en {len(BARRIOS)} localidades.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
