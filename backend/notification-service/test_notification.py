# backend/notification-service/test_notification.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# Set environment variables before imports
os.environ['JSON_PATH'] = '/tmp/dummy.json'
os.environ['DATABASE_URL'] = 'https://dummy.firebaseio.com'
os.environ['EMAIL_SERVICE_URL'] = 'http://email-service:6005'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Firebase BEFORE importing anything
with patch('firebase_admin.initialize_app'):
    with patch('firebase_admin.credentials.Certificate'):
        with patch('firebase_admin.db.reference') as mock_db_ref:
            mock_db_ref.return_value = Mock()

            from notification_service import NotificationService
            from scheduler_service import SchedulerService
            from models import Notification
            from app import app
            from shared import current_timestamp

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db_refs():
    """Mock all database references"""
    with patch('notification_service.get_db_reference') as mock_notif, \
         patch('scheduler_service.get_db_reference') as mock_sched:
        yield {'notification': mock_notif, 'scheduler': mock_sched}

@pytest.fixture
def sample_notification():
    """Create sample notification"""
    return Notification(
        notification_id="n1",
        user_id="u1",
        notification_type="task_deadline_reminder",
        title="Task Deadline",
        message="Task due soon",
        task_title="Test Task",
        task_deadline=1700000000,
        days_until_deadline=3.0,
        read=False,
        created_at=1600000000,
        task_id="t1"
    )

class TestNotificationModels:
    """Test notification models"""
    
    def test_notification_from_dict(self):
        """Test creating Notification from dictionary"""
        data = {
            "notificationId": "n1",
            "userId": "u1",
            "type": "task_deadline_reminder",
            "title": "Task Deadline",
            "message": "Task due soon",
            "taskTitle": "Test Task",
            "taskDeadline": 1700000000,
            "daysUntilDeadline": 3,
            "read": False,
            "createdAt": 1600000000,
            "taskId": "t1",
            "subTaskId": "st1",
            "parentTaskTitle": "Parent"
        }
        notification = Notification.from_dict(data)
        
        assert notification.notification_id == "n1"
        assert notification.user_id == "u1"
        assert notification.notification_type == "task_deadline_reminder"
        assert notification.read == False
        assert notification.task_id == "t1"
        assert notification.subtask_id == "st1"
    
    def test_notification_to_dict(self, sample_notification):
        """Test converting Notification to dictionary"""
        data = sample_notification.to_dict()
        
        assert data["notificationId"] == "n1"
        assert data["userId"] == "u1"
        assert data["taskId"] == "t1"
        assert data["read"] == False
    
    def test_notification_to_dict_optional_fields(self):
        """Test to_dict with optional fields"""
        notification = Notification(
            notification_id="n1",
            user_id="u1",
            notification_type="task_deadline_reminder",
            title="Test",
            message="Message",
            task_title="Task",
            task_deadline=1700000000,
            days_until_deadline=3.0,
            read=False,
            created_at=1600000000,
            subtask_id="st1",
            parent_task_title="Parent"
        )
        data = notification.to_dict()
        
        assert "subTaskId" in data
        assert "parentTaskTitle" in data

