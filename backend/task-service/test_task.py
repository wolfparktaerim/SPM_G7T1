# backend/task-service/test_task.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Set environment variables before imports
os.environ['JSON_PATH'] = '/tmp/dummy.json'
os.environ['DATABASE_URL'] = 'https://dummy.firebaseio.com'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a mock Firebase app that will be returned by initialize_app
mock_firebase_app = MagicMock()

# Mock Firebase admin at module level BEFORE any imports
firebase_admin_patcher = patch.dict('sys.modules', {
    'firebase_admin': MagicMock(),
    'firebase_admin.credentials': MagicMock(),
    'firebase_admin.db': MagicMock()
})
firebase_admin_patcher.start()

# Now we can import
from task_service import TaskService
from models import Task, CreateTaskRequest, UpdateTaskRequest
from app import app


@pytest.fixture(autouse=True)
def mock_firebase():
    """Mock Firebase for all tests"""
    with patch('firebase_admin.initialize_app', return_value=mock_firebase_app):
        with patch('firebase_admin.get_app', return_value=mock_firebase_app):
            with patch('firebase_admin.credentials.Certificate'):
                yield


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


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
        custom_schedule=None
    )


class TestTaskModels:
    """Test task models"""
    
    def test_task_from_dict(self):
        """Test creating Task from dictionary"""
        data = {
            "taskId": "t1",
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "status": "ongoing",
            "notes": "Test",
            "attachments": [],
            "collaborators": ["u1"],
            "projectId": "p1",
            "ownerId": "u1",
            "priority": 1,
            "createdAt": 1600000000,
            "updatedAt": 1600000000,
            "start_date": 1600000000,
            "active": True,
            "scheduled": False,
            "schedule": "daily",
            "custom_schedule": None
        }
        task = Task.from_dict(data)
        
        assert task.task_id == "t1"
        assert task.title == "Test Task"
        assert task.active == True
        assert task.schedule == "daily"
    
    def test_task_to_dict(self, sample_task):
        """Test converting Task to dictionary"""
        data = sample_task.to_dict()
        
        assert data["taskId"] == "t1"
        assert data["title"] == "Test Task"
        assert data["active"] == True
    
    def test_create_task_request_validate_success(self):
        """Test validation with valid data"""
        req = CreateTaskRequest(
            title="Test Task",
            creator_id="u1",
            deadline=1700000000
        )
        errors = req.validate()
        assert len(errors) == 0
    
    def test_create_task_request_validate_missing_fields(self):
        """Test validation with missing fields"""
        req = CreateTaskRequest(
            title="",
            creator_id="",
            deadline=0
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("title" in error for error in errors)
        assert any("creatorId" in error for error in errors)
    
    def test_create_task_request_custom_schedule(self):
        """Test validation with custom schedule"""
        req = CreateTaskRequest(
            title="Test",
            creator_id="u1",
            deadline=1700000000,
            schedule="custom",
            custom_schedule=None
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("custom_schedule" in error for error in errors)


class TestTaskService:
    """Test task service class"""
    
    def test_validate_status(self, mock_db):
        """Test status validation"""
        mock_db.return_value = Mock()
        service = TaskService()
        
        assert service.validate_status("ongoing") == True
        assert service.validate_status("completed") == True
        assert service.validate_status("invalid") == False
    
    def test_should_task_be_active_past_start(self, mock_db):
        """Test task should be active with past start date"""
        mock_db.return_value = Mock()
        service = TaskService()
        now = 1700000000
        past_start = 1600000000
        
        assert service.should_task_be_active(past_start, now) == True
    
    def test_should_task_be_active_future_start(self, mock_db):
        """Test task should not be active with future start date"""
        mock_db.return_value = Mock()
        service = TaskService()
        now = 1700000000
        future_start = 1800000000
        
        assert service.should_task_be_active(future_start, now) == False
    
    def test_should_task_be_active_same_date(self, mock_db):
        """Test task should be active on start date"""
        mock_db.return_value = Mock()
        service = TaskService()
        # Same date
        date_ts = 1700000000
        
        assert service.should_task_be_active(date_ts, date_ts) == True
    
    def test_calculate_new_start_date_daily(self, mock_db):
        """Test calculating next start date for daily schedule"""
        mock_db.return_value = Mock()
        
        # Mock current_timestamp to control the "now" time
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            old_start = 1600000000  # Past date
            
            new_start = service.calculate_new_start_date(old_start, "daily")
            
            # Should be 1 day after current time
            assert new_start == current_time + (24 * 60 * 60)
    
    def test_calculate_new_start_date_weekly(self, mock_db):
        """Test calculating next start date for weekly schedule"""
        mock_db.return_value = Mock()
        
        # Mock current_timestamp to control the "now" time
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            old_start = 1600000000  # Past date
            
            new_start = service.calculate_new_start_date(old_start, "weekly")
            
            # Should be 7 days after current time
            assert new_start == current_time + (7 * 24 * 60 * 60)
    
    def test_calculate_new_start_date_custom(self, mock_db):
        """Test calculating next start date for custom schedule"""
        mock_db.return_value = Mock()
        
        # Mock current_timestamp to control the "now" time
        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            old_start = 1600000000  # Past date
            custom_days = 10
            
            new_start = service.calculate_new_start_date(old_start, "custom", custom_days)
            
            # Should be 10 days after current time
            assert new_start == current_time + (10 * 24 * 60 * 60)
    
    def test_create_task(self, mock_db):
        """Test creating a task"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref
        
        service = TaskService()
        req = CreateTaskRequest(
            title="Test Task",
            creator_id="u1",
            deadline=1700000000,
            project_id="p1"
        )
        
        task, error = service.create_task(req)
        
        assert error is None
        assert task.title == "Test Task"
        assert task.task_id == "test-task-id"
        assert task.owner_id == "u1"  # Should default to creator
        mock_new_ref.set.assert_called_once()
    
    def test_create_task_with_owner(self, mock_db):
        """Test creating task with explicit owner"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref
        
        service = TaskService()
        req = CreateTaskRequest(
            title="Test Task",
            creator_id="u1",
            deadline=1700000000,
            owner_id="u2"
        )
        
        task, error = service.create_task(req)
        
        assert task.owner_id == "u2"
    
    def test_get_all_tasks(self, mock_db):
        """Test getting all active tasks"""
        mock_tasks = Mock()
        mock_db.return_value = mock_tasks
        
        current_time = 1700000000
        mock_tasks.get.return_value = {
            "t1": {
                "taskId": "t1",
                "title": "Active Task",
                "creatorId": "u1",
                "deadline": 1800000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "projectId": "",
                "ownerId": "u1",
                "priority": 0,
                "createdAt": 1600000000,
                "updatedAt": 1600000000,
                "start_date": 1600000000,
                "active": False,  # Will be updated
                "scheduled": False,
                "schedule": "daily"
            },
            "t2": {
                "taskId": "t2",
                "title": "Future Task",
                "creatorId": "u1",
                "deadline": 1900000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "projectId": "",
                "ownerId": "u1",
                "priority": 0,
                "createdAt": 1600000000,
                "updatedAt": 1600000000,
                "start_date": 1800000000,  # Future
                "active": False,
                "scheduled": False,
                "schedule": "daily"
            }
        }
        
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            tasks = service.get_all_tasks()
        
        # Only t1 should be returned (active)
        assert len(tasks) == 1
        assert tasks[0].task_id == "t1"
    
    def test_get_task_by_id(self, mock_db):
        """Test getting task by ID"""
        mock_tasks = Mock()
        mock_db.return_value = mock_tasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {
            "taskId": "t1",
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "status": "ongoing",
            "notes": "",
            "attachments": [],
            "collaborators": [],
            "projectId": "",
            "ownerId": "u1",
            "priority": 0,
            "createdAt": 1600000000,
            "updatedAt": 1600000000,
            "start_date": 1600000000,
            "active": True,
            "scheduled": False,
            "schedule": "daily"
        }
        mock_tasks.child.return_value = mock_task_ref
        
        service = TaskService()
        task, error = service.get_task_by_id("t1")
        
        assert error is None
        assert task.task_id == "t1"
    
    def test_get_task_by_id_not_found(self, mock_db):
        """Test getting non-existent task"""
        mock_tasks = Mock()
        mock_db.return_value = mock_tasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = None
        mock_tasks.child.return_value = mock_task_ref
        
        service = TaskService()
        task, error = service.get_task_by_id("invalid")
        
        assert task is None
        assert "not found" in error.lower()
    
    def test_update_task(self, mock_db):
        """Test updating task"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.side_effect = [
            {  # First call - existing task
                "taskId": "t1",
                "status": "ongoing",
                "scheduled": False
            },
            {  # Second call - updated task
                "taskId": "t1",
                "title": "Updated Title",
                "creatorId": "u1",
                "deadline": 1700000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "projectId": "",
                "ownerId": "u1",
                "priority": 0,
                "createdAt": 1600000000,
                "updatedAt": 1700000000,
                "start_date": 1600000000,
                "active": True,
                "scheduled": False,
                "schedule": "daily"
            }
        ]
        mock_tasks.child.return_value = mock_task_ref
        
        service = TaskService()
        req = UpdateTaskRequest(
            task_id="t1",
            title="Updated Title"
        )
        
        task, error = service.update_task(req)
        
        assert error is None
        mock_task_ref.update.assert_called_once()
    
    def test_update_task_empty_title(self, mock_db):
        """Test updating task with empty title"""
        mock_tasks = Mock()
        mock_db.return_value = mock_tasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        service = TaskService()
        req = UpdateTaskRequest(
            task_id="t1",
            title="   "  # Empty/whitespace only
        )
        
        task, error = service.update_task(req)
        
        assert task is None
        assert "empty" in error.lower()
    
    def test_delete_task(self, mock_db):
        """Test deleting task"""
        mock_tasks = Mock()
        mock_db.return_value = mock_tasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {"taskId": "t1"}
        mock_tasks.child.return_value = mock_task_ref
        
        service = TaskService()
        success, error = service.delete_task("t1")
        
        assert success == True
        assert error is None
        mock_task_ref.delete.assert_called_once()
    
    def test_get_tasks_by_project(self, mock_db):
        """Test getting tasks by project"""
        mock_tasks = Mock()
        mock_db.return_value = mock_tasks
        
        current_time = 1700000000
        mock_tasks.get.return_value = {
            "t1": {
                "taskId": "t1",
                "title": "Project Task",
                "creatorId": "u1",
                "deadline": 1800000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "projectId": "p1",
                "ownerId": "u1",
                "priority": 0,
                "createdAt": 1600000000,
                "updatedAt": 1600000000,
                "start_date": 1600000000,
                "active": False,
                "scheduled": False,
                "schedule": "daily"
            },
            "t2": {
                "taskId": "t2",
                "title": "Other Project Task",
                "creatorId": "u1",
                "deadline": 1800000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "projectId": "p2",
                "ownerId": "u1",
                "priority": 0,
                "createdAt": 1600000000,
                "updatedAt": 1600000000,
                "start_date": 1600000000,
                "active": False,
                "scheduled": False,
                "schedule": "daily"
            }
        }
        
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            tasks = service.get_tasks_by_project("p1")
        
        assert len(tasks) == 1
        assert tasks[0].project_id == "p1"


class TestTaskEndpoints:
    """Test Flask endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'task-service'
    
    def test_create_task_missing_body(self, client):
        """Test creating task without body (no Content-Type)"""
        response = client.post('/tasks')
        # Flask returns 415 when Content-Type is missing for JSON endpoints
        assert response.status_code == 415
    
    @patch('app.task_service.create_task')
    def test_create_task_success(self, mock_create, client, sample_task):
        """Test successful task creation"""
        mock_create.return_value = (sample_task, None)
        
        response = client.post('/tasks', json={
            "title": "Test Task",
            "creatorId": "u1",
            "deadline": 1700000000,
            "attachments": [],
            "collaborators": [],
            "schedule": "daily"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'task' in data
    
    @patch('app.task_service.get_all_tasks')
    def test_get_all_tasks(self, mock_get, client):
        """Test getting all tasks"""
        mock_get.return_value = []
        
        response = client.get('/tasks')
        assert response.status_code == 200
        data = response.get_json()
        assert 'tasks' in data
    
    @patch('app.task_service.get_task_by_id')
    def test_get_task_by_id(self, mock_get, client, sample_task):
        """Test getting task by ID"""
        mock_get.return_value = (sample_task, None)
        
        response = client.get('/tasks/t1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'task' in data
    
    @patch('app.task_service.update_task')
    def test_update_task(self, mock_update, client, sample_task):
        """Test updating task"""
        mock_update.return_value = (sample_task, None)
        
        response = client.put('/tasks/t1', json={
            "title": "Updated Title",
            "attachments": [],
            "collaborators": []
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'task' in data
    
    @patch('app.task_service.delete_task')
    def test_delete_task(self, mock_delete, client):
        """Test deleting task"""
        mock_delete.return_value = (True, None)
        
        response = client.delete('/tasks/t1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    @patch('app.task_service.get_tasks_by_project')
    def test_get_tasks_by_project(self, mock_get, client):
        """Test getting tasks by project"""
        mock_get.return_value = []
        
        response = client.get('/tasks/project/p1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'tasks' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])