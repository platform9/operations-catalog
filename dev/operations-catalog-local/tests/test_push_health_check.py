import json
import pytest
from unittest.mock import patch, MagicMock


def _all_patches():
    return (
        patch("push_health_check.CollectorRegistry"),
        patch("push_health_check.Gauge"),
        patch("push_health_check.push_to_gateway"),
        patch("push_health_check.requests.post"),
    )


def test_pass_sets_gauge_to_0():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge") as mock_gauge_cls, \
         patch("push_health_check.push_to_gateway"), \
         patch("push_health_check.requests.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass", "All good")
        mock_gauge_cls.return_value.labels.assert_called_once_with(service="bork", check_name="db_connectivity")
        mock_gauge_cls.return_value.labels.return_value.set.assert_called_once_with(0)


def test_warn_sets_gauge_to_1():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge") as mock_gauge_cls, \
         patch("push_health_check.push_to_gateway"), \
         patch("push_health_check.requests.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        from push_health_check import push_health_check
        push_health_check("bork", "queue_consumer", "warn", "High lag")
        mock_gauge_cls.return_value.labels.return_value.set.assert_called_once_with(1)


def test_fail_sets_gauge_to_2():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge") as mock_gauge_cls, \
         patch("push_health_check.push_to_gateway"), \
         patch("push_health_check.requests.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "fail", "Connection refused")
        mock_gauge_cls.return_value.labels.return_value.set.assert_called_once_with(2)


def test_invalid_status_raises_value_error():
    from push_health_check import push_health_check
    with pytest.raises(ValueError, match="status must be one of"):
        push_health_check("bork", "db_connectivity", "unknown")


def test_detail_is_optional():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge"), \
         patch("push_health_check.push_to_gateway"), \
         patch("push_health_check.requests.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass")


def test_pushes_log_to_loki_with_correct_payload():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge"), \
         patch("push_health_check.push_to_gateway"), \
         patch("push_health_check.requests.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass", "All good")
        args, kwargs = mock_post.call_args
        assert "loki/api/v1/push" in args[0]
        stream = kwargs["json"]["streams"][0]
        assert stream["stream"]["service"] == "bork"
        assert stream["stream"]["check_name"] == "db_connectivity"
        log_entry = json.loads(stream["values"][0][1])
        assert log_entry["status"] == "pass"
        assert log_entry["detail"] == "All good"
