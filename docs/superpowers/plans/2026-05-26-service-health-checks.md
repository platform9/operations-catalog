# Service Health Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new Flask endpoints that serve per-service health check data read from groundcover, and a producer utility script that pushes health check results into groundcover via OpenTelemetry.

**Architecture:** groundcover is the source of truth. Each health check push writes two OTel signals — a gauge metric (`service_health_check_status`, value 0/1/2) for alerting and dashboards, and a structured JSON log event for detail text. The catalog API queries groundcover's PromQL metrics endpoint and Loki log endpoint, joins results by `check_name`, and returns structured JSON.

**Tech Stack:** Python 3, Flask, OpenTelemetry SDK (metrics + logs), opentelemetry-exporter-otlp-proto-http, requests, pytest 7+

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `dev/operations-catalog-local/requirements.txt` | Add OTel + requests + pytest deps |
| Modify | `dev/operations-catalog-local/.env` | Add GROUNDCOVER_* env vars |
| Create | `dev/operations-catalog-local/pytest.ini` | Pytest config and pythonpath |
| Create | `dev/operations-catalog-local/tests/__init__.py` | Makes tests a package |
| Create | `dev/operations-catalog-local/tests/conftest.py` | Flask test client fixture |
| Create | `dev/operations-catalog-local/groundcover.py` | Query groundcover metrics + logs APIs, derive overall_status |
| Create | `dev/operations-catalog-local/tests/test_groundcover.py` | Unit tests for groundcover.py |
| Modify | `dev/operations-catalog-local/app.py` | Add two new health routes + import |
| Create | `dev/operations-catalog-local/tests/test_health_endpoints.py` | Flask route tests for new endpoints |
| Create | `dev/operations-catalog-local/push_health_check.py` | Producer utility: push a health check to groundcover via OTel |
| Create | `dev/operations-catalog-local/tests/test_push_health_check.py` | Unit tests for push_health_check.py |
| Modify | `dev/operations-catalog-local/README.md` | Document new env vars and endpoints |

---

## Task 1: Add Dependencies and Env Vars

**Files:**
- Modify: `dev/operations-catalog-local/requirements.txt`
- Modify: `dev/operations-catalog-local/.env`

- [ ] **Step 1: Update requirements.txt**

Replace the contents of `dev/operations-catalog-local/requirements.txt` with:

```
flask>=3.0.0
flask-cors
psycopg2-binary
python-dotenv
requests>=2.31.0
opentelemetry-api>=1.22.0
opentelemetry-sdk>=1.22.0
opentelemetry-exporter-otlp-proto-http>=1.22.0
pytest>=7.0
```

- [ ] **Step 2: Add groundcover env vars to .env**

Append to `dev/operations-catalog-local/.env`:

```
GROUNDCOVER_METRICS_URL=https://your-groundcover-instance/metrics
GROUNDCOVER_LOGS_URL=https://your-groundcover-instance
GROUNDCOVER_API_KEY=your-api-key-here
GROUNDCOVER_OTLP_ENDPOINT=https://your-groundcover-instance/otlp
```

- [ ] **Step 3: Install new dependencies**

```bash
cd dev/operations-catalog-local
source venv/bin/activate
pip install -r requirements.txt
```

Expected: packages install without errors; `opentelemetry-sdk` and `opentelemetry-exporter-otlp-proto-http` appear in output.

- [ ] **Step 4: Commit**

```bash
git add dev/operations-catalog-local/requirements.txt dev/operations-catalog-local/.env
git commit -m "feat: add OTel and requests dependencies for groundcover integration"
```

---

## Task 2: Set Up Test Infrastructure

**Files:**
- Create: `dev/operations-catalog-local/pytest.ini`
- Create: `dev/operations-catalog-local/tests/__init__.py`
- Create: `dev/operations-catalog-local/tests/conftest.py`

- [ ] **Step 1: Create pytest.ini**

Create `dev/operations-catalog-local/pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
```

(`pythonpath = .` adds `dev/operations-catalog-local/` to sys.path so `import app`, `import groundcover`, etc. work from tests.)

- [ ] **Step 2: Create tests/__init__.py**

Create `dev/operations-catalog-local/tests/__init__.py` as an empty file.

- [ ] **Step 3: Create tests/conftest.py**

Create `dev/operations-catalog-local/tests/conftest.py`:

```python
import pytest
from unittest.mock import patch


@pytest.fixture
def client():
    from app import app
    app.config["TESTING"] = True
    with patch("app.init_db"):
        with app.test_client() as c:
            yield c
```

(`patch("app.init_db")` prevents the `before_request` hook from trying to open a Postgres connection during tests.)

- [ ] **Step 4: Verify test collection works**

```bash
cd dev/operations-catalog-local
source venv/bin/activate
pytest --collect-only
```

Expected output:
```
======================== no tests ran ========================
```
No errors, zero tests collected.

- [ ] **Step 5: Commit**

```bash
git add dev/operations-catalog-local/pytest.ini dev/operations-catalog-local/tests/
git commit -m "feat: add pytest infrastructure for health check tests"
```

---

## Task 3: Implement groundcover.py (TDD)

