# notification-service/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase configuration
JSON_PATH = os.getenv("JSON_PATH")
DATABASE_URL = os.getenv("DATABASE_URL")

cred = credentials.Certificate(JSON_PATH)
firebase_admin.initialize_app(cred, {
    "databaseURL": DATABASE_URL
})

# Utility functions
def current_timestamp():
    """Return current timestamp in epoch format"""
    return int(datetime.now(timezone.utc).timestamp())

def days_until_deadline(deadline_epoch):
    """Calculate days until deadline from current time"""
    current_time = current_timestamp()
    seconds_until_deadline = deadline_epoch - current_time
    days = seconds_until_deadline / (24 * 60 * 60)
    return round(days, 1)  # Return with one decimal place

def create_notification(user_id, task_id, task_data, days_until):
    """Create a notification in Firebase"""
    try:
        notifications_ref = db.reference(f"notifications/{user_id}")
        new_notification_ref = notifications_ref.push()
        notification_id = new_notification_ref.key

        # Determine message based on days until deadline
        if days_until < 1:
            if days_until < 0:
                time_msg = "overdue"
            else:
                hours_until = int(days_until * 24)
                time_msg = f"due in {hours_until} hours"
        else:
            time_msg = f"due in {int(days_until)} days"

        notification_data = {
            "notificationId": notification_id,
            "userId": user_id,
            "taskId": task_id,
            "type": "task_deadline_reminder",
            "title": "Task Deadline Approaching",
            "message": f"Task '{task_data.get('title', 'Untitled')}' is {time_msg}",
            "taskTitle": task_data.get('title', 'Untitled'),
            "taskDeadline": task_data.get('deadline'),
            "daysUntilDeadline": days_until,
            "read": False,
            "createdAt": current_timestamp(),
            "readAt": None
        }

        new_notification_ref.set(notification_data)
        logger.info(f"Created notification for user {user_id}, task {task_id}, {days_until} days until deadline")
        return notification_id
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return None

def should_send_notification(task_id, user_id, days_until, reminder_times):
    """
    Check if notification should be sent based on:
    1. Days until deadline matches one of the reminder times
    2. Notification hasn't been sent already for this reminder interval
    """
    # Check if current days_until matches any reminder time (with tolerance)
    should_send = False
    for reminder_day in reminder_times:
        # Allow a small tolerance for matching (e.g., 6.9-7.1 days matches 7 days)
        if abs(days_until - reminder_day) < 0.5:
            should_send = True
            break

    if not should_send:
        return False

    # Check if we've already sent a notification for this task and reminder interval
    try:
        notifications_ref = db.reference(f"notifications/{user_id}")
        user_notifications = notifications_ref.get() or {}

        # Look for existing notifications for this task created within the last 24 hours
        current_time = current_timestamp()
        for notification in user_notifications.values():
            if (notification.get('taskId') == task_id and
                notification.get('type') == 'task_deadline_reminder' and
                current_time - notification.get('createdAt', 0) < 86400):  # 24 hours
                logger.info(f"Notification already sent for task {task_id} to user {user_id} recently")
                return False

        return True
    except Exception as e:
        logger.error(f"Error checking existing notifications: {str(e)}")
        return False

def check_task_deadlines():
    """
    Scheduled job to check all tasks and create notifications
    This runs periodically (every hour by default)
    """
    logger.info("Starting task deadline check...")

    try:
        # Get all tasks
        tasks_ref = db.reference("tasks")
        all_tasks = tasks_ref.get() or {}

        # Get all notification preferences
        preferences_ref = db.reference("notificationPreferences")
        all_preferences = preferences_ref.get() or {}

        notification_count = 0

        for task_id, task_data in all_tasks.items():
            # Skip completed tasks
            if task_data.get('status', '').lower() == 'completed':
                continue

            # Get task owner
            owner_id = task_data.get('ownerId')
            if not owner_id:
                continue

            # Get owner's notification preferences
            user_prefs = all_preferences.get(owner_id)
            if not user_prefs:
                continue

            # Check if notifications are enabled
            if not user_prefs.get('enabled', False) or not user_prefs.get('taskDeadlineReminders', False):
                continue

            # Check if in-app notifications are enabled
            channel = user_prefs.get('channel', 'both')
            if channel not in ['in-app', 'both']:
                continue

            # Calculate days until deadline
            deadline = task_data.get('deadline')
            if not deadline:
                continue

            days_until = days_until_deadline(deadline)

            # Skip if deadline has passed by more than 1 day
            if days_until < -1:
                continue

            # Get reminder times
            reminder_times = user_prefs.get('reminderTimes', [])
            if not reminder_times:
                continue

            # Check if we should send notification
            if should_send_notification(task_id, owner_id, days_until, reminder_times):
                notification_id = create_notification(owner_id, task_id, task_data, days_until)
                if notification_id:
                    notification_count += 1

        logger.info(f"Task deadline check completed. Created {notification_count} notifications.")

    except Exception as e:
        logger.error(f"Error during task deadline check: {str(e)}")

