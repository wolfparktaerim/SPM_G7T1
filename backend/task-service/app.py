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

# Role helpers
def is_manager_or_director(role):
    return role in ("manager", "director")

def is_staff(role):
    return role == "staff"

# Timestamp helper
def current_timestamp():
    return datetime.now(timezone.utc).isoformat()

# Determine initial status based on role and ownership
def determine_initial_status(role, owner_provided):
    # If created/assigned to staff or self, status "Ongoing"
    # If created by manager/director and no owner assigned, "Unassigned"
    if owner_provided:
        if role in ("manager", "director"):
            # owner assigned by manager/director means ongoing for assignee
            return "Ongoing"
        else:
            # staff created task for self or assigned others => ongoing
            return "Ongoing"
    else:
        if role == "manager":
            return "Unassigned"
        else:
            # staff creating task for self without owner (should not happen normally)
            return "Ongoing"
        
@app.route("/task/create", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    role = data.get("role")
    title = data.get("title")
    deadline = data.get("deadline")
    status = data.get("status")
    ownerUid = data.get("ownerUid")  # optional owner, only managers/directors can assign others as owner on create
    collaborators = data.get("collaborators", [])
    notes = data.get("notes", "")
    attachments = data.get("attachments", [])
    project = data.get("project", "")

    # Required fields check
    if not userid or not role:
        return jsonify(error="Missing userid or role"), 400
    if not title or not deadline:
        return jsonify(error="Missing required fields: title and deadline"), 400

    # Validate owner ownership assignment
    # Managers/directors may assign tasks to others as owner,
    # Staff are owner and collaborator by default themselves
    if ownerUid:
        # Only managers/directors can assign others as owner
        if role not in ("manager", "director"):
            return jsonify(error="Only managers/directors can assign another owner on task creation"), 403
    else:
        # No owner given means the creator is owner by default
        ownerUid = userid

    # Set collaborators, ensure owner and creator are included
    collaborators_set = set(collaborators)
    collaborators_set.add(userid)
    collaborators_set.add(ownerUid)

    # Determine status: forced by acceptance criteria
    # If user creates for self or assigned owner to staff, status ongoing
    # If manager creates and no owner assigned => Unassigned
    initial_status = determine_initial_status(role, owner_provided=ownerUid != userid)
    # Overwrite status if provided in body but only accept "Ongoing" or "Unassigned" based on logic
    if status and status in ("Ongoing", "Unassigned", "Under Review", "Completed"):
        # For creation enforce status to initial_status ignoring user provided? 
        # As per acceptance, new tasks appear immediately as Ongoing (assigned staff) or Unassigned (manager no owner)
        # So override status forcibly:
        status = initial_status
    else:
        status = initial_status

    # Generate unique task ID and save under "tasks" node
    tasks_ref = db.reference("tasks")
    new_task_ref = tasks_ref.push()
    task_uid = new_task_ref.key

    task_data = {
        "uid": task_uid,
        "title": title,
        "deadline": deadline,
        "status": status,
        "ownerUid": ownerUid,
        "collaborators": list(collaborators_set),
        "project": project,
        "notes": notes,
        "attachments": attachments,
        "creationDate": current_timestamp(),
        "subtasks": {}  # subtasks nested here by uid
    }

    # Save to Firebase
    try:
        new_task_ref.set(task_data)
    except Exception as e:
        return jsonify(error=f"Failed to create task: {str(e)}"), 500

    return jsonify(message="Task created", task=task_data), 201


@app.route("/subtask/create", methods=["POST"])
def create_subtask():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    role = data.get("role")
    taskId = data.get("taskId")  # parent task ID to link this subtask
    title = data.get("title")
    deadline = data.get("deadline")
    status = data.get("status")
    owner = data.get("owner")  # optional owner, only manager/director can assign others at create
    collaborators = data.get("collaborators", [])
    notes = data.get("notes", "")
    attachments = data.get("attachments", [])
    comments = []  # initially empty comments list

    # Required fields validation
    if not userid or not role:
        return jsonify(error="Missing userid or role"), 400
    if not taskId:
        return jsonify(error="Missing taskId for linking subtask"), 400
    if not title or not deadline:
        return jsonify(error="Missing required fields: title and deadline"), 400

    # Owner assignment rules
    if owner:
        if role not in ("manager", "director"):
            return jsonify(error="Only managers/directors can assign a different owner on subtask creation"), 403
    else:
        owner = userid

    # Verify parent task exists
    task_ref = db.reference(f"tasks/{taskId}")
    task = task_ref.get()
    if not task:
        return jsonify(error="Parent task not found"), 404

    # Build unique subtask ID key by pushing a new node
    subtask_ref = db.reference("subtask")
    new_subtask_ref = subtask_ref.push()
    subtaskId = new_subtask_ref.key

    # Ensure collaborators include creator and owner
    collaborators_set = set(collaborators)
    collaborators_set.add(userid)
    collaborators_set.add(owner)



    initial_status = determine_initial_status(role, owner_provided=owner != userid)
    if status in ("Ongoing", "Unassigned", "Under Review", "Completed"):
        status = initial_status
    else:
        status = initial_status

    # Compose subtask data as required
    subtask_data = {
        "subtaskId": subtaskId,
        "title": title,
        "owner": owner,
        "collaborators": list(collaborators_set),
        "notes": notes,
        "attachments": attachments,
        "taskId": taskId,
        "status": status,
        "deadline": deadline,
        "creationDate": datetime.now(timezone.utc).isoformat(),
        "comments": comments
    }

    try:
        new_subtask_ref.set(subtask_data)
    except Exception as e:
        return jsonify(error=f"Failed to create subtask: {str(e)}"), 500

    return jsonify(message="Subtask created", subtask=subtask_data), 201

@app.route("/task/<projectid>", methods=["GET"])
def get_tasks_by_project(projectid):
    tasks_ref = db.reference("tasks")
    all_tasks = tasks_ref.get() or {}

    # Filter tasks where project matches projectid
    filtered_tasks = [
        task for task in all_tasks.values() if task.get("project") == projectid
    ]

    return jsonify({"tasks": filtered_tasks}), 200


@app.route("/subtask/<taskid>", methods=["GET"])
def get_subtasks_by_task(taskid):
    subtasks_ref = db.reference("subtask")
    all_subtasks = subtasks_ref.get() or {}

    # Filter subtasks where taskId matches taskid
    filtered_subtasks = [
        subtask for subtask in all_subtasks.values() if subtask.get("taskId") == taskid
    ]

    return jsonify({"subtasks": filtered_subtasks}), 200
@app.route("/task/update", methods=["POST"])
def update_task():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    role = data.get("role")
    uid = data.get("uid")  # task ID
    if not userid or not role or not uid:
        return jsonify(error="userid, role, and uid required"), 400

    # Allowed fields to update for tasks
    allowed_fields = {"title", "deadline", "status", "notes", "attachments", "ownerUid", "collaborators", "project"}

    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return jsonify(error=f"At least one updatable field required: {', '.join(allowed_fields)}"), 400

    # Validate required fields if being updated
    if "title" in update_data and not update_data["title"]:
        return jsonify(error="Title cannot be empty"), 400
    if "deadline" in update_data and not update_data["deadline"]:
        return jsonify(error="Deadline cannot be empty"), 400

    task_ref = db.reference(f"tasks/{uid}")
    task = task_ref.get()

    if not task:
        return jsonify(error="Task not found"), 404

    # Only owner can update
    if task.get("ownerUid") != userid:
        return jsonify(error="Unauthorized: only owner can update task"), 403

    # Owner field update validation: only managers/directors allowed
    if "ownerUid" in update_data:
        if role not in ("manager", "director"):
            return jsonify(error="Only managers/directors can change task owner"), 403

    # Update task data
    try:
        task_ref.update(update_data)
    except Exception as e:
        return jsonify(error=f"Failed to update task: {str(e)}"), 500

    updated_task = task_ref.get()
    return jsonify(message="Task updated", task=updated_task), 200


@app.route("/subtask/update", methods=["POST"])
def update_subtask():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    role = data.get("role")
    subtaskId = data.get("subtaskId")
    if not userid or not role or not subtaskId:
        return jsonify(error="userid, role, and subtaskId required"), 400

    # Allowed fields to update for subtasks (no project field)
    allowed_fields = {"title", "deadline", "status", "notes", "attachments", "owner", "collaborators"}

    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return jsonify(error=f"At least one updatable field required: {', '.join(allowed_fields)}"), 400

    # Validate required fields if being updated
    if "title" in update_data and not update_data["title"]:
        return jsonify(error="Title cannot be empty"), 400
    if "deadline" in update_data and not update_data["deadline"]:
        return jsonify(error="Deadline cannot be empty"), 400

    subtask_ref = db.reference(f"subtask/{subtaskId}")
    subtask = subtask_ref.get()
    if not subtask:
        return jsonify(error="Subtask not found"), 404

    # Only owner can update
    if subtask.get("owner") != userid:
        return jsonify(error="Unauthorized: only owner can update subtask"), 403

    # Owner field update validation: only managers/directors allowed
    if "owner" in update_data:
        if role not in ("manager", "director"):
            return jsonify(error="Only managers/directors can change subtask owner"), 403

    # Update subtask data
    try:
        subtask_ref.update(update_data)
    except Exception as e:
        return jsonify(error=f"Failed to update subtask: {str(e)}"), 500

    updated_subtask = subtask_ref.get()
    return jsonify(message="Subtask updated", subtask=updated_subtask), 200



@app.route("/task/delete", methods=["POST"])
def delete_task():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    userid = data.get("userid")
    uid = data.get("uid")  # task ID to delete
    if not userid or not uid:
        return jsonify(error="userid and uid required"), 400
    
    task_ref = db.reference(f"tasks/{uid}")
    task = task_ref.get()
    if not task:
        return jsonify(error="Task not found"), 404
    
    # Only owner can delete
    if task.get("ownerUid") != userid:
        return jsonify(error="Unauthorized: only owner can delete task"), 403
    
    try:
        # Delete all subtasks associated with this task
        subtasks_ref = db.reference("subtask")
        all_subtasks = subtasks_ref.get() or {}
        # Filter subtasks linked to this task and delete them
        for key, subtask in all_subtasks.items():
            if subtask.get("taskId") == uid:
                subtasks_ref.child(key).delete()
        
        # Delete the task itself
        task_ref.delete()
    except Exception as e:
        return jsonify(error=f"Failed to delete task and its subtasks: {str(e)}"), 500

    return jsonify(message="Task and its subtasks deleted"), 200


@app.route("/subtask/delete", methods=["POST"])
def delete_subtask():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400
    
    userid = data.get("userid")
    subtaskId = data.get("subtaskId")
    if not userid or not subtaskId:
        return jsonify(error="userid and subtaskId required"), 400
    
    subtask_ref = db.reference(f"subtask/{subtaskId}")
    subtask = subtask_ref.get()
    if not subtask:
        return jsonify(error="Subtask not found"), 404
    
    # Only owner can delete
    if subtask.get("owner") != userid:
        return jsonify(error="Unauthorized: only owner can delete subtask"), 403

    try:
        subtask_ref.delete()
    except Exception as e:
        return jsonify(error=f"Failed to delete subtask: {str(e)}"), 500

    return jsonify(message="Subtask deleted"), 200


@app.route("/task/add-collaborator", methods=["POST"])
def add_task_collaborator():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    uid = data.get("uid")  # task ID
    adduserid = data.get("adduserid")  # user to add as collaborator

    if not userid or not uid or not adduserid:
        return jsonify(error="userid, uid and adduserid required"), 400

    task_ref = db.reference(f"tasks/{uid}")
    task = task_ref.get()
    if not task:
        return jsonify(error="Task not found"), 404

    # Only owner can add collaborators
    if task.get("ownerUid") != userid:
        return jsonify(error="Unauthorized: only owner can add collaborators"), 403

    collaborators = set(task.get("collaborators", []))
    collaborators.add(adduserid)

    try:
        task_ref.update({"collaborators": list(collaborators)})
    except Exception as e:
        return jsonify(error=f"Failed to add collaborator: {str(e)}"), 500

    updated_task = task_ref.get()
    return jsonify(message="Collaborator added", task=updated_task), 200


@app.route("/subtask/add-collaborator", methods=["POST"])
def add_subtask_collaborator():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400

    userid = data.get("userid")
    subtaskId = data.get("subtaskId")  # subtask ID
    adduserid = data.get("adduserid")  # user to add

    if not userid or not subtaskId or not adduserid:
        return jsonify(error="userid, subtaskId and adduserid required"), 400

    subtask_ref = db.reference(f"subtask/{subtaskId}")
    subtask = subtask_ref.get()
    if not subtask:
        return jsonify(error="Subtask not found"), 404

    # Only owner can add collaborators
    if subtask.get("owner") != userid:
        return jsonify(error="Unauthorized: only owner can add collaborators"), 403

    collaborators = set(subtask.get("collaborators", []))
    collaborators.add(adduserid)

    try:
        subtask_ref.update({"collaborators": list(collaborators)})
    except Exception as e:
        return jsonify(error=f"Failed to add collaborator: {str(e)}"), 500

    updated_subtask = subtask_ref.get()
    return jsonify(message="Collaborator added", subtask=updated_subtask), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002, debug=True)
