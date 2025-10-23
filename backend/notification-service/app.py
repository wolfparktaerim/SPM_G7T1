
# backend/notification-service/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared import init_firebase

from notification_service import NotificationService
from scheduler_service import SchedulerService

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase
init_firebase()

# Initialize services
notification_service = NotificationService()
email_service_url = os.getenv("EMAIL_SERVICE_URL", "http://email-service:6005")
scheduler_service = SchedulerService(email_service_url)

@app.route("/notifications/<user_id>", methods=["GET"])
def get_user_notifications(user_id):
    """Get all notifications for a user"""
    try:
        notifications = notification_service.get_user_notifications(user_id)
        return jsonify(notifications=[n.to_dict() for n in notifications]), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve notifications: {str(e)}"), 500

@app.route("/notifications/<user_id>/unread", methods=["GET"])
def get_unread_notifications(user_id):
    """Get unread notifications for a user"""
    try:
        unread = notification_service.get_unread_notifications(user_id)
        return jsonify(
            notifications=[n.to_dict() for n in unread],
            count=len(unread)
        ), 200
    except Exception as e:
        return jsonify(error=f"Failed to retrieve unread notifications: {str(e)}"), 500

@app.route("/notifications/<user_id>/<notification_id>/read", methods=["PATCH"])
def mark_notification_read(user_id, notification_id):
    """Mark a notification as read"""
    try:
        notification, error = notification_service.mark_notification_read(user_id, notification_id)
        if error:
            return jsonify(error=error), 404
        
        return jsonify(
            message="Notification marked as read",
            notification=notification.to_dict()
        ), 200
    except Exception as e:
        return jsonify(error=f"Failed to mark notification as read: {str(e)}"), 500

@app.route("/notifications/<user_id>/<notification_id>", methods=["DELETE"])
def delete_notification(user_id, notification_id):
    """Delete a notification"""
    try:
        success, error = notification_service.delete_notification(user_id, notification_id)
        if error:
            return jsonify(error=error), 404
        
        return jsonify(message="Notification deleted successfully"), 200
    except Exception as e:
        return jsonify(error=f"Failed to delete notification: {str(e)}"), 500

