# backend/subtask-service/test_subtask.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

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

from subtask_service import SubtaskService
from models import Subtask, CreateSubtaskRequest, UpdateSubtaskRequest


@pytest.fixture(autouse=True)
def mock_firebase():
    """Mock Firebase for all tests"""
    with patch('firebase_admin.initialize_app', return_value=mock_firebase_app):
        with patch('firebase_admin.get_app', return_value=mock_firebase_app):
            with patch('firebase_admin.credentials.Certificate'):
                yield


@pytest.fixture
def mock_db():
    """Mock database references"""
    with patch('subtask_service.get_db_reference') as mock:
        yield mock


@pytest.fixture
def sample_subtask():
    """Create sample subtask"""
    return Subtask(
        subtask_id="st1",
        title="Test Subtask",
        creator_id="u1",
        deadline=1700000000,
        status="ongoing",
        notes="",
        attachments=[],
        collaborators=[],
        task_id="t1",
        owner_id="u1",
        priority=0,
        created_at=1600000000,
        updated_at=1600000000,
        start_date=1600000000,
        active=True,
        scheduled=False,
        schedule="daily",
        custom_schedule=None,
        completed_at=None,
        started_at=None
    )


class TestSubtaskServiceStartedAt:
    """Test startedAt logic for subtasks"""
    
    def test_create_subtask_owner_is_creator_unassigned(self, mock_db):
        """Test creating subtask where owner is creator - status should be 'unassigned', startedAt should be None"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = CreateSubtaskRequest(
                title="Test Subtask",
                creator_id="u1",
                deadline=1800000000,
                task_id="t1",
                owner_id="u1"  # Same as creator
            )
            
            subtask, error = service.create_subtask(req)
            
            assert error is None
            assert subtask.status == "unassigned"
            assert subtask.started_at is None
            
            # Verify the data sent to Firebase
            call_args = mock_new_ref.set.call_args[0][0]
            assert call_args["status"] == "unassigned"
            assert call_args["startedAt"] is None
    
    def test_create_subtask_owner_is_creator_default(self, mock_db):
        """Test creating subtask with default owner (creator) - status should be 'unassigned', startedAt should be None"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = CreateSubtaskRequest(
                title="Test Subtask",
                creator_id="u1",
                deadline=1800000000,
                task_id="t1"
                # No owner_id specified, should default to creator
            )
            
            subtask, error = service.create_subtask(req)
            
            assert error is None
            assert subtask.status == "unassigned"
            assert subtask.started_at is None
            assert subtask.owner_id == "u1"
    
    def test_create_subtask_owner_is_different_user(self, mock_db):
        """Test creating subtask where owner is different from creator - status should be 'ongoing', startedAt should be set"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = CreateSubtaskRequest(
                title="Test Subtask",
                creator_id="u1",
                deadline=1800000000,
                task_id="t1",
                owner_id="u2"  # Different from creator
            )
            
            subtask, error = service.create_subtask(req)
            
            assert error is None
            assert subtask.status == "ongoing"
            assert subtask.started_at == current_time
            
            # Verify the data sent to Firebase
            call_args = mock_new_ref.set.call_args[0][0]
            assert call_args["status"] == "ongoing"
            assert call_args["startedAt"] == current_time
    
    def test_update_subtask_status_unassigned_to_ongoing(self, mock_db):
        """Test updating subtask status from 'unassigned' to 'ongoing' - startedAt should be set"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        existing_data = {
            "subTaskId": "st1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "unassigned",
            "taskId": "t1",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": None
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "ongoing"
        updated_data["startedAt"] = 1700000000
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = UpdateSubtaskRequest(
                subtask_id="st1",
                status="ongoing"
            )
            
            subtask, error = service.update_subtask(req)
            
            assert error is None
            assert subtask.status == "ongoing"
            assert subtask.started_at == current_time
            
            # Verify update was called with startedAt
            update_call_args = mock_subtask_ref.update.call_args[0][0]
            assert update_call_args["status"] == "ongoing"
            assert update_call_args["startedAt"] == current_time
    
    def test_update_subtask_status_ongoing_to_under_review_no_started_at_change(self, mock_db):
        """Test updating status from 'ongoing' to 'under_review' - startedAt should NOT change"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        original_started_at = 1600000000
        existing_data = {
            "subTaskId": "st1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "ongoing",
            "taskId": "t1",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": original_started_at
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "under_review"
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = UpdateSubtaskRequest(
                subtask_id="st1",
                status="under_review"
            )
            
            subtask, error = service.update_subtask(req)
            
            assert error is None
            # startedAt should remain the original value
            assert subtask.started_at == original_started_at
            
            # Verify update was called without startedAt
            update_call_args = mock_subtask_ref.update.call_args[0][0]
            assert "startedAt" not in update_call_args
    
    def test_update_subtask_owner_unassigned_to_different_user(self, mock_db):
        """Test changing owner from creator to different user when status is 'unassigned' - should set to 'ongoing' and set startedAt"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        existing_data = {
            "subTaskId": "st1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "unassigned",
            "taskId": "t1",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": None
        }
        
        updated_data = existing_data.copy()
        updated_data["ownerId"] = "u2"
        updated_data["status"] = "ongoing"
        updated_data["startedAt"] = 1700000000
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = UpdateSubtaskRequest(
                subtask_id="st1",
                owner_id="u2"  # Changing to different user
            )
            
            subtask, error = service.update_subtask(req)
            
            assert error is None
            assert subtask.owner_id == "u2"
            assert subtask.status == "ongoing"
            assert subtask.started_at == current_time
            
            # Verify update was called with both status and startedAt
            update_call_args = mock_subtask_ref.update.call_args[0][0]
            assert update_call_args["ownerId"] == "u2"
            assert update_call_args["status"] == "ongoing"
            assert update_call_args["startedAt"] == current_time
    
    def test_update_subtask_owner_ongoing_no_status_change(self, mock_db):
        """Test changing owner when status is already 'ongoing' - status should NOT change again"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        original_started_at = 1600000000
        existing_data = {
            "subTaskId": "st1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u2",
            "status": "ongoing",
            "taskId": "t1",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": original_started_at
        }
        
        updated_data = existing_data.copy()
        updated_data["ownerId"] = "u3"
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = UpdateSubtaskRequest(
                subtask_id="st1",
                owner_id="u3"
            )
            
            subtask, error = service.update_subtask(req)
            
            assert error is None
            # Status should remain ongoing, startedAt should not change
            assert subtask.started_at == original_started_at
            
            # Verify status was NOT added to update
            update_call_args = mock_subtask_ref.update.call_args[0][0]
            assert "status" not in update_call_args


class TestSubtaskServiceCompletedAt:
    """Test completedAt logic for subtasks"""
    
    def test_update_subtask_status_to_completed(self, mock_db):
        """Test updating subtask status to 'completed' - completedAt should be set"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        existing_data = {
            "subTaskId": "st1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "ongoing",
            "taskId": "t1",
            "deadline": 1800000000,
            "scheduled": False,
            "completedAt": None
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "completed"
        updated_data["completedAt"] = 1700000000
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = UpdateSubtaskRequest(
                subtask_id="st1",
                status="completed"
            )
            
            subtask, error = service.update_subtask(req)
            
            assert error is None
            assert subtask.status == "completed"
            assert subtask.completed_at == current_time
            
            # Verify update was called with completedAt
            update_call_args = mock_subtask_ref.update.call_args[0][0]
            assert update_call_args["status"] == "completed"
            assert update_call_args["completedAt"] == current_time
    
    def test_update_subtask_status_from_completed_to_ongoing_no_completed_at_change(self, mock_db):
        """Test changing status from 'completed' back to 'ongoing' - completedAt should NOT be modified"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        original_completed_at = 1600000000
        existing_data = {
            "subTaskId": "st1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "completed",
            "taskId": "t1",
            "deadline": 1800000000,
            "scheduled": False,
            "completedAt": original_completed_at
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "ongoing"
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = UpdateSubtaskRequest(
                subtask_id="st1",
                status="ongoing"
            )
            
            subtask, error = service.update_subtask(req)
            
            assert error is None
            # completedAt should remain the original value
            assert subtask.completed_at == original_completed_at
            
            # Verify completedAt was NOT updated
            update_call_args = mock_subtask_ref.update.call_args[0][0]
            assert "completedAt" not in update_call_args
    
    def test_create_subtask_completed_at_is_none(self, mock_db):
        """Test creating subtask - completedAt should be None initially"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = CreateSubtaskRequest(
                title="Test Subtask",
                creator_id="u1",
                deadline=1800000000,
                task_id="t1"
            )
            
            subtask, error = service.create_subtask(req)
            
            assert error is None
            assert subtask.completed_at is None
            
            # Verify the data sent to Firebase
            call_args = mock_new_ref.set.call_args[0][0]
            assert call_args["completedAt"] is None


