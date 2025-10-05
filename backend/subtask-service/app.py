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
    return int(datetime.now(timezone.utc).timestamp())


def validate_status(status):
    allowed_statuses = ["ongoing", "unassigned", "under_review", "completed"]
    return status.lower() in allowed_statuses


def validate_epoch_timestamp(timestamp):
    try:
        if isinstance(timestamp, (int, float)):
            return timestamp > 0
        return False
    except (ValueError, TypeError):
        return False


def calculate_new_start_date(old_start_date, schedule, custom_schedule=None):
    today_ts = current_timestamp()
    old_dt = datetime.fromtimestamp(old_start_date, tz=timezone.utc)


    if schedule == "daily":
        new_dt = old_dt + timedelta(days=1)
    elif schedule == "weekly":
        new_dt = old_dt + timedelta(weeks=1)
    elif schedule == "monthly":
        month = old_dt.month + 1 if old_dt.month < 12 else 1
        year = old_dt.year if old_dt.month < 12 else old_dt.year + 1
        day = old_dt.day
        try:
            new_dt = datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            last_day = calendar.monthrange(year, month)[1]
            new_dt = datetime(year, month, last_day, tzinfo=timezone.utc)
    elif schedule == "custom" and custom_schedule:
        new_dt = old_dt + timedelta(days=custom_schedule)
    else:
        new_dt = old_dt


    new_start_ts = int(new_dt.timestamp())


    if new_start_ts < today_ts:
        today_dt = datetime.fromtimestamp(today_ts, tz=timezone.utc)
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


def create_subtask_with_params(subtask):
    now = current_timestamp()
    new_start_date = calculate_new_start_date(
        subtask.get("start_date", now),
        subtask.get("schedule"),
        subtask.get("custom_schedule")
    )
    active_flag = True if new_start_date <= now else False


    new_subtask_ref = db.reference("subtasks").push()
    new_subtask_data = dict(subtask)  # clone original subtask


    new_subtask_data.update({
        "subTaskId": new_subtask_ref.key,
        "start_date": new_start_date,
        "active": active_flag,
        "status": "ongoing",
        "createdAt": now,
        "updatedAt": now
    })


    new_subtask_ref.set(new_subtask_data)


@app.route("/subtasks", methods=["POST"])
def create_subtask():
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400


    required_fields = ["title", "creatorId", "deadline", "taskId"]
    for field in required_fields:
        if not data.get(field):
            return jsonify(error=f"Missing required field: {field}"), 400


    deadline = data.get("deadline")
    if not validate_epoch_timestamp(deadline):
        return jsonify(error="Deadline must be a valid epoch timestamp"), 400


    status = data.get("status", "ongoing").lower()
    if not validate_status(status):
        return jsonify(error="Status must be one of: ongoing, unassigned, under_review, completed"), 400


    task_id = data.get("taskId")
    try:
        parent_task_ref = db.reference(f"tasks/{task_id}")
        parent_task = parent_task_ref.get()
        if not parent_task:
            return jsonify(error="Parent task not found"), 404
    except Exception as e:
        return jsonify(error=f"Failed to validate parent task: {str(e)}"), 500


    title = data.get("title").strip()
    if not title:
        return jsonify(error="Title cannot be empty"), 400


    creator_id = data.get("creatorId")
    owner_id = data.get("ownerId", creator_id)
    notes = data.get("notes", "")
    attachments = data.get("attachments", [])
    collaborators = data.get("collaborators", [])


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


    subtasks_ref = db.reference("subtasks")
    new_subtask_ref = subtasks_ref.push()
    subtask_id = new_subtask_ref.key


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
        new_subtask_ref.set(subtask_data)
        return jsonify(message="Subtask created successfully", subtask=subtask_data), 201
    except Exception as e:
        return jsonify(error=f"Failed to create subtask: {str(e)}"), 500


