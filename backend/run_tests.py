# run_tests.py - Test runner script for all services

import unittest
import sys
import os
from io import StringIO
from unittest.mock import patch

def run_tests_for_service(service_name, test_module):
    """Run tests for a specific service and return results"""
    print(f"\n{'='*70}")
    print(f"Running tests for {service_name}")
    print(f"{'='*70}\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("TASK MANAGEMENT SYSTEM - UNIT TEST SUITE")
    print("="*70)
    
    results = []
    
    # Set dummy environment variables if not set
    if not os.getenv('JSON_PATH'):
        os.environ['JSON_PATH'] = 'dummy_path.json'
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'https://dummy.firebaseio.com'
    
    # Test Task Service
    try:
        task_service_path = os.path.join(os.path.dirname(__file__), 'task-service')
        sys.path.insert(0, task_service_path)
        
        # Import with Firebase mocked
        with patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.initialize_app'):
            import test_app as task_tests
            
        task_result = run_tests_for_service("Task Service", task_tests)
        results.append(("Task Service", task_result))
        
        # Remove from path to avoid conflicts
        sys.path.remove(task_service_path)
        
    except ImportError as e:
        print(f"Error importing task service tests: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Error running task service tests: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Subtask Service
    try:
        subtask_service_path = os.path.join(os.path.dirname(__file__), 'subtask-service')
        sys.path.insert(0, subtask_service_path)
        
        # Need to reload sys.modules to get fresh import
        if 'test_app' in sys.modules:
            del sys.modules['test_app']
        if 'app' in sys.modules:
            del sys.modules['app']
        
        # Import with Firebase mocked
        with patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.initialize_app'):
            import test_app as subtask_tests
            
        subtask_result = run_tests_for_service("Subtask Service", subtask_tests)
        results.append(("Subtask Service", subtask_result))
        
        # Remove from path
        sys.path.remove(subtask_service_path)
        
    except ImportError as e:
        print(f"Error importing subtask service tests: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Error running subtask service tests: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for service_name, result in results:
        tests_run = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        
        total_tests += tests_run
        total_failures += failures
        total_errors += errors
        
        status = "✓ PASSED" if (failures == 0 and errors == 0) else "✗ FAILED"
        
        print(f"\n{service_name}:")
        print(f"  Tests Run: {tests_run}")
        print(f"  Failures: {failures}")
        print(f"  Errors: {errors}")
        print(f"  Status: {status}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {total_tests} tests, {total_failures} failures, {total_errors} errors")
    print(f"{'='*70}\n")
    
    # Return exit code
    if total_failures > 0 or total_errors > 0:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())


