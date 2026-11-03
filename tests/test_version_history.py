"""Tests for persistent version history and rollback functionality."""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from agents.version_manager import VersionManager
from agents.construction_agent import ConstructionAgent
from agents.testing_agent import TestingAgent
from graph.state import BugReport


@pytest.fixture
def version_db():
    """Provide a temporary version database."""
    path = tempfile.mktemp(suffix=".db", prefix="test_version_")
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def workspace():
    """Provide a temporary workspace directory."""
    path = tempfile.mkdtemp(prefix="test_workspace_")
    yield path
    # Cleanup
    if os.path.exists(path):
        shutil.rmtree(path)


def test_version_manager_saves_version(version_db):
    """Test that VersionManager can save file versions."""
    manager = VersionManager(version_db)

    version_id = manager.save_version(
        file_path="app.py",
        content="def hello():\n    return 'world'",
        version=1,
        generated_by="task-1",
        description="Initial version",
        syntax_valid=True,
    )

    assert version_id is not None
    assert version_id > 0


def test_version_manager_retrieves_version(version_db):
    """Test that VersionManager can retrieve a specific version."""
    manager = VersionManager(version_db)

    manager.save_version(
        file_path="app.py",
        content="def hello():\n    return 'world'",
        version=1,
        generated_by="task-1",
        description="Initial version",
    )

    version = manager.get_version("app.py", 1)

    assert version is not None
    assert version.version == 1
    assert version.content == "def hello():\n    return 'world'"
    assert version.generated_by == "task-1"


def test_version_manager_retrieves_latest_version(version_db):
    """Test that VersionManager can retrieve the latest version."""
    manager = VersionManager(version_db)

    manager.save_version("app.py", "v1", 1, "task-1", "Version 1")
    manager.save_version("app.py", "v2", 2, "task-2", "Version 2")

    latest = manager.get_latest_version("app.py")

    assert latest is not None
    assert latest.version == 2
    assert latest.content == "v2"


def test_version_manager_tracks_working_version(version_db):
    """Test that VersionManager can track working versions."""
    manager = VersionManager(version_db)

    manager.save_version("app.py", "v1", 1, "task-1", "Version 1")
    manager.save_version("app.py", "v2", 2, "task-2", "Version 2")

    # Mark version 1 as working
    manager.mark_as_working("app.py", 1)

    working = manager.get_working_version("app.py")

    assert working is not None
    assert working.version == 1
    assert working.content == "v1"


def test_version_manager_records_rollback(version_db):
    """Test that VersionManager records rollback events."""
    manager = VersionManager(version_db)

    manager.save_version("app.py", "v1", 1, "task-1", "Version 1")
    manager.save_version("app.py", "v2", 2, "task-2", "Version 2")

    manager.record_rollback("app.py", 2, 1, "Tests failed")

    history = manager.get_rollback_history("app.py")

    assert len(history) == 1
    assert history[0]["from_version"] == 2
    assert history[0]["to_version"] == 1
    assert history[0]["reason"] == "Tests failed"


def test_construction_agent_saves_to_version_db(workspace, version_db):
    """Test that Construction Agent saves versions to database."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="def hello():\n    return 'world'")

    agent = ConstructionAgent(llm=mock_llm, workspace_root=workspace, version_db=version_db)

    # Create a file
    file_path = os.path.join(workspace, "app.py")
    agent._save_file_with_version(
        file_path,
        "def hello():\n    return 'world'",
        "task-1",
        True,
        description="Initial version",
    )

    # Verify it was saved to database
    version_manager = VersionManager(version_db)
    version = version_manager.get_latest_version("app.py")

    assert version is not None
    assert version.content == "def hello():\n    return 'world'"


def test_construction_agent_rollback_file(workspace, version_db):
    """Test that Construction Agent can rollback a file."""
    mock_llm = Mock()
    agent = ConstructionAgent(llm=mock_llm, workspace_root=workspace, version_db=version_db)

    # Create file with version 1
    file_path = os.path.join(workspace, "app.py")
    agent._save_file_with_version(file_path, "v1", "task-1", True, description="Version 1")

    # Update to version 2
    agent._save_file_with_version(file_path, "v2", "task-2", True, description="Version 2")

    # Rollback to version 1
    success = agent.rollback_file("app.py", 1, "Test rollback")

    assert success is True

    # Verify file content
    with open(file_path, "r") as f:
        content = f.read()
    assert content == "v1"


def test_testing_agent_detects_regression(workspace, version_db):
    """Test that Testing Agent can detect regression."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="def hello():\n    return 'world'")

    testing_agent = TestingAgent(llm=mock_llm, version_db=version_db)

    # Simulate bug reports as dicts (as they come from state)
    bug_reports = [
        {
            "bug_id": "bug-1",
            "test_id": "test-1",
            "failure_type": "syntax_error",
            "file_path": "app.py",
            "error_message": "SyntaxError",
        }
    ]

    state = {
        "workspace_path": workspace,
        "architecture": "Simple app",
        "requirements_doc": "Requirements",
    }

    # This tests the regression detection logic
    # (Full integration would require actual test execution)
    # The _rollback_corrections method is called when regression is detected
    testing_agent._rollback_corrections(bug_reports, state, "Regression detected")


