"""Virtual-tour CRUD, scene upload, hotspots, publication, and AI generation."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

from src.api.deps import CurrentUser, DB
from src.db.models.project_models import ProjectImageORM, ProjectORM
from src.db.models.property_models import PropertyImageORM, PropertyORM
from src.db.models.virtual_tour_models import (
    VirtualTourGenerationAttemptORM,
    VirtualTourHotspotORM,
    VirtualTourORM,
    VirtualTourSceneORM,
)
from src.media.pano_assets import MAX_PANO_BYTES, build_pano_assets
from src.media.pano_provider import resolve_provider
from src.media.tour_generation import generate_scene_task
from src.repositories.virtual_tour_repo import VirtualTourRepository
from src.schemas.virtual_tour_schemas import (
    HotspotReplaceRequest,
    HotspotResponse,
    ProviderInfoResponse,
    SceneGenerateRequest,
    SceneReorderRequest,
    SceneResponse,
    SceneUpdateRequest,
    TourResponse,
    TourUpdateRequest,
)
from src.storage.image_store import remove as storage_remove, store as storage_store
from src.virtual_tour import (
    SceneSource,
    SceneState,
    TourScene,
    TourValidationError,
    VirtualTour,
    normalize_floor_pitch,
    normalize_yaw,
)

router = APIRouter(tags=["virtual-tours"])

from src.api.routers.tour_billing import require_active_credit  # noqa: E402

# Tope duro de escenas por tour (006: el producto vendido es un tour de hasta 10 escenas).
MAX_SCENES_PER_TOUR = 10


def _assert_scene_capacity(tour: VirtualTourORM) -> None:
    if len(tour.scenes) >= MAX_SCENES_PER_TOUR:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"El tour alcanzo su maximo de {MAX_SCENES_PER_TOUR} escenas",
        )


def _entity_or_404(entity: str) -> str:
    if entity not in {"properties", "projects"}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entity not found")
    return entity


def _guard_parent(entity: str, entity_id: str, user, db, *, public: bool = False):
    _entity_or_404(entity)
    if entity == "properties":
        parent = db.get(PropertyORM, entity_id)
        if not parent or parent.deleted_at:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
        if public and parent.status != "published":
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
        if not public and parent.owner_id != user.id and not user.has_permission("property:moderate"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the property owner")
        return parent
    parent = db.get(ProjectORM, entity_id)
    if not parent or parent.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if public and parent.status != "published":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    if not public and not user.has_permission("project:create"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Permission required: project:create")
    return parent


def _scene_response(scene: VirtualTourSceneORM, ready_ids: set[str] | None = None) -> SceneResponse:
    hotspots = scene.hotspots
    if ready_ids is not None:
        hotspots = [hotspot for hotspot in hotspots if hotspot.to_scene_id in ready_ids]
    return SceneResponse(
        id=scene.id,
        title=scene.title,
        position=scene.position,
        source=scene.source,
        state=scene.state,
        error_message=scene.error_message,
        pano_url=scene.pano_url,
        thumb_url=scene.thumb_url,
        width=scene.width,
        height=scene.height,
        initial_yaw=scene.initial_yaw,
        initial_pitch=scene.initial_pitch,
        hfov_deg=scene.hfov_deg,
        vfov_deg=scene.vfov_deg,
        source_image_ids=scene.source_image_ids or [],
        provider=scene.provider,
        provider_model=scene.provider_model,
        cost_usd=scene.cost_usd,
        hotspots=[HotspotResponse.model_validate(hotspot, from_attributes=True) for hotspot in hotspots],
    )


def _tour_response(tour: VirtualTourORM, *, public: bool = False) -> TourResponse:
    scenes = sorted(tour.scenes, key=lambda item: (item.position, item.id))
    if public:
        scenes = [scene for scene in scenes if scene.state == "ready" and scene.pano_url]
    ready_ids = {scene.id for scene in scenes} if public else None
    start_scene_id = tour.start_scene_id
    if scenes and start_scene_id not in {scene.id for scene in scenes}:
        start_scene_id = scenes[0].id
    return TourResponse(
        id=tour.id,
        property_id=tour.property_id,
        project_id=tour.project_id,
        status=tour.status,
        start_scene_id=start_scene_id,
        ai_disclaimer_ack=tour.ai_disclaimer_ack,
        contains_ai=any(scene.source == "ai" for scene in scenes),
        scenes=[_scene_response(scene, ready_ids) for scene in scenes],
    )


def _domain_tour(tour: VirtualTourORM) -> VirtualTour:
    return VirtualTour(
        scenes=[
            TourScene(
                id=scene.id,
                title=scene.title,
                position=scene.position,
                source=SceneSource(scene.source),
                state=SceneState(scene.state),
                pano_url=scene.pano_url,
            )
            for scene in tour.scenes
        ],
        start_scene_id=tour.start_scene_id,
        ai_disclaimer_ack=tour.ai_disclaimer_ack,
    )


@router.get("/tour/provider", response_model=ProviderInfoResponse)
def get_provider_info(current_user: CurrentUser):
    del current_user
    provider = resolve_provider()
    if provider is None:
        return ProviderInfoResponse(
            available=False,
            reason="Configura OPENAI_API_KEY para habilitar la generación con IA",
        )
    # Costos internos: nunca salen por la API (el cliente paga por tour, no por escena).
    return ProviderInfoResponse(
        available=provider.is_available(),
        provider=provider.name,
        model=provider.model,
        quality=provider.quality,
        size=provider.size,
        estimated_cost_usd=None,
        estimated_seam_cost_usd=None,
    )


@router.get("/{entity}/{entity_id}/tour", response_model=TourResponse)
def get_public_tour(entity: str, entity_id: str, db: DB):
    _guard_parent(entity, entity_id, None, db, public=True)
    tour = VirtualTourRepository(db).get_published(entity, entity_id)
    if not tour:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    response = _tour_response(tour, public=True)
    if not response.scenes:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    return response


@router.get("/{entity}/{entity_id}/tour/admin", response_model=TourResponse)
def get_admin_tour(entity: str, entity_id: str, current_user: CurrentUser, db: DB):
    _guard_parent(entity, entity_id, current_user, db)
    tour = VirtualTourRepository(db).get_for_entity(entity, entity_id)
    if not tour:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    return _tour_response(tour)


@router.post(
    "/{entity}/{entity_id}/tour",
    response_model=TourResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tour(entity: str, entity_id: str, current_user: CurrentUser, db: DB):
    _guard_parent(entity, entity_id, current_user, db)
    repo = VirtualTourRepository(db)
    existing = repo.get_for_entity(entity, entity_id)
    if existing:
        return _tour_response(existing)

    # Monetizacion (006): todo tour nuevo requiere un pago aprobado sin consumir.
    from src.api.routers.tour_billing import _unconsumed_payment, billing_enabled, entity_exempt

    payment = None
    if billing_enabled() and not entity_exempt(entity_id):
        payment = _unconsumed_payment(db, entity, entity_id)
        if not payment:
            raise HTTPException(
                status.HTTP_402_PAYMENT_REQUIRED,
                "Este tour requiere el pago de creacion ($50.000 COP)",
            )

    tour = VirtualTourORM(
        id=str(uuid.uuid4()),
        property_id=entity_id if entity == "properties" else None,
        project_id=entity_id if entity == "projects" else None,
        status="draft",
    )
    db.add(tour)
    # ``tour_payments.tour_id`` points at this row.  Flush the new tour first so
    # PostgreSQL never sees the credit update before its referenced tour exists.
    # Assigning only the scalar FK does not give SQLAlchemy a relationship from
    # which it can infer the required INSERT-before-UPDATE order.
    db.flush()
    if payment is not None:
        payment.tour_id = tour.id
    db.commit()
    return _tour_response(repo.get_for_entity(entity, entity_id))


@router.patch("/{entity}/{entity_id}/tour", response_model=TourResponse)
def update_tour(
    entity: str,
    entity_id: str,
    body: TourUpdateRequest,
    current_user: CurrentUser,
    db: DB,
):
    _guard_parent(entity, entity_id, current_user, db)
    repo = VirtualTourRepository(db)
    tour = repo.get_for_entity(entity, entity_id)
    if not tour:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    require_active_credit(db, entity, entity_id, tour)
    if body.ai_disclaimer_ack is not None:
        tour.ai_disclaimer_ack = body.ai_disclaimer_ack
    if "start_scene_id" in body.model_fields_set:
        if body.start_scene_id and body.start_scene_id not in {scene.id for scene in tour.scenes}:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Start scene is not in this tour")
        tour.start_scene_id = body.start_scene_id
    if body.status == "published":
        domain = _domain_tour(tour)
        try:
            domain.validate_for_publication()
        except TourValidationError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        tour.start_scene_id = domain.resolved_start_scene_id()
        tour.status = "published"
    elif body.status == "draft":
        tour.status = "draft"
    db.commit()
    return _tour_response(repo.get_for_entity(entity, entity_id))


@router.post(
    "/{entity}/{entity_id}/tour/scenes",
    response_model=SceneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_scene(
    entity: str,
    entity_id: str,
    current_user: CurrentUser,
    db: DB,
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=120),
    hfov_deg: float = Form(360.0, gt=0, le=360),
    vfov_deg: float = Form(180.0, gt=0, le=180),
):
    _guard_parent(entity, entity_id, current_user, db)
    repo = VirtualTourRepository(db)
    tour = repo.get_for_entity(entity, entity_id)
    if not tour:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    require_active_credit(db, entity, entity_id, tour)
    _assert_scene_capacity(tour)
    raw = await file.read(MAX_PANO_BYTES + 1)
    try:
        assets = build_pano_assets(raw)
    except TourValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    scene_id = str(uuid.uuid4())
    base_key = f"tours/{tour.id}/{scene_id}"
    pano_key = f"{base_key}.webp"
    thumb_key = f"{base_key}-thumb.webp"
    scene = VirtualTourSceneORM(
        id=scene_id,
        tour_id=tour.id,
        title=title,
        position=max((item.position for item in tour.scenes), default=-1) + 1,
        source="upload",
        state="ready",
        storage_key=pano_key,
        thumb_storage_key=thumb_key,
        pano_url=storage_store(assets.pano_bytes, pano_key),
        thumb_url=storage_store(assets.thumb_bytes, thumb_key),
        width=assets.width,
        height=assets.height,
        hfov_deg=hfov_deg,
        vfov_deg=vfov_deg,
    )
    tour.status = "draft"
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return _scene_response(scene)


@router.patch("/tour/scenes/{scene_id}", response_model=SceneResponse)
def update_scene(
    scene_id: str, body: SceneUpdateRequest, current_user: CurrentUser, db: DB
):
    scene = VirtualTourRepository(db).get_scene(scene_id)
    if not scene:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scene not found")
    entity = "properties" if scene.tour.property_id else "projects"
    entity_id = scene.tour.property_id or scene.tour.project_id
    _guard_parent(entity, entity_id, current_user, db)
    require_active_credit(db, entity, entity_id, scene.tour)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(scene, key, value)
    scene.tour.status = "draft"
    db.commit()
    db.refresh(scene)
    return _scene_response(scene)


@router.delete("/tour/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(scene_id: str, current_user: CurrentUser, db: DB):
    scene = VirtualTourRepository(db).get_scene(scene_id)
    if not scene:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scene not found")
    tour = scene.tour
    entity = "properties" if tour.property_id else "projects"
    _guard_parent(entity, tour.property_id or tour.project_id, current_user, db)
    require_active_credit(db, entity, tour.property_id or tour.project_id, tour)
    db.query(VirtualTourHotspotORM).filter(
        (VirtualTourHotspotORM.from_scene_id == scene_id)
        | (VirtualTourHotspotORM.to_scene_id == scene_id)
    ).delete(synchronize_session=False)
    if tour.start_scene_id == scene_id:
        tour.start_scene_id = None
    tour.status = "draft"
    if scene.storage_key:
        storage_remove(scene.storage_key)
    if scene.thumb_storage_key:
        storage_remove(scene.thumb_storage_key)
    db.delete(scene)
    db.commit()
    return None


@router.patch("/{entity}/{entity_id}/tour/scenes/reorder", response_model=TourResponse)
def reorder_scenes(
    entity: str,
    entity_id: str,
    body: SceneReorderRequest,
    current_user: CurrentUser,
    db: DB,
):
    _guard_parent(entity, entity_id, current_user, db)
    repo = VirtualTourRepository(db)
    tour = repo.get_for_entity(entity, entity_id)
    if not tour:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    require_active_credit(db, entity, entity_id, tour)
    scene_map = {scene.id: scene for scene in tour.scenes}
    if set(body.ordered_ids) != set(scene_map) or len(body.ordered_ids) != len(scene_map):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "ordered_ids must contain every scene once")
    for position, scene_id in enumerate(body.ordered_ids):
        scene_map[scene_id].position = position
    tour.status = "draft"
    db.commit()
    return _tour_response(repo.get_for_entity(entity, entity_id))


@router.put("/tour/scenes/{scene_id}/hotspots", response_model=SceneResponse)
def replace_hotspots(
    scene_id: str,
    body: HotspotReplaceRequest,
    current_user: CurrentUser,
    db: DB,
):
    repo = VirtualTourRepository(db)
    scene = repo.get_scene(scene_id)
    if not scene:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scene not found")
    tour = scene.tour
    entity = "properties" if tour.property_id else "projects"
    _guard_parent(entity, tour.property_id or tour.project_id, current_user, db)
    require_active_credit(db, entity, tour.property_id or tour.project_id, tour)
    valid_ids = {item.id for item in tour.scenes if item.id != scene_id}
    for hotspot in body.hotspots:
        if hotspot.to_scene_id not in valid_ids:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Hotspot target is not in this tour")
    db.query(VirtualTourHotspotORM).filter_by(from_scene_id=scene_id).delete()
    for hotspot in body.hotspots:
        db.add(
            VirtualTourHotspotORM(
                id=str(uuid.uuid4()),
                from_scene_id=scene_id,
                yaw=normalize_yaw(hotspot.yaw),
                pitch=normalize_floor_pitch(hotspot.pitch),
                to_scene_id=hotspot.to_scene_id,
                label=hotspot.label,
            )
        )
    tour.status = "draft"
    db.commit()
    return _scene_response(repo.get_scene(scene_id))


def _validate_source_images(entity: str, entity_id: str, ids: list[str], db) -> None:
    model = PropertyImageORM if entity == "properties" else ProjectImageORM
    owner_column = model.property_id if entity == "properties" else model.project_id
    count = db.query(model).filter(owner_column == entity_id, model.id.in_(ids)).count()
    if count != len(set(ids)) or len(ids) != len(set(ids)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid source_image_ids")


@router.post(
    "/{entity}/{entity_id}/tour/scenes:generate",
    response_model=SceneResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_scene(
    entity: str,
    entity_id: str,
    body: SceneGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DB,
):
    _guard_parent(entity, entity_id, current_user, db)
    provider = resolve_provider()
    if provider is None or not provider.is_available():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "AI panorama provider is not configured")
    repo = VirtualTourRepository(db)
    tour = repo.get_for_entity(entity, entity_id)
    if not tour:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tour not found")
    require_active_credit(db, entity, entity_id, tour)
    _assert_scene_capacity(tour)
    _validate_source_images(entity, entity_id, body.source_image_ids, db)
    seam_pass = body.seam_pass or os.getenv("TOUR_SEAM_PASS", "0") == "1"
    scene_id = str(uuid.uuid4())
    scene = VirtualTourSceneORM(
        id=scene_id,
        tour_id=tour.id,
        title=body.title,
        position=max((item.position for item in tour.scenes), default=-1) + 1,
        source="ai",
        state="pending",
        source_image_ids=body.source_image_ids,
        provider=provider.name,
        provider_model=provider.model,
        hfov_deg=360.0 if seam_pass else 180.0,
        vfov_deg=180.0 if seam_pass else 90.0,
    )
    attempt = VirtualTourGenerationAttemptORM(
        id=str(uuid.uuid4()),
        scene_id=scene_id,
        input_image_ids=body.source_image_ids,
        provider=provider.name,
        provider_model=provider.model,
        quality=provider.quality,
        output_size=provider.size,
        seam_pass=seam_pass,
        estimated_cost_usd=provider.estimate_cost_usd(
            len(body.source_image_ids), seam_pass
        ),
    )
    tour.status = "draft"
    db.add_all([scene, attempt])
    db.commit()
    prompt = body.prompt or (
        f"Crea una panorámica equirectangular fotorrealista 2:1 del ambiente '{body.title}', "
        "usando las fotos adjuntas como referencia principal. Mantén materiales, distribución y mobiliario; "
        "coloca el horizonte a media altura y no agregues elementos que no aparezcan en las referencias."
    )
    background_tasks.add_task(generate_scene_task, scene.id, attempt.id, prompt)
    db.refresh(scene)
    return _scene_response(scene)


@router.get("/tour/scenes/{scene_id}/status", response_model=SceneResponse)
def get_scene_status(scene_id: str, current_user: CurrentUser, db: DB):
    repo = VirtualTourRepository(db)
    scene = repo.get_scene(scene_id)
    if not scene:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scene not found")
    tour = scene.tour
    entity = "properties" if tour.property_id else "projects"
    _guard_parent(entity, tour.property_id or tour.project_id, current_user, db)
    if scene.state == "pending":
        updated_at = scene.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        timeout = timedelta(minutes=15)
        if datetime.now(timezone.utc) - updated_at > timeout:
            scene.state = "failed"
            scene.error_message = "La generación quedó interrumpida; intenta nuevamente"
            db.commit()
    return _scene_response(scene)
