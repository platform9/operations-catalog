# Catalog Prometheus Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich single-service catalog GET responses with live Prometheus health data by replacing the `health` field with `{ prom_health, overall_status, checks }`.

**Architecture:** A new `enrich_entry(entry)` helper in `health_store.py` wraps `get_service_health()` and swaps the `health` field on a catalog dict. Both single-service GET routes in `app.py` call it immediately before `jsonify()`. If Prometheus is unreachable, `health` becomes `{ "prom_health": "red" }` and the rest of the catalog entry still returns 200.

**Tech Stack:** Python 3, Flask, prometheus-client, requests, pytest 7+

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `dev/operations-catalog-local/health_store.py` | Add `enrich_entry()` |
| Modify | `dev/operations-catalog-local/app.py` | Import `enrich_entry`, call it in two GET routes |
| Modify | `dev/operations-catalog-local/tests/test_health_store.py` | Two new unit tests for `enrich_entry()` |
| Modify | `dev/operations-catalog-local/tests/test_health_endpoints.py` | Two new route tests asserting enriched health shape |

---

## Task 1: Add `enrich_entry()` to health_store.py (TDD)

**Files:**
- Modify: `dev/operations-catalog-local/tests/test_health_store.py`
- Modify: `dev/operations-catalog-local/health_store.py`

- [ ] **Step 1: Write the two failing tests**

Append to `dev/operations-catalog-local/tests/test_health_store.py`:

```python
def test_enrich_entry_replaces_health_on_success():
    mock_health = {
        "service": "bork",
        "overall_status": "pass",
        "checks": [{"check_name": "db_connectivity", "status": "pass", "last_updated": "2026-05-27T10:00:00+00:00"}],
    }
    with patch("health_store.get_service_health", return_value=mock_health):
        import health_store
        entry = {"serviceName": "bork", "health": "http://grafana/bork", "description": "test"}
        result = health_store.enrich_entry(entry)
        assert result["health"]["prom_health"] == "green"
        assert result["health"]["overall_status"] == "pass"
        assert result["health"]["checks"] == mock_health["checks"]
        assert result["description"] == "test"  # other fields unchanged


def test_enrich_entry_sets_prom_health_red_on_failure():
    with patch("health_store.get_service_health", side_effect=Exception("connection refused")):
        import health_store
        entry = {"serviceName": "bork", "health": "http://grafana/bork", "description": "test"}
        result = health_store.enrich_entry(entry)
        assert result["health"] == {"prom_health": "red"}
        assert result["description"] == "test"  # other fields unchanged
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd dev/operations-catalog-local
source venv/bin/activate
pytest tests/test_health_store.py::test_enrich_entry_replaces_health_on_success tests/test_health_store.py::test_enrich_entry_sets_prom_health_red_on_failure -v
```

Expected: both fail with `AttributeError: module 'health_store' has no attribute 'enrich_entry'`.

- [ ] **Step 3: Add `enrich_entry()` to health_store.py**

Append to `dev/operations-catalog-local/health_store.py` (after `get_single_check`):

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_health_store.py::test_enrich_entry_replaces_health_on_success tests/test_health_store.py::test_enrich_entry_sets_prom_health_red_on_failure -v
```

Expected: both pass.

- [ ] **Step 5: Run the full suite to check for regressions**

```bash
pytest -v
```

Expected: all 17 existing tests pass plus the 2 new ones = 19 total.

- [ ] **Step 6: Commit**

```bash
git add dev/operations-catalog-local/health_store.py dev/operations-catalog-local/tests/test_health_store.py
git commit -m "feat: add enrich_entry() to health_store for Prometheus-enriched catalog responses"
```

---

## Task 2: Wire `enrich_entry()` into the two single-service GET routes (TDD)

**Files:**
- Modify: `dev/operations-catalog-local/tests/test_health_endpoints.py`
- Modify: `dev/operations-catalog-local/app.py`

- [ ] **Step 1: Write the two failing route tests**

First, update the import at the top of `dev/operations-catalog-local/tests/test_health_endpoints.py` from:

```python
from unittest.mock import patch
```

to:

```python
from unittest.mock import patch, MagicMock
```

Then append the following to the same file:

```python

