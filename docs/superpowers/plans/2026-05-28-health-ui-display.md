# Health UI Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `index.html` so the service detail panel fetches and displays live Prometheus health data — an overall_status badge and an expandable checks table.

**Architecture:** When a service is selected, `selectEntry` renders the panel immediately from pre-loaded list data with a "checking…" placeholder in the Health field, then calls `fetchAndRenderHealth(serviceName)` which hits `GET /catalog/name/<serviceName>` and swaps in the real health content once the response arrives.

**Tech Stack:** Vanilla JS, HTML/CSS (no build step, no JS test framework — verification is manual browser smoke test)

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `dev/operations-catalog-local/index.html` | All health display changes |

---

## Task 1: Update health display in index.html

**Files:**
- Modify: `dev/operations-catalog-local/index.html`

- [ ] **Step 1: Add `.badge-warning` and `.health-checks` CSS**

In the `<style>` block, after the existing `.badge-default` rule (line 190), insert:

```css
.badge-warning  { background: #fef3c7; color: #92400e; }

.health-checks { margin-top: 8px; }
.health-checks summary {
  font-size: 12px;
  color: #78716c;
  cursor: pointer;
  user-select: none;
  padding: 2px 0;
}
.health-checks summary:hover { color: #1c1917; }
.health-checks table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  font-size: 12px;
}
.health-checks th {
  text-align: left;
  color: #78716c;
  font-weight: 600;
  padding: 4px 8px 4px 0;
  border-bottom: 1px solid #e7e5e4;
}
.health-checks td { padding: 6px 8px 6px 0; border-bottom: 1px solid #f5f5f4; }
```

- [ ] **Step 2: Remove `getHealthValue` and update `renderList` sidebar meta**

**Delete** the entire `getHealthValue` function (currently lines 389–393):

```js
// DELETE — old array-of-{key,value} helper, no longer used:
function getHealthValue(health, key) {
    if (!health || !Array.isArray(health)) return null;
    const entry = health.find(h => h.key === key);
    return entry ? entry.value : null;
}
```

**Update** the `entry-meta` line inside `renderList` (currently line 321). The existing line reads:

```js
<div class="entry-meta">${esc(e.serviceCategory || '—')} · ${esc(e.status || 'Unknown')} · ${esc(getHealthValue(e.health, 'overall') || '—')}</div>
```

Change it to (health is detail-panel only — no sidebar indicator):

```js
<div class="entry-meta">${esc(e.serviceCategory || '—')} · ${esc(e.status || 'Unknown')}</div>
```

- [ ] **Step 3: Rewrite `healthBadgeClass` for new data shape**

Replace the existing `healthBadgeClass` function (lines 395–403) with:

```js
function healthBadgeClass(health) {
    if (!health || health.prom_health === 'red') return 'badge-default';
    switch (health.overall_status) {
        case 'pass': return 'badge-active';
        case 'warn': return 'badge-warning';
        case 'fail': return 'badge-inactive';
        default:     return 'badge-default';
    }
}
```

- [ ] **Step 4: Replace `healthField` with `renderHealthSection`**

Replace the entire `healthField` function (lines 405–414) with:

```js
function renderHealthSection(health) {
    if (!health || health.prom_health === 'red') {
        return `<div class="field full">
          <div class="field-label">Health</div>
          <div class="field-value">
            <span class="badge badge-default">unavailable</span>
            <small style="color:#888;margin-left:6px">Prometheus unreachable</small>
          </div>
        </div>`;
    }
    const overallClass = healthBadgeClass(health);
    const checks = health.checks || [];
    const checkRows = checks.map(c => {
        const cls = c.status === 'pass' ? 'badge-active'
                  : c.status === 'warn' ? 'badge-warning'
                  : 'badge-inactive';
        const ts = c.last_updated
            ? new Date(c.last_updated).toUTCString().replace(' GMT', ' UTC')
            : '—';
        return `<tr>
          <td>${esc(c.check_name)}</td>
          <td><span class="badge ${cls}">${esc(c.status)}</span></td>
          <td style="color:#78716c">${ts}</td>
        </tr>`;
    }).join('');
    const summary = checks.length === 1 ? '1 check' : `${checks.length} checks`;
    return `<div class="field full">
      <div class="field-label">Health</div>
      <div style="margin-top:4px">
        <span class="badge ${overallClass}">${esc(health.overall_status)}</span>
        ${checks.length ? `
        <details class="health-checks">
          <summary>${summary}</summary>
          <table>
            <tr><th>Check</th><th>Status</th><th>Last updated</th></tr>
            ${checkRows}
          </table>
        </details>` : ''}
      </div>
    </div>`;
}
```

- [ ] **Step 5: Add `fetchAndRenderHealth` async function**

Add the following immediately after `renderHealthSection`:

```js
async function fetchAndRenderHealth(serviceName) {
    const el = document.getElementById('health-section');
    if (!el) return;
    try {
        const base = document.getElementById('api-url').value.replace(/\/$/, '');
        const resp = await fetch(`${base}/catalog/name/${encodeURIComponent(serviceName)}`);
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        el.outerHTML = renderHealthSection(data.health);
    } catch (_) {
        el.outerHTML = renderHealthSection(null);
    }
}
```

`outerHTML` replaces the entire `<div id="health-section">` element with the rendered field block. `renderHealthSection(null)` produces the "unavailable / Prometheus unreachable" state, which is also the right fallback for a network failure.

- [ ] **Step 6: Update `renderDetail` — remove health from header, add loading health-section**

Replace the entire `renderDetail` function with the following. Key changes vs. the original:

1. The second `<span class="badge …">` in the header (the health badge) is **removed** — health is now displayed only in the fields grid.
2. `${healthField(e.health)}` in the `.fields` block is replaced with `<div id="health-section" …>checking…</div>`.

```js
function renderDetail(e) {
    const status = (e.status || '').toLowerCase();
    const badgeClass = status === 'active' ? 'badge-active' : status === 'inactive' ? 'badge-inactive' : 'badge-default';

    document.getElementById('detail').innerHTML = `
      <div class="detail-card">
        <div class="detail-header">
          <div>
            <div class="detail-title">${esc(e.serviceName)}</div>
            <div class="detail-subtitle">${esc(e.serviceCategory || 'Uncategorized')}</div>
          </div>
          <span class="badge ${badgeClass}">${esc(e.status || 'Unknown')}</span>
        </div>
        <div class="fields">
          ${field('Description', e.description, true)}
          <div id="health-section" class="field full">
            <div class="field-label">Health</div>
            <div class="field-value"><span class="badge badge-default">checking…</span></div>
          </div>
          ${field('Target audience', e.targetAudience)}
          ${field('Requests channel', e.requestsChannel)}
          ${field('Incident management', e.incidentManagement)}
          ${field('Monitoring tools', e.monitoringTools)}
          ${field('Maintenance windows', e.activeMaintenanceWindows)}
          ${field('Cost model', e.costModel)}
          ${field('Version info', e.versionInformation)}
          ${field('Deprecation policy', e.deprecationPolicy)}
          ${tagsField('Subject matter experts', e.serviceSubjectMatterExperts)}
          ${tagsField('Critical dependencies', e.criticalDependencies)}
          ${linksField('Documentation', e.documentation)}
          ${slaField(e.SLA)}
          ${e.onboardingDocumentation ? linkField('Onboarding docs', e.onboardingDocumentation) : ''}
        </div>
      </div>
    `;
}
```

- [ ] **Step 7: Update `selectEntry` to trigger the async health fetch**

Change `selectEntry` from:

```js
function selectEntry(id) {
    selectedId = id;
    renderList();
    const e = entries.find(x => x.id === id);
    if (e) renderDetail(e);
}
```

To:

```js
function selectEntry(id) {
    selectedId = id;
    renderList();
    const e = entries.find(x => x.id === id);
    if (e) {
        renderDetail(e);
        fetchAndRenderHealth(e.serviceName);
    }
}
```

`renderDetail` is synchronous and sets the `innerHTML` (including `<div id="health-section">`), so the element exists in the DOM by the time `fetchAndRenderHealth` runs its `getElementById` lookup.

- [ ] **Step 8: Manual smoke test**

Start the Flask app (from the PR #3 branch, which has the `enrich_entry` enrichment and `POST /health` endpoint):

```bash
cd dev/operations-catalog-local
source venv/bin/activate
python app.py
```

Open `index.html` in a browser directly (File → Open) or via `http://localhost:5000` if the app serves it. Set the API URL to `http://localhost:5000` and click **Load**.

**Scenario A — Prometheus is running and has data:**

First push a health check so there is data:
```bash
python push_health_check.py bork db_connectivity pass
```

Click "bork" in the sidebar. Verify:
1. Panel renders instantly — service name, description, and all fields appear immediately.
2. Health field shows a grey "checking…" badge briefly.
3. Health field updates to show a **green "pass" badge** and a "1 check" expandable summary.
4. Clicking "1 check" expands the table showing `db_connectivity / pass / <timestamp>`.
5. Sidebar entry-meta shows only `category · status` — no health value.

**Scenario B — Prometheus not running:**

Stop Prometheus (or point `PROMETHEUS_URL` at a bad address). Click any service. Verify:
1. Health field shows "checking…" briefly, then shows grey **"unavailable"** badge + "Prometheus unreachable".

**Scenario C — warn and fail statuses:**

```bash
python push_health_check.py bork api_latency warn
python push_health_check.py bork disk_usage fail
```

Click "bork". Verify the overall_status badge shows **"fail"** (red — worst of the three), and the collapsible shows all three checks with correct colors (green/amber/red).

- [ ] **Step 9: Commit**

```bash
git add dev/operations-catalog-local/index.html
git commit -m "feat: display Prometheus health data in service detail panel"
```
