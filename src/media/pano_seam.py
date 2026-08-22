"""CPU-only helpers for the optional second-pass panorama seam repair."""
from __future__ import annotations

from io import BytesIO

from PIL import Image


def rotate_half_turn(image_bytes: bytes) -> tuple[bytes, int, int]:
    with Image.open(BytesIO(image_bytes)) as source:
        image = source.convert("RGB")
    width, height = image.size
    offset = width // 2
    rotated = Image.new("RGB", image.size)
    rotated.paste(image.crop((offset, 0, width, height)), (0, 0))
    rotated.paste(image.crop((0, 0, offset, height)), (width - offset, 0))
    output = BytesIO()
    rotated.save(output, format="PNG")
    return output.getvalue(), width, height


def seam_mask(width: int, height: int, stripe_ratio: float = 0.08) -> bytes:
    """Return an alpha mask whose transparent center stripe is repainted."""
    mask = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    pixels = mask.load()
    half = max(8, int(width * stripe_ratio / 2))
    center = width // 2
    for x in range(max(0, center - half), min(width, center + half)):
        for y in range(height):
            pixels[x, y] = (0, 0, 0, 0)
    output = BytesIO()
    mask.save(output, format="PNG")
    return output.getvalue()


def restore_half_turn(image_bytes: bytes) -> bytes:
    restored, _, _ = rotate_half_turn(image_bytes)
    return restored
