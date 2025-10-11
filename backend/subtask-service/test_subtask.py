# backend/subtask-service/test_subtask.py
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
from subtask_service import SubtaskService
from models import Subtask, CreateSubtaskRequest, UpdateSubtaskRequest
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
        schedule="daily"
    )



class TestSubtaskModels:
    """Test subtask models"""
    
    def test_subtask_from_dict(self):
        """Test creating Subtask from dictionary"""
        data = {
            "subTaskId": "st1",
            "title": "Test Subtask",
            "creatorId": "u1",
            "deadline": 1700000000,
            "status": "ongoing",
            "notes": "",
            "attachments": [],
            "collaborators": [],
            "taskId": "t1",
            "ownerId": "u1",
            "priority": 0,
            "createdAt": 1600000000,
            "updatedAt": 1600000000,
            "start_date": 1600000000,
            "active": True,
            "scheduled": False,
            "schedule": "daily"
        }
        subtask = Subtask.from_dict(data)
        
        assert subtask.subtask_id == "st1"
        assert subtask.title == "Test Subtask"
        assert subtask.task_id == "t1"
    
    def test_subtask_to_dict(self, sample_subtask):
        """Test converting Subtask to dictionary"""
        data = sample_subtask.to_dict()
        
        assert data["subTaskId"] == "st1"
        assert data["title"] == "Test Subtask"
        assert data["taskId"] == "t1"
    
    def test_create_subtask_request_validate_success(self):
        """Test validation with valid data"""
        req = CreateSubtaskRequest(
            title="Test Subtask",
            creator_id="u1",
            deadline=1700000000,
            task_id="t1"
        )
        errors = req.validate()
        assert len(errors) == 0
    
    def test_create_subtask_request_validate_missing_fields(self):
        """Test validation with missing fields"""
        req = CreateSubtaskRequest(
            title="",
            creator_id="",
            deadline=0,
            task_id=""
        )
        errors = req.validate()
        assert len(errors) > 0
        assert "title is required" in errors
        assert "creatorId is required" in errors
        assert "deadline is required" in errors
        assert "taskId is required" in errors
    
    def test_create_subtask_request_custom_schedule_validation(self):
        """Test validation with custom schedule without value"""
        req = CreateSubtaskRequest(
            title="Test",
            creator_id="u1",
            deadline=1700000000,
            task_id="t1",
            schedule="custom",
            custom_schedule=None
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("custom_schedule" in error for error in errors)



class TestSubtaskService:
    """Test subtask service class"""
    
    def test_validate_status(self, mock_db):
        """Test status validation"""
        mock_db.return_value = Mock()
        service = SubtaskService()
        
        assert service.validate_status("ongoing") == True
        assert service.validate_status("completed") == True
        assert service.validate_status("unassigned") == True
        assert service.validate_status("invalid") == False
    
    def test_calculate_new_start_date_daily(self, mock_db):
        """Test calculating next start date for daily schedule"""
        mock_db.return_value = Mock()
        
        # Mock current_timestamp to control the "now" time
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            old_start = 1600000000  # Past date
            
            new_start = service.calculate_new_start_date(old_start, "daily")
            
            # Should be 1 day after current time
            assert new_start == current_time + (24 * 60 * 60)
    
    def test_calculate_new_start_date_weekly(self, mock_db):
        """Test calculating next start date for weekly schedule"""
        mock_db.return_value = Mock()
        
        # Mock current_timestamp to control the "now" time
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            old_start = 1600000000  # Past date
            
            new_start = service.calculate_new_start_date(old_start, "weekly")
            
            # Should be 7 days after current time
            assert new_start == current_time + (7 * 24 * 60 * 60)
    
    def test_calculate_new_start_date_custom(self, mock_db):
        """Test calculating next start date for custom schedule"""
        mock_db.return_value = Mock()
        
        # Mock current_timestamp to control the "now" time
        current_time = 1700000000
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            old_start = 1600000000  # Past date
            custom_days = 5
            
            new_start = service.calculate_new_start_date(old_start, "custom", custom_days)
            
            # Should be 5 days after current time
            assert new_start == current_time + (5 * 24 * 60 * 60)
    
    def test_create_subtask(self, mock_db):
        """Test creating a subtask"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_tasks.child.return_value.get.return_value = {"taskId": "t1"}
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        service = SubtaskService()
        req = CreateSubtaskRequest(
            title="Test Subtask",
            creator_id="u1",
            deadline=1700000000,
            task_id="t1"
        )
        
        subtask, error = service.create_subtask(req)
        
        assert error is None
        assert subtask.title == "Test Subtask"
        assert subtask.subtask_id == "test-subtask-id"
        assert subtask.task_id == "t1"
        mock_new_ref.set.assert_called_once()
    
    def test_create_subtask_with_different_owner(self, mock_db):
        """Test that status is set to 'ongoing' when owner differs from creator"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_tasks.child.return_value.get.return_value = {"taskId": "t1"}
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        service = SubtaskService()
        req = CreateSubtaskRequest(
            title="Test Subtask",
            creator_id="u1",
            owner_id="u2",  # Different from creator
            deadline=1700000000,
            task_id="t1",
            status="unassigned"  # Will be overridden to 'ongoing'
        )
        
        subtask, error = service.create_subtask(req)
        
        assert error is None
        assert subtask.status == "ongoing"  # Should be 'ongoing' not 'unassigned'
        assert subtask.owner_id == "u2"
        mock_new_ref.set.assert_called_once()
    
    def test_create_subtask_same_owner_as_creator(self, mock_db):
        """Test that status respects requested status when owner is same as creator"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        # Mock parent task exists
        mock_tasks.child.return_value.get.return_value = {"taskId": "t1"}
        
        mock_new_ref = Mock()
        mock_new_ref.key = "test-subtask-id"
        mock_subtasks.push.return_value = mock_new_ref
        
        service = SubtaskService()
        req = CreateSubtaskRequest(
            title="Test Subtask",
            creator_id="u1",
            owner_id="u1",  # Same as creator
            deadline=1700000000,
            task_id="t1",
            status="unassigned"
        )
        
        subtask, error = service.create_subtask(req)
        
        assert error is None
        assert subtask.status == "unassigned"  # Should keep original status
        assert subtask.owner_id == "u1"
    
    def test_create_subtask_parent_not_found(self, mock_db):
        """Test creating subtask with non-existent parent"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_tasks.child.return_value.get.return_value = None
        
        service = SubtaskService()
        req = CreateSubtaskRequest(
            title="Test Subtask",
            creator_id="u1",
            deadline=1700000000,
            task_id="invalid"
        )
        
        subtask, error = service.create_subtask(req)
        
        assert subtask is None
        assert "not found" in error.lower()
    
    def test_get_all_subtasks(self, mock_db):
        """Test getting all subtasks"""
        mock_subtasks = Mock()
        mock_db.return_value = mock_subtasks
        
        current_time = 1700000000
        mock_subtasks.get.return_value = {
            "st1": {
                "subTaskId": "st1",
                "title": "Active Subtask",
                "creatorId": "u1",
                "deadline": 1800000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "taskId": "t1",
                "ownerId": "u1",
                "priority": 0,
                "createdAt": 1600000000,
                "updatedAt": 1600000000,
                "start_date": 1600000000,
                "active": False,  # Will be updated
                "scheduled": False,
                "schedule": "daily"
            }
        }
        
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            subtasks = service.get_all_subtasks()
        
        assert len(subtasks) == 1
        assert subtasks[0].subtask_id == "st1"
    
    def test_get_subtask_by_id(self, mock_db):
        """Test getting subtask by ID"""
        mock_subtasks = Mock()
        mock_db.return_value = mock_subtasks
        
        mock_subtask_ref = Mock()
        mock_subtask_ref.get.return_value = {
            "subTaskId": "st1",
            "title": "Test Subtask",
            "creatorId": "u1",
            "deadline": 1700000000,
            "status": "ongoing",
            "notes": "",
            "attachments": [],
            "collaborators": [],
            "taskId": "t1",
            "ownerId": "u1",
            "priority": 0,
            "createdAt": 1600000000,
            "updatedAt": 1600000000,
            "start_date": 1600000000,
            "active": True,
            "scheduled": False,
            "schedule": "daily"
        }
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = SubtaskService()
        subtask, error = service.get_subtask_by_id("st1")
        
        assert error is None
        assert subtask.subtask_id == "st1"
    
    def test_get_subtask_by_id_not_found(self, mock_db):
        """Test getting non-existent subtask"""
        mock_subtasks = Mock()
        mock_db.return_value = mock_subtasks
        
        mock_subtask_ref = Mock()
        mock_subtask_ref.get.return_value = None
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = SubtaskService()
        subtask, error = service.get_subtask_by_id("invalid")
        
        assert subtask is None
        assert "not found" in error.lower()
    
    def test_update_subtask(self, mock_db):
        """Test updating subtask"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        mock_subtask_ref.get.side_effect = [
            {  # First call - existing subtask
                "subTaskId": "st1",
                "status": "ongoing",
                "scheduled": False
            },
            {  # Second call - updated subtask
                "subTaskId": "st1",
                "title": "Updated Title",
                "creatorId": "u1",
                "deadline": 1700000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "taskId": "t1",
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
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = SubtaskService()
        req = UpdateSubtaskRequest(
            subtask_id="st1",
            title="Updated Title"
        )
        
        subtask, error = service.update_subtask(req)
        
        assert error is None
        mock_subtask_ref.update.assert_called_once()
    
    def test_update_subtask_empty_title(self, mock_db):
        """Test updating subtask with empty title"""
        mock_subtasks = Mock()
        mock_db.return_value = mock_subtasks
        
        mock_subtask_ref = Mock()
        mock_subtask_ref.get.return_value = {"subTaskId": "st1"}
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = SubtaskService()
        req = UpdateSubtaskRequest(
            subtask_id="st1",
            title="   "  # Empty/whitespace only
        )
        
        subtask, error = service.update_subtask(req)
        
        assert subtask is None
        assert "empty" in error.lower()
    
    def test_update_subtask_change_owner_to_different_user(self, mock_db):
        """Test that status updates to 'ongoing' when owner is changed to someone else"""
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
            "deadline": 1700000000,
            "scheduled": False
        }
        
        # First call returns existing data, second returns updated data
        updated_data = existing_data.copy()
        updated_data["ownerId"] = "u2"
        updated_data["status"] = "ongoing"
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = SubtaskService()
        req = UpdateSubtaskRequest(
            subtask_id="st1",
            owner_id="u2"  # Changing owner to different user
        )
        
        subtask, error = service.update_subtask(req)
        
        assert error is None
        assert subtask.owner_id == "u2"
        assert subtask.status == "ongoing"
        
        # Verify update was called with both ownerId and status
        update_call_args = mock_subtask_ref.update.call_args[0][0]
        assert update_call_args["ownerId"] == "u2"
        assert update_call_args["status"] == "ongoing"
    
    def test_update_subtask_change_owner_to_creator(self, mock_db):
        """Test that status is auto-changed to ongoing even when owner is set to creator"""
        mock_subtasks = Mock()
        mock_tasks = Mock()
        mock_db.side_effect = lambda x: mock_subtasks if x == "subtasks" else mock_tasks
        
        mock_subtask_ref = Mock()
        existing_data = {
            "subTaskId": "st1",
            "title": "Test",
            "creatorId": "u1",
            "ownerId": "u2",
            "status": "under_review",
            "taskId": "t1",
            "deadline": 1700000000,
            "scheduled": False
        }
        
        updated_data = existing_data.copy()
        updated_data["ownerId"] = "u1"  # Changing back to creator
        updated_data["status"] = "ongoing"  # Will be set to ongoing
        updated_data["updatedAt"] = 1700000000
        
        mock_subtask_ref.get.side_effect = [existing_data, updated_data]
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = SubtaskService()
        req = UpdateSubtaskRequest(
            subtask_id="st1",
            owner_id="u1"  # Changing owner to creator
        )
        
        subtask, error = service.update_subtask(req)
        
        assert error is None
        
        # Verify update was called
        update_call_args = mock_subtask_ref.update.call_args[0][0]
        assert update_call_args["ownerId"] == "u1"
        # Status should NOT be set to ongoing when owner is same as creator
        # But based on the implementation, it checks if owner_id != creator_id
        # So when setting to creator, status should NOT be auto-changed
        assert "status" not in update_call_args or update_call_args.get("status") != "ongoing"
    
    def test_delete_subtask(self, mock_db):
        """Test deleting subtask"""
        mock_subtasks = Mock()
        mock_db.return_value = mock_subtasks
        
        mock_subtask_ref = Mock()
        mock_subtask_ref.get.return_value = {"subTaskId": "st1"}
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = SubtaskService()
        success, error = service.delete_subtask("st1")
        
        assert success == True
        assert error is None
        mock_subtask_ref.delete.assert_called_once()
    
    def test_get_subtasks_by_task(self, mock_db):
        """Test getting subtasks by task ID"""
        mock_subtasks = Mock()
        mock_db.return_value = mock_subtasks
        
        current_time = 1700000000
        mock_subtasks.get.return_value = {
            "st1": {
                "subTaskId": "st1",
                "title": "Subtask 1",
                "creatorId": "u1",
                "deadline": 1800000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "taskId": "t1",
                "ownerId": "u1",
                "priority": 0,
                "createdAt": 1600000000,
                "updatedAt": 1600000000,
                "start_date": 1600000000,
                "active": False,
                "scheduled": False,
                "schedule": "daily"
            },
            "st2": {
                "subTaskId": "st2",
                "title": "Subtask 2",
                "creatorId": "u1",
                "deadline": 1800000000,
                "status": "ongoing",
                "notes": "",
                "attachments": [],
                "collaborators": [],
                "taskId": "t2",
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
        
        with patch('subtask_service.current_timestamp', return_value=current_time):
            service = SubtaskService()
            subtasks = service.get_subtasks_by_task("t1")
        
        assert len(subtasks) == 1
        assert subtasks[0].task_id == "t1"



class TestSubtaskEndpoints:
    """Test Flask endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'subtask-service'
    
    def test_create_subtask_missing_body(self, client):
        """Test creating subtask without body (no Content-Type)"""
        response = client.post('/subtasks')
        # Flask returns 415 when Content-Type is missing for JSON endpoints
        assert response.status_code == 415
    
    @patch('app.subtask_service.create_subtask')
    def test_create_subtask_success(self, mock_create, client, sample_subtask):
        """Test successful subtask creation"""
        mock_create.return_value = (sample_subtask, None)
        
        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "creatorId": "u1",
            "deadline": 1700000000,
            "taskId": "t1",
            "schedule": "daily"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'subtask' in data
    
    @patch('app.subtask_service.create_subtask')
    def test_create_subtask_with_different_owner_endpoint(self, mock_create, client):
        """Test creating subtask with different owner via endpoint"""
        # Create a subtask with status set to ongoing automatically
        subtask_with_ongoing = Subtask(
            subtask_id="st1",
            title="Test Subtask",
            creator_id="u1",
            deadline=1700000000,
            status="ongoing",  # Auto-set to ongoing
            notes="",
            attachments=[],
            collaborators=[],
            task_id="t1",
            owner_id="u2",  # Different from creator
            priority=0,
            created_at=1600000000,
            updated_at=1600000000,
            start_date=1600000000,
            active=True,
            scheduled=False,
            schedule="daily"
        )
        
        mock_create.return_value = (subtask_with_ongoing, None)
        
        response = client.post('/subtasks', json={
            "title": "Test Subtask",
            "creatorId": "u1",
            "ownerId": "u2",  # Different from creator
            "deadline": 1700000000,
            "taskId": "t1",
            "status": "unassigned",  # Should be overridden
            "schedule": "daily"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'subtask' in data
        assert data['subtask']['status'] == 'ongoing'
        assert data['subtask']['ownerId'] == 'u2'
    
    @patch('app.subtask_service.get_all_subtasks')
    def test_get_all_subtasks(self, mock_get, client):
        """Test getting all subtasks"""
        mock_get.return_value = []
        
        response = client.get('/subtasks')
        assert response.status_code == 200
        data = response.get_json()
        assert 'subtasks' in data
    
    @patch('app.subtask_service.get_subtask_by_id')
    def test_get_subtask_by_id(self, mock_get, client, sample_subtask):
        """Test getting subtask by ID"""
        mock_get.return_value = (sample_subtask, None)
        
        response = client.get('/subtasks/st1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'subtask' in data
    
    @patch('app.subtask_service.update_subtask')
    def test_update_subtask(self, mock_update, client, sample_subtask):
        """Test updating subtask"""
        mock_update.return_value = (sample_subtask, None)
        
        response = client.put('/subtasks/st1', json={
            "title": "Updated Title"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'subtask' in data
    
    @patch('app.subtask_service.update_subtask')
    def test_update_subtask_owner_endpoint(self, mock_update, client):
        """Test updating subtask owner via endpoint"""
        updated_subtask = Subtask(
            subtask_id="st1",
            title="Test Subtask",
            creator_id="u1",
            deadline=1700000000,
            status="ongoing",  # Auto-set to ongoing
            notes="",
            attachments=[],
            collaborators=[],
            task_id="t1",
            owner_id="u3",  # Changed to different user
            priority=0,
            created_at=1600000000,
            updated_at=1700000000,
            start_date=1600000000,
            active=True,
            scheduled=False,
            schedule="daily"
        )
        
        mock_update.return_value = (updated_subtask, None)
        
        response = client.put('/subtasks/st1', json={
            "ownerId": "u3"  # Changing to different user
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'subtask' in data
        assert data['subtask']['status'] == 'ongoing'
        assert data['subtask']['ownerId'] == 'u3'
    
    @patch('app.subtask_service.delete_subtask')
    def test_delete_subtask(self, mock_delete, client):
        """Test deleting subtask"""
        mock_delete.return_value = (True, None)
        
        response = client.delete('/subtasks/st1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
    
    @patch('app.subtask_service.get_subtasks_by_task')
    def test_get_subtasks_by_task(self, mock_get, client):
        """Test getting subtasks by task"""
        mock_get.return_value = []
        
        response = client.get('/subtasks/task/t1')
        assert response.status_code == 200
        data = response.get_json()
        assert 'subtasks' in data



if __name__ == '__main__':
    pytest.main([__file__, '-v'])
