import pytest
from unittest.mock import patch

MOCK_HEALTH = {
    "service": "bork",
    "overall_status": "warn",
    "checks": [
        {"check_name": "db_connectivity", "status": "pass", "last_updated": "2026-05-26T10:00:00Z"},
        {"check_name": "queue_consumer", "status": "warn", "last_updated": "2026-05-26T09:58:00Z"},
    ],
}

MOCK_CHECK = {
    "check_name": "db_connectivity",
    "status": "pass",
    "last_updated": "2026-05-26T10:00:00Z",
}


def test_get_service_health_returns_200(client):
    with patch("app.get_service_health", return_value=MOCK_HEALTH):
        resp = client.get("/catalog/name/bork/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "bork"
        assert data["overall_status"] == "warn"
        assert len(data["checks"]) == 2


def test_get_service_health_returns_502_on_error(client):
    with patch("app.get_service_health", side_effect=Exception("prometheus unavailable")):
        resp = client.get("/catalog/name/bork/health")
        assert resp.status_code == 502
        assert "error" in resp.get_json()


def test_get_single_health_check_returns_200(client):
    with patch("app.get_single_check", return_value=MOCK_CHECK):
        resp = client.get("/catalog/name/bork/health/db_connectivity")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["check_name"] == "db_connectivity"
        assert data["status"] == "pass"


def test_get_single_health_check_returns_404_when_not_found(client):
    with patch("app.get_single_check", return_value=None):
        resp = client.get("/catalog/name/bork/health/nonexistent")
        assert resp.status_code == 404


def test_get_single_health_check_returns_502_on_error(client):
    with patch("app.get_single_check", side_effect=Exception("prometheus unavailable")):
        resp = client.get("/catalog/name/bork/health/db_connectivity")
        assert resp.status_code == 502
        assert "error" in resp.get_json()
