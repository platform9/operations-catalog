import json
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

LOG_LINE_DB = json.dumps({
    "service": "bork", "check_name": "db_connectivity",
    "status": "pass", "detail": "Connected in 12ms", "timestamp": "2026-05-26T10:00:00Z"
})
LOG_LINE_QUEUE = json.dumps({
    "service": "bork", "check_name": "queue_consumer",
    "status": "warn", "detail": "Lag at 4500", "timestamp": "2026-05-26T09:58:00Z"
})
LOGS_RESPONSE = {
    "data": {
        "result": [
            {
                "stream": {"service": "bork"},
                "values": [
                    ["1716720000000000000", LOG_LINE_DB],
                    ["1716719880000000000", LOG_LINE_QUEUE],
                ],
            }
        ]
    }
}


def _mock_get(metrics_resp, logs_resp):
    def side_effect(url, **kwargs):
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        if "loki" in url:
            mock.json.return_value = logs_resp
        else:
            mock.json.return_value = metrics_resp
        return mock
    return side_effect


def test_query_metrics_maps_values_to_status():
    with patch("groundcover.requests.get", side_effect=_mock_get(METRICS_RESPONSE, LOGS_RESPONSE)):
        import groundcover
        result = groundcover._query_metrics("bork")
        assert result == {"db_connectivity": "pass", "queue_consumer": "warn"}


def test_query_logs_returns_latest_detail_per_check():
    with patch("groundcover.requests.get", side_effect=_mock_get(METRICS_RESPONSE, LOGS_RESPONSE)):
        import groundcover
        result = groundcover._query_logs("bork")
        assert result["db_connectivity"]["detail"] == "Connected in 12ms"
        assert result["queue_consumer"]["detail"] == "Lag at 4500"
        assert result["db_connectivity"]["last_updated"] == "2026-05-26T10:00:00Z"


def test_get_service_health_returns_combined_result():
    with patch("groundcover.requests.get", side_effect=_mock_get(METRICS_RESPONSE, LOGS_RESPONSE)):
        import groundcover
        result = groundcover.get_service_health("bork")
        assert result["service"] == "bork"
        assert result["overall_status"] == "warn"
        assert len(result["checks"]) == 2
        db_check = next(c for c in result["checks"] if c["check_name"] == "db_connectivity")
        assert db_check["status"] == "pass"
        assert db_check["detail"] == "Connected in 12ms"


def test_get_service_health_overall_fail_takes_priority():
    fail_metrics = {
        "data": {
            "result": [
                {"metric": {"service": "bork", "check_name": "check_a"}, "value": [0, "0"]},
                {"metric": {"service": "bork", "check_name": "check_b"}, "value": [0, "2"]},
            ]
        }
    }
    empty_logs = {"data": {"result": []}}
    with patch("groundcover.requests.get", side_effect=_mock_get(fail_metrics, empty_logs)):
        import groundcover
        result = groundcover.get_service_health("bork")
        assert result["overall_status"] == "fail"


def test_get_service_health_no_checks_returns_pass():
    empty = {"data": {"result": []}}
    with patch("groundcover.requests.get", side_effect=_mock_get(empty, empty)):
        import groundcover
        result = groundcover.get_service_health("bork")
        assert result["overall_status"] == "pass"
        assert result["checks"] == []


def test_get_single_check_returns_matching_check():
    with patch("groundcover.requests.get", side_effect=_mock_get(METRICS_RESPONSE, LOGS_RESPONSE)):
        import groundcover
        result = groundcover.get_single_check("bork", "db_connectivity")
        assert result is not None
        assert result["check_name"] == "db_connectivity"
        assert result["status"] == "pass"


def test_get_single_check_returns_none_for_unknown():
    with patch("groundcover.requests.get", side_effect=_mock_get(METRICS_RESPONSE, LOGS_RESPONSE)):
        import groundcover
        result = groundcover.get_single_check("bork", "nonexistent_check")
        assert result is None
