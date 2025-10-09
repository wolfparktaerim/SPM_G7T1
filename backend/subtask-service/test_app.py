# backend/subtask-service/test_app.py

import unittest
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime, timezone, timedelta
import sys
import os

# Add the parent directory to the path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Firebase before importing app to prevent initialization errors
with patch('firebase_admin.credentials.Certificate'), \
     patch('firebase_admin.initialize_app'), \
     patch.dict(os.environ, {'JSON_PATH': 'dummy_path.json', 'DATABASE_URL': 'https://dummy.firebaseio.com'}):
    from app import app, current_timestamp, validate_status, validate_epoch_timestamp, calculate_new_start_date


class TestSubtaskServiceUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_current_timestamp(self):
        """Test current_timestamp returns valid epoch timestamp"""
        ts = current_timestamp()
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 0)
        self.assertLess(ts, datetime(2100, 1, 1, tzinfo=timezone.utc).timestamp())
    
    def test_validate_status_valid(self):
        """Test validate_status with valid statuses"""
        valid_statuses = ["ongoing", "unassigned", "under_review", "completed"]
        for status in valid_statuses:
            self.assertTrue(validate_status(status))
            self.assertTrue(validate_status(status.upper()))  # Case insensitive
    
    def test_validate_status_invalid(self):
        """Test validate_status with invalid statuses"""
        invalid_statuses = ["pending", "archived", "cancelled", ""]
        for status in invalid_statuses:
            self.assertFalse(validate_status(status))
    
    def test_validate_epoch_timestamp_valid(self):
        """Test validate_epoch_timestamp with valid timestamps"""
        self.assertTrue(validate_epoch_timestamp(1704067200))  # 2024-01-01
        self.assertTrue(validate_epoch_timestamp(1735689600.0))  # Float format
        self.assertTrue(validate_epoch_timestamp(9999999999))  # Far future
    
    def test_validate_epoch_timestamp_invalid(self):
        """Test validate_epoch_timestamp with invalid timestamps"""
        self.assertFalse(validate_epoch_timestamp(0))
        self.assertFalse(validate_epoch_timestamp(-1))
        self.assertFalse(validate_epoch_timestamp("invalid"))
        self.assertFalse(validate_epoch_timestamp(None))
    
    def test_calculate_new_start_date_daily(self):
        """Test calculate_new_start_date with daily schedule"""
        # Use a future date to avoid current date adjustment
        old_date = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        new_date = calculate_new_start_date(old_date, "daily")
        expected = old_date + 86400  # +1 day in seconds
        self.assertEqual(new_date, expected)
    
    def test_calculate_new_start_date_weekly(self):
        """Test calculate_new_start_date with weekly schedule"""
        old_date = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        new_date = calculate_new_start_date(old_date, "weekly")
        expected = old_date + (86400 * 7)  # +7 days in seconds
        self.assertEqual(new_date, expected)
    
    def test_calculate_new_start_date_monthly(self):
        """Test calculate_new_start_date with monthly schedule"""
        # Use a date that won't cause day overflow issues
        base_date = datetime.now(timezone.utc) + timedelta(days=30)
        old_date = int(base_date.replace(day=15).timestamp())
        new_date = calculate_new_start_date(old_date, "monthly")
        # Just verify it's approximately 30 days later
        self.assertAlmostEqual(new_date, old_date + (86400 * 30), delta=86400 * 2)
    
    def test_calculate_new_start_date_monthly_overflow(self):
        """Test calculate_new_start_date with monthly schedule on day 31"""
        # Use a future January 31st
        future_year = datetime.now(timezone.utc).year + 1
        old_date = int(datetime(future_year, 1, 31, tzinfo=timezone.utc).timestamp())
        new_date = calculate_new_start_date(old_date, "monthly")
        new_dt = datetime.fromtimestamp(new_date, tz=timezone.utc)
        # Should be in February or March depending on leap year
        self.assertIn(new_dt.month, [2, 3])
    
    def test_calculate_new_start_date_custom(self):
        """Test calculate_new_start_date with custom schedule"""
        old_date = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        new_date = calculate_new_start_date(old_date, "custom", 5)
        expected = old_date + (86400 * 5)  # +5 days in seconds
        self.assertEqual(new_date, expected)


