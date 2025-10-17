# backend/subtask-service/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import init_firebase, validate_epoch_timestamp

from subtask_service import SubtaskService
from models import CreateSubtaskRequest, UpdateSubtaskRequest

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
subtask_service = SubtaskService()

@app.route("/subtasks", methods=["POST"])
def create_subtask():
    """Create a new subtask"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = CreateSubtaskRequest.from_dict(data)
    errors = req.validate()
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    if not validate_epoch_timestamp(req.deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400
    
    if req.start_date and not validate_epoch_timestamp(req.start_date):
        return jsonify(error="start_date must be a valid epoch timestamp"), 400
    
    if not subtask_service.validate_status(req.status):
        return jsonify(error="Status must be one of: ongoing, unassigned, under_review, completed"), 400
    
    if req.schedule not in ["daily", "weekly", "monthly", "custom"]:
        return jsonify(error="Schedule must be one of: daily, weekly, monthly, custom"), 400
    
    subtask, error = subtask_service.create_subtask(req)
    if error:
        return jsonify(error=error), 404 if "not found" in error else 400
    
    return jsonify(message="Subtask created successfully", subtask=subtask.to_dict()), 201

@app.route("/subtasks", methods=["GET"])
def get_all_subtasks():
    """Get all subtasks"""
    subtasks = subtask_service.get_all_subtasks()
    return jsonify(subtasks=[s.to_dict() for s in subtasks]), 200

@app.route("/subtasks/<subtask_id>", methods=["GET"])
def get_subtask_by_id(subtask_id):
    """Get a subtask by ID"""
    subtask, error = subtask_service.get_subtask_by_id(subtask_id)
    if error:
        return jsonify(error=error), 404
    
    return jsonify(subtask=subtask.to_dict()), 200

@app.route("/subtasks/<subtask_id>", methods=["PUT"])
def update_subtask_by_id(subtask_id):
    """Update a subtask by ID"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    req = UpdateSubtaskRequest.from_dict(data, subtask_id)
    
    if req.deadline is not None and not validate_epoch_timestamp(req.deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400
    
    if req.start_date is not None and not validate_epoch_timestamp(req.start_date):
        return jsonify(error="start_date must be a valid epoch timestamp"), 400
    
    if req.status is not None and not subtask_service.validate_status(req.status):
        return jsonify(error="Status must be one of: ongoing, unassigned, under_review, completed"), 400
    
    if req.schedule is not None and req.schedule not in ["daily", "weekly", "monthly", "custom"]:
        return jsonify(error="Schedule must be one of: daily, weekly, monthly, custom"), 400
    
    subtask, error = subtask_service.update_subtask(req)
    if error:
        return jsonify(error=error), 404 if "not found" in error else 400
    
    return jsonify(message="Subtask updated successfully", subtask=subtask.to_dict()), 200

@app.route("/subtasks/<subtask_id>", methods=["DELETE"])
def delete_subtask_by_id(subtask_id):
    """Delete a subtask by ID"""
    success, error = subtask_service.delete_subtask(subtask_id)
    if error:
        return jsonify(error=error), 404
    
    return jsonify(message="Subtask deleted successfully"), 200

@app.route("/subtasks/task/<task_id>", methods=["GET"])
def get_subtasks_by_task(task_id):
    """Get all subtasks by task ID"""
    subtasks = subtask_service.get_subtasks_by_task(task_id)
    return jsonify(subtasks=[s.to_dict() for s in subtasks]), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="subtask-service"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6003, debug=True)

# ===================================================
# backend/subtask-service/test_subtask.py
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from subtask_service import SubtaskService
from models import Subtask, CreateSubtaskRequest

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    with patch('subtask_service.get_db_reference') as mock:
        yield mock

class TestSubtaskModels:
    def test_subtask_from_dict(self):
        data = {
            "subTaskId": "st1",
            "title": "Test Subtask",
            "creatorId": "u1",
            "deadline": 1700000000,
            "status": "ongoing",
            "notes": "",
            "attachments": [],
            "collaborators": [],
            "taskId": "t1",
            "ownerId": "u1",
            "priority": 0,
            "createdAt": 1600000000,
            "updatedAt": 1600000000,
            "start_date": 1600000000,
            "active": True,
            "scheduled": False,
            "schedule": "daily"
        }
        subtask = Subtask.from_dict(data)
        assert subtask.subtask_id == "st1"
        assert subtask.title == "Test Subtask"

class TestSubtaskService:
    def test_create_subtask(self, mock_db):
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_tasks.child.return_value.get.return_value = {"taskId": "t1"}
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        service = SubtaskService()
        req = CreateSubtaskRequest(
            title="Test Subtask",
            creator_id="u1",
            deadline=1700000000,
            task_id="t1"
        )
        
        subtask, error = service.create_subtask(req)
        assert error is None
        assert subtask.title == "Test Subtask"

class TestSubtaskEndpoints:
    def test_health_check(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'healthy'
    
    @patch('app.subtask_service.get_all_subtasks')
    def test_get_all_subtasks(self, mock_get, client):
        mock_get.return_value = []
        response = client.get('/subtasks')
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])