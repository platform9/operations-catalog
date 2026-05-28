# Health UI Display

**Date:** 2026-05-28

## Overview

Update `index.html` to display Prometheus health data in the service detail panel. The health section shows the overall status as a prominent badge, with individual checks in a collapsible `<details>` section. Health data is fetched asynchronously on panel open — the panel renders immediately from pre-loaded list data, then the health section updates once the enriched per-service response arrives.

## Architecture

```
User clicks service in sidebar
  → selectEntry(id) renders panel from pre-loaded list data
      health section = <span class="badge badge-default">checking…</span>
  → fetchAndRenderHealth(serviceName) fires async
      GET /catalog/name/<serviceName>
      → on resolve: document.getElementById('health-section').innerHTML = renderHealthSection(data.health)
      → on error:   health section = grey "unavailable" badge
```

The list endpoint (`GET /catalog`) is never called again — only `selectEntry` changes, and only for the health section update.

## Health Data Shape

The enriched per-service response includes:

```json
{
  "health": {
    "prom_health": "green",
    "overall_status": "pass",
    "checks": [
      { "check_name": "db_connectivity", "status": "pass", "last_updated": "2026-05-28T14:22:01Z" },
      { "check_name": "api_latency",     "status": "warn", "last_updated": "2026-05-28T14:20:15Z" }
    ]
  }
}
```

`prom_health: "red"` means Prometheus is unreachable — the `overall_status` and `checks` fields are absent. `prom_health: "green"` means Prometheus is reachable and the metric data is live.

## JS Changes

### Delete

- `getHealthValue(health, key)` — reads old `Array<{key, value}>` format, no longer needed.

### Rewrite

**`healthBadgeClass(health)`** — reads `health.overall_status`:

| `overall_status` | `prom_health` | CSS class |
|---|---|---|
| `"pass"` | `"green"` | `badge-active` |
| `"warn"` | `"green"` | `badge-warning` |
| `"fail"` | `"green"` | `badge-inactive` |
| — | `"red"` | `badge-default` |
| missing/null | — | `badge-default` |

**`healthField(health)`** — renamed to `renderHealthSection(health)`. Returns an HTML string:
- `prom_health === "red"` or `health` is falsy → grey "unavailable" badge + `<small>Prometheus unreachable</small>`
- Otherwise → overall_status badge + `<details class="health-checks">` collapsible with a checks table

### Add

**`fetchAndRenderHealth(serviceName)`** — async function:
```js
async function fetchAndRenderHealth(serviceName) {
    const el = document.getElementById('health-section');
    try {
        const resp = await fetch(`/catalog/name/${encodeURIComponent(serviceName)}`);
        const data = await resp.json();
        el.innerHTML = renderHealthSection(data.health);
    } catch (_) {
        el.innerHTML = '<span class="badge badge-default">unavailable</span>';
    }
}
```

### Modify `selectEntry(id)`

Two changes:
1. Wrap the health field render in `<div id="health-section">…</div>` with an initial "checking…" placeholder.
2. Call `fetchAndRenderHealth(entry.serviceName)` after rendering the panel (fire-and-forget).

## Rendered HTML (health section states)

**Loading (initial):**
```html
<div id="health-section">
  <span class="badge badge-default">checking…</span>
</div>
```

**Prometheus healthy, checks present:**
```html
<div id="health-section">
  <span class="badge badge-active">pass</span>
  <details class="health-checks">
    <summary>2 checks</summary>
    <table>
      <tr><th>Check</th><th>Status</th><th>Last updated</th></tr>
      <tr>
        <td>db_connectivity</td>
        <td><span class="badge badge-active">pass</span></td>
        <td>2026-05-28 14:22 UTC</td>
      </tr>
      <tr>
        <td>api_latency</td>
        <td><span class="badge badge-warning">warn</span></td>
        <td>2026-05-28 14:20 UTC</td>
      </tr>
    </table>
  </details>
</div>
```

**Prometheus unreachable:**
```html
<div id="health-section">
  <span class="badge badge-default">unavailable</span>
  <small style="color:#888">Prometheus unreachable</small>
</div>
```

## CSS

One new class added to the existing `<style>` block:

```css
.badge-warning { background-color: #f59e0b; color: #fff; }
```

The existing `badge-active` (green), `badge-inactive` (red), and `badge-default` (grey) classes already cover the other states.

## Testing

Four new tests in `tests/test_index_health_ui.js` (or manual browser verification if no JS test harness exists):

| Test | Input | Expected |
|---|---|---|
| Prometheus healthy, pass | `{ prom_health: "green", overall_status: "pass", checks: [...] }` | green badge, collapsible present |
| Prometheus healthy, warn | `{ prom_health: "green", overall_status: "warn", checks: [...] }` | amber badge |
| Prometheus healthy, fail | `{ prom_health: "green", overall_status: "fail", checks: [...] }` | red badge |
| Prometheus unreachable | `{ prom_health: "red" }` | grey "unavailable" badge |

Since `index.html` uses inline scripts (no module system), verification will be done via manual browser smoke testing against the running Flask app. No JS unit test framework is currently present in the project.
