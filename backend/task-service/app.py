# task-service/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timezone
import os
import time
import json 

app = Flask(__name__)
CORS(app)

print("🚀 Starting Task Service...")

# Firebase configuration - Updated for Railway with FULL DEBUG
def initialize_firebase():
    print("=== FIREBASE INITIALIZATION START ===")
    
    # Check if Firebase is already initialized
    if firebase_admin._apps:
        print(f"✅ Firebase already initialized. Apps: {list(firebase_admin._apps.keys())}")
        return True
    
    print("🔄 No Firebase apps found, initializing...")
    
    try:
        # Check environment variables
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
        database_url = os.getenv("DATABASE_URL")
        
        print(f"📊 Environment Variables Check:")
        print(f"   DATABASE_URL exists: {database_url is not None}")
        if database_url:
            print(f"   DATABASE_URL: {database_url}")
        else:
            print("   ❌ DATABASE_URL is missing!")
            
        print(f"   FIREBASE_CREDENTIALS exists: {firebase_creds is not None}")
        
        if firebase_creds:
            print(f"   FIREBASE_CREDENTIALS length: {len(firebase_creds)}")
            print(f"   FIREBASE_CREDENTIALS starts with: {firebase_creds[:50]}...")
            print(f"   FIREBASE_CREDENTIALS ends with: ...{firebase_creds[-50:]}")
        else:
            print("   ❌ FIREBASE_CREDENTIALS is missing!")
            return False
        
        if not database_url:
            print("❌ DATABASE_URL environment variable is required")
            return False
            
        # Try to parse JSON
        print("🔄 Parsing Firebase credentials JSON...")
        try:
            cred_dict = json.loads(firebase_creds)
            print(f"✅ JSON parsed successfully!")
            print(f"   Project ID: {cred_dict.get('project_id', 'N/A')}")
            print(f"   Client Email: {cred_dict.get('client_email', 'N/A')}")
            print(f"   Type: {cred_dict.get('type', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"   Problematic JSON (first 200 chars): {firebase_creds[:200]}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error parsing JSON: {e}")
            return False
        
        # Try to create credentials
        print("🔄 Creating Firebase credentials object...")
        try:
            cred = credentials.Certificate(cred_dict)
            print("✅ Firebase credentials object created successfully")
        except Exception as e:
            print(f"❌ Failed to create credentials object: {e}")
            return False
        
        # Try to initialize Firebase
        print("🔄 Initializing Firebase app...")
        try:
            firebase_admin.initialize_app(cred, {
                "databaseURL": database_url
            })
            print("✅ Firebase app initialized successfully!")
        except Exception as e:
            print(f"❌ Firebase app initialization failed: {e}")
            return False
        
        # Verify initialization
        if firebase_admin._apps:
            print(f"✅ Verification: Firebase apps now available: {list(firebase_admin._apps.keys())}")
            print("=== FIREBASE INITIALIZATION SUCCESS ===")
            return True
        else:
            print("❌ Verification failed: No Firebase apps found after initialization")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR during Firebase initialization: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return False

# Initialize Firebase and track success
print("🔄 Calling initialize_firebase()...")
firebase_init_success = initialize_firebase()
print(f"🎯 Firebase initialization result: {firebase_init_success}")

if not firebase_init_success:
    print("🚨 WARNING: Firebase initialization failed! Service will start but database operations will fail.")

    
# Utility functions
def current_timestamp():
    """Return current timestamp in epoch format"""
    return int(datetime.now(timezone.utc).timestamp())

def validate_status(status):
    """Validate status is one of the allowed values"""
    allowed_statuses = ["Ongoing", "Unassigned", "Under Review", "Completed"]
    return status.lower() in allowed_statuses

def validate_epoch_timestamp(timestamp):
    """Validate that timestamp is a valid epoch timestamp"""
    try:
        if isinstance(timestamp, (int, float)):
            return timestamp > 0
        return False
    except (ValueError, TypeError):
        return False

@app.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    # Required fields validation
    required_fields = ["title", "creatorId", "deadline"]
    for field in required_fields:
        if not data.get(field):
            return jsonify(error=f"Missing required field: {field}"), 400

    # Validate deadline format (epoch timestamp)
    deadline = data.get("deadline")
    if not validate_epoch_timestamp(deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400

    # Validate status if provided
    status = data.get("status", "ongoing").lower()
    # if not validate_status(status):
    #     return jsonify(error="Status must be one of: Ongoing, Unassigned, Under Review, Completed"), 400

    # Extract and validate data
    title = data.get("title").strip()
    if not title:
        return jsonify(error="Title cannot be empty"), 400

    creator_id = data.get("creatorId")
    owner_id = data.get("ownerId", creator_id)  # Default to creator if not specified
    notes = data.get("notes", "")
    attachments = data.get("attachments", [])
    collaborators = data.get("collaborators", [])
    project_id = data.get("projectId", "")

    # Validate attachments are strings (base64)
    if not isinstance(attachments, list) or not all(isinstance(att, str) for att in attachments):
        return jsonify(error="Attachments must be an array of strings (base64)"), 400

    # Validate collaborators are strings (user IDs)
    if not isinstance(collaborators, list) or not all(isinstance(collab, str) for collab in collaborators):
        return jsonify(error="Collaborators must be an array of user IDs"), 400

    # Generate task reference and get auto-generated ID
    tasks_ref = db.reference("tasks")
    new_task_ref = tasks_ref.push()
    task_id = new_task_ref.key

    # Prepare task data
    current_time = current_timestamp()
    task_data = {
        "taskId": task_id,
        "title": title,
        "creatorId": creator_id,
        "deadline": deadline,
        "status": status,
        "notes": notes,
        "attachments": attachments,
        "collaborators": collaborators,
        "projectId": project_id,
        "ownerId": owner_id,
        "createdAt": current_time,
        "updatedAt": current_time
    }

    # Save to Firebase
    try:
        new_task_ref.set(task_data)
        return jsonify(message="Task created successfully", task=task_data), 201
    except Exception as e:
        return jsonify(error=f"Failed to create task: {str(e)}"), 500

@app.route("/tasks", methods=["GET"])
def get_all_tasks():
    """Get all tasks"""
    try:
        tasks_ref = db.reference("tasks")
        all_tasks = tasks_ref.get() or {}
        
        # Convert to list format
        tasks_list = list(all_tasks.values()) if all_tasks else []
        
        return jsonify(tasks=tasks_list), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve tasks: {str(e)}"), 500

@app.route("/tasks/<task_id>", methods=["GET"])
def get_task_by_id(task_id):
    """Get a task by ID"""
    try:
        task_ref = db.reference(f"tasks/{task_id}")
        task = task_ref.get()
        
        if not task:
            return jsonify(error="Task not found"), 404
            
        return jsonify(task=task), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve task: {str(e)}"), 500

@app.route("/tasks/<task_id>", methods=["PUT"])
def update_task_by_id(task_id):
    """Update a task by ID"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    try:
        # Check if task exists
        task_ref = db.reference(f"tasks/{task_id}")
        existing_task = task_ref.get()
        
        if not existing_task:
            return jsonify(error="Task not found"), 404

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
            # if not validate_status(status):
            #     return jsonify(error="Status must be one of: ongoing, unassigned, under_review, completed"), 400
            update_data["status"] = status

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
            
        if "projectId" in data:
            update_data["projectId"] = data["projectId"]
            
        if "ownerId" in data:
            update_data["ownerId"] = data["ownerId"]

        # Always update the updatedAt timestamp
        update_data["updatedAt"] = current_timestamp()

        if not update_data or len(update_data) == 1:  # Only updatedAt
            return jsonify(error="No valid fields provided for update"), 400

        # Perform update
        task_ref.update(update_data)
        
        # Get updated task
        updated_task = task_ref.get()
        return jsonify(message="Task updated successfully", task=updated_task), 200
        
    except Exception as e:
        return jsonify(error=f"Failed to update task: {str(e)}"), 500

@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task_by_id(task_id):
    """Delete a task by ID"""
    try:
        # Check if task exists
        task_ref = db.reference(f"tasks/{task_id}")
        existing_task = task_ref.get()
        
        if not existing_task:
            return jsonify(error="Task not found"), 404

        # Delete the task
        task_ref.delete()
        
        return jsonify(message="Task deleted successfully"), 200
        
    except Exception as e:
        return jsonify(error=f"Failed to delete task: {str(e)}"), 500

@app.route("/tasks/project/<project_id>", methods=["GET"])
def get_tasks_by_project(project_id):
    """Get all tasks by project ID"""
    try:
        tasks_ref = db.reference("tasks")
        all_tasks = tasks_ref.get() or {}
        
        # Filter tasks by project ID
        filtered_tasks = [
            task for task in all_tasks.values() 
            if task.get("projectId") == project_id
        ]
        
        return jsonify(tasks=filtered_tasks), 200
        
    except Exception as e:
        return jsonify(error=f"Failed to retrieve tasks by project: {str(e)}"), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="task-service"), 200

# Update the main run block at the end
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6002))
    app.run(host='0.0.0.0', port=port, debug=False)