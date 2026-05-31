# Quality Score Design

**Date:** 2026-05-31

## Overview

Add a Quality Score to catalog entries: a 0–1 float derived by periodically fetching a configurable JSON health endpoint for each service and pushing the result to Prometheus as a metric. The score surfaces in the existing `health` field of single-service API responses and in the `index.html` UI.

## Architecture

```
APScheduler (inside Flask, interval = QUALITY_SCORE_INTERVAL_MINUTES, default 10)
  → refresh_all_quality_scores(app)
      → query Postgres for all entries with statusPageUrl != NULL
      → for each: fetch_and_push_quality_score(service_name, url)
          → GET <statusPageUrl> (5s timeout)
          → parse JSON {"status": "..."}
          → map status string → 0.0–1.0 float via STATUS_SCORE_MAP
          → push_to_gateway(service_quality_score{service=<name>} = score)
          → on failure: log warning, skip push

GET /catalog/name/<service>  (or /<id>)
  → enrich_entry()
      → existing: PromQL for service_health_check_status → checks[]
      → new:      PromQL for service_quality_score{service=<name>} → float | null
      → new:      read QUALITY_SCORE_INTERVAL_MINUTES env var → int
      → health field includes quality_score and quality_score_interval_minutes
```

## New Catalog Field: `statusPageUrl`

A nullable `TEXT` column added to the `catalog` table. Operators set it per service to the URL of a JSON health endpoint (e.g. `https://api.example.com/health`). If absent or null, the service is skipped by the scheduler and `quality_score` is `null` in API responses.

**Schema change:** `database.py` adds to `init_db()`:

```sql
ALTER TABLE catalog ADD COLUMN IF NOT EXISTS "statusPageUrl" TEXT;
```

This is idempotent — safe to run on an existing database.

**CRUD:** `statusPageUrl` is added to the INSERT field list in `create_catalog_entry` and to the UPDATE field list in `update_catalog_entry` and `update_catalog_entry_by_name` in `app.py`. It is a plain text field — no URL validation at the API layer.

## Environment Variable

| Variable | Default | Description |
|---|---|---|
| `QUALITY_SCORE_INTERVAL_MINUTES` | `10` | How often the scheduler re-fetches all status endpoints |

Added to `.env` as a documented line: `QUALITY_SCORE_INTERVAL_MINUTES=10`

## New Module: `quality_score.py`

### `STATUS_SCORE_MAP`

```python
STATUS_SCORE_MAP = {
    "ok": 1.0, "healthy": 1.0, "operational": 1.0, "up": 1.0, "green": 1.0,
    "degraded": 0.5, "warning": 0.5, "partial_outage": 0.5, "yellow": 0.5,
    "down": 0.0, "error": 0.0, "critical": 0.0, "major_outage": 0.0, "red": 0.0,
}
```

Unknown status strings map to `0.0` (conservative default).

### `fetch_and_push_quality_score(service_name, url) -> float | None`

1. `GET url` with a 5-second timeout.
2. Raise on non-2xx (`resp.raise_for_status()`).
3. Parse JSON; read `data["status"]`, lowercase it, look it up in `STATUS_SCORE_MAP`. Unknown values map to `0.0`.
4. Push `service_quality_score{service=service_name}` to Pushgateway via `push_to_gateway`.
5. Return the score.
6. On any exception (connection error, timeout, non-JSON, missing `status` key, Pushgateway unreachable): log `WARNING`, return `None`. Do not push.

### `refresh_all_quality_scores(app)`

Runs inside an application context. Queries Postgres:

```sql
SELECT "serviceName", "statusPageUrl" FROM catalog WHERE "statusPageUrl" IS NOT NULL
```

Calls `fetch_and_push_quality_score` for each row. Exceptions from individual fetches are caught and logged — one failing service does not stop the rest.

### Scheduler setup in `app.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
import os

interval = int(os.environ.get("QUALITY_SCORE_INTERVAL_MINUTES", "10"))
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: refresh_all_quality_scores(app), "interval", minutes=interval)
scheduler.start()
```

Scheduler is started once at module level (after `app = Flask(__name__)`). If APScheduler fails to start, the error is logged and Flask continues normally — quality scores simply never populate.

## Extended `health` Field Shape

`enrich_entry()` in `health_store.py` adds two new keys:

```json
{
  "prom_health": "green",
  "overall_status": "green",
  "checks": [
    {"check_name": "db_connectivity", "status": "green", "last_updated": "..."}
  ],
  "quality_score": 0.85,
  "quality_score_interval_minutes": 10
}
```

| Key | Type | Value when absent |
|---|---|---|
| `quality_score` | `float \| null` | `null` — no `statusPageUrl` or fetch failed |
| `quality_score_interval_minutes` | `int` | Always present; read from env at response time |

### PromQL query for quality score

```
service_quality_score{service="<service_name>"}
```

If the query returns no results, `quality_score` is set to `null`. If results exist, the value is cast to `float` and rounded to 4 decimal places.

## `index.html` UI Changes

In the health section (rendered by `renderHealthSection`), add a quality score line below the overall_status badge:

- If `quality_score` is not null: display `Quality: 0.85` with a small grey label and the refresh interval as a tooltip or sub-label: `(refreshed every 10 min)`
- If `quality_score` is null: omit the quality score line entirely (no "unavailable" noise for services that simply have no status page configured)

## Error Handling Summary

| Scenario | Behaviour |
|---|---|
| `statusPageUrl` is null/absent | Skipped by scheduler; `quality_score: null` in response |
| Fetch timeout or connection error | Log warning, no push; metric stays absent or at last value |
| Non-2xx HTTP response | Log warning, no push |
| Non-JSON response body | Log warning, no push |
| Missing `status` key in JSON | Log warning, no push |
| Unknown `status` string value | Map to `0.0`, push |
| Pushgateway unreachable | Log warning, no push; scheduler continues to next service |
| Prometheus unreachable at read time | `prom_health: "red"` (existing behaviour); `quality_score` effectively null |

## Testing

### New: `tests/test_quality_score.py`

| Test | What it verifies |
|---|---|
| `test_known_status_strings_map_correctly` | All keys in `STATUS_SCORE_MAP` produce the expected float |
| `test_unknown_status_string_maps_to_zero` | `"unknown_status"` → `0.0` |
| `test_successful_fetch_pushes_score` | Mock `requests.get` returning `{"status": "ok"}` → score `1.0` pushed, function returns `1.0` |
| `test_fetch_failure_does_not_push` | Mock `requests.get` raising `ConnectionError` → push not called, function returns `None` |
| `test_non_200_does_not_push` | Mock returning 503 → push not called |
| `test_non_json_response_does_not_push` | Mock returning non-JSON body → push not called |
| `test_missing_status_key_does_not_push` | Mock returning `{"message": "ok"}` → push not called |
| `test_case_insensitive_status_lookup` | `{"status": "OK"}` → score `1.0` |

### Modified: `tests/test_health_store.py`

- `test_enrich_entry_replaces_health_on_success`: extend to assert `quality_score` and `quality_score_interval_minutes` present when mock Prometheus returns a quality score metric.
- Add `test_enrich_entry_quality_score_null_when_absent`: mock Prometheus returning no `service_quality_score` metric → `quality_score: null`, `quality_score_interval_minutes` still present.

## Dependencies

Add to `requirements.txt`:
```
APScheduler>=3.10,<4.0
```

APScheduler is the only new dependency. `prometheus-client`, `requests`, and `psycopg2` are already present.
