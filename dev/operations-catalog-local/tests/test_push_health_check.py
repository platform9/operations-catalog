import pytest
from unittest.mock import patch, MagicMock


def test_pass_sets_gauge_to_0():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge") as mock_gauge_cls, \
         patch("push_health_check.push_to_gateway"):
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass")
        mock_gauge_cls.return_value.labels.assert_called_once_with(service="bork", check_name="db_connectivity")
        mock_gauge_cls.return_value.labels.return_value.set.assert_called_once_with(0)


def test_warn_sets_gauge_to_1():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge") as mock_gauge_cls, \
         patch("push_health_check.push_to_gateway"):
        from push_health_check import push_health_check
        push_health_check("bork", "queue_consumer", "warn")
        mock_gauge_cls.return_value.labels.return_value.set.assert_called_once_with(1)


def test_fail_sets_gauge_to_2():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge") as mock_gauge_cls, \
         patch("push_health_check.push_to_gateway"):
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "fail")
        mock_gauge_cls.return_value.labels.return_value.set.assert_called_once_with(2)


def test_invalid_status_raises_value_error():
    from push_health_check import push_health_check
    with pytest.raises(ValueError, match="status must be one of"):
        push_health_check("bork", "db_connectivity", "unknown")


def test_pushes_to_gateway_with_correct_job():
    with patch("push_health_check.CollectorRegistry"), \
         patch("push_health_check.Gauge"), \
         patch("push_health_check.push_to_gateway") as mock_push:
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass")
        mock_push.assert_called_once()
        assert mock_push.call_args[1]["job"] == "health_checks"
