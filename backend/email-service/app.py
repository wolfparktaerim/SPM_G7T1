# email-service/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
import os
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "Task Management System")

# Utility functions
def current_timestamp():
    """Return current timestamp in epoch format"""
    return int(datetime.now(timezone.utc).timestamp())

def format_deadline(deadline_epoch):
    """Format deadline epoch to readable date"""
    dt = datetime.fromtimestamp(deadline_epoch, tz=timezone.utc)
    return dt.strftime("%B %d, %Y at %I:%M %p UTC")

def get_time_remaining_text(days_until):
    """Get human-readable time remaining text"""
    if days_until < 0:
        overdue_days = abs(int(days_until))
        return f"{overdue_days} day{'s' if overdue_days != 1 else ''} overdue"
    elif days_until < 1:
        hours = int(days_until * 24)
        if hours == 0:
            return "Due now"
        return f"{hours} hour{'s' if hours != 1 else ''} left"
    else:
        whole_days = int(days_until)
        return f"{whole_days} day{'s' if whole_days != 1 else ''} left"

def create_email_html(task_title, task_deadline, days_until, task_notes="", parent_task_title=None):
    """Create HTML email template for task or subtask deadline notification"""
    deadline_str = format_deadline(task_deadline)
    time_remaining = get_time_remaining_text(days_until)

    # Determine urgency color
    if days_until < 0:
        urgency_color = "#dc2626"  # Red
        urgency_label = "OVERDUE"
    elif days_until < 1:
        urgency_color = "#ea580c"  # Orange
        urgency_label = "CRITICAL"
    elif days_until <= 2:
        urgency_color = "#f59e0b"  # Amber
        urgency_label = "URGENT"
    elif days_until <= 7:
        urgency_color = "#3b82f6"  # Blue
        urgency_label = "UPCOMING"
    else:
        urgency_color = "#6b7280"  # Gray
        urgency_label = "REMINDER"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Task Deadline Reminder</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">Task Deadline Reminder</h1>
                            </td>
                        </tr>

                        <!-- Urgency Badge -->
                        <tr>
                            <td style="padding: 20px 30px 0;">
                                <div style="display: inline-block; background-color: {urgency_color}; color: #ffffff; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;">
                                    {urgency_label}
                                </div>
                            </td>
                        </tr>

                        <!-- Task Details -->
                        <tr>
                            <td style="padding: 20px 30px;">
                                <h2 style="margin: 0 0 16px 0; color: #111827; font-size: 20px; font-weight: 600;">{task_title}</h2>
                                {f'<p style="margin: 0 0 16px 0; color: #6b7280; font-size: 14px;">Part of task: <strong style="color: #111827;">{parent_task_title}</strong></p>' if parent_task_title else ''}

                                <div style="background-color: #f9fafb; border-left: 4px solid {urgency_color}; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
                                    <table role="presentation" style="width: 100%;">
                                        <tr>
                                            <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500;">Deadline:</td>
                                            <td style="padding: 8px 0; color: #111827; font-size: 14px; font-weight: 600; text-align: right;">{deadline_str}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px 0; color: #6b7280; font-size: 14px; font-weight: 500;">Time Remaining:</td>
                                            <td style="padding: 8px 0; color: {urgency_color}; font-size: 14px; font-weight: 600; text-align: right;">{time_remaining}</td>
                                        </tr>
                                    </table>
                                </div>

                                {f'<p style="margin: 16px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">{task_notes}</p>' if task_notes else ''}
                            </td>
                        </tr>

                        <!-- Call to Action -->
                        <tr>
                            <td style="padding: 0 30px 30px;">
                                <p style="margin: 0 0 16px 0; color: #6b7280; font-size: 14px;">
                                    Please review this task and take necessary action before the deadline.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 30px; border-radius: 0 0 12px 12px; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                                    This is an automated notification from your Task Management System.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html

def send_email(to_email, subject, html_content):
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

# API Endpoints

@app.route("/email/send-task-reminder", methods=["POST"])
def send_task_reminder():
    """Send task or subtask deadline reminder email"""
    data = request.get_json()

    # Validate required fields
    required_fields = ["toEmail", "taskTitle", "taskDeadline", "daysUntilDeadline"]
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    to_email = data["toEmail"]
    task_title = data["taskTitle"]
    task_deadline = data["taskDeadline"]
    days_until = data["daysUntilDeadline"]
    task_notes = data.get("taskNotes", "")
    is_subtask = data.get("isSubtask", False)
    parent_task_title = data.get("parentTaskTitle")

    try:
        # Create email content with appropriate subject line
        if is_subtask:
            subject = f"Subtask Deadline Reminder: {task_title}"
        else:
            subject = f"Task Deadline Reminder: {task_title}"

        html_content = create_email_html(task_title, task_deadline, days_until, task_notes, parent_task_title)

        # Send email
        success = send_email(to_email, subject, html_content)

        if success:
            return jsonify(
                message="Email sent successfully",
                sentAt=current_timestamp()
            ), 200
        else:
            return jsonify(error="Failed to send email"), 500

    except Exception as e:
        logger.error(f"Error sending task reminder email: {str(e)}")
        return jsonify(error=f"Failed to send email: {str(e)}"), 500

@app.route("/email/test", methods=["POST"])
def test_email():
    """Test email configuration by sending a test email"""
    data = request.get_json()

    if not data or "toEmail" not in data:
        return jsonify(error="Missing required field: toEmail"), 400

    to_email = data["toEmail"]

    try:
        subject = "Test Email from Task Management System"
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #3b82f6;">Email Service Test</h2>
            <p>This is a test email to verify your email configuration is working correctly.</p>
            <p>If you received this email, your SMTP settings are configured properly!</p>
        </body>
        </html>
        """

        success = send_email(to_email, subject, html_content)

        if success:
            return jsonify(message="Test email sent successfully"), 200
        else:
            return jsonify(error="Failed to send test email"), 500

    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify(error=f"Failed to send test email: {str(e)}"), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        status="healthy",
        service="email-service",
        smtp_configured=bool(SMTP_USER and SMTP_PASSWORD)
    ), 200

if __name__ == '__main__':
    # Check if SMTP credentials are configured
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Email sending will fail.")
        logger.warning("Please set SMTP_USER and SMTP_PASSWORD environment variables.")

    app.run(host='0.0.0.0', port=6005, debug=True)
