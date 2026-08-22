"""Unit tests for virtual-tour domain invariants."""
import math

from pydantic import ValidationError
import pytest

from src.virtual_tour import (
    SceneSource,
    SceneState,
    TourScene,
    TourValidationError,
    VirtualTour,
    validate_equirectangular_aspect,
)

pytestmark = pytest.mark.unit


def test_scenes_are_ordered_and_start_falls_back_to_first_ready():
    tour = VirtualTour(scenes=[
        TourScene(id="b", title="Cocina", position=2),
        TourScene(id="a", title="Sala", position=0),
    ], start_scene_id="missing")
    assert [scene.id for scene in tour.ordered_scenes()] == ["a", "b"]
    assert tour.resolved_start_scene_id() == "a"


def test_publish_requires_ready_scene_with_url():
    tour = VirtualTour(scenes=[
        TourScene(id="a", title="Sala", state=SceneState.PENDING),
    ])
    with pytest.raises(TourValidationError, match="al menos una escena"):
        tour.validate_for_publication()


def test_ai_scene_requires_disclaimer_acknowledgement():
    tour = VirtualTour(scenes=[
        TourScene(id="a", title="Sala", source=SceneSource.AI, pano_url="https://cdn/pano.webp"),
    ])
    with pytest.raises(TourValidationError, match="contenido generado con IA"):
        tour.validate_for_publication()
    tour.ai_disclaimer_ack = True
    tour.validate_for_publication()


@pytest.mark.parametrize("width,height", [(2048, 1024), (4000, 2000), (2010, 1000)])
def test_valid_equirectangular_aspects(width, height):
    validate_equirectangular_aspect(width, height)


def test_invalid_equirectangular_aspect():
    with pytest.raises(TourValidationError, match="2:1"):
        validate_equirectangular_aspect(1920, 1080)


def test_hotspot_input_accepts_angles_in_range():
    from src.schemas.virtual_tour_schemas import HotspotInput

    spot = HotspotInput(to_scene_id="sala", yaw=3.0, pitch=-1.4)
    assert spot.yaw == 3.0
    assert spot.pitch == -1.4


@pytest.mark.parametrize("field,value", [
    ("yaw", math.pi + 0.01),
    ("yaw", -math.pi - 0.01),
    ("pitch", math.pi / 2 + 0.01),
    ("pitch", -math.pi / 2 - 0.01),
])
def test_hotspot_input_rejects_angles_out_of_range(field, value):
    from src.schemas.virtual_tour_schemas import HotspotInput

    payload = {"to_scene_id": "sala", "yaw": 0.0, "pitch": 0.0}
    payload[field] = value
    with pytest.raises(ValidationError):
        HotspotInput(**payload)
