# Health Check Push Endpoint

**Date:** 2026-05-28

## Overview

Add a `POST /catalog/name/<service>/health` endpoint to the catalog API so callers can push health check results without direct knowledge of Prometheus or the Pushgateway. The catalog API becomes the single interface for both reading and writing health state.

## Architecture

The new route sits in `app.py` alongside the existing health routes. It calls the existing `push_health_check()` function from `push_health_check.py` directly — no new modules or abstractions needed.

```
POST /catalog/name/<service>/health
  → Postgres lookup (serviceName)
      404 if not found
  → validate status ∈ {pass, warn, fail}
      400 if invalid
  → push_health_check(service, check_name, status)
      502 if Pushgateway unreachable
  → 200 {"pushed": true, "service": ..., "check_name": ..., "status": ...}
```

Prometheus remains the source of truth — this endpoint is a facade over the Pushgateway push. Reads still go through `enrich_entry()` → PromQL.

## Endpoint

**Method/Path:** `POST /catalog/name/<service>/health`

**Request body:**
```json
{ "check_name": "db_connectivity", "status": "pass" }
```

| Field | Type | Required | Values |
|---|---|---|---|
| `check_name` | string | yes | any snake_case identifier |
| `status` | string | yes | `pass` \| `warn` \| `fail` |

**Responses:**

| Code | Condition | Body |
|---|---|---|
| 200 | Success | `{"pushed": true, "service": "<name>", "check_name": "<check>", "status": "<status>"}` |
| 400 | Missing/invalid field | `{"error": "<message>"}` |
| 404 | Service not in catalog | `{"error": "Entry '<service>' not found"}` |
| 502 | Pushgateway unreachable | `{"error": "Failed to push health check: <detail>"}` |

## Validation

- `check_name` missing or empty → 400
- `status` not in `{pass, warn, fail}` → 400 (caught before calling `push_health_check()` to avoid the ValueError bubbling up as a 502)
- Service not found in Postgres → 404 (consistent with existing route behavior)

## Implementation Notes

- `push_health_check()` is imported from `push_health_check.py` — already imported nowhere in `app.py`, so a new import is needed
- The 400 for invalid status is caught explicitly in the route (check before calling `push_health_check()`) so the ValueError from `push_health_check()` never reaches the error handler
- The existing `push_health_check.py` CLI interface is unchanged

## Testing

Four new tests in `tests/test_health_endpoints.py`:

| Test | Mock | Assert |
|---|---|---|
| `test_push_health_check_returns_200` | DB hit, `push_health_check` succeeds | 200, pushed=true, correct fields |
| `test_push_health_check_returns_404_when_service_missing` | DB miss | 404 |
| `test_push_health_check_returns_400_on_invalid_status` | — | 400 (no mocks needed) |
| `test_push_health_check_returns_502_on_pushgateway_failure` | DB hit, `push_health_check` raises | 502 |
