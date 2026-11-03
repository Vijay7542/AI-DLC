"""Docker utility functions for path conversion and connectivity checks.

Provides cross-platform compatibility for Docker operations on Windows, Linux, and macOS.
"""

import os
import sys
import subprocess
from typing import Optional


def _is_running_on_windows() -> bool:
    """Check if Python is running on Windows (not WSL).

    Returns:
        True if running on native Windows, False if on Linux/macOS/WSL
    """
    return sys.platform == "win32"


def convert_path_for_docker(path: str) -> str:
    """Convert a local path to Docker-compatible format.

    Platform-aware conversion:
    - Windows (native): Converts backslashes to forward slashes, keeps Windows format (C:/path)
    - Linux/macOS/WSL: Keeps paths as-is or converts to WSL format if needed

    Docker Desktop with WSL 2 backend handles Windows path translation internally
    when invoked from Windows CMD/PowerShell.

    Args:
        path: Local file system path

    Returns:
        Docker-compatible path string

    Examples:
        Windows (native): "C:\\Users\\test\\workspace" → "C:/Users/test/workspace"
        Linux/WSL: "/home/user/workspace" → "/home/user/workspace"
        macOS: "/Users/test/workspace" → "/Users/test/workspace"
    """
    # Convert backslashes to forward slashes (Docker prefers forward slashes)
    path = path.replace("\\", "/")

    # If running on native Windows, keep Windows format (C:/path)
    # Docker Desktop handles the translation to WSL format internally
    if _is_running_on_windows():
        return path

    # If running on Linux/macOS/WSL, keep paths as-is
    return path


def check_docker_available() -> bool:
    """Check if Docker CLI is available in PATH.

    Returns:
        True if docker command is available
    """
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_docker_daemon_running() -> bool:
    """Check if Docker daemon is running and responsive.

    Uses 'docker info' to verify daemon connectivity, not just CLI availability.

    Returns:
        True if Docker daemon is running and responsive
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_docker_ready() -> bool:
    """Check if Docker is fully ready (CLI available and daemon running).

    Returns:
        True if Docker is ready for operations
    """
    return check_docker_available() and check_docker_daemon_running()
