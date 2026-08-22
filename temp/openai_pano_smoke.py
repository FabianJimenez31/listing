"""One-shot GPT Image panorama smoke test using an existing listing photo."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from src.media.openai_pano_provider import OpenAIPanoProvider
from src.media.pano_assets import build_pano_assets


def main() -> None:
    source_path = Path(sys.argv[1])
    output_dir = Path("/app/temp/uploads/tour-ai-smoke")
    output_dir.mkdir(parents=True, exist_ok=True)

    provider = OpenAIPanoProvider()
    started = time.monotonic()
    result = provider.generate(
        [source_path.read_bytes()],
        (
            "Create a realistic 2:1 equirectangular virtual-tour panorama from this "
            "kitchen reference. Preserve the cabinetry, black countertops, appliances, "
            "windows, materials, colors, and natural lighting. Extend the room plausibly "
            "to the left and right from a central camera position, with straight verticals "
            "and coherent perspective. Do not add people, text, logos, or new architectural "
            "features. The result must be suitable for an interactive property-tour viewer."
        ),
        seam_pass=False,
    )
    assets = build_pano_assets(result.pano_bytes)
    pano_path = output_dir / "kitchen-gpt-image-2-medium.webp"
    thumb_path = output_dir / "kitchen-gpt-image-2-medium-thumb.webp"
    pano_path.write_bytes(assets.pano_bytes)
    thumb_path.write_bytes(assets.thumb_bytes)
    print(json.dumps({
        "provider": result.provider,
        "model": result.provider_model,
        "width": assets.width,
        "height": assets.height,
        "hfov_deg": result.hfov_deg,
        "vfov_deg": result.vfov_deg,
        "estimated_cost_usd": str(result.cost_usd),
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "pano_path": str(pano_path),
        "thumb_path": str(thumb_path),
    }))


if __name__ == "__main__":
    main()
