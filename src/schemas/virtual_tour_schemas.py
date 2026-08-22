"""Pydantic contracts for the virtual-tour API."""
from __future__ import annotations

import math
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class HotspotResponse(BaseModel):
    id: str
    from_scene_id: str
    to_scene_id: str
    yaw: float
    pitch: float
    label: str | None = None


class SceneResponse(BaseModel):
    id: str
    title: str
    position: int
    source: str
    state: str
    error_message: str | None = None
    pano_url: str | None = None
    thumb_url: str | None = None
    width: int | None = None
    height: int | None = None
    initial_yaw: float
    initial_pitch: float
    hfov_deg: float
    vfov_deg: float
    source_image_ids: list[str] = Field(default_factory=list)
    provider: str | None = None
    provider_model: str | None = None
    cost_usd: Decimal | None = None
    hotspots: list[HotspotResponse] = Field(default_factory=list)


class TourResponse(BaseModel):
    id: str
    property_id: str | None = None
    project_id: str | None = None
    status: str
    start_scene_id: str | None = None
    ai_disclaimer_ack: bool
    contains_ai: bool
    scenes: list[SceneResponse]


class TourUpdateRequest(BaseModel):
    status: Literal["draft", "published"] | None = None
    start_scene_id: str | None = None
    ai_disclaimer_ack: bool | None = None


class SceneUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=120)
    position: int | None = Field(None, ge=0)
    initial_yaw: float | None = None
    initial_pitch: float | None = None


class SceneReorderRequest(BaseModel):
    ordered_ids: list[str] = Field(min_length=1)


class HotspotInput(BaseModel):
    to_scene_id: str
    yaw: float = Field(ge=-math.pi, le=math.pi)
    pitch: float = Field(ge=-math.pi / 2, le=math.pi / 2)
    label: str | None = Field(None, max_length=120)


class HotspotReplaceRequest(BaseModel):
    hotspots: list[HotspotInput]


class SceneGenerateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    source_image_ids: list[str] = Field(min_length=1, max_length=10)
    prompt: str | None = Field(None, max_length=1000)
    seam_pass: bool = False


class ProviderInfoResponse(BaseModel):
    available: bool
    provider: str | None = None
    model: str | None = None
    quality: str | None = None
    size: str | None = None
    estimated_cost_usd: Decimal | None = None
    estimated_seam_cost_usd: Decimal | None = None
    reason: str | None = None
