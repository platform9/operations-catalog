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
        assert result["db_connectivity"]["status"] == "pass"
        assert result["queue_consumer"]["status"] == "warn"


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
        assert result["overall_status"] == "warn"
        assert len(result["checks"]) == 2
        db_check = next(c for c in result["checks"] if c["check_name"] == "db_connectivity")
        assert db_check["status"] == "pass"


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
        assert result["overall_status"] == "fail"


def test_get_service_health_no_checks_returns_pass():
    empty = {"data": {"result": []}}
    with patch("health_store.requests.get", side_effect=_mock_get(empty)):
        import health_store
        result = health_store.get_service_health("bork")
        assert result["overall_status"] == "pass"
        assert result["checks"] == []


def test_get_single_check_returns_matching_check():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_single_check("bork", "db_connectivity")
        assert result is not None
        assert result["check_name"] == "db_connectivity"
        assert result["status"] == "pass"


def test_get_single_check_returns_none_for_unknown():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_single_check("bork", "nonexistent_check")
        assert result is None
