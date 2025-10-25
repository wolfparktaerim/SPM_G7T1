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
                owner_id="u1",  # Same as creator
                status="unassigned"  # Explicitly set status to unassigned
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
                deadline=1800000000,
                status="unassigned"  # Explicitly set status to unassigned
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
                deadline=1800000000,
                status="unassigned"  # Explicitly set status to unassigned
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


class TestTaskEndpoints:
    """Test Flask endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @patch('app.task_service.create_task')
    def test_create_task_endpoint(self, mock_create, client, sample_task):
        """Test POST /tasks"""
        mock_create.return_value = (sample_task, None)

        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "projectId": "p1"
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['task']['title'] == "Test Task"

    @patch('app.task_service.create_task')
    def test_create_task_invalid_data(self, mock_create, client):
        """Test POST /tasks with invalid data"""
        mock_create.return_value = (None, "Validation failed")

        response = client.post('/tasks', json={
            "title": "",
            "creatorId": "u1"
        })

        assert response.status_code == 400

    def test_create_task_missing_body(self, client):
        """Test POST /tasks with missing body"""
        response = client.post('/tasks')
        assert response.status_code in [400, 415]  # 415 for unsupported media type

    @patch('app.task_service.get_all_tasks')
    def test_get_all_tasks_endpoint(self, mock_get, client, sample_task):
        """Test GET /tasks"""
        mock_get.return_value = [sample_task]

        response = client.get('/tasks')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['tasks']) == 1

    @patch('app.task_service.get_task_by_id')
    def test_get_task_by_id_endpoint(self, mock_get, client, sample_task):
        """Test GET /tasks/<id>"""
        mock_get.return_value = (sample_task, None)

        response = client.get('/tasks/t1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['task']['taskId'] == "t1"

    @patch('app.task_service.get_task_by_id')
    def test_get_task_by_id_not_found(self, mock_get, client):
        """Test GET /tasks/<id> not found"""
        mock_get.return_value = (None, "Task not found")

        response = client.get('/tasks/invalid')
        assert response.status_code == 404

    @patch('app.task_service.update_task')
    @patch('app.task_service.get_task_by_id')
    def test_update_task_endpoint(self, mock_get, mock_update, client, sample_task):
        """Test PUT /tasks/<id>"""
        updated_task = Task(**{**sample_task.__dict__, 'title': 'Updated Task'})
        mock_get.return_value = (sample_task, None)
        mock_update.return_value = (updated_task, None)

        response = client.put('/tasks/t1', json={
            "title": "Updated Task"
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['task']['title'] == "Updated Task"

    @patch('app.task_service.update_task')
    def test_update_task_not_found(self, mock_update, client):
        """Test PUT /tasks/<id> not found"""
        mock_update.return_value = (None, "Task not found")

        response = client.put('/tasks/invalid', json={
            "title": "Updated"
        }, headers={'Content-Type': 'application/json'})

        assert response.status_code == 400

    def test_update_task_missing_body(self, client):
        """Test PUT /tasks/<id> with missing body"""
        response = client.put('/tasks/t1')
        assert response.status_code in [400, 415]  # 415 for unsupported media type

    @patch('app.task_service.update_task')
    @patch('app.task_service.get_task_by_id')
    def test_update_task_invalid_data(self, mock_get, mock_update, client, sample_task):
        """Test PUT /tasks/<id> with invalid data"""
        mock_get.return_value = (sample_task, None)
        mock_update.return_value = (None, "Invalid data")

        response = client.put('/tasks/t1', json={
            "status": "invalid_status"
        })

        assert response.status_code == 400

    @patch('app.task_service.delete_task')
    def test_delete_task_endpoint(self, mock_delete, client):
        """Test DELETE /tasks/<id>"""
        mock_delete.return_value = (True, None)

        response = client.delete('/tasks/t1')
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == "Task deleted successfully"

    @patch('app.task_service.delete_task')
    def test_delete_task_not_found(self, mock_delete, client):
        """Test DELETE /tasks/<id> not found"""
        mock_delete.return_value = (False, "Task not found")

        response = client.delete('/tasks/invalid')
        assert response.status_code == 404

    @patch('app.task_service.get_tasks_by_project')
    def test_get_tasks_by_project_endpoint(self, mock_get, client, sample_task):
        """Test GET /tasks/project/<id>"""
        mock_get.return_value = [sample_task]

        response = client.get('/tasks/project/p1')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['tasks']) == 1
        assert data['tasks'][0]['projectId'] == "p1"

    def test_health_check_endpoint(self, client):
        """Test GET /health"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'task-service'

    def test_create_task_invalid_deadline(self, client):
        """Test POST /tasks with invalid deadline"""
        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": "invalid",
            "projectId": "p1"
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Deadline must be a valid epoch timestamp' in data['error']

    def test_create_task_invalid_start_date(self, client):
        """Test POST /tasks with invalid start_date"""
        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "projectId": "p1",
            "start_date": "invalid"
        })
        assert response.status_code == 400

    def test_create_task_invalid_attachments(self, client):
        """Test POST /tasks with invalid attachments"""
        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "projectId": "p1",
            "attachments": "not an array"
        })
        assert response.status_code == 400

    def test_create_task_invalid_collaborators(self, client):
        """Test POST /tasks with invalid collaborators"""
        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "projectId": "p1",
            "collaborators": "not an array"
        })
        assert response.status_code == 400

    def test_create_task_invalid_schedule(self, client):
        """Test POST /tasks with invalid schedule"""
        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "projectId": "p1",
            "schedule": "invalid"
        })
        assert response.status_code == 400

    @patch('app.task_service.get_task_by_id')
    def test_update_task_empty_title(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with empty title"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "title": "   "
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Title cannot be empty' in data['error']

    @patch('app.task_service.get_task_by_id')
    def test_update_task_invalid_deadline(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with invalid deadline"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "deadline": "invalid"
        })
        assert response.status_code == 400

    @patch('app.task_service.get_task_by_id')
    def test_update_task_invalid_start_date(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with invalid start_date"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "startDate": "invalid"
        })
        assert response.status_code == 400

    @patch('app.task_service.get_task_by_id')
    def test_update_task_invalid_priority(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with invalid priority"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "priority": "high"
        })
        assert response.status_code == 400

    @patch('app.task_service.get_task_by_id')
    def test_update_task_invalid_attachments(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with invalid attachments"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "attachments": "not an array"
        })
        assert response.status_code == 400

    @patch('app.task_service.get_task_by_id')
    def test_update_task_invalid_collaborators(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with invalid collaborators"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "collaborators": "not an array"
        })
        assert response.status_code == 400

    @patch('app.task_service.create_task')
    def test_create_task_service_error(self, mock_create, client):
        """Test POST /tasks when service returns error"""
        mock_create.return_value = (None, "Database error")

        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "projectId": "p1"
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Database error' in data['error']

    @patch('app.task_service.update_task')
    @patch('app.task_service.get_task_by_id')
    def test_update_task_invalid_schedule(self, mock_get, mock_update, client, sample_task):
        """Test PUT /tasks/<id> with invalid schedule"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "schedule": "invalid_schedule"
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Schedule must be one of' in data['error']

    def test_create_task_with_negative_start_date(self, client):
        """Test POST /tasks with negative start_date"""
        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "projectId": "p1",
            "start_date": -1  # Invalid timestamp
        })
        assert response.status_code == 400

    @patch('app.task_service.get_task_by_id')
    def test_update_task_with_negative_start_date(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with negative start_date"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1', json={
            "startDate": -1  # Invalid timestamp
        })
        assert response.status_code == 400

    def test_create_task_with_null_body(self, client):
        """Test POST /tasks with null JSON body"""
        response = client.post('/tasks',
                              data='null',
                              content_type='application/json')
        assert response.status_code == 400

    @patch('app.task_service.get_task_by_id')
    def test_update_task_with_null_body(self, mock_get, client, sample_task):
        """Test PUT /tasks/<id> with null JSON body"""
        mock_get.return_value = (sample_task, None)

        response = client.put('/tasks/t1',
                             data='null',
                             content_type='application/json')
        assert response.status_code == 400


class TestTaskServiceAdditionalMethods:
    """Test additional TaskService methods for better coverage"""

    def test_is_same_date_true(self, mock_db):
        """Test is_same_date returns True for same date"""
        service = TaskService()
        # Two timestamps on the same day
        ts1 = 1700000000  # Nov 14, 2023 22:13:20 UTC
        ts2 = 1700010000  # Nov 15, 2023 01:00:00 UTC (same day in some timezone but different in UTC)
        # Let's use timestamps that are definitely same day in UTC
        ts1 = 1700000000  # Nov 14, 2023 22:13:20 UTC
        ts2 = 1700050000  # Nov 15, 2023 12:06:40 UTC
        # Actually let's use timestamps that are same calendar date
        from datetime import datetime, timezone
        dt = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        ts1 = int(dt.timestamp())
        ts2 = int(dt.replace(hour=15).timestamp())

        result = service.is_same_date(ts1, ts2)
        assert result == True

    def test_is_same_date_false(self, mock_db):
        """Test is_same_date returns False for different dates"""
        service = TaskService()
        from datetime import datetime, timezone, timedelta
        dt1 = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = dt1 + timedelta(days=1)
        ts1 = int(dt1.timestamp())
        ts2 = int(dt2.timestamp())

        result = service.is_same_date(ts1, ts2)
        assert result == False

    def test_should_task_be_active_none_start_date(self, mock_db):
        """Test should_task_be_active with None start_date"""
        service = TaskService()
        result = service.should_task_be_active(None, 1700000000)
        assert result == False

    def test_should_task_be_active_future_start_date(self, mock_db):
        """Test should_task_be_active with future start_date"""
        service = TaskService()
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=5)

        result = service.should_task_be_active(int(future.timestamp()), int(now.timestamp()))
        assert result == False

    def test_should_task_be_active_past_start_date(self, mock_db):
        """Test should_task_be_active with past start_date"""
        service = TaskService()
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=5)

        result = service.should_task_be_active(int(past.timestamp()), int(now.timestamp()))
        assert result == True

    @patch('task_service.current_timestamp')
    def test_calculate_new_start_date_daily(self, mock_timestamp, mock_db):
        """Test calculate_new_start_date for daily schedule"""
        from datetime import datetime, timezone, timedelta
        old_date = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = int(old_date.timestamp())

        service = TaskService()
        old_ts = int(old_date.timestamp())
        new_ts = service.calculate_new_start_date(old_ts, "daily")

        # Should be 1 day later
        new_date = datetime.fromtimestamp(new_ts, tz=timezone.utc)
        expected_date = old_date + timedelta(days=1)
        assert new_date.date() == expected_date.date()

    @patch('task_service.current_timestamp')
    def test_calculate_new_start_date_weekly(self, mock_timestamp, mock_db):
        """Test calculate_new_start_date for weekly schedule"""
        from datetime import datetime, timezone, timedelta
        old_date = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = int(old_date.timestamp())

        service = TaskService()
        old_ts = int(old_date.timestamp())
        new_ts = service.calculate_new_start_date(old_ts, "weekly")

        # Should be 7 days later
        new_date = datetime.fromtimestamp(new_ts, tz=timezone.utc)
        expected_date = old_date + timedelta(weeks=1)
        assert new_date.date() == expected_date.date()

    @patch('task_service.current_timestamp')
    def test_calculate_new_start_date_monthly(self, mock_timestamp, mock_db):
        """Test calculate_new_start_date for monthly schedule"""
        from datetime import datetime, timezone
        old_date = datetime(2023, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_timestamp.return_value = int(old_date.timestamp())

        service = TaskService()
        old_ts = int(old_date.timestamp())
        new_ts = service.calculate_new_start_date(old_ts, "monthly")

        # Should be 1 month later
        new_date = datetime.fromtimestamp(new_ts, tz=timezone.utc)
        # Month should be incremented
        assert new_date.month == 12 or (new_date.month == 1 and new_date.year == 2024)

    @patch('task_service.requests.post')
    def test_send_task_update_notification_success(self, mock_post, mock_db):
        """Test send_task_update_notification successfully sends"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()

        # Setup user data
        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = {
            "taskUpdateReminders": True,
            "channel": "both"
        }

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 200

        service = TaskService()
        service.send_task_update_notification("t1", "Test Task", "to_do", "in_progress", "u1", ["u2"])

        # Should have made notification API call
        assert mock_post.called

    @patch('task_service.requests.post')
    def test_send_task_update_notification_disabled_preference(self, mock_post, mock_db):
        """Test send_task_update_notification with disabled user preference"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()

        # Setup user data with notifications disabled
        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = {
            "taskUpdateReminders": False
        }

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            return Mock()

        mock_db.side_effect = db_side_effect

        service = TaskService()
        service.send_task_update_notification("t1", "Test Task", "to_do", "in_progress", "u1", ["u2"])

        # Should not make API call since preference is disabled
        mock_post.assert_not_called()

    @patch('task_service.requests.post')
    def test_send_task_update_notification_no_preferences(self, mock_post, mock_db):
        """Test send_task_update_notification with no user preferences set"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()

        # Setup user data but no preferences
        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = None

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 200

        service = TaskService()
        service.send_task_update_notification("t1", "Test Task", "to_do", "in_progress", "u1", ["u2"])

        # Should use default settings and send notification
        assert mock_post.called

    @patch('task_service.requests.post')
    def test_send_task_update_notification_api_failure(self, mock_post, mock_db):
        """Test send_task_update_notification handles API failure"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()

        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = None

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Server error"

        service = TaskService()
        # Should not raise exception
        service.send_task_update_notification("t1", "Test Task", "to_do", "in_progress", "u1", ["u2"])

    @patch('task_service.requests.post')
    def test_send_task_update_notification_exception(self, mock_post, mock_db):
        """Test send_task_update_notification handles exceptions"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()

        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        mock_prefs_ref.child.return_value.get.return_value = None

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.side_effect = Exception("Network error")

        service = TaskService()
        # Should not raise exception, should handle gracefully
        service.send_task_update_notification("t1", "Test Task", "to_do", "in_progress", "u1", ["u2"])

    @patch('task_service.requests.post')
    def test_send_task_update_notification_preference_fetch_error(self, mock_post, mock_db):
        """Test send_task_update_notification when preference fetch fails"""
        mock_users_ref = Mock()
        mock_prefs_ref = Mock()

        mock_users_ref.child.return_value.get.return_value = {"email": "user@test.com"}
        # Simulate exception when fetching preferences
        mock_prefs_ref.child.return_value.get.side_effect = Exception("DB error")

        def db_side_effect(arg):
            if arg == "users":
                return mock_users_ref
            elif arg == "notificationPreferences":
                return mock_prefs_ref
            return Mock()

        mock_db.side_effect = db_side_effect
        mock_post.return_value.status_code = 200

        service = TaskService()
        # Should fallback to default and still send
        service.send_task_update_notification("t1", "Test Task", "to_do", "in_progress", "u1", ["u2"])

        assert mock_post.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])