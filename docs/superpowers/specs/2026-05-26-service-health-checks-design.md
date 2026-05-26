# Service Health Checks via groundcover

**Date:** 2026-05-26

## Overview

Store structured per-service health check results in groundcover as the source of truth. The operations catalog API reads from groundcover and serves health data to humans, programmatic clients, and alerting/automation.

## Architecture

```
Services / Scripts
      │
      │  OTel SDK (OTLP push)
      ▼
 groundcover OTLP endpoint
      │
      ├── gauge metrics  ──► groundcover metrics store (PromQL-queryable)
      └── structured logs ──► groundcover log store (REST-queryable)
                                        │
                              Catalog API (Flask)
                              reads metrics + logs
                              from groundcover APIs
                                        │
                              ┌─────────┴─────────┐
                            Humans            Services /
                           (UI/dashboard)     Alerting /
                                              Automation
```

## Health Check Data Model

Each health check result carries:

| Field | Type | Description |
|---|---|---|
| `service_name` | string | Matches `serviceName` in the catalog |
| `check_name` | string | Stable identifier (e.g. `"db_connectivity"`) |
| `status` | enum | `"pass"` \| `"warn"` \| `"fail"` — set by the producer |
| `detail` | string | Human-readable explanation (optional but expected) |
| `timestamp` | ISO8601 | When the check was last evaluated |

**Metric signal in groundcover:**
```
Name:   service_health_check_status
Labels: service=<service_name>, check_name=<check_name>
Value:  0 (pass) | 1 (warn) | 2 (fail)
```

**Log signal in groundcover (JSON):**
```json
{
  "service": "<service_name>",
  "check_name": "<check_name>",
  "status": "pass|warn|fail",
  "detail": "<human-readable text>",
  "timestamp": "<ISO8601>"
}
```

## Ingest Path

Any producer pushes via the OTel SDK to groundcover's OTLP endpoint. Two signals per check evaluation: a gauge metric update and a structured log event. Producers may be the service itself, an external script, a CI/CD step, or a human-triggered push.

Producers are responsible for using consistent `check_name` values across pushes. There is no server-side schema validation.

**Required environment variables for producers:**
```
GROUNDCOVER_OTLP_ENDPOINT
GROUNDCOVER_API_KEY
```

## Catalog API Changes

**New endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/catalog/name/<service>/health` | All checks + overall status for a service |
| `GET` | `/catalog/name/<service>/health/<check_name>` | Single check with detail |

**Request-to-response flow for `/catalog/name/<service>/health`:**
1. Query groundcover metrics API: `service_health_check_status{service="<service>"}` → check names + numeric status
2. Query groundcover log API: latest log event per `check_name` for the service → `detail` + `timestamp`
3. Join by `check_name`, map `0→pass`, `1→warn`, `2→fail`
4. Derive `overall_status`: `fail` if any check is `fail`, else `warn` if any is `warn`, else `pass`
5. Return JSON response

**Example response:**
```json
{
  "service": "bork",
  "overall_status": "warn",
  "checks": [
    {
      "check_name": "db_connectivity",
      "status": "pass",
      "detail": "Connected to postgres in 12ms",
      "last_updated": "2026-05-26T10:00:00Z"
    },
    {
      "check_name": "queue_consumer",
      "status": "warn",
      "detail": "Consumer lag at 4500 (threshold: 1000)",
      "last_updated": "2026-05-26T09:58:00Z"
    }
  ]
}
```

**New module:** `groundcover.py` — wraps the two groundcover API calls and the join logic.

**Existing `health` field** in the Postgres catalog schema becomes a URL string pointing to the service's groundcover dashboard. It no longer stores check state.

**New environment variables for the catalog API:**
```
GROUNDCOVER_METRICS_URL
GROUNDCOVER_LOGS_URL
GROUNDCOVER_API_KEY
```