class TestNotificationService:
    """Test notification service class"""
    
    def test_create_notification_task(self, mock_db_refs):
        """Test creating a task notification"""
        mock_notifications = Mock()
        mock_sent = Mock()
        mock_db = Mock()
        mock_db_refs['notification'].side_effect = lambda x=None: (
            mock_notifications if x == "notifications"
            else mock_sent if x == "notificationsSent"
            else mock_db
        )
        
        mock_user_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "test-notification-id"
        mock_user_ref.push.return_value = mock_new_ref
        mock_notifications.child.return_value = mock_user_ref
        
        service = NotificationService()
        
        task_data = {
            "title": "Test Task",
            "deadline": 1700000000
        }
        
        notification_id = service.create_notification(
            "u1", "t1", task_data, 3.0, is_subtask=False
        )
        
        assert notification_id == "test-notification-id"
        mock_new_ref.set.assert_called_once()
    
    def test_create_notification_subtask(self, mock_db_refs):
        """Test creating a subtask notification"""
        mock_notifications = Mock()
        mock_sent = Mock()
        mock_db = Mock()
        mock_db_refs['notification'].side_effect = lambda x=None: (
            mock_notifications if x == "notifications"
            else mock_sent if x == "notificationsSent"
            else mock_db
        )
        
        mock_user_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-notif"
        mock_user_ref.push.return_value = mock_new_ref
        mock_notifications.child.return_value = mock_user_ref
        
        service = NotificationService()
        
        subtask_data = {
            "title": "Test Subtask",
            "deadline": 1700000000,
            "taskId": "t1"
        }
        
        notification_id = service.create_notification(
            "u1", "st1", subtask_data, 2.0, 
            is_subtask=True, parent_task_title="Parent Task"
        )
        
        assert notification_id == "test-subtask-notif"
    
    def test_get_user_notifications(self, mock_db_refs):
        """Test getting user notifications"""
        mock_notifications = Mock()
        mock_db_refs['notification'].return_value = mock_notifications
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = {
            "n1": {
                "notificationId": "n1",
                "userId": "u1",
                "type": "task_deadline_reminder",
                "title": "Test",
                "message": "Test message",
                "taskTitle": "Task",
                "taskDeadline": 1700000000,
                "daysUntilDeadline": 3,
                "read": False,
                "createdAt": 1600000000
            },
            "n2": {
                "notificationId": "n2",
                "userId": "u1",
                "type": "task_deadline_reminder",
                "title": "Test2",
                "message": "Test message 2",
                "taskTitle": "Task2",
                "taskDeadline": 1700000000,
                "daysUntilDeadline": 5,
                "read": True,
                "createdAt": 1600001000
            }
        }
        mock_notifications.child.return_value = mock_user_ref
        
        service = NotificationService()
        notifications = service.get_user_notifications("u1")
        
        assert len(notifications) == 2
        # Should be sorted by created_at descending
        assert notifications[0].notification_id == "n2"
    
    def test_get_unread_notifications(self, mock_db_refs):
        """Test getting unread notifications"""
        mock_notifications = Mock()
        mock_db_refs['notification'].return_value = mock_notifications
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = {
            "n1": {
                "notificationId": "n1",
                "userId": "u1",
                "type": "task_deadline_reminder",
                "title": "Test",
                "message": "Test",
                "taskTitle": "Task",
                "taskDeadline": 1700000000,
                "daysUntilDeadline": 3,
                "read": False,
                "createdAt": 1600000000
            },
            "n2": {
                "notificationId": "n2",
                "userId": "u1",
                "type": "task_deadline_reminder",
                "title": "Test2",
                "message": "Test2",
                "taskTitle": "Task2",
                "taskDeadline": 1700000000,
                "daysUntilDeadline": 5,
                "read": True,
                "createdAt": 1600001000
            }
        }
        mock_notifications.child.return_value = mock_user_ref
        
        service = NotificationService()
        unread = service.get_unread_notifications("u1")
        
        assert len(unread) == 1
        assert unread[0].notification_id == "n1"
        assert unread[0].read == False
    
    def test_mark_notification_read(self, mock_db_refs):
        """Test marking notification as read"""
        mock_notifications = Mock()
        mock_db_refs['notification'].return_value = mock_notifications
        
        mock_notification_ref = Mock()
        mock_notification_ref.get.return_value = {
            "notificationId": "n1",
            "userId": "u1",
            "type": "task_deadline_reminder",
            "title": "Test",
            "message": "Test",
            "taskTitle": "Task",
            "taskDeadline": 1700000000,
            "daysUntilDeadline": 3,
            "read": False,
            "createdAt": 1600000000,
            "readAt": None
        }
        
        mock_notifications.child.return_value.child.return_value = mock_notification_ref
        
        service = NotificationService()
        notification, error = service.mark_notification_read("u1", "n1")
        
        assert error is None
        assert notification is not None
        mock_notification_ref.update.assert_called_once()
    
    def test_mark_notification_read_not_found(self, mock_db_refs):
        """Test marking non-existent notification as read"""
        mock_notifications = Mock()
        mock_db_refs['notification'].return_value = mock_notifications
        
        mock_notification_ref = Mock()
        mock_notification_ref.get.return_value = None
        
        mock_notifications.child.return_value.child.return_value = mock_notification_ref
        
        service = NotificationService()
        notification, error = service.mark_notification_read("u1", "invalid")
        
        assert notification is None
        assert error == "Notification not found"
    
    def test_delete_notification(self, mock_db_refs):
        """Test deleting notification"""
        mock_notifications = Mock()
        mock_db_refs['notification'].return_value = mock_notifications
        
        mock_notification_ref = Mock()
        mock_notification_ref.get.return_value = {"notificationId": "n1"}
        
        mock_notifications.child.return_value.child.return_value = mock_notification_ref
        
        service = NotificationService()
        success, error = service.delete_notification("u1", "n1")
        
        assert success == True
        assert error is None
        mock_notification_ref.delete.assert_called_once()
    
    def test_mark_all_notifications_read(self, mock_db_refs):
        """Test marking all notifications as read"""
        mock_notifications = Mock()
        mock_db_refs['notification'].return_value = mock_notifications
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = {
            "n1": {"read": False},
            "n2": {"read": False},
            "n3": {"read": True}
        }
        mock_user_ref.child.return_value = Mock()
        mock_notifications.child.return_value = mock_user_ref
        
        service = NotificationService()
        count = service.mark_all_notifications_read("u1")
        
        assert count == 2
    
    def test_should_send_notification_no_match(self, mock_db_refs):
        """Test should_send_notification with no matching reminder time"""
        mock_sent = Mock()
        mock_notifications = Mock()
        mock_db = Mock()
        mock_db_refs['notification'].side_effect = lambda x=None: (
            mock_notifications if x == "notifications"
            else mock_sent if x == "notificationsSent"
            else mock_db
        )
        
        service = NotificationService()
        result = service.should_send_notification("t1", "u1", 5.0, [1, 3, 7])
        
        assert result == False
    
    def test_should_send_notification_match(self, mock_db_refs):
        """Test should_send_notification with matching reminder time"""
        mock_notifications = Mock()
        mock_sent = Mock()
        mock_db = Mock()
        mock_db_refs['notification'].side_effect = lambda x=None: (
            mock_notifications if x == "notifications"
            else mock_sent if x == "notificationsSent"
            else mock_db
        )
        
        mock_sent_ref = Mock()
        mock_sent_ref.get.return_value = None
        mock_sent.child.return_value = mock_sent_ref
        
        service = NotificationService()
        result = service.should_send_notification("t1", "u1", 3.2, [1, 3, 7])
        
        assert result == 3
    
    def test_mark_notification_sent(self, mock_db_refs):
        """Test marking notification as sent"""
        mock_sent = Mock()
        mock_notifications = Mock()
        mock_db = Mock()
        mock_db_refs['notification'].side_effect = lambda x=None: (
            mock_notifications if x == "notifications"
            else mock_sent if x == "notificationsSent"
            else mock_db
        )
        
        mock_sent_ref = Mock()
        mock_sent.child.return_value = mock_sent_ref
        
        service = NotificationService()
        service.mark_notification_sent("t1", "u1", 3)
        
        mock_sent_ref.set.assert_called_once()

