# backend/extension-request-service/test_extension_request.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Set environment variables before imports
os.environ['JSON_PATH'] = '/tmp/dummy.json'
os.environ['DATABASE_URL'] = 'https://dummy.firebaseio.com'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a mock Firebase app
mock_firebase_app = MagicMock()

# Mock Firebase admin at module level BEFORE any imports
firebase_admin_patcher = patch.dict('sys.modules', {
    'firebase_admin': MagicMock(),
    'firebase_admin.credentials': MagicMock(),
    'firebase_admin.db': MagicMock()
})
firebase_admin_patcher.start()

from app import app
from extension_request_service import ExtensionRequestService
from models import ExtensionRequest, CreateExtensionRequestRequest, UpdateExtensionRequestRequest

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client



@pytest.fixture
def mock_db():
    """Mock Firebase database"""
    with patch('extension_request_service.get_db_reference') as mock:
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests library for HTTP calls"""
    with patch('extension_request_service.requests') as mock:
        yield mock


@pytest.fixture
def sample_task_data():
    """Sample task data for testing"""
    return {
        "taskId": "task-123",
        "title": "Test Task",
        "ownerId": "owner-user-123",
        "collaborators": ["collab-user-456", "collab-user-789"],
        "deadline": int(datetime.now().timestamp()) + 86400 * 7,  # 7 days from now
        "status": "ongoing"
    }


@pytest.fixture
def sample_subtask_data():
    """Sample subtask data for testing"""
    return {
        "subTaskId": "subtask-123",
        "title": "Test Subtask",
        "ownerId": "owner-user-123",
        "collaborators": ["collab-user-456"],
        "deadline": int(datetime.now().timestamp()) + 86400 * 5,  # 5 days from now
        "status": "ongoing",
        "taskId": "parent-task-123"
    }


class TestExtensionRequestModels:
    """Test data models"""
    
    def test_extension_request_from_dict(self):
        """Test creating ExtensionRequest from dictionary"""
        data = {
            "requestId": "req-123",
            "itemId": "task-123",
            "itemType": "task",
            "requesterId": "user-456",
            "ownerId": "user-789",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1700086400,
            "reason": "Need more time",
            "status": "pending",
            "createdAt": 1699000000
        }
        
        request = ExtensionRequest.from_dict(data)
        
        assert request.request_id == "req-123"
        assert request.item_id == "task-123"
        assert request.item_type == "task"
        assert request.requester_id == "user-456"
        assert request.owner_id == "user-789"
        assert request.status == "pending"
        assert request.rejection_reason is None
    
    def test_extension_request_to_dict(self):
        """Test converting ExtensionRequest to dictionary"""
        request = ExtensionRequest(
            request_id="req-123",
            item_id="task-123",
            item_type="task",
            requester_id="user-456",
            owner_id="user-789",
            current_deadline=1700000000,
            proposed_deadline=1700086400,
            reason="Need more time",
            status="pending",
            created_at=1699000000
        )
        
        data = request.to_dict()
        
        assert data["requestId"] == "req-123"
        assert data["itemType"] == "task"
        assert data["status"] == "pending"
        assert "rejectionReason" not in data
        assert "respondedAt" not in data
    
    def test_extension_request_to_dict_with_rejection(self):
        """Test converting ExtensionRequest with rejection to dictionary"""
        request = ExtensionRequest(
            request_id="req-123",
            item_id="task-123",
            item_type="task",
            requester_id="user-456",
            owner_id="user-789",
            current_deadline=1700000000,
            proposed_deadline=1700086400,
            reason="Need more time",
            status="rejected",
            created_at=1699000000,
            rejection_reason="Cannot extend",
            responded_at=1699500000
        )
        
        data = request.to_dict()
        
        assert data["status"] == "rejected"
        assert data["rejectionReason"] == "Cannot extend"
        assert data["respondedAt"] == 1699500000
    
    def test_create_extension_request_validation_success(self):
        """Test CreateExtensionRequestRequest validation with valid data"""
        req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="task",
            requester_id="user-456",
            proposed_deadline=1700086400,
            reason="Need more time for testing"
        )
        
        errors = req.validate()
        assert len(errors) == 0
    
    def test_create_extension_request_validation_missing_fields(self):
        """Test CreateExtensionRequestRequest validation with missing fields"""
        req = CreateExtensionRequestRequest(
            item_id="",
            item_type="task",
            requester_id="",
            proposed_deadline=0,
            reason=""
        )
        
        errors = req.validate()
        assert len(errors) > 0
        assert any("itemId" in error for error in errors)
        assert any("requesterId" in error for error in errors)
        assert any("proposedDeadline" in error for error in errors)
        assert any("reason" in error for error in errors)
    
    def test_create_extension_request_validation_invalid_item_type(self):
        """Test CreateExtensionRequestRequest validation with invalid item type"""
        req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="invalid",
            requester_id="user-456",
            proposed_deadline=1700086400,
            reason="Need more time"
        )
        
        errors = req.validate()
        assert len(errors) > 0
        assert any("itemType" in error for error in errors)
    
    def test_update_extension_request_validation_success(self):
        """Test UpdateExtensionRequestRequest validation with valid data"""
        req = UpdateExtensionRequestRequest(
            request_id="req-123",
            responder_id="user-789",
            status="approved"
        )
        
        errors = req.validate()
        assert len(errors) == 0
    
    def test_update_extension_request_validation_invalid_status(self):
        """Test UpdateExtensionRequestRequest validation with invalid status"""
        req = UpdateExtensionRequestRequest(
            request_id="req-123",
            responder_id="user-789",
            status="invalid"
        )
        
        errors = req.validate()
        assert len(errors) > 0
        assert any("status" in error for error in errors)


class TestExtensionRequestService:
    """Test service methods"""
    
    @patch('extension_request_service.current_timestamp')
    def test_create_extension_request_success(self, mock_timestamp, mock_db, mock_requests, sample_task_data):
        """Test successful creation of extension request"""
        mock_timestamp.return_value = 1699000000
        
        # Mock database references
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        mock_requests_ref.get.return_value = {} 

        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        # Mock task data retrieval
        mock_tasks_ref.child.return_value.get.return_value = sample_task_data
        
        # Mock requests.post for notification
        mock_requests.post.return_value.status_code = 200
        
        # Create service
        service = ExtensionRequestService()
        
        # Create request
        req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="task",
            requester_id="collab-user-456",
            proposed_deadline=sample_task_data["deadline"] + 86400,
            reason="Need more time for testing"
        )
        
        extension_request, error = service.create_extension_request(req)
        
        assert error is None
        assert extension_request is not None
        assert extension_request.item_id == "task-123"
        assert extension_request.status == "pending"
        assert extension_request.owner_id == sample_task_data["ownerId"]
    
    def test_create_extension_request_item_not_found(self, mock_db):
        """Test creation fails when task/subtask not found"""
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        
        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        # Mock task not found
        mock_tasks_ref.child.return_value.get.return_value = None
        
        service = ExtensionRequestService()
        
        req = CreateExtensionRequestRequest(
            item_id="nonexistent-task",
            item_type="task",
            requester_id="user-456",
            proposed_deadline=1700086400,
            reason="Need more time"
        )
        
        extension_request, error = service.create_extension_request(req)
        
        assert extension_request is None
        assert error == "Task not found"
    
    def test_create_extension_request_requester_not_collaborator(self, mock_db, sample_task_data):
        """Test creation fails when requester is not a collaborator"""
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        
        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        mock_tasks_ref.child.return_value.get.return_value = sample_task_data
        
        service = ExtensionRequestService()
        
        req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="task",
            requester_id="non-collab-user",
            proposed_deadline=sample_task_data["deadline"] + 86400,
            reason="Need more time"
        )
        
        extension_request, error = service.create_extension_request(req)
        
        assert extension_request is None
        assert error == "Requester must be a collaborator"
    
    def test_create_extension_request_owner_cannot_request(self, mock_db, sample_task_data):
        """Test creation fails when owner tries to request extension"""
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        
        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        mock_tasks_ref.child.return_value.get.return_value = sample_task_data
        
        service = ExtensionRequestService()
        
        req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="task",
            requester_id=sample_task_data["ownerId"],
            proposed_deadline=sample_task_data["deadline"] + 86400,
            reason="Need more time"
        )
        
        extension_request, error = service.create_extension_request(req)
        
        assert extension_request is None
        assert error == "Requester must be a collaborator"
    
    def test_create_extension_request_invalid_deadline(self, mock_db, sample_task_data):
        """Test creation fails when proposed deadline is not after current"""
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        
        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        mock_tasks_ref.child.return_value.get.return_value = sample_task_data
        
        service = ExtensionRequestService()
        
        req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="task",
            requester_id="collab-user-456",
            proposed_deadline=sample_task_data["deadline"] - 86400,  # Before current deadline
            reason="Need more time"
        )
        
        extension_request, error = service.create_extension_request(req)
        
        assert extension_request is None
        assert error == "Proposed deadline must be after current deadline"
    
    def test_create_extension_request_duplicate_pending(self, mock_db, sample_task_data):
        """Test creation fails when there's already a pending request"""
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        
        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        mock_tasks_ref.child.return_value.get.return_value = sample_task_data
        
        # Mock existing pending request
        existing_request = {
            "req-999": {
                "itemId": "task-123",
                "requesterId": "collab-user-456",
                "status": "pending"
            }
        }
        mock_requests_ref.get.return_value = existing_request
        
        service = ExtensionRequestService()
        
        req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="task",
            requester_id="collab-user-456",
            proposed_deadline=sample_task_data["deadline"] + 86400,
            reason="Need more time"
        )
        
        extension_request, error = service.create_extension_request(req)
        
        assert extension_request is None
        assert "already have a pending request" in error
    
    def test_get_request_by_id_success(self, mock_db):
        """Test successful retrieval of extension request by ID"""
        mock_requests_ref = Mock()
        mock_db.return_value = mock_requests_ref
        
        request_data = {
            "requestId": "req-123",
            "itemId": "task-123",
            "itemType": "task",
            "requesterId": "user-456",
            "ownerId": "user-789",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1700086400,
            "reason": "Need more time",
            "status": "pending",
            "createdAt": 1699000000
        }
        
        mock_requests_ref.child.return_value.get.return_value = request_data
        
        service = ExtensionRequestService()
        extension_request, error = service.get_request_by_id("req-123")
        
        assert error is None
        assert extension_request is not None
        assert extension_request.request_id == "req-123"
    
    def test_get_request_by_id_not_found(self, mock_db):
        """Test retrieval fails when request not found"""
        mock_requests_ref = Mock()
        mock_db.return_value = mock_requests_ref
        
        mock_requests_ref.child.return_value.get.return_value = None
        
        service = ExtensionRequestService()
        extension_request, error = service.get_request_by_id("nonexistent")
        
        assert extension_request is None
        assert error == "Extension request not found"
    
    def test_get_requests_by_owner(self, mock_db):
        """Test retrieval of all requests for an owner"""
        mock_requests_ref = Mock()
        mock_db.return_value = mock_requests_ref
        
        all_requests = {
            "req-123": {
                "requestId": "req-123",
                "itemId": "task-123",
                "itemType": "task",
                "requesterId": "user-456",
                "ownerId": "owner-user",
                "currentDeadline": 1700000000,
                "proposedDeadline": 1700086400,
                "reason": "Need more time",
                "status": "pending",
                "createdAt": 1699000000
            },
            "req-456": {
                "requestId": "req-456",
                "itemId": "task-456",
                "itemType": "task",
                "requesterId": "user-789",
                "ownerId": "owner-user",
                "currentDeadline": 1700000000,
                "proposedDeadline": 1700086400,
                "reason": "More testing needed",
                "status": "approved",
                "createdAt": 1698000000
            },
            "req-789": {
                "requestId": "req-789",
                "itemId": "task-789",
                "itemType": "task",
                "requesterId": "user-111",
                "ownerId": "other-owner",
                "currentDeadline": 1700000000,
                "proposedDeadline": 1700086400,
                "reason": "Delays",
                "status": "pending",
                "createdAt": 1697000000
            }
        }
        
        mock_requests_ref.get.return_value = all_requests
        
        service = ExtensionRequestService()
        requests = service.get_requests_by_owner("owner-user")
        
        assert len(requests) == 2
        assert all(r.owner_id == "owner-user" for r in requests)
    
    def test_get_requests_by_owner_filtered_by_status(self, mock_db):
        """Test retrieval of requests for an owner filtered by status"""
        mock_requests_ref = Mock()
        mock_db.return_value = mock_requests_ref
        
        all_requests = {
            "req-123": {
                "requestId": "req-123",
                "ownerId": "owner-user",
                "status": "pending",
                "createdAt": 1699000000,
                "itemId": "task-123",
                "itemType": "task",
                "requesterId": "user-456",
                "currentDeadline": 1700000000,
                "proposedDeadline": 1700086400,
                "reason": "Need time"
            },
            "req-456": {
                "requestId": "req-456",
                "ownerId": "owner-user",
                "status": "approved",
                "createdAt": 1698000000,
                "itemId": "task-456",
                "itemType": "task",
                "requesterId": "user-789",
                "currentDeadline": 1700000000,
                "proposedDeadline": 1700086400,
                "reason": "More time"
            }
        }
        
        mock_requests_ref.get.return_value = all_requests
        
        service = ExtensionRequestService()
        requests = service.get_requests_by_owner("owner-user", status="pending")
        
        assert len(requests) == 1
        assert requests[0].status == "pending"
    
    @patch('extension_request_service.current_timestamp')
    def test_respond_to_request_approve(self, mock_timestamp, mock_db, mock_requests):
        """Test approving an extension request"""
        mock_timestamp.return_value = 1699500000
        
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        
        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        request_data = {
            "requestId": "req-123",
            "itemId": "task-123",
            "itemType": "task",
            "requesterId": "user-456",
            "ownerId": "owner-user",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1700086400,
            "reason": "Need more time",
            "status": "pending",
            "createdAt": 1699000000
        }
        
        updated_request_data = {**request_data, "status": "approved", "respondedAt": 1699500000}
        
        mock_request_ref = Mock()
        mock_requests_ref.child.return_value = mock_request_ref
        mock_request_ref.get.side_effect = [request_data, updated_request_data]
        
        # Mock task data
        task_data = {
            "taskId": "task-123",
            "title": "Test Task",
            "collaborators": ["user-456", "user-789"]
        }
        mock_tasks_ref.child.return_value.get.return_value = task_data
        
        # Mock API calls
        mock_requests.put.return_value.status_code = 200
        mock_requests.post.return_value.status_code = 200
        
        service = ExtensionRequestService()
        
        req = UpdateExtensionRequestRequest(
            request_id="req-123",
            responder_id="owner-user",
            status="approved"
        )
        
        extension_request, error = service.respond_to_request(req)
        
        assert error is None
        assert extension_request.status == "approved"
        mock_request_ref.update.assert_called_once()
    
    def test_respond_to_request_reject_with_reason(self, mock_db, mock_requests):
        """Test rejecting an extension request with reason"""
        mock_requests_ref = Mock()
        mock_users_ref = Mock()
        mock_notification_prefs_ref = Mock()

        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "users": mock_users_ref,
            "notificationPreferences": mock_notification_prefs_ref
        }.get(path, Mock())

        request_data = {
            "requestId": "req-123",
            "itemId": "task-123",
            "itemType": "task",
            "requesterId": "user-456",
            "ownerId": "owner-user",
            "currentDeadline": 1700000000,
            "proposedDeadline": 1700086400,
            "reason": "Need more time",
            "status": "pending",
            "createdAt": 1699000000
        }

        updated_request_data = {
            **request_data,
            "status": "rejected",
            "rejectionReason": "Timeline is fixed",
            "respondedAt": 1699500000
        }

        mock_request_ref = Mock()
        mock_requests_ref.child.return_value = mock_request_ref
        mock_request_ref.get.side_effect = [request_data, updated_request_data]

        # Mock user data
        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com", "name": "Test User"}
        mock_notification_prefs_ref.child.return_value.get.return_value = {"channel": "both", "enabled": True}

        # Mock notification call
        mock_requests.post.return_value.status_code = 200

        service = ExtensionRequestService()

        req = UpdateExtensionRequestRequest(
            request_id="req-123",
            responder_id="owner-user",
            status="rejected",
            rejection_reason="Timeline is fixed"
        )

        extension_request, error = service.respond_to_request(req)

        assert error is None
        assert extension_request.status == "rejected"
        assert extension_request.rejection_reason == "Timeline is fixed"
    
    def test_respond_to_request_already_responded(self, mock_db):
        """Test responding fails when request already responded to"""
        mock_requests_ref = Mock()
        mock_db.return_value = mock_requests_ref
        
        request_data = {
            "requestId": "req-123",
            "status": "approved",  # Already approved
            "ownerId": "owner-user"
        }
        
        mock_requests_ref.child.return_value.get.return_value = request_data
        
        service = ExtensionRequestService()
        
        req = UpdateExtensionRequestRequest(
            request_id="req-123",
            responder_id="owner-user",
            status="rejected"
        )
        
        extension_request, error = service.respond_to_request(req)
        
        assert extension_request is None
        assert error == "Request has already been responded to"
    
    def test_respond_to_request_not_owner(self, mock_db):
        """Test responding fails when responder is not the owner"""
        mock_requests_ref = Mock()
        mock_db.return_value = mock_requests_ref
        
        request_data = {
            "requestId": "req-123",
            "status": "pending",
            "ownerId": "owner-user"
        }
        
        mock_requests_ref.child.return_value.get.return_value = request_data
        
        service = ExtensionRequestService()
        
        req = UpdateExtensionRequestRequest(
            request_id="req-123",
            responder_id="other-user",
            status="approved"
        )
        
        extension_request, error = service.respond_to_request(req)
        
        assert extension_request is None
        assert error == "Only the owner can respond to this request"


