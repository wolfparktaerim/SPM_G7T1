# subtask-service/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timezone
import os

app = Flask(__name__)
CORS(app)

# Firebase configuration
JSON_PATH = os.getenv("JSON_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")

cred = credentials.Certificate(JSON_PATH)
firebase_admin.initialize_app(cred, {
    "databaseURL": DATABASE_URL
})

# Utility functions
def current_timestamp():
    """Return current timestamp in epoch format"""
    return int(datetime.now(timezone.utc).timestamp())

def validate_status(status):
    """Validate status is one of the allowed values"""
    allowed_statuses = ["ongoing", "unassigned", "under_review", "completed"]
    return status.lower() in allowed_statuses

def validate_epoch_timestamp(timestamp):
    """Validate that timestamp is a valid epoch timestamp"""
    try:
        if isinstance(timestamp, (int, float)):
            return timestamp > 0
        return False
    except (ValueError, TypeError):
        return False

@app.route("/subtasks", methods=["POST"])
def create_subtask():
    """Create a new subtask"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    # Required fields validation
    required_fields = ["title", "creatorId", "deadline", "taskId"]
    for field in required_fields:
        if not data.get(field):
            return jsonify(error=f"Missing required field: {field}"), 400

    # Validate deadline format (epoch timestamp)
    deadline = data.get("deadline")
    if not validate_epoch_timestamp(deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400

    # Validate status if provided
    status = data.get("status", "ongoing").lower()
    if not validate_status(status):
        return jsonify(error="Status must be one of: ongoing, unassigned, under_review, completed"), 400

    # Check if parent task exists
    task_id = data.get("taskId")
    try:
        parent_task_ref = db.reference(f"tasks/{task_id}")
        parent_task = parent_task_ref.get()
        if not parent_task:
            return jsonify(error="Parent task not found"), 404
    except Exception as e:
        return jsonify(error=f"Failed to validate parent task: {str(e)}"), 500

    # Extract and validate data
    title = data.get("title").strip()
    if not title:
        return jsonify(error="Title cannot be empty"), 400

    creator_id = data.get("creatorId")
    owner_id = data.get("ownerId", creator_id)  # Default to creator if not specified
    notes = data.get("notes", "")
    attachments = data.get("attachments", [])
    collaborators = data.get("collaborators", [])

    # Validate attachments are strings (base64)
    if not isinstance(attachments, list) or not all(isinstance(att, str) for att in attachments):
        return jsonify(error="Attachments must be an array of strings (base64)"), 400

    # Validate collaborators are strings (user IDs)
    if not isinstance(collaborators, list) or not all(isinstance(collab, str) for collab in collaborators):
        return jsonify(error="Collaborators must be an array of user IDs"), 400

    # Generate subtask reference and get auto-generated ID
    subtasks_ref = db.reference("subtasks")
    new_subtask_ref = subtasks_ref.push()
    subtask_id = new_subtask_ref.key

    # Prepare subtask data
    current_time = current_timestamp()
    subtask_data = {
        "subTaskId": subtask_id,
        "title": title,
        "creatorId": creator_id,
        "deadline": deadline,
        "status": status,
        "notes": notes,
        "attachments": attachments,
        "collaborators": collaborators,
        "taskId": task_id,
        "ownerId": owner_id,
        "createdAt": current_time,
        "updatedAt": current_time
    }

    # Save to Firebase
    try:
        new_subtask_ref.set(subtask_data)
        return jsonify(message="Subtask created successfully", subtask=subtask_data), 201
    except Exception as e:
        return jsonify(error=f"Failed to create subtask: {str(e)}"), 500

@app.route("/subtasks", methods=["GET"])
def get_all_subtasks():
    """Get all subtasks"""
    try:
        subtasks_ref = db.reference("subtasks")
        all_subtasks = subtasks_ref.get() or {}
        
        # Convert to list format
        subtasks_list = list(all_subtasks.values()) if all_subtasks else []
        
        return jsonify(subtasks=subtasks_list), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve subtasks: {str(e)}"), 500

@app.route("/subtasks/<subtask_id>", methods=["GET"])
def get_subtask_by_id(subtask_id):
    """Get a subtask by ID"""
    try:
        subtask_ref = db.reference(f"subtasks/{subtask_id}")
        subtask = subtask_ref.get()
        
        if not subtask:
            return jsonify(error="Subtask not found"), 404
            
        return jsonify(subtask=subtask), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve subtask: {str(e)}"), 500

@app.route("/subtasks/<subtask_id>", methods=["PUT"])
def update_subtask_by_id(subtask_id):
    """Update a subtask by ID"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    try:
        # Check if subtask exists
        subtask_ref = db.reference(f"subtasks/{subtask_id}")
        existing_subtask = subtask_ref.get()
        
        if not existing_subtask:
            return jsonify(error="Subtask not found"), 404

        # Prepare update data (only include provided fields)
        update_data = {}
        
        # Validate and update title if provided
        if "title" in data:
            title = data["title"].strip()
            if not title:
                return jsonify(error="Title cannot be empty"), 400
            update_data["title"] = title

        # Validate and update deadline if provided
        if "deadline" in data:
            deadline = data["deadline"]
            if not validate_epoch_timestamp(deadline):
                return jsonify(error="Deadline must be a valid epoch timestamp"), 400
            update_data["deadline"] = deadline

        # Validate and update status if provided
        if "status" in data:
            status = data["status"].lower()
            if not validate_status(status):
                return jsonify(error="Status must be one of: ongoing, unassigned, under_review, completed"), 400
            update_data["status"] = status

        # Validate taskId if provided (check if parent task exists)
        if "taskId" in data:
            task_id = data["taskId"]
            parent_task_ref = db.reference(f"tasks/{task_id}")
            parent_task = parent_task_ref.get()
            if not parent_task:
                return jsonify(error="Parent task not found"), 404
            update_data["taskId"] = task_id

        # Update other optional fields if provided
        if "notes" in data:
            update_data["notes"] = data["notes"]
            
        if "attachments" in data:
            attachments = data["attachments"]
            if not isinstance(attachments, list) or not all(isinstance(att, str) for att in attachments):
                return jsonify(error="Attachments must be an array of strings (base64)"), 400
            update_data["attachments"] = attachments
            
        if "collaborators" in data:
            collaborators = data["collaborators"]
            if not isinstance(collaborators, list) or not all(isinstance(collab, str) for collab in collaborators):
                return jsonify(error="Collaborators must be an array of user IDs"), 400
            update_data["collaborators"] = collaborators
            
        if "ownerId" in data:
            update_data["ownerId"] = data["ownerId"]

        # Always update the updatedAt timestamp
        update_data["updatedAt"] = current_timestamp()

        if not update_data or len(update_data) == 1:  # Only updatedAt
            return jsonify(error="No valid fields provided for update"), 400

        # Perform update
        subtask_ref.update(update_data)
        
        # Get updated subtask
        updated_subtask = subtask_ref.get()
        return jsonify(message="Subtask updated successfully", subtask=updated_subtask), 200
        
    except Exception as e:
        return jsonify(error=f"Failed to update subtask: {str(e)}"), 500

