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

@app.route("/project/indiv/<projectid>", methods=["GET"])
def read_project(projectid):
    # Retrieve specific project by projectid
    project_ref = db.reference(f"project/{projectid}")
    project_data = project_ref.get()
    
    # Check if project exists and if projectid matches the uid in the project
    if project_data and project_data.get("projectId") == projectid:
        return jsonify({"project": project_data}), 200
    else:
        return jsonify({"error": "Project not found or access denied"}), 404

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

    # Check if any tasks exist under this project
    tasks_ref = db.reference("tasks")
    all_tasks = tasks_ref.get() or {}
    project_tasks = [t for t in all_tasks.values() if t.get("project") == uid]

    if project_tasks:
        return jsonify(error="Cannot delete project with existing tasks"), 400

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


@app.route("/project/change-owner", methods=["POST"])
def change_owner():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")          # Current owner making the change
    changeuserid = data.get("changeuserid")  # New owner to assign
    uid = data.get("uid")
    if not userid or not changeuserid or not uid:
        return jsonify(error="userid, changeuserid, and uid required"), 400

    project_ref = db.reference(f"project/{uid}")
    project = project_ref.get()
    if not project:
        return jsonify(error="Project not found"), 404

    # Check current owner matches userid
    if project.get("ownerUid") != userid:
        return jsonify(error="Unauthorized: only current owner can change owner"), 403

    # Only change owner if status == "unassigned"
    if project.get("status") != "unassigned":
        return jsonify(error="Owner can only be changed if project status is 'unassigned'"), 400

    # Get roles of both users from /users node
    users_ref = db.reference("users")
    users = users_ref.get() or {}

    current_owner_role = users.get(userid, {}).get("role")
    new_owner_role = users.get(changeuserid, {}).get("role")

    if not current_owner_role or not new_owner_role:
        return jsonify(error="User roles not found in /users database"), 404

    # Validate delegation rules:
    # director can delegate only to manager
    # manager can delegate to users who are NOT manager or director
    if current_owner_role == "director":
        if new_owner_role != "manager":
            return jsonify(error="Director can only delegate ownership to a manager"), 403
    elif current_owner_role == "manager":
        if new_owner_role in ("manager", "director"):
            return jsonify(error="Manager cannot delegate ownership to manager or director"), 403
    else:
        return jsonify(error="Only director or manager can delegate ownership"), 403

    # Perform ownership change and add new owner as collaborator if not already present
    collaborators = set(project.get("collaborators", []))
    collaborators.add(changeuserid)

    project_ref.update({
        "ownerUid": changeuserid,
        "collaborators": list(collaborators)
    })

    updated_project = project_ref.get()
    return jsonify({"message": "Project ownership changed", "project": updated_project}), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)