class TestSubtaskServiceCombinedScenarios:
    """Test combined scenarios for startedAt and completedAt for subtasks"""
    
    def test_full_lifecycle_unassigned_to_completed(self, mock_db):
        """Test full subtask lifecycle: unassigned -> ongoing -> completed"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Scenario 1: Create subtask (unassigned)
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        current_time_1 = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time_1):
            service = SubtaskService()
            req = CreateSubtaskRequest(
                title="Test Subtask",
                creator_id="u1",
                deadline=1800000000,
                task_id="t1"
            )
            
            subtask, _ = service.create_subtask(req)
            assert subtask.status == "unassigned"
            assert subtask.started_at is None
            assert subtask.completed_at is None
        
        # Scenario 2: Update to ongoing
        mock_subtask_ref = Mock()
        existing_data = {
            "subTaskId": "test-subtask-id",
            "title": "Test Subtask",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "unassigned",
            "taskId": "t1",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": None,
            "completedAt": None
        }
        
        current_time_2 = 1700010000
        updated_data_2 = existing_data.copy()
        updated_data_2["status"] = "ongoing"
        updated_data_2["startedAt"] = current_time_2
        updated_data_2["updatedAt"] = current_time_2
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data_2]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        with patch('subtask_service.current_timestamp', return_value=current_time_2):
            req2 = UpdateSubtaskRequest(
                subtask_id="test-subtask-id",
                status="ongoing"
            )
            subtask, _ = service.update_subtask(req2)
            assert subtask.status == "ongoing"
            assert subtask.started_at == current_time_2
            assert subtask.completed_at is None
        
        # Scenario 3: Update to completed
        existing_data_3 = updated_data_2.copy()
        current_time_3 = 1700020000
        updated_data_3 = existing_data_3.copy()
        updated_data_3["status"] = "completed"
        updated_data_3["completedAt"] = current_time_3
        updated_data_3["updatedAt"] = current_time_3
        
        mock_subtask_ref.get.side_effect = [existing_data_3, updated_data_3]
        
        with patch('subtask_service.current_timestamp', return_value=current_time_3):
            req3 = UpdateSubtaskRequest(
                subtask_id="test-subtask-id",
                status="completed"
            )
            subtask, _ = service.update_subtask(req3)
            assert subtask.status == "completed"
            assert subtask.started_at == current_time_2  # Should remain unchanged
            assert subtask.completed_at == current_time_3
    
    def test_manager_assigns_subtask_to_staff(self, mock_db):
        """Test manager creating subtask and assigning to staff - should be ongoing with startedAt"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            req = CreateSubtaskRequest(
                title="Test Subtask",
                creator_id="manager1",  # Manager creates
                deadline=1800000000,
                task_id="t1",
                owner_id="staff1"  # Assigns to staff
            )
            
            subtask, error = service.create_subtask(req)
            
            assert error is None
            assert subtask.status == "ongoing"
            assert subtask.started_at == current_time
            assert subtask.completed_at is None
            assert subtask.owner_id == "staff1"


