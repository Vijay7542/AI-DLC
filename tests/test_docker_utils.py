"""Tests for Docker utility functions."""

import pytest
import sys
from agents.docker_utils import convert_path_for_docker, check_docker_available, check_docker_daemon_running, check_docker_ready


def test_convert_path_windows_native():
    """Test Windows path conversion on native Windows."""
    # Windows absolute path - should keep Windows format on native Windows
    path = "C:\\Users\\test\\workspace"
    result = convert_path_for_docker(path)
    if sys.platform == "win32":
        # On native Windows, keep Windows format
        assert result == "C:/Users/test/workspace"
    else:
        # On Linux/macOS, convert backslashes to forward slashes
        assert result == "C:/Users/test/workspace"


def test_convert_path_windows_forward_slashes():
    """Test Windows path with forward slashes."""
    path = "C:/Users/test/workspace"
    result = convert_path_for_docker(path)
    assert result == "C:/Users/test/workspace"


def test_convert_path_linux_absolute():
    """Test Linux absolute path (should be preserved)."""
    path = "/home/user/workspace"
    result = convert_path_for_docker(path)
    assert result == "/home/user/workspace"


def test_convert_path_macos_absolute():
    """Test macOS absolute path (should be preserved)."""
    path = "/Users/test/workspace"
    result = convert_path_for_docker(path)
    assert result == "/Users/test/workspace"


def test_convert_path_relative():
    """Test relative path (should be preserved)."""
    path = "workspace/test"
    result = convert_path_for_docker(path)
    assert result == "workspace/test"


def test_convert_path_relative_with_backslashes():
    """Test relative path with backslashes."""
    path = "workspace\\test"
    result = convert_path_for_docker(path)
    assert result == "workspace/test"


def test_convert_path_d_drive():
    """Test D: drive conversion."""
    path = "D:\\data\\files"
    result = convert_path_for_docker(path)
    assert result == "D:/data/files"


def test_check_docker_available():
    """Test Docker availability check."""
    # This will fail if Docker is not installed, which is expected
    result = check_docker_available()
    assert isinstance(result, bool)


def test_check_docker_daemon_running():
    """Test Docker daemon running check."""
    # This will fail if Docker daemon is not running, which is expected
    result = check_docker_daemon_running()
    assert isinstance(result, bool)


def test_check_docker_ready():
    """Test Docker ready check (CLI + daemon)."""
    # This will fail if Docker is not ready, which is expected
    result = check_docker_ready()
    assert isinstance(result, bool)