@app.route("/subtasks/<subtask_id>", methods=["DELETE"])
def delete_subtask_by_id(subtask_id):
    """Delete a subtask by ID"""
    try:
        # Check if subtask exists
        subtask_ref = db.reference(f"subtasks/{subtask_id}")
        existing_subtask = subtask_ref.get()
        
        if not existing_subtask:
            return jsonify(error="Subtask not found"), 404

        # Delete the subtask
        subtask_ref.delete()
        
        return jsonify(message="Subtask deleted successfully"), 200
        
    except Exception as e:
        return jsonify(error=f"Failed to delete subtask: {str(e)}"), 500

@app.route("/subtasks/task/<task_id>", methods=["GET"])
def get_subtasks_by_task(task_id):
    """Get all subtasks by task ID"""
    try:
        subtasks_ref = db.reference("subtasks")
        all_subtasks = subtasks_ref.get() or {}
        
        # Filter subtasks by task ID
        filtered_subtasks = [
            subtask for subtask in all_subtasks.values() 
            if subtask.get("taskId") == task_id
        ]
        
        return jsonify(subtasks=filtered_subtasks), 200
        
    except Exception as e:
        return jsonify(error=f"Failed to retrieve subtasks by task: {str(e)}"), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="subtask-service"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6003, debug=True)