@app.route("/subtasks", methods=["GET"])
def get_all_subtasks():
    try:
        subtasks_ref = db.reference("subtasks")
        all_subtasks = subtasks_ref.get() or {}


        now = current_timestamp()
        for subtask in all_subtasks.values():
            start_date = subtask.get("start_date")
            if start_date is not None:
                if now >= start_date:
                    if not subtask.get("active", False):
                        db.reference(f"subtasks/{subtask['subTaskId']}").update({"active": True})
                    subtask["active"] = True
                else:
                    subtask["active"] = False


        return jsonify(subtasks=list(all_subtasks.values())), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve subtasks: {str(e)}"), 500


@app.route("/subtasks/<subtask_id>", methods=["GET"])
def get_subtask_by_id(subtask_id):
    try:
        subtask_ref = db.reference(f"subtasks/{subtask_id}")
        subtask = subtask_ref.get()


        if not subtask:
            return jsonify(error="Subtask not found"), 404


        now = current_timestamp()
        start_date = subtask.get("start_date")
        if start_date is not None:
            if now >= start_date and not subtask.get("active", False):
                subtask_ref.update({"active": True})
                subtask["active"] = True
            elif now < start_date:
                subtask["active"] = False


        return jsonify(subtask=subtask), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve subtask: {str(e)}"), 500


@app.route("/subtasks/<subtask_id>", methods=["PUT"])
def update_subtask_by_id(subtask_id):
    data = request.get_json()
    if not data:
        return jsonify(error="Missing JSON body"), 400


    try:
        subtask_ref = db.reference(f"subtasks/{subtask_id}")
        existing_subtask = subtask_ref.get()
        if not existing_subtask:
            return jsonify(error="Subtask not found"), 404


        prev_status = existing_subtask.get("status", "").lower()


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
            if not validate_status(status):
                return jsonify(error="Status must be one of: ongoing, unassigned, under_review, completed"), 400
            update_data["status"] = status


        if "taskId" in data:
            task_id = data["taskId"]
            parent_task_ref = db.reference(f"tasks/{task_id}")
            parent_task = parent_task_ref.get()
            if not parent_task:
                return jsonify(error="Parent task not found"), 404
            update_data["taskId"] = task_id


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
            if existing_subtask.get("schedule") == "custom":
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


        update_data["updatedAt"] = current_timestamp()


        if not update_data or (len(update_data) == 1 and "updatedAt" in update_data):
            return jsonify(error="No valid fields provided for update"), 400


        subtask_ref.update(update_data)


        new_status = data.get("status", prev_status).lower()
        if prev_status != "completed" and new_status == "completed" and existing_subtask.get("scheduled"):
            updated_subtask = subtask_ref.get()
            create_subtask_with_params(updated_subtask)


        updated_subtask = subtask_ref.get()
        return jsonify(message="Subtask updated successfully", subtask=updated_subtask), 200


    except Exception as e:
        return jsonify(error=f"Failed to update subtask: {str(e)}"), 500


@app.route("/subtasks/<subtask_id>", methods=["DELETE"])
def delete_subtask_by_id(subtask_id):
    try:
        subtask_ref = db.reference(f"subtasks/{subtask_id}")
        existing_subtask = subtask_ref.get()
        if not existing_subtask:
            return jsonify(error="Subtask not found"), 404


        subtask_ref.delete()


        return jsonify(message="Subtask deleted successfully"), 200
    except Exception as e:
        return jsonify(error=f"Failed to delete subtask: {str(e)}"), 500


@app.route("/subtasks/task/<task_id>", methods=["GET"])
def get_subtasks_by_task(task_id):
    try:
        subtasks_ref = db.reference("subtasks")
        all_subtasks = subtasks_ref.get() or {}


        now = current_timestamp()
        filtered_subtasks = []
        for subtask in all_subtasks.values():
            if subtask.get("taskId") == task_id:
                start_date = subtask.get("start_date")
                if start_date is not None:
                    if now >= start_date:
                        if not subtask.get("active", False):
                            db.reference(f"subtasks/{subtask['subTaskId']}").update({"active": True})
                        subtask["active"] = True
                    else:
                        subtask["active"] = False
                filtered_subtasks.append(subtask)


        return jsonify(subtasks=filtered_subtasks), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve subtasks by task: {str(e)}"), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="healthy", service="subtask-service"), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6003, debug=True)
