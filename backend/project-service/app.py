from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timezone
import os

app = Flask(__name__)
CORS(app)
JSON_PATH = os.getenv("JSON_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")

cred = credentials.Certificate(JSON_PATH)
firebase_admin.initialize_app(cred, {
    "databaseURL": DATABASE_URL
})


# Helper to check role for creation
def can_create(role):
    return role in ("manager", "director")

# Helper to get current timestamp string
def current_timestamp():
    return datetime.now(timezone.utc).isoformat()

@app.route("/project/create", methods=["POST"])
def create_project():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    role = data.get("role")

    # Check required fields
    if not userid or not role:
        return jsonify(error="userid and role required"), 400

    if not can_create(role):
        return jsonify(error="Unauthorized: role not allowed to create"), 403

    # Generate unique UID for new project
    project_ref = db.reference("project")
    new_proj_ref = project_ref.push()
    uid = new_proj_ref.key

    # Create project data
    project_data = {
        "uid": uid,
        "title": data.get("title", ""),
        "ownerUid": userid,
        "collaborators": data.get("collaborators", [])+[userid],
        "description": data.get("description", ""),
        "status": data.get("status", ""),
        "deadline": data.get("deadline", ""),
        "creationDate": current_timestamp(),
        "comments": data.get("comments", [])
    }

    new_proj_ref.set(project_data)

    return jsonify({"message": "Project created", "project": project_data}), 201


@app.route("/project/<userid>", methods=["GET"])
def read_projects(userid):
    # Retrieve all projects under "project" node
    project_ref = db.reference("project")
    all_projects = project_ref.get() or {}

    # Filter projects where the user is in the collaborators list
    collaborator_projects = [
        proj for proj in all_projects.values()
        if userid in proj.get("collaborators", [])
    ]

    return jsonify({"projects": collaborator_projects}), 200


@app.route("/project/delete", methods=["POST"])
def delete_project():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    uid = data.get("uid")
    if not userid or not uid:
        return jsonify(error="userid and uid required"), 400

    project_ref = db.reference(f"project/{uid}")
    project = project_ref.get()
    if not project:
        return jsonify(error="Project not found"), 404

    if project.get("ownerUid") != userid:
        return jsonify(error="Unauthorized: only owner can delete"), 403

    project_ref.delete()
    return jsonify({"message": "Project deleted"}), 200

@app.route("/project/update", methods=["POST"])
def update_project():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    uid = data.get("uid")
    if not userid or not uid:
        return jsonify(error="userid and uid required"), 400

    # Fields allowed to update
    allowed_fields = {"deadline", "description", "status", "title"}

    # Filter update fields present in the request
    updates = {k: v for k, v in data.items() if k in allowed_fields}

    if not updates:
        return jsonify(error="At least one updatable field (deadline, description, status, title) required"), 400

    project_ref = db.reference(f"project/{uid}")
    project = project_ref.get()
    if not project:
        return jsonify(error="Project not found"), 404

    if project.get("ownerUid") != userid:
        return jsonify(error="Unauthorized: only owner can update"), 403

    # Update project data with allowed fields
    project_ref.update(updates)

    updated_project = project_ref.get()
    return jsonify({"message": "Project updated", "project": updated_project}), 200
@app.route("/project/add-collaborator", methods=["POST"])
def add_collaborator():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    adduserid = data.get("adduserid")
    uid = data.get("uid")
    if not userid or not adduserid or not uid:
        return jsonify(error="userid, adduserid and uid required"), 400

    project_ref = db.reference(f"project/{uid}")
    project = project_ref.get()
    if not project:
        return jsonify(error="Project not found"), 404

    # Only owner can add collaborators
    if project.get("ownerUid") != userid:
        return jsonify(error="Unauthorized: only owner can add collaborators"), 403

    collaborators = set(project.get("collaborators", []))
    collaborators.add(adduserid)

    project_ref.update({"collaborators": list(collaborators)})

    updated_project = project_ref.get()
    return jsonify({"message": "Collaborator added", "project": updated_project}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)
