# backend/email-service/test_email.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Set up environment variables BEFORE any imports
os.environ['SMTP_HOST'] = 'smtp.test.com'
os.environ['SMTP_PORT'] = '587'
os.environ['SMTP_USER'] = 'test@test.com'
os.environ['SMTP_PASSWORD'] = 'testpass'
os.environ['FROM_EMAIL'] = 'test@test.com'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from email_service import EmailService
from models import EmailRequest

# Import app AFTER setting environment and mocking
from app import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def email_service():
    """Create email service instance"""
    return EmailService()

@pytest.fixture
def sample_email_request():
    """Create sample email request"""
    return EmailRequest(
        to_email="test@example.com",
        task_title="Test Task",
        task_deadline=1700000000,
        days_until_deadline=3.5,
        task_notes="Test notes"
    )

class TestEmailModels:
    """Test email models"""
    
    def test_email_request_from_dict(self):
        """Test creating EmailRequest from dictionary"""
        data = {
            "toEmail": "test@example.com",
            "taskTitle": "Test Task",
            "taskDeadline": 1700000000,
            "daysUntilDeadline": 3.5,
            "taskNotes": "Test notes",
            "isSubtask": True,
            "parentTaskTitle": "Parent Task"
        }
        email_req = EmailRequest.from_dict(data)
        
        assert email_req.to_email == "test@example.com"
        assert email_req.task_title == "Test Task"
        assert email_req.task_deadline == 1700000000
        assert email_req.days_until_deadline == 3.5
        assert email_req.is_subtask == True
        assert email_req.parent_task_title == "Parent Task"
    
    def test_email_request_validate_success(self):
        """Test validation with valid data"""
        email_req = EmailRequest(
            to_email="test@example.com",
            task_title="Test Task",
            task_deadline=1700000000,
            days_until_deadline=3.5
        )
        errors = email_req.validate()
        assert len(errors) == 0
    
    def test_email_request_validate_missing_fields(self):
        """Test validation with missing required fields"""
        email_req = EmailRequest(
            to_email="",
            task_title="",
            task_deadline=0,
            days_until_deadline=None
        )
        errors = email_req.validate()
        assert len(errors) > 0
        assert "toEmail is required" in errors
        assert "taskTitle is required" in errors
        assert "taskDeadline is required" in errors
        assert "daysUntilDeadline is required" in errors

class TestEmailService:
    """Test email service class"""
    
    def test_format_deadline(self, email_service):
        """Test deadline formatting"""
        # Test epoch 1700000000 = November 14, 2023
        result = email_service.format_deadline(1700000000)
        assert "November" in result
        assert "2023" in result
    
    def test_get_time_remaining_text_overdue(self, email_service):
        """Test time remaining text for overdue tasks"""
        result = email_service.get_time_remaining_text(-2.5)
        assert "overdue" in result.lower()
        assert "2" in result
    
    def test_get_time_remaining_text_hours(self, email_service):
        """Test time remaining text in hours"""
        result = email_service.get_time_remaining_text(0.5)
        assert "hour" in result.lower()
    
    def test_get_time_remaining_text_days(self, email_service):
        """Test time remaining text in days"""
        result = email_service.get_time_remaining_text(5.5)
        assert "day" in result.lower()
        assert "5" in result
    
    def test_get_time_remaining_text_due_now(self, email_service):
        """Test time remaining text when due now"""
        result = email_service.get_time_remaining_text(0.01)
        assert "now" in result.lower() or "0" in result
    
    def test_create_email_html(self, email_service, sample_email_request):
        """Test HTML email creation"""
        html = email_service.create_email_html(sample_email_request)
        
        assert sample_email_request.task_title in html
        assert sample_email_request.task_notes in html
        assert "UPCOMING" in html or "URGENT" in html
        assert "<!DOCTYPE html>" in html
    
    def test_create_email_html_with_parent_task(self, email_service):
        """Test HTML email creation with parent task"""
        email_req = EmailRequest(
            to_email="test@example.com",
            task_title="Subtask",
            task_deadline=1700000000,
            days_until_deadline=3.0,
            is_subtask=True,
            parent_task_title="Parent Task"
        )
        html = email_service.create_email_html(email_req)
        
        assert "Parent Task" in html
        assert "Subtask" in html
    
    @patch('email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_service):
        """Test successful email sending"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service.send_email(
            "recipient@example.com",
            "Test Subject",
            "<html>Test</html>"
        )
        
        assert result == True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            email_service.smtp_user,
            email_service.smtp_password
        )
        mock_server.send_message.assert_called_once()
    
    @patch('email_service.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp, email_service):
        """Test email sending failure"""
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Error")
        
        result = email_service.send_email(
            "recipient@example.com",
            "Test Subject",
            "<html>Test</html>"
        )
        
        assert result == False
    
    @patch('email_service.smtplib.SMTP')
    def test_send_task_reminder(self, mock_smtp, email_service, sample_email_request):
        """Test sending task reminder"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        success, errors = email_service.send_task_reminder(sample_email_request)
        
        assert success == True
        assert len(errors) == 0
        mock_server.send_message.assert_called_once()
    
    @patch('email_service.smtplib.SMTP')
    def test_send_test_email(self, mock_smtp, email_service):
        """Test sending test email"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service.send_test_email("test@example.com")
        
        assert result == True
        mock_server.send_message.assert_called_once()
    
    def test_is_configured(self, email_service):
        """Test configuration check"""
        assert email_service.is_configured() == True
    
    def test_is_not_configured(self):
        """Test configuration check when not configured"""
        with patch.dict(os.environ, {'SMTP_USER': '', 'SMTP_PASSWORD': ''}):
            service = EmailService()
            assert service.is_configured() == False

class TestEmailEndpoints:
    """Test Flask endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'email-service'
        assert 'smtp_configured' in data
    
    def test_send_task_reminder_missing_body(self, client):
        """Test sending reminder without body"""
        response = client.post(
            '/email/send-task-reminder',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_send_task_reminder_invalid_data(self, client):
        """Test sending reminder with invalid data"""
        response = client.post(
            '/email/send-task-reminder',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.email_service.send_task_reminder')
    def test_send_task_reminder_success(self, mock_send, client):
        """Test successful task reminder sending"""
        mock_send.return_value = (True, [])
        
        response = client.post(
            '/email/send-task-reminder',
            json={
                "toEmail": "test@example.com",
                "taskTitle": "Test Task",
                "taskDeadline": 1700000000,
                "daysUntilDeadline": 3.5
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'sentAt' in data
    
    @patch('app.email_service.send_task_reminder')
    def test_send_task_reminder_failure(self, mock_send, client):
        """Test failed task reminder sending"""
        mock_send.return_value = (False, ["SMTP Error"])
        
        response = client.post(
            '/email/send-task-reminder',
            json={
                "toEmail": "test@example.com",
                "taskTitle": "Test Task",
                "taskDeadline": 1700000000,
                "daysUntilDeadline": 3.5
            },
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    def test_test_email_missing_email(self, client):
        """Test test email endpoint without email"""
        response = client.post(
            '/email/test',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.email_service.send_test_email')
    def test_test_email_success(self, mock_send, client):
        """Test successful test email"""
        mock_send.return_value = True
        
        response = client.post(
            '/email/test',
            json={"toEmail": "test@example.com"},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    @patch('app.email_service.send_test_email')
    def test_test_email_failure(self, mock_send, client):
        """Test failed test email"""
        mock_send.return_value = False
        
        response = client.post(
            '/email/test',
            json={"toEmail": "test@example.com"},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 500

if __name__ == '__main__':
    pytest.main([__file__, '-v'])