CATALOG_COLUMNS = [
    "id", "serviceName", "health", "description", "status", "serviceCategory",
    "serviceSubjectMatterExperts", "criticalDependencies", "documentation",
    "SLA", "targetAudience", "requestsChannel", "incidentManagement",
    "monitoringTools", "activeMaintenanceWindows", "onboardingDocumentation",
    "costModel", "versionInformation", "deprecationPolicy",
]

BORK_ROW = (
    1, "bork", None, "Test service", "Active", None,
    None, None, None, None, None, None, None, None, None, None, None, None, None,
)

ENRICHED_HEALTH = {"prom_health": "green", "overall_status": "pass", "checks": []}


def _make_db_mock(row):
    mock_cursor = MagicMock()
    mock_cursor.description = [(col,) for col in CATALOG_COLUMNS]
    mock_cursor.fetchone.return_value = row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


def test_get_by_name_health_is_enriched(client):
    with patch("app.get_db", return_value=_make_db_mock(BORK_ROW)), \
         patch("app.enrich_entry", side_effect=lambda e: {**e, "health": ENRICHED_HEALTH}):
        resp = client.get("/catalog/name/bork")
        assert resp.status_code == 200
        assert resp.get_json()["health"] == ENRICHED_HEALTH


def test_get_by_id_health_is_enriched(client):
    with patch("app.get_db", return_value=_make_db_mock(BORK_ROW)), \
         patch("app.enrich_entry", side_effect=lambda e: {**e, "health": ENRICHED_HEALTH}):
        resp = client.get("/catalog/1")
        assert resp.status_code == 200
        assert resp.get_json()["health"] == ENRICHED_HEALTH
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_health_endpoints.py::test_get_by_name_health_is_enriched tests/test_health_endpoints.py::test_get_by_id_health_is_enriched -v
```

Expected: both fail — `patch("app.enrich_entry")` raises `AttributeError` because `enrich_entry` is not yet imported in `app.py`.

- [ ] **Step 3: Update the import in app.py**

In `dev/operations-catalog-local/app.py`, change line 5 from:

```python
from health_store import get_service_health, get_single_check
```

to:

```python
from health_store import get_service_health, get_single_check, enrich_entry
```

- [ ] **Step 4: Update `get_catalog_entry` (by ID) in app.py**

In `dev/operations-catalog-local/app.py`, change the return line in `get_catalog_entry`:

```python
# Before:
return jsonify(deserialize(row_to_dict(cur, row)))

# After:
return jsonify(enrich_entry(deserialize(row_to_dict(cur, row))))
```

The full updated function:

```python
@app.route("/catalog/<int:entry_id>", methods=["GET"])
def get_catalog_entry(entry_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM catalog WHERE id = %s', (entry_id,))
        row = cur.fetchone()
        if row is None:
            abort(404, description=f"Entry {entry_id} not found")
        return jsonify(enrich_entry(deserialize(row_to_dict(cur, row))))
```

- [ ] **Step 5: Update `get_catalog_entry_by_name` in app.py**

In `dev/operations-catalog-local/app.py`, change the return line in `get_catalog_entry_by_name`:

```python
# Before:
return jsonify(deserialize(row_to_dict(cur, row)))

# After:
return jsonify(enrich_entry(deserialize(row_to_dict(cur, row))))
```

The full updated function:

```python
@app.route("/catalog/name/<string:service_name>", methods=["GET"])
def get_catalog_entry_by_name(service_name):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM catalog WHERE "serviceName" = %s', (service_name,))
        row = cur.fetchone()
        if row is None:
            abort(404, description=f"Entry '{service_name}' not found")
        return jsonify(enrich_entry(deserialize(row_to_dict(cur, row))))
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
pytest tests/test_health_endpoints.py::test_get_by_name_health_is_enriched tests/test_health_endpoints.py::test_get_by_id_health_is_enriched -v
```

Expected: both pass.

- [ ] **Step 7: Run the full suite**

```bash
pytest -v
```

Expected: all 21 tests pass.

- [ ] **Step 8: Commit**

```bash
git add dev/operations-catalog-local/app.py dev/operations-catalog-local/tests/test_health_endpoints.py
git commit -m "feat: enrich single-service catalog GET responses with Prometheus health data"
```
