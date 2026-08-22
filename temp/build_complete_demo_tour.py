"""Generate, connect, and publish a complete demo apartment tour."""
from __future__ import annotations

import json
import time

import httpx

from src.auth.jwt_handler import create_access_token


PROPERTY_ID = "919a3d5d-0e95-423c-b07b-bf5bcbc5a46c"
OWNER_ID = "c9efaf88-3f4a-46b7-a41c-1244a055946c"
OWNER_EMAIL = "ventas@casatoropropiedades.com"
API_BASE = "http://127.0.0.1:8000/api/v1"
TOUR_PATH = f"/properties/{PROPERTY_ID}/tour"

SCENES = [
    {
        "title": "Sala principal",
        "image_id": "cf907d8b-56a1-408d-81a6-a2330ae67c36",
        "details": "la sala principal con sofás claros, mesa central, ventanales y vegetación exterior",
    },
    {
        "title": "Comedor",
        "image_id": "e63c444a-7211-4241-9d9b-bd1daa70d520",
        "details": "el comedor conectado visualmente con la cocina, su mesa, sillas, lámparas y acabados",
    },
    {
        "title": "Habitación principal",
        "image_id": "0e1f9731-e30c-41b1-ad14-29e647d245a3",
        "details": "la habitación principal, cama, ventanales, piso de madera y mobiliario existente",
    },
    {
        "title": "Habitación auxiliar",
        "image_id": "074b7c7d-05b0-4e66-b4d0-a69208519f67",
        "details": "la habitación auxiliar, cama, armarios, piso de madera y proporciones existentes",
    },
    {
        "title": "Baño",
        "image_id": "8618fd3f-6376-4565-ba47-8dcbb4a13619",
        "details": "el baño, su mesón, lavamanos, espejos, ducha, iluminación y revestimientos",
    },
    {
        "title": "Terraza",
        "image_id": "5b7586e8-1f30-4852-92c9-004c67416e7a",
        "details": "la terraza cubierta, sus muebles exteriores, vegetación, barandas y vista",
    },
]


def checked(response: httpx.Response, expected: set[int]) -> dict:
    if response.status_code not in expected:
        raise RuntimeError(
            f"HTTP {response.status_code} {response.request.method} "
            f"{response.request.url.path}: {response.text[:500]}"
        )
    return response.json()


def prompt_for(details: str) -> str:
    return (
        "Crea una panorámica equirectangular 2:1 fotorrealista para un tour inmobiliario "
        f"360 que represente fielmente {details}. Conserva materiales, distribución, "
        "colores, mobiliario y luz de la foto. Extiende el ambiente coherentemente desde "
        "una cámara central, con verticales rectas y perspectiva realista. No agregues "
        "personas, texto, logos ni elementos arquitectónicos nuevos. Asegura continuidad "
        "entre los bordes izquierdo y derecho."
    )


def wait_for_scene(client: httpx.Client, scene_id: str) -> dict:
    started = time.monotonic()
    while True:
        scene = checked(client.get(f"/tour/scenes/{scene_id}/status"), {200})
        if scene["state"] != "pending":
            return scene
        if time.monotonic() - started > 330:
            raise RuntimeError(f"Timed out waiting for scene {scene_id}")
        time.sleep(3)


def hotspot(to_scene_id: str, yaw: float, label: str) -> dict:
    return {"to_scene_id": to_scene_id, "yaw": yaw, "pitch": -4.0, "label": label}


