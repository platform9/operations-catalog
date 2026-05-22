# Service Catalog API — Local Setup

## Requirements
- Python 3.10+

## Setup & Run

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) CAUTION! Erase the local SQLite db and seed the database with a sample entry
rm -f catalog.db
python seed.py

# 4. Start the server
python app.py
# → http://localhost:5000

# 5. Open local UI
open index.html
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Health check |
| `GET` | `/catalog` | List all entries |
| `GET` | `/catalog/<id>` | Get a single entry |
| `POST` | `/catalog` | Create a new entry |
| `PUT` | `/catalog/<id>` | Update an entry |
| `DELETE` | `/catalog/<id>` | Delete an entry |

## Data Model

| Field | Type |
|-------|------|
| `serviceName` | string (required) |
| `description` | string |
| `status` | string (e.g. Active, Inactive) |
| `serviceCategory` | string |
| `serviceSubjectMatterExperts` | array of strings |
| `criticalDependencies` | array of strings |
| `documentation` | array of URLs |
| `SLA` | object `{"externalLink": "..."}` |
| `targetAudience` | string |
| `requestsChannel` | string |
| `incidentManagement` | string |
| `monitoringTools` | string |
| `activeMaintenanceWindows` | string |
| `onboardingDocumentation` | string |
| `costModel` | string |
| `versionInformation` | string |
| `deprecationPolicy` | string |

# See template-entry.json
```
cat ./template-entry.json
```