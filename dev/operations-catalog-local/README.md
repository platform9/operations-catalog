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

```bash
DLETELET ALLLL THISISSSSS WITHE SETUPDB FILE THERE
brew install postgresql@15
brew services start postgresql@15

# Create database and user
psql postgres
CREATE DATABASE catalog;
\l
CREATE USER $PGUSER WITH PASSWORD $PGPASSWORD;
GRANT ALL PRIVILEGES ON DATABASE catalog TO catalog_user;
\q
```
```
chmod +x setup_db.py
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


## Backup a local DB
```
# connected to DB
\du 

# back in the directory with values from above
pg_dump -h localhost -U your_username -d mydb > backup.sql
```

## Restore a local DB

If needed, drop the local db
```
psql -U bensmith_pf9 -d postgres -c "DROP DATABASE catalog;" 
```

Create the database
```
psql -U bensmith_pf9 -d postgres -c "CREATE DATABASE catalog;" 
```

Restore database
```
psql -U your_username -d mydb < backup.sql
```

Verify
```
psql -U your_username -d mydb -c "SELECT * FROM catalog;"
```