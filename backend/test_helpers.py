# test_helpers.py - Helper utilities for testing

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import json

class FirebaseMockHelper:
    """Helper class for creating Firebase mocks"""
    
    @staticmethod
    def create_task_mock(task_id="task123", **kwargs):
        """Create a mock task object"""
        default_task = {
            "taskId": task_id,
            "title": "Test Task",
            "creatorId": "user123",
            "ownerId": "user123",
            "deadline": int(datetime(2025, 12, 31, tzinfo=timezone.utc).timestamp()),
            "status": "ongoing",
            "notes": "",
            "attachments": [],
            "collaborators": ["user123"],
            "projectId": "",
            "priority": 0,
            "createdAt": int(datetime.now(timezone.utc).timestamp()),
            "updatedAt": int(datetime.now(timezone.utc).timestamp()),
            "active": True,
            "scheduled": False,
            "schedule": "daily",
            "custom_schedule": None,
            "start_date": int(datetime.now(timezone.utc).timestamp())
        }
        default_task.update(kwargs)
        return default_task
    
    @staticmethod
    def create_subtask_mock(subtask_id="subtask123", task_id="task123", **kwargs):
        """Create a mock subtask object"""
        default_subtask = {
            "subTaskId": subtask_id,
            "taskId": task_id,
            "title": "Test Subtask",
            "creatorId": "user123",
            "ownerId": "user123",
            "deadline": int(datetime(2025, 12, 31, tzinfo=timezone.utc).timestamp()),
            "status": "ongoing",
            "notes": "",
            "attachments": [],
            "collaborators": ["user123"],
            "priority": 0,
            "createdAt": int(datetime.now(timezone.utc).timestamp()),
            "updatedAt": int(datetime.now(timezone.utc).timestamp()),
            "active": True,
            "scheduled": False,
            "schedule": "daily",
            "custom_schedule": None,
            "start_date": int(datetime.now(timezone.utc).timestamp())
        }
        default_subtask.update(kwargs)
        return default_subtask
    
    @staticmethod
    def create_db_mock(return_data=None):
        """Create a mock Firebase database reference"""
        mock_ref = MagicMock()
        if return_data is not None:
            mock_ref.get.return_value = return_data
        mock_ref.push.return_value.key = "mock-id-123"
        return mock_ref


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def valid_task_data(**kwargs):
        """Generate valid task creation data"""
        data = {
            "title": "Integration Test Task",
            "creatorId": "test-user-123",
            "deadline": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp()),
            "status": "ongoing",
            "notes": "Test notes",
            "projectId": "test-project-123",
            "attachments": [],
            "collaborators": ["test-user-123"],
            "priority": 1
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def valid_subtask_data(task_id="task123", **kwargs):
        """Generate valid subtask creation data"""
        data = {
            "title": "Integration Test Subtask",
            "creatorId": "test-user-123",
            "deadline": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp()),
            "taskId": task_id,
            "status": "ongoing",
            "notes": "Test subtask notes",
            "attachments": [],
            "collaborators": ["test-user-123"],
            "priority": 1
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def invalid_task_data(missing_field="deadline"):
        """Generate invalid task data for error testing"""
        data = TestDataFactory.valid_task_data()
        if missing_field in data:
            del data[missing_field]
        return data
    
    @staticmethod
    def create_scheduled_task_data(schedule_type="daily", **kwargs):
        """Generate scheduled task data"""
        data = TestDataFactory.valid_task_data()
        data.update({
            "scheduled": True,
            "schedule": schedule_type,
            "start_date": int(datetime.now(timezone.utc).timestamp())
        })
        if schedule_type == "custom":
            data["custom_schedule"] = kwargs.get("custom_schedule", 3)
        data.update(kwargs)
        return data


class AssertionHelpers:
    """Helper methods for common assertions"""
    
    @staticmethod
    def assert_valid_task_response(test_case, response_data):
        """Assert that response contains valid task data"""
        test_case.assertIn('taskId', response_data)
        test_case.assertIn('title', response_data)
        test_case.assertIn('deadline', response_data)
        test_case.assertIn('status', response_data)
        test_case.assertIn('createdAt', response_data)
        test_case.assertIn('updatedAt', response_data)
    
    @staticmethod
    def assert_valid_subtask_response(test_case, response_data):
        """Assert that response contains valid subtask data"""
        test_case.assertIn('subTaskId', response_data)
        test_case.assertIn('taskId', response_data)
        test_case.assertIn('title', response_data)
        test_case.assertIn('deadline', response_data)
        test_case.assertIn('status', response_data)
    
    @staticmethod
    def assert_error_response(test_case, response, expected_status=400):
        """Assert that response is an error with correct format"""
        test_case.assertEqual(response.status_code, expected_status)
        data = response.get_json()
        test_case.assertIn('error', data)
        test_case.assertIsInstance(data['error'], str)
        test_case.assertGreater(len(data['error']), 0)