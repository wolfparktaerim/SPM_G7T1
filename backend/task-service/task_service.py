# backend/task-service/task_service.py
import sys
import os
import calendar
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, current_timestamp, validate_epoch_timestamp
from models import Task, CreateTaskRequest, UpdateTaskRequest

class TaskService:
    """Service for managing tasks"""
    
    def __init__(self):
        self.tasks_ref = get_db_reference("tasks")
        self.subtasks_ref = get_db_reference("subtasks")
    
    def validate_status(self, status):
        """Validate status is one of the allowed values"""
        allowed_statuses = ["ongoing", "unassigned", "under review", "completed"]
        return status.lower() in [s.lower() for s in allowed_statuses]
    
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
        
        if completion_time:
            if new_start_ts < completion_time:
                new_start_ts = completion_time
        else:
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
        """Create a new recurring task based on a completed task"""
        now = current_timestamp()
        
        original_duration = task_data.get("deadline", now) - task_data.get("start_date", now)
        
        new_start_date = self.calculate_new_start_date(
            task_data.get("start_date", now),
            task_data.get("schedule"),
            task_data.get("custom_schedule"),
            completion_time
        )
        
        new_deadline = new_start_date + original_duration
        active_flag = self.should_task_be_active(new_start_date, now)
        
        new_task_ref = self.tasks_ref.push()
        new_task_data = dict(task_data)
        
        new_task_data.update({
            "taskId": new_task_ref.key,
            "start_date": new_start_date,
            "deadline": new_deadline,
            "active": active_flag,
            "status": "ongoing",
            "createdAt": now,
            "updatedAt": now
        })
        
        new_task_ref.set(new_task_data)
        
        # Create subtasks for the new task
        original_task_id = task_data.get("taskId")
        all_subtasks = self.subtasks_ref.get() or {}
        
        filtered_subtasks = {
            subtask_id: subtask
            for subtask_id, subtask in all_subtasks.items()
            if subtask.get("taskId") == original_task_id
        }
        
        for subtask_id, subtask in filtered_subtasks.items():
            new_subtask = dict(subtask)
            new_subtask.pop("subTaskId", None)
            
            subtask_original_duration = subtask.get("deadline", now) - subtask.get("start_date", now)
            
            new_subtask_start_date = self.calculate_new_start_date(
                subtask.get("start_date", now),
                subtask.get("schedule") if "schedule" in subtask else None,
                subtask.get("custom_schedule") if "custom_schedule" in subtask else None,
                completion_time
            )
            
            new_subtask_deadline = new_subtask_start_date + subtask_original_duration
            
            new_subtask["start_date"] = new_subtask_start_date
            new_subtask["deadline"] = new_subtask_deadline
            new_subtask["taskId"] = new_task_ref.key
            new_subtask["status"] = "ongoing"
            new_subtask["active"] = self.should_task_be_active(new_subtask_start_date, now)
            new_subtask["createdAt"] = now
            new_subtask["updatedAt"] = now
            
            if "schedule" not in subtask:
                new_subtask.pop("schedule", None)
            if "custom_schedule" not in subtask:
                new_subtask.pop("custom_schedule", None)
            
            new_subtask_ref = self.subtasks_ref.push()
            new_subtask["subTaskId"] = new_subtask_ref.key
            new_subtask_ref.set(new_subtask)
    
    def create_task(self, req: CreateTaskRequest):
        """Create a new task"""
        current_time = current_timestamp()
        
        # Set owner_id to creator_id if not provided
        owner_id = req.owner_id if req.owner_id else req.creator_id
        
        # Set start_date to current time if not provided
        start_date = req.start_date if req.start_date else current_time
        
        new_task_ref = self.tasks_ref.push()
        task_id = new_task_ref.key
        
        task = Task(
            task_id=task_id,
            title=req.title,
            creator_id=req.creator_id,
            deadline=req.deadline,
            status=req.status,
            notes=req.notes,
            attachments=req.attachments,
            collaborators=req.collaborators,
            project_id=req.project_id,
            owner_id=owner_id,
            priority=req.priority,
            created_at=current_time,
            updated_at=current_time,
            start_date=start_date,
            active=bool(req.active),
            scheduled=bool(req.scheduled),
            schedule=req.schedule,
            custom_schedule=req.custom_schedule
        )
        
        new_task_ref.set(task.to_dict())
        return task, None
    
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
        
        prev_status = existing_task.get("status", "").lower()
        
        update_data = {}
        
        if req.title is not None:
            title = req.title.strip()
            if not title:
                return None, "Title cannot be empty"
            update_data["title"] = title
        
        if req.deadline is not None:
            update_data["deadline"] = req.deadline
        
        if req.status is not None:
            update_data["status"] = req.status.lower()
        
        if req.priority is not None:
            update_data["priority"] = req.priority
        
        if req.notes is not None:
            update_data["notes"] = req.notes
        
        if req.attachments is not None:
            update_data["attachments"] = req.attachments
        
        if req.collaborators is not None:
            update_data["collaborators"] = req.collaborators
        
        if req.project_id is not None:
            update_data["projectId"] = req.project_id
        
        if req.owner_id is not None:
            update_data["ownerId"] = req.owner_id
        
        if req.active is not None:
            update_data["active"] = bool(req.active)
        
        if req.scheduled is not None:
            update_data["scheduled"] = bool(req.scheduled)
        
        if req.schedule is not None:
            update_data["schedule"] = req.schedule
            if req.schedule == "custom":
                if req.custom_schedule is None:
                    return None, "custom_schedule required when schedule is 'custom'"
                update_data["custom_schedule"] = req.custom_schedule
            else:
                update_data["custom_schedule"] = None
        elif req.custom_schedule is not None:
            if existing_task.get("schedule") == "custom":
                update_data["custom_schedule"] = req.custom_schedule
        
        if req.start_date is not None:
            update_data["start_date"] = req.start_date
        
        current_time = current_timestamp()
        update_data["updatedAt"] = current_time
        
        if len(update_data) == 1 and "updatedAt" in update_data:
            return None, "No valid fields provided for update"
        
        task_ref.update(update_data)
        
        # Check for recurring task creation
        new_status = req.status.lower() if req.status else prev_status
        if prev_status != "completed" and new_status == "completed" and existing_task.get("scheduled"):
            updated_task = task_ref.get()
            self.create_task_with_params(updated_task, completion_time=current_time)
        
        return Task.from_dict(task_ref.get()), None
    
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