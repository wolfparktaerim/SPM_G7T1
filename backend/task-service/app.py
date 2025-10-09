from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timezone, timedelta
import os
import calendar


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
    allowed_statuses = ["ongoing", "unassigned", "under review", "completed"]
    return status.lower() in [s.lower() for s in allowed_statuses]


def validate_epoch_timestamp(timestamp):
    """Validate that timestamp is a valid epoch timestamp"""
    try:
        if isinstance(timestamp, (int, float)):
            return timestamp > 0
        return False
    except (ValueError, TypeError):
        return False


def is_same_date(timestamp1, timestamp2):
    """Check if two timestamps are on the same calendar date (UTC)"""
    dt1 = datetime.fromtimestamp(timestamp1, tz=timezone.utc).date()
    dt2 = datetime.fromtimestamp(timestamp2, tz=timezone.utc).date()
    return dt1 == dt2


def should_task_be_active(start_date, now):
    """
    Determine if a task should be active based on start_date.
    Task is active if start_date <= current date (same day or past).
    """
    if start_date is None:
        return False
    
    start_dt = datetime.fromtimestamp(start_date, tz=timezone.utc).date()
    current_dt = datetime.fromtimestamp(now, tz=timezone.utc).date()
    
    return start_dt <= current_dt


def calculate_new_start_date(old_start_date, schedule, custom_schedule=None, completion_time=None):
    """
    Calculate the next start date based on schedule type and old start date.
    If completion_time is provided and the calculated new start date is in the past,
    the task starts immediately.
    """
    now = current_timestamp()
    old_dt = datetime.fromtimestamp(old_start_date, tz=timezone.utc)


    if schedule == "daily":
        new_dt = old_dt + timedelta(days=1)
    elif schedule == "weekly":
        new_dt = old_dt + timedelta(weeks=1)
    elif schedule == "monthly":
        month = old_dt.month + 1 if old_dt.month < 12 else 1
        year = old_dt.year if old_dt.month < 12 else old_dt.year + 1
        day = old_dt.day
        # handle day overflow in next month
        try:
            new_dt = datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            last_day = calendar.monthrange(year, month)[1]
            new_dt = datetime(year, month, last_day, tzinfo=timezone.utc)
    elif schedule == "custom" and custom_schedule:
        new_dt = old_dt + timedelta(days=custom_schedule)
    else:
        new_dt = old_dt  # fallback


    new_start_ts = int(new_dt.timestamp())


    # If completion_time is provided (task was completed)
    if completion_time:
        # If the calculated new start date has already passed (task was completed late)
        if new_start_ts < completion_time:
            # Start immediately
            new_start_ts = completion_time
    else:
        # Original logic for non-completion scenarios
        # If new start date is earlier than today, shift to today + schedule
        if new_start_ts < now:
            today_dt = datetime.fromtimestamp(now, tz=timezone.utc)
            if schedule == "daily":
                new_dt = today_dt + timedelta(days=1)
            elif schedule == "weekly":
                new_dt = today_dt + timedelta(weeks=1)
            elif schedule == "monthly":
                month = today_dt.month + 1 if today_dt.month < 12 else 1
                year = today_dt.year if today_dt.month < 12 else today_dt.year + 1
                day = today_dt.day
                try:
                    new_dt = datetime(year, month, day, tzinfo=timezone.utc)
                except ValueError:
                    last_day = calendar.monthrange(year, month)[1]
                    new_dt = datetime(year, month, last_day, tzinfo=timezone.utc)
            elif schedule == "custom" and custom_schedule:
                new_dt = today_dt + timedelta(days=custom_schedule)
            new_start_ts = int(new_dt.timestamp())


    return new_start_ts


