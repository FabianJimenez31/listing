"""Unit tests for virtual-tour domain invariants."""
import math

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


def test_hotspot_input_accepts_any_angle():
    from src.schemas.virtual_tour_schemas import HotspotInput

    spot = HotspotInput(to_scene_id="sala", yaw=10313.2, pitch=-229.2)
    assert spot.yaw == 10313.2
    assert spot.pitch == -229.2


def test_normalize_yaw_wraps_full_turns():
    from src.virtual_tour import normalize_yaw

    wrapped = normalize_yaw(math.radians(10313.2))
    assert math.degrees(wrapped) == pytest.approx(-126.8, abs=0.1)
    assert -math.pi < wrapped <= math.pi


@pytest.mark.parametrize("yaw_deg", [0, 190, -190, 720, -2578.3, 10313.2])
def test_normalize_yaw_stays_in_range(yaw_deg):
    from src.virtual_tour import normalize_yaw

    assert -math.pi < normalize_yaw(math.radians(yaw_deg)) <= math.pi


@pytest.mark.parametrize("pitch_deg", [0, 30, -45, -120, -229.2, 500])
def test_normalize_floor_pitch_clamps_to_band(pitch_deg):
    from src.virtual_tour import FLOOR_PITCH_HIGH, FLOOR_PITCH_LOW, normalize_floor_pitch

    clamped = normalize_floor_pitch(math.radians(pitch_deg))
    assert FLOOR_PITCH_LOW <= clamped <= FLOOR_PITCH_HIGH
