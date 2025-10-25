# backend/task-service/task_service.py
import sys
import os
import calendar
import logging
import requests
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, current_timestamp, validate_epoch_timestamp
from models import Task, CreateTaskRequest, UpdateTaskRequest

logger = logging.getLogger(__name__)

class TaskService:
    """Service for managing tasks"""

    def __init__(self):
        self.tasks_ref = get_db_reference("tasks")
        self.subtasks_ref = get_db_reference("subtasks")
        self.users_ref = get_db_reference("users")
        self.notification_prefs_ref = get_db_reference("notificationPreferences")
        self.notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:6004")
    
    def validate_status(self, status):
        """Validate status is one of the allowed values"""
        allowed_statuses = ["ongoing", "unassigned", "under review", "completed"]
        return status.lower() in [s.lower() for s in allowed_statuses]

    def send_task_update_notification(self, task_id, task_title, old_status, new_status, owner_id, collaborators):
        """Send task status update notifications to owner and collaborators"""
        try:
            # Combine owner and collaborators (assigned staff)
            user_ids = [owner_id] + (collaborators if collaborators else [])
            user_ids = list(set(user_ids))  # Remove duplicates

            # Fetch user emails and notification preferences for EACH user
            user_preferences = {}
            for user_id in user_ids:
                try:
                    # Get user email
                    user_data = self.users_ref.child(user_id).get()
                    user_email = user_data.get('email') if user_data else None

                    # Get user preferences
                    prefs = self.notification_prefs_ref.child(user_id).get()
                    if prefs:
                        # Check if task update reminders are enabled
                        if prefs.get('taskUpdateReminders', True):
                            user_preferences[user_id] = {
                                'email': user_email,
                                'channel': prefs.get('channel', 'both')
                            }
                    else:
                        # No preferences set, use default (enabled with both channels)
                        user_preferences[user_id] = {
                            'email': user_email,
                            'channel': 'both'
                        }
                except Exception as e:
                    logger.error(f"Failed to fetch preferences for user {user_id}: {str(e)}")
                    # Default to sending notification
                    user_data = self.users_ref.child(user_id).get()
                    user_email = user_data.get('email') if user_data else None
                    user_preferences[user_id] = {
                        'email': user_email,
                        'channel': 'both'
                    }

            if not user_preferences:
                logger.info("No users to notify for task update")
                return

            # Send notifications for each user with their individual preferences
            for user_id, prefs in user_preferences.items():
                try:
                    notification_data = {
                        'itemId': task_id,
                        'taskTitle': task_title,
                        'oldStatus': old_status,
                        'newStatus': new_status,
                        'userIds': [user_id],  # Send to one user at a time
                        'channel': prefs['channel'],
                        'isSubtask': False,
                        'userEmails': {user_id: prefs['email']} if prefs['email'] else {}
                    }

                    response = requests.post(
                        f"{self.notification_service_url}/notifications/task-update",
                        json=notification_data,
                        timeout=5
                    )

                    if response.status_code == 200:
                        logger.info(f"Task update notification sent for task {task_id} to user {user_id}")
                    else:
                        logger.error(f"Failed to send task update notification to {user_id}: {response.text}")
                except Exception as e:
                    logger.error(f"Error sending notification to user {user_id}: {str(e)}")

        except Exception as e:
            logger.error(f"Error sending task update notification: {str(e)}")
    
    def is_same_date(self, timestamp1, timestamp2):
        """Check if two timestamps are on the same calendar date (UTC)"""
        dt1 = datetime.fromtimestamp(timestamp1, tz=timezone.utc).date()
        dt2 = datetime.fromtimestamp(timestamp2, tz=timezone.utc).date()
        return dt1 == dt2
    
    def should_task_be_active(self, start_date, now):
        """Determine if a task should be active based on start_date"""
        if start_date is None:
            return False
        
        start_dt = datetime.fromtimestamp(start_date, tz=timezone.utc).date()
        current_dt = datetime.fromtimestamp(now, tz=timezone.utc).date()
        
        return start_dt <= current_dt
    
    def calculate_new_start_date(self, old_start_date, schedule, custom_schedule=None, completion_time=None):
        """Calculate the next start date based on schedule type"""
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
    
    def create_task_with_params(self, task_data, completion_time=None):
        """Create a recurring task based on existing task parameters"""
        now = completion_time if completion_time else current_timestamp()
        
        old_start_date = task_data.get("start_date")
        schedule = task_data.get("schedule", "daily")
        custom_schedule = task_data.get("custom_schedule")
        
        new_start_date = self.calculate_new_start_date(
            old_start_date, 
            schedule, 
            custom_schedule, 
            now
        )
        
        new_deadline_offset = task_data.get("deadline") - old_start_date
        new_deadline = new_start_date + new_deadline_offset
        
        new_task_ref = self.tasks_ref.push()
        
        # Determine status and startedAt based on owner
        owner_id = task_data.get("ownerId", "")
        creator_id = task_data.get("creatorId", "")
        
        # If owner is not the creator, status should be 'ongoing' and startedAt should be set

        if owner_id and owner_id != creator_id:
            new_status = "ongoing"
            new_started_at = now
        elif task_data.get("status") == "ongoing":
            new_status = "ongoing"
            new_started_at = now
        else:
            new_status = "unassigned"
            new_started_at = None
        
        new_task_data = {
            "taskId": new_task_ref.key,
            "title": task_data.get("title"),
            "creatorId": creator_id,
            "deadline": new_deadline,
            "status": new_status,
            "notes": task_data.get("notes", ""),
            "attachments": task_data.get("attachments", []),
            "collaborators": task_data.get("collaborators", []),
            "projectId": task_data.get("projectId", ""),
            "ownerId": owner_id if owner_id else creator_id,
            "priority": task_data.get("priority", 0),
            "createdAt": now,
            "updatedAt": now,
            "start_date": new_start_date,
            "active": self.should_task_be_active(new_start_date, now),
            "scheduled": True,
            "schedule": schedule,
            "custom_schedule": custom_schedule,
            "completedAt": None,
            "startedAt": new_started_at
        }
        
        new_task_ref.set(new_task_data)
        return Task.from_dict(new_task_data)
    
    def create_task(self, req: CreateTaskRequest):
        """Create a new task"""
        new_task_ref = self.tasks_ref.push()
        current_time = current_timestamp()
        
        # Set owner_id to creator_id if not provided
        owner_id = req.owner_id if req.owner_id else req.creator_id
        
        # Determine initial status and startedAt based on business rules
        # If owner is different from creator, status = 'ongoing' and startedAt = current_time
        # If owner is same as creator (or default), status = 'unassigned' and startedAt = None
        if owner_id != req.creator_id:
            initial_status = "ongoing"
            started_at = current_time
        elif req.status == "ongoing":
            initial_status = "ongoing"
            started_at = current_time
        else:
            initial_status = "unassigned"
            started_at = None
        
        task_data = {
            "taskId": new_task_ref.key,
            "title": req.title,
            "creatorId": req.creator_id,
            "deadline": req.deadline,
            "status": initial_status,
            "notes": req.notes,
            "attachments": req.attachments,
            "collaborators": req.collaborators,
            "projectId": req.project_id,
            "ownerId": owner_id,
            "priority": req.priority,
            "createdAt": current_time,
            "updatedAt": current_time,
            "start_date": req.start_date if req.start_date else current_time,
            "active": req.active,
            "scheduled": req.scheduled,
            "schedule": req.schedule,
            "custom_schedule": req.custom_schedule,
            "completedAt": None,
            "startedAt": started_at
        }
        
        new_task_ref.set(task_data)
        return Task.from_dict(task_data), None
    
    def get_all_tasks(self):
        """Get all active tasks"""
        all_tasks = self.tasks_ref.get() or {}
        now = current_timestamp()
        active_tasks = []
        
        for task_data in all_tasks.values():
            start_date = task_data.get("start_date")
            if start_date is not None:
                should_be_active = self.should_task_be_active(start_date, now)
                
                if should_be_active != task_data.get("active", False):
                    self.tasks_ref.child(task_data['taskId']).update({"active": should_be_active})
                
                task_data["active"] = should_be_active
                
                if should_be_active:
                    active_tasks.append(Task.from_dict(task_data))
            elif task_data.get("active", False):
                active_tasks.append(Task.from_dict(task_data))
        
        return active_tasks
    
    def get_task_by_id(self, task_id):
        """Get a task by ID"""
        task_ref = self.tasks_ref.child(task_id)
        task_data = task_ref.get()
        
        if not task_data:
            return None, "Task not found"
        
        now = current_timestamp()
        start_date = task_data.get("start_date")
        
        if start_date is not None:
            should_be_active = self.should_task_be_active(start_date, now)
            if should_be_active != task_data.get("active", False):
                task_ref.update({"active": should_be_active})
                task_data["active"] = should_be_active
        
        return Task.from_dict(task_data), None
    
    def update_task(self, req: UpdateTaskRequest):
        """Update a task by ID"""
        task_ref = self.tasks_ref.child(req.task_id)
        existing_task = task_ref.get()
        
        if not existing_task:
            return None, "Task not found"
        
        update_data = {}
        prev_status = existing_task.get("status", "").lower()
        prev_owner_id = existing_task.get("ownerId", "")
        creator_id = existing_task.get("creatorId", "")
        
        # Handle title update
        if req.title is not None:
            if not req.title.strip():
                return None, "Title cannot be empty"
            update_data["title"] = req.title
        
        # Handle deadline update
        if req.deadline is not None:
            update_data["deadline"] = req.deadline
        
        # Handle status update and set completedAt/startedAt
        if req.status is not None:
            new_status = req.status.lower()
            update_data["status"] = new_status
            
            # Set completedAt when status changes to 'completed'
            if prev_status != "completed" and new_status == "completed":
                current_time = current_timestamp()
                update_data["completedAt"] = current_time
            
            # Set startedAt when status changes from 'unassigned' to 'ongoing'
            if prev_status == "unassigned" and new_status == "ongoing":
                if existing_task.get("startedAt") is None:
                    current_time = current_timestamp()
                    update_data["startedAt"] = current_time
        
        # Handle owner_id update - auto-change status to 'ongoing' if owner != creator
        if req.owner_id is not None:
            update_data["ownerId"] = req.owner_id
            
            # If owner is being changed to someone other than creator, and status is 'unassigned'
            # then automatically change status to 'ongoing' and set startedAt
            if req.owner_id != creator_id and prev_status == "unassigned":
                update_data["status"] = "ongoing"
                if existing_task.get("startedAt") is None:
                    current_time = current_timestamp()
                    update_data["startedAt"] = current_time
        
        # Handle other fields
        if req.notes is not None:
            update_data["notes"] = req.notes
        
        if req.attachments is not None:
            update_data["attachments"] = req.attachments
        
        if req.collaborators is not None:
            update_data["collaborators"] = req.collaborators
        
        if req.project_id is not None:
            update_data["projectId"] = req.project_id
        
        if req.priority is not None:
            update_data["priority"] = req.priority
        
        if req.active is not None:
            update_data["active"] = req.active
        
        if req.scheduled is not None:
            update_data["scheduled"] = req.scheduled
        
        if req.schedule is not None:
            update_data["schedule"] = req.schedule
            if req.schedule == "custom" and req.custom_schedule:
                update_data["custom_schedule"] = req.custom_schedule
            else:
                update_data["custom_schedule"] = None
        
        if req.start_date is not None:
            update_data["start_date"] = req.start_date
        
        current_time = current_timestamp()
        update_data["updatedAt"] = current_time
        
        if len(update_data) == 1 and "updatedAt" in update_data:
            return None, "No valid fields provided for update"
        
        task_ref.update(update_data)

        # Get updated task
        updated_task = task_ref.get()

        # Check for status change and send notifications
        new_status = req.status.lower() if req.status else prev_status
        if new_status != prev_status:
            # Send notification to owner and collaborators
            self.send_task_update_notification(
                req.task_id,
                updated_task.get('title', 'Untitled'),
                prev_status,
                new_status,
                updated_task.get('ownerId'),
                updated_task.get('collaborators', [])
            )

        # Check for recurring task creation
        if prev_status != "completed" and new_status == "completed" and existing_task.get("scheduled"):
            self.create_task_with_params(updated_task, completion_time=current_time)

        return Task.from_dict(updated_task), None
    
    def delete_task(self, task_id):
        """Delete a task by ID"""
        task_ref = self.tasks_ref.child(task_id)
        existing_task = task_ref.get()
        
        if not existing_task:
            return False, "Task not found"
        
        task_ref.delete()
        return True, None
    
    def get_tasks_by_project(self, project_id):
        """Get all active tasks by project ID"""
        all_tasks = self.tasks_ref.get() or {}
        now = current_timestamp()
        active_filtered_tasks = []
        
        for task_data in all_tasks.values():
            if task_data.get("projectId") == project_id:
                start_date = task_data.get("start_date")
                if start_date is not None:
                    should_be_active = self.should_task_be_active(start_date, now)
                    
                    if should_be_active != task_data.get("active", False):
                        self.tasks_ref.child(task_data['taskId']).update({"active": should_be_active})
                    
                    task_data["active"] = should_be_active
                    
                    if should_be_active:
                        active_filtered_tasks.append(Task.from_dict(task_data))
                elif task_data.get("active", False):
                    active_filtered_tasks.append(Task.from_dict(task_data))
        
        return active_filtered_tasks
