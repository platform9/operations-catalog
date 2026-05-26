import os
import psycopg2
import psycopg2.extras
from flask import g
from dotenv import load_dotenv
load_dotenv()

# Connection config from environment variables
DB_CONFIG = {
    "host":     os.environ.get("PGHOST", "localhost"),
    "port":     os.environ.get("PGPORT", "5432"),
    "dbname":   os.environ.get("PGDATABASE", "catalog"),
    "user":     os.environ.get("PGUSER", "catalog_user"),
    "password": os.environ.get("PGPASSWORD", "catalog_pass"),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog (
    id                          SERIAL PRIMARY KEY,
    "serviceName"               TEXT NOT NULL,
    health                      TEXT,
    description                 TEXT,
    status                      TEXT,
    "serviceCategory"           TEXT,
    "serviceSubjectMatterExperts" JSONB,
    "criticalDependencies"      JSONB,
    documentation               JSONB,
    "SLA"                       JSONB,
    "targetAudience"            TEXT,
    "requestsChannel"           TEXT,
    "incidentManagement"        TEXT,
    "monitoringTools"           TEXT,
    "activeMaintenanceWindows"  TEXT,
    "onboardingDocumentation"   TEXT,
    "costModel"                 TEXT,
    "versionInformation"        TEXT,
    "deprecationPolicy"         TEXT
);
"""


def get_db():
    """Return the per-request Postgres connection, creating it if needed."""
    if "db" not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
    return g.db


def init_db():
    """Create tables if they don't exist yet."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
    conn.commit()


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def row_to_dict(cursor, row):
    """Convert a psycopg2 row to a dict using cursor description."""
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))
