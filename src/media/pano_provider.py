"""Provider-neutral contract and runtime selection for panorama generation."""
from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PanoResult:
    pano_bytes: bytes
    width: int
    height: int
    hfov_deg: float
    vfov_deg: float
    provider: str
    provider_model: str
    cost_usd: Decimal | None


class PanoProvider(Protocol):
    name: str
    model: str
    quality: str
    size: str

    def is_available(self) -> bool: ...

    def estimate_cost_usd(self, image_count: int, seam_pass: bool) -> Decimal: ...

    def generate(
        self,
        reference_images: list[bytes],
        prompt: str,
        *,
        seam_pass: bool,
    ) -> PanoResult: ...


def resolve_provider() -> PanoProvider | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from src.media.openai_pano_provider import OpenAIPanoProvider

    return OpenAIPanoProvider()