class TestSubtaskEndpoints:
    """Test Flask endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @patch('app.subtask_service.create_subtask')
    def test_create_subtask_endpoint(self, mock_create, client, sample_subtask):
        """Test POST /subtasks"""
        mock_create.return_value = (sample_subtask, None)

        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "taskId": "t1",
            "creatorId": "u1",
            "deadline": 1700000000
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['subtask']['title'] == "Test Subtask"

    @patch('app.subtask_service.create_subtask')
    def test_create_subtask_invalid_data(self, mock_create, client):
        """Test POST /subtasks with invalid data"""
        mock_create.return_value = (None, "Validation failed")

        response = client.post('/subtasks', json={
            "title": "",
            "taskId": "t1"
        })

        assert response.status_code == 400

    def test_create_subtask_missing_body(self, client):
        """Test POST /subtasks with missing body"""
        response = client.post('/subtasks')
        assert response.status_code in [400, 415]

    @patch('app.subtask_service.get_all_subtasks')
    def test_get_all_subtasks_endpoint(self, mock_get, client, sample_subtask):
        """Test GET /subtasks"""
        mock_get.return_value = [sample_subtask]

        response = client.get('/subtasks')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['subtasks']) == 1

    @patch('app.subtask_service.get_subtask_by_id')
    def test_get_subtask_by_id_endpoint(self, mock_get, client, sample_subtask):
        """Test GET /subtasks/<id>"""
        mock_get.return_value = (sample_subtask, None)

        response = client.get('/subtasks/s1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['subtask']['subTaskId'] == "st1"

    @patch('app.subtask_service.get_subtask_by_id')
    def test_get_subtask_by_id_not_found(self, mock_get, client):
        """Test GET /subtasks/<id> not found"""
        mock_get.return_value = (None, "Subtask not found")

        response = client.get('/subtasks/invalid')
        assert response.status_code == 404

    @patch('app.subtask_service.update_subtask')
    @patch('app.subtask_service.get_subtask_by_id')
    def test_update_subtask_endpoint(self, mock_get, mock_update, client, sample_subtask):
        """Test PUT /subtasks/<id>"""
        from models import Subtask
        updated_subtask = Subtask(**{**sample_subtask.__dict__, 'title': 'Updated Subtask'})
        mock_get.return_value = (sample_subtask, None)
        mock_update.return_value = (updated_subtask, None)

        response = client.put('/subtasks/s1', json={
            "title": "Updated Subtask"
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['subtask']['title'] == "Updated Subtask"

    @patch('app.subtask_service.update_subtask')
    def test_update_subtask_not_found(self, mock_update, client):
        """Test PUT /subtasks/<id> not found"""
        mock_update.return_value = (None, "Subtask not found")

        response = client.put('/subtasks/invalid', json={
            "title": "Updated"
        }, headers={'Content-Type': 'application/json'})

        assert response.status_code == 404

    def test_update_subtask_missing_body(self, client):
        """Test PUT /subtasks/<id> with missing body"""
        response = client.put('/subtasks/s1')
        assert response.status_code in [400, 415]

    @patch('app.subtask_service.delete_subtask')
    def test_delete_subtask_endpoint(self, mock_delete, client):
        """Test DELETE /subtasks/<id>"""
        mock_delete.return_value = (True, None)

        response = client.delete('/subtasks/s1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Subtask deleted successfully"

    @patch('app.subtask_service.delete_subtask')
    def test_delete_subtask_not_found(self, mock_delete, client):
        """Test DELETE /subtasks/<id> not found"""
        mock_delete.return_value = (False, "Subtask not found")

        response = client.delete('/subtasks/invalid')
        assert response.status_code == 404

    @patch('app.subtask_service.get_subtasks_by_task')
    def test_get_subtasks_by_task_endpoint(self, mock_get, client, sample_subtask):
        """Test GET /subtasks/task/<id>"""
        mock_get.return_value = [sample_subtask]

        response = client.get('/subtasks/task/t1')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['subtasks']) == 1
        assert data['subtasks'][0]['taskId'] == "t1"

    def test_health_check_endpoint(self, client):
        """Test GET /health"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'subtask-service'

    def test_create_subtask_invalid_deadline(self, client):
        """Test POST /subtasks with invalid deadline"""
        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "taskId": "t1",
            "creatorId": "u1",
            "deadline": "invalid"
        })
        assert response.status_code == 400

    @patch('app.subtask_service.update_subtask')
    @patch('app.subtask_service.get_subtask_by_id')
    def test_update_subtask_invalid_data(self, mock_get, mock_update, client, sample_subtask):
        """Test PUT /subtasks/<id> with invalid data"""
        mock_get.return_value = (sample_subtask, None)
        mock_update.return_value = (None, "Invalid data")

        response = client.put('/subtasks/s1', json={
            "status": "invalid_status"
        })

        assert response.status_code == 400

    def test_create_subtask_invalid_status(self, client):
        """Test POST /subtasks with invalid status"""
        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "taskId": "t1",
            "creatorId": "u1",
            "deadline": 1700000000,
            "status": "invalid_status"
        })
        assert response.status_code == 400

    def test_create_subtask_invalid_schedule(self, client):
        """Test POST /subtasks with invalid schedule"""
        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "taskId": "t1",
            "creatorId": "u1",
            "deadline": 1700000000,
            "schedule": "invalid"
        })
        assert response.status_code == 400

    def test_create_subtask_with_negative_start_date(self, client):
        """Test POST /subtasks with negative start_date"""
        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "taskId": "t1",
            "creatorId": "u1",
            "deadline": 1700000000,
            "start_date": -1
        })
        assert response.status_code == 400

    @patch('app.subtask_service.create_subtask')
    def test_create_subtask_service_error(self, mock_create, client):
        """Test POST /subtasks when service returns error"""
        mock_create.return_value = (None, "Task not found")

        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "taskId": "invalid_task",
            "creatorId": "u1",
            "deadline": 1700000000
        })
        assert response.status_code == 404

    @patch('app.subtask_service.create_subtask')
    def test_create_subtask_service_error_400(self, mock_create, client):
        """Test POST /subtasks with non-404 error"""
        mock_create.return_value = (None, "Invalid data")

        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "taskId": "t1",
            "creatorId": "u1",
            "deadline": 1700000000
        })
        assert response.status_code == 400

    def test_update_subtask_invalid_deadline(self, client):
        """Test PUT /subtasks/<id> with invalid deadline"""
        response = client.put('/subtasks/s1', json={
            "deadline": "invalid"
        })
        assert response.status_code == 400

    def test_update_subtask_invalid_start_date(self, client):
        """Test PUT /subtasks/<id> with invalid start_date"""
        response = client.put('/subtasks/s1', json={
            "startDate": -1
        })
        assert response.status_code == 400

    def test_update_subtask_invalid_status(self, client):
        """Test PUT /subtasks/<id> with invalid status"""
        response = client.put('/subtasks/s1', json={
            "status": "invalid"
        })
        assert response.status_code == 400

    def test_update_subtask_invalid_schedule(self, client):
        """Test PUT /subtasks/<id> with invalid schedule"""
        response = client.put('/subtasks/s1', json={
            "schedule": "invalid"
        })
        assert response.status_code == 400

    @patch('app.subtask_service.update_subtask')
    def test_update_subtask_service_error_404(self, mock_update, client):
        """Test PUT /subtasks/<id> with not found error"""
        mock_update.return_value = (None, "Subtask not found")

        response = client.put('/subtasks/s1', json={
            "title": "Updated"
        })
        assert response.status_code == 404

    @patch('app.subtask_service.update_subtask')
    def test_update_subtask_service_error_400(self, mock_update, client):
        """Test PUT /subtasks/<id> with validation error"""
        mock_update.return_value = (None, "Invalid update")

        response = client.put('/subtasks/s1', json={
            "title": "Updated"
        })
        assert response.status_code == 400

    def test_create_subtask_with_null_body(self, client):
        """Test POST /subtasks with null JSON body"""
        response = client.post('/subtasks',
                              data='null',
                              content_type='application/json')
        assert response.status_code == 400

    def test_update_subtask_with_null_body(self, client):
        """Test PUT /subtasks/<id> with null JSON body"""
        response = client.put('/subtasks/s1',
                             data='null',
                             content_type='application/json')
        assert response.status_code == 400


