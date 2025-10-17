# backend/api-gateway/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

app = Flask(__name__)

# Configure CORS to allow frontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://spm-g7-t1-td8d.vercel.app",
            "http://localhost:3000", 
            "http://localhost:3001" 
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs (from environment variables)
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL")
PROJECT_SERVICE_URL = os.getenv("PROJECT_SERVICE_URL")
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL")
SUBTASK_SERVICE_URL = os.getenv("SUBTASK_SERVICE_URL" )

# ============================================
# NOTIFICATION SERVICE ROUTES
# ============================================
@app.route("/api/notifications/<user_id>", methods=["GET"])
def get_user_notifications(user_id):
    try:
        resp = requests.get(f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/notifications/<user_id>/unread", methods=["GET"])
def get_unread_notifications(user_id):
    try:
        resp = requests.get(f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}/unread")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/notifications/<user_id>/<notification_id>/read", methods=["PATCH"])
def mark_notification_read(user_id, notification_id):
    try:
        resp = requests.patch(f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}/{notification_id}/read")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/notifications/<user_id>/<notification_id>", methods=["DELETE"])
def delete_notification(user_id, notification_id):
    try:
        resp = requests.delete(f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}/{notification_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/notifications/<user_id>/mark-all-read", methods=["PATCH"])
def mark_all_notifications_read(user_id):
    try:
        resp = requests.patch(f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}/mark-all-read")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# ============================================
# PROJECT SERVICE ROUTES
# ============================================
@app.route("/api/projects/create", methods=["POST"])
def create_project():
    try:
        resp = requests.post(f"{PROJECT_SERVICE_URL}/project/create", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/all", methods=["GET"])
def get_all_projects():
    try:
        resp = requests.get(f"{PROJECT_SERVICE_URL}/project/all")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/department/<department>", methods=["GET"])
def get_projects_by_department(department):
    try:
        resp = requests.get(f"{PROJECT_SERVICE_URL}/project/department/{department}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/<user_id>", methods=["GET"])
@app.route("/api/project/<user_id>", methods=["GET"])  # Support both singular and plural
def get_user_projects(user_id):
    try:
        resp = requests.get(f"{PROJECT_SERVICE_URL}/project/{user_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/update", methods=["POST"])
def update_project():
    try:
        resp = requests.post(f"{PROJECT_SERVICE_URL}/project/update", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/all-users", methods=["GET"])
def get_all_users():
    try:
        resp = requests.get(f"{PROJECT_SERVICE_URL}/project/all-users")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/users/available-for-collaboration/<uid>", methods=["GET"])
def get_available_users(uid):
    try:
        resp = requests.get(f"{PROJECT_SERVICE_URL}/project/users/available-for-collaboration/{uid}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/add-collaborator", methods=["POST"])
def add_collaborator():
    try:
        resp = requests.post(f"{PROJECT_SERVICE_URL}/project/add-collaborator", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects/change-owner", methods=["POST"])
def change_owner():
    try:
        resp = requests.post(f"{PROJECT_SERVICE_URL}/project/change-owner", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# ============================================
# TASK SERVICE ROUTES
# ============================================
@app.route("/api/tasks", methods=["POST"])
def create_task():
    try:
        resp = requests.post(f"{TASK_SERVICE_URL}/tasks", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/tasks", methods=["GET"])
def get_all_tasks():
    try:
        resp = requests.get(f"{TASK_SERVICE_URL}/tasks")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/tasks/<task_id>", methods=["GET"])
def get_task_by_id(task_id):
    try:
        resp = requests.get(f"{TASK_SERVICE_URL}/tasks/{task_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task_by_id(task_id):
    try:
        resp = requests.put(f"{TASK_SERVICE_URL}/tasks/{task_id}", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task_by_id(task_id):
    try:
        resp = requests.delete(f"{TASK_SERVICE_URL}/tasks/{task_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/tasks/project/<project_id>", methods=["GET"])
def get_tasks_by_project(project_id):
    try:
        resp = requests.get(f"{TASK_SERVICE_URL}/tasks/project/{project_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# ============================================
# SUBTASK SERVICE ROUTES
# ============================================
@app.route("/api/subtasks", methods=["POST"])
def create_subtask():
    try:
        resp = requests.post(f"{SUBTASK_SERVICE_URL}/subtasks", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/subtasks", methods=["GET"])
def get_all_subtasks():
    try:
        resp = requests.get(f"{SUBTASK_SERVICE_URL}/subtasks")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/subtasks/<subtask_id>", methods=["GET"])
def get_subtask_by_id(subtask_id):
    try:
        resp = requests.get(f"{SUBTASK_SERVICE_URL}/subtasks/{subtask_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/subtasks/<subtask_id>", methods=["PUT"])
def update_subtask_by_id(subtask_id):
    try:
        resp = requests.put(f"{SUBTASK_SERVICE_URL}/subtasks/{subtask_id}", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/subtasks/<subtask_id>", methods=["DELETE"])
def delete_subtask_by_id(subtask_id):
    try:
        resp = requests.delete(f"{SUBTASK_SERVICE_URL}/subtasks/{subtask_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/subtasks/task/<task_id>", methods=["GET"])
def get_subtasks_by_task(task_id):
    try:
        resp = requests.get(f"{SUBTASK_SERVICE_URL}/subtasks/task/{task_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# ============================================
# EMAIL SERVICE ROUTES
# ============================================
@app.route("/api/email/send-task-reminder", methods=["POST"])
def send_task_reminder():
    try:
        resp = requests.post(f"{EMAIL_SERVICE_URL}/email/send-task-reminder", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/email/test", methods=["POST"])
def test_email():
    try:
        resp = requests.post(f"{EMAIL_SERVICE_URL}/email/test", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# ============================================
# SCHEDULER SERVICE ROUTES
# ============================================
@app.route("/api/scheduler/trigger", methods=["POST"])
def trigger_scheduler():
    try:
        resp = requests.post(f"{NOTIFICATION_SERVICE_URL}/scheduler/trigger")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# ============================================
# HEALTH CHECK
# ============================================
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="healthy", service="api-gateway"), 200

@app.route("/api/health", methods=["GET"])
def api_health_check():
    return jsonify(status="healthy", service="api-gateway"), 200

# Handle 404 errors with CORS headers
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Endpoint not found"), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=False)