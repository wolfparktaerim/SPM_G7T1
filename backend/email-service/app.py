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

# Configure CORS to allow rontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://spm-g7-t1-td8d.vercel.app",
            "http://localhost:3000", 
            "http://localhost:3001" 
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

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