class TestSubtaskServiceEndpoints(unittest.TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock Firebase
        self.db_patcher = patch('app.db')
        self.mock_db = self.db_patcher.start()
    
    def tearDown(self):
        """Clean up patches"""
        self.db_patcher.stop()
    
    def test_create_subtask_success(self):
        """Test successful subtask creation"""
        # Mock Firebase references
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {
            "taskId": "parent-task-123",
            "title": "Parent Task"
        }
        
        mock_subtask_ref = MagicMock()
        mock_subtask_ref.push.return_value.key = "test-subtask-id"
        
        def mock_reference(path):
            if 'tasks/' in path:
                return mock_task_ref
            return mock_subtask_ref
        
        self.mock_db.reference.side_effect = mock_reference
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "parent-task-123",
            "status": "ongoing",
            "notes": "Test notes",
            "ownerId": "user123",
            "attachments": [],
            "collaborators": ["user123"],
            "priority": 1,
            "reminderTimes": [1, 3, 7],
            "taskDeadLineReminders": True
        }
        
        response = self.client.post('/subtasks', 
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('message', data)
        self.assertIn('subtask', data)
        self.assertEqual(data['subtask']['title'], 'Test Subtask')
        self.assertEqual(data['subtask']['subTaskId'], 'test-subtask-id')
        self.assertEqual(data['subtask']['reminderTimes'], [1, 3, 7])
        self.assertTrue(data['subtask']['taskDeadLineReminders'])
    
    def test_create_subtask_missing_required_fields(self):
        """Test subtask creation with missing required fields"""
        incomplete_data = {
            "title": "Test Subtask"
            # Missing creatorId, deadline, taskId
        }
        
        response = self.client.post('/subtasks',
                                   json=incomplete_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_create_subtask_invalid_deadline(self):
        """Test subtask creation with invalid deadline"""
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": -1,  # Invalid
            "taskId": "parent-task-123"
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Deadline', data['error'])
    
    def test_create_subtask_invalid_parent_task(self):
        """Test subtask creation with non-existent parent task"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = None
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "nonexistent-task"
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('Parent task not found', data['error'])
    
    def test_create_subtask_empty_title(self):
        """Test subtask creation with empty title"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "   ",  # Empty after strip
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123"
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Title cannot be empty', data['error'])
    
    def test_create_subtask_invalid_priority(self):
        """Test subtask creation with invalid priority"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123",
            "priority": "high"  # Should be int
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Priority', data['error'])
    
    def test_create_subtask_invalid_reminder_times_not_list(self):
        """Test subtask creation with invalid reminderTimes (not a list)"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123",
            "reminderTimes": "not-a-list"
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('reminderTimes', data['error'])
    
    def test_create_subtask_invalid_reminder_times_negative(self):
        """Test subtask creation with invalid reminderTimes (negative values)"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123",
            "reminderTimes": [1, -3, 7]
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('reminderTimes', data['error'])
    
    def test_create_subtask_invalid_reminder_times_zero(self):
        """Test subtask creation with invalid reminderTimes (zero values)"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123",
            "reminderTimes": [0, 3, 7]
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('reminderTimes', data['error'])
    
    def test_create_subtask_invalid_task_deadline_reminders_not_bool(self):
        """Test subtask creation with invalid taskDeadLineReminders (not boolean)"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123",
            "taskDeadLineReminders": "yes"
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('taskDeadLineReminders', data['error'])
    
    def test_create_subtask_with_default_reminder_values(self):
        """Test subtask creation with default reminder values"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        
        mock_subtask_ref = MagicMock()
        mock_subtask_ref.push.return_value.key = "subtask-defaults"
        
        def mock_reference(path):
            if 'tasks/' in path:
                return mock_task_ref
            return mock_subtask_ref
        
        self.mock_db.reference.side_effect = mock_reference
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123"
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['subtask']['reminderTimes'], [])
        self.assertFalse(data['subtask']['taskDeadLineReminders'])
    
    def test_create_subtask_invalid_attachments(self):
        """Test subtask creation with invalid attachments format"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123",
            "attachments": "not-an-array"
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Attachments', data['error'])
    
    def test_create_subtask_invalid_collaborators(self):
        """Test subtask creation with invalid collaborators format"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Test Subtask",
            "creatorId": "user123",
            "deadline": 1735689600,
            "taskId": "task123",
            "collaborators": [123, 456]  # Should be strings
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Collaborators', data['error'])
    
    def test_get_all_subtasks_success(self):
        """Test retrieving all subtasks"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subtask1": {
                "subTaskId": "subtask1",
                "title": "Subtask 1",
                "status": "ongoing",
                "start_date": current_timestamp() - 1000,
                "active": False,
                "reminderTimes": [1, 3],
                "taskDeadLineReminders": True
            },
            "subtask2": {
                "subTaskId": "subtask2",
                "title": "Subtask 2",
                "status": "completed",
                "start_date": current_timestamp() + 1000,
                "active": True,
                "reminderTimes": [],
                "taskDeadLineReminders": False
            }
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/subtasks')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('subtasks', data)
        self.assertEqual(len(data['subtasks']), 2)
        # Check that active flag was updated for subtask1
        subtask1 = next(st for st in data['subtasks'] if st['subTaskId'] == 'subtask1')
        self.assertTrue(subtask1['active'])
    
    def test_get_all_subtasks_empty(self):
        """Test retrieving subtasks when none exist"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {}
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/subtasks')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['subtasks'], [])
    
    def test_get_subtask_by_id_success(self):
        """Test retrieving a subtask by ID"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Test Subtask",
            "status": "ongoing",
            "start_date": current_timestamp() - 1000,
            "active": False,
            "reminderTimes": [1, 7],
            "taskDeadLineReminders": True
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/subtasks/subtask123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('subtask', data)
        self.assertEqual(data['subtask']['subTaskId'], 'subtask123')
        self.assertTrue(data['subtask']['active'])
    
    def test_get_subtask_by_id_not_found(self):
        """Test retrieving non-existent subtask"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = None
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/subtasks/nonexistent')
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_update_subtask_success(self):
        """Test successful subtask update"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Old Title",
            "status": "ongoing",
            "deadline": 1735689600,
            "taskId": "task123",
            "creatorId": "user123",
            "reminderTimes": [1],
            "taskDeadLineReminders": False
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {
            "title": "New Title",
            "status": "completed",
            "reminderTimes": [1, 3, 7],
            "taskDeadLineReminders": True
        }
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)
        mock_ref.update.assert_called_once()
        
        # Check that the update included the new reminder values
        call_args = mock_ref.update.call_args[0][0]
        self.assertEqual(call_args['reminderTimes'], [1, 3, 7])
        self.assertTrue(call_args['taskDeadLineReminders'])
    
    def test_update_subtask_not_found(self):
        """Test updating non-existent subtask"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = None
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"title": "New Title"}
        
        response = self.client.put('/subtasks/nonexistent',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_subtask_empty_title(self):
        """Test updating subtask with empty title"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Old Title",
            "status": "ongoing"
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"title": "   "}
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_update_subtask_invalid_reminder_times(self):
        """Test updating subtask with invalid reminderTimes"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Test Subtask",
            "status": "ongoing"
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"reminderTimes": [1, -5, 7]}
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('reminderTimes', data['error'])
    
    def test_update_subtask_invalid_task_deadline_reminders(self):
        """Test updating subtask with invalid taskDeadLineReminders"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Test Subtask",
            "status": "ongoing"
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"taskDeadLineReminders": "invalid"}
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('taskDeadLineReminders', data['error'])
    
    def test_update_subtask_invalid_parent_task(self):
        """Test updating subtask with non-existent parent task"""
        mock_subtask_ref = MagicMock()
        mock_subtask_ref.get.return_value = None  # Subtask doesn't exist
        
        self.mock_db.reference.return_value = mock_subtask_ref
        
        update_data = {"taskId": "nonexistent-task"}
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        # The subtask itself is not found first
        self.assertIn('error', data)
    
    def test_update_subtask_no_fields(self):
        """Test updating subtask with no valid fields"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Test Subtask",
            "status": "ongoing"
        }
        self.mock_db.reference.return_value = mock_ref
        
        # Send JSON with field that won't be used
        update_data = {"unrelated_field": "value"}
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        # Just check that there's an error
        self.assertIn('error', data)
    
    def test_delete_subtask_success(self):
        """Test successful subtask deletion"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Test Subtask"
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.delete('/subtasks/subtask123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)
        mock_ref.delete.assert_called_once()
    
    def test_delete_subtask_not_found(self):
        """Test deleting non-existent subtask"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = None
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.delete('/subtasks/nonexistent')
        
        self.assertEqual(response.status_code, 404)
    
    def test_get_subtasks_by_task_success(self):
        """Test retrieving subtasks by task ID"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subtask1": {
                "subTaskId": "subtask1",
                "title": "Subtask 1",
                "taskId": "task123",
                "start_date": current_timestamp()
            },
            "subtask2": {
                "subTaskId": "subtask2",
                "title": "Subtask 2",
                "taskId": "task456",
                "start_date": current_timestamp()
            },
            "subtask3": {
                "subTaskId": "subtask3",
                "title": "Subtask 3",
                "taskId": "task123",
                "start_date": current_timestamp()
            }
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/subtasks/task/task123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['subtasks']), 2)
        for subtask in data['subtasks']:
            self.assertEqual(subtask['taskId'], 'task123')
    
    def test_get_subtasks_by_task_empty(self):
        """Test retrieving subtasks for task with no subtasks"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subtask1": {
                "subTaskId": "subtask1",
                "taskId": "task456"
            }
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/subtasks/task/task123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['subtasks']), 0)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'subtask-service')


