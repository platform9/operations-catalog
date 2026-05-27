import json
import os
import requests
from datetime import datetime, timedelta, timezone

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "")
LOKI_URL = os.environ.get("LOKI_URL", "")

STATUS_MAP = {0: "pass", 1: "warn", 2: "fail"}
STATUS_RANK = {"pass": 0, "warn": 1, "fail": 2}


def _query_metrics(service_name):
    url = f"{PROMETHEUS_URL}/api/v1/query"
    query = f'service_health_check_status{{service="{service_name}"}}'
    resp = requests.get(url, params={"query": query}, timeout=10)
    resp.raise_for_status()
    results = {}
    for result in resp.json().get("data", {}).get("result", []):
        check_name = result["metric"].get("check_name")
        value = int(float(result["value"][1]))
        if check_name:
            results[check_name] = STATUS_MAP.get(value, "unknown")
    return results


def _query_logs(service_name):
    url = f"{LOKI_URL}/loki/api/v1/query_range"
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)
    params = {
        "query": f'{{service="{service_name}"}} | json',
        "start": int(start.timestamp()),
        "end": int(now.timestamp()),
        "limit": 1000,
        "direction": "backward",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    seen = {}
    for stream in resp.json().get("data", {}).get("result", []):
        for _ts_ns, line in stream.get("values", []):
            try:
                entry = json.loads(line)
                check_name = entry.get("check_name")
                if check_name and check_name not in seen:
                    seen[check_name] = {
                        "detail": entry.get("detail", ""),
                        "last_updated": entry.get("timestamp", ""),
                    }
            except (json.JSONDecodeError, KeyError):
                continue
    return seen


def get_service_health(service_name):
    statuses = _query_metrics(service_name)
    details = _query_logs(service_name)
    checks = []
    for check_name, status in statuses.items():
        log = details.get(check_name, {})
        checks.append({
            "check_name": check_name,
            "status": status,
            "detail": log.get("detail", ""),
            "last_updated": log.get("last_updated", ""),
        })
    overall = "pass"
    for check in checks:
        if STATUS_RANK.get(check["status"], 0) > STATUS_RANK.get(overall, 0):
            overall = check["status"]
    return {"service": service_name, "overall_status": overall, "checks": checks}


def get_single_check(service_name, check_name):
    health = get_service_health(service_name)
    for check in health["checks"]:
        if check["check_name"] == check_name:
            return check
    return None
