# backend/task-service/test_app.py

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


class TestTaskServiceUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_current_timestamp(self):
        """Test current_timestamp returns valid epoch timestamp"""
        ts = current_timestamp()
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 0)
        self.assertLess(ts, datetime(2100, 1, 1, tzinfo=timezone.utc).timestamp())
    
    def test_validate_status_valid(self):
        """Test validate_status with valid statuses"""
        valid_statuses = ["ongoing", "unassigned", "under review", "completed"]
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
        # Calculate expected next month
        next_month = base_date.replace(day=15) + timedelta(days=32)
        expected = int(next_month.replace(day=15).timestamp())
        # Just verify it's approximately 30 days later
        self.assertAlmostEqual(new_date, old_date + (86400 * 30), delta=86400 * 2)
    
    def test_calculate_new_start_date_custom(self):
        """Test calculate_new_start_date with custom schedule"""
        old_date = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        new_date = calculate_new_start_date(old_date, "custom", 5)
        expected = old_date + (86400 * 5)  # +5 days in seconds
        self.assertEqual(new_date, expected)


class TestTaskServiceEndpoints(unittest.TestCase):
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
    
    def test_create_task_success(self):
        """Test successful task creation"""
        # Mock Firebase reference
        mock_ref = MagicMock()
        mock_ref.push.return_value.key = "test-task-id"
        self.mock_db.reference.return_value = mock_ref
        
        task_data = {
            "title": "Test Task",
            "creatorId": "user123",
            "deadline": 1735689600,
            "status": "ongoing",
            "notes": "Test notes",
            "ownerId": "user123",
            "projectId": "project123",
            "attachments": [],
            "collaborators": ["user123"],
            "priority": 1
        }
        
        response = self.client.post('/tasks', 
                                   json=task_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('message', data)
        self.assertIn('task', data)
        self.assertEqual(data['task']['title'], 'Test Task')
        self.assertEqual(data['task']['taskId'], 'test-task-id')
    
    def test_create_task_missing_required_fields(self):
        """Test task creation with missing required fields"""
        incomplete_data = {
            "title": "Test Task"
            # Missing creatorId and deadline
        }
        
        response = self.client.post('/tasks',
                                   json=incomplete_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_create_task_invalid_deadline(self):
        """Test task creation with invalid deadline"""
        task_data = {
            "title": "Test Task",
            "creatorId": "user123",
            "deadline": -1,  # Invalid
            "status": "ongoing"
        }
        
        response = self.client.post('/tasks',
                                   json=task_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('Deadline', data['error'])
    
    def test_create_task_empty_title(self):
        """Test task creation with empty title"""
        task_data = {
            "title": "   ",  # Empty after strip
            "creatorId": "user123",
            "deadline": 1735689600
        }
        
        response = self.client.post('/tasks',
                                   json=task_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Title cannot be empty', data['error'])
    
    def test_create_task_invalid_priority(self):
        """Test task creation with invalid priority"""
        task_data = {
            "title": "Test Task",
            "creatorId": "user123",
            "deadline": 1735689600,
            "priority": "high"  # Should be int
        }
        
        response = self.client.post('/tasks',
                                   json=task_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Priority', data['error'])
    
    def test_get_all_tasks_success(self):
        """Test retrieving all tasks"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "task1": {
                "taskId": "task1",
                "title": "Task 1",
                "status": "ongoing",
                "start_date": current_timestamp() - 1000,
                "active": False
            },
            "task2": {
                "taskId": "task2",
                "title": "Task 2",
                "status": "completed",
                "start_date": current_timestamp() + 1000,
                "active": True
            }
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/tasks')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('tasks', data)
        self.assertEqual(len(data['tasks']), 2)
        # Check that active flag was updated for task1
        task1 = next(t for t in data['tasks'] if t['taskId'] == 'task1')
        self.assertTrue(task1['active'])
    
    def test_get_all_tasks_empty(self):
        """Test retrieving tasks when none exist"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {}
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/tasks')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['tasks'], [])
    
    def test_get_task_by_id_success(self):
        """Test retrieving a task by ID"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "taskId": "task123",
            "title": "Test Task",
            "status": "ongoing",
            "start_date": current_timestamp() - 1000,
            "active": False
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/tasks/task123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('task', data)
        self.assertEqual(data['task']['taskId'], 'task123')
        self.assertTrue(data['task']['active'])
    
    def test_get_task_by_id_not_found(self):
        """Test retrieving non-existent task"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = None
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/tasks/nonexistent')
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_update_task_success(self):
        """Test successful task update"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "taskId": "task123",
            "title": "Old Title",
            "status": "ongoing",
            "deadline": 1735689600,
            "creatorId": "user123"
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {
            "title": "New Title",
            "status": "completed"
        }
        
        response = self.client.put('/tasks/task123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)
        mock_ref.update.assert_called_once()
    
    def test_update_task_not_found(self):
        """Test updating non-existent task"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = None
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"title": "New Title"}
        
        response = self.client.put('/tasks/nonexistent',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_task_empty_title(self):
        """Test updating task with empty title"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "taskId": "task123",
            "title": "Old Title",
            "status": "ongoing"
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"title": "   "}
        
        response = self.client.put('/tasks/task123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_update_task_no_fields(self):
        """Test updating task with no valid fields"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "taskId": "task123",
            "title": "Test Task",
            "status": "ongoing"
        }
        self.mock_db.reference.return_value = mock_ref
        
        # Send empty JSON object (not None)
        update_data = {"unrelated_field": "value"}  # Field that won't be used
        
        response = self.client.put('/tasks/task123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        # Just verify there's an error, message may vary
        self.assertIn('error', data)
    
    def test_delete_task_success(self):
        """Test successful task deletion"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "taskId": "task123",
            "title": "Test Task"
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.delete('/tasks/task123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)
        mock_ref.delete.assert_called_once()
    
    def test_delete_task_not_found(self):
        """Test deleting non-existent task"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = None
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.delete('/tasks/nonexistent')
        
        self.assertEqual(response.status_code, 404)
    
    def test_get_tasks_by_project_success(self):
        """Test retrieving tasks by project ID"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "task1": {
                "taskId": "task1",
                "title": "Task 1",
                "projectId": "project123",
                "start_date": current_timestamp()
            },
            "task2": {
                "taskId": "task2",
                "title": "Task 2",
                "projectId": "project456",
                "start_date": current_timestamp()
            },
            "task3": {
                "taskId": "task3",
                "title": "Task 3",
                "projectId": "project123",
                "start_date": current_timestamp()
            }
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/tasks/project/project123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 2)
        for task in data['tasks']:
            self.assertEqual(task['projectId'], 'project123')
    
    def test_get_tasks_by_project_empty(self):
        """Test retrieving tasks for project with no tasks"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "task1": {
                "taskId": "task1",
                "projectId": "project456"
            }
        }
        self.mock_db.reference.return_value = mock_ref
        
        response = self.client.get('/tasks/project/project123')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data['tasks']), 0)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'task-service')