class TestSchedulerService:
    """Test scheduler service class"""
    
    @patch('scheduler_service.requests.post')
    def test_send_email_notification_success(self, mock_post, mock_db_refs):
        """Test successful email notification sending"""
        mock_post.return_value.status_code = 200
        
        # Mock all required database references
        for ref_name in ["tasks", "subtasks", "notificationPreferences", "users"]:
            mock_db_refs['scheduler'].side_effect = lambda x: Mock()
        
        service = SchedulerService("http://email-service:6005")
        
        task_data = {
            "title": "Test Task",
            "deadline": 1700000000,
            "notes": "Test notes"
        }
        
        result = service.send_email_notification(
            "test@example.com",
            task_data,
            3.0
        )
        
        assert result == True
        mock_post.assert_called_once()
        
        # Verify the payload
        call_args = mock_post.call_args
        assert call_args[1]['json']['toEmail'] == "test@example.com"
        assert call_args[1]['json']['taskTitle'] == "Test Task"
    
    @patch('scheduler_service.requests.post')
    def test_send_email_notification_failure(self, mock_post, mock_db_refs):
        """Test failed email notification sending"""
        mock_post.return_value.status_code = 500
        
        for ref_name in ["tasks", "subtasks", "notificationPreferences", "users"]:
            mock_db_refs['scheduler'].side_effect = lambda x: Mock()
        
        service = SchedulerService("http://email-service:6005")
        
        task_data = {
            "title": "Test Task",
            "deadline": 1700000000,
            "notes": ""
        }
        
        result = service.send_email_notification(
            "test@example.com",
            task_data,
            3.0
        )
        
        assert result == False
    
    @patch('scheduler_service.requests.post')
    def test_send_email_notification_with_subtask(self, mock_post, mock_db_refs):
        """Test email notification for subtask"""
        mock_post.return_value.status_code = 200
        
        for ref_name in ["tasks", "subtasks", "notificationPreferences", "users"]:
            mock_db_refs['scheduler'].side_effect = lambda x: Mock()
        
        service = SchedulerService("http://email-service:6005")
        
        subtask_data = {
            "title": "Test Subtask",
            "deadline": 1700000000,
            "notes": "Subtask notes"
        }
        
        result = service.send_email_notification(
            "test@example.com",
            subtask_data,
            2.0,
            is_subtask=True,
            parent_task_title="Parent Task"
        )
        
        assert result == True
        call_args = mock_post.call_args
        assert call_args[1]['json']['isSubtask'] == True
        assert call_args[1]['json']['parentTaskTitle'] == "Parent Task"

