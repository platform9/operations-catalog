import json
import os
import requests
from datetime import datetime, timezone

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

PROMETHEUS_PUSHGATEWAY_URL = os.environ.get("PROMETHEUS_PUSHGATEWAY_URL", "")
LOKI_URL = os.environ.get("LOKI_URL", "")

STATUS_VALUES = {"pass": 0, "warn": 1, "fail": 2}


def push_health_check(service_name: str, check_name: str, status: str, detail: str = "") -> None:
    if status not in STATUS_VALUES:
        raise ValueError(f"status must be one of {list(STATUS_VALUES.keys())}, got '{status}'")

    timestamp = datetime.now(timezone.utc)

    # Push metric to Prometheus Pushgateway
    registry = CollectorRegistry()
    gauge = Gauge(
        "service_health_check_status",
        "Health check status: 0=pass, 1=warn, 2=fail",
        labelnames=["service", "check_name"],
        registry=registry,
    )
    gauge.labels(service=service_name, check_name=check_name).set(STATUS_VALUES[status])
    push_to_gateway(PROMETHEUS_PUSHGATEWAY_URL, job="health_checks", registry=registry)

    # Push log event to Loki
    payload = {
        "streams": [
            {
                "stream": {"service": service_name, "check_name": check_name},
                "values": [
                    [
                        str(int(timestamp.timestamp() * 1e9)),
                        json.dumps({
                            "service": service_name,
                            "check_name": check_name,
                            "status": status,
                            "detail": detail,
                            "timestamp": timestamp.isoformat(),
                        }),
                    ]
                ],
            }
        ]
    }
    resp = requests.post(
        f"{LOKI_URL}/loki/api/v1/push",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()


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
