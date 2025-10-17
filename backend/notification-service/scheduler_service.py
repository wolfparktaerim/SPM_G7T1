# backend/notification-service/scheduler_service.py
import sys
import os
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared import get_db_reference, days_until_deadline
from notification_service import NotificationService

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for scheduling deadline checks"""
    
    def __init__(self, email_service_url):
        self.tasks_ref = get_db_reference("tasks")
        self.subtasks_ref = get_db_reference("subtasks")
        self.preferences_ref = get_db_reference("notificationPreferences")
        self.users_ref = get_db_reference("users")
        self.notification_service = NotificationService()
        self.email_service_url = email_service_url
        self.scheduler = None
    
    def send_email_notification(self, user_email, task_data, days_until, is_subtask=False, parent_task_title=None):
        """Send email notification via email service"""
        try:
            payload = {
                "toEmail": user_email,
                "taskTitle": task_data.get('title', 'Untitled'),
                "taskDeadline": task_data.get('deadline'),
                "daysUntilDeadline": days_until,
                "taskNotes": task_data.get('notes', ''),
                "isSubtask": is_subtask
            }
            
            if is_subtask and parent_task_title:
                payload["parentTaskTitle"] = parent_task_title
            
            response = requests.post(
                f"{self.email_service_url}/email/send-task-reminder",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {user_email}")
                return True
            else:
                logger.error(f"Failed to send email to {user_email}: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending email to {user_email}: {str(e)}")
            return False
    
    def check_task_deadlines(self):
        """Check all tasks and subtasks and create notifications"""
        logger.info("Starting task and subtask deadline check...")
        
        try:
            all_tasks = self.tasks_ref.get() or {}
            all_subtasks = self.subtasks_ref.get() or {}
            all_preferences = self.preferences_ref.get() or {}
            all_users = self.users_ref.get() or {}
            
            notification_count = 0
            email_count = 0
            
            # Check tasks
            for task_id, task_data in all_tasks.items():
                if task_data.get('status', '').lower() == 'completed':
                    continue
                
                deadline = task_data.get('deadline')
                if not deadline:
                    continue
                
                days_until = days_until_deadline(deadline)
                
                if days_until < -1:
                    continue
                
                # Get users to notify
                users_to_notify = []
                owner_id = task_data.get('ownerId')
                if owner_id:
                    users_to_notify.append(owner_id)
                
                collaborators = task_data.get('collaborators', [])
                if isinstance(collaborators, list):
                    collaborators_without_owner = [c for c in collaborators if c != owner_id]
                    users_to_notify.extend(collaborators_without_owner)
                
                users_to_notify = list(set(users_to_notify))
                
                # Send notifications
                for user_id in users_to_notify:
                    user_prefs = all_preferences.get(user_id)
                    if not user_prefs:
                        continue
                    
                    if not user_prefs.get('enabled', False) or not user_prefs.get('taskDeadlineReminders', False):
                        continue
                    
                    channel = user_prefs.get('channel', 'both')
                    reminder_times = user_prefs.get('reminderTimes', [])
                    
                    if not reminder_times:
                        continue
                    
                    matched_reminder_day = self.notification_service.should_send_notification(
                        task_id, user_id, days_until, reminder_times
                    )
                    
                    if matched_reminder_day:
                        self.notification_service.mark_notification_sent(task_id, user_id, matched_reminder_day)
                        
                        if channel in ['in-app', 'both']:
                            notification_id = self.notification_service.create_notification(
                                user_id, task_id, task_data, days_until
                            )
                            if notification_id:
                                notification_count += 1
                        
                        if channel in ['email', 'both']:
                            user_data = all_users.get(user_id)
                            if user_data and user_data.get('email'):
                                email_sent = self.send_email_notification(
                                    user_data['email'],
                                    task_data,
                                    days_until
                                )
                                if email_sent:
                                    email_count += 1
            
            # Check subtasks
            for subtask_id, subtask_data in all_subtasks.items():
                if subtask_data.get('status', '').lower() == 'completed':
                    continue
                
                deadline = subtask_data.get('deadline')
                if not deadline:
                    continue
                
                days_until = days_until_deadline(deadline)
                
                if days_until < -1:
                    continue
                
                parent_task_id = subtask_data.get('taskId')
                parent_task_title = None
                if parent_task_id and parent_task_id in all_tasks:
                    parent_task_title = all_tasks[parent_task_id].get('title', 'Untitled')
                
                # Get users to notify
                users_to_notify = []
                owner_id = subtask_data.get('ownerId')
                if owner_id:
                    users_to_notify.append(owner_id)
                
                collaborators = subtask_data.get('collaborators', [])
                if isinstance(collaborators, list):
                    collaborators_without_owner = [c for c in collaborators if c != owner_id]
                    users_to_notify.extend(collaborators_without_owner)
                
                users_to_notify = list(set(users_to_notify))
                
                # Send notifications
                for user_id in users_to_notify:
                    user_prefs = all_preferences.get(user_id)
                    if not user_prefs:
                        continue
                    
                    if not user_prefs.get('enabled', False) or not user_prefs.get('taskDeadlineReminders', False):
                        continue
                    
                    channel = user_prefs.get('channel', 'both')
                    reminder_times = user_prefs.get('reminderTimes', [])
                    
                    if not reminder_times:
                        continue
                    
                    matched_reminder_day = self.notification_service.should_send_notification(
                        subtask_id, user_id, days_until, reminder_times
                    )
                    
                    if matched_reminder_day:
                        self.notification_service.mark_notification_sent(subtask_id, user_id, matched_reminder_day)
                        
                        if channel in ['in-app', 'both']:
                            notification_id = self.notification_service.create_notification(
                                user_id, subtask_id, subtask_data, days_until,
                                is_subtask=True, parent_task_title=parent_task_title
                            )
                            if notification_id:
                                notification_count += 1
                        
                        if channel in ['email', 'both']:
                            user_data = all_users.get(user_id)
                            if user_data and user_data.get('email'):
                                email_sent = self.send_email_notification(
                                    user_data['email'],
                                    subtask_data,
                                    days_until,
                                    is_subtask=True,
                                    parent_task_title=parent_task_title
                                )
                                if email_sent:
                                    email_count += 1
            
            logger.info(f"Deadline check completed. Created {notification_count} notifications, sent {email_count} emails.")
        
        except Exception as e:
            logger.error(f"Error during deadline check: {str(e)}")
    
    def start(self):
        """Start the background scheduler"""
        self.scheduler = BackgroundScheduler()
        
        # Run every 15 minutes
        self.scheduler.add_job(
            func=self.check_task_deadlines,
            trigger="interval",
            seconds=900,
            id="task_deadline_checker",
            name="Check task and subtask deadlines",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started. Running every 15 minutes.")
        
        # Run once on startup
        self.check_task_deadlines()
    
    def trigger_manually(self):
        """Manually trigger deadline check (for testing)"""
        self.check_task_deadlines()