def create_task_with_params(task, completion_time=None):
    """
    Create a new recurring task based on the completed task.
    The new task's deadline is calculated as: new_start_date + (old_deadline - old_start_date)
    The task is only active if the start date is <= current date.
    """
    now = current_timestamp()
    
    # Calculate the duration of the original task (deadline - start_date)
    original_duration = task.get("deadline", now) - task.get("start_date", now)
    
    # Calculate new start date
    new_start_date = calculate_new_start_date(
        task.get("start_date", now),
        task.get("schedule"),
        task.get("custom_schedule"),
        completion_time  # Pass completion time to determine if task should start immediately
    )
    
    # Calculate new deadline: new_start_date + original_duration
    new_deadline = new_start_date + original_duration
    
    # Task is active if start date <= current date
    active_flag = should_task_be_active(new_start_date, now)


    new_task_ref = db.reference("tasks").push()
    new_task_data = dict(task)  # copy all fields


    # Update fields for the new task
    new_task_data.update({
        "taskId": new_task_ref.key,
        "start_date": new_start_date,
        "deadline": new_deadline,  # Updated deadline calculation
        "active": active_flag,
        "status": "ongoing",  # new task is ongoing
        "createdAt": now,
        "updatedAt": now
    })


    new_task_ref.set(new_task_data)


    # --- Load all subtasks and filter manually to avoid requiring an index ---
    original_task_id = task.get("taskId")
    subtasks_ref = db.reference("subtasks")
    all_subtasks = subtasks_ref.get() or {}


    # Filter locally for subtasks matching the original task ID
    filtered_subtasks = {
        subtask_id: subtask
        for subtask_id, subtask in all_subtasks.items()
        if subtask.get("taskId") == original_task_id
    }


    for subtask_id, subtask in filtered_subtasks.items():
        # Prepare new subtask based on the old one
        new_subtask = dict(subtask)
        # Remove old subtask id to generate new one
        new_subtask.pop("subTaskId", None)


        # Calculate the original subtask duration
        subtask_original_duration = subtask.get("deadline", now) - subtask.get("start_date", now)


        # Calculate the new start date for the subtask
        new_subtask_start_date = calculate_new_start_date(
            subtask.get("start_date", now),
            subtask.get("schedule") if "schedule" in subtask else None,
            subtask.get("custom_schedule") if "custom_schedule" in subtask else None,
            completion_time
        )
        
        # Calculate new subtask deadline
        new_subtask_deadline = new_subtask_start_date + subtask_original_duration
        
        new_subtask["start_date"] = new_subtask_start_date
        new_subtask["deadline"] = new_subtask_deadline  # Updated deadline for subtask
        new_subtask["taskId"] = new_task_ref.key
        new_subtask["status"] = "ongoing"
        new_subtask["active"] = should_task_be_active(new_subtask_start_date, now)
        new_subtask["createdAt"] = now
        new_subtask["updatedAt"] = now


        # Conditionally include schedule fields only if they existed in the original subtask
        if "schedule" not in subtask:
            new_subtask.pop("schedule", None)
        if "custom_schedule" not in subtask:
            new_subtask.pop("custom_schedule", None)


        # Push the new subtask and assign its new ID
        new_subtask_ref = subtasks_ref.push()
        new_subtask["subTaskId"] = new_subtask_ref.key
        new_subtask_ref.set(new_subtask)


