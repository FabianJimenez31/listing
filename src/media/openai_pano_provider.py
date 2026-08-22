"""OpenAI GPT Image implementation of the panorama provider contract."""
from __future__ import annotations

import base64
import os
from decimal import Decimal
from io import BytesIO

import httpx
from PIL import Image

from src.media.pano_provider import PanoResult
from src.media.pano_seam import restore_half_turn, rotate_half_turn, seam_mask


class PanoProviderError(RuntimeError):
    pass


class OpenAIPanoProvider:
    name = "openai"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("TOUR_PANO_MODEL", "gpt-image-2")
        self.quality = os.getenv("TOUR_PANO_QUALITY", "medium")
        self.size = os.getenv("TOUR_PANO_SIZE", "2048x1024")
        timeout = float(os.getenv("TOUR_PANO_TIMEOUT_SECONDS", "300"))
        self._client = client or httpx.Client(timeout=timeout)
        self._estimated_cost = Decimal(
            os.getenv("TOUR_PANO_ESTIMATED_COST_USD", "0.06000")
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def estimate_cost_usd(self, image_count: int, seam_pass: bool) -> Decimal:
        reference_surcharge = Decimal("0.003") * max(0, image_count - 1)
        cost = self._estimated_cost + reference_surcharge
        return cost * (2 if seam_pass else 1)

    @staticmethod
    def _dimensions(image_bytes: bytes) -> tuple[int, int]:
        with Image.open(BytesIO(image_bytes)) as image:
            return image.size

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        if response.status_code == 401:
            return "Credencial del proveedor inválida"
        if response.status_code == 402:
            return "El proveedor no tiene créditos disponibles"
        if response.status_code == 429:
            return "Límite de solicitudes del proveedor; intenta nuevamente"
        if response.status_code >= 500:
            return "El proveedor de imágenes no está disponible"
        try:
            payload = response.json()
            code = payload.get("error", {}).get("code", "")
            if "moderation" in code or "policy" in code:
                return "El proveedor rechazó una imagen por su política de contenido"
            detail = payload.get("error", {}).get("message")
            if detail:
                return f"El proveedor rechazó la generación: {detail[:300]}"
        except ValueError:
            pass
        return "El proveedor rechazó la generación"

    def _edit(
        self,
        images: list[bytes],
        prompt: str,
        *,
        mask: bytes | None = None,
    ) -> tuple[bytes, Decimal | None]:
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        for index, image_bytes in enumerate(images):
            try:
                with Image.open(BytesIO(image_bytes)) as source:
                    normalized = BytesIO()
                    source.convert("RGBA").save(normalized, format="PNG")
            except OSError as exc:
                raise PanoProviderError("Una foto de referencia no es una imagen válida") from exc
            files.append((
                "image[]",
                (f"reference-{index}.png", normalized.getvalue(), "image/png"),
            ))
        if mask is not None:
            files.append(("mask", ("seam-mask.png", mask, "image/png")))
        data = {
            "model": self.model,
            "prompt": prompt,
            "size": self.size,
            "quality": self.quality,
            "output_format": "png",
        }
        try:
            response = self._client.post(
                "https://api.openai.com/v1/images/edits",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=data,
                files=files,
            )
        except httpx.TimeoutException as exc:
            raise PanoProviderError("La generación excedió el tiempo límite") from exc
        except httpx.HTTPError as exc:
            raise PanoProviderError("No fue posible conectar con el proveedor") from exc
        if response.status_code >= 400:
            raise PanoProviderError(self._error_message(response))
        payload = response.json()
        try:
            image_bytes = base64.b64decode(payload["data"][0]["b64_json"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise PanoProviderError("El proveedor devolvió una respuesta sin imagen") from exc
        return image_bytes, None

    def generate(
        self,
        reference_images: list[bytes],
        prompt: str,
        *,
        seam_pass: bool,
    ) -> PanoResult:
        if not self.is_available():
            raise PanoProviderError("La generación con IA no está configurada")
        generated, cost = self._edit(reference_images, prompt)
        width, height = self._dimensions(generated)
        if seam_pass:
            rotated, width, height = rotate_half_turn(generated)
            repaired, second_cost = self._edit(
                [rotated],
                "Repara únicamente la costura vertical central y conserva sin cambios el resto de la panorámica.",
                mask=seam_mask(width, height),
            )
            generated = restore_half_turn(repaired)
            if cost is not None and second_cost is not None:
                cost += second_cost
        return PanoResult(
            pano_bytes=generated,
            width=width,
            height=height,
            hfov_deg=360.0 if seam_pass else 180.0,
            vfov_deg=180.0 if seam_pass else 90.0,
            provider=self.name,
            provider_model=self.model,
            cost_usd=cost or self.estimate_cost_usd(len(reference_images), seam_pass),
        )