class TestExtensionRequestEndpoints:
    """Test API endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'extension-request-service'
    
    @patch('app.extension_request_service.create_extension_request')
    def test_create_extension_request_endpoint_success(self, mock_create, client):
        """Test POST /extension-requests endpoint success"""
        mock_request = ExtensionRequest(
            request_id="req-123",
            item_id="task-123",
            item_type="task",
            requester_id="user-456",
            owner_id="owner-789",
            current_deadline=1700000000,
            proposed_deadline=1700086400,
            reason="Need more time",
            status="pending",
            created_at=1699000000
        )
        
        mock_create.return_value = (mock_request, None)
        
        response = client.post('/extension-requests', json={
            "itemId": "task-123",
            "itemType": "task",
            "requesterId": "user-456",
            "proposedDeadline": 1700086400,
            "reason": "Need more time"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == "Extension request created successfully"
        assert data['request']['requestId'] == "req-123"
    
    @patch('app.extension_request_service.create_extension_request')
    def test_create_extension_request_endpoint_error(self, mock_create, client):
        """Test POST /extension-requests endpoint with error"""
        mock_create.return_value = (None, "Requester must be a collaborator")
        
        response = client.post('/extension-requests', json={
            "itemId": "task-123",
            "itemType": "task",
            "requesterId": "user-456",
            "proposedDeadline": 1700086400,
            "reason": "Need more time"
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == "Requester must be a collaborator"
    
    def test_create_extension_request_endpoint_missing_fields(self, client):
        """Test POST /extension-requests endpoint with missing fields"""
        response = client.post('/extension-requests', json={
            "itemId": "task-123"
            # Missing required fields
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Validation failed' in data['error']
    
    def test_create_extension_request_endpoint_no_body(self, client):
        """Test POST /extension-requests endpoint with no body"""
        response = client.post('/extension-requests', json={})
        
        assert response.status_code == 400
        assert response.is_json
        data = response.get_json()
        assert data['error'] == "Missing JSON body"
    
    @patch('app.extension_request_service.get_request_by_id')
    def test_get_extension_request_endpoint_success(self, mock_get, client):
        """Test GET /extension-requests/<id> endpoint success"""
        mock_request = ExtensionRequest(
            request_id="req-123",
            item_id="task-123",
            item_type="task",
            requester_id="user-456",
            owner_id="owner-789",
            current_deadline=1700000000,
            proposed_deadline=1700086400,
            reason="Need more time",
            status="pending",
            created_at=1699000000
        )

        mock_get.return_value = (mock_request, None)

        response = client.get('/extension-requests/req-123')

        assert response.status_code == 200
        data = response.get_json()
        assert data['requestId'] == "req-123"
    
    @patch('app.extension_request_service.get_request_by_id')
    def test_get_extension_request_endpoint_not_found(self, mock_get, client):
        """Test GET /extension-requests/<id> endpoint not found"""
        mock_get.return_value = (None, "Extension request not found")
        
        response = client.get('/extension-requests/nonexistent')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == "Extension request not found"
    
    @patch('app.extension_request_service.get_requests_by_owner')
    def test_get_requests_by_owner_endpoint(self, mock_get, client):
        """Test GET /extension-requests/owner/<id> endpoint"""
        mock_requests = [
            ExtensionRequest(
                request_id="req-123",
                item_id="task-123",
                item_type="task",
                requester_id="user-456",
                owner_id="owner-789",
                current_deadline=1700000000,
                proposed_deadline=1700086400,
                reason="Need more time",
                status="pending",
                created_at=1699000000
            )
        ]
        
        mock_get.return_value = mock_requests
        
        response = client.get('/extension-requests/owner/owner-789')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['requests']) == 1
        assert data['requests'][0]['ownerId'] == "owner-789"
    
    @patch('app.extension_request_service.get_requests_by_owner')
    def test_get_requests_by_owner_with_status_filter(self, mock_get, client):
        """Test GET /extension-requests/owner/<id> with status filter"""
        mock_get.return_value = []
        
        response = client.get('/extension-requests/owner/owner-789?status=pending')
        
        assert response.status_code == 200
        mock_get.assert_called_once_with("owner-789", "pending")
    
    @patch('app.extension_request_service.respond_to_request')
    def test_respond_to_request_endpoint_success(self, mock_respond, client):
        """Test PATCH /extension-requests/<id>/respond endpoint success"""
        mock_request = ExtensionRequest(
            request_id="req-123",
            item_id="task-123",
            item_type="task",
            requester_id="user-456",
            owner_id="owner-789",
            current_deadline=1700000000,
            proposed_deadline=1700086400,
            reason="Need more time",
            status="approved",
            created_at=1699000000,
            responded_at=1699500000
        )
        
        mock_respond.return_value = (mock_request, None)
        
        response = client.patch('/extension-requests/req-123/respond', json={
            "responderId": "owner-789",
            "status": "approved"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Extension request approved"
        assert data['request']['status'] == "approved"
    
    @patch('app.extension_request_service.respond_to_request')
    def test_respond_to_request_endpoint_rejection(self, mock_respond, client):
        """Test PATCH /extension-requests/<id>/respond endpoint rejection"""
        mock_request = ExtensionRequest(
            request_id="req-123",
            item_id="task-123",
            item_type="task",
            requester_id="user-456",
            owner_id="owner-789",
            current_deadline=1700000000,
            proposed_deadline=1700086400,
            reason="Need more time",
            status="rejected",
            created_at=1699000000,
            responded_at=1699500000,
            rejection_reason="Timeline is fixed"
        )
        
        mock_respond.return_value = (mock_request, None)
        
        response = client.patch('/extension-requests/req-123/respond', json={
            "responderId": "owner-789",
            "status": "rejected",
            "rejectionReason": "Timeline is fixed"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Extension request rejected"
        assert data['request']['status'] == "rejected"
    
    def test_respond_to_request_endpoint_invalid_status(self, client):
        """Test PATCH /extension-requests/<id>/respond with invalid status"""
        response = client.patch('/extension-requests/req-123/respond', json={
            "responderId": "owner-789",
            "status": "invalid"
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Validation failed' in data['error']


class TestExtensionRequestIntegration:
    """Integration tests for complete workflows"""
    
    @patch('extension_request_service.current_timestamp')
    @patch('extension_request_service.requests')
    def test_complete_approval_workflow(self, mock_requests_lib, mock_timestamp, mock_db, sample_task_data):
        """Test complete workflow from request creation to approval"""
        mock_timestamp.return_value = 1699000000
        
        # Mock database
        mock_requests_ref = Mock()
        mock_tasks_ref = Mock()
        
        mock_db.side_effect = lambda path: {
            "deadlineExtensionRequests": mock_requests_ref,
            "tasks": mock_tasks_ref
        }.get(path, Mock())
        
        # Mock task data
        mock_tasks_ref.child.return_value.get.return_value = sample_task_data
        mock_requests_ref.get.return_value = {}
        
        # Mock HTTP calls
        mock_requests_lib.post.return_value.status_code = 200
        mock_requests_lib.put.return_value.status_code = 200
        
        service = ExtensionRequestService()
        
        # Step 1: Create extension request
        create_req = CreateExtensionRequestRequest(
            item_id="task-123",
            item_type="task",
            requester_id="collab-user-456",
            proposed_deadline=sample_task_data["deadline"] + 86400 * 3,
            reason="Need 3 more days for thorough testing"
        )
        
        extension_request, error = service.create_extension_request(create_req)
        assert error is None
        assert extension_request.status == "pending"
        
        # Step 2: Approve the request
        request_id = extension_request.request_id
        
        # Mock getting the pending request
        pending_request_data = extension_request.to_dict()
        approved_request_data = {**pending_request_data, "status": "approved", "respondedAt": 1699500000}
        
        mock_request_ref = Mock()
        mock_requests_ref.child.return_value = mock_request_ref
        mock_request_ref.get.side_effect = [pending_request_data, approved_request_data]
        
        update_req = UpdateExtensionRequestRequest(
            request_id=request_id,
            responder_id=sample_task_data["ownerId"],
            status="approved"
        )
        
        approved_request, error = service.respond_to_request(update_req)
        assert error is None
        assert approved_request.status == "approved"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])