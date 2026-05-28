import pytest
from unittest.mock import patch, MagicMock

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


CATALOG_COLUMNS = [
    "id", "serviceName", "health", "description", "status", "serviceCategory",
    "serviceSubjectMatterExperts", "criticalDependencies", "documentation",
    "SLA", "targetAudience", "requestsChannel", "incidentManagement",
    "monitoringTools", "activeMaintenanceWindows", "onboardingDocumentation",
    "costModel", "versionInformation", "deprecationPolicy",
]

BORK_ROW = (
    1, "bork", None, "Test service", "Active", None,
    None, None, None, None, None, None, None, None, None, None, None, None, None,
)

ENRICHED_HEALTH = {"prom_health": "green", "overall_status": "pass", "checks": []}


def _make_db_mock(row):
    mock_cursor = MagicMock()
    mock_cursor.description = [(col,) for col in CATALOG_COLUMNS]
    mock_cursor.fetchone.return_value = row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


def test_get_by_name_health_is_enriched(client):
    with patch("app.get_db", return_value=_make_db_mock(BORK_ROW)), \
         patch("app.enrich_entry", side_effect=lambda e: {**e, "health": ENRICHED_HEALTH}):
        resp = client.get("/catalog/name/bork")
        assert resp.status_code == 200
        assert resp.get_json()["health"] == ENRICHED_HEALTH


def test_get_by_id_health_is_enriched(client):
    with patch("app.get_db", return_value=_make_db_mock(BORK_ROW)), \
         patch("app.enrich_entry", side_effect=lambda e: {**e, "health": ENRICHED_HEALTH}):
        resp = client.get("/catalog/1")
        assert resp.status_code == 200
        assert resp.get_json()["health"] == ENRICHED_HEALTH


def _make_push_db_mock(found=True):
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = (1,) if found else None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


def test_push_health_check_returns_200(client):
    with patch("app.get_db", return_value=_make_push_db_mock(found=True)), \
         patch("app.push_health_check"):
        resp = client.post(
            "/catalog/name/bork/health",
            json={"check_name": "db_connectivity", "status": "pass"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pushed"] is True
        assert data["service"] == "bork"
        assert data["check_name"] == "db_connectivity"
        assert data["status"] == "pass"


def test_push_health_check_returns_404_when_service_missing(client):
    with patch("app.get_db", return_value=_make_push_db_mock(found=False)):
        resp = client.post(
            "/catalog/name/nonexistent/health",
            json={"check_name": "db_connectivity", "status": "pass"},
        )
        assert resp.status_code == 404


def test_push_health_check_returns_400_on_invalid_status(client):
    resp = client.post(
        "/catalog/name/bork/health",
        json={"check_name": "db_connectivity", "status": "broken"},
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_push_health_check_returns_502_on_pushgateway_failure(client):
    with patch("app.get_db", return_value=_make_push_db_mock(found=True)), \
         patch("app.push_health_check", side_effect=Exception("connection refused")):
        resp = client.post(
            "/catalog/name/bork/health",
            json={"check_name": "db_connectivity", "status": "pass"},
        )
        assert resp.status_code == 502
        assert "error" in resp.get_json()
