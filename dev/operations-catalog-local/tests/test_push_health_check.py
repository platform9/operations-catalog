import pytest
from unittest.mock import patch, MagicMock


def test_pass_sets_gauge_to_0():
    with patch("push_health_check.OTLPMetricExporter"), \
         patch("push_health_check.PeriodicExportingMetricReader"), \
         patch("push_health_check.MeterProvider") as mock_mp, \
         patch("push_health_check.OTLPLogExporter"), \
         patch("push_health_check.BatchLogRecordProcessor"), \
         patch("push_health_check.LoggerProvider"), \
         patch("push_health_check.otel_logs"):
        mock_gauge = mock_mp.return_value.get_meter.return_value.create_gauge.return_value
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass", "All good")
        mock_gauge.set.assert_called_once_with(0, {"service": "bork", "check_name": "db_connectivity"})


def test_warn_sets_gauge_to_1():
    with patch("push_health_check.OTLPMetricExporter"), \
         patch("push_health_check.PeriodicExportingMetricReader"), \
         patch("push_health_check.MeterProvider") as mock_mp, \
         patch("push_health_check.OTLPLogExporter"), \
         patch("push_health_check.BatchLogRecordProcessor"), \
         patch("push_health_check.LoggerProvider"), \
         patch("push_health_check.otel_logs"):
        mock_gauge = mock_mp.return_value.get_meter.return_value.create_gauge.return_value
        from push_health_check import push_health_check
        push_health_check("bork", "queue_consumer", "warn", "High lag")
        mock_gauge.set.assert_called_once_with(1, {"service": "bork", "check_name": "queue_consumer"})


def test_fail_sets_gauge_to_2():
    with patch("push_health_check.OTLPMetricExporter"), \
         patch("push_health_check.PeriodicExportingMetricReader"), \
         patch("push_health_check.MeterProvider") as mock_mp, \
         patch("push_health_check.OTLPLogExporter"), \
         patch("push_health_check.BatchLogRecordProcessor"), \
         patch("push_health_check.LoggerProvider"), \
         patch("push_health_check.otel_logs"):
        mock_gauge = mock_mp.return_value.get_meter.return_value.create_gauge.return_value
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "fail", "Connection refused")
        mock_gauge.set.assert_called_once_with(2, {"service": "bork", "check_name": "db_connectivity"})


def test_invalid_status_raises_value_error():
    from push_health_check import push_health_check
    with pytest.raises(ValueError, match="status must be one of"):
        push_health_check("bork", "db_connectivity", "unknown")


def test_detail_is_optional():
    with patch("push_health_check.OTLPMetricExporter"), \
         patch("push_health_check.PeriodicExportingMetricReader"), \
         patch("push_health_check.MeterProvider"), \
         patch("push_health_check.OTLPLogExporter"), \
         patch("push_health_check.BatchLogRecordProcessor"), \
         patch("push_health_check.LoggerProvider"), \
         patch("push_health_check.otel_logs"):
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass")


def test_metric_provider_is_flushed_and_shutdown():
    with patch("push_health_check.OTLPMetricExporter"), \
         patch("push_health_check.PeriodicExportingMetricReader"), \
         patch("push_health_check.MeterProvider") as mock_mp, \
         patch("push_health_check.OTLPLogExporter"), \
         patch("push_health_check.BatchLogRecordProcessor"), \
         patch("push_health_check.LoggerProvider"), \
         patch("push_health_check.otel_logs"):
        from push_health_check import push_health_check
        push_health_check("bork", "db_connectivity", "pass")
        mock_mp.return_value.force_flush.assert_called_once()
        mock_mp.return_value.shutdown.assert_called_once()
