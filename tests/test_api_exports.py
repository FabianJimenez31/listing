"""Integration tests for /api/v1/exports/* (inventory download)."""
from __future__ import annotations

import io

import pytest

pytestmark = pytest.mark.integration

_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_PROPERTY_PAYLOAD = {
    "title": "Apartamento con balcón",
    "operation_type": "sale",
    "property_kind": "apartment",
    "price_amount": 35000000000,  # 350.000.000 in minor units
    "currency": "COP",
    "bedrooms": 3,
    "total_area_m2": 85.5,
}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create(client, token, **overrides):
    payload = {**_PROPERTY_PAYLOAD, **overrides}
    resp = client.post("/api/v1/properties", json=payload, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


def _csv_text(resp) -> str:
    assert resp.content.startswith(b"\xef\xbb\xbf")  # BOM so Excel reads UTF-8
    return resp.content.decode("utf-8-sig")


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

class TestExportAccess:
    def test_unauthenticated(self, client):
        assert client.get("/api/v1/exports/properties").status_code == 401

    def test_agent_cannot_export_whole_portal(self, client, agent_user, agent_token):
        resp = client.get("/api/v1/exports/properties?all=true", headers=_auth(agent_token))
        assert resp.status_code == 403

    def test_agent_exports_only_own_properties(self, client, agent_user, agent_token, admin_user, admin_token):
        _create(client, agent_token, title="Mío del agente")
        _create(client, admin_token, title="Del administrador")

        text = _csv_text(client.get("/api/v1/exports/properties?format=csv", headers=_auth(agent_token)))
        assert "Mío del agente" in text
        assert "Del administrador" not in text

    def test_admin_exports_every_owner(self, client, agent_user, agent_token, admin_user, admin_token):
        _create(client, agent_token, title="Mío del agente")
        _create(client, admin_token, title="Del administrador")

        text = _csv_text(client.get("/api/v1/exports/properties?format=csv&all=true", headers=_auth(admin_token)))
        assert "Mío del agente" in text
        assert "Del administrador" in text


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

class TestExportCsv:
    def test_headers_and_filename(self, client, agent_user, agent_token):
        _create(client, agent_token)
        resp = client.get("/api/v1/exports/properties?format=csv", headers=_auth(agent_token))
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert 'filename="inventario-' in resp.headers["content-disposition"]
        assert resp.headers["content-disposition"].endswith('.csv"')

    def test_row_content(self, client, agent_user, agent_token):
        prop = _create(client, agent_token)
        lines = _csv_text(client.get("/api/v1/exports/properties?format=csv", headers=_auth(agent_token))).splitlines()

        header, row = lines[0].split(";"), lines[1].split(";")
        assert header[0] == "ID" and "Precio" in header
        cells = dict(zip(header, row))
        assert cells["ID"] == str(prop["nid"])
        assert cells["Título"] == "Apartamento con balcón"
        assert cells["Estado"] == "Borrador"        # a fresh property is a draft
        assert cells["Operación"] == "Venta"
        assert cells["Tipo"] == "Apartamento"
        assert cells["Precio"] == "350000000"       # minor units → pesos
        assert cells["Habitaciones"] == "3"
        assert cells["Área total (m²)"] == "85,5"   # es-CO decimal separator

    def test_includes_every_status(self, client, agent_user, agent_token, admin_user, admin_token):
        prop = _create(client, agent_token, title="Publicada")
        client.post(f"/api/v1/properties/{prop['id']}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop['id']}/approve", headers=_auth(admin_token))
        _create(client, agent_token, title="Borrador sin enviar")

        text = _csv_text(client.get("/api/v1/exports/properties?format=csv", headers=_auth(agent_token)))
        assert "Publicada" in text and "Borrador sin enviar" in text

    def test_status_filter(self, client, agent_user, agent_token, admin_user, admin_token):
        prop = _create(client, agent_token, title="Publicada")
        client.post(f"/api/v1/properties/{prop['id']}/submit", headers=_auth(agent_token))
        client.post(f"/api/v1/properties/{prop['id']}/approve", headers=_auth(admin_token))
        _create(client, agent_token, title="Borrador sin enviar")

        text = _csv_text(client.get(
            "/api/v1/exports/properties?format=csv&status=published", headers=_auth(agent_token)
        ))
        assert "Publicada" in text
        assert "Borrador sin enviar" not in text

    def test_search_filters_rows(self, client, agent_user, agent_token):
        _create(client, agent_token, title="Casa campestre")
        _create(client, agent_token, title="Oficina centro")

        text = _csv_text(client.get(
            "/api/v1/exports/properties?format=csv&q=campestre", headers=_auth(agent_token)
        ))
        assert "Casa campestre" in text
        assert "Oficina centro" not in text

    def test_nid_filter(self, client, agent_user, agent_token):
        wanted = _create(client, agent_token, title="Buscada por ID")
        _create(client, agent_token, title="Otra cualquiera")

        text = _csv_text(client.get(
            f"/api/v1/exports/properties?format=csv&nid={wanted['nid']}", headers=_auth(agent_token)
        ))
        assert "Buscada por ID" in text
        assert "Otra cualquiera" not in text

    def test_empty_export_still_has_headers(self, client, agent_user, agent_token):
        lines = _csv_text(client.get("/api/v1/exports/properties?format=csv", headers=_auth(agent_token))).splitlines()
        assert lines[0].startswith("ID;Título;Estado")
        assert len(lines) == 1


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

class TestExportXlsx:
    def test_default_format_is_xlsx(self, client, agent_user, agent_token):
        _create(client, agent_token)
        resp = client.get("/api/v1/exports/properties", headers=_auth(agent_token))
        assert resp.status_code == 200
        assert resp.headers["content-type"] == _XLSX_MEDIA_TYPE
        assert resp.headers["content-disposition"].endswith('.xlsx"')
        assert resp.content[:2] == b"PK"  # xlsx is a zip container

    def test_sheet_is_readable_with_typed_cells(self, client, agent_user, agent_token):
        from openpyxl import load_workbook

        prop = _create(client, agent_token)
        resp = client.get("/api/v1/exports/properties", headers=_auth(agent_token))
        sheet = load_workbook(io.BytesIO(resp.content)).active

        assert sheet.title == "Inventario"
        headers = [cell.value for cell in sheet[1]]
        row = dict(zip(headers, [cell.value for cell in sheet[2]]))
        assert row["ID"] == prop["nid"]
        assert row["Título"] == "Apartamento con balcón"
        assert row["Precio"] == 350000000        # a number, so Excel can sum it
        assert row["Área total (m²)"] == 85.5
        assert row["Balcón"] == "No"

    def test_invalid_format_rejected(self, client, agent_user, agent_token):
        resp = client.get("/api/v1/exports/properties?format=pdf", headers=_auth(agent_token))
        assert resp.status_code == 422
