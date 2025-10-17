# backend/task-service/models.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Task:
    """Task data model"""
    task_id: str
    title: str
    creator_id: str
    deadline: int
    status: str
    notes: str
    attachments: List[str]
    collaborators: List[str]
    project_id: str
    owner_id: str
    priority: int
    created_at: int
    updated_at: int
    start_date: int
    active: bool
    scheduled: bool
    schedule: str
    custom_schedule: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Task from dictionary"""
        return cls(
            task_id=data.get("taskId", ""),
            title=data.get("title", ""),
            creator_id=data.get("creatorId", ""),
            deadline=data.get("deadline", 0),
            status=data.get("status", "ongoing"),
            notes=data.get("notes", ""),
            attachments=data.get("attachments", []),
            collaborators=data.get("collaborators", []),
            project_id=data.get("projectId", ""),
            owner_id=data.get("ownerId", ""),
            priority=data.get("priority", 0),
            created_at=data.get("createdAt", 0),
            updated_at=data.get("updatedAt", 0),
            start_date=data.get("start_date", 0),
            active=data.get("active", True),
            scheduled=data.get("scheduled", False),
            schedule=data.get("schedule", "daily"),
            custom_schedule=data.get("custom_schedule")
        )
    
    def to_dict(self):
        """Convert Task to dictionary"""
        return {
            "taskId": self.task_id,
            "title": self.title,
            "creatorId": self.creator_id,
            "deadline": self.deadline,
            "status": self.status,
            "notes": self.notes,
            "attachments": self.attachments,
            "collaborators": self.collaborators,
            "projectId": self.project_id,
            "ownerId": self.owner_id,
            "priority": self.priority,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "start_date": self.start_date,
            "active": self.active,
            "scheduled": self.scheduled,
            "schedule": self.schedule,
            "custom_schedule": self.custom_schedule
        }

@dataclass
class CreateTaskRequest:
    """Request model for creating a task"""
    title: str
    creator_id: str
    deadline: int
    status: str = "ongoing"
    notes: str = ""
    attachments: List[str] = field(default_factory=list)
    collaborators: List[str] = field(default_factory=list)
    project_id: str = ""
    owner_id: Optional[str] = None
    priority: int = 0
    start_date: Optional[int] = None
    active: bool = True
    scheduled: bool = False
    schedule: str = "daily"
    custom_schedule: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            title=data.get("title", ""),
            creator_id=data.get("creatorId", ""),
            deadline=data.get("deadline", 0),
            status=data.get("status", "ongoing"),
            notes=data.get("notes", ""),
            attachments=data.get("attachments", []),
            collaborators=data.get("collaborators", []),
            project_id=data.get("projectId", ""),
            owner_id=data.get("ownerId"),
            priority=data.get("priority", 0),
            start_date=data.get("start_date"),
            active=data.get("active", True),
            scheduled=data.get("scheduled", False),
            schedule=data.get("schedule", "daily"),
            custom_schedule=data.get("custom_schedule")
        )
    
    def validate(self):
        """Validate create task request"""
        errors = []
        if not self.title or not self.title.strip():
            errors.append("title is required and cannot be empty")
        if not self.creator_id:
            errors.append("creatorId is required")
        if not self.deadline:
            errors.append("deadline is required")
        if self.schedule == "custom" and self.custom_schedule is None:
            errors.append("custom_schedule is required when schedule is 'custom'")
        return errors

@dataclass
class UpdateTaskRequest:
    """Request model for updating a task"""
    task_id: str
    title: Optional[str] = None
    deadline: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[List[str]] = None
    collaborators: Optional[List[str]] = None
    project_id: Optional[str] = None
    owner_id: Optional[str] = None
    priority: Optional[int] = None
    start_date: Optional[int] = None
    active: Optional[bool] = None
    scheduled: Optional[bool] = None
    schedule: Optional[str] = None
    custom_schedule: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict, task_id: str):
        return cls(
            task_id=task_id,
            title=data.get("title"),
            deadline=data.get("deadline"),
            status=data.get("status"),
            notes=data.get("notes"),
            attachments=data.get("attachments"),
            collaborators=data.get("collaborators"),
            project_id=data.get("projectId"),
            owner_id=data.get("ownerId"),
            priority=data.get("priority"),
            start_date=data.get("start_date"),
            active=data.get("active"),
            scheduled=data.get("scheduled"),
            schedule=data.get("schedule"),
            custom_schedule=data.get("custom_schedule")
        )