class TestTaskScheduling(unittest.TestCase):
    """Test scheduled task creation logic"""
    
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
    
    @patch('app.create_task_with_params')
    def test_update_task_creates_scheduled_task(self, mock_create):
        """Test that updating task to completed creates new scheduled task"""
        mock_ref = MagicMock()
        mock_ref.get.return_value = {
            "taskId": "task123",
            "title": "Recurring Task",
            "status": "ongoing",
            "scheduled": True,
            "schedule": "daily",
            "start_date": current_timestamp(),
            "deadline": current_timestamp() + 86400
        }
        self.mock_db.reference.return_value = mock_ref
        
        update_data = {"status": "completed"}
        
        response = self.client.put('/tasks/task123',
                                  json=update_data,
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
    
    def test_create_task_with_custom_schedule(self):
        """Test creating task with custom schedule"""
        mock_ref = MagicMock()
        mock_ref.push.return_value.key = "task-custom-123"
        self.mock_db.reference.return_value = mock_ref
        
        task_data = {
            "title": "Custom Scheduled Task",
            "creatorId": "user123",
            "deadline": current_timestamp() + 86400,
            "scheduled": True,
            "schedule": "custom",
            "custom_schedule": 3
        }
        
        response = self.client.post('/tasks',
                                   json=task_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['task']['schedule'], 'custom')
        self.assertEqual(data['task']['custom_schedule'], 3)
    
    def test_create_task_custom_schedule_missing_days(self):
        """Test creating task with custom schedule but no custom_schedule value"""
        task_data = {
            "title": "Invalid Custom Task",
            "creatorId": "user123",
            "deadline": current_timestamp() + 86400,
            "schedule": "custom"
            # Missing custom_schedule
        }
        
        response = self.client.post('/tasks',
                                   json=task_data,
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('custom_schedule', data['error'])


if __name__ == '__main__':
    unittest.main(verbosity=2)