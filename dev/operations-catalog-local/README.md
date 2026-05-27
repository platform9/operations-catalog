# Operations Catalog API

A Flask + PostgreSQL service catalog REST API, packaged for Kubernetes with a Helm chart.

---

## Local Setup

### Setup local env 
Create .env where your database.py is
```
PGHOST=localhost
PGPORT=5432
PGDATABASE=catalog
PGUSER=yourUserName
PGPASSWORD=yourPostgresPassword

```
```
source .env
```

### 1. Install Postgres and create the database

```
cd dev/operations-catalog-local/
./setup_db.py
```

### 2. Install dependencies and run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Only for local dev testing

```
# refer to template-entry.json and entry upload examples first
python seed.py
```

# Start the server
```
python app.py
# → http://localhost:5000
```

### 3. Environment variables (optional overrides)

| Variable | Default |
|----------|---------|
| `PGHOST` | `localhost` |
| `PGPORT` | `5432` |
| `PGDATABASE` | `catalog` |
| `PGUSER` | `catalog_user` |
| `PGPASSWORD` | `catalog_pass` |
| `PROMETHEUS_URL` | (required) Prometheus base URL, e.g. `http://prometheus:9090` |
| `PROMETHEUS_PUSHGATEWAY_URL` | (required for producers) Pushgateway URL, e.g. `http://pushgateway:9091` |

---

## Docker

```bash
docker build -t your-registry/operations-catalog-api:latest .
docker push your-registry/operations-catalog-api:latest
```

---

## Kubernetes (Helm)

```bash
helm install operations-catalog ./helm/operations-catalog-api \
  --namespace operations-catalog \
  --create-namespace \
  --set image.repository=your-registry/operations-catalog-api \
  --set postgres.host=your-postgres-host \
  --set postgres.password=your-password
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Health check |
| `GET` | `/catalog` | List all entries |
| `GET` | `/catalog/<id>` | Get entry by ID |
| `GET` | `/catalog/name/<name>` | Get entry by serviceName |
| `POST` | `/catalog` | Create entry |
| `PUT` | `/catalog/<id>` | Update entry by ID |
| `PUT` | `/catalog/name/<name>` | Update entry by serviceName |
| `DELETE` | `/catalog/<id>` | Delete entry by ID |
| `DELETE` | `/catalog/name/<name>` | Delete entry by serviceName |
| `GET` | `/catalog/name/<name>/health` | All health checks + overall status for a service |
| `GET` | `/catalog/name/<name>/health/<check>` | Single health check with detail |


## Pushing Health Checks

Use `push_health_check.py` to push a named health check result into Prometheus + Loki:

```bash
python push_health_check.py <service> <check_name> <pass|warn|fail> [detail]
```

Examples:
```bash
python push_health_check.py bork db_connectivity pass "Connected in 12ms"
python push_health_check.py bork queue_consumer warn "Consumer lag at 4500 messages"
python push_health_check.py bork db_connectivity fail "Connection refused"
```

Requires `PROMETHEUS_PUSHGATEWAY_URL` and `LOKI_URL` to be set. Each push writes a gauge metric to the Prometheus Pushgateway (for alerting/dashboards) and a structured JSON log event to Loki (for detail text).

`check_name` must be consistent across pushes — use snake_case identifiers (e.g. `db_connectivity`, not `DB Connectivity`).

### Updating the Prometheus dashboard link

The `health` field on each catalog entry stores a URL to the service's Prometheus/Grafana dashboard (not check state — check state lives in Prometheus + Loki). Update existing entries via the existing PUT endpoint:

```bash
curl -X PUT http://localhost:5000/catalog/name/bork \
  -H "Content-Type: application/json" \
  -d '{"health": "https://your-grafana/d/service-health?var-service=bork"}'
```


## Backup a local DB
```
# connected to DB
\du 

# back in the directory with values from above
cd dev/operations-catalog-local
pg_dump -h localhost -U yourUserName -d catalog > db_backups/$(date -u +"%Y-%m-%dT%H:%M")_catalog_backup.sql
```

## Restore a local DB

If needed, drop the local db and then recreate it
```
psql -U your_username -d postgres -c "DROP DATABASE catalog;"
psql -U your_username -d postgres -c "CREATE DATABASE catalog;"
```

Restore database
```
psql -U your_username -d catalog < catalog_backup.sql
```

If you need to restart the flask UI
```
python app.py
```

Verify
```
psql -U your_username -d catalog -c "SELECT * FROM catalog;"
```