# backend/run_all_tests.py
"""
Central test runner for all microservices
Run with: python run_all_tests.py
"""
import subprocess
import sys
from pathlib import Path
import time
import io

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print('='*70)

def print_subheader(text):
    """Print a formatted subheader"""
    print(f"\n{'-'*70}")
    print(f"  {text}")
    print('-'*70)

def run_tests_for_service(service_path):
    """Run tests for a specific service in Docker container"""
    service_name = service_path.name
    test_file = None

    # Determine test file name
    if service_name == "email-service":
        test_file = "test_email.py"
    elif service_name == "notification-service":
        test_file = "test_notification.py"
    elif service_name == "project-service":
        test_file = "test_project.py"
    elif service_name == "task-service":
        test_file = "test_task.py"
    elif service_name == "subtask-service":
        test_file = "test_subtask.py"
    elif service_name == "comment-service":
        test_file = "test_comment.py"
    elif service_name == 'extension-request-service':
        test_file = "test_extension_request.py"
    else:
        print(f"Warning: Unknown service {service_name}")
        return False

    test_path = service_path / test_file

    if not test_path.exists():
        print(f"⚠️  Test file not found: {test_path}")
        return False

    print_subheader(f"Testing {service_name}")
    print(f"📁 Path: {service_path}")
    print(f"📄 Test file: {test_file}\n")

    start_time = time.time()

    # Get container name
    container_name = f"backend-{service_name}-1"

    try:
        # Check if container is running
        check_result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )

        if container_name not in check_result.stdout:
            print(f"⚠️  Container {container_name} is not running. Skipping tests.")
            print(f"   Run 'docker-compose up -d {service_name}' to start the container.")
            return False

        # Run tests in Docker container (use relative path to avoid Git Bash path conversion)
        result = subprocess.run(
            ['docker', 'exec', container_name, 'pytest', test_file, '-v', '--tb=short'],
            capture_output=False,
            text=True
        )

        elapsed_time = time.time() - start_time

        if result.returncode == 0:
            print(f"\n✅ {service_name} tests PASSED ({elapsed_time:.2f}s)")
            return True
        else:
            print(f"\n❌ {service_name} tests FAILED ({elapsed_time:.2f}s)")
            return False

    except FileNotFoundError:
        print(f"\n⚠️  Docker not found. Please install Docker Desktop")
        return False
    except Exception as e:
        print(f"\n❌ Error running tests for {service_name}: {str(e)}")
        return False

def main():
    """Main test runner"""
    print_header("🧪 Running All Microservice Tests")
    
    services = [
        'email-service',
        'notification-service',
        'project-service',
        'task-service',
        'subtask-service',
        'comment-service',
        'extension-request-service'
    ]
    
    root = Path(__file__).parent
    results = {}
    
    total_start_time = time.time()
    
    # Run tests for each service
    for service in services:
        service_path = root / service
        if service_path.exists():
            results[service] = run_tests_for_service(service_path)
        else:
            print(f"\n⚠️  Service directory not found: {service_path}")
            results[service] = False
    
    total_elapsed_time = time.time() - total_start_time
    
    # Print summary
    print_header("📊 Test Summary")
    
    passed_count = sum(1 for result in results.values() if result)
    failed_count = len(results) - passed_count
    
    for service, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {service:30} {status}")
    
    print(f"\n{'='*70}")
    print(f"  Total: {len(results)} services")
    print(f"  Passed: {passed_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Time: {total_elapsed_time:.2f}s")
    print('='*70)
    
    # Exit with appropriate code
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! ✨")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        sys.exit(1)

if __name__ == '__main__':
    main()

