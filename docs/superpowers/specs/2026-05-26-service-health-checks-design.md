# Service Health Checks via Prometheus

**Date:** 2026-05-26

## Overview

Store structured per-service health check results in Prometheus as the source of truth. The operations catalog API reads from Prometheus and serves health data to humans, programmatic clients, and alerting/automation.

## Architecture

```
Services / Scripts
      │
      │  prometheus_client push_to_gateway
      ▼
 Prometheus Pushgateway
      │
      ▼
 Prometheus (scraped from Pushgateway)
      │
      │  PromQL instant query
      ▼
 Catalog API (Flask)
 reads metrics via /api/v1/query
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
| `last_updated` | ISO8601 | Sourced from the Prometheus metric timestamp |

**Metric stored in Prometheus:**
```
Name:   service_health_check_status
Labels: service=<service_name>, check_name=<check_name>
Value:  0 (pass) | 1 (warn) | 2 (fail)
```

## Ingest Path

Producers call `push_health_check.py`, which pushes a labeled gauge to the Prometheus Pushgateway using `prometheus_client`. Prometheus scrapes the Pushgateway on its normal interval. Producers may be the service itself, an external script, a CI/CD step, or a human-triggered push.

Producers are responsible for using consistent `check_name` values across pushes. There is no server-side schema validation.

**Required environment variables for producers:**
```
PROMETHEUS_PUSHGATEWAY_URL
```

## Catalog API Changes

**New endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/catalog/name/<service>/health` | All checks + overall status for a service |
| `GET` | `/catalog/name/<service>/health/<check_name>` | Single check |

**Request-to-response flow for `/catalog/name/<service>/health`:**
1. Query Prometheus: `service_health_check_status{service="<service>"}` via `/api/v1/query`
2. Map values: `0→pass`, `1→warn`, `2→fail`; source `last_updated` from the metric timestamp
3. Derive `overall_status`: `fail` if any check is `fail`, else `warn` if any is `warn`, else `pass`
4. Return JSON response

**Example response:**
```json
{
  "service": "bork",
  "overall_status": "warn",
  "checks": [
    {
      "check_name": "db_connectivity",
      "status": "pass",
      "last_updated": "2026-05-26T10:00:00+00:00"
    },
    {
      "check_name": "queue_consumer",
      "status": "warn",
      "last_updated": "2026-05-26T09:58:00+00:00"
    }
  ]
}
```

**New module:** `health_store.py` — wraps the Prometheus PromQL query and derives `overall_status`.

**Existing `health` field** in the Postgres catalog schema stores a URL string pointing to the service's Grafana/Prometheus dashboard. It does not store check state.

**New environment variables for the catalog API:**
```
PROMETHEUS_URL
PROMETHEUS_PUSHGATEWAY_URL
```
