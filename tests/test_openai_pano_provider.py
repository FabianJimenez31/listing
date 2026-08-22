"""Provider tests use an in-memory HTTP transport and spend no API credits."""
from __future__ import annotations

import base64
import io

import httpx
import pytest
from PIL import Image

from src.media.openai_pano_provider import OpenAIPanoProvider, PanoProviderError

pytestmark = pytest.mark.unit


def _image() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (800, 400), (120, 90, 60)).save(output, format="PNG")
    return output.getvalue()


def test_generate_decodes_image_and_declares_partial_coverage(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, json={"data": [{"b64_json": base64.b64encode(_image()).decode()}]}, request=request,
    ))
    provider = OpenAIPanoProvider(httpx.Client(transport=transport))
    result = provider.generate([_image()], "Panorama de una sala", seam_pass=False)
    assert result.width == 800
    assert result.height == 400
    assert result.hfov_deg == 180
    assert result.cost_usd is not None


def test_rate_limit_has_legible_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    transport = httpx.MockTransport(lambda request: httpx.Response(429, request=request))
    provider = OpenAIPanoProvider(httpx.Client(transport=transport))
    with pytest.raises(PanoProviderError, match="Límite de solicitudes"):
        provider.generate([_image()], "Panorama", seam_pass=False)


@pytest.mark.parametrize(
    "handler,message",
    [
        (lambda request: httpx.Response(503, request=request), "no está disponible"),
        (lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("slow", request=request)), "tiempo límite"),
    ],
)
def test_provider_outages_are_legible(monkeypatch, handler, message):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = OpenAIPanoProvider(httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(PanoProviderError, match=message):
        provider.generate([_image()], "Panorama", seam_pass=False)
