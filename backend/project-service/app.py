# backend/project-service/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import init_firebase

from project_service import ProjectService
from models import CreateProjectRequest, UpdateProjectRequest

app = Flask(__name__)
CORS(app)

# Initialize Firebase
init_firebase()

# Initialize service
project_service = ProjectService()

@app.route("/project/create", methods=["POST"])
def create_project():
    """Create a new project"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = CreateProjectRequest.from_dict(data)
    errors = req.validate()
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    project, error = project_service.create_project(req)
    if error:
        return jsonify(error=error), 404 if "not found" in error else 400
    
    return jsonify(message="Project created", project=project.to_dict()), 201

@app.route("/project/all", methods=["GET"])
def get_all_projects():
    """Get all projects"""
    projects = project_service.get_all_projects()
    return jsonify(projects=[p.to_dict() for p in projects]), 200

@app.route("/project/department/<department>", methods=["GET"])
def get_projects_by_department(department):
    """Get projects by department"""
    projects = project_service.get_projects_by_department(department)
    return jsonify(projects=[p.to_dict() for p in projects]), 200

@app.route("/project/<userid>", methods=["GET"])
def get_user_projects(userid):
    """Get projects for a user"""
    projects = project_service.get_user_projects(userid)
    return jsonify(projects=[p.to_dict() for p in projects]), 200

@app.route("/project/update", methods=["POST"])
def update_project():
    """Update a project"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = UpdateProjectRequest.from_dict(data)
    errors = req.validate()
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    project, error = project_service.update_project(req)
    if error:
        code = 404 if "not found" in error else 403 if "owner" in error or "role" in error else 400
        return jsonify(error=error), code
    
    return jsonify(success=True, updatedProject=project.to_dict()), 200

@app.route("/project/all-users", methods=["GET"])
def get_all_users():
    """Get all users"""
    users = project_service.get_all_users()
    return jsonify(users=users), 200

@app.route("/project/users/available-for-collaboration/<uid>", methods=["GET"])
def get_available_users(uid):
    """Get users available for collaboration on a project"""
    users, error = project_service.get_available_users_for_collaboration(uid)
    if error:
        return jsonify(error=error), 404
    
    return jsonify(availableUsers=users), 200

@app.route("/project/add-collaborator", methods=["POST"])
def add_collaborator():
    """Add collaborators to a project"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    userid = data.get("userid")
    adduserid = data.get("adduserid")
    uid = data.get("uid")
    
    if not userid or not adduserid or not uid:
        return jsonify(error="userid, adduserid and uid required"), 400
    
    project, error = project_service.add_collaborators(userid, uid, adduserid)
    if error:
        code = 404 if "not found" in error else 403
        return jsonify(error=error), code
    
    return jsonify(message="Collaborator added", project=project.to_dict()), 200

@app.route("/project/change-owner", methods=["POST"])
def change_owner():
    """Change project owner"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    userid = data.get("userid")
    changeuserid = data.get("changeuserid")
    uid = data.get("uid")
    
    if not userid or not changeuserid or not uid:
        return jsonify(error="userid, changeuserid, and uid required"), 400
    
    project, error = project_service.change_owner(userid, uid, changeuserid)
    if error:
        code = 404 if "not found" in error else 403
        return jsonify(error=error), code
    
    return jsonify(message="Project ownership changed", project=project.to_dict()), 200

@app.route("/project/archive", methods=["POST"])
def archive_project():
    """Archive a project"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    userid = data.get("userid")
    project_id = data.get("projectId")
    
    if not userid or not project_id:
        return jsonify(error="userid and projectId required"), 400
    
    project, error = project_service.archive_project(userid, project_id)
    if error:
        code = 404 if "not found" in error else 403
        return jsonify(error=error), code
    
    return jsonify(message="Project archived successfully", project=project.to_dict()), 200

@app.route("/project/unarchive", methods=["POST"])
def unarchive_project():
    """Unarchive a project"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    userid = data.get("userid")
    project_id = data.get("projectId")
    
    if not userid or not project_id:
        return jsonify(error="userid and projectId required"), 400
    
    project, error = project_service.unarchive_project(userid, project_id)
    if error:
        code = 404 if "not found" in error else 403
        return jsonify(error=error), code
    
    return jsonify(message="Project unarchived successfully", project=project.to_dict()), 200

@app.route("/project/archived/<userid>", methods=["GET"])
def get_archived_projects(userid):
    """Get archived projects for a user"""
    projects = project_service.get_archived_projects(userid)
    return jsonify(projects=[p.to_dict() for p in projects]), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="project-service"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)