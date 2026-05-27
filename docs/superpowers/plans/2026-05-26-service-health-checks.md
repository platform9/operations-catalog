# Service Health Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new Flask endpoints that serve per-service health check data read from Prometheus, and a producer utility script that pushes health check results into the Prometheus Pushgateway.

**Architecture:** Prometheus is the source of truth. Each health check push writes a labeled gauge metric (`service_health_check_status`, value 0/1/2) to the Pushgateway via `prometheus_client`. The catalog API queries Prometheus via PromQL and returns structured JSON.

**Tech Stack:** Python 3, Flask, prometheus-client, requests, pytest 7+

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `dev/operations-catalog-local/requirements.txt` | Add prometheus-client + requests + pytest deps |
| Modify | `dev/operations-catalog-local/.env` | Add PROMETHEUS_* env vars |
| Create | `dev/operations-catalog-local/pytest.ini` | Pytest config and pythonpath |
| Create | `dev/operations-catalog-local/tests/__init__.py` | Makes tests a package |
| Create | `dev/operations-catalog-local/tests/conftest.py` | Flask test client fixture |
| Create | `dev/operations-catalog-local/health_store.py` | Query Prometheus PromQL API, derive overall_status |
| Create | `dev/operations-catalog-local/tests/test_health_store.py` | Unit tests for health_store.py |
| Modify | `dev/operations-catalog-local/app.py` | Add two new health routes + import |
| Create | `dev/operations-catalog-local/tests/test_health_endpoints.py` | Flask route tests for new endpoints |
| Create | `dev/operations-catalog-local/push_health_check.py` | Producer utility: push a health check to Prometheus Pushgateway |
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
prometheus-client>=0.20.0
pytest>=7.0
```

- [ ] **Step 2: Add Prometheus env vars to .env**

Append to `dev/operations-catalog-local/.env`:

```
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091
```

- [ ] **Step 3: Install new dependencies**

```bash
cd dev/operations-catalog-local
source venv/bin/activate
pip install -r requirements.txt
```

Expected: packages install without errors; `prometheus-client` appears in output.

- [ ] **Step 4: Commit**

```bash
git add dev/operations-catalog-local/requirements.txt dev/operations-catalog-local/.env
git commit -m "feat: add prometheus-client and requests dependencies for health check integration"
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

(`pythonpath = .` adds `dev/operations-catalog-local/` to sys.path so `import app`, `import health_store`, etc. work from tests.)

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

## Task 3: Implement health_store.py (TDD)

**Files:**
- Create: `dev/operations-catalog-local/tests/test_health_store.py`
- Create: `dev/operations-catalog-local/health_store.py`

- [ ] **Step 1: Write the failing tests**

Create `dev/operations-catalog-local/tests/test_health_store.py`:

```python
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


def _mock_get(metrics_resp):
    def side_effect(url, **kwargs):
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        mock.json.return_value = metrics_resp
        return mock
    return side_effect


def test_query_metrics_maps_values_to_status():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store._query_metrics("bork")
        assert result["db_connectivity"]["status"] == "pass"
        assert result["queue_consumer"]["status"] == "warn"


def test_query_metrics_includes_timestamp():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store._query_metrics("bork")
        assert "last_updated" in result["db_connectivity"]
        assert result["db_connectivity"]["last_updated"].startswith("2024-")


def test_get_service_health_returns_checks():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_service_health("bork")
        assert result["service"] == "bork"
        assert result["overall_status"] == "warn"
        assert len(result["checks"]) == 2
        db_check = next(c for c in result["checks"] if c["check_name"] == "db_connectivity")
        assert db_check["status"] == "pass"


def test_get_service_health_overall_fail_takes_priority():
    fail_metrics = {
        "data": {
            "result": [
                {"metric": {"service": "bork", "check_name": "check_a"}, "value": [1716720000, "0"]},
                {"metric": {"service": "bork", "check_name": "check_b"}, "value": [1716720000, "2"]},
            ]
        }
    }
    with patch("health_store.requests.get", side_effect=_mock_get(fail_metrics)):
        import health_store
        result = health_store.get_service_health("bork")
        assert result["overall_status"] == "fail"


def test_get_service_health_no_checks_returns_pass():
    empty = {"data": {"result": []}}
    with patch("health_store.requests.get", side_effect=_mock_get(empty)):
        import health_store
        result = health_store.get_service_health("bork")
        assert result["overall_status"] == "pass"
        assert result["checks"] == []


def test_get_single_check_returns_matching_check():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_single_check("bork", "db_connectivity")
        assert result is not None
        assert result["check_name"] == "db_connectivity"
        assert result["status"] == "pass"


def test_get_single_check_returns_none_for_unknown():
    with patch("health_store.requests.get", side_effect=_mock_get(METRICS_RESPONSE)):
        import health_store
        result = health_store.get_single_check("bork", "nonexistent_check")
        assert result is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd dev/operations-catalog-local
source venv/bin/activate
pytest tests/test_health_store.py -v
```