class TestSubtaskServiceAdditionalMethods:
    """Test additional SubtaskService methods for better coverage"""

    @patch('subtask_service.current_timestamp')
    def test_calculate_new_start_date_daily(self, mock_timestamp, mock_db):
        """Test calculate_new_start_date for daily schedule"""
        from datetime import datetime, timezone, timedelta
        # Set current time to be in the future so the calculated date won't be adjusted
        old_date = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = int(old_date.timestamp())

        service = SubtaskService()
        old_ts = int(old_date.timestamp())
        new_ts = service.calculate_new_start_date(old_ts, "daily")

        # Should be 1 day later
        new_date = datetime.fromtimestamp(new_ts, tz=timezone.utc)
        expected_date = old_date + timedelta(days=1)
        assert new_date.date() == expected_date.date()

    @patch('subtask_service.current_timestamp')
    def test_calculate_new_start_date_weekly(self, mock_timestamp, mock_db):
        """Test calculate_new_start_date for weekly schedule"""
        from datetime import datetime, timezone, timedelta
        old_date = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = int(old_date.timestamp())

        service = SubtaskService()
        old_ts = int(old_date.timestamp())
        new_ts = service.calculate_new_start_date(old_ts, "weekly")

        # Should be 7 days later
        new_date = datetime.fromtimestamp(new_ts, tz=timezone.utc)
        expected_date = old_date + timedelta(weeks=1)
        assert new_date.date() == expected_date.date()

    @patch('subtask_service.current_timestamp')
    def test_calculate_new_start_date_monthly(self, mock_timestamp, mock_db):
        """Test calculate_new_start_date for monthly schedule"""
        from datetime import datetime, timezone
        old_date = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = int(old_date.timestamp())

        service = SubtaskService()
        old_ts = int(old_date.timestamp())
        new_ts = service.calculate_new_start_date(old_ts, "monthly")

        # Should be 1 month later
        new_date = datetime.fromtimestamp(new_ts, tz=timezone.utc)
        # Month should be incremented
        assert new_date.month == 12 or (new_date.month == 1 and new_date.year == 2024)

    @patch('subtask_service.requests.post')
    def test_send_subtask_update_notification_success(self, mock_post, mock_db):
        """Test send_subtask_update_notification successfully sends"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()
        mock_tasks_ref = Mock()

        # Setup user data
        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = {
            "taskUpdateReminders": True,
            "channel": "both"
        }
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 200

        service = SubtaskService()
        service.send_subtask_update_notification("s1", "Test Subtask", "to_do", "in_progress", "u1", ["u2"], "t1")

        # Should have made notification API call
        assert mock_post.called

    @patch('subtask_service.requests.post')
    def test_send_subtask_update_notification_disabled_preference(self, mock_post, mock_db):
        """Test send_subtask_update_notification with disabled user preference"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()
        mock_tasks_ref = Mock()

        # Setup user data with notifications disabled
        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = {
            "taskUpdateReminders": False
        }
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return Mock()

        mock_db.side_effect = db_side_effect

        service = SubtaskService()
        service.send_subtask_update_notification("s1", "Test Subtask", "to_do", "in_progress", "u1", ["u2"], "t1")

        # Should not make API call since preference is disabled
        mock_post.assert_not_called()

    @patch('subtask_service.requests.post')
    def test_send_subtask_update_notification_no_preferences(self, mock_post, mock_db):
        """Test send_subtask_update_notification with no user preferences set"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()
        mock_tasks_ref = Mock()

        # Setup user data but no preferences
        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = None
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 200

        service = SubtaskService()
        service.send_subtask_update_notification("s1", "Test Subtask", "to_do", "in_progress", "u1", ["u2"], "t1")

        # Should use default settings and send notification
        assert mock_post.called

    @patch('subtask_service.requests.post')
    def test_send_subtask_update_notification_api_failure(self, mock_post, mock_db):
        """Test send_subtask_update_notification handles API failure"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()
        mock_tasks_ref = Mock()

        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = None
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Server error"

        service = SubtaskService()
        # Should not raise exception
        service.send_subtask_update_notification("s1", "Test Subtask", "to_do", "in_progress", "u1", ["u2"], "t1")

    @patch('subtask_service.requests.post')
    def test_send_subtask_update_notification_exception(self, mock_post, mock_db):
        """Test send_subtask_update_notification handles exceptions"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()
        mock_tasks_ref = Mock()

        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = None
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.side_effect = Exception("Network error")

        service = SubtaskService()
        # Should not raise exception, should handle gracefully
        service.send_subtask_update_notification("s1", "Test Subtask", "to_do", "in_progress", "u1", ["u2"], "t1")

    @patch('subtask_service.requests.post')
    def test_send_subtask_update_notification_preference_fetch_error(self, mock_post, mock_db):
        """Test send_subtask_update_notification when preference fetch fails"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()
        mock_tasks_ref = Mock()

        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        # Simulate exception when fetching preferences
        mock_prefs_ref.child.return_value.get.side_effect = Exception("DB error")
        mock_tasks_ref.child.return_value.get.return_value = {"title": "Parent Task"}

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            elif arg == "tasks":
                return mock_tasks_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 200

        service = SubtaskService()
        # Should fallback to default and still send
        service.send_subtask_update_notification("s1", "Test Subtask", "to_do", "in_progress", "u1", ["u2"], "t1")

        assert mock_post.called

    def test_validate_status_valid(self, mock_db):
        """Test validate_status with valid statuses"""
        service = SubtaskService()
        assert service.validate_status("ongoing") == True
        assert service.validate_status("unassigned") == True
        assert service.validate_status("under_review") == True
        assert service.validate_status("completed") == True

    def test_validate_status_invalid(self, mock_db):
        """Test validate_status with invalid status"""
        service = SubtaskService()
        assert service.validate_status("invalid") == False
        assert service.validate_status("") == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])