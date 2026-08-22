"""Background orchestration for AI panorama generation and persistence."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from src.db.engine import SessionLocal
from src.db.models.project_models import ProjectImageORM
from src.db.models.property_models import PropertyImageORM
from src.db.models.virtual_tour_models import (
    VirtualTourGenerationAttemptORM,
    VirtualTourSceneORM,
)
from src.media.pano_assets import build_pano_assets
from src.media.pano_provider import resolve_provider
from src.storage.image_store import read as storage_read, store as storage_store


def _reference_bytes(db: Session, scene: VirtualTourSceneORM) -> list[bytes]:
    tour = scene.tour
    image_ids = scene.source_image_ids or []
    if tour.property_id:
        images = db.query(PropertyImageORM).filter(
            PropertyImageORM.property_id == tour.property_id,
            PropertyImageORM.id.in_(image_ids),
        ).all()
    else:
        images = db.query(ProjectImageORM).filter(
            ProjectImageORM.project_id == tour.project_id,
            ProjectImageORM.id.in_(image_ids),
        ).all()
    by_id = {image.id: image for image in images}
    if set(by_id) != set(image_ids):
        raise RuntimeError("Una o más fotos de referencia ya no existen")
    result: list[bytes] = []
    for image_id in image_ids:
        image = by_id[image_id]
        if image.storage_key:
            result.append(storage_read(image.storage_key))
        elif image.cdn_url:
            response = httpx.get(image.cdn_url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            result.append(response.content)
        else:
            raise RuntimeError("Una foto de referencia no tiene un archivo disponible")
    return result


def generate_scene_task(scene_id: str, attempt_id: str, prompt: str) -> None:
    """Generate one scene using a fresh DB session safe for background execution."""
    db = SessionLocal()
    attempt: VirtualTourGenerationAttemptORM | None = None
    scene: VirtualTourSceneORM | None = None
    try:
        scene = db.get(VirtualTourSceneORM, scene_id)
        attempt = db.get(VirtualTourGenerationAttemptORM, attempt_id)
        if not scene or not attempt:
            return
        attempt.state = "running"
        db.commit()

        provider = resolve_provider()
        if provider is None:
            raise RuntimeError("La generación con IA no está configurada")
        references = _reference_bytes(db, scene)
        result = provider.generate(
            references,
            prompt,
            seam_pass=bool(attempt.seam_pass),
        )
        assets = build_pano_assets(result.pano_bytes)
        base_key = f"tours/{scene.tour_id}/{scene.id}"
        scene.storage_key = f"{base_key}.webp"
        scene.thumb_storage_key = f"{base_key}-thumb.webp"
        scene.pano_url = storage_store(assets.pano_bytes, scene.storage_key)
        scene.thumb_url = storage_store(assets.thumb_bytes, scene.thumb_storage_key)
        scene.width = assets.width
        scene.height = assets.height
        scene.hfov_deg = result.hfov_deg
        scene.vfov_deg = result.vfov_deg
        scene.provider = result.provider
        scene.provider_model = result.provider_model
        scene.cost_usd = result.cost_usd
        scene.state = "ready"
        scene.error_message = None
        attempt.state = "ready"
        attempt.actual_cost_usd = result.cost_usd
        attempt.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:  # background boundary: persist a legible failure
        db.rollback()
        scene = db.get(VirtualTourSceneORM, scene_id)
        attempt = db.get(VirtualTourGenerationAttemptORM, attempt_id)
        message = str(exc)[:500] or "La generación falló"
        if scene:
            scene.state = "failed"
            scene.error_message = message
        if attempt:
            attempt.state = "failed"
            attempt.error_message = message
            attempt.completed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
