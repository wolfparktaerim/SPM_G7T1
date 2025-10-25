# backend/comment-service/test_comment.py
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
from comment_service import CommentService
from models import CreateCommentRequest, UpdateCommentRequest, ArchiveCommentRequest
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
    with patch('comment_service.get_db_reference') as mock:
        yield mock


@pytest.fixture
def sample_comment_thread():
    """Create sample comment thread"""
    return {
        'active': True,
        'comments': [
            ['u1', 'This is a comment', 1700000000],
            ['u2', 'This is a reply', 1700000100]
        ],
        'mention': ['u1', 'u2'],
        'creation_date': 1700000000
    }


@pytest.fixture
def sample_task_data():
    """Create sample task with comment threads"""
    return {
        'taskId': 't1',
        'title': 'Test Task',
        'comment_thread': [
            {
                'active': True,
                'comments': [['u1', 'First comment', 1700000000]],
                'mention': ['u1'],
                'creation_date': 1700000000
            },
            {
                'active': True,
                'comments': [['u2', 'Second comment', 1700000100]],
                'mention': ['u2'],
                'creation_date': 1700000100
            }
        ]
    }


class TestCommentModels:
    """Test comment models"""
    
    def test_create_comment_request_from_dict(self):
        """Test creating CreateCommentRequest from dictionary"""
        data = {
            "comment": "Test comment",
            "userId": "u1",
            "creationDate": 1700000000,
            "mention": ["u2", "u3"],
            "type": "task",
            "parentId": "t1"
        }
        req = CreateCommentRequest.from_dict(data)
        
        assert req.comment == "Test comment"
        assert req.user_id == "u1"
        assert req.creation_date == 1700000000
        assert req.mention == ["u2", "u3"]
        assert req.type == "task"
        assert req.parent_id == "t1"
    
    def test_create_comment_request_validate_success(self):
        """Test validation with valid data"""
        req = CreateCommentRequest(
            comment="Test comment",
            user_id="u1",
            creation_date=1700000000,
            mention=["u2"],
            type="task",
            parent_id="t1"
        )
        errors = req.validate()
        assert len(errors) == 0
    
    def test_create_comment_request_validate_missing_comment(self):
        """Test validation with missing comment"""
        req = CreateCommentRequest(
            comment="",
            user_id="u1",
            creation_date=1700000000,
            mention=[],
            type="task",
            parent_id="t1"
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("comment" in error for error in errors)
    
    def test_create_comment_request_validate_missing_user_id(self):
        """Test validation with missing userId"""
        req = CreateCommentRequest(
            comment="Test",
            user_id="",
            creation_date=1700000000,
            mention=[],
            type="task",
            parent_id="t1"
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("userId" in error for error in errors)
    
    def test_create_comment_request_validate_invalid_type(self):
        """Test validation with invalid type"""
        req = CreateCommentRequest(
            comment="Test",
            user_id="u1",
            creation_date=1700000000,
            mention=[],
            type="invalid",
            parent_id="t1"
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("type" in error for error in errors)
    
    def test_create_comment_request_validate_invalid_mention(self):
        """Test validation with invalid mention"""
        req = CreateCommentRequest(
            comment="Test",
            user_id="u1",
            creation_date=1700000000,
            mention="not_a_list",
            type="task",
            parent_id="t1"
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("mention" in error for error in errors)
    
    def test_update_comment_request_from_dict(self):
        """Test creating UpdateCommentRequest from dictionary"""
        data = {
            "type": "task",
            "parentId": "t1",
            "threadIndex": 0,
            "comment": "Reply comment",
            "userId": "u2",
            "creationDate": 1700000100,
            "mention": ["u3"]
        }
        req = UpdateCommentRequest.from_dict(data)
        
        assert req.type == "task"
        assert req.parent_id == "t1"
        assert req.thread_index == 0
        assert req.comment == "Reply comment"
        assert req.mention == ["u3"]
    
    def test_update_comment_request_validate_success(self):
        """Test validation with valid update data"""
        req = UpdateCommentRequest(
            type="task",
            parent_id="t1",
            thread_index=0,
            comment="Reply",
            user_id="u2",
            creation_date=1700000100
        )
        errors = req.validate()
        assert len(errors) == 0
    
    def test_update_comment_request_validate_negative_index(self):
        """Test validation with negative thread index"""
        req = UpdateCommentRequest(
            type="task",
            parent_id="t1",
            thread_index=-1,
            comment="Reply",
            user_id="u2",
            creation_date=1700000100
        )
        errors = req.validate()
        assert len(errors) > 0
        assert any("threadIndex" in error for error in errors)
    
    def test_archive_comment_request_from_dict(self):
        """Test creating ArchiveCommentRequest from dictionary"""
        data = {
            "type": "subtask",
            "parentId": "st1",
            "threadIndex": 1
        }
        req = ArchiveCommentRequest.from_dict(data)
        
        assert req.type == "subtask"
        assert req.parent_id == "st1"
        assert req.thread_index == 1
    
    def test_archive_comment_request_validate_success(self):
        """Test validation with valid archive data"""
        req = ArchiveCommentRequest(
            type="task",
            parent_id="t1",
            thread_index=0,
            active=False
        )
        errors = req.validate()
        assert len(errors) == 0


class TestCommentService:
    """Test comment service class"""
    
    def test_create_comment_success(self, mock_db):
        """Test creating a comment successfully"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {
            'taskId': 't1',
            'comment_thread': []
        }
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        comment_data = {
            'comment': 'Test comment',
            'user_id': 'u1',
            'creation_date': 1700000000,
            'mention': ['u2'],
            'type': 'task',
            'parent_id': 't1'
        }
        
        thread, error = service.create_comment(comment_data)
        
        assert error is None
        assert thread['active'] == True
        assert len(thread['comments']) == 1
        assert thread['comments'][0] == ['u1', 'Test comment', 1700000000]
        assert thread['mention'] == ['u2']
        mock_task_ref.update.assert_called_once()
    
    def test_create_comment_parent_not_found(self, mock_db):
        """Test creating comment with non-existent parent"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = None
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        comment_data = {
            'comment': 'Test comment',
            'user_id': 'u1',
            'creation_date': 1700000000,
            'mention': [],
            'type': 'task',
            'parent_id': 'invalid'
        }
        
        thread, error = service.create_comment(comment_data)
        
        assert thread is None
        assert "not found" in error.lower()
    
    def test_create_comment_for_subtask(self, mock_db):
        """Test creating comment for subtask"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_subtask_ref = Mock()
        mock_subtask_ref.get.return_value = {
            'subtaskId': 'st1',
            'comment_thread': []
        }
        mock_subtasks.child.return_value = mock_subtask_ref
        
        service = CommentService()
        
        comment_data = {
            'comment': 'Subtask comment',
            'user_id': 'u1',
            'creation_date': 1700000000,
            'mention': [],
            'type': 'subtask',
            'parent_id': 'st1'
        }
        
        thread, error = service.create_comment(comment_data)
        
        assert error is None
        assert thread['active'] == True
        mock_subtask_ref.update.assert_called_once()
    
    def test_create_comment_missing_fields(self, mock_db):
        """Test creating comment with missing fields"""
        service = CommentService()
        
        comment_data = {
            'comment': 'Test',
            'user_id': 'u1'
            # Missing other required fields
        }
        
        thread, error = service.create_comment(comment_data)
        
        assert thread is None
        assert "Missing required field" in error
    
    def test_update_comment_thread_success(self, mock_db, sample_task_data):
        """Test adding reply to comment thread"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = sample_task_data
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        update_data = {
            'type': 'task',
            'parent_id': 't1',
            'thread_index': 0,
            'comment': 'This is a reply',
            'user_id': 'u2',
            'creation_date': 1700000200,
            'mention': ['u3']
        }
        
        thread, error = service.update_comment_thread(update_data)
        
        assert error is None
        assert len(thread['comments']) == 2
        assert thread['comments'][1] == ['u2', 'This is a reply', 1700000200]
        assert 'u3' in thread['mention']
        mock_task_ref.update.assert_called_once()
    
    def test_update_comment_thread_invalid_index(self, mock_db, sample_task_data):
        """Test updating with invalid thread index"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = sample_task_data
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        update_data = {
            'type': 'task',
            'parent_id': 't1',
            'thread_index': 99,  # Invalid index
            'comment': 'Reply',
            'user_id': 'u2',
            'creation_date': 1700000200
        }
        
        thread, error = service.update_comment_thread(update_data)
        
        assert thread is None
        assert "Invalid thread_index" in error
    
    def test_update_comment_thread_merge_mentions(self, mock_db, sample_task_data):
        """Test merging mentions when updating thread"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = sample_task_data
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        update_data = {
            'type': 'task',
            'parent_id': 't1',
            'thread_index': 0,
            'comment': 'Reply',
            'user_id': 'u2',
            'creation_date': 1700000200,
            'mention': ['u1', 'u3']  # u1 already exists, u3 is new
        }
        
        thread, error = service.update_comment_thread(update_data)
        
        assert error is None
        # Should contain both u1 (existing) and u3 (new)
        assert 'u1' in thread['mention']
        assert 'u3' in thread['mention']
    
    def test_archive_comment_thread_success(self, mock_db, sample_task_data):
        """Test archiving a comment thread"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = sample_task_data
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        archive_data = {
            'type': 'task',
            'parent_id': 't1',
            'thread_index': 0,
            'active': False
        }
        
        thread, error = service.archive_comment_thread(archive_data)
        
        assert error is None
        assert thread['active'] == False
        mock_task_ref.update.assert_called_once()
    
    def test_archive_comment_thread_invalid_index(self, mock_db, sample_task_data):
        """Test archiving with invalid thread index"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = sample_task_data
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        archive_data = {
            'type': 'task',
            'parent_id': 't1',
            'thread_index': 99,
            'active': False
        }
        
        thread, error = service.archive_comment_thread(archive_data)
        
        assert thread is None
        assert "Invalid thread_index" in error
    
    def test_get_comment_threads_success(self, mock_db, sample_task_data):
        """Test getting all comment threads"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = sample_task_data
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        threads, error = service.get_comment_threads('t1', 'task')
        
        assert error is None
        assert len(threads) == 2
        assert threads[0]['active'] == True
    
    def test_get_comment_threads_parent_not_found(self, mock_db):
        """Test getting threads for non-existent parent"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = None
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        threads, error = service.get_comment_threads('invalid', 'task')
        
        assert threads is None
        assert "not found" in error.lower()
    
    def test_get_comment_threads_empty(self, mock_db):
        """Test getting threads when none exist"""
        mock_tasks = Mock()
        mock_subtasks = Mock()
        mock_db.side_effect = lambda x: mock_tasks if x == "tasks" else mock_subtasks
        
        mock_task_ref = Mock()
        mock_task_ref.get.return_value = {'taskId': 't1'}  # No comment_thread
        mock_tasks.child.return_value = mock_task_ref
        
        service = CommentService()
        
        threads, error = service.get_comment_threads('t1', 'task')
        
        assert error is None
        assert threads == []


class TestCommentEndpoints:
    """Test Flask endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'comment-service'
    
    def test_create_comment_missing_body(self, client):
        """Test creating comment without body"""
        response = client.post('/comments', json=None)
        assert response.status_code == 415
    
    @patch('app.comment_service.create_comment')
    def test_create_comment_success(self, mock_create, client, sample_comment_thread):
        """Test successful comment creation"""
        mock_create.return_value = (sample_comment_thread, None)
        
        response = client.post('/comments', json={
            "comment": "Test comment",
            "userId": "u1",
            "creationDate": 1700000000,
            "mention": ["u2"],
            "type": "task",
            "parentId": "t1"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'commentThread' in data
        assert 'message' in data
    
    @patch('app.comment_service.create_comment')
    def test_create_comment_validation_error(self, mock_create, client):
        """Test creating comment with validation errors"""
        response = client.post('/comments', json={
            "comment": "",  # Empty comment
            "userId": "u1",
            "creationDate": 1700000000,
            "mention": [],
            "type": "task",
            "parentId": "t1"
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.comment_service.create_comment')
    def test_create_comment_service_error(self, mock_create, client):
        """Test creating comment with service error"""
        mock_create.return_value = (None, "Task not found")
        
        response = client.post('/comments', json={
            "comment": "Test",
            "userId": "u1",
            "creationDate": 1700000000,
            "mention": [],
            "type": "task",
            "parentId": "invalid"
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.comment_service.update_comment_thread')
    def test_update_comment_success(self, mock_update, client, sample_comment_thread):
        """Test successful comment thread update"""
        mock_update.return_value = (sample_comment_thread, None)
        
        response = client.put('/comments', json={
            "type": "task",
            "parentId": "t1",
            "threadIndex": 0,
            "comment": "Reply",
            "userId": "u2",
            "creationDate": 1700000100
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'commentThread' in data
        assert 'message' in data
    
    @patch('app.comment_service.update_comment_thread')
    def test_update_comment_validation_error(self, mock_update, client):
        """Test updating comment with validation errors"""
        response = client.put('/comments', json={
            "type": "task",
            "parentId": "t1",
            "threadIndex": -1,  # Invalid index
            "comment": "Reply",
            "userId": "u2",
            "creationDate": 1700000100
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.comment_service.archive_comment_thread')
    def test_archive_comment_success(self, mock_archive, client, sample_comment_thread):
        """Test successful comment thread archival"""
        archived_thread = sample_comment_thread.copy()
        archived_thread['active'] = False
        mock_archive.return_value = (archived_thread, None)
        
        response = client.put('/comments/archive', json={
            "type": "task",
            "parentId": "t1",
            "threadIndex": 0
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'commentThread' in data
        assert data['commentThread']['active'] == False
    
    @patch('app.comment_service.archive_comment_thread')
    def test_archive_comment_validation_error(self, mock_archive, client):
        """Test archiving comment with validation errors"""
        response = client.put('/comments/archive', json={
            "type": "invalid",  # Invalid type
            "parentId": "t1",
            "threadIndex": 0
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.comment_service.get_comment_threads')
    def test_get_comments_success(self, mock_get, client, sample_task_data):
        """Test getting comments successfully"""
        mock_get.return_value = (sample_task_data['comment_thread'], None)
        
        response = client.get('/comments/t1?type=task')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'commentThreads' in data
        assert len(data['commentThreads']) == 2
    
    @patch('app.comment_service.get_comment_threads')
    def test_get_comments_default_type(self, mock_get, client):
        """Test getting comments with default type"""
        mock_get.return_value = ([], None)
        
        response = client.get('/comments/t1')  # No type parameter
        
        assert response.status_code == 200
        mock_get.assert_called_once_with('t1', 'task')  # Should default to 'task'
    
    @patch('app.comment_service.get_comment_threads')
    def test_get_comments_invalid_type(self, mock_get, client):
        """Test getting comments with invalid type"""
        response = client.get('/comments/t1?type=invalid')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.comment_service.get_comment_threads')
    def test_get_comments_not_found(self, mock_get, client):
        """Test getting comments for non-existent parent"""
        mock_get.return_value = (None, "Task not found")
        
        response = client.get('/comments/invalid?type=task')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_create_comment_invalid_timestamp(self, client):
        """Test creating comment with invalid timestamp"""
        with patch('app.validate_epoch_timestamp', return_value=False):
            response = client.post('/comments', json={
                "comment": "Test",
                "userId": "u1",
                "creationDate": -1,  # Invalid
                "mention": [],
                "type": "task",
                "parentId": "t1"
            })
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'creationDate' in data['error']
    
    def test_create_comment_invalid_mention_type(self, client):
        """Test creating comment with invalid mention type"""
        with patch('app.validate_epoch_timestamp', return_value=True):
            response = client.post('/comments', json={
                "comment": "Test",
                "userId": "u1",
                "creationDate": 1700000000,
                "mention": "not_a_list",  # Should be array
                "type": "task",
                "parentId": "t1"
            })
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'mention' in data['error']
    
    def test_update_comment_invalid_timestamp(self, client):
        """Test updating comment with invalid timestamp"""
        with patch('app.validate_epoch_timestamp', return_value=False):
            response = client.put('/comments', json={
                "type": "task",
                "parentId": "t1",
                "threadIndex": 0,
                "comment": "Reply",
                "userId": "u2",
                "creationDate": -1  # Invalid
            })
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'creationDate' in data['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])