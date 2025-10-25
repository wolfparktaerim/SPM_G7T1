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
import re

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print('='*80)

def print_subheader(text):
    """Print a formatted subheader"""
    print(f"\n{'-'*80}")
    print(f"  {text}")
    print('-'*80)

def extract_coverage(output):
    """Extract coverage percentage from pytest output"""
    # Look for pattern like "TOTAL  1043  119  89%"
    match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
    if match:
        return int(match.group(1))
    return None

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
        return False, None

    test_path = service_path / test_file

    if not test_path.exists():
        print(f"⚠️  Test file not found: {test_path}")
        return False, None

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
            return False, None

        # Get all Python modules in the service directory (excluding __pycache__, shared, etc.)
        # We need to get the list from inside the container
        list_result = subprocess.run(
            ['docker', 'exec', container_name, 'sh', '-c',
             'ls -1 *.py 2>/dev/null | grep -v __pycache__ | sed "s/.py$//"'],
            capture_output=True,
            text=True
        )

        # Build coverage arguments for all Python files in the service
        modules = list_result.stdout.strip().split('\n') if list_result.stdout.strip() else []
        cov_args = []
        for module in modules:
            if module:  # Skip empty lines
                cov_args.extend(['--cov', module])

        # Run tests in Docker container with coverage on all service files
        result = subprocess.run(
            ['docker', 'exec', container_name, 'pytest', test_file] + cov_args +
            ['--cov-report=term', '-v', '--tb=short'],
            capture_output=True,
            text=True
        )

        # Print the output
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        elapsed_time = time.time() - start_time

        # Extract coverage
        coverage = extract_coverage(result.stdout)

        if result.returncode == 0:
            print(f"\n✅ {service_name} tests PASSED ({elapsed_time:.2f}s)")
            return True, coverage
        else:
            print(f"\n❌ {service_name} tests FAILED ({elapsed_time:.2f}s)")
            return False, coverage

    except FileNotFoundError:
        print(f"\n⚠️  Docker not found. Please install Docker Desktop")
        return False, None
    except Exception as e:
        print(f"\n❌ Error running tests for {service_name}: {str(e)}")
        return False, None

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
            results[service] = (False, None)

    total_elapsed_time = time.time() - total_start_time

    # Print summary
    print_header("📊 Test Summary")

    passed_count = sum(1 for passed, _ in results.values() if passed)
    failed_count = len(results) - passed_count

    # Print table header
    print(f"  {'Service':<35} {'Status':<15} {'Coverage':<10}")
    print(f"  {'-'*35} {'-'*15} {'-'*10}")

    for service, (passed, coverage) in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        cov_str = f"{coverage}%" if coverage is not None else "N/A"
        print(f"  {service:<35} {status:<15} {cov_str:<10}")

    print(f"\n{'='*80}")
    print(f"  Total: {len(results)} services")
    print(f"  Passed: {passed_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Time: {total_elapsed_time:.2f}s")

    # Calculate average coverage
    coverages = [cov for _, cov in results.values() if cov is not None]
    if coverages:
        avg_coverage = sum(coverages) / len(coverages)
        print(f"  Average Coverage: {avg_coverage:.1f}%")

    print('='*80)

    # Exit with appropriate code
    all_passed = all(passed for passed, _ in results.values())

    if all_passed:
        print("\n🎉 All tests passed! ✨")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
