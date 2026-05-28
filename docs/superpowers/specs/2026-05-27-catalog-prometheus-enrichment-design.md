# Catalog Entry Prometheus Enrichment

**Date:** 2026-05-27

## Overview

Enrich single-service catalog GET responses with live health check data from Prometheus. When a consumer fetches a catalog entry by name or ID, the `health` field in the response is replaced with a structured object sourced from Prometheus rather than the raw JSONB value stored in Postgres.

## Architecture

A new `enrich_entry(entry: dict) -> dict` helper is added to `health_store.py`. It accepts a deserialized Postgres catalog dict, queries Prometheus for the service's health check state, and returns the dict with the `health` field replaced. Both single-service GET routes call it immediately before `jsonify()`. All other routes (list, write) are unchanged.

```
health_store.py
  ├── _query_metrics(service_name)     # existing
  ├── get_service_health(service_name) # existing
  ├── get_single_check(service_name, check_name) # existing
  └── enrich_entry(entry)              # new
```

## Data Flow

```
GET /catalog/name/<name>  OR  GET /catalog/<id>
  → Postgres query → row_to_dict → deserialize
  → enrich_entry(entry)
      → get_service_health(entry["serviceName"])
          success  → entry["health"] = {
                        "prom_health": "green",
                        "overall_status": "pass"|"warn"|"fail",
                        "checks": [{ "check_name": ..., "status": ..., "last_updated": ... }, ...]
                      }
          exception → entry["health"] = { "prom_health": "red" }
  → jsonify(entry) → 200
```

## health Field Shape

**Prometheus reachable:**
```json
"health": {
  "prom_health": "green",
  "overall_status": "warn",
  "checks": [
    { "check_name": "db_connectivity", "status": "pass", "last_updated": "2026-05-27T10:00:00+00:00" },
    { "check_name": "queue_consumer",  "status": "warn", "last_updated": "2026-05-27T09:58:00+00:00" }
  ]
}
```

**Prometheus unavailable:**
```json
"health": {
  "prom_health": "red"
}
```

`prom_health: "red"` covers any failure: connection refused, timeout, non-2xx response, or unexpected response shape. No partial data is returned when Prometheus is unreachable.

The previously stored Postgres `health` value (a dashboard URL string) is not included in the enriched response. It remains in the database and can still be written via PUT, but is superseded on single-service GET reads.

## Affected Endpoints

| Endpoint | Change |
|---|---|
| `GET /catalog/name/<name>` | Calls `enrich_entry()` before returning |
| `GET /catalog/<id>` | Calls `enrich_entry()` before returning |
| `GET /catalog` | No change — list endpoint returns Postgres data only |
| `GET /catalog/name/<name>/health` | No change — raw Prometheus view, unaffected |
| `GET /catalog/name/<name>/health/<check>` | No change |
| All POST / PUT / DELETE | No change |

## Testing

**New unit tests for `enrich_entry()` in `tests/test_health_store.py`:**
- `test_enrich_entry_replaces_health_on_success` — mock `get_service_health` returning data; assert `health["prom_health"] == "green"`, `health["overall_status"]` present, `health["checks"]` is a list; assert other fields (e.g. `serviceName`) are unchanged
- `test_enrich_entry_sets_prom_health_red_on_failure` — mock `get_service_health` raising an exception; assert `health == {"prom_health": "red"}`

**Updated route tests in `tests/test_health_endpoints.py`:**
- `test_get_catalog_entry_by_name_includes_enriched_health` — mock `enrich_entry` on the two affected routes; assert the enriched `health` shape appears in the response
- `test_get_catalog_entry_by_id_includes_enriched_health` — same for the ID route

## Implementation Notes

- `enrich_entry()` catches all exceptions from `get_service_health()` — the catalog GET never returns a non-200 due to Prometheus failure
- `enrich_entry()` mutates and returns the dict in place (same pattern as existing `deserialize()` helper in `app.py`)
- No changes to the Postgres schema
- No changes to `push_health_check.py` or the existing `/health` sub-routes
