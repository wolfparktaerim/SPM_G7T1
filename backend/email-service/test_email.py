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


class TestTaskUpdateEndpoint:
    """Test task update email endpoint"""

    @patch('app.email_service.send_task_update_email')
    def test_send_task_update_success(self, mock_send, client):
        """Test POST /email/send-task-update success"""
        mock_send.return_value = True

        response = client.post('/email/send-task-update', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Task",
            "oldStatus": "in_progress",
            "newStatus": "completed"
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Task update email sent successfully"
        mock_send.assert_called_once()

    @patch('app.email_service.send_task_update_email')
    def test_send_task_update_with_subtask(self, mock_send, client):
        """Test POST /email/send-task-update for subtask"""
        mock_send.return_value = True

        response = client.post('/email/send-task-update', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Subtask",
            "oldStatus": "to_do",
            "newStatus": "in_progress",
            "isSubtask": True,
            "parentTaskTitle": "Parent Task"
        })

        assert response.status_code == 200
        mock_send.assert_called_once_with(
            "test@example.com", "Test Subtask", "to_do", "in_progress", True, "Parent Task"
        )

    def test_send_task_update_missing_body(self, client):
        """Test POST /email/send-task-update with missing body"""
        response = client.post('/email/send-task-update')
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid JSON' in data['error'] or 'Missing JSON body' in data['error']

    def test_send_task_update_invalid_json(self, client):
        """Test POST /email/send-task-update with invalid JSON"""
        response = client.post('/email/send-task-update',
                              data="invalid json",
                              content_type='application/json')
        assert response.status_code == 400

    def test_send_task_update_missing_fields(self, client):
        """Test POST /email/send-task-update with missing required fields"""
        response = client.post('/email/send-task-update', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Task"
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Missing required field' in data['error']

    @patch('app.email_service.send_task_update_email')
    def test_send_task_update_failure(self, mock_send, client):
        """Test POST /email/send-task-update failure"""
        mock_send.return_value = False

        response = client.post('/email/send-task-update', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Task",
            "oldStatus": "to_do",
            "newStatus": "in_progress"
        })

        assert response.status_code == 500
        data = response.get_json()
        assert 'Failed to send task update email' in data['error']


class TestCommentNotificationEndpoint:
    """Test comment notification email endpoint"""

    @patch('app.email_service.send_comment_notification_email')
    def test_send_comment_notification_success(self, mock_send, client):
        """Test POST /email/send-comment-notification success"""
        mock_send.return_value = True

        response = client.post('/email/send-comment-notification', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Task",
            "commentText": "Great work!",
            "commenterName": "John Doe"
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Comment notification email sent successfully"

    @patch('app.email_service.send_comment_notification_email')
    def test_send_comment_notification_with_subtask(self, mock_send, client):
        """Test POST /email/send-comment-notification for subtask"""
        mock_send.return_value = True

        response = client.post('/email/send-comment-notification', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Subtask",
            "commentText": "Looks good",
            "commenterName": "Jane Doe",
            "isSubtask": True,
            "parentTaskTitle": "Parent Task",
            "taskDeadline": 1700000000
        })

        assert response.status_code == 200
        mock_send.assert_called_once_with(
            "test@example.com", "Test Subtask", "Looks good", "Jane Doe",
            True, "Parent Task", 1700000000
        )

    def test_send_comment_notification_missing_body(self, client):
        """Test POST /email/send-comment-notification with missing body"""
        response = client.post('/email/send-comment-notification')
        assert response.status_code == 400

    def test_send_comment_notification_invalid_json(self, client):
        """Test POST /email/send-comment-notification with invalid JSON"""
        response = client.post('/email/send-comment-notification',
                              data="invalid",
                              content_type='application/json')
        assert response.status_code == 400

    def test_send_comment_notification_missing_fields(self, client):
        """Test POST /email/send-comment-notification with missing fields"""
        response = client.post('/email/send-comment-notification', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Task"
        })
        assert response.status_code == 400

    @patch('app.email_service.send_comment_notification_email')
    def test_send_comment_notification_failure(self, mock_send, client):
        """Test POST /email/send-comment-notification failure"""
        mock_send.return_value = False

        response = client.post('/email/send-comment-notification', json={
            "toEmail": "test@example.com",
            "taskTitle": "Test Task",
            "commentText": "Comment",
            "commenterName": "John"
        })

        assert response.status_code == 500


