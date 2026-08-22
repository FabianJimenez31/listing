"""Pure domain rules for virtual tours, scenes, and navigation hotspots."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

# Banda de piso estilo Matterport: las flechas de navegacion viven cerca del
# horizonte inferior, nunca a media pared ni mas alla de los polos.
FLOOR_PITCH_LOW = math.radians(-85)
FLOOR_PITCH_HIGH = math.radians(-60)


def normalize_yaw(yaw: float) -> float:
    """Wrap any yaw angle into (-pi, pi]."""
    return math.atan2(math.sin(yaw), math.cos(yaw))


def normalize_floor_pitch(pitch: float) -> float:
    """Clamp any pitch angle into the floor band."""
    return max(FLOOR_PITCH_LOW, min(FLOOR_PITCH_HIGH, pitch))


class TourStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class SceneSource(str, Enum):
    UPLOAD = "upload"
    AI = "ai"


class SceneState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class TourValidationError(ValueError):
    """Raised when a tour violates a product-level invariant."""


@dataclass(slots=True)
class TourHotspot:
    from_scene_id: str
    to_scene_id: str
    yaw: float
    pitch: float
    label: str | None = None


@dataclass(slots=True)
class TourScene:
    id: str
    title: str
    position: int = 0
    source: SceneSource = SceneSource.UPLOAD
    state: SceneState = SceneState.READY
    pano_url: str | None = None
    hotspots: list[TourHotspot] = field(default_factory=list)


@dataclass(slots=True)
class VirtualTour:
    scenes: list[TourScene] = field(default_factory=list)
    start_scene_id: str | None = None
    ai_disclaimer_ack: bool = False

    def ordered_scenes(self) -> list[TourScene]:
        return sorted(self.scenes, key=lambda scene: (scene.position, scene.id))

    def resolved_start_scene_id(self) -> str | None:
        ready = [scene for scene in self.ordered_scenes() if scene.state == SceneState.READY]
        if self.start_scene_id and any(scene.id == self.start_scene_id for scene in ready):
            return self.start_scene_id
        return ready[0].id if ready else None

    def validate_for_publication(self) -> None:
        ready = [
            scene for scene in self.scenes
            if scene.state == SceneState.READY and bool(scene.pano_url)
        ]
        if not ready:
            raise TourValidationError("El tour necesita al menos una escena lista para publicarse")
        if any(scene.source == SceneSource.AI for scene in ready) and not self.ai_disclaimer_ack:
            raise TourValidationError("Debes aceptar el aviso de contenido generado con IA")


def validate_equirectangular_aspect(width: int, height: int, tolerance: float = 0.10) -> None:
    """Validate an approximately 2:1 equirectangular image."""
    if width <= 0 or height <= 0:
        raise TourValidationError("La imagen panorámica no tiene dimensiones válidas")
    ratio = width / height
    if abs(ratio - 2.0) > tolerance:
        raise TourValidationError(
            f"La panorámica debe tener relación aproximada 2:1; se recibió {width}x{height}"
        )
