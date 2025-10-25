# backend/email-service/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only the utility function we need, not firebase config
from shared.utils import current_timestamp

from email_service import EmailService
from models import EmailRequest

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize service
email_service = EmailService()

@app.route("/email/send-task-reminder", methods=["POST"])
def send_task_reminder():
    """Send task or subtask deadline reminder email"""
    
    try:
        data = request.get_json(force=False, silent=False)
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400
    
    # Handle missing body
    if data is None:
        return jsonify({"error": "Missing JSON body"}), 400
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    
    # Create email request model
    email_req = EmailRequest.from_dict(data)
    
    # Validate
    errors = email_req.validate()
    if errors:
        return jsonify(error=f"Validation failed: {', '.join(errors)}"), 400
    
    # Send email
    success, errors = email_service.send_task_reminder(email_req)
    
    if success:
        return jsonify(
            message="Email sent successfully",
            sentAt=current_timestamp()
        ), 200
    else:
        return jsonify(error="Failed to send email"), 500

@app.route("/email/send-task-update", methods=["POST"])
def send_task_update():
    """Send task status update email"""

    try:
        data = request.get_json(force=False, silent=False)
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    # Handle missing body
    if data is None or not data:
        return jsonify({"error": "Missing JSON body"}), 400

    # Validate required fields
    required_fields = ['toEmail', 'taskTitle', 'oldStatus', 'newStatus']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    # Extract data
    to_email = data['toEmail']
    task_title = data['taskTitle']
    old_status = data['oldStatus']
    new_status = data['newStatus']
    is_subtask = data.get('isSubtask', False)
    parent_task_title = data.get('parentTaskTitle')

    # Send email
    success = email_service.send_task_update_email(
        to_email, task_title, old_status, new_status, is_subtask, parent_task_title
    )

    if success:
        return jsonify(
            message="Task update email sent successfully",
            sentAt=current_timestamp()
        ), 200
    else:
        return jsonify(error="Failed to send task update email"), 500

@app.route("/email/send-comment-notification", methods=["POST"])
def send_comment_notification():
    """Send comment notification email"""

    try:
        data = request.get_json(force=False, silent=False)
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    # Handle missing body
    if data is None or not data:
        return jsonify({"error": "Missing JSON body"}), 400

    # Validate required fields
    required_fields = ['toEmail', 'taskTitle', 'commentText', 'commenterName']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    # Extract data
    to_email = data['toEmail']
    task_title = data['taskTitle']
    comment_text = data['commentText']
    commenter_name = data['commenterName']
    is_subtask = data.get('isSubtask', False)
    parent_task_title = data.get('parentTaskTitle')
    task_deadline = data.get('taskDeadline')

    # Send email
    success = email_service.send_comment_notification_email(
        to_email, task_title, comment_text, commenter_name,
        is_subtask, parent_task_title, task_deadline
    )

    if success:
        return jsonify(
            message="Comment notification email sent successfully",
            sentAt=current_timestamp()
        ), 200
    else:
        return jsonify(error="Failed to send comment notification email"), 500

@app.route("/email/send-deadline-extension-request", methods=["POST"])
def send_deadline_extension_request():
    """Send deadline extension request email"""
    try:
        data = request.get_json(force=False, silent=False)
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    if data is None or not data:
        return jsonify({"error": "Missing JSON body"}), 400

    required_fields = ['toEmail', 'itemTitle', 'requesterName', 'currentDeadline', 'proposedDeadline']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    to_email = data['toEmail']
    item_title = data['itemTitle']
    requester_name = data['requesterName']
    current_deadline = data['currentDeadline']
    proposed_deadline = data['proposedDeadline']
    reason = data.get('reason', '')
    item_type = data.get('itemType', 'task')
    parent_task_title = data.get('parentTaskTitle')

    success = email_service.send_deadline_extension_request_email(
        to_email, item_title, requester_name, current_deadline, proposed_deadline,
        reason, item_type, parent_task_title
    )

    if success:
        return jsonify(message="Deadline extension request email sent successfully"), 200
    else:
        return jsonify(error="Failed to send deadline extension request email"), 500

@app.route("/email/send-deadline-extension-response", methods=["POST"])
def send_deadline_extension_response():
    """Send deadline extension response email"""
    try:
        data = request.get_json(force=False, silent=False)
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    if data is None or not data:
        return jsonify({"error": "Missing JSON body"}), 400

    required_fields = ['toEmail', 'itemTitle', 'status']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    to_email = data['toEmail']
    item_title = data['itemTitle']
    status = data['status']
    new_deadline = data.get('newDeadline')
    rejection_reason = data.get('rejectionReason')
    item_type = data.get('itemType', 'task')
    parent_task_title = data.get('parentTaskTitle')

    success = email_service.send_deadline_extension_response_email(
        to_email, item_title, status, new_deadline, rejection_reason,
        item_type, parent_task_title
    )

    if success:
        return jsonify(message="Deadline extension response email sent successfully"), 200
    else:
        return jsonify(error="Failed to send deadline extension response email"), 500

@app.route("/email/send-deadline-changed", methods=["POST"])
def send_deadline_changed():
    """Send deadline changed email"""
    try:
        data = request.get_json(force=False, silent=False)
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    if data is None or not data:
        return jsonify({"error": "Missing JSON body"}), 400

    required_fields = ['toEmail', 'itemTitle', 'newDeadline']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    to_email = data['toEmail']
    item_title = data['itemTitle']
    new_deadline = data['newDeadline']
    requester_name = data.get('requesterName')
    item_type = data.get('itemType', 'task')
    parent_task_title = data.get('parentTaskTitle')

    success = email_service.send_deadline_changed_email(
        to_email, item_title, new_deadline, requester_name,
        item_type, parent_task_title
    )

    if success:
        return jsonify(message="Deadline changed email sent successfully"), 200
    else:
        return jsonify(error="Failed to send deadline changed email"), 500

@app.route("/email/test", methods=["POST"])
def test_email():
    """Test email configuration"""
    data = request.get_json()
    if not data or "toEmail" not in data:
        return jsonify(error="Missing required field: toEmail"), 400

    success = email_service.send_test_email(data["toEmail"])

    if success:
        return jsonify(message="Test email sent successfully"), 200
    else:
        return jsonify(error="Failed to send test email"), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        status="healthy",
        service="email-service",
        smtp_configured=email_service.is_configured()
    ), 200

if __name__ == '__main__':
    if not email_service.is_configured():
        logger.warning("SMTP credentials not configured. Email sending will fail.")
        logger.warning("Please set SMTP_USER and SMTP_PASSWORD environment variables.")
    
    app.run(host='0.0.0.0', port=6005, debug=True)