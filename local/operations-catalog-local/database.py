import sqlite3
import os
from flask import g

DATABASE = os.environ.get("DATABASE_PATH", "catalog.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    serviceName                 TEXT NOT NULL,
    description                 TEXT,
    status                      TEXT,
    serviceCategory             TEXT,
    serviceSubjectMatterExperts TEXT,   -- JSON array
    criticalDependencies        TEXT,   -- JSON array
    documentation               TEXT,   -- JSON array
    SLA                         TEXT,   -- JSON object
    targetAudience              TEXT,
    requestsChannel             TEXT,
    incidentManagement          TEXT,
    monitoringTools             TEXT,
    activeMaintenanceWindows    TEXT,
    onboardingDocumentation     TEXT,
    costModel                   TEXT,
    versionInformation          TEXT,
    deprecationPolicy           TEXT
);
"""


def get_db():
    """Return the per-request SQLite connection, creating it if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    """Create tables if they don't exist yet."""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
