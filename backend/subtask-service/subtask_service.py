# backend/subtask-service/subtask_service.py
import sys
import os
import calendar
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, current_timestamp, validate_epoch_timestamp
from models import Subtask, CreateSubtaskRequest, UpdateSubtaskRequest

class SubtaskService:
    """Service for managing subtasks"""
    
    def __init__(self):
        self.subtasks_ref = get_db_reference("subtasks")
        self.tasks_ref = get_db_reference("tasks")
    
    def validate_status(self, status):
        allowed_statuses = ["ongoing", "unassigned", "under_review", "completed"]
        return status.lower() in allowed_statuses
    
    def calculate_new_start_date(self, old_start_date, schedule, custom_schedule=None):
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
    
    def create_subtask_with_params(self, subtask_data):
        now = current_timestamp()
        new_start_date = self.calculate_new_start_date(
            subtask_data.get("start_date", now),
            subtask_data.get("schedule"),
            subtask_data.get("custom_schedule")
        )
        active_flag = True if new_start_date <= now else False
        
        new_subtask_ref = self.subtasks_ref.push()
        new_subtask_data = dict(subtask_data)
        
        new_subtask_data.update({
            "subTaskId": new_subtask_ref.key,
            "start_date": new_start_date,
            "active": active_flag,
            "status": "ongoing",
            "createdAt": now,
            "updatedAt": now
        })
        
        new_subtask_ref.set(new_subtask_data)
    
    def create_subtask(self, req: CreateSubtaskRequest):
    # Validate parent task exists
        parent_task = self.tasks_ref.child(req.task_id).get()
        if not parent_task:
            return None, "Parent task not found"
        
        current_time = current_timestamp()
        owner_id = req.owner_id if req.owner_id else req.creator_id
        start_date = req.start_date if req.start_date else current_time
        
        # Auto-update status to "ongoing" if owner is different from creator
        status = req.status
        if owner_id != req.creator_id:
            status = "ongoing"
        
        new_subtask_ref = self.subtasks_ref.push()
        subtask_id = new_subtask_ref.key
        
        subtask = Subtask(
            subtask_id=subtask_id,
            title=req.title,
            creator_id=req.creator_id,
            deadline=req.deadline,
            status=status,  # Use the potentially updated status
            notes=req.notes,
            attachments=req.attachments,
            collaborators=req.collaborators,
            task_id=req.task_id,
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
        
        new_subtask_ref.set(subtask.to_dict())
        return subtask, None

    
    def get_all_subtasks(self):
        all_subtasks = self.subtasks_ref.get() or {}
        now = current_timestamp()
        
        subtasks = []
        for subtask_data in all_subtasks.values():
            start_date = subtask_data.get("start_date")
            if start_date is not None:
                if now >= start_date:
                    if not subtask_data.get("active", False):
                        self.subtasks_ref.child(subtask_data['subTaskId']).update({"active": True})
                    subtask_data["active"] = True
                else:
                    subtask_data["active"] = False
            
            subtasks.append(Subtask.from_dict(subtask_data))
        
        return subtasks
    
    def get_subtask_by_id(self, subtask_id):
        subtask_ref = self.subtasks_ref.child(subtask_id)
        subtask_data = subtask_ref.get()
        
        if not subtask_data:
            return None, "Subtask not found"
        
        now = current_timestamp()
        start_date = subtask_data.get("start_date")
        if start_date is not None:
            if now >= start_date and not subtask_data.get("active", False):
                subtask_ref.update({"active": True})
                subtask_data["active"] = True
            elif now < start_date:
                subtask_data["active"] = False
        
        return Subtask.from_dict(subtask_data), None
    
    def update_subtask(self, req: UpdateSubtaskRequest):
        subtask_ref = self.subtasks_ref.child(req.subtask_id)
        existing_subtask = subtask_ref.get()
        
        if not existing_subtask:
            return None, "Subtask not found"
        
        prev_status = existing_subtask.get("status", "").lower()
        
        update_data = {}
        
        if req.title is not None:
            if not req.title.strip():
                return None, "Title cannot be empty"
            update_data["title"] = req.title
        
        if req.deadline is not None:
            update_data["deadline"] = req.deadline
        
        if req.status is not None:
            update_data["status"] = req.status.lower()
        
        if req.task_id is not None:
            parent_task = self.tasks_ref.child(req.task_id).get()
            if not parent_task:
                return None, "Parent task not found"
            update_data["taskId"] = req.task_id
        
        if req.priority is not None:
            update_data["priority"] = req.priority
        
        if req.notes is not None:
            update_data["notes"] = req.notes
        
        if req.attachments is not None:
            update_data["attachments"] = req.attachments
        
        if req.collaborators is not None:
            update_data["collaborators"] = req.collaborators
        
        # Handle owner change and auto-update status
        if req.owner_id is not None:
            update_data["ownerId"] = req.owner_id
            # Get the creator ID from existing subtask
            creator_id = existing_subtask.get("creatorId", "")
            # If owner is being changed to someone other than creator, set status to ongoing
            if req.owner_id != creator_id:
                update_data["status"] = "ongoing"
        
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
        
        if req.start_date is not None:
            update_data["start_date"] = req.start_date
        
        update_data["updatedAt"] = current_timestamp()
        
        if len(update_data) == 1:
            return None, "No valid fields provided for update"
        
        subtask_ref.update(update_data)
        
        # Check for recurring subtask
        new_status = update_data.get("status", prev_status)
        if prev_status != "completed" and new_status == "completed" and existing_subtask.get("scheduled"):
            updated_subtask = subtask_ref.get()
            self.create_subtask_with_params(updated_subtask)
        
        return Subtask.from_dict(subtask_ref.get()), None

    
    def delete_subtask(self, subtask_id):
        subtask_ref = self.subtasks_ref.child(subtask_id)
        existing_subtask = subtask_ref.get()
        
        if not existing_subtask:
            return False, "Subtask not found"
        
        subtask_ref.delete()
        return True, None
    
    def get_subtasks_by_task(self, task_id):
        all_subtasks = self.subtasks_ref.get() or {}
        now = current_timestamp()
        
        filtered = []
        for subtask_data in all_subtasks.values():
            if subtask_data.get("taskId") == task_id:
                start_date = subtask_data.get("start_date")
                if start_date is not None:
                    if now >= start_date:
                        if not subtask_data.get("active", False):
                            self.subtasks_ref.child(subtask_data['subTaskId']).update({"active": True})
                        subtask_data["active"] = True
                    else:
                        subtask_data["active"] = False
                
                filtered.append(Subtask.from_dict(subtask_data))
        
        return filtered