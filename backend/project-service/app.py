# backend/project-service/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timezone
import os

app = Flask(__name__)
CORS(app)

# --- Firebase setup ---
JSON_PATH = os.getenv("JSON_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")

cred = credentials.Certificate(JSON_PATH)
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

# --- Helpers ---
def current_timestamp():
    return int(datetime.now(timezone.utc).timestamp())

# --- Create project ---
@app.route("/project/create", methods=["POST"])
def create_project():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    role = data.get("role")
    if not userid or not role:
        return jsonify(error="userid and role required"), 400

    # Fetch creator info
    users_ref = db.reference("users")
    user_info = users_ref.child(userid).get()
    if not user_info:
        return jsonify(error="User not found"), 404

    department = user_info.get("department", "Unknown")

    project_ref = db.reference("project")
    new_proj_ref = project_ref.push()
    uid = new_proj_ref.key

    project_data = {
        "projectId": uid,
        "title": data.get("title", ""),
        "ownerId": userid,
        "collaborators": list(set(data.get("collaborators", []) + [userid])),
        "description": data.get("description", ""),
        "deadline": data.get("deadline", ""),
        "creationDate": current_timestamp(),
        "department": department
    }

    new_proj_ref.set(project_data)
    return jsonify({"message": "Project created", "project": project_data}), 201

# --- Get all projects (admin/debug) ---
@app.route("/project/all", methods=["GET"])
def get_all_projects():
    project_ref = db.reference("project")
    all_projects = project_ref.get() or {}
    print("All projects retrieved from DB:", len(all_projects))
    return jsonify({"projects": list(all_projects.values())}), 200

# --- Get projects by department (for directors) ---
@app.route("/project/department/<department>", methods=["GET"])
def get_projects_by_department(department):
    project_ref = db.reference("project")
    all_projects = project_ref.get() or {}
    
    dept_lower = (department or "unknown").lower()
    dept_projects = [
        proj for proj in all_projects.values()
        if (proj.get("department") or "unknown").lower() == dept_lower
    ]

    print(f"Department requested: {department}, Projects found: {len(dept_projects)}")
    return jsonify({"projects": dept_projects}), 200

# --- Get projects for a specific user (non-directors) ---
@app.route("/project/<userid>", methods=["GET"])
def get_user_projects(userid):
    project_ref = db.reference("project")
    all_projects = project_ref.get() or {}

    user_projects = [
        proj for proj in all_projects.values()
        if userid == proj.get("ownerId") or userid in proj.get("collaborators", [])
    ]
    return jsonify({"projects": user_projects}), 200

# --- Update project ---
@app.route("/project/update", methods=["POST"])
def update_project():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get('userid')
    project_id = data.get('projectId')
    new_title = data.get('title')
    new_deadline = data.get('deadline')
    new_description = data.get('description')
    new_collaborators = data.get('collaborators', [])
    new_owner_id = data.get('ownerId')

    if not userid or not project_id:
        return jsonify(error="userid and projectId are required"), 400

    project_ref = db.reference(f'project/{project_id}')
    project = project_ref.get()
    if not project:
        return jsonify(error="Project not found"), 404

    if project.get('ownerId') != userid:
        return jsonify(error="Only project owner can update the project"), 403

    updated_data = {}
    if new_title is not None:
        updated_data['title'] = new_title
    if new_deadline is not None:
        updated_data['deadline'] = new_deadline
    if new_description is not None:
        updated_data['description'] = new_description

    current_collaborators = set(project.get('collaborators', []))
    filtered_new_collaborators = [uid for uid in new_collaborators if uid not in current_collaborators]
    updated_collaborators = list(current_collaborators) + filtered_new_collaborators
    updated_data['collaborators'] = updated_collaborators

    if new_owner_id and new_owner_id != project.get('ownerId'):
        users_ref = db.reference("users")
        users = users_ref.get() or {}
        current_owner_role = users.get(userid, {}).get("role")
        new_owner_role = users.get(new_owner_id, {}).get("role")
        roles_order = {'director': 3, 'manager': 2, 'staff': 1}

        if roles_order.get(current_owner_role, 0) < roles_order.get(new_owner_role, 0):
            return jsonify(error="Cannot assign project ownership to a higher role"), 403

        updated_data['ownerId'] = new_owner_id
        if new_owner_id not in updated_collaborators:
            updated_collaborators.append(new_owner_id)
        updated_data['collaborators'] = updated_collaborators

    if updated_data:
        project_ref.update(updated_data)

    return jsonify(success=True, updatedProject=updated_data), 200

# --- Get all users ---
@app.route("/project/all-users", methods=["GET"])
def get_all_users():
    users_ref = db.reference("users")
    all_users = users_ref.get() or {}
    users_list = [{"uid": uid, "name": info.get("name"), "email": info.get("email")} 
                  for uid, info in all_users.items()]
    return jsonify({"users": users_list}), 200

# --- Get available users for collaboration ---
@app.route("/project/users/available-for-collaboration/<uid>", methods=["GET"])
def get_available_users(uid):
    project_ref = db.reference(f"project/{uid}")
    project = project_ref.get()
    if not project:
        return jsonify(error="Project not found"), 404

    users_ref = db.reference("users")
    all_users = users_ref.get() or {}
    owner_uid = project.get("ownerId")
    current_collaborators = set(project.get("collaborators", []))

    available_users = [
        {"uid": user_uid, "name": user_info.get("name"), "email": user_info.get("email")}
        for user_uid, user_info in all_users.items()
        if user_uid != owner_uid and user_uid not in current_collaborators
    ]

    return jsonify({"availableUsers": available_users}), 200

# --- Add collaborators ---
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

    if project.get("ownerId") != userid:
        return jsonify(error="Unauthorized: only owner can add collaborators"), 403

    collaborators = set(project.get("collaborators", []))
    for new_collab in adduserid:
        collaborators.add(new_collab)

    project_ref.update({"collaborators": list(collaborators)})
    updated_project = project_ref.get()
    return jsonify({"message": "Collaborator added", "project": updated_project}), 200

# --- Change project owner ---
@app.route("/project/change-owner", methods=["POST"])
def change_owner():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    changeuserid = data.get("changeuserid")
    uid = data.get("uid")
    if not userid or not changeuserid or not uid:
        return jsonify(error="userid, changeuserid, and uid required"), 400

    project_ref = db.reference(f"project/{uid}")
    project = project_ref.get()
    if not project:
        return jsonify(error="Project not found"), 404

    if project.get("ownerId") != userid:
        return jsonify(error="Unauthorized: only current owner can change owner"), 403

    users_ref = db.reference("users")
    users = users_ref.get() or {}

    current_owner_role = users.get(userid, {}).get("role")
    new_owner_role = users.get(changeuserid, {}).get("role")

    if not current_owner_role or not new_owner_role:
        return jsonify(error="User roles not found in /users database"), 404

    if current_owner_role == "director":
        if new_owner_role != "manager":
            return jsonify(error="Director can only delegate ownership to a manager"), 403
    elif current_owner_role == "manager":
        if new_owner_role in ("manager", "director"):
            return jsonify(error="Manager cannot delegate ownership to manager or director"), 403
    else:
        return jsonify(error="Only director or manager can delegate ownership"), 403

    collaborators = set(project.get("collaborators", []))
    collaborators.add(changeuserid)

    project_ref.update({
        "ownerId": changeuserid,
        "collaborators": list(collaborators)
    })

    updated_project = project_ref.get()
    return jsonify({"message": "Project ownership changed", "project": updated_project}), 200

# --- Run app ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)
