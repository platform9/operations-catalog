import json
from flask import Flask, jsonify, request, abort, send_file
from database import get_db, init_db

app = Flask(__name__)


@app.before_request
def setup():
    init_db()


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/healthz", methods=["GET"])
def healthz():
    try:
        get_db().execute("SELECT 1")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


# ── GET all catalog entries ───────────────────────────────────────────────────
@app.route("/catalog", methods=["GET"])
def get_catalog():
    db = get_db()
    rows = db.execute("SELECT * FROM catalog").fetchall()
    return jsonify([deserialize(row) for row in rows])


# ── GET single catalog entry by ID ───────────────────────────────────────────
@app.route("/catalog/<int:entry_id>", methods=["GET"])
def get_catalog_entry(entry_id):
    db = get_db()
    row = db.execute("SELECT * FROM catalog WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        abort(404, description=f"Entry {entry_id} not found")
    return jsonify(deserialize(row))


# ── POST create a new catalog entry ──────────────────────────────────────────
@app.route("/catalog", methods=["POST"])
def create_catalog_entry():
    data = request.get_json(force=True)
    if not data or "serviceName" not in data:
        abort(400, description="'serviceName' is required")

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO catalog (
            serviceName, health, description, status, serviceCategory,
            serviceSubjectMatterExperts, criticalDependencies, documentation,
            SLA, targetAudience, requestsChannel, incidentManagement,
            monitoringTools, activeMaintenanceWindows, onboardingDocumentation,
            costModel, versionInformation, deprecationPolicy
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            data.get("serviceName"),
            data.get("health"),
            data.get("description"),
            data.get("status"),
            data.get("serviceCategory"),
            json.dumps(data.get("serviceSubjectMatterExperts", [])),
            json.dumps(data.get("criticalDependencies", [])),
            json.dumps(data.get("documentation", [])),
            json.dumps(data.get("SLA", {})),
            data.get("targetAudience"),
            data.get("requestsChannel"),
            data.get("incidentManagement"),
            data.get("monitoringTools"),
            data.get("activeMaintenanceWindows"),
            data.get("onboardingDocumentation"),
            data.get("costModel"),
            data.get("versionInformation"),
            data.get("deprecationPolicy"),
        ),
    )
    db.commit()
    new_id = cursor.lastrowid
    row = db.execute("SELECT * FROM catalog WHERE id = ?", (new_id,)).fetchone()
    return jsonify(deserialize(row)), 201


# ── PUT update a catalog entry ────────────────────────────────────────────────
@app.route("/catalog/<int:entry_id>", methods=["PUT"])
def update_catalog_entry(entry_id):
    db = get_db()
    existing = db.execute("SELECT * FROM catalog WHERE id = ?", (entry_id,)).fetchone()
    if existing is None:
        abort(404, description=f"Entry {entry_id} not found")

    data = request.get_json(force=True)
    current = deserialize(existing)
    current.update(data)

    db.execute(
        """
        UPDATE catalog SET
            serviceName=?, description=?, status=?, serviceCategory=?,
            serviceSubjectMatterExperts=?, criticalDependencies=?, documentation=?,
            SLA=?, targetAudience=?, requestsChannel=?, incidentManagement=?,
            monitoringTools=?, activeMaintenanceWindows=?, onboardingDocumentation=?,
            costModel=?, versionInformation=?, deprecationPolicy=?
        WHERE id=?
        """,
        (
            current.get("serviceName"),
            current.get("health"),
            current.get("description"),
            current.get("status"),
            current.get("serviceCategory"),
            json.dumps(current.get("serviceSubjectMatterExperts", [])),
            json.dumps(current.get("criticalDependencies", [])),
            json.dumps(current.get("documentation", [])),
            json.dumps(current.get("SLA", {})),
            current.get("targetAudience"),
            current.get("requestsChannel"),
            current.get("incidentManagement"),
            current.get("monitoringTools"),
            current.get("activeMaintenanceWindows"),
            current.get("onboardingDocumentation"),
            current.get("costModel"),
            current.get("versionInformation"),
            current.get("deprecationPolicy"),
            entry_id,
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM catalog WHERE id = ?", (entry_id,)).fetchone()
    return jsonify(deserialize(row))


# ── DELETE a catalog entry ────────────────────────────────────────────────────
@app.route("/catalog/<int:entry_id>", methods=["DELETE"])
def delete_catalog_entry(entry_id):
    db = get_db()
    existing = db.execute("SELECT id FROM catalog WHERE id = ?", (entry_id,)).fetchone()
    if existing is None:
        abort(404, description=f"Entry {entry_id} not found")
    db.execute("DELETE FROM catalog WHERE id = ?", (entry_id,))
    db.commit()
    return jsonify({"deleted": entry_id})

# ── DELETE a catalog entry by serviceName ────────────────────────────────────────────────────
@app.route("/catalog/name/<string:service_name>", methods=["DELETE"])
def delete_catalog_entry_by_name(service_name):
    db = get_db()
    existing = db.execute("SELECT id FROM catalog WHERE serviceName = ?", (service_name,)).fetchone()
    if existing is None:
        abort(404, description=f"Entry '{service_name}' not found")
    db.execute("DELETE FROM catalog WHERE serviceName = ?", (service_name,))
    db.commit()
    return jsonify({"deleted": service_name})


# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(e):
    return jsonify({"error": e.description}), e.code


# ── Helpers ───────────────────────────────────────────────────────────────────
JSON_FIELDS = {"serviceSubjectMatterExperts", "criticalDependencies", "documentation", "SLA"}

def deserialize(row):
    d = dict(row)
    for field in JSON_FIELDS:
        if d.get(field):
            d[field] = json.loads(d[field])
    return d


@app.route("/")
def index():
    return send_file("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
