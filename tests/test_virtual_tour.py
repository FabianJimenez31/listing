"""Unit tests for virtual-tour domain invariants."""
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