class TestNotificationEndpoints:
    """Test Flask endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'notification-service'
    
    @patch('app.notification_service.get_user_notifications')
    def test_get_user_notifications(self, mock_get, client, sample_notification):
        """Test getting user notifications endpoint"""
        mock_get.return_value = [sample_notification]
        
        response = client.get('/notifications/u1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'notifications' in data
        assert len(data['notifications']) == 1
    
    @patch('app.notification_service.get_unread_notifications')
    def test_get_unread_notifications(self, mock_get, client):
        """Test getting unread notifications endpoint"""
        mock_get.return_value = []
        
        response = client.get('/notifications/u1/unread')
        assert response.status_code == 200
        data = response.get_json()
        assert 'count' in data
        assert data['count'] == 0
    
    @patch('app.notification_service.mark_notification_read')
    def test_mark_notification_read(self, mock_mark, client, sample_notification):
        """Test marking notification as read endpoint"""
        mock_mark.return_value = (sample_notification, None)
        
        response = client.patch('/notifications/u1/n1/read')
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'notification' in data
    
    @patch('app.notification_service.mark_notification_read')
    def test_mark_notification_read_not_found(self, mock_mark, client):
        """Test marking non-existent notification as read"""
        mock_mark.return_value = (None, "Notification not found")
        
        response = client.patch('/notifications/u1/invalid/read')
        assert response.status_code == 404
    
    @patch('app.notification_service.delete_notification')
    def test_delete_notification(self, mock_delete, client):
        """Test deleting notification endpoint"""
        mock_delete.return_value = (True, None)
        
        response = client.delete('/notifications/u1/n1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    @patch('app.notification_service.mark_all_notifications_read')
    def test_mark_all_read(self, mock_mark_all, client):
        """Test marking all notifications as read"""
        mock_mark_all.return_value = 5
        
        response = client.patch('/notifications/u1/mark-all-read')
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 5
    
    @patch('app.scheduler_service.trigger_manually')
    def test_trigger_scheduler(self, mock_trigger, client):
        """Test triggering scheduler manually"""
        response = client.post('/scheduler/trigger')
        assert response.status_code == 200
        mock_trigger.assert_called_once()

    @patch('app.notification_service.create_task_update_notification')
    @patch('app.notification_service.check_duplicate_update_notification')
    def test_send_task_update_notification_in_app(self, mock_check_dup, mock_create, client):
        """Test sending task update notification (in-app only)"""
        mock_check_dup.return_value = False
        mock_create.return_value = "notif123"

        data = {
            "itemId": "t1",
            "taskTitle": "Test Task",
            "oldStatus": "in_progress",
            "newStatus": "completed",
            "userIds": ["u1", "u2"],
            "channel": "in-app"
        }

        response = client.post('/notifications/task-update', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notificationsSent']) == 2

    @patch('requests.post')
    @patch('app.notification_service.create_task_update_notification')
    @patch('app.notification_service.check_duplicate_update_notification')
    def test_send_task_update_notification_both_channels(self, mock_check_dup, mock_create, mock_post, client):
        """Test sending task update notification (both channels)"""
        mock_check_dup.return_value = False
        mock_create.return_value = "notif123"
        mock_post.return_value.status_code = 200

        data = {
            "itemId": "st1",
            "taskTitle": "Test Subtask",
            "oldStatus": "to_do",
            "newStatus": "in_progress",
            "userIds": ["u1"],
            "channel": "both",
            "isSubtask": True,
            "parentTaskTitle": "Parent Task",
            "userEmails": {"u1": "user1@example.com"}
        }

        response = client.post('/notifications/task-update', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notificationsSent']) == 1
        assert len(data['emailsSent']) == 1

    @patch('app.notification_service.check_duplicate_update_notification')
    def test_send_task_update_notification_duplicate(self, mock_check_dup, client):
        """Test skipping duplicate task update notification"""
        mock_check_dup.return_value = True

        data = {
            "itemId": "t1",
            "taskTitle": "Test Task",
            "oldStatus": "in_progress",
            "newStatus": "completed",
            "userIds": ["u1"],
            "channel": "in-app"
        }

        response = client.post('/notifications/task-update', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notificationsSent']) == 0

    def test_send_task_update_notification_missing_field(self, client):
        """Test task update notification with missing fields"""
        data = {
            "itemId": "t1",
            "taskTitle": "Test Task"
        }

        response = client.post('/notifications/task-update', json=data)
        assert response.status_code == 400

    @patch('app.notification_service.create_comment_notification')
    @patch('app.notification_service.check_duplicate_comment_notification')
    def test_send_comment_notification_in_app(self, mock_check_dup, mock_create, client):
        """Test sending comment notification (in-app only)"""
        mock_check_dup.return_value = False
        mock_create.return_value = "notif456"

        data = {
            "itemId": "t1",
            "taskTitle": "Test Task",
            "commentText": "Great work!",
            "commenterName": "John",
            "commenterId": "u1",
            "recipientIds": ["u2", "u3"],
            "channel": "in-app"
        }

        response = client.post('/notifications/comment', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notificationsSent']) == 2

    @patch('app.notification_service.create_comment_notification')
    @patch('app.notification_service.check_duplicate_comment_notification')
    def test_send_comment_notification_skip_commenter(self, mock_check_dup, mock_create, client):
        """Test comment notification doesn't notify commenter"""
        mock_check_dup.return_value = False
        mock_create.return_value = "notif456"

        data = {
            "itemId": "t1",
            "taskTitle": "Test Task",
            "commentText": "Great work!",
            "commenterName": "John",
            "commenterId": "u1",
            "recipientIds": ["u1", "u2"],
            "channel": "in-app"
        }

        response = client.post('/notifications/comment', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notificationsSent']) == 1

    @patch('requests.post')
    @patch('app.notification_service.create_comment_notification')
    @patch('app.notification_service.check_duplicate_comment_notification')
    def test_send_comment_notification_with_email(self, mock_check_dup, mock_create, mock_post, client):
        """Test sending comment notification with email"""
        mock_check_dup.return_value = False
        mock_create.return_value = "notif456"
        mock_post.return_value.status_code = 200

        data = {
            "itemId": "st1",
            "taskTitle": "Test Subtask",
            "commentText": "Looks good",
            "commenterName": "Jane",
            "commenterId": "u1",
            "recipientIds": ["u2"],
            "channel": "both",
            "isSubtask": True,
            "parentTaskTitle": "Parent",
            "taskDeadline": 1700000000,
            "recipientEmails": {"u2": "user2@example.com"}
        }

        response = client.post('/notifications/comment', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['emailsSent']) == 1

    @patch('app.notification_service.create_deadline_extension_request_notification')
    def test_send_deadline_extension_request_in_app(self, mock_create, client):
        """Test sending deadline extension request notification"""
        mock_create.return_value = "notif789"

        data = {
            "ownerId": "u1",
            "itemId": "t1",
            "itemTitle": "Test Task",
            "requesterId": "u2",
            "itemType": "task",
            "extensionRequestId": "er1"
        }

        response = client.post('/notifications/deadline-extension-request', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['notificationSent'] == True

    @patch('requests.post')
    @patch('app.notification_service.create_deadline_extension_request_notification')
    def test_send_deadline_extension_request_with_email(self, mock_create, mock_post, client):
        """Test sending deadline extension request with email"""
        mock_create.return_value = "notif789"
        mock_post.return_value.status_code = 200

        data = {
            "ownerId": "u1",
            "itemId": "st1",
            "itemTitle": "Test Subtask",
            "requesterId": "u2",
            "itemType": "subtask",
            "extensionRequestId": "er1",
            "channel": "both",
            "ownerEmail": "owner@example.com",
            "requesterName": "John",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1710000000,
            "reason": "Need more time",
            "parentTaskTitle": "Parent"
        }

        response = client.post('/notifications/deadline-extension-request', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['emailSent'] == True

    @patch('app.notification_service.create_deadline_extension_response_notification')
    def test_send_deadline_extension_response(self, mock_create, client):
        """Test sending deadline extension response notification"""
        mock_create.return_value = "notif890"

        data = {
            "requesterId": "u2",
            "itemId": "t1",
            "itemType": "task",
            "status": "approved",
            "itemTitle": "Test Task",
            "newDeadline": 1710000000
        }

        response = client.post('/notifications/deadline-extension-response', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['notificationSent'] == True

    @patch('app.notification_service.create_deadline_extension_response_notification')
    @patch('app.notification_service.db')
    def test_send_deadline_extension_response_without_title(self, mock_db, mock_create, client):
        """Test extension response notification fetching title from DB"""
        mock_create.return_value = "notif890"
        mock_ref = Mock()
        mock_ref.get.return_value = {"title": "Fetched Task"}
        mock_db.reference.return_value = mock_ref

        data = {
            "requesterId": "u2",
            "itemId": "t1",
            "itemType": "task",
            "status": "rejected",
            "rejectionReason": "Cannot extend"
        }

        response = client.post('/notifications/deadline-extension-response', json=data)
        assert response.status_code == 200

    @patch('requests.post')
    @patch('app.notification_service.create_deadline_extension_response_notification')
    def test_send_deadline_extension_response_with_email(self, mock_create, mock_post, client):
        """Test extension response notification with email"""
        mock_create.return_value = "notif890"
        mock_post.return_value.status_code = 200

        data = {
            "requesterId": "u2",
            "itemId": "st1",
            "itemType": "subtask",
            "status": "approved",
            "itemTitle": "Test Subtask",
            "newDeadline": 1710000000,
            "channel": "both",
            "requesterEmail": "requester@example.com",
            "parentTaskTitle": "Parent"
        }

        response = client.post('/notifications/deadline-extension-response', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert data['emailSent'] == True

    @patch('app.notification_service.create_deadline_changed_notification')
    def test_send_deadline_changed_notification(self, mock_create, client):
        """Test sending deadline changed notification"""
        mock_create.return_value = "notif901"

        data = {
            "itemId": "t1",
            "itemTitle": "Test Task",
            "itemType": "task",
            "collaboratorIds": ["u1", "u2"],
            "newDeadline": 1710000000
        }

        response = client.post('/notifications/deadline-changed', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notificationsSent']) == 2

    @patch('requests.post')
    @patch('app.notification_service.create_deadline_changed_notification')
    def test_send_deadline_changed_notification_with_email(self, mock_create, mock_post, client):
        """Test deadline changed notification with email"""
        mock_create.return_value = "notif901"
        mock_post.return_value.status_code = 200

        data = {
            "itemId": "st1",
            "itemTitle": "Test Subtask",
            "itemType": "subtask",
            "collaboratorIds": ["u1"],
            "newDeadline": 1710000000,
            "requesterId": "u2",
            "channel": "both",
            "userEmails": {"u1": "user1@example.com"},
            "requesterName": "John",
            "parentTaskTitle": "Parent"
        }

        response = client.post('/notifications/deadline-changed', json=data)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['emailsSent']) == 1

    # Error handling tests
    @patch('app.notification_service.get_user_notifications')
    def test_get_user_notifications_error(self, mock_get, client):
        """Test error handling in get_user_notifications"""
        mock_get.side_effect = Exception("Database error")

        response = client.get('/notifications/u1')
        assert response.status_code == 500

    @patch('app.notification_service.get_unread_notifications')
    def test_get_unread_notifications_error(self, mock_get, client):
        """Test error handling in get_unread_notifications"""
        mock_get.side_effect = Exception("Database error")

        response = client.get('/notifications/u1/unread')
        assert response.status_code == 500

    @patch('app.notification_service.mark_notification_read')
    def test_mark_notification_read_error(self, mock_mark, client):
        """Test error handling in mark_notification_read"""
        mock_mark.side_effect = Exception("Database error")

        response = client.patch('/notifications/u1/n1/read')
        assert response.status_code == 500

    @patch('app.notification_service.delete_notification')
    def test_delete_notification_error(self, mock_delete, client):
        """Test error handling in delete_notification"""
        mock_delete.side_effect = Exception("Database error")

        response = client.delete('/notifications/u1/n1')
        assert response.status_code == 500

    @patch('app.notification_service.delete_notification')
    def test_delete_notification_not_found(self, mock_delete, client):
        """Test deleting non-existent notification"""
        mock_delete.return_value = (False, "Notification not found")

        response = client.delete('/notifications/u1/invalid')
        assert response.status_code == 404

    @patch('app.notification_service.mark_all_notifications_read')
    def test_mark_all_read_error(self, mock_mark_all, client):
        """Test error handling in mark_all_notifications_read"""
        mock_mark_all.side_effect = Exception("Database error")

        response = client.patch('/notifications/u1/mark-all-read')
        assert response.status_code == 500

    @patch('app.scheduler_service.trigger_manually')
    def test_trigger_scheduler_error(self, mock_trigger, client):
        """Test error handling in trigger_scheduler"""
        mock_trigger.side_effect = Exception("Scheduler error")

        response = client.post('/scheduler/trigger')
        assert response.status_code == 500

    @patch('app.notification_service.create_task_update_notification')
    def test_send_task_update_notification_error(self, mock_create, client):
        """Test error handling in send_task_update_notification"""
        mock_create.side_effect = Exception("Creation error")

        data = {
            "itemId": "t1",
            "taskTitle": "Test Task",
            "oldStatus": "in_progress",
            "newStatus": "completed",
            "userIds": ["u1"],
            "channel": "in-app"
        }

        response = client.post('/notifications/task-update', json=data)
        assert response.status_code == 500

    def test_send_comment_notification_missing_field(self, client):
        """Test comment notification with missing fields"""
        data = {
            "itemId": "t1",
            "taskTitle": "Test Task"
        }

        response = client.post('/notifications/comment', json=data)
        assert response.status_code == 400

    def test_send_deadline_extension_request_missing_field(self, client):
        """Test extension request with missing fields"""
        data = {
            "ownerId": "u1",
            "itemId": "t1"
        }

        response = client.post('/notifications/deadline-extension-request', json=data)
        assert response.status_code == 400

    def test_send_deadline_extension_response_missing_field(self, client):
        """Test extension response with missing fields"""
        data = {
            "requesterId": "u2"
        }

        response = client.post('/notifications/deadline-extension-response', json=data)
        assert response.status_code == 400

    def test_send_deadline_changed_notification_missing_field(self, client):
        """Test deadline changed with missing fields"""
        data = {
            "itemId": "t1"
        }

        response = client.post('/notifications/deadline-changed', json=data)
        assert response.status_code == 400

    @patch('app.notification_service.create_deadline_extension_request_notification')
    def test_send_deadline_extension_request_failure(self, mock_create, client):
        """Test extension request notification failure"""
        mock_create.return_value = None

        data = {
            "ownerId": "u1",
            "itemId": "t1",
            "itemTitle": "Test Task",
            "requesterId": "u2",
            "itemType": "task",
            "extensionRequestId": "er1"
        }

        response = client.post('/notifications/deadline-extension-request', json=data)
        assert response.status_code == 500

    @patch('app.notification_service.create_deadline_extension_response_notification')
    def test_send_deadline_extension_response_failure(self, mock_create, client):
        """Test extension response notification failure"""
        mock_create.return_value = None

        data = {
            "requesterId": "u2",
            "itemId": "t1",
            "itemType": "task",
            "status": "approved",
            "itemTitle": "Test Task"
        }

        response = client.post('/notifications/deadline-extension-response', json=data)
        assert response.status_code == 500

class TestNotificationServiceMethods:
    """Test additional notification service methods"""

    @patch('notification_service.get_db_reference')
    def test_create_task_update_notification_task(self, mock_ref):
        """Test creating task status update notification"""
        mock_notif_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "notif123"
        mock_notif_ref.child.return_value.push.return_value = mock_new_ref
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        notif_id = service.create_task_update_notification(
            "u1", "t1", "Test Task", "to_do", "in_progress"
        )

        assert notif_id == "notif123"
        mock_new_ref.set.assert_called_once()

    @patch('notification_service.get_db_reference')
    def test_create_task_update_notification_subtask(self, mock_ref):
        """Test creating subtask status update notification"""
        mock_notif_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "notif456"
        mock_notif_ref.child.return_value.push.return_value = mock_new_ref
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        notif_id = service.create_task_update_notification(
            "u1", "st1", "Test Subtask", "in_progress", "completed",
            is_subtask=True, parent_task_title="Parent Task"
        )

        assert notif_id == "notif456"

    @patch('notification_service.get_db_reference')
    def test_check_duplicate_update_notification_found(self, mock_ref):
        """Test duplicate update notification detection"""
        mock_notif_ref = Mock()
        mock_notif_ref.child.return_value.get.return_value = {
            "n1": {
                "type": "task_status_update",
                "taskId": "t1",
                "newStatus": "completed",
                "createdAt": current_timestamp() - 60
            }
        }
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        is_duplicate = service.check_duplicate_update_notification(
            "u1", "t1", "completed", is_subtask=False
        )

        assert is_duplicate == True

    @patch('notification_service.get_db_reference')
    def test_check_duplicate_update_notification_not_found(self, mock_ref):
        """Test no duplicate update notification"""
        mock_notif_ref = Mock()
        mock_notif_ref.child.return_value.get.return_value = {
            "n1": {
                "type": "task_status_update",
                "taskId": "t1",
                "newStatus": "in_progress",
                "createdAt": current_timestamp() - 60
            }
        }
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        is_duplicate = service.check_duplicate_update_notification(
            "u1", "t1", "completed", is_subtask=False
        )

        assert is_duplicate == False

    @patch('notification_service.get_db_reference')
    def test_create_comment_notification_task(self, mock_ref):
        """Test creating comment notification for task"""
        mock_notif_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "notif789"
        mock_notif_ref.child.return_value.push.return_value = mock_new_ref
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        notif_id = service.create_comment_notification(
            "u1", "t1", "Test Task", "Great work!", "John", "u2", 1700000000
        )

        assert notif_id == "notif789"

    @patch('notification_service.get_db_reference')
    def test_create_comment_notification_long_text(self, mock_ref):
        """Test comment notification with long comment text"""
        mock_notif_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "notif890"
        mock_notif_ref.child.return_value.push.return_value = mock_new_ref
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        long_comment = "A" * 150
        notif_id = service.create_comment_notification(
            "u1", "st1", "Test Subtask", long_comment, "Jane", "u2",
            is_subtask=True, parent_task_title="Parent"
        )

        assert notif_id == "notif890"

    @patch('notification_service.get_db_reference')
    def test_check_duplicate_comment_notification_found(self, mock_ref):
        """Test duplicate comment notification detection"""
        mock_notif_ref = Mock()
        mock_notif_ref.child.return_value.get.return_value = {
            "n1": {
                "type": "task_comment_notification",
                "taskId": "t1",
                "commenterId": "u2",
                "createdAt": current_timestamp() - 30
            }
        }
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        is_duplicate = service.check_duplicate_comment_notification(
            "u1", "t1", "u2", is_subtask=False
        )

        assert is_duplicate == True

    @patch('notification_service.get_db_reference')
    def test_create_deadline_extension_request_notification_task(self, mock_ref):
        """Test creating deadline extension request notification for task"""
        mock_notif_ref = Mock()
        mock_users_ref = Mock()
        mock_users_ref.child.return_value.get.return_value = {"name": "John Doe"}

        def side_effect(arg=None):
            if arg == "users":
                return mock_users_ref
            return mock_notif_ref

        mock_ref.side_effect = side_effect

        service = NotificationService()
        notif_id = service.create_deadline_extension_request_notification(
            "u1", "t1", "Test Task", "u2", "task", "er1"
        )

        assert notif_id is not None

    @patch('notification_service.get_db_reference')
    def test_create_deadline_extension_request_notification_subtask(self, mock_ref):
        """Test creating deadline extension request notification for subtask"""
        mock_notif_ref = Mock()
        mock_users_ref = Mock()
        mock_subtasks_ref = Mock()
        mock_tasks_ref = Mock()

        mock_users_ref.child.return_value.get.return_value = {"name": "Jane Doe"}
        mock_subtasks_ref.child.return_value.get.return_value = {"taskId": "t1"}
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def side_effect(arg=None):
            if arg == "users":
                return mock_users_ref
            elif arg == "subtasks":
                return mock_subtasks_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return mock_notif_ref

        mock_ref.side_effect = side_effect

        service = NotificationService()
        notif_id = service.create_deadline_extension_request_notification(
            "u1", "st1", "Test Subtask", "u2", "subtask", "er1"
        )

        assert notif_id is not None

    @patch('notification_service.get_db_reference')
    def test_create_deadline_extension_response_notification_approved(self, mock_ref):
        """Test creating extension response notification (approved)"""
        mock_notif_ref = Mock()
        mock_ref.return_value = mock_notif_ref

        service = NotificationService()
        notif_id = service.create_deadline_extension_response_notification(
            "u2", "t1", "task", "Test Task", "approved", new_deadline=1710000000
        )

        assert notif_id is not None

    @patch('notification_service.get_db_reference')
    def test_create_deadline_extension_response_notification_rejected(self, mock_ref):
        """Test creating extension response notification (rejected)"""
        mock_notif_ref = Mock()
        mock_subtasks_ref = Mock()
        mock_tasks_ref = Mock()

        mock_subtasks_ref.child.return_value.get.return_value = {"taskId": "t1"}
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def side_effect(arg=None):
            if arg == "subtasks":
                return mock_subtasks_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return mock_notif_ref

        mock_ref.side_effect = side_effect

        service = NotificationService()
        notif_id = service.create_deadline_extension_response_notification(
            "u2", "st1", "subtask", "Test Subtask", "rejected",
            rejection_reason="Cannot approve"
        )

        assert notif_id is not None

    @patch('notification_service.get_db_reference')
    def test_create_deadline_changed_notification_with_requester(self, mock_ref):
        """Test creating deadline changed notification with requester"""
        mock_notif_ref = Mock()
        mock_users_ref = Mock()
        mock_users_ref.child.return_value.get.return_value = {"name": "John Doe"}

        def side_effect(arg=None):
            if arg == "users":
                return mock_users_ref
            return mock_notif_ref

        mock_ref.side_effect = side_effect

        service = NotificationService()
        notif_id = service.create_deadline_changed_notification(
            "u1", "t1", "task", "Test Task", 1710000000, requester_id="u2"
        )

        assert notif_id is not None

    @patch('notification_service.get_db_reference')
    def test_create_deadline_changed_notification_no_requester(self, mock_ref):
        """Test creating deadline changed notification without requester"""
        mock_notif_ref = Mock()
        mock_subtasks_ref = Mock()
        mock_tasks_ref = Mock()

        mock_subtasks_ref.child.return_value.get.return_value = {"taskId": "t1"}
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def side_effect(arg=None):
            if arg == "subtasks":
                return mock_subtasks_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return mock_notif_ref

        mock_ref.side_effect = side_effect

        service = NotificationService()
        notif_id = service.create_deadline_changed_notification(
            "u1", "st1", "subtask", "Test Subtask", 1710000000
        )

        assert notif_id is not None

    @patch('notification_service.get_db_reference')
    def test_get_user_name(self, mock_ref):
        """Test getting user name"""
        mock_users_ref = Mock()
        mock_users_ref.child.return_value.get.return_value = {"name": "Test User"}
        mock_ref.return_value = mock_users_ref

        service = NotificationService()
        name = service._get_user_name("u1")

        assert name == "Test User"

    @patch('notification_service.get_db_reference')
    def test_get_user_name_not_found(self, mock_ref):
        """Test getting user name when user not found"""
        mock_users_ref = Mock()
        mock_users_ref.child.return_value.get.return_value = None
        mock_ref.return_value = mock_users_ref

        service = NotificationService()
        name = service._get_user_name("invalid")

        assert name == "Unknown User"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])