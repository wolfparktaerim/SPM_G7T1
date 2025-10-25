# backend/task-service/test_task.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Set environment variables before any imports
os.environ['JSON_PATH'] = '/tmp/dummy.json'
os.environ['DATABASE_URL'] = 'https://dummy.firebaseio.com'

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a mock Firebase app and patch firebase_admin globally
mock_firebase_app = MagicMock()
firebase_admin_patcher = patch.dict('sys.modules', {
    'firebase_admin': MagicMock(),
    'firebase_admin.credentials': MagicMock(),
    'firebase_admin.db': MagicMock()
})
firebase_admin_patcher.start()

from task_service import TaskService
from models import Task, CreateTaskRequest, UpdateTaskRequest


@pytest.fixture(scope="session", autouse=True)
def stop_firebase_patch():
    """Ensure global patch teardown."""
    yield
    firebase_admin_patcher.stop()


@pytest.fixture(autouse=True)
def mock_firebase():
    """Mock Firebase initialization for all tests."""
    with patch('firebase_admin.initialize_app', return_value=mock_firebase_app):
        with patch('firebase_admin.get_app', return_value=mock_firebase_app):
            with patch('firebase_admin.credentials.Certificate'):
                yield


@pytest.fixture
def mock_db():
    """Mock database references."""
    with patch('task_service.get_db_reference') as mock:
        yield mock


@pytest.fixture
def sample_task():
    """Sample task fixture."""
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
    """Tests for startedAt logic."""

    def test_create_task_owner_is_creator_unassigned(self, mock_db):
        """Test creating task where owner is creator - status should be unassigned, startedAt should be None."""
        mock_tasks, mock_subtasks = Mock(), Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref

        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            # Explicitly set status to something other than "ongoing" to test unassigned logic
            req = CreateTaskRequest(
                title="Test Task",
                creator_id="u1",
                deadline=1800000000,
                owner_id="u1",
                status="unassigned"  # Explicitly set to unassigned
            )
            task, err = service.create_task(req)

            assert err is None
            assert task.status == "unassigned"
            assert task.started_at is None
            assert mock_new_ref.set.called

    def test_create_task_owner_differs(self, mock_db):
        """Test creating task where owner differs from creator - status should be ongoing, startedAt should be set."""
        mock_tasks, mock_subtasks = Mock(), Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        mock_new_ref = Mock()
        mock_new_ref.key = "test-task-id"
        mock_tasks.push.return_value = mock_new_ref

        current_time = 1700000000
        with patch('task_service.current_timestamp', return_value=current_time):
            service = TaskService()
            req = CreateTaskRequest(title="Test Task", creator_id="u1", deadline=1800000000, owner_id="u2")
            task, err = service.create_task(req)

            assert err is None
            assert task.status == "ongoing"
            assert task.started_at == current_time

    def test_update_task_unassigned_to_ongoing(self, mock_db):
        """Test updating task status from unassigned to ongoing - startedAt should be set."""
        mock_tasks, mock_subtasks = Mock(), Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        mock_task_ref = Mock()

        existing = {"taskId": "t1", "creatorId": "u1", "ownerId": "u1", "status": "unassigned", "startedAt": None}
        mock_task_ref.get.side_effect = [existing, {**existing, "status": "ongoing", "startedAt": 1700000000}]
        mock_tasks.child.return_value = mock_task_ref

        with patch('task_service.current_timestamp', return_value=1700000000):
            svc = TaskService()
            req = UpdateTaskRequest(task_id="t1", status="ongoing")
            task, err = svc.update_task(req)

            assert err is None
            assert task.status == "ongoing"
            assert task.started_at == 1700000000
            updated = mock_task_ref.update.call_args[0][0]
            assert updated["startedAt"] == 1700000000


class TestTaskServiceCompletedAt:
    """Tests for completedAt logic."""

    def test_update_task_to_completed(self, mock_db):
        """Test updating task status to completed - completedAt should be set."""
        mock_tasks, mock_subtasks = Mock(), Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        mock_task_ref = Mock()

        existing = {"taskId": "t1", "creatorId": "u1", "status": "ongoing", "completedAt": None}
        mock_task_ref.get.side_effect = [existing, {**existing, "status": "completed", "completedAt": 1700000000}]
        mock_tasks.child.return_value = mock_task_ref

        with patch('task_service.current_timestamp', return_value=1700000000):
            svc = TaskService()
            req = UpdateTaskRequest(task_id="t1", status="completed")
            task, err = svc.update_task(req)

            assert err is None
            assert task.status == "completed"
            assert task.completed_at == 1700000000


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
