"""Validate and optimize equirectangular panorama assets on CPU."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from src.virtual_tour import TourValidationError, validate_equirectangular_aspect

MAX_PANO_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class PanoAssets:
    pano_bytes: bytes
    thumb_bytes: bytes
    width: int
    height: int


def build_pano_assets(file_bytes: bytes) -> PanoAssets:
    if not file_bytes:
        raise TourValidationError("La imagen panorámica está vacía")
    if len(file_bytes) > MAX_PANO_BYTES:
        raise TourValidationError("La panorámica supera el límite de 25 MB")
    try:
        with Image.open(BytesIO(file_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise TourValidationError("El archivo no es una imagen válida") from exc

    width, height = image.size
    validate_equirectangular_aspect(width, height)

    pano_buffer = BytesIO()
    image.save(pano_buffer, format="WEBP", quality=88, method=4)

    thumb = image.copy()
    thumb.thumbnail((640, 320), Image.Resampling.LANCZOS)
    thumb_buffer = BytesIO()
    thumb.save(thumb_buffer, format="WEBP", quality=78, method=4)
    return PanoAssets(pano_buffer.getvalue(), thumb_buffer.getvalue(), width, height)
