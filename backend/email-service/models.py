# backend/email-service/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class EmailRequest:
    """Email request data model"""
    to_email: str
    task_title: str
    task_deadline: int
    days_until_deadline: float
    task_notes: str = ""
    is_subtask: bool = False
    parent_task_title: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create EmailRequest from dictionary"""
        return cls(
            to_email=data.get("toEmail", ""),
            task_title=data.get("taskTitle", ""),
            task_deadline=data.get("taskDeadline", 0),
            days_until_deadline=data.get("daysUntilDeadline", 0),
            task_notes=data.get("taskNotes", ""),
            is_subtask=data.get("isSubtask", False),
            parent_task_title=data.get("parentTaskTitle")
        )
    
    def validate(self):
        """Validate email request data"""
        errors = []
        if not self.to_email:
            errors.append("toEmail is required")
        if not self.task_title:
            errors.append("taskTitle is required")
        if not self.task_deadline:
            errors.append("taskDeadline is required")
        if self.days_until_deadline is None:
            errors.append("daysUntilDeadline is required")
        return errors