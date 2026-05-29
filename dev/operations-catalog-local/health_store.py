import os
import requests
from datetime import datetime, timezone

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "")

STATUS_MAP = {0: "green", 1: "yellow", 2: "red"}
STATUS_RANK = {"green": 0, "yellow": 1, "red": 2}


def _query_metrics(service_name):
    url = f"{PROMETHEUS_URL}/api/v1/query"
    query = f'service_health_check_status{{service="{service_name}"}}'
    resp = requests.get(url, params={"query": query}, timeout=10)
    resp.raise_for_status()
    results = {}
    for result in resp.json().get("data", {}).get("result", []):
        check_name = result["metric"].get("check_name")
        value = int(float(result["value"][1]))
        timestamp = datetime.fromtimestamp(float(result["value"][0]), tz=timezone.utc).isoformat()
        if check_name:
            results[check_name] = {
                "status": STATUS_MAP.get(value, "unknown"),
                "last_updated": timestamp,
            }
    return results


def get_service_health(service_name):
    checks_data = _query_metrics(service_name)
    checks = [
        {"check_name": name, **data}
        for name, data in checks_data.items()
    ]
    overall = "green"
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


def enrich_entry(entry: dict) -> dict:
    try:
        health = get_service_health(entry["serviceName"])
        entry["health"] = {
            "prom_health": "green",
            "overall_status": health["overall_status"],
            "checks": health["checks"],
        }
    except Exception:
        entry["health"] = {"prom_health": "red"}
    return entry
