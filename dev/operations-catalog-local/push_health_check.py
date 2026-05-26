import json
import logging
import os
from datetime import datetime, timezone

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry import _logs as otel_logs

GROUNDCOVER_OTLP_ENDPOINT = os.environ.get("GROUNDCOVER_OTLP_ENDPOINT", "")
GROUNDCOVER_API_KEY = os.environ.get("GROUNDCOVER_API_KEY", "")

STATUS_VALUES = {"pass": 0, "warn": 1, "fail": 2}


def _headers():
    return {"Authorization": f"Bearer {GROUNDCOVER_API_KEY}"}


def push_health_check(service_name: str, check_name: str, status: str, detail: str = "") -> None:
    if status not in STATUS_VALUES:
        raise ValueError(f"status must be one of {list(STATUS_VALUES.keys())}, got '{status}'")

    timestamp = datetime.now(timezone.utc).isoformat()
    headers = _headers()

    metric_exporter = OTLPMetricExporter(
        endpoint=f"{GROUNDCOVER_OTLP_ENDPOINT}/v1/metrics",
        headers=headers,
    )
    reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=500)
    meter_provider = MeterProvider(metric_readers=[reader])
    gauge = meter_provider.get_meter("health_checks").create_gauge("service_health_check_status")
    gauge.set(STATUS_VALUES[status], {"service": service_name, "check_name": check_name})
    meter_provider.force_flush()
    meter_provider.shutdown()

    log_exporter = OTLPLogExporter(
        endpoint=f"{GROUNDCOVER_OTLP_ENDPOINT}/v1/logs",
        headers=headers,
    )
    log_provider = LoggerProvider()
    log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    otel_logs.set_logger_provider(log_provider)
    handler = LoggingHandler(level=logging.DEBUG, logger_provider=log_provider)
    logger = logging.getLogger(f"health_checks.{service_name}.{check_name}")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.info(json.dumps({
        "service": service_name,
        "check_name": check_name,
        "status": status,
        "detail": detail,
        "timestamp": timestamp,
    }))
    log_provider.force_flush()
    log_provider.shutdown()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python push_health_check.py <service> <check_name> <pass|warn|fail> [detail]")
        sys.exit(1)
    push_health_check(
        service_name=sys.argv[1],
        check_name=sys.argv[2],
        status=sys.argv[3],
        detail=sys.argv[4] if len(sys.argv) > 4 else "",
    )
    print(f"Pushed: {sys.argv[1]}/{sys.argv[2]} = {sys.argv[3]}")