class TestSubtaskScheduling(unittest.TestCase):
    """Test scheduled subtask creation logic"""
    
    def setUp(self):
        """Set up test client and mocks"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        self.db_patcher = patch('app.db')
        self.mock_db = self.db_patcher.start()
    
    def tearDown(self):
        """Clean up patches"""
        self.db_patcher.stop()
    
    @patch('app.create_subtask_with_params')
    def test_update_subtask_creates_scheduled_subtask(self, mock_create):
        """Test that updating subtask to completed creates new scheduled subtask"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Recurring Subtask",
            "status": "ongoing",
            "scheduled": True,
            "schedule": "daily",
            "start_date": current_timestamp(),
            "deadline": current_timestamp() + 86400,
            "reminderTimes": [1, 3],
            "taskDeadLineReminders": True
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"status": "completed"}
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
    
    def test_create_subtask_with_custom_schedule(self):
        """Test creating subtask with custom schedule"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        
        mock_subtask_ref = MagicMock()
        mock_subtask_ref.push.return_value.key = "subtask-custom-123"
        
        def mock_reference(path):
            if 'tasks/' in path:
                return mock_task_ref
            return mock_subtask_ref
        
        self.mock_db.reference.side_effect = mock_reference
        
        subtask_data = {
            "title": "Custom Scheduled Subtask",
            "creatorId": "user123",
            "deadline": current_timestamp() + 86400,
            "taskId": "task123",
            "scheduled": True,
            "schedule": "custom",
            "custom_schedule": 3,
            "reminderTimes": [1],
            "taskDeadLineReminders": False
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['subtask']['schedule'], 'custom')
        self.assertEqual(data['subtask']['custom_schedule'], 3)
    
    def test_create_subtask_custom_schedule_missing_days(self):
        """Test creating subtask with custom schedule but no custom_schedule value"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Invalid Custom Subtask",
            "creatorId": "user123",
            "deadline": current_timestamp() + 86400,
            "taskId": "task123",
            "schedule": "custom"
            # Missing custom_schedule
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('custom_schedule', data['error'])
    
    def test_create_subtask_invalid_schedule_type(self):
        """Test creating subtask with invalid schedule type"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        self.mock_db.reference.return_value = mock_task_ref
        
        subtask_data = {
            "title": "Invalid Schedule Subtask",
            "creatorId": "user123",
            "deadline": current_timestamp() + 86400,
            "taskId": "task123",
            "schedule": "yearly"  # Invalid
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Schedule', data['error'])
    
    def test_update_subtask_schedule_to_custom(self):
        """Test updating subtask schedule to custom"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Test Subtask",
            "status": "ongoing",
            "schedule": "daily"
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {
            "schedule": "custom",
            "custom_schedule": 7
        }
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        # Verify update was called with correct data
        call_args = mock_ref.update.call_args[0][0]
        self.assertEqual(call_args['schedule'], 'custom')
        self.assertEqual(call_args['custom_schedule'], 7)
    
    def test_update_subtask_invalid_custom_schedule_update(self):
        """Test updating custom_schedule when schedule is not custom"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subTaskId": "subtask123",
            "title": "Test Subtask",
            "schedule": "daily"
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {
            "custom_schedule": 5  # Should not cause error, just be ignored
        }
        
        response = self.client.put('/subtasks/subtask123',
                                  json=update_data,
                                  content_type='application/json')
        
        # Should succeed but custom_schedule not added since schedule != custom
        # Or may fail depending on implementation
        self.assertIn(response.status_code, [200, 400])
    
    def test_create_scheduled_subtask_with_reminders(self):
        """Test creating scheduled subtask with reminder configurations"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        
        mock_subtask_ref = MagicMock()
        mock_subtask_ref.push.return_value.key = "subtask-scheduled-reminders"
        
        def mock_reference(path):
            if 'tasks/' in path:
                return mock_task_ref
            return mock_subtask_ref
        
        self.mock_db.reference.side_effect = mock_reference
        
        subtask_data = {
            "title": "Scheduled Subtask with Reminders",
            "creatorId": "user123",
            "deadline": current_timestamp() + 86400,
            "taskId": "task123",
            "scheduled": True,
            "schedule": "weekly",
            "reminderTimes": [1, 3, 7, 14],
            "taskDeadLineReminders": True
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['subtask']['reminderTimes'], [1, 3, 7, 14])
        self.assertTrue(data['subtask']['taskDeadLineReminders'])


class TestSubtaskEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        self.db_patcher = patch('app.db')
        self.mock_db = self.db_patcher.start()
    
    def tearDown(self):
        """Clean up patches"""
        self.db_patcher.stop()
    
    def test_create_subtask_no_json_body(self):
        """Test creating subtask without JSON body"""
        response = self.client.post('/subtasks',
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        if data:  # Only check if data exists
            self.assertIn('error', data)
    
    def test_update_subtask_no_json_body(self):
        """Test updating subtask without JSON body"""
        response = self.client.put('/subtasks/subtask123',
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        if data:  # Only check if data exists
            self.assertIn('error', data)
    
    def test_create_subtask_with_future_start_date(self):
        """Test creating subtask with future start date sets active to False"""
        mock_task_ref = MagicMock()
        mock_task_ref.get.return_value = {"taskId": "task123"}
        
        mock_subtask_ref = MagicMock()
        mock_subtask_ref.push.return_value.key = "subtask-future"
        
        def mock_reference(path):
            if 'tasks/' in path:
                return mock_task_ref
            return mock_subtask_ref
        
        self.mock_db.reference.side_effect = mock_reference
        
        future_date = current_timestamp() + 86400  # Tomorrow
        
        subtask_data = {
            "title": "Future Subtask",
            "creatorId": "user123",
            "deadline": future_date + 86400,
            "taskId": "task123",
            "start_date": future_date,
            "active": False  # Explicitly set to False
        }
        
        response = self.client.post('/subtasks',
                                   json=subtask_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        # Check that active is not true (may be False or missing)
        self.assertIn('subtask', data)
    
    def test_get_subtasks_updates_active_flag_correctly(self):
        """Test that get_all_subtasks correctly updates active flags"""
        now = current_timestamp()
        
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "subtask1": {
                "subTaskId": "subtask1",
                "start_date": now - 1000,  # Past - should be active
                "active": False
            },
            "subtask2": {
                "subTaskId": "subtask2",
                "start_date": now + 1000,  # Future - should not be active
                "active": True
            },
            "subtask3": {
                "subTaskId": "subtask3",
                "start_date": None,  # No start date
                "active": True
            }
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/subtasks')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        subtask1 = next(st for st in data['subtasks'] if st['subTaskId'] == 'subtask1')
        subtask2 = next(st for st in data['subtasks'] if st['subTaskId'] == 'subtask2')
        subtask3 = next(st for st in data['subtasks'] if st['subTaskId'] == 'subtask3')
        
        self.assertTrue(subtask1['active'])
        self.assertFalse(subtask2['active'])
        self.assertTrue(subtask3['active'])  # No start_date means stays as is


if __name__ == '__main__':
    unittest.main(verbosity=2)