**Files:**
- Create: `dev/operations-catalog-local/tests/test_groundcover.py`
- Create: `dev/operations-catalog-local/groundcover.py`

- [ ] **Step 1: Write the failing tests**

Create `dev/operations-catalog-local/tests/test_groundcover.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd dev/operations-catalog-local
source venv/bin/activate
pytest tests/test_groundcover.py -v
```

Expected: all 7 tests fail with `ModuleNotFoundError: No module named 'groundcover'`.

- [ ] **Step 3: Create groundcover.py**

Create `dev/operations-catalog-local/groundcover.py`:

```python
import json
import os
import requests
from datetime import datetime, timedelta, timezone

GROUNDCOVER_METRICS_URL = os.environ.get("GROUNDCOVER_METRICS_URL", "")
GROUNDCOVER_LOGS_URL = os.environ.get("GROUNDCOVER_LOGS_URL", "")
GROUNDCOVER_API_KEY = os.environ.get("GROUNDCOVER_API_KEY", "")

STATUS_MAP = {0: "pass", 1: "warn", 2: "fail"}
STATUS_RANK = {"pass": 0, "warn": 1, "fail": 2}


def _auth_headers():
    return {"Authorization": f"Bearer {GROUNDCOVER_API_KEY}"}


def _query_metrics(service_name):
    url = f"{GROUNDCOVER_METRICS_URL}/api/v1/query"
    query = f'service_health_check_status{{service="{service_name}"}}'
    resp = requests.get(url, params={"query": query}, headers=_auth_headers(), timeout=10)
    resp.raise_for_status()
    results = {}
    for result in resp.json().get("data", {}).get("result", []):
        check_name = result["metric"].get("check_name")
        value = int(float(result["value"][1]))
        if check_name:
            results[check_name] = STATUS_MAP.get(value, "unknown")
    return results


def _query_logs(service_name):
    url = f"{GROUNDCOVER_LOGS_URL}/loki/api/v1/query_range"
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)
    params = {
        "query": f'{{service="{service_name}"}} | json',
        "start": int(start.timestamp()),
        "end": int(now.timestamp()),
        "limit": 1000,
        "direction": "backward",
    }
    resp = requests.get(url, params=params, headers=_auth_headers(), timeout=10)
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_groundcover.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add dev/operations-catalog-local/groundcover.py dev/operations-catalog-local/tests/test_groundcover.py
git commit -m "feat: add groundcover query module with health check aggregation"
```

---

## Task 4: Add Health Endpoints to app.py (TDD)

**Files:**
- Create: `dev/operations-catalog-local/tests/test_health_endpoints.py`
- Modify: `dev/operations-catalog-local/app.py`

- [ ] **Step 1: Write the failing tests**

Create `dev/operations-catalog-local/tests/test_health_endpoints.py`:

```python
import pytest
from unittest.mock import patch

MOCK_HEALTH = {
    "service": "bork",
    "overall_status": "warn",
    "checks": [
        {"check_name": "db_connectivity", "status": "pass", "detail": "ok", "last_updated": "2026-05-26T10:00:00Z"},
        {"check_name": "queue_consumer", "status": "warn", "detail": "lag at 4500", "last_updated": "2026-05-26T09:58:00Z"},
    ],
}

MOCK_CHECK = {
    "check_name": "db_connectivity",
    "status": "pass",
    "detail": "ok",
    "last_updated": "2026-05-26T10:00:00Z",
}


def test_get_service_health_returns_200(client):
    with patch("app.get_service_health", return_value=MOCK_HEALTH):
        resp = client.get("/catalog/name/bork/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "bork"
        assert data["overall_status"] == "warn"
        assert len(data["checks"]) == 2


def test_get_service_health_returns_502_on_error(client):
    with patch("app.get_service_health", side_effect=Exception("groundcover unavailable")):
        resp = client.get("/catalog/name/bork/health")
        assert resp.status_code == 502
        assert "error" in resp.get_json()


def test_get_single_health_check_returns_200(client):
    with patch("app.get_single_check", return_value=MOCK_CHECK):
        resp = client.get("/catalog/name/bork/health/db_connectivity")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["check_name"] == "db_connectivity"
        assert data["status"] == "pass"


def test_get_single_health_check_returns_404_when_not_found(client):
    with patch("app.get_single_check", return_value=None):
        resp = client.get("/catalog/name/bork/health/nonexistent")
        assert resp.status_code == 404


def test_get_single_health_check_returns_502_on_error(client):
    with patch("app.get_single_check", side_effect=Exception("groundcover unavailable")):
        resp = client.get("/catalog/name/bork/health/db_connectivity")
        assert resp.status_code == 502
        assert "error" in resp.get_json()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_health_endpoints.py -v
```

Expected: all 5 tests fail — `ImportError` or 404 because the routes don't exist yet.

- [ ] **Step 3: Add import and two new routes to app.py**

At the top of `dev/operations-catalog-local/app.py`, add the import after the existing imports:

```python
from groundcover import get_service_health, get_single_check
```

Add these two routes before the `# ── Diagrams` section:

```python
# ── Health checks (groundcover) ───────────────────────────────────────────────
@app.route("/catalog/name/<string:service_name>/health", methods=["GET"])
def get_service_health_checks(service_name):
    try:
        result = get_service_health(service_name)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch health data: {str(e)}"}), 502
    return jsonify(result)


@app.route("/catalog/name/<string:service_name>/health/<string:check_name>", methods=["GET"])
def get_single_health_check(service_name, check_name):
    try:
        check = get_single_check(service_name, check_name)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch health data: {str(e)}"}), 502
    if check is None:
        abort(404, description=f"Check '{check_name}' not found for service '{service_name}'")
    return jsonify(check)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_health_endpoints.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
pytest -v
```

Expected: all 12 tests pass (7 from test_groundcover + 5 from test_health_endpoints).

- [ ] **Step 6: Commit**

```bash
git add dev/operations-catalog-local/app.py dev/operations-catalog-local/tests/test_health_endpoints.py
git commit -m "feat: add /health endpoints to catalog API backed by groundcover"
```

---

## Task 5: Implement push_health_check.py (TDD)

**Files:**
- Create: `dev/operations-catalog-local/tests/test_push_health_check.py`
- Create: `dev/operations-catalog-local/push_health_check.py`

- [ ] **Step 1: Write the failing tests**

Create `dev/operations-catalog-local/tests/test_push_health_check.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def _patches():
    return [
        patch("push_health_check.OTLPMetricExporter"),
        patch("push_health_check.PeriodicExportingMetricReader"),
        patch("push_health_check.MeterProvider"),
        patch("push_health_check.OTLPLogExporter"),
        patch("push_health_check.BatchLogRecordProcessor"),
        patch("push_health_check.LoggerProvider"),
        patch("push_health_check.otel_logs"),
    ]


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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_push_health_check.py -v
```

Expected: all 6 tests fail with `ModuleNotFoundError: No module named 'push_health_check'`.

- [ ] **Step 3: Create push_health_check.py**

Create `dev/operations-catalog-local/push_health_check.py`:

```python
import json
import logging
import os
from datetime import datetime, timezone

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http.log_exporter import OTLPLogExporter
from opentelemetry import logs as otel_logs

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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_push_health_check.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 5: Run the full test suite**

```bash
pytest -v
```

Expected: all 18 tests pass.

- [ ] **Step 6: Commit**

```bash
git add dev/operations-catalog-local/push_health_check.py dev/operations-catalog-local/tests/test_push_health_check.py
git commit -m "feat: add push_health_check producer utility for groundcover OTel ingest"
```

---

## Task 6: Update README

**Files:**
- Modify: `dev/operations-catalog-local/README.md`

- [ ] **Step 1: Add groundcover env vars to the environment variables table**

In the "Environment variables" table, append these rows:

```markdown
| `GROUNDCOVER_METRICS_URL` | (required) PromQL endpoint base URL, e.g. `https://your-instance/metrics` |
| `GROUNDCOVER_LOGS_URL` | (required) Loki-compatible log endpoint base URL, e.g. `https://your-instance` |
| `GROUNDCOVER_API_KEY` | (required) API key for groundcover auth |
| `GROUNDCOVER_OTLP_ENDPOINT` | (required for producers) OTLP base URL, e.g. `https://your-instance/otlp` |
```

- [ ] **Step 2: Add new endpoints to the Endpoints table**

In the "Endpoints" table, append these rows:

```markdown
| `GET` | `/catalog/name/<name>/health` | All health checks + overall status for a service |
| `GET` | `/catalog/name/<name>/health/<check>` | Single health check with detail |
```

- [ ] **Step 3: Add a "Pushing health checks" section**

Append a new section after the Endpoints table:

```markdown
## Pushing Health Checks

Use `push_health_check.py` to push a named health check result into groundcover:

```bash
python push_health_check.py <service> <check_name> <pass|warn|fail> [detail]
```

Examples:
```bash
python push_health_check.py bork db_connectivity pass "Connected in 12ms"
python push_health_check.py bork queue_consumer warn "Consumer lag at 4500 messages"
python push_health_check.py bork db_connectivity fail "Connection refused"
```

Requires `GROUNDCOVER_OTLP_ENDPOINT` and `GROUNDCOVER_API_KEY` to be set. Each push writes two OTel signals to groundcover: a gauge metric (for alerting/dashboards) and a structured log event (for detail text).

`check_name` must be consistent across pushes — use snake_case identifiers (e.g. `db_connectivity`, not `DB Connectivity`).
```

- [ ] **Step 4: Add a note about the health field**

In the README, append to the "Pushing Health Checks" section:

```markdown
### Updating the groundcover dashboard link

The `health` field on each catalog entry now stores a URL to the service's groundcover dashboard (not check state — check state lives in groundcover). Update existing entries via the existing PUT endpoint:

```bash
curl -X PUT http://localhost:5000/catalog/name/bork \
  -H "Content-Type: application/json" \
  -d '{"health": "https://your-groundcover-instance/service/bork"}'
```
```

- [ ] **Step 5: Commit**

```bash
git add dev/operations-catalog-local/README.md
git commit -m "docs: document groundcover health check endpoints and push utility"
```
