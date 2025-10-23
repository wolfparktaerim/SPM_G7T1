# backend/task-service/test_task.py
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

from task_service import TaskService
from models import Task, CreateTaskRequest, UpdateTaskRequest


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
    with patch('task_service.get_db_reference') as mock:
        yield mock


@pytest.fixture
def sample_task():
    """Create sample task"""
    return Task(
        task_id="t1",
        title="Test Task",
        creator_id="u1",
        deadline=1700000000,
        status="ongoing",
        notes="Test",
        attachments=[],
        collaborators=["u1"],
        project_id="p1",
        owner_id="u1",
        priority=1,
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


class TestTaskServiceStartedAt:
    """Test startedAt logic"""
    
    def test_create_task_owner_is_creator_unassigned(self, mock_db):
        """Test creating task where owner is creator - status should be 'unassigned', startedAt should be None"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = CreateTaskRequest(
                title="Test Task",
                creator_id="u1",
                deadline=1800000000,
                owner_id="u1"  # Same as creator
            )
            
            task, error = service.create_task(req)
            
            assert error is None
            assert task.status == "unassigned"
            assert task.started_at is None
            
            # Verify the data sent to Firebase
            call_args = mock_new_ref.set.call_args[0][0]
            assert call_args["status"] == "unassigned"
            assert call_args["startedAt"] is None
    
    def test_create_task_owner_is_creator_default(self, mock_db):
        """Test creating task with default owner (creator) - status should be 'unassigned', startedAt should be None"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = CreateTaskRequest(
                title="Test Task",
                creator_id="u1",
                deadline=1800000000
                # No owner_id specified, should default to creator
            )
            
            task, error = service.create_task(req)
            
            assert error is None
            assert task.status == "unassigned"
            assert task.started_at is None
            assert task.owner_id == "u1"
    
    def test_create_task_owner_is_different_user(self, mock_db):
        """Test creating task where owner is different from creator - status should be 'ongoing', startedAt should be set"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = CreateTaskRequest(
                title="Test Task",
                creator_id="u1",
                deadline=1800000000,
                owner_id="u2"  # Different from creator
            )
            
            task, error = service.create_task(req)
            
            assert error is None
            assert task.status == "ongoing"
            assert task.started_at == current_time
            
            # Verify the data sent to Firebase
            call_args = mock_new_ref.set.call_args[0][0]
            assert call_args["status"] == "ongoing"
            assert call_args["startedAt"] == current_time
    
    def test_update_task_status_unassigned_to_ongoing(self, mock_db):
        """Test updating task status from 'unassigned' to 'ongoing' - startedAt should be set"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        existing_data = {
            "taskId": "t1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "unassigned",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": None
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "ongoing"
        updated_data["startedAt"] = 1700000000
        updated_data["updatedAt"] = 1700000000
        
        mock_task_ref.get.side_effect = [existing_data, updated_data]
        mock_tasks.child.return_value = mock_task_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = UpdateTaskRequest(
                task_id="t1",
                status="ongoing"
            )
            
            task, error = service.update_task(req)
            
            assert error is None
            assert task.status == "ongoing"
            assert task.started_at == current_time
            
            # Verify update was called with startedAt
            update_call_args = mock_task_ref.update.call_args[0][0]
            assert update_call_args["status"] == "ongoing"
            assert update_call_args["startedAt"] == current_time
    
    def test_update_task_status_ongoing_to_under_review_no_started_at_change(self, mock_db):
        """Test updating status from 'ongoing' to 'under_review' - startedAt should NOT change"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        original_started_at = 1600000000
        existing_data = {
            "taskId": "t1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "ongoing",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": original_started_at
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "under_review"
        updated_data["updatedAt"] = 1700000000
        
        mock_task_ref.get.side_effect = [existing_data, updated_data]
        mock_tasks.child.return_value = mock_task_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = UpdateTaskRequest(
                task_id="t1",
                status="under_review"
            )
            
            task, error = service.update_task(req)
            
            assert error is None
            # startedAt should remain the original value
            assert task.started_at == original_started_at
            
            # Verify update was called without startedAt
            update_call_args = mock_task_ref.update.call_args[0][0]
            assert "startedAt" not in update_call_args
    
    def test_update_task_owner_unassigned_to_different_user(self, mock_db):
        """Test changing owner from creator to different user when status is 'unassigned' - should set to 'ongoing' and set startedAt"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        existing_data = {
            "taskId": "t1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "unassigned",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": None
        }
        
        updated_data = existing_data.copy()
        updated_data["ownerId"] = "u2"
        updated_data["status"] = "ongoing"
        updated_data["startedAt"] = 1700000000
        updated_data["updatedAt"] = 1700000000
        
        mock_task_ref.get.side_effect = [existing_data, updated_data]
        mock_tasks.child.return_value = mock_task_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = UpdateTaskRequest(
                task_id="t1",
                owner_id="u2"  # Changing to different user
            )
            
            task, error = service.update_task(req)
            
            assert error is None
            assert task.owner_id == "u2"
            assert task.status == "ongoing"
            assert task.started_at == current_time
            
            # Verify update was called with both status and startedAt
            update_call_args = mock_task_ref.update.call_args[0][0]
            assert update_call_args["ownerId"] == "u2"
            assert update_call_args["status"] == "ongoing"
            assert update_call_args["startedAt"] == current_time
    
    def test_update_task_owner_ongoing_no_status_change(self, mock_db):
        """Test changing owner when status is already 'ongoing' - status should NOT change again"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        original_started_at = 1600000000
        existing_data = {
            "taskId": "t1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u2",
            "status": "ongoing",
            "deadline": 1800000000,
            "scheduled": False,
            "startedAt": original_started_at
        }
        
        updated_data = existing_data.copy()
        updated_data["ownerId"] = "u3"
        updated_data["updatedAt"] = 1700000000
        
        mock_task_ref.get.side_effect = [existing_data, updated_data]
        mock_tasks.child.return_value = mock_task_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = UpdateTaskRequest(
                task_id="t1",
                owner_id="u3"
            )
            
            task, error = service.update_task(req)
            
            assert error is None
            # Status should remain ongoing, startedAt should not change
            assert task.started_at == original_started_at
            
            # Verify status was NOT added to update
            update_call_args = mock_task_ref.update.call_args[0][0]
            assert "status" not in update_call_args


class TestTaskServiceCompletedAt:
    """Test completedAt logic"""
    
    def test_update_task_status_to_completed(self, mock_db):
        """Test updating task status to 'completed' - completedAt should be set"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        existing_data = {
            "taskId": "t1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "ongoing",
            "deadline": 1800000000,
            "scheduled": False,
            "completedAt": None
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "completed"
        updated_data["completedAt"] = 1700000000
        updated_data["updatedAt"] = 1700000000
        
        mock_task_ref.get.side_effect = [existing_data, updated_data]
        mock_tasks.child.return_value = mock_task_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = UpdateTaskRequest(
                task_id="t1",
                status="completed"
            )
            
            task, error = service.update_task(req)
            
            assert error is None
            assert task.status == "completed"
            assert task.completed_at == current_time
            
            # Verify update was called with completedAt
            update_call_args = mock_task_ref.update.call_args[0][0]
            assert update_call_args["status"] == "completed"
            assert update_call_args["completedAt"] == current_time
    
    def test_update_task_status_from_completed_to_ongoing_no_completed_at_change(self, mock_db):
        """Test changing status from 'completed' back to 'ongoing' - completedAt should NOT be modified"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        original_completed_at = 1600000000
        existing_data = {
            "taskId": "t1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "completed",
            "deadline": 1800000000,
            "scheduled": False,
            "completedAt": original_completed_at
        }
        
        updated_data = existing_data.copy()
        updated_data["status"] = "ongoing"
        updated_data["updatedAt"] = 1700000000
        
        mock_task_ref.get.side_effect = [existing_data, updated_data]
        mock_tasks.child.return_value = mock_task_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = UpdateTaskRequest(
                task_id="t1",
                status="ongoing"
            )
            
            task, error = service.update_task(req)
            
            assert error is None
            # completedAt should remain the original value
            assert task.completed_at == original_completed_at
            
            # Verify completedAt was NOT updated
            update_call_args = mock_task_ref.update.call_args[0][0]
            assert "completedAt" not in update_call_args
    
    def test_create_task_completed_at_is_none(self, mock_db):
        """Test creating task - completedAt should be None initially"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref
        
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = CreateTaskRequest(
                title="Test Task",
                creator_id="u1",
                deadline=1800000000
            )
            
            task, error = service.create_task(req)
            
            assert error is None
            assert task.completed_at is None
            
            # Verify the data sent to Firebase
            call_args = mock_new_ref.set.call_args[0][0]
            assert call_args["completedAt"] is None


