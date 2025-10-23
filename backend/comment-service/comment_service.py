# backend/comment-service/comment_service.py

import sys
import os
import logging
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, current_timestamp

logger = logging.getLogger(__name__)

class CommentService:
    """Service for managing comments"""

    def __init__(self):
        self.tasks_ref = get_db_reference("tasks")
        self.subtasks_ref = get_db_reference("subtasks")
        self.users_ref = get_db_reference("users")
        self.notification_prefs_ref = get_db_reference("notificationPreferences")
        self.notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:6004")
    
    def create_comment(self, comment_data):
        """
        Create a new comment thread or append to existing thread
        
        Args:
            comment_data: dict with keys:
                - comment: str
                - user_id: str
                - creation_date: int (epoch timestamp)
                - mention: list of str (user IDs)
                - type: str ("task" or "subtask")
                - parent_id: str (task_id or subtask_id)
        
        Returns:
            tuple: (comment_thread_data, error)
        """
        # Validate required fields
        required_fields = ['comment', 'user_id', 'creation_date', 'mention', 'type', 'parent_id']
        for field in required_fields:
            if field not in comment_data:
                return None, f"Missing required field: {field}"
        
        comment_text = comment_data['comment']
        user_id = comment_data['user_id']
        creation_date = comment_data['creation_date']
        mention = comment_data['mention']
        comment_type = comment_data['type']
        parent_id = comment_data['parent_id']
        
        # Validate type
        if comment_type not in ['task', 'subtask']:
            return None, "Type must be either 'task' or 'subtask'"
        
        # Select appropriate reference based on type
        if comment_type == 'task':
            parent_ref = self.tasks_ref.child(parent_id)
        else:
            parent_ref = self.subtasks_ref.child(parent_id)
        
        # Check if parent exists
        parent_data = parent_ref.get()
        if not parent_data:
            return None, f"{comment_type.capitalize()} not found"
        
        # Get existing comment threads or initialize empty list
        comment_threads = parent_data.get('comment_thread', [])
        
        # Create new comment entry [user_id, comment_text, timestamp]
        new_comment = [user_id, comment_text, creation_date]
        
        # Create new comment thread object
        new_thread = {
            'active': True,
            'comments': [new_comment],
            'mention': mention,
            'creation_date': creation_date
        }
        
        # Append to comment threads
        comment_threads.append(new_thread)
        
        # Update parent with new comment thread
        parent_ref.update({'comment_thread': comment_threads})

        # Send notifications after successfully creating comment
        self.send_comment_notifications(
            parent_id=parent_id,
            parent_data=parent_data,
            comment_type=comment_type,
            commenter_id=user_id,
            comment_text=comment_text,
            mentioned_users=mention
        )

        return new_thread, None
    
    def update_comment_thread(self, update_data):
        """
        Add a reply to an existing comment thread
        
        Args:
            update_data: dict with keys:
                - comment: str
                - user_id: str
                - creation_date: int (epoch timestamp)
                - type: str ("task" or "subtask")
                - parent_id: str (task_id or subtask_id)
                - thread_index: int (index of the comment thread to update)
                - mention: list of str (optional, additional user IDs to mention)
        
        Returns:
            tuple: (updated_thread_data, error)
        """
        # Validate required fields
        required_fields = ['comment', 'user_id', 'creation_date', 'type', 'parent_id', 'thread_index']
        for field in required_fields:
            if field not in update_data:
                return None, f"Missing required field: {field}"
        
        comment_text = update_data['comment']
        user_id = update_data['user_id']
        creation_date = update_data['creation_date']
        comment_type = update_data['type']
        parent_id = update_data['parent_id']
        thread_index = update_data['thread_index']
        mention = update_data.get('mention', [])
        
        # Validate type
        if comment_type not in ['task', 'subtask']:
            return None, "Type must be either 'task' or 'subtask'"
        
        # Select appropriate reference based on type
        if comment_type == 'task':
            parent_ref = self.tasks_ref.child(parent_id)
        else:
            parent_ref = self.subtasks_ref.child(parent_id)
        
        # Check if parent exists
        parent_data = parent_ref.get()
        if not parent_data:
            return None, f"{comment_type.capitalize()} not found"
        
        # Get existing comment threads
        comment_threads = parent_data.get('comment_thread', [])
        
        # Validate thread index
        if thread_index < 0 or thread_index >= len(comment_threads):
            return None, f"Invalid thread_index: {thread_index}"
        
        # Get the specific thread
        thread = comment_threads[thread_index]
        
        # Add new comment to thread
        new_comment = [user_id, comment_text, creation_date]
        thread['comments'].append(new_comment)
        
        # Update mentions if provided
        if mention:
            # Merge new mentions with existing ones (avoid duplicates)
            existing_mentions = set(thread.get('mention', []))
            new_mentions = set(mention)
            thread['mention'] = list(existing_mentions.union(new_mentions))

        # Update the thread in the list
        comment_threads[thread_index] = thread

        # Update parent with modified comment threads
        parent_ref.update({'comment_thread': comment_threads})

        # Send notifications after successfully adding reply
        # Combine existing mentions with new mentions for notification
        all_mentioned_users = list(set(thread.get('mention', [])))
        self.send_comment_notifications(
            parent_id=parent_id,
            parent_data=parent_data,
            comment_type=comment_type,
            commenter_id=user_id,
            comment_text=comment_text,
            mentioned_users=all_mentioned_users
        )

        return thread, None
    
    def archive_comment_thread(self, archive_data):
        """
        Archive a comment thread by setting active to False
        
        Args:
            archive_data: dict with keys:
                - type: str ("task" or "subtask")
                - parent_id: str (task_id or subtask_id)
                - thread_index: int (index of the comment thread to archive)
        
        Returns:
            tuple: (updated_thread_data, error)
        """
        # Validate required fields
        required_fields = ['type', 'parent_id', 'thread_index']
        for field in required_fields:
            if field not in archive_data:
                return None, f"Missing required field: {field}"
        
        comment_type = archive_data['type']
        parent_id = archive_data['parent_id']
        thread_index = archive_data['thread_index']
        
        # Validate type
        if comment_type not in ['task', 'subtask']:
            return None, "Type must be either 'task' or 'subtask'"
        
        # Select appropriate reference based on type
        if comment_type == 'task':
            parent_ref = self.tasks_ref.child(parent_id)
        else:
            parent_ref = self.subtasks_ref.child(parent_id)
        
        # Check if parent exists
        parent_data = parent_ref.get()
        if not parent_data:
            return None, f"{comment_type.capitalize()} not found"
        
        # Get existing comment threads
        comment_threads = parent_data.get('comment_thread', [])
        
        # Validate thread index
        if thread_index < 0 or thread_index >= len(comment_threads):
            return None, f"Invalid thread_index: {thread_index}"
        
        # Get the specific thread and set active to False
        thread = comment_threads[thread_index]
        thread['active'] = False
        
        # Update the thread in the list
        comment_threads[thread_index] = thread
        
        # Update parent with modified comment threads
        parent_ref.update({'comment_thread': comment_threads})
        
        return thread, None
    
    def get_comment_threads(self, parent_id, comment_type):
        """
        Get all comment threads for a task or subtask
        
        Args:
            parent_id: str (task_id or subtask_id)
            comment_type: str ("task" or "subtask")
        
        Returns:
            tuple: (list of comment threads, error)
        """
        # Validate type
        if comment_type not in ['task', 'subtask']:
            return None, "Type must be either 'task' or 'subtask'"
        
        # Select appropriate reference based on type
        if comment_type == 'task':
            parent_ref = self.tasks_ref.child(parent_id)
        else:
            parent_ref = self.subtasks_ref.child(parent_id)
        
        # Check if parent exists
        parent_data = parent_ref.get()
        if not parent_data:
            return None, f"{comment_type.capitalize()} not found"
        
        # Get comment threads
        comment_threads = parent_data.get('comment_thread', [])
        
        return comment_threads, None

    def send_comment_notifications(self, parent_id, parent_data, comment_type, commenter_id, comment_text, mentioned_users):
        """
        Send notifications for a new comment

        Args:
            parent_id: str (task_id or subtask_id)
            parent_data: dict (task or subtask data)
            comment_type: str ("task" or "subtask")
            commenter_id: str (user ID of the person who commented)
            comment_text: str (the comment content)
            mentioned_users: list of str (user IDs mentioned in comment)
        """
        try:
            # Get task/subtask details
            task_title = parent_data.get('title', 'Untitled')
            task_deadline = parent_data.get('deadline')
            parent_task_title = None

            # For subtasks, get parent task info
            if comment_type == 'subtask':
                task_id = parent_data.get('taskId')
                if task_id:
                    task_data = self.tasks_ref.child(task_id).get()
                    if task_data:
                        parent_task_title = task_data.get('title')

            # Get commenter name (try 'name' first, then 'displayName', then email, then default)
            commenter_data = self.users_ref.child(commenter_id).get()
            if commenter_data:
                commenter_name = (
                    commenter_data.get('name') or
                    commenter_data.get('displayName') or
                    commenter_data.get('email', '').split('@')[0] or
                    'Unknown User'
                )
            else:
                commenter_name = 'Unknown User'

            # Determine recipients:
            # 1. Task owner and collaborators (if their taskCommentNotifications setting is enabled)
            # 2. Mentioned users (ALWAYS notified, even if taskCommentNotifications is disabled)

            owner_id = parent_data.get('owner_id') or parent_data.get('ownerId')
            collaborators = parent_data.get('collaborators', [])

            # Combine owner and collaborators
            assigned_users = set()
            if owner_id:
                assigned_users.add(owner_id)
            if collaborators:
                assigned_users.update(collaborators)

            # Recipients who should be notified
            recipients_to_notify = {}  # {user_id: {'channel': channel, 'email': email}}

            # Check notification preferences for assigned users
            for user_id in assigned_users:
                if user_id == commenter_id:
                    continue  # Don't notify the commenter

                # Get user's notification preferences
                prefs = self.notification_prefs_ref.child(user_id).get()
                if not prefs:
                    continue

                # Check if notifications are enabled and taskCommentNotifications is enabled
                if not prefs.get('enabled', False):
                    continue

                if not prefs.get('taskCommentNotifications', True):
                    # Skip if comment notifications are disabled, unless they're mentioned
                    if user_id not in mentioned_users:
                        continue

                # Get user email and channel preference
                user_data = self.users_ref.child(user_id).get()
                if user_data:
                    recipients_to_notify[user_id] = {
                        'channel': prefs.get('channel', 'both'),
                        'email': user_data.get('email', '')
                    }

            # Add mentioned users (always notify, even if taskCommentNotifications is disabled)
            for user_id in mentioned_users:
                if user_id == commenter_id:
                    continue  # Don't notify the commenter

                if user_id not in recipients_to_notify:
                    # Get user's notification preferences
                    prefs = self.notification_prefs_ref.child(user_id).get()
                    if not prefs or not prefs.get('enabled', False):
                        continue

                    # Get user email and channel preference
                    user_data = self.users_ref.child(user_id).get()
                    if user_data:
                        recipients_to_notify[user_id] = {
                            'channel': prefs.get('channel', 'both'),
                            'email': user_data.get('email', '')
                        }

            # If no one to notify, return early
            if not recipients_to_notify:
                logger.info(f"No recipients to notify for comment on {comment_type} {parent_id}")
                return

            # Prepare notification data
            recipient_ids = list(recipients_to_notify.keys())
            recipient_emails = {uid: info['email'] for uid, info in recipients_to_notify.items() if info['email']}

            # Determine channel - use 'both' if any user has 'both', otherwise use the most common
            channels = [info['channel'] for info in recipients_to_notify.values()]
            if 'both' in channels:
                channel = 'both'
            else:
                channel = max(set(channels), key=channels.count)

            notification_data = {
                'itemId': parent_id,
                'taskTitle': task_title,
                'commentText': comment_text,
                'commenterName': commenter_name,
                'commenterId': commenter_id,
                'recipientIds': recipient_ids,
                'channel': channel,
                'isSubtask': comment_type == 'subtask',
                'recipientEmails': recipient_emails
            }

            if parent_task_title:
                notification_data['parentTaskTitle'] = parent_task_title
            if task_deadline:
                notification_data['taskDeadline'] = task_deadline

            # Send notification request
            response = requests.post(
                f"{self.notification_service_url}/notifications/comment",
                json=notification_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Comment notifications sent: {result.get('notificationsSent', [])}")
            else:
                logger.error(f"Failed to send comment notifications: {response.text}")

        except Exception as e:
            logger.error(f"Error sending comment notifications: {str(e)}")
            # Don't fail the comment creation if notification fails
