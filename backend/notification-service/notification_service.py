# backend/notification-service/notification_service.py
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, current_timestamp, days_until_deadline
from models import Notification

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self):
        self.db = get_db_reference()
        self.notifications_ref = get_db_reference("notifications")
        self.notification_sent_ref = get_db_reference("notificationsSent")
    
    def create_notification(self, user_id, item_id, item_data, days_until, is_subtask=False, parent_task_title=None):
        """Create a notification in Firebase"""
        try:
            user_notifications_ref = self.notifications_ref.child(user_id)
            new_notification_ref = user_notifications_ref.push()
            notification_id = new_notification_ref.key
            
            # Determine message
            if days_until < 1:
                if days_until < 0:
                    time_msg = "overdue"
                else:
                    hours_until = int(days_until * 24)
                    time_msg = f"due in {hours_until} hours"
            else:
                time_msg = f"due in {int(days_until)} days"
            
            # Create notification
            if is_subtask:
                notification_type = "subtask_deadline_reminder"
                title = "Subtask Deadline Approaching"
                message = f"'{item_data.get('title', 'Untitled')}' is {time_msg}"
                item_id_field = "subTaskId"
            else:
                notification_type = "task_deadline_reminder"
                title = "Task Deadline Approaching"
                message = f"'{item_data.get('title', 'Untitled')}' is {time_msg}"
                item_id_field = "taskId"
            
            notification_data = {
                "notificationId": notification_id,
                "userId": user_id,
                item_id_field: item_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "taskTitle": item_data.get('title', 'Untitled'),
                "taskDeadline": item_data.get('deadline'),
                "daysUntilDeadline": days_until,
                "read": False,
                "createdAt": current_timestamp(),
                "readAt": None
            }
            
            if is_subtask and 'taskId' in item_data:
                notification_data["taskId"] = item_data["taskId"]
                if parent_task_title:
                    notification_data["parentTaskTitle"] = parent_task_title
            
            new_notification_ref.set(notification_data)
            logger.info(f"Created notification for user {user_id}")
            return notification_id
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            return None
    
    def get_user_notifications(self, user_id):
        """Get all notifications for a user"""
        user_notifications_ref = self.notifications_ref.child(user_id)
        all_notifications = user_notifications_ref.get() or {}
        
        notifications_list = [Notification.from_dict(n) for n in all_notifications.values()]
        notifications_list.sort(key=lambda x: x.created_at, reverse=True)
        
        return notifications_list
    
    def get_unread_notifications(self, user_id):
        """Get unread notifications for a user"""
        user_notifications_ref = self.notifications_ref.child(user_id)
        all_notifications = user_notifications_ref.get() or {}
        
        unread = [
            Notification.from_dict(n) for n in all_notifications.values()
            if not n.get('read', False)
        ]
        unread.sort(key=lambda x: x.created_at, reverse=True)
        
        return unread
    
    def mark_notification_read(self, user_id, notification_id):
        """Mark a notification as read"""
        notification_ref = self.notifications_ref.child(user_id).child(notification_id)
        notification = notification_ref.get()
        
        if not notification:
            return None, "Notification not found"
        
        notification_ref.update({
            "read": True,
            "readAt": current_timestamp()
        })
        
        return Notification.from_dict(notification_ref.get()), None
    
    def delete_notification(self, user_id, notification_id):
        """Delete a notification"""
        notification_ref = self.notifications_ref.child(user_id).child(notification_id)
        notification = notification_ref.get()
        
        if not notification:
            return False, "Notification not found"
        
        notification_ref.delete()
        return True, None
    
    def mark_all_notifications_read(self, user_id):
        """Mark all notifications as read for a user"""
        user_notifications_ref = self.notifications_ref.child(user_id)
        all_notifications = user_notifications_ref.get() or {}
        
        current_time = current_timestamp()
        update_count = 0
        
        for notification_id, notification in all_notifications.items():
            if not notification.get('read', False):
                notification_ref = user_notifications_ref.child(notification_id)
                notification_ref.update({
                    "read": True,
                    "readAt": current_time
                })
                update_count += 1
        
        return update_count
    
    def should_send_notification(self, task_id, user_id, days_until, reminder_times):
        """Check if notification should be sent"""
        # Check if days_until matches any reminder time
        matched_reminder_day = None
        for reminder_day in reminder_times:
            if abs(days_until - reminder_day) < 0.5:
                matched_reminder_day = reminder_day
                break
        
        if not matched_reminder_day:
            return False
        
        # Check if already sent
        try:
            notification_key = f"{task_id}_{user_id}_{matched_reminder_day}"
            sent_ref = self.notification_sent_ref.child(notification_key)
            sent_record = sent_ref.get()
            
            current_time = current_timestamp()
            
            if sent_record:
                sent_timestamp = sent_record.get('sentAt', 0)
                if current_time - sent_timestamp < 86400:  # 24 hours
                    return False
            
            return matched_reminder_day
        except Exception as e:
            logger.error(f"Error checking sent notifications: {str(e)}")
            return False
    
    def mark_notification_sent(self, task_id, user_id, matched_reminder_day):
        """Mark that a notification has been sent"""
        try:
            notification_key = f"{task_id}_{user_id}_{matched_reminder_day}"
            sent_ref = self.notification_sent_ref.child(notification_key)
            sent_ref.set({
                'taskId': task_id,
                'userId': user_id,
                'reminderDay': matched_reminder_day,
                'sentAt': current_timestamp()
            })
        except Exception as e:
            logger.error(f"Error marking notification as sent: {str(e)}")

    def create_task_update_notification(self, user_id, item_id, task_title, old_status, new_status, is_subtask=False, parent_task_title=None):
        """Create a notification for task status update"""
        try:
            user_notifications_ref = self.notifications_ref.child(user_id)
            new_notification_ref = user_notifications_ref.push()
            notification_id = new_notification_ref.key

            # Format status for display
            def format_status(status):
                return status.replace('_', ' ').title()

            # Create notification
            if is_subtask:
                notification_type = "subtask_status_update"
                title = "Subtask Status Updated"
                if parent_task_title:
                    message = f"'{task_title}' (in {parent_task_title}) status changed from {format_status(old_status)} to {format_status(new_status)}"
                else:
                    message = f"'{task_title}' status changed from {format_status(old_status)} to {format_status(new_status)}"
                item_id_field = "subTaskId"
            else:
                notification_type = "task_status_update"
                title = "Task Status Updated"
                message = f"'{task_title}' status changed from {format_status(old_status)} to {format_status(new_status)}"
                item_id_field = "taskId"

            notification_data = {
                "notificationId": notification_id,
                "userId": user_id,
                item_id_field: item_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "taskTitle": task_title,
                "oldStatus": old_status,
                "newStatus": new_status,
                "read": False,
                "createdAt": current_timestamp(),
                "readAt": None
            }

            if is_subtask and parent_task_title:
                notification_data["parentTaskTitle"] = parent_task_title

            new_notification_ref.set(notification_data)
            logger.info(f"Created task update notification for user {user_id}")
            return notification_id
        except Exception as e:
            logger.error(f"Failed to create task update notification: {str(e)}")
            return None

    def check_duplicate_update_notification(self, user_id, item_id, new_status, is_subtask=False):
        """Check if a similar notification was recently sent to prevent duplicates"""
        try:
            user_notifications_ref = self.notifications_ref.child(user_id)
            all_notifications = user_notifications_ref.get() or {}

            current_time = current_timestamp()
            time_window = 300  # 5 minutes in seconds

            for notification in all_notifications.values():
                # Check if it's a status update notification
                notification_type = notification.get('type', '')
                if not (notification_type == 'task_status_update' or notification_type == 'subtask_status_update'):
                    continue

                # Check if it's for the same item
                item_id_field = 'subTaskId' if is_subtask else 'taskId'
                if notification.get(item_id_field) != item_id:
                    continue

                # Check if it's the same status change
                if notification.get('newStatus') != new_status:
                    continue

                # Check if it was created within the time window
                created_at = notification.get('createdAt', 0)
                if current_time - created_at < time_window:
                    return True  # Duplicate found

            return False  # No duplicate
        except Exception as e:
            logger.error(f"Error checking duplicate notification: {str(e)}")
            return False

    def create_comment_notification(self, user_id, item_id, task_title, comment_text, commenter_name, commenter_id,
                                    task_deadline=None, is_subtask=False, parent_task_title=None):
        """Create a notification for a new comment on a task"""
        try:
            user_notifications_ref = self.notifications_ref.child(user_id)
            new_notification_ref = user_notifications_ref.push()
            notification_id = new_notification_ref.key

            # Truncate comment if too long for notification
            max_comment_length = 100
            comment_preview = comment_text if len(comment_text) <= max_comment_length else comment_text[:max_comment_length] + "..."

            # Create notification
            if is_subtask:
                notification_type = "subtask_comment_notification"
                title = "New Comment on Subtask"
                if parent_task_title:
                    message = f"{commenter_name} commented on '{task_title}' (in {parent_task_title}): {comment_preview}"
                else:
                    message = f"{commenter_name} commented on '{task_title}': {comment_preview}"
                item_id_field = "subTaskId"
            else:
                notification_type = "task_comment_notification"
                title = "New Comment on Task"
                message = f"{commenter_name} commented on '{task_title}': {comment_preview}"
                item_id_field = "taskId"

            notification_data = {
                "notificationId": notification_id,
                "userId": user_id,
                item_id_field: item_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "taskTitle": task_title,
                "taskDeadline": task_deadline or 0,
                "daysUntilDeadline": 0,
                "commentText": comment_text,
                "commenterName": commenter_name,
                "commenterId": commenter_id,
                "read": False,
                "createdAt": current_timestamp(),
                "readAt": None
            }

            if is_subtask and parent_task_title:
                notification_data["parentTaskTitle"] = parent_task_title

            new_notification_ref.set(notification_data)
            logger.info(f"Created comment notification for user {user_id}")
            return notification_id
        except Exception as e:
            logger.error(f"Failed to create comment notification: {str(e)}")
            return None

    def check_duplicate_comment_notification(self, user_id, item_id, commenter_id, is_subtask=False):
        """Check if a similar comment notification was recently sent to prevent duplicates"""
        try:
            user_notifications_ref = self.notifications_ref.child(user_id)
            all_notifications = user_notifications_ref.get() or {}

            current_time = current_timestamp()
            time_window = 60  # 1 minute in seconds - shorter window for comments

            for notification in all_notifications.values():
                # Check if it's a comment notification
                notification_type = notification.get('type', '')
                if not (notification_type == 'task_comment_notification' or notification_type == 'subtask_comment_notification'):
                    continue

                # Check if it's for the same item
                item_id_field = 'subTaskId' if is_subtask else 'taskId'
                if notification.get(item_id_field) != item_id:
                    continue

                # Check if it's from the same commenter
                if notification.get('commenterId') != commenter_id:
                    continue

                # Check if it was created within the time window
                created_at = notification.get('createdAt', 0)
                if current_time - created_at < time_window:
                    return True  # Duplicate found

            return False  # No duplicate
        except Exception as e:
            logger.error(f"Error checking duplicate comment notification: {str(e)}")
            return False

    def create_deadline_extension_request_notification(self, owner_id: str, item_id: str,
                                                        item_title: str, requester_id: str,
                                                        item_type: str, extension_request_id: str):  # ADD this parameter
        """Create notification for deadline extension request"""
        import uuid

        notification_id = str(uuid.uuid4())
        current_time = current_timestamp()
        
        # Get requester name
        requester_name = self._get_user_name(requester_id)
        
        notification_data = {
            "notificationId": notification_id,
            "userId": owner_id,
            "type": "deadline_extension_request",
            "itemId": item_id,
            "itemType": item_type,
            "itemTitle": item_title,
            "message": f"{requester_name} has requested a deadline extension for {item_type}: {item_title}",
            "requesterId": requester_id,
            "requesterName": requester_name,
            "extensionRequestId": extension_request_id,  
            "actionable": True,
            "read": False,
            "createdAt": current_time,
            "actionable": True
        }
        
        self.notifications_ref.child(owner_id).child(notification_id).set(notification_data)
        return notification_id
    
    def create_deadline_extension_response_notification(self, requester_id: str, item_id: str,
                                                        item_type: str, item_title: str,
                                                        status: str, rejection_reason: str = None):
        """Create notification for deadline extension response"""
        import uuid

        notification_id = str(uuid.uuid4())
        current_time = current_timestamp()
        
        if status == "approved":
            message = f"Your deadline extension request for {item_type}: {item_title} has been approved"
        else:
            message = f"Your deadline extension request for {item_type}: {item_title} has been rejected"
            if rejection_reason:
                message += f" - Reason: {rejection_reason}"
        
        notification_data = {
            "notificationId": notification_id,
            "userId": requester_id,
            "type": "deadline_extension_response",
            "itemId": item_id,
            "itemType": item_type,
            "itemTitle": item_title,
            "message": message,
            "status": status,
            "rejectionReason": rejection_reason,
            "read": False,
            "createdAt": current_time,
            "actionable": False
        }
        
        self.notifications_ref.child(requester_id).child(notification_id).set(notification_data)
        return notification_id

    def create_deadline_changed_notification(self, user_id: str, item_id: str,
                                            item_type: str, item_title: str,
                                            new_deadline: int):
        """Create notification for deadline change (for all collaborators)"""
        import uuid
        from datetime import datetime

        notification_id = str(uuid.uuid4())
        current_time = current_timestamp()
        
        # Format the new deadline
        deadline_str = datetime.fromtimestamp(new_deadline).strftime("%B %d, %Y")
        
        notification_data = {
            "notificationId": notification_id,
            "userId": user_id,
            "type": "deadline_changed",
            "itemId": item_id,
            "itemType": item_type,
            "itemTitle": item_title,
            "message": f"The deadline for {item_type}: {item_title} has been extended to {deadline_str}",
            "newDeadline": new_deadline,
            "read": False,
            "createdAt": current_time,
            "actionable": False
        }
        
        self.notifications_ref.child(user_id).child(notification_id).set(notification_data)
        return notification_id

    def _get_user_name(self, user_id: str):
        """Helper to get user name from user_id"""
        users_ref = get_db_reference("users") 
        user_data = users_ref.child(user_id).get()
        if user_data:
            return user_data.get("name", "Unknown User")
        return "Unknown User"