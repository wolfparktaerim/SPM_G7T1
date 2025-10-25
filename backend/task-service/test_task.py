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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
