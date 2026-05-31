"""
seed.py — populate the database with a sample entry.
Run once: python seed.py
"""

import json
import psycopg2
import os

DB_CONFIG = {
    "host":     os.environ.get("PGHOST", "localhost"),
    "port":     os.environ.get("PGPORT", "5432"),
    "dbname":   os.environ.get("PGDATABASE", "catalog"),
    "user":     os.environ.get("PGUSER", "catalog_user"),
    "password": os.environ.get("PGPASSWORD", "catalog_pass"),
}

SAMPLE = {
    "serviceName": "Spiderman",
    "health": "GREEN",
    "description": "with great power comes great responsibility",
    "status": "Active",
    "serviceCategory": "TBD",
    "serviceSubjectMatterExperts": ["Platform Engineering", "Peter Parker"],
    "criticalDependencies": ["link|description"],
    "documentation": ["https://example.com/docs"],
    "SLA": {"externalLink": "https://<>"},
    "targetAudience": "Platform9 Internal",
    "requestsChannel": "Platform Engineering",
    "incidentManagement": "SRE",
    "monitoringTools": "UNDEFINED",
    "activeMaintenanceWindows": "UNDEFINED",
    "onboardingDocumentation": "https://example.com/onboarding",
    "costModel": "External information needed",
    "versionInformation": "N/A",
    "deprecationPolicy": "External information needed",
    "statusPageUrl": None,
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
    "deprecationPolicy"         TEXT,
    "statusPageUrl"             TEXT
);
"""

if __name__ == "__main__":
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(SCHEMA)
    cur.execute(
        """
        INSERT INTO catalog (
            "serviceName", health, description, status, "serviceCategory",
            "serviceSubjectMatterExperts", "criticalDependencies", documentation,
            "SLA", "targetAudience", "requestsChannel", "incidentManagement",
            "monitoringTools", "activeMaintenanceWindows", "onboardingDocumentation",
            "costModel", "versionInformation", "deprecationPolicy", "statusPageUrl"
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            SAMPLE["serviceName"],
            SAMPLE["health"],
            SAMPLE["description"],
            SAMPLE["status"],
            SAMPLE["serviceCategory"],
            json.dumps(SAMPLE["serviceSubjectMatterExperts"]),
            json.dumps(SAMPLE["criticalDependencies"]),
            json.dumps(SAMPLE["documentation"]),
            json.dumps(SAMPLE["SLA"]),
            SAMPLE["targetAudience"],
            SAMPLE["requestsChannel"],
            SAMPLE["incidentManagement"],
            SAMPLE["monitoringTools"],
            SAMPLE["activeMaintenanceWindows"],
            SAMPLE["onboardingDocumentation"],
            SAMPLE["costModel"],
            SAMPLE["versionInformation"],
            SAMPLE["deprecationPolicy"],
            SAMPLE["statusPageUrl"],
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    print("Seeded 1 catalog entry.")
