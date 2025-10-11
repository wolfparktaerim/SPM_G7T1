# backend/email-service/email_service.py
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import EmailRequest

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "Task Management System")
    
    def format_deadline(self, deadline_epoch):
        """Format deadline epoch to readable date"""
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(deadline_epoch, tz=timezone.utc)
        return dt.strftime("%B %d, %Y at %I:%M %p UTC")
    
    def get_time_remaining_text(self, days_until):
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
    
    def create_email_html(self, email_req: EmailRequest):
        """Create HTML email template"""
        deadline_str = self.format_deadline(email_req.task_deadline)
        time_remaining = self.get_time_remaining_text(email_req.days_until_deadline)
        
        # Determine urgency
        if email_req.days_until_deadline < 0:
            urgency_color = "#dc2626"
            urgency_label = "OVERDUE"
        elif email_req.days_until_deadline < 1:
            urgency_color = "#ea580c"
            urgency_label = "CRITICAL"
        elif email_req.days_until_deadline <= 2:
            urgency_color = "#f59e0b"
            urgency_label = "URGENT"
        elif email_req.days_until_deadline <= 7:
            urgency_color = "#3b82f6"
            urgency_label = "UPCOMING"
        else:
            urgency_color = "#6b7280"
            urgency_label = "REMINDER"
        
        parent_task_html = ""
        if email_req.parent_task_title:
            parent_task_html = f'<p style="margin: 0 0 16px 0; color: #6b7280; font-size: 14px;">Part of task: <strong style="color: #111827;">{email_req.parent_task_title}</strong></p>'
        
        notes_html = ""
        if email_req.task_notes:
            notes_html = f'<p style="margin: 16px 0; color: #4b5563; font-size: 14px; line-height: 1.6;">{email_req.task_notes}</p>'
        
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
                            <tr>
                                <td style="background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">Task Deadline Reminder</h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 20px 30px 0;">
                                    <div style="display: inline-block; background-color: {urgency_color}; color: #ffffff; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;">
                                        {urgency_label}
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 20px 30px;">
                                    <h2 style="margin: 0 0 16px 0; color: #111827; font-size: 20px; font-weight: 600;">{email_req.task_title}</h2>
                                    {parent_task_html}
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
                                    {notes_html}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 0 30px 30px;">
                                    <p style="margin: 0 0 16px 0; color: #6b7280; font-size: 14px;">
                                        Please review this task and take necessary action before the deadline.
                                    </p>
                                </td>
                            </tr>
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
    
    def send_email(self, to_email, subject, html_content):
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_task_reminder(self, email_req: EmailRequest):
        """Send task or subtask deadline reminder email"""
        # Validate request
        errors = email_req.validate()
        if errors:
            return False, errors
        
        # Create subject
        if email_req.is_subtask:
            subject = f"Subtask Deadline Reminder: {email_req.task_title}"
        else:
            subject = f"Task Deadline Reminder: {email_req.task_title}"
        
        # Create and send email
        html_content = self.create_email_html(email_req)
        success = self.send_email(email_req.to_email, subject, html_content)
        
        return success, []
    
    def send_test_email(self, to_email):
        """Send test email"""
        subject = "Test Email from Task Management System"
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #3b82f6;">Email Service Test</h2>
            <p>This is a test email to verify your email configuration is working correctly.</p>
            <p>If you received this email, your SMTP settings are configured properly!</p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html_content)
    
    def is_configured(self):
        """Check if SMTP credentials are configured"""
        return bool(self.smtp_user and self.smtp_password)