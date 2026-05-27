import json
from flask import Flask, jsonify, request, abort, send_file, g
from flask_cors import CORS
from database import get_db, init_db, row_to_dict
from health_store import get_service_health, get_single_check

app = Flask(__name__)
CORS(app)


@app.before_request
def setup():
    init_db()


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/healthz", methods=["GET"])
def healthz():
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


# ── GET all catalog entries ───────────────────────────────────────────────────
@app.route("/catalog", methods=["GET"])
def get_catalog():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM catalog ORDER BY id')
        rows = [deserialize(row_to_dict(cur, row)) for row in cur.fetchall()]
    return jsonify(rows)


# ── GET single catalog entry by ID ───────────────────────────────────────────
@app.route("/catalog/<int:entry_id>", methods=["GET"])
def get_catalog_entry(entry_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM catalog WHERE id = %s', (entry_id,))
        row = cur.fetchone()
        if row is None:
            abort(404, description=f"Entry {entry_id} not found")
        return jsonify(deserialize(row_to_dict(cur, row)))


# ── GET single catalog entry by serviceName ───────────────────────────────────
@app.route("/catalog/name/<string:service_name>", methods=["GET"])
def get_catalog_entry_by_name(service_name):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM catalog WHERE "serviceName" = %s', (service_name,))
        row = cur.fetchone()
        if row is None:
            abort(404, description=f"Entry '{service_name}' not found")
        return jsonify(deserialize(row_to_dict(cur, row)))


# ── POST create a new catalog entry ──────────────────────────────────────────
@app.route("/catalog", methods=["POST"])
def create_catalog_entry():
    data = request.get_json(force=True)
    if not data or "serviceName" not in data:
        abort(400, description="'serviceName' is required")

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO catalog (
                "serviceName", health, description, status, "serviceCategory",
                "serviceSubjectMatterExperts", "criticalDependencies", documentation,
                "SLA", "targetAudience", "requestsChannel", "incidentManagement",
                "monitoringTools", "activeMaintenanceWindows", "onboardingDocumentation",
                "costModel", "versionInformation", "deprecationPolicy"
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
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
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.execute('SELECT * FROM catalog WHERE id = %s', (new_id,))
        row = cur.fetchone()
        return jsonify(deserialize(row_to_dict(cur, row))), 201


# ── PUT update a catalog entry by ID ─────────────────────────────────────────
@app.route("/catalog/<int:entry_id>", methods=["PUT"])
def update_catalog_entry(entry_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM catalog WHERE id = %s', (entry_id,))
        row = cur.fetchone()
        if row is None:
            abort(404, description=f"Entry {entry_id} not found")

        data = request.get_json(force=True)
        current = deserialize(row_to_dict(cur, row))
        current.update(data)

        cur.execute(
            """
            UPDATE catalog SET
                "serviceName"=%s, health=%s, description=%s, status=%s, "serviceCategory"=%s,
                "serviceSubjectMatterExperts"=%s, "criticalDependencies"=%s, documentation=%s,
                "SLA"=%s, "targetAudience"=%s, "requestsChannel"=%s, "incidentManagement"=%s,
                "monitoringTools"=%s, "activeMaintenanceWindows"=%s, "onboardingDocumentation"=%s,
                "costModel"=%s, "versionInformation"=%s, "deprecationPolicy"=%s
            WHERE id=%s
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
        conn.commit()
        cur.execute('SELECT * FROM catalog WHERE id = %s', (entry_id,))
        row = cur.fetchone()
        return jsonify(deserialize(row_to_dict(cur, row)))


# ── PUT update a catalog entry by serviceName ─────────────────────────────────
@app.route("/catalog/name/<string:service_name>", methods=["PUT"])
def update_catalog_entry_by_name(service_name):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM catalog WHERE "serviceName" = %s', (service_name,))
        row = cur.fetchone()
        if row is None:
            abort(404, description=f"Entry '{service_name}' not found")

        data = request.get_json(force=True)
        current = deserialize(row_to_dict(cur, row))
        current.update(data)

        cur.execute(
            """
            UPDATE catalog SET
                "serviceName"=%s, health=%s, description=%s, status=%s, "serviceCategory"=%s,
                "serviceSubjectMatterExperts"=%s, "criticalDependencies"=%s, documentation=%s,
                "SLA"=%s, "targetAudience"=%s, "requestsChannel"=%s, "incidentManagement"=%s,
                "monitoringTools"=%s, "activeMaintenanceWindows"=%s, "onboardingDocumentation"=%s,
                "costModel"=%s, "versionInformation"=%s, "deprecationPolicy"=%s
            WHERE "serviceName"=%s
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
                service_name,
            ),
        )
        conn.commit()
        cur.execute('SELECT * FROM catalog WHERE "serviceName" = %s', (service_name,))
        row = cur.fetchone()
        return jsonify(deserialize(row_to_dict(cur, row)))


# ── DELETE a catalog entry by ID ──────────────────────────────────────────────
@app.route("/catalog/<int:entry_id>", methods=["DELETE"])
def delete_catalog_entry(entry_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM catalog WHERE id = %s', (entry_id,))
        if cur.fetchone() is None:
            abort(404, description=f"Entry {entry_id} not found")
        cur.execute('DELETE FROM catalog WHERE id = %s', (entry_id,))
        conn.commit()
    return jsonify({"deleted": entry_id})


# ── DELETE a catalog entry by serviceName ─────────────────────────────────────
@app.route("/catalog/name/<string:service_name>", methods=["DELETE"])
def delete_catalog_entry_by_name(service_name):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM catalog WHERE "serviceName" = %s', (service_name,))
        if cur.fetchone() is None:
            abort(404, description=f"Entry '{service_name}' not found")
        cur.execute('DELETE FROM catalog WHERE "serviceName" = %s', (service_name,))
        conn.commit()
    return jsonify({"deleted": service_name})

# ── Health checks (groundcover) ───────────────────────────────────────────────
@app.route("/catalog/name/<string:service_name>/health", methods=["GET"])
def get_service_health_checks(service_name):
    try:
        result = get_service_health(service_name)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch health data: {str(e)}"}), 502
    return jsonify(result)


@app.route("/catalog/name/<string:service_name>/health/<string:check_name>", methods=["GET"])
def get_single_health_check(service_name, check_name):
    try:
        check = get_single_check(service_name, check_name)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch health data: {str(e)}"}), 502
    if check is None:
        abort(404, description=f"Check '{check_name}' not found for service '{service_name}'")
    return jsonify(check)


# ── Diagrams ────────────────────────────────────────────────────────────
@app.route("/docs")
def docs():
    return send_file("catalog_api_diagrams.html")


# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(e):
    return jsonify({"error": e.description}), e.code


# ── Helpers ───────────────────────────────────────────────────────────────────
JSON_FIELDS = {"serviceSubjectMatterExperts", "criticalDependencies", "documentation", "SLA"}

def deserialize(row):
    for field in JSON_FIELDS:
        if row.get(field) and isinstance(row[field], str):
            row[field] = json.loads(row[field])
    return row


@app.route("/")
def index():
    return send_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
