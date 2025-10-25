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
    comment_text: Optional[str] = None
    commenter_name: Optional[str] = None
    commenter_id: Optional[str] = None
    # Extension request fields
    actionable: Optional[bool] = None
    extension_request_id: Optional[str] = None
    requester_id: Optional[str] = None
    requester_name: Optional[str] = None
    item_id: Optional[str] = None
    item_type: Optional[str] = None
    item_title: Optional[str] = None
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    new_deadline: Optional[int] = None
    
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
            new_status=data.get("newStatus"),
            comment_text=data.get("commentText"),
            commenter_name=data.get("commenterName"),
            commenter_id=data.get("commenterId"),
            # Extension request fields
            actionable=data.get("actionable"),
            extension_request_id=data.get("extensionRequestId"),
            requester_id=data.get("requesterId"),
            requester_name=data.get("requesterName"),
            item_id=data.get("itemId"),
            item_type=data.get("itemType"),
            item_title=data.get("itemTitle"),
            status=data.get("status"),
            rejection_reason=data.get("rejectionReason"),
            new_deadline=data.get("newDeadline")
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

        # Add optional fields if they exist
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
        if self.comment_text:
            result["commentText"] = self.comment_text
        if self.commenter_name:
            result["commenterName"] = self.commenter_name
        if self.commenter_id:
            result["commenterId"] = self.commenter_id
        
        # Extension request fields
        if self.actionable is not None:
            result["actionable"] = self.actionable
        if self.extension_request_id:
            result["extensionRequestId"] = self.extension_request_id
        if self.requester_id:
            result["requesterId"] = self.requester_id
        if self.requester_name:
            result["requesterName"] = self.requester_name
        if self.item_id:
            result["itemId"] = self.item_id
        if self.item_type:
            result["itemType"] = self.item_type
        if self.item_title:
            result["itemTitle"] = self.item_title
        if self.status:
            result["status"] = self.status
        if self.rejection_reason:
            result["rejectionReason"] = self.rejection_reason
        if self.new_deadline:
            result["newDeadline"] = self.new_deadline

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