
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

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(status="healthy", service="notification-service"), 200

if __name__ == '__main__':
    # Start the background scheduler
    scheduler_service.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=6004, debug=True)