"""Create and publish one AI scene on the BOSQUE VERDE demo property."""
from __future__ import annotations

import json
import time

import httpx

from src.auth.jwt_handler import create_access_token


PROPERTY_ID = "919a3d5d-0e95-423c-b07b-bf5bcbc5a46c"
SOURCE_IMAGE_ID = "264dc52a-3dc7-47c4-86b8-85c3d271bef6"
OWNER_ID = "c9efaf88-3f4a-46b7-a41c-1244a055946c"
OWNER_EMAIL = "ventas@casatoropropiedades.com"
API_BASE = "http://127.0.0.1:8000/api/v1"


def checked(response: httpx.Response, expected: set[int]) -> dict:
    if response.status_code not in expected:
        raise RuntimeError(
            f"HTTP {response.status_code} {response.request.method} "
            f"{response.request.url.path}: {response.text[:500]}"
        )
    return response.json()


def main() -> None:
    token = create_access_token(OWNER_ID, OWNER_EMAIL)
    headers = {"Authorization": f"Bearer {token}"}
    tour_path = f"/properties/{PROPERTY_ID}/tour"

    with httpx.Client(base_url=API_BASE, headers=headers, timeout=30) as client:
        tour = checked(client.post(tour_path), {200, 201})
        generated = checked(
            client.post(
                f"{tour_path}/scenes:generate",
                json={
                    "title": "Cocina",
                    "source_image_ids": [SOURCE_IMAGE_ID],
                    "seam_pass": True,
                    "prompt": (
                        "Crea una panorámica equirectangular 2:1 fotorrealista de esta cocina "
                        "para un tour inmobiliario 360. Conserva fielmente gabinetes de madera, "
                        "mesones negros, electrodomésticos, ventanas, materiales, colores y luz "
                        "natural. Extiende el ambiente de forma coherente desde una cámara central, "
                        "mantén verticales rectas y perspectiva realista. No agregues personas, "
                        "texto, logos ni elementos arquitectónicos nuevos. Asegura continuidad "
                        "entre los bordes izquierdo y derecho."
                    ),
                },
            ),
            {202},
        )
        scene_id = generated["id"]
        started = time.monotonic()
        while True:
            scene = checked(client.get(f"/tour/scenes/{scene_id}/status"), {200})
            if scene["state"] != "pending":
                break
            if time.monotonic() - started > 330:
                raise RuntimeError("Timed out waiting for panorama generation")
            time.sleep(3)
        if scene["state"] != "ready":
            raise RuntimeError(f"Scene generation failed: {scene.get('error_message')}")

        tour = checked(
            client.patch(
                tour_path,
                json={
                    "start_scene_id": scene_id,
                    "ai_disclaimer_ack": True,
                    "status": "published",
                },
            ),
            {200},
        )
        print(json.dumps({
            "tour_id": tour["id"],
            "tour_status": tour["status"],
            "scene_id": scene_id,
            "scene_state": scene["state"],
            "pano_url": scene["pano_url"],
            "thumb_url": scene["thumb_url"],
            "width": scene["width"],
            "height": scene["height"],
            "hfov_deg": scene["hfov_deg"],
            "vfov_deg": scene["vfov_deg"],
            "cost_usd": str(scene["cost_usd"]),
            "elapsed_seconds": round(time.monotonic() - started, 2),
        }))


if __name__ == "__main__":
    main()
