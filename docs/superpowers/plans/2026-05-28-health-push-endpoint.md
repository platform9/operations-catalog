# Health Check Push Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `POST /catalog/name/<service>/health` so callers can push health check results through the catalog API without direct Prometheus knowledge.

**Architecture:** One new route in `app.py` imports `push_health_check()` from `push_health_check.py`. The route validates input, looks up the service in Postgres, then delegates to `push_health_check()`. Prometheus remains the source of truth — this endpoint is a facade over the Pushgateway.

**Tech Stack:** Python 3, Flask, prometheus-client, psycopg2, pytest 7+

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `dev/operations-catalog-local/app.py` | Add import + new POST route |
| Modify | `dev/operations-catalog-local/tests/test_health_endpoints.py` | Four new route tests |

---

## Task 1: Add POST /catalog/name/<service>/health (TDD)

**Files:**
- Modify: `dev/operations-catalog-local/tests/test_health_endpoints.py`
- Modify: `dev/operations-catalog-local/app.py`

- [ ] **Step 1: Add a helper and four failing tests to test_health_endpoints.py**

Append to `dev/operations-catalog-local/tests/test_health_endpoints.py`:

```python
def _make_push_db_mock(found=True):
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = (1,) if found else None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


def test_push_health_check_returns_200(client):
    with patch("app.get_db", return_value=_make_push_db_mock(found=True)), \
         patch("app.push_health_check"):
        resp = client.post(
            "/catalog/name/bork/health",
            json={"check_name": "db_connectivity", "status": "pass"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pushed"] is True
        assert data["service"] == "bork"
        assert data["check_name"] == "db_connectivity"
        assert data["status"] == "pass"


def test_push_health_check_returns_404_when_service_missing(client):
    with patch("app.get_db", return_value=_make_push_db_mock(found=False)):
        resp = client.post(
            "/catalog/name/nonexistent/health",
            json={"check_name": "db_connectivity", "status": "pass"},
        )
        assert resp.status_code == 404


def test_push_health_check_returns_400_on_invalid_status(client):
    resp = client.post(
        "/catalog/name/bork/health",
        json={"check_name": "db_connectivity", "status": "broken"},
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_push_health_check_returns_502_on_pushgateway_failure(client):
    with patch("app.get_db", return_value=_make_push_db_mock(found=True)), \
         patch("app.push_health_check", side_effect=Exception("connection refused")):
        resp = client.post(
            "/catalog/name/bork/health",
            json={"check_name": "db_connectivity", "status": "pass"},
        )
        assert resp.status_code == 502
        assert "error" in resp.get_json()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd dev/operations-catalog-local
source venv/bin/activate
pytest tests/test_health_endpoints.py::test_push_health_check_returns_200 tests/test_health_endpoints.py::test_push_health_check_returns_404_when_service_missing tests/test_health_endpoints.py::test_push_health_check_returns_400_on_invalid_status tests/test_health_endpoints.py::test_push_health_check_returns_502_on_pushgateway_failure -v
```

Expected: all four fail. The first three will return 405 (Method Not Allowed — the GET route exists but POST does not). The 400 test will also get 405.

- [ ] **Step 3: Add the import to app.py**

In `dev/operations-catalog-local/app.py`, change line 5 from:

```python
from health_store import get_service_health, get_single_check, enrich_entry
```

to:

```python
from health_store import get_service_health, get_single_check, enrich_entry
from push_health_check import push_health_check
```

- [ ] **Step 4: Add the POST route to app.py**

In `dev/operations-catalog-local/app.py`, insert the following immediately after the existing `get_single_health_check` route (after line ending `return jsonify(check)`) and before the `# ── Diagrams` section:

```python
@app.route("/catalog/name/<string:service_name>/health", methods=["POST"])
def push_service_health_check(service_name):
    data = request.get_json(force=True) or {}
    check_name = (data.get("check_name") or "").strip()
    status = data.get("status", "")

    if not check_name:
        return jsonify({"error": "'check_name' is required"}), 400
    if status not in ("pass", "warn", "fail"):
        return jsonify({"error": f"'status' must be one of pass, warn, fail; got '{status}'"}), 400

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM catalog WHERE "serviceName" = %s', (service_name,))
        if cur.fetchone() is None:
            abort(404, description=f"Entry '{service_name}' not found")

    try:
        push_health_check(service_name, check_name, status)
    except Exception as e:
        return jsonify({"error": f"Failed to push health check: {str(e)}"}), 502

    return jsonify({"pushed": True, "service": service_name, "check_name": check_name, "status": status})
```

- [ ] **Step 5: Run the four new tests to confirm they pass**

```bash
pytest tests/test_health_endpoints.py::test_push_health_check_returns_200 tests/test_health_endpoints.py::test_push_health_check_returns_404_when_service_missing tests/test_health_endpoints.py::test_push_health_check_returns_400_on_invalid_status tests/test_health_endpoints.py::test_push_health_check_returns_502_on_pushgateway_failure -v
```

Expected: all four pass.

- [ ] **Step 6: Run the full test suite**

```bash
pytest -v
```

Expected: all 25 tests pass (21 existing + 4 new).

- [ ] **Step 7: Commit**

```bash
git add dev/operations-catalog-local/app.py dev/operations-catalog-local/tests/test_health_endpoints.py
git commit -m "feat: add POST /catalog/name/<service>/health endpoint for health check pushes"
```
