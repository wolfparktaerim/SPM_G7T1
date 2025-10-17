# backend/api-gateway/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs (from environment variables)
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://email-service:6005")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:6004")
PROJECT_SERVICE_URL = os.getenv("PROJECT_SERVICE_URL", "http://project-service:6001")
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://task-service:6002")
SUBTASK_SERVICE_URL = os.getenv("SUBTASK_SERVICE_URL", "http://sub-task-service:6003")

# Notification Service Routes
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

# Project Service Routes (template - add all your routes)
@app.route("/api/projects/<user_id>", methods=["GET"])
def get_user_projects(user_id):
    try:
        resp = requests.get(f"{PROJECT_SERVICE_URL}/projects/{user_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/projects", methods=["POST"])
def create_project():
    try:
        resp = requests.post(f"{PROJECT_SERVICE_URL}/projects", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# Task Service Routes (template)
@app.route("/api/tasks/<project_id>", methods=["GET"])
def get_project_tasks(project_id):
    try:
        resp = requests.get(f"{TASK_SERVICE_URL}/tasks/{project_id}")
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/tasks", methods=["POST"])
def create_task():
    try:
        resp = requests.post(f"{TASK_SERVICE_URL}/tasks", json=request.json)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

# Add similar routes for subtasks and other services...

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="healthy", service="api-gateway"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000, debug=False)