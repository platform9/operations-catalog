"""
seed.py — populate the database with sample data.
Run once: python seed.py
"""

import json
import sqlite3
from database import DATABASE, SCHEMA

SAMPLE = {
    "serviceName": "Spiderman",
    "description": "with great power comes great responsibility",
    "status": "Active",
    "serviceCategory": "TBD",
    "serviceSubjectMatterExperts": ["Platform Engineering", "Peter Parker"],
    "criticalDependencies": ["link|description"],
    "documentation": ["https://example.com/docs"],
    "SLA": {
        "externalLink": "https://<>"
    },
    "targetAudience": "Platform9 Internal",
    "requestsChannel": "Platform Engineering",
    "incidentManagement": "SRE",
    "monitoringTools": "UNDEFINED",
    "activeMaintenanceWindows": "UNDEFINED",
    "onboardingDocumentation": "https://example.com/onboarding",
    "costModel": "External information needed",
    "versionInformation": "N/A",
    "deprecationPolicy": "External information needed",
}

if __name__ == "__main__":
    conn = sqlite3.connect(DATABASE)
    conn.executescript(SCHEMA)
    conn.execute(
        """
        INSERT INTO catalog (
            serviceName, description, status, serviceCategory,
            serviceSubjectMatterExperts, criticalDependencies, documentation,
            SLA, targetAudience, requestsChannel, incidentManagement,
            monitoringTools, activeMaintenanceWindows, onboardingDocumentation,
            costModel, versionInformation, deprecationPolicy
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            SAMPLE["serviceName"],
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
        ),
    )
    conn.commit()
    conn.close()
    print("Seeded 1 catalog entry.")