class TestTaskServiceCombinedScenarios:
    """Test combined scenarios for startedAt and completedAt"""
    
    def test_full_lifecycle_unassigned_to_completed(self, mock_db):
        """Test full task lifecycle: unassigned -> ongoing -> completed"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        # Scenario 1: Create task (unassigned)
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref
        
        current_time_1 = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time_1):
            service = TaskService()
            req = CreateTaskRequest(
                title="Test Task",
                creator_id="u1",
                deadline=1800000000
            )
            
            task, _ = service.create_task(req)
            assert task.status == "unassigned"
            assert task.started_at is None
            assert task.completed_at is None
        
        # Scenario 2: Update to ongoing
        mock_task_ref = Mock()
        existing_data = {
            "taskId": "test-task-id",
            "title": "Test Task",
            "creatorId": "u1",
            "ownerId": "u1",
            "status": "unassigned",
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
        
        mock_task_ref.get.side_effect = [existing_data, updated_data_2]
        mock_tasks.child.return_value = mock_task_ref
        
        with patch('task_service.current_timestamp', return_value=current_time_2):
            req2 = UpdateTaskRequest(
                task_id="test-task-id",
                status="ongoing"
            )
            task, _ = service.update_task(req2)
            assert task.status == "ongoing"
            assert task.started_at == current_time_2
            assert task.completed_at is None
        
        # Scenario 3: Update to completed
        existing_data_3 = updated_data_2.copy()
        current_time_3 = 1700020000
        updated_data_3 = existing_data_3.copy()
        updated_data_3["status"] = "completed"
        updated_data_3["completedAt"] = current_time_3
        updated_data_3["updatedAt"] = current_time_3
        
        mock_task_ref.get.side_effect = [existing_data_3, updated_data_3]
        
        with patch('task_service.current_timestamp', return_value=current_time_3):
            req3 = UpdateTaskRequest(
                task_id="test-task-id",
                status="completed"
            )
            task, _ = service.update_task(req3)
            assert task.status == "completed"
            assert task.started_at == current_time_2  # Should remain unchanged
            assert task.completed_at == current_time_3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])