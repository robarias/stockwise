"""Pruebas unitarias para el servicio de auditoría de recursos educativos."""

from unittest.mock import MagicMock, patch

import requests

from stockwise.services.education_auditor import (
    audit_educational_catalog,
    generate_markdown_summary,
    validate_single_url,
)


def test_validate_single_url_active():
    with patch("requests.head") as mock_head:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/edu"
        mock_resp.elapsed.total_seconds.return_value = 0.15
        mock_head.return_value = mock_resp

        res = validate_single_url("https://example.com/edu")
        assert res["status"] == "active"
        assert res["status_code"] == 200
        assert res["latency_ms"] >= 0
        assert res["error_detail"] is None


def test_validate_single_url_head_405_get_fallback():
    with patch("requests.head") as mock_head, patch("requests.get") as mock_get:
        head_resp = MagicMock()
        head_resp.status_code = 405
        mock_head.return_value = head_resp

        get_resp = MagicMock()
        get_resp.status_code = 200
        get_resp.url = "https://example.com/fallback"
        get_resp.elapsed.total_seconds.return_value = 0.22
        mock_get.return_value = get_resp

        res = validate_single_url("https://example.com/fallback")
        assert res["status"] == "active"
        assert res["status_code"] == 200


def test_validate_single_url_broken_404():
    with patch("requests.head") as mock_head, patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.url = "https://example.com/missing"
        mock_resp.elapsed.total_seconds.return_value = 0.1
        mock_head.return_value = mock_resp
        mock_get.return_value = mock_resp

        res = validate_single_url("https://example.com/missing")
        assert res["status"] == "broken"
        assert res["status_code"] == 404
        assert "404" in res["error_detail"]


def test_validate_single_url_timeout():
    with patch("requests.head", side_effect=requests.Timeout("Timed out")):
        res = validate_single_url("https://example.com/slow", timeout=1.0)
        assert res["status"] == "error"
        assert res["status_code"] is None
        assert "agotado" in res["error_detail"]


def test_audit_educational_catalog_mocked(tmp_path):
    catalog_content = {
        "version": "1.0",
        "updated_at": "2026-10-09",
        "resources": [
            {
                "id": "item1",
                "title": "Recurso 1",
                "url": "https://example.com/item1",
                "category": "Básicos",
                "status": "active",
            },
            {
                "id": "item2",
                "title": "Recurso 2",
                "url": "https://example.com/item2",
                "category": "Avanzado",
                "status": "active",
            },
        ],
    }

    import json
    catalog_file = tmp_path / "test_catalog.json"
    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(catalog_content, f)

    def mock_val(url, timeout=8.0):
        if "item1" in url:
            return {"status": "active", "status_code": 200, "latency_ms": 120.0, "redirect_url": None, "error_detail": None}
        return {"status": "broken", "status_code": 404, "latency_ms": 110.0, "redirect_url": None, "error_detail": "Not Found"}

    with patch("stockwise.services.education_auditor.validate_single_url", side_effect=mock_val):
        summary = audit_educational_catalog(catalog_path=catalog_file, update_in_place=True)

        assert summary["total_resources"] == 2
        assert summary["active_resources"] == 1
        assert summary["broken_resources"] == 1
        assert summary["health_score_pct"] == 50.0

        # Verificar que el archivo JSON fue actualizado en el disco
        with open(catalog_file, encoding="utf-8") as f:
            updated_data = json.load(f)
        status_map = {r["id"]: r["status"] for r in updated_data["resources"]}
        assert status_map["item1"] == "active"
        assert status_map["item2"] == "broken"


def test_generate_markdown_summary():
    summary_data = {
        "timestamp": "2026-10-09",
        "total_resources": 2,
        "active_resources": 2,
        "broken_resources": 0,
        "health_score_pct": 100.0,
        "items": [
            {
                "title": "Khan Academy",
                "url": "https://es.khanacademy.org",
                "category": "Básicos",
                "current_status": "active",
                "status_code": 200,
                "latency_ms": 95.0,
                "error_detail": None,
            }
        ],
    }
    md = generate_markdown_summary(summary_data)
    assert "Auditoría de Recursos Educativos" in md
    assert "100.0%" in md
    assert "Khan Academy" in md
    assert "200" in md