def main() -> None:
    token = create_access_token(OWNER_ID, OWNER_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}
    completed: list[dict] = []

    with httpx.Client(base_url=API_BASE, headers=headers, timeout=30) as client:
        tour = checked(client.get(f"{TOUR_PATH}/admin"), {200})
        by_title = {scene["title"]: scene for scene in tour["scenes"]}

        for index, definition in enumerate(SCENES, start=1):
            existing = by_title.get(definition["title"])
            if existing and existing["state"] == "ready":
                completed.append(existing)
                print(f"SKIP {index}/{len(SCENES)} {definition['title']} ready", flush=True)
                continue
            generated = checked(
                client.post(
                    f"{TOUR_PATH}/scenes:generate",
                    json={
                        "title": definition["title"],
                        "source_image_ids": [definition["image_id"]],
                        "prompt": prompt_for(definition["details"]),
                        "seam_pass": True,
                    },
                ),
                {202},
            )
            print(f"START {index}/{len(SCENES)} {definition['title']}", flush=True)
            scene = wait_for_scene(client, generated["id"])
            if scene["state"] != "ready":
                raise RuntimeError(
                    f"Scene {definition['title']} failed: {scene.get('error_message')}"
                )
            completed.append(scene)
            by_title[definition["title"]] = scene
            print(
                f"READY {index}/{len(SCENES)} {definition['title']} "
                f"{scene['width']}x{scene['height']} cost={scene['cost_usd']}",
                flush=True,
            )

        tour = checked(client.get(f"{TOUR_PATH}/admin"), {200})
        by_title = {scene["title"]: scene for scene in tour["scenes"]}
        ordered_titles = [
            "Sala principal",
            "Comedor",
            "Cocina",
            "Habitación principal",
            "Baño",
            "Habitación auxiliar",
            "Terraza",
        ]
        missing = [title for title in ordered_titles if title not in by_title]
        if missing:
            raise RuntimeError(f"Missing ready scenes: {missing}")
        ordered_ids = [by_title[title]["id"] for title in ordered_titles]
        checked(
            client.patch(f"{TOUR_PATH}/scenes/reorder", json={"ordered_ids": ordered_ids}),
            {200},
        )

        sala = by_title["Sala principal"]["id"]
        links = {
            "Sala principal": [
                hotspot(by_title["Comedor"]["id"], -45, "Ir al comedor"),
                hotspot(by_title["Cocina"]["id"], 35, "Ir a la cocina"),
                hotspot(by_title["Habitación principal"]["id"], 110, "Habitación principal"),
                hotspot(by_title["Habitación auxiliar"]["id"], -115, "Habitación auxiliar"),
                hotspot(by_title["Terraza"]["id"], 178, "Salir a la terraza"),
            ],
            "Comedor": [hotspot(sala, 180, "Volver a la sala")],
            "Cocina": [hotspot(sala, 180, "Volver a la sala")],
            "Habitación principal": [
                hotspot(sala, 180, "Volver a la sala"),
                hotspot(by_title["Baño"]["id"], 55, "Ir al baño"),
            ],
            "Baño": [hotspot(by_title["Habitación principal"]["id"], 180, "Habitación principal")],
            "Habitación auxiliar": [hotspot(sala, 180, "Volver a la sala")],
            "Terraza": [hotspot(sala, 180, "Entrar a la sala")],
        }
        for title, hotspots in links.items():
            checked(
                client.put(
                    f"/tour/scenes/{by_title[title]['id']}/hotspots",
                    json={"hotspots": hotspots},
                ),
                {200},
            )
        print("HOTSPOTS ready", flush=True)

        published = checked(
            client.patch(
                TOUR_PATH,
                json={
                    "start_scene_id": sala,
                    "ai_disclaimer_ack": True,
                    "status": "published",
                },
            ),
            {200},
        )
        print(json.dumps({
            "tour_id": published["id"],
            "status": published["status"],
            "start_scene_id": published["start_scene_id"],
            "scene_count": len(published["scenes"]),
            "scenes": [
                {
                    "title": scene["title"],
                    "state": scene["state"],
                    "cost_usd": str(scene["cost_usd"]),
                    "hotspot_count": len(scene["hotspots"]),
                }
                for scene in published["scenes"]
            ],
        }), flush=True)


if __name__ == "__main__":
    main()