# API Endpoints

@app.route("/notifications/<user_id>", methods=["GET"])
def get_user_notifications(user_id):
    """Get all notifications for a user"""
    try:
        notifications_ref = db.reference(f"notifications/{user_id}")
        all_notifications = notifications_ref.get() or {}

        # Convert to list and sort by createdAt (newest first)
        notifications_list = list(all_notifications.values()) if all_notifications else []
        notifications_list.sort(key=lambda x: x.get('createdAt', 0), reverse=True)

        return jsonify(notifications=notifications_list), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve notifications: {str(e)}"), 500

@app.route("/notifications/<user_id>/unread", methods=["GET"])
def get_unread_notifications(user_id):
    """Get unread notifications for a user"""
    try:
        notifications_ref = db.reference(f"notifications/{user_id}")
        all_notifications = notifications_ref.get() or {}

        # Filter unread notifications
        unread_notifications = [
            notification for notification in all_notifications.values()
            if not notification.get('read', False)
        ]

        # Sort by createdAt (newest first)
        unread_notifications.sort(key=lambda x: x.get('createdAt', 0), reverse=True)

        return jsonify(
            notifications=unread_notifications,
            count=len(unread_notifications)
        ), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve unread notifications: {str(e)}"), 500

@app.route("/notifications/<user_id>/<notification_id>/read", methods=["PATCH"])
def mark_notification_read(user_id, notification_id):
    """Mark a notification as read"""
    try:
        notification_ref = db.reference(f"notifications/{user_id}/{notification_id}")
        notification = notification_ref.get()

        if not notification:
            return jsonify(error="Notification not found"), 404

        # Update read status
        notification_ref.update({
            "read": True,
            "readAt": current_timestamp()
        })

        # Get updated notification
        updated_notification = notification_ref.get()

        return jsonify(
            message="Notification marked as read",
            notification=updated_notification
        ), 200
    except Exception as e:
        return jsonify(error=f"Failed to mark notification as read: {str(e)}"), 500

@app.route("/notifications/<user_id>/<notification_id>", methods=["DELETE"])
def delete_notification(user_id, notification_id):
    """Delete a notification"""
    try:
        notification_ref = db.reference(f"notifications/{user_id}/{notification_id}")
        notification = notification_ref.get()

        if not notification:
            return jsonify(error="Notification not found"), 404

        # Delete the notification
        notification_ref.delete()

        return jsonify(message="Notification deleted successfully"), 200
    except Exception as e:
        return jsonify(error=f"Failed to delete notification: {str(e)}"), 500

@app.route("/notifications/<user_id>/mark-all-read", methods=["PATCH"])
def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user"""
    try:
        notifications_ref = db.reference(f"notifications/{user_id}")
        all_notifications = notifications_ref.get() or {}

        current_time = current_timestamp()
        update_count = 0

        for notification_id, notification in all_notifications.items():
            if not notification.get('read', False):
                notification_ref = db.reference(f"notifications/{user_id}/{notification_id}")
                notification_ref.update({
                    "read": True,
                    "readAt": current_time
                })
                update_count += 1

        return jsonify(
            message=f"Marked {update_count} notifications as read",
            count=update_count
        ), 200
    except Exception as e:
        return jsonify(error=f"Failed to mark all notifications as read: {str(e)}"), 500

@app.route("/scheduler/trigger", methods=["POST"])
def trigger_scheduler_manually():
    """Manually trigger the deadline checker (for testing)"""
    try:
        check_task_deadlines()
        return jsonify(message="Scheduler triggered successfully"), 200
    except Exception as e:
        return jsonify(error=f"Failed to trigger scheduler: {str(e)}"), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="notification-service"), 200

# Initialize and start scheduler
def start_scheduler():
    """Initialize and start the background scheduler"""
    scheduler = BackgroundScheduler()

    # Schedule the task deadline checker to run every hour
    # You can adjust the interval as needed (e.g., every 30 minutes, every 6 hours)
    scheduler.add_job(
        func=check_task_deadlines,
        trigger="interval",
        hours=1,
        id="task_deadline_checker",
        name="Check task deadlines and send notifications",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started. Task deadline checker will run every hour.")

    # Also run once on startup
    check_task_deadlines()

if __name__ == '__main__':
    # Start the background scheduler
    start_scheduler()

    # Start the Flask app
    app.run(host='0.0.0.0', port=6004, debug=True)