@app.route("/notifications/<user_id>/mark-all-read", methods=["PATCH"])
def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user"""
    try:
        count = notification_service.mark_all_notifications_read(user_id)
        return jsonify(
            message=f"Marked {count} notifications as read",
            count=count
        ), 200
    except Exception as e:
        return jsonify(error=f"Failed to mark all notifications as read: {str(e)}"), 500

@app.route("/scheduler/trigger", methods=["POST"])
def trigger_scheduler_manually():
    """Manually trigger the deadline checker (for testing)"""
    try:
        scheduler_service.trigger_manually()
        return jsonify(message="Scheduler triggered successfully"), 200
    except Exception as e:
        return jsonify(error=f"Failed to trigger scheduler: {str(e)}"), 500

@app.route("/notifications/task-update", methods=["POST"])
def send_task_update_notification():
    """Send notification for task status update"""
    try:
        data = request.json

        # Validate required fields
        required_fields = ['itemId', 'taskTitle', 'oldStatus', 'newStatus', 'userIds', 'channel']
        for field in required_fields:
            if field not in data:
                return jsonify(error=f"Missing required field: {field}"), 400

        item_id = data['itemId']
        task_title = data['taskTitle']
        old_status = data['oldStatus']
        new_status = data['newStatus']
        user_ids = data['userIds']  # List of user IDs (owner + collaborators)
        channel = data['channel']
        is_subtask = data.get('isSubtask', False)
        parent_task_title = data.get('parentTaskTitle')
        user_emails = data.get('userEmails', {})  # Dict mapping user_id to email

        notifications_sent = []
        emails_sent = []

        # Send notifications to each user
        for user_id in user_ids:
            # Check for duplicates
            if notification_service.check_duplicate_update_notification(user_id, item_id, new_status, is_subtask):
                logger.info(f"Skipping duplicate notification for user {user_id}")
                continue

            # Send in-app notification if channel includes in-app
            if channel in ['in-app', 'both']:
                notification_id = notification_service.create_task_update_notification(
                    user_id, item_id, task_title, old_status, new_status, is_subtask, parent_task_title
                )
                if notification_id:
                    notifications_sent.append(user_id)

            # Send email notification if channel includes email
            if channel in ['email', 'both'] and user_id in user_emails:
                try:
                    import requests
                    email_data = {
                        "toEmail": user_emails[user_id],
                        "taskTitle": task_title,
                        "oldStatus": old_status,
                        "newStatus": new_status,
                        "isSubtask": is_subtask,
                        "parentTaskTitle": parent_task_title
                    }

                    response = requests.post(
                        f"{email_service_url}/email/send-task-update",
                        json=email_data,
                        timeout=10
                    )

                    if response.status_code == 200:
                        emails_sent.append(user_id)
                        logger.info(f"Task update email sent to {user_emails[user_id]}")
                    else:
                        logger.error(f"Failed to send email: {response.text}")
                except Exception as e:
                    logger.error(f"Error sending email: {str(e)}")

        return jsonify(
            message="Task update notifications sent",
            notificationsSent=notifications_sent,
            emailsSent=emails_sent
        ), 200

    except Exception as e:
        logger.error(f"Failed to send task update notifications: {str(e)}")
        return jsonify(error=f"Failed to send notifications: {str(e)}"), 500

@app.route("/notifications/comment", methods=["POST"])
def send_comment_notification():
    """Send notification for new comment on task"""
    try:
        data = request.json

        # Validate required fields
        required_fields = ['itemId', 'taskTitle', 'commentText', 'commenterName', 'commenterId',
                         'recipientIds', 'channel']
        for field in required_fields:
            if field not in data:
                return jsonify(error=f"Missing required field: {field}"), 400

        item_id = data['itemId']
        task_title = data['taskTitle']
        comment_text = data['commentText']
        commenter_name = data['commenterName']
        commenter_id = data['commenterId']
        recipient_ids = data['recipientIds']  # List of user IDs to notify
        channel = data['channel']
        is_subtask = data.get('isSubtask', False)
        parent_task_title = data.get('parentTaskTitle')
        task_deadline = data.get('taskDeadline')
        recipient_emails = data.get('recipientEmails', {})  # Dict mapping user_id to email

        notifications_sent = []
        emails_sent = []

        # Send notifications to each recipient
        for user_id in recipient_ids:
            # Don't notify the commenter themselves
            if user_id == commenter_id:
                continue

            # Check for duplicates
            if notification_service.check_duplicate_comment_notification(user_id, item_id, commenter_id, is_subtask):
                logger.info(f"Skipping duplicate comment notification for user {user_id}")
                continue

            # Send in-app notification if channel includes in-app
            if channel in ['in-app', 'both']:
                notification_id = notification_service.create_comment_notification(
                    user_id, item_id, task_title, comment_text, commenter_name, commenter_id,
                    task_deadline, is_subtask, parent_task_title
                )
                if notification_id:
                    notifications_sent.append(user_id)

            # Send email notification if channel includes email
            if channel in ['email', 'both'] and user_id in recipient_emails:
                try:
                    import requests
                    email_data = {
                        "toEmail": recipient_emails[user_id],
                        "taskTitle": task_title,
                        "commentText": comment_text,
                        "commenterName": commenter_name,
                        "isSubtask": is_subtask,
                        "parentTaskTitle": parent_task_title,
                        "taskDeadline": task_deadline
                    }

                    response = requests.post(
                        f"{email_service_url}/email/send-comment-notification",
                        json=email_data,
                        timeout=10
                    )

                    if response.status_code == 200:
                        emails_sent.append(user_id)
                        logger.info(f"Comment notification email sent to {recipient_emails[user_id]}")
                    else:
                        logger.error(f"Failed to send email: {response.text}")
                except Exception as e:
                    logger.error(f"Error sending email: {str(e)}")

        return jsonify(
            message="Comment notifications sent",
            notificationsSent=notifications_sent,
            emailsSent=emails_sent
        ), 200

    except Exception as e:
        logger.error(f"Failed to send comment notifications: {str(e)}")
        return jsonify(error=f"Failed to send notifications: {str(e)}"), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="notification-service"), 200


@app.route("/notifications/deadline-extension-request", methods=["POST"])
def send_deadline_extension_request_notification():
    """Send notification for deadline extension request"""
    try:
        data = request.json
        
        required_fields = ['ownerId', 'itemId', 'itemTitle', 'requesterId', 'itemType', 'extensionRequestId']  
        for field in required_fields:
            if field not in data:
                return jsonify(error=f"Missing required field: {field}"), 400
        
        owner_id = data['ownerId']
        item_id = data['itemId']
        item_title = data['itemTitle']
        requester_id = data['requesterId']
        item_type = data['itemType']
        extension_request_id = data['extensionRequestId'] 
        
        notification_id = notification_service.create_deadline_extension_request_notification(
            owner_id, item_id, item_title, requester_id, item_type, extension_request_id 
        )
        
        if notification_id:
            return jsonify(
                message="Extension request notification sent",
                notificationId=notification_id
            ), 200
        else:
            return jsonify(error="Failed to create notification"), 500
            
    except Exception as e:
        logger.error(f"Failed to send extension request notification: {str(e)}")
        return jsonify(error=f"Failed to send notification: {str(e)}"), 500

@app.route("/notifications/deadline-extension-response", methods=["POST"])
def send_deadline_extension_response_notification():
    """Send notification for deadline extension response"""
    try:
        data = request.json
        
        required_fields = ['requesterId', 'itemId', 'itemType', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify(error=f"Missing required field: {field}"), 400
        
        requester_id = data['requesterId']
        item_id = data['itemId']
        item_type = data['itemType']
        status = data['status']
        rejection_reason = data.get('rejectionReason')
        
        # Get item title
        if item_type == 'task':
            item_ref = notification_service.db.reference(f"tasks/{item_id}")
        else:
            item_ref = notification_service.db.reference(f"subtasks/{item_id}")
        
        item_data = item_ref.get()
        item_title = item_data.get('title', 'Untitled') if item_data else 'Untitled'
        
        notification_id = notification_service.create_deadline_extension_response_notification(
            requester_id, item_id, item_type, item_title, status, rejection_reason
        )
        
        if notification_id:
            return jsonify(
                message="Extension response notification sent",
                notificationId=notification_id
            ), 200
        else:
            return jsonify(error="Failed to create notification"), 500
            
    except Exception as e:
        logger.error(f"Failed to send extension response notification: {str(e)}")
        return jsonify(error=f"Failed to send notification: {str(e)}"), 500

@app.route("/notifications/deadline-changed", methods=["POST"])
def send_deadline_changed_notification():
    """Send notification to all collaborators about deadline change"""
    try:
        data = request.json
        
        required_fields = ['itemId', 'itemTitle', 'itemType', 'collaboratorIds', 'newDeadline']
        for field in required_fields:
            if field not in data:
                return jsonify(error=f"Missing required field: {field}"), 400
        
        item_id = data['itemId']
        item_title = data['itemTitle']
        item_type = data['itemType']
        collaborator_ids = data['collaboratorIds']
        new_deadline = data['newDeadline']
        
        notifications_sent = []
        
        for user_id in collaborator_ids:
            notification_id = notification_service.create_deadline_changed_notification(
                user_id, item_id, item_type, item_title, new_deadline
            )
            if notification_id:
                notifications_sent.append(user_id)
        
        return jsonify(
            message="Deadline change notifications sent",
            notificationsSent=notifications_sent
        ), 200
            
    except Exception as e:
        logger.error(f"Failed to send deadline change notifications: {str(e)}")
        return jsonify(error=f"Failed to send notifications: {str(e)}"), 500


if __name__ == '__main__':
    # Start the background scheduler
    scheduler_service.start()

    # Start the Flask app
    app.run(host='0.0.0.0', port=6004, debug=True)