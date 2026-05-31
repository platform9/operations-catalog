import pytest
from unittest.mock import patch, MagicMock


METRICS_RESPONSE = {
    "data": {
        "result": [
            {"metric": {"service": "bork", "check_name": "db_connectivity"}, "value": [1716720000, "0"]},
            {"metric": {"service": "bork", "check_name": "queue_consumer"}, "value": [1716720000, "1"]},
        ]
    }
}


def _mock_get(metrics_resp):
    def side_effect(url, **kwargs):
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        mock.json.return_value = metrics_resp
        return mock
    return side_effect


def test_query_metrics_maps_values_to_status():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store._query_metrics("bork")
        assert result["db_connectivity"]["status"] == "green"
        assert result["queue_consumer"]["status"] == "yellow"


def test_query_metrics_includes_timestamp():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store._query_metrics("bork")
        assert "last_updated" in result["db_connectivity"]
        assert result["db_connectivity"]["last_updated"].startswith("2024-")


def test_get_service_health_returns_checks():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_service_health("bork")
        assert result["service"] == "bork"
        assert result["overall_status"] == "yellow"
        assert len(result["checks"]) == 2
        db_check = next(c for c in result["checks"] if c["check_name"] == "db_connectivity")
        assert db_check["status"] == "green"


def test_get_service_health_overall_fail_takes_priority():
    fail_metrics = {
        "data": {
            "result": [
                {"metric": {"service": "bork", "check_name": "check_a"}, "value": [1716720000, "0"]},
                {"metric": {"service": "bork", "check_name": "check_b"}, "value": [1716720000, "2"]},
            ]
        }
    }
    with patch("health_store.requests.get", side_effect=_mock_get(fail_metrics)):
        import health_store
        result = health_store.get_service_health("bork")
        assert result["overall_status"] == "red"


def test_get_service_health_no_checks_returns_pass():
    empty = {"data": {"result": []}}
    with patch("health_store.requests.get", side_effect=_mock_get(empty)):
        import health_store
        result = health_store.get_service_health("bork")
        assert result["overall_status"] == "green"
        assert result["checks"] == []


def test_get_single_check_returns_matching_check():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_single_check("bork", "db_connectivity")
        assert result is not None
        assert result["check_name"] == "db_connectivity"
        assert result["status"] == "green"


def test_get_single_check_returns_none_for_unknown():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_single_check("bork", "nonexistent_check")
        assert result is None


def test_enrich_entry_replaces_health_on_success():
    mock_health = {
        "service": "bork",
        "overall_status": "green",
        "checks": [{"check_name": "db_connectivity", "status": "green", "last_updated": "2026-05-27T10:00:00+00:00"}],
    }
    with patch("health_store.get_service_health", return_value=mock_health), \
         patch("health_store._query_quality_score", return_value=0.85):
        import health_store
        entry = {"serviceName": "bork", "health": "http://grafana/bork", "description": "test"}
        result = health_store.enrich_entry(entry)
        assert result["health"]["prom_health"] == "green"
        assert result["health"]["overall_status"] == "green"
        assert result["health"]["checks"] == mock_health["checks"]
        assert result["health"]["quality_score"] == 0.85
        assert result["health"]["quality_score_interval_minutes"] == 10
        assert result["description"] == "test"  # other fields unchanged


def test_enrich_entry_quality_score_null_when_absent():
    mock_health = {
        "service": "bork",
        "overall_status": "green",
        "checks": [],
    }
    with patch("health_store.get_service_health", return_value=mock_health), \
         patch("health_store._query_quality_score", return_value=None):
        import health_store
        entry = {"serviceName": "bork", "health": None, "description": "no status page"}
        result = health_store.enrich_entry(entry)
        assert result["health"]["quality_score"] is None
        assert result["health"]["quality_score_interval_minutes"] == 10


def test_enrich_entry_sets_prom_health_red_on_failure():
    with patch("health_store.get_service_health", side_effect=Exception("connection refused")):
        import health_store
        entry = {"serviceName": "bork", "health": "http://grafana/bork", "description": "test"}
        result = health_store.enrich_entry(entry)
        assert result["health"] == {"prom_health": "red"}
        assert result["description"] == "test"  # other fields unchanged
