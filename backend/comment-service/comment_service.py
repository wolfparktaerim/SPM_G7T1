# backend/comment-service/comment_service.py

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, current_timestamp

class CommentService:
    """Service for managing comments"""
    
    def __init__(self):
        self.tasks_ref = get_db_reference("tasks")
        self.subtasks_ref = get_db_reference("subtasks")
    
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
