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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])