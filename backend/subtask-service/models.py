# backend/subtask-service/models.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Subtask:
    """Subtask data model"""
    subtask_id: str
    title: str
    creator_id: str
    deadline: int
    status: str
    notes: str
    attachments: List[str]
    collaborators: List[str]
    task_id: str
    owner_id: str
    priority: int
    created_at: int
    updated_at: int
    start_date: int
    active: bool
    scheduled: bool
    schedule: str
    custom_schedule: Optional[int] = None
    completed_at: Optional[int] = None
    started_at: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            subtask_id=data.get("subTaskId", ""),
            title=data.get("title", ""),
            creator_id=data.get("creatorId", ""),
            deadline=data.get("deadline", 0),
            status=data.get("status", "ongoing"),
            notes=data.get("notes", ""),
            attachments=data.get("attachments", []),
            collaborators=data.get("collaborators", []),
            task_id=data.get("taskId", ""),
            owner_id=data.get("ownerId", ""),
            priority=data.get("priority", 0),
            created_at=data.get("createdAt", 0),
            updated_at=data.get("updatedAt", 0),
            start_date=data.get("start_date", 0),
            active=data.get("active", True),
            scheduled=data.get("scheduled", False),
            schedule=data.get("schedule", "daily"),
            custom_schedule=data.get("custom_schedule"),
            completed_at=data.get("completedAt"),
            started_at=data.get("startedAt")
        )
    
    def to_dict(self):
        return {
            "subTaskId": self.subtask_id,
            "title": self.title,
            "creatorId": self.creator_id,
            "deadline": self.deadline,
            "status": self.status,
            "notes": self.notes,
            "attachments": self.attachments,
            "collaborators": self.collaborators,
            "taskId": self.task_id,
            "ownerId": self.owner_id,
            "priority": self.priority,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "start_date": self.start_date,
            "active": self.active,
            "scheduled": self.scheduled,
            "schedule": self.schedule,
            "custom_schedule": self.custom_schedule,
            "completedAt": self.completed_at,
            "startedAt": self.started_at
        }

@dataclass
class CreateSubtaskRequest:
    """Request model for creating a subtask"""
    title: str
    creator_id: str
    deadline: int
    task_id: str
    status: str = "ongoing"
    notes: str = ""
    attachments: List[str] = field(default_factory=list)
    collaborators: List[str] = field(default_factory=list)
    owner_id: str = ""
    priority: int = 0
    start_date: int = 0
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
            task_id=data.get("taskId", ""),
            status=data.get("status", "ongoing"),
            notes=data.get("notes", ""),
            attachments=data.get("attachments", []),
            collaborators=data.get("collaborators", []),
            owner_id=data.get("ownerId", ""),
            priority=data.get("priority", 0),
            start_date=data.get("start_date", 0),
            active=data.get("active", True),
            scheduled=data.get("scheduled", False),
            schedule=data.get("schedule", "daily"),
            custom_schedule=data.get("custom_schedule")
        )
    
    def validate(self):
        """Validate create subtask request"""
        errors = []
        if not self.title or not self.title.strip():
            errors.append("title is required and cannot be empty")
        if not self.creator_id:
            errors.append("creatorId is required")
        if not self.deadline:
            errors.append("deadline is required")
        if not self.task_id:
            errors.append("taskId is required")
        return errors

@dataclass
class UpdateSubtaskRequest:
    """Request model for updating a subtask"""
    subtask_id: str
    title: Optional[str] = None
    deadline: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    attachments: Optional[List[str]] = None
    collaborators: Optional[List[str]] = None
    owner_id: Optional[str] = None
    priority: Optional[int] = None
    start_date: Optional[int] = None
    active: Optional[bool] = None
    scheduled: Optional[bool] = None
    schedule: Optional[str] = None
    custom_schedule: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict, subtask_id: str):
        return cls(
            subtask_id=subtask_id,
            title=data.get("title"),
            deadline=data.get("deadline"),
            status=data.get("status"),
            notes=data.get("notes"),
            attachments=data.get("attachments"),
            collaborators=data.get("collaborators"),
            owner_id=data.get("ownerId"),
            priority=data.get("priority"),
            start_date=data.get("start_date"),
            active=data.get("active"),
            scheduled=data.get("scheduled"),
            schedule=data.get("schedule"),
            custom_schedule=data.get("custom_schedule")
        )