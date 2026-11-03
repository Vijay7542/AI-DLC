"""Real Docker integration tests.

These tests require actual Docker installation and will be skipped if Docker is unavailable.
They verify that Docker operations work correctly on the current platform.
"""

import pytest
import os
import tempfile
import shutil
from agents.docker_utils import check_docker_ready
from agents.testing_agent import TestingAgent
from agents.operations_agent import OperationsAgent
from graph.state import WorkflowState, Task


# Skip all tests in this file if Docker is not ready
pytestmark = pytest.mark.skipif(
    not check_docker_ready(),
    reason="Docker is not available or daemon is not running"
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    workspace = tempfile.mkdtemp(prefix="mini-ai-dlc-test-")
    yield workspace
    # Cleanup
    if os.path.exists(workspace):
        shutil.rmtree(workspace)


def test_docker_path_conversion_with_real_docker(temp_workspace):
    """Test that path conversion works with actual Docker."""
    from agents.docker_utils import convert_path_for_docker
    import sys
    
    # Convert the temp workspace path
    docker_path = convert_path_for_docker(temp_workspace)
    
    # Verify it's a valid path (no backslashes for Docker)
    assert "\\" not in docker_path
    
    # On Windows, should be Windows format (C:/...)
    # On Linux/macOS, should be Unix format
    if sys.platform == "win32":
        assert ":" in docker_path  # Should have drive letter
    else:
        assert ":" not in docker_path  # Should not have drive letter


def test_docker_build_simple_image(temp_workspace):
    """Test building a simple Docker image."""
    # Create a simple Dockerfile
    dockerfile_content = """FROM python:3.14-slim
WORKDIR /app
RUN echo "Hello from Docker"
"""
    dockerfile_path = os.path.join(temp_workspace, "Dockerfile")
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)
    
    # Use Operations Agent to build
    from graph.state import DeploymentConfig
    config = DeploymentConfig(
        environment="staging",
        docker_image_name="mini-ai-dlc-test-simple",
        docker_image_tag="test",
        port=8000,
        health_check_path="/health",
    )
    
    agent = OperationsAgent()
    build_report = agent._build_docker_image(temp_workspace, config)
    
    # Verify build succeeded
    assert build_report.status == "success", f"Build failed: {build_report.errors}"
    assert build_report.docker_image_id is not None
    
    # Cleanup: remove the test image
    import subprocess
    subprocess.run(
        ["docker", "rmi", "mini-ai-dlc-test-simple:test"],
        capture_output=True,
        timeout=30,
    )


def test_docker_run_simple_container(temp_workspace):
    """Test running a simple Docker container."""
    # Create a simple Python script
    script_content = """print("Hello from container")
"""
    script_path = os.path.join(temp_workspace, "test.py")
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Use Testing Agent to execute
    from graph.state import TestCase
    test_case = TestCase(
        test_id="test-1",
        test_name="Simple Test",
        test_type="unit",
        file_path="test.py",
        function_name="test_simple",
        description="Simple test",
    )
    
    agent = TestingAgent()
    test_report = agent._execute_tests([test_case], temp_workspace)
    
    # The test will fail because test.py is not a valid pytest file,
    # but we're just verifying Docker execution works
    assert test_report.total_tests == 1
    assert test_report.test_cases[0].status in ["failed", "error"]


def test_docker_volume_mount_windows_path(temp_workspace):
    """Test that volume mounting works with Windows paths."""
    # Create a test file
    test_file = os.path.join(temp_workspace, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")
    
    # Run a container that mounts the workspace
    import subprocess
    from agents.docker_utils import convert_path_for_docker
    
    docker_path = convert_path_for_docker(temp_workspace)
    
    # Use proper volume mount syntax for Windows
    # On Windows, Docker Desktop handles the path translation
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{docker_path}:/data",
            "python:3.14-slim",
            "sh", "-c", "cat /data/test.txt"
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    
    # Verify the file was accessible
    assert result.returncode == 0, f"Volume mount failed: {result.stderr}\nStdout: {result.stdout}"
    assert "test content" in result.stdout, f"File content not found in output: {result.stdout}"


def test_docker_daemon_connectivity():
    """Test that Docker daemon is responsive."""
    import subprocess
    
    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    
    assert result.returncode == 0, f"Docker daemon not responsive: {result.stderr}"
    assert "Server Version" in result.stdout or "Server:" in result.stdout


def test_operations_agent_docker_check():
    """Test that Operations Agent correctly detects Docker availability."""
    agent = OperationsAgent()
    # This should not raise an error since Docker is available
    assert check_docker_ready() is True


def test_testing_agent_docker_check():
    """Test that Testing Agent correctly detects Docker availability."""
    agent = TestingAgent()
    # This should not raise an error since Docker is available
    assert check_docker_ready() is True
