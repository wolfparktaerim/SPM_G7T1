# backend/notification-service/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Notification:
    """Notification data model"""
    notification_id: str
    user_id: str
    notification_type: str
    title: str
    message: str
    task_title: str
    task_deadline: int
    days_until_deadline: float
    read: bool
    created_at: int
    read_at: Optional[int] = None
    task_id: Optional[str] = None
    subtask_id: Optional[str] = None
    parent_task_title: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Notification from dictionary"""
        return cls(
            notification_id=data.get("notificationId", ""),
            user_id=data.get("userId", ""),
            notification_type=data.get("type", ""),
            title=data.get("title", ""),
            message=data.get("message", ""),
            task_title=data.get("taskTitle", ""),
            task_deadline=data.get("taskDeadline", 0),
            days_until_deadline=data.get("daysUntilDeadline", 0),
            read=data.get("read", False),
            created_at=data.get("createdAt", 0),
            read_at=data.get("readAt"),
            task_id=data.get("taskId"),
            subtask_id=data.get("subTaskId"),
            parent_task_title=data.get("parentTaskTitle"),
            old_status=data.get("oldStatus"),
            new_status=data.get("newStatus")
        )
    
    def to_dict(self):
        """Convert Notification to dictionary"""
        result = {
            "notificationId": self.notification_id,
            "userId": self.user_id,
            "type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "taskTitle": self.task_title,
            "taskDeadline": self.task_deadline,
            "daysUntilDeadline": self.days_until_deadline,
            "read": self.read,
            "createdAt": self.created_at,
            "readAt": self.read_at
        }

        if self.task_id:
            result["taskId"] = self.task_id
        if self.subtask_id:
            result["subTaskId"] = self.subtask_id
        if self.parent_task_title:
            result["parentTaskTitle"] = self.parent_task_title
        if self.old_status:
            result["oldStatus"] = self.old_status
        if self.new_status:
            result["newStatus"] = self.new_status

        return result

@dataclass
class NotificationPreferences:
    """User notification preferences"""
    user_id: str
    enabled: bool
    task_deadline_reminders: bool
    task_update_reminders: bool
    task_comment_notifications: bool
    channel: str
    reminder_times: list

    @classmethod
    def from_dict(cls, data: dict, user_id: str):
        return cls(
            user_id=user_id,
            enabled=data.get("enabled", False),
            task_deadline_reminders=data.get("taskDeadlineReminders", False),
            task_update_reminders=data.get("taskUpdateReminders", True),
            task_comment_notifications=data.get("taskCommentNotifications", True),
            channel=data.get("channel", "both"),
            reminder_times=data.get("reminderTimes", [])
        )