import os

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

PROMETHEUS_PUSHGATEWAY_URL = os.environ.get("PROMETHEUS_PUSHGATEWAY_URL", "")

STATUS_VALUES = {"pass": 0, "warn": 1, "fail": 2}


def push_health_check(service_name: str, check_name: str, status: str) -> None:
    if status not in STATUS_VALUES:
        raise ValueError(f"status must be one of {list(STATUS_VALUES.keys())}, got '{status}'")

    registry = CollectorRegistry()
    gauge = Gauge(
        "service_health_check_status",
        "Health check status: 0=pass, 1=warn, 2=fail",
        labelnames=["service", "check_name"],
        registry=registry,
    )
    gauge.labels(service=service_name, check_name=check_name).set(STATUS_VALUES[status])
    push_to_gateway(PROMETHEUS_PUSHGATEWAY_URL, job="health_checks", registry=registry)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python push_health_check.py <service> <check_name> <pass|warn|fail>")
        sys.exit(1)
    push_health_check(
        service_name=sys.argv[1],
        check_name=sys.argv[2],
        status=sys.argv[3],
    )
    print(f"Pushed: {sys.argv[1]}/{sys.argv[2]} = {sys.argv[3]}")