@app.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task"""
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400


    required_fields = ["title", "creatorId", "deadline"]
    for field in required_fields:
        if not data.get(field):
            return jsonify(error=f"Missing required field: {field}"), 400


    deadline = data.get("deadline")
    if not validate_epoch_timestamp(deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400


    status = data.get("status", "ongoing").lower()


    title = data.get("title").strip()
    if not title:
        return jsonify(error="Title cannot be empty"), 400


    creator_id = data.get("creatorId")
    owner_id = data.get("ownerId", creator_id)
    notes = data.get("notes", "")
    attachments = data.get("attachments", [])
    collaborators = data.get("collaborators", [])
    project_id = data.get("projectId", "")


    priority = data.get("priority")
    if priority is not None:
        if not isinstance(priority, int):
            return jsonify(error="Priority must be an integer"), 400
    else:
        priority = 0


    if not isinstance(attachments, list) or not all(isinstance(att, str) for att in attachments):
        return jsonify(error="Attachments must be an array of strings (base64)"), 400


    if not isinstance(collaborators, list) or not all(isinstance(collab, str) for collab in collaborators):
        return jsonify(error="Collaborators must be an array of user IDs"), 400


    active = data.get("active", True)
    scheduled = data.get("scheduled", False)
    schedule = data.get("schedule", "daily")
    valid_schedules = ["daily", "weekly", "monthly", "custom"]
    if schedule not in valid_schedules:
        return jsonify(error=f"Schedule must be one of: {', '.join(valid_schedules)}"), 400


    custom_schedule = data.get("custom_schedule")
    if schedule == "custom":
        if custom_schedule is None or not isinstance(custom_schedule, int):
            return jsonify(error="custom_schedule must be an integer when schedule is 'custom'"), 400
    else:
        custom_schedule = None


    reminder_interval = data.get("reminderInterval", [])
    if not isinstance(reminder_interval, list) or not all(isinstance(i, int) for i in reminder_interval):
        return jsonify(error="reminderInterval must be a list of integers"), 400


    current_time = current_timestamp()
    start_date = data.get("start_date", current_time)
    if not validate_epoch_timestamp(start_date):
        return jsonify(error="start_date must be a valid epoch timestamp"), 400


    tasks_ref = db.reference("tasks")
    new_task_ref = tasks_ref.push()
    task_id = new_task_ref.key


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
        "priority": priority,
        "createdAt": current_time,
        "updatedAt": current_time,
        "start_date": start_date,
        "active": bool(active),
        "scheduled": bool(scheduled),
        "schedule": schedule,
        "custom_schedule": custom_schedule,
        "reminderInterval": reminder_interval
    }


    try:
        new_task_ref.set(task_data)
        return jsonify(message="Task created successfully", task=task_data), 201
    except Exception as e:
        return jsonify(error=f"Failed to create task: {str(e)}"), 500


@app.route("/tasks", methods=["GET"])
def get_all_tasks():
    """Get all active tasks only, filtered in-memory. Update active flag if start_date <= current_date"""
    try:
        tasks_ref = db.reference("tasks")
        all_tasks = tasks_ref.get() or {}


        now = current_timestamp()
        active_tasks = []
        
        for task in all_tasks.values():
            start_date = task.get("start_date")
            if start_date is not None:
                # Task is active if start date <= current date
                should_be_active = should_task_be_active(start_date, now)
                
                # Update active flag in DB if it changed
                if should_be_active != task.get("active", False):
                    db.reference(f"tasks/{task['taskId']}").update({"active": should_be_active})
                
                task["active"] = should_be_active
                
                # Only add to result if task is active
                if should_be_active:
                    active_tasks.append(task)
            elif task.get("active", False):
                # Include tasks without start_date if they're marked as active
                active_tasks.append(task)


        return jsonify(tasks=active_tasks), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve tasks: {str(e)}"), 500


@app.route("/tasks/<task_id>", methods=["GET"])
def get_task_by_id(task_id):
    """Get a task by ID with active flag updated if start_date <= current_date"""
    try:
        task_ref = db.reference(f"tasks/{task_id}")
        task = task_ref.get()


        if not task:
            return jsonify(error="Task not found"), 404


        now = current_timestamp()
        start_date = task.get("start_date")
        if start_date is not None:
            # Task is active if start date <= current date
            should_be_active = should_task_be_active(start_date, now)
            if should_be_active != task.get("active", False):
                task_ref.update({"active": should_be_active})
            task["active"] = should_be_active


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
        task_ref = db.reference(f"tasks/{task_id}")
        existing_task = task_ref.get()
        if not existing_task:
            return jsonify(error="Task not found"), 404


        prev_status = existing_task.get("status", "").lower()


        update_data = {}


        if "title" in data:
            title = data["title"].strip()
            if not title:
                return jsonify(error="Title cannot be empty"), 400
            update_data["title"] = title


        if "deadline" in data:
            deadline = data["deadline"]
            if not validate_epoch_timestamp(deadline):
                return jsonify(error="Deadline must be a valid epoch timestamp"), 400
            update_data["deadline"] = deadline


        if "status" in data:
            status = data["status"].lower()
            update_data["status"] = status


        if "priority" in data:
            priority = data["priority"]
            if not isinstance(priority, int):
                return jsonify(error="Priority must be an integer"), 400
            update_data["priority"] = priority


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


        if "active" in data:
            update_data["active"] = bool(data["active"])


        if "scheduled" in data:
            update_data["scheduled"] = bool(data["scheduled"])


        if "schedule" in data:
            schedule = data["schedule"]
            valid_schedules = ["daily", "weekly", "monthly", "custom"]
            if schedule not in valid_schedules:
                return jsonify(error=f"Schedule must be one of: {', '.join(valid_schedules)}"), 400
            update_data["schedule"] = schedule


            if schedule == "custom":
                custom_schedule = data.get("custom_schedule")
                if custom_schedule is None or not isinstance(custom_schedule, int):
                    return jsonify(error="custom_schedule must be an integer when schedule is 'custom'"), 400
                update_data["custom_schedule"] = custom_schedule
            else:
                update_data["custom_schedule"] = None
        elif "custom_schedule" in data:
            if existing_task.get("schedule") == "custom":
                if data["custom_schedule"] is None or not isinstance(data["custom_schedule"], int):
                    return jsonify(error="custom_schedule must be an integer when schedule is 'custom'"), 400
                update_data["custom_schedule"] = data["custom_schedule"]


        if "start_date" in data:
            start_date = data["start_date"]
            if not validate_epoch_timestamp(start_date):
                return jsonify(error="start_date must be a valid epoch timestamp"), 400
            update_data["start_date"] = start_date


        if "reminderInterval" in data:
            reminder_interval = data["reminderInterval"]
            if not isinstance(reminder_interval, list) or not all(isinstance(i, int) for i in reminder_interval):
                return jsonify(error="reminderInterval must be a list of integers"), 400
            update_data["reminderInterval"] = reminder_interval


        current_time = current_timestamp()
        update_data["updatedAt"] = current_time


        if not update_data or (len(update_data) == 1 and "updatedAt" in update_data):
            return jsonify(error="No valid fields provided for update"), 400


        task_ref.update(update_data)


        # Check for status transition to completed and scheduled true
        new_status = data.get("status", prev_status).lower()
        if prev_status != "completed" and new_status == "completed" and existing_task.get("scheduled"):
            # Create new scheduled task with completion time
            updated_task = task_ref.get()
            create_task_with_params(updated_task, completion_time=current_time)


        updated_task = task_ref.get()
        return jsonify(message="Task updated successfully", task=updated_task), 200


    except Exception as e:
        return jsonify(error=f"Failed to update task: {str(e)}"), 500


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task_by_id(task_id):
    """Delete a task by ID"""
    try:
        task_ref = db.reference(f"tasks/{task_id}")
        existing_task = task_ref.get()
        if not existing_task:
            return jsonify(error="Task not found"), 404


        task_ref.delete()


        return jsonify(message="Task deleted successfully"), 200


    except Exception as e:
        return jsonify(error=f"Failed to delete task: {str(e)}"), 500


@app.route("/tasks/project/<project_id>", methods=["GET"])
def get_tasks_by_project(project_id):
    """Get all active tasks by project ID, filtered in-memory. Update active flag if start_date <= current_date"""
    try:
        tasks_ref = db.reference("tasks")
        all_tasks = tasks_ref.get() or {}


        now = current_timestamp()
        active_filtered_tasks = []
        
        for task in all_tasks.values():
            if task.get("projectId") == project_id:
                start_date = task.get("start_date")
                if start_date is not None:
                    # Task is active if start date <= current date
                    should_be_active = should_task_be_active(start_date, now)
                    
                    # Update active flag in DB if it changed
                    if should_be_active != task.get("active", False):
                        db.reference(f"tasks/{task['taskId']}").update({"active": should_be_active})
                    
                    task["active"] = should_be_active
                    
                    # Only add to result if task is active
                    if should_be_active:
                        active_filtered_tasks.append(task)
                elif task.get("active", False):
                    # Include tasks without start_date if they're marked as active
                    active_filtered_tasks.append(task)


        return jsonify(tasks=active_filtered_tasks), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve tasks by project: {str(e)}"), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="task-service"), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6002, debug=True)