def test_correction_runtime_error(workspace, version_db):
    """Test that runtime errors can be corrected."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="def hello():\n    return 'world'")

    agent = ConstructionAgent(llm=mock_llm, workspace_root=workspace, version_db=version_db)

    # Create file with runtime error
    file_path = os.path.join(workspace, "app.py")
    with open(file_path, "w") as f:
        f.write("def hello():\n    return undefined_var")

    bug_reports = [
        {
            "bug_id": "bug-1",
            "test_id": "test-1",
            "failure_type": "runtime_error",
            "file_path": "app.py",
            "error_message": "NameError: name 'undefined_var' is not defined",
            "stack_trace": "Traceback (most recent call last):\n  File 'test.py', line 1",
        }
    ]

    state = {
        "workspace_path": workspace,
        "architecture": "Simple app",
        "requirements_doc": "Requirements",
    }

    result = agent.apply_corrections(bug_reports, state)

    assert "app.py" in result["corrected_files"]


def test_correction_dependency_error(workspace, version_db):
    """Test that dependency errors can be corrected."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="import os\n\ndef hello():\n    return 'world'")

    agent = ConstructionAgent(llm=mock_llm, workspace_root=workspace, version_db=version_db)

    # Create file with missing import
    file_path = os.path.join(workspace, "app.py")
    with open(file_path, "w") as f:
        f.write("def hello():\n    return os.getcwd()")

    bug_reports = [
        {
            "bug_id": "bug-1",
            "test_id": "test-1",
            "failure_type": "dependency_error",
            "file_path": "app.py",
            "error_message": "NameError: name 'os' is not defined",
            "stack_trace": "Traceback (most recent call last):\n  File 'test.py', line 1",
        }
    ]

    state = {
        "workspace_path": workspace,
        "architecture": "Simple app",
        "requirements_doc": "Requirements",
    }

    result = agent.apply_corrections(bug_reports, state)

    assert "app.py" in result["corrected_files"]


def test_correction_logical_error(workspace, version_db):
    """Test that logical errors can be corrected."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="def add(a, b):\n    return a + b")

    agent = ConstructionAgent(llm=mock_llm, workspace_root=workspace, version_db=version_db)

    # Create file with logical error
    file_path = os.path.join(workspace, "app.py")
    with open(file_path, "w") as f:
        f.write("def add(a, b):\n    return a - b")

    bug_reports = [
        {
            "bug_id": "bug-1",
            "test_id": "test-1",
            "failure_type": "logical_error",
            "file_path": "app.py",
            "error_message": "AssertionError: Expected 5 but got -1",
            "stack_trace": "Traceback (most recent call last):\n  File 'test.py', line 1",
        }
    ]

    state = {
        "workspace_path": workspace,
        "architecture": "Simple app",
        "requirements_doc": "Requirements",
    }

    result = agent.apply_corrections(bug_reports, state)

    assert "app.py" in result["corrected_files"]


def test_version_persistence_across_restart(version_db):
    """Test that version history persists across restarts."""
    # First session
    manager1 = VersionManager(version_db)
    manager1.save_version("app.py", "v1", 1, "task-1", "Version 1")

    # Simulate restart by creating new manager instance
    manager2 = VersionManager(version_db)
    version = manager2.get_version("app.py", 1)

    assert version is not None
    assert version.content == "v1"