class TestDeadlineExtensionRequestEndpoint:
    """Test deadline extension request email endpoint"""

    @patch('app.email_service.send_deadline_extension_request_email')
    def test_send_deadline_extension_request_success(self, mock_send, client):
        """Test POST /email/send-deadline-extension-request success"""
        mock_send.return_value = True

        response = client.post('/email/send-deadline-extension-request', json={
            "toEmail": "owner@example.com",
            "itemTitle": "Test Task",
            "requesterName": "John Doe",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1700086400,
            "reason": "Need more time"
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Deadline extension request email sent successfully"

    @patch('app.email_service.send_deadline_extension_request_email')
    def test_send_deadline_extension_request_with_subtask(self, mock_send, client):
        """Test POST /email/send-deadline-extension-request for subtask"""
        mock_send.return_value = True

        response = client.post('/email/send-deadline-extension-request', json={
            "toEmail": "owner@example.com",
            "itemTitle": "Test Subtask",
            "requesterName": "Jane Doe",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1700086400,
            "reason": "Extended work needed",
            "itemType": "subtask",
            "parentTaskTitle": "Parent Task"
        })

        assert response.status_code == 200
        mock_send.assert_called_once()

    def test_send_deadline_extension_request_missing_body(self, client):
        """Test POST /email/send-deadline-extension-request with missing body"""
        response = client.post('/email/send-deadline-extension-request')
        assert response.status_code == 400

    def test_send_deadline_extension_request_invalid_json(self, client):
        """Test POST /email/send-deadline-extension-request with invalid JSON"""
        response = client.post('/email/send-deadline-extension-request',
                              data="invalid",
                              content_type='application/json')
        assert response.status_code == 400

    def test_send_deadline_extension_request_missing_fields(self, client):
        """Test POST /email/send-deadline-extension-request with missing fields"""
        response = client.post('/email/send-deadline-extension-request', json={
            "toEmail": "owner@example.com",
            "itemTitle": "Test Task"
        })
        assert response.status_code == 400

    @patch('app.email_service.send_deadline_extension_request_email')
    def test_send_deadline_extension_request_failure(self, mock_send, client):
        """Test POST /email/send-deadline-extension-request failure"""
        mock_send.return_value = False

        response = client.post('/email/send-deadline-extension-request', json={
            "toEmail": "owner@example.com",
            "itemTitle": "Test Task",
            "requesterName": "John",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1700086400
        })

        assert response.status_code == 500


class TestDeadlineExtensionResponseEndpoint:
    """Test deadline extension response email endpoint"""

    @patch('app.email_service.send_deadline_extension_response_email')
    def test_send_deadline_extension_response_approved(self, mock_send, client):
        """Test POST /email/send-deadline-extension-response approved"""
        mock_send.return_value = True

        response = client.post('/email/send-deadline-extension-response', json={
            "toEmail": "requester@example.com",
            "itemTitle": "Test Task",
            "status": "approved",
            "newDeadline": 1700086400
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Deadline extension response email sent successfully"

    @patch('app.email_service.send_deadline_extension_response_email')
    def test_send_deadline_extension_response_rejected(self, mock_send, client):
        """Test POST /email/send-deadline-extension-response rejected"""
        mock_send.return_value = True

        response = client.post('/email/send-deadline-extension-response', json={
            "toEmail": "requester@example.com",
            "itemTitle": "Test Task",
            "status": "rejected",
            "rejectionReason": "Timeline is fixed",
            "itemType": "subtask",
            "parentTaskTitle": "Parent"
        })

        assert response.status_code == 200
        mock_send.assert_called_once()

    def test_send_deadline_extension_response_missing_body(self, client):
        """Test POST /email/send-deadline-extension-response with missing body"""
        response = client.post('/email/send-deadline-extension-response')
        assert response.status_code == 400

    def test_send_deadline_extension_response_invalid_json(self, client):
        """Test POST /email/send-deadline-extension-response with invalid JSON"""
        response = client.post('/email/send-deadline-extension-response',
                              data="invalid",
                              content_type='application/json')
        assert response.status_code == 400

    def test_send_deadline_extension_response_missing_fields(self, client):
        """Test POST /email/send-deadline-extension-response with missing fields"""
        response = client.post('/email/send-deadline-extension-response', json={
            "toEmail": "requester@example.com"
        })
        assert response.status_code == 400

    @patch('app.email_service.send_deadline_extension_response_email')
    def test_send_deadline_extension_response_failure(self, mock_send, client):
        """Test POST /email/send-deadline-extension-response failure"""
        mock_send.return_value = False

        response = client.post('/email/send-deadline-extension-response', json={
            "toEmail": "requester@example.com",
            "itemTitle": "Test Task",
            "status": "approved"
        })

        assert response.status_code == 500


class TestDeadlineChangedEndpoint:
    """Test deadline changed email endpoint"""

    @patch('app.email_service.send_deadline_changed_email')
    def test_send_deadline_changed_success(self, mock_send, client):
        """Test POST /email/send-deadline-changed success"""
        mock_send.return_value = True

        response = client.post('/email/send-deadline-changed', json={
            "toEmail": "collaborator@example.com",
            "itemTitle": "Test Task",
            "newDeadline": 1700086400
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Deadline changed email sent successfully"

    @patch('app.email_service.send_deadline_changed_email')
    def test_send_deadline_changed_with_requester(self, mock_send, client):
        """Test POST /email/send-deadline-changed with requester"""
        mock_send.return_value = True

        response = client.post('/email/send-deadline-changed', json={
            "toEmail": "collaborator@example.com",
            "itemTitle": "Test Subtask",
            "newDeadline": 1700086400,
            "requesterName": "John Doe",
            "itemType": "subtask",
            "parentTaskTitle": "Parent Task"
        })

        assert response.status_code == 200
        mock_send.assert_called_once_with(
            "collaborator@example.com", "Test Subtask", 1700086400,
            "John Doe", "subtask", "Parent Task"
        )

    def test_send_deadline_changed_missing_body(self, client):
        """Test POST /email/send-deadline-changed with missing body"""
        response = client.post('/email/send-deadline-changed')
        assert response.status_code == 400

    def test_send_deadline_changed_invalid_json(self, client):
        """Test POST /email/send-deadline-changed with invalid JSON"""
        response = client.post('/email/send-deadline-changed',
                              data="invalid",
                              content_type='application/json')
        assert response.status_code == 400

    def test_send_deadline_changed_missing_fields(self, client):
        """Test POST /email/send-deadline-changed with missing fields"""
        response = client.post('/email/send-deadline-changed', json={
            "toEmail": "collaborator@example.com"
        })
        assert response.status_code == 400

    @patch('app.email_service.send_deadline_changed_email')
    def test_send_deadline_changed_failure(self, mock_send, client):
        """Test POST /email/send-deadline-changed failure"""
        mock_send.return_value = False

        response = client.post('/email/send-deadline-changed', json={
            "toEmail": "collaborator@example.com",
            "itemTitle": "Test Task",
            "newDeadline": 1700086400
        })

        assert response.status_code == 500


if __name__ == '__main__':
    pytest.main([__file__, '-v'])