Expected: all 7 tests fail with `ModuleNotFoundError: No module named 'health_store'`.

- [ ] **Step 3: Create health_store.py**

Create `dev/operations-catalog-local/health_store.py`:

```python
import os
import requests
from datetime import datetime, timezone

PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "")

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
        timestamp = datetime.fromtimestamp(float(result["value"][0]), tz=timezone.utc).isoformat()
        if check_name:
            results[check_name] = {
                "status": STATUS_MAP.get(value, "unknown"),
                "last_updated": timestamp,
            }
    return results


def get_service_health(service_name):
    checks_data = _query_metrics(service_name)
    checks = [{"check_name": name, **data} for name, data in checks_data.items()]
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
pytest tests/test_health_store.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add dev/operations-catalog-local/health_store.py dev/operations-catalog-local/tests/test_health_store.py
git commit -m "feat: add health_store module with Prometheus PromQL query and health aggregation"
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
        {"check_name": "db_connectivity", "status": "pass", "last_updated": "2026-05-26T10:00:00Z"},
        {"check_name": "queue_consumer", "status": "warn", "last_updated": "2026-05-26T09:58:00Z"},
    ],
}

MOCK_CHECK = {
    "check_name": "db_connectivity",
    "status": "pass",
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
    with patch("app.get_service_health", side_effect=Exception("prometheus unavailable")):
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
    with patch("app.get_single_check", side_effect=Exception("prometheus unavailable")):
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
from health_store import get_service_health, get_single_check
```

Add these two routes before the `# ── Diagrams` section:

```python
# ── Health checks ─────────────────────────────────────────────────────────────
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

Expected: all 12 tests pass (7 from test_health_store + 5 from test_health_endpoints).

- [ ] **Step 6: Commit**

```bash
git add dev/operations-catalog-local/app.py dev/operations-catalog-local/tests/test_health_endpoints.py
git commit -m "feat: add /health endpoints to catalog API backed by Prometheus"
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_push_health_check.py -v
```

Expected: all 5 tests fail with `ModuleNotFoundError: No module named 'push_health_check'`.

- [ ] **Step 3: Create push_health_check.py**

Create `dev/operations-catalog-local/push_health_check.py`:

```python
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
    push_health_check(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Pushed: {sys.argv[1]}/{sys.argv[2]} = {sys.argv[3]}")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_push_health_check.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 5: Run the full test suite**

```bash
pytest -v
```

Expected: all 17 tests pass.

- [ ] **Step 6: Commit**

```bash
git add dev/operations-catalog-local/push_health_check.py dev/operations-catalog-local/tests/test_push_health_check.py
git commit -m "feat: add push_health_check producer utility for Prometheus Pushgateway ingest"
```

---

## Task 6: Update README

**Files:**
- Modify: `dev/operations-catalog-local/README.md`

- [ ] **Step 1: Add Prometheus env vars to the environment variables table**

In the "Environment variables" table, append these rows:

```markdown
| `PROMETHEUS_URL` | (required) Prometheus base URL, e.g. `http://prometheus:9090` |
| `PROMETHEUS_PUSHGATEWAY_URL` | (required for producers) Pushgateway URL, e.g. `http://pushgateway:9091` |
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

Use `push_health_check.py` to push a named health check result into Prometheus:

```bash
python push_health_check.py <service> <check_name> <pass|warn|fail>
```

Examples:
```bash
python push_health_check.py bork db_connectivity pass
python push_health_check.py bork queue_consumer warn
python push_health_check.py bork db_connectivity fail
```

Requires `PROMETHEUS_PUSHGATEWAY_URL` to be set. Each push writes a gauge metric to the
Prometheus Pushgateway (for alerting/dashboards).

`check_name` must be consistent across pushes — use snake_case identifiers
(e.g. `db_connectivity`, not `DB Connectivity`).
```

- [ ] **Step 4: Add a note about the health field**

In the README, append to the "Pushing Health Checks" section:

```markdown
### Updating the Prometheus dashboard link

The `health` field on each catalog entry stores a URL to the service's Prometheus/Grafana
dashboard (not check state — check state lives in Prometheus). Update existing entries via
the existing PUT endpoint:

```bash
curl -X PUT http://localhost:5000/catalog/name/bork \
  -H "Content-Type: application/json" \
  -d '{"health": "https://your-grafana/d/service-health?var-service=bork"}'
```
```

- [ ] **Step 5: Commit**

```bash
git add dev/operations-catalog-local/README.md
git commit -m "docs: document Prometheus health check endpoints and push utility"
```
