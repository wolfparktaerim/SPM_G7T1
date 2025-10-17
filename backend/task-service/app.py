# backend/task-service/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import init_firebase, validate_epoch_timestamp

from task_service import TaskService
from models import CreateTaskRequest, UpdateTaskRequest

app = Flask(__name__)

# Configure CORS to allow rontend
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

# Initialize Firebase
init_firebase()

# Initialize service
task_service = TaskService()

@app.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = CreateTaskRequest.from_dict(data)
    errors = req.validate()
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    # Additional validations
    if not validate_epoch_timestamp(req.deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400
    
    if req.start_date and not validate_epoch_timestamp(req.start_date):
        return jsonify(error="start_date must be a valid epoch timestamp"), 400
    
    if not isinstance(req.attachments, list) or not all(isinstance(att, str) for att in req.attachments):
        return jsonify(error="Attachments must be an array of strings"), 400
    
    if not isinstance(req.collaborators, list) or not all(isinstance(collab, str) for collab in req.collaborators):
        return jsonify(error="Collaborators must be an array of user IDs"), 400
    
    if req.schedule not in ["daily", "weekly", "monthly", "custom"]:
        return jsonify(error="Schedule must be one of: daily, weekly, monthly, custom"), 400
    
    task, error = task_service.create_task(req)
    if error:
        return jsonify(error=error), 400
    
    return jsonify(message="Task created successfully", task=task.to_dict()), 201

@app.route("/tasks", methods=["GET"])
def get_all_tasks():
    """Get all active tasks"""
    tasks = task_service.get_all_tasks()
    return jsonify(tasks=[t.to_dict() for t in tasks]), 200

@app.route("/tasks/<task_id>", methods=["GET"])
def get_task_by_id(task_id):
    """Get a task by ID"""
    task, error = task_service.get_task_by_id(task_id)
    if error:
        return jsonify(error=error), 404
    
    return jsonify(task=task.to_dict()), 200

@app.route("/tasks/<task_id>", methods=["PUT"])
def update_task_by_id(task_id):
    """Update a task by ID"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = UpdateTaskRequest.from_dict(data, task_id)
    
    # Additional validations
    if req.title is not None and not req.title.strip():
        return jsonify(error="Title cannot be empty"), 400
    
    if req.deadline is not None and not validate_epoch_timestamp(req.deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400
    
    if req.start_date is not None and not validate_epoch_timestamp(req.start_date):
        return jsonify(error="start_date must be a valid epoch timestamp"), 400
    
    if req.priority is not None and not isinstance(req.priority, int):
        return jsonify(error="Priority must be an integer"), 400
    
    if req.attachments is not None:
        if not isinstance(req.attachments, list) or not all(isinstance(att, str) for att in req.attachments):
            return jsonify(error="Attachments must be an array of strings"), 400
    
    if req.collaborators is not None:
        if not isinstance(req.collaborators, list) or not all(isinstance(collab, str) for collab in req.collaborators):
            return jsonify(error="Collaborators must be an array of user IDs"), 400
    
    if req.schedule is not None:
        if req.schedule not in ["daily", "weekly", "monthly", "custom"]:
            return jsonify(error="Schedule must be one of: daily, weekly, monthly, custom"), 400
    
    task, error = task_service.update_task(req)
    if error:
        return jsonify(error=error), 400
    
    return jsonify(message="Task updated successfully", task=task.to_dict()), 200

@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task_by_id(task_id):
    """Delete a task by ID"""
    success, error = task_service.delete_task(task_id)
    if error:
        return jsonify(error=error), 404
    
    return jsonify(message="Task deleted successfully"), 200

@app.route("/tasks/project/<project_id>", methods=["GET"])
def get_tasks_by_project(project_id):
    """Get all active tasks by project ID"""
    tasks = task_service.get_tasks_by_project(project_id)
    return jsonify(tasks=[t.to_dict() for t in tasks]), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="task-service"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002, debug=True)