"""Focused checkpoint recovery tests for human approval workflow."""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from graph.workflow import run_workflow, resume_workflow, get_workflow_state
from graph.state import Task
from agents.inception_agent import InceptionAgent
from agents.planning_agent import PlanningAgent


@pytest.fixture
def checkpoint_path():
    """Provide a temporary checkpoint database path."""
    path = tempfile.mktemp(suffix=".db", prefix="test_checkpoint_")
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@patch("agents.inception_agent.InceptionAgent._initialize_llm")
def test_checkpoint_preserves_inception_outputs(mock_init, checkpoint_path):
    """Test that inception outputs are preserved across checkpoint."""
    mock_llm = Mock()
    mock_init.return_value = mock_llm
    mock_llm.invoke.side_effect = [
        AIMessage(content="# Requirements\n\nTest requirements document"),
        AIMessage(content='["Criterion 1", "Criterion 2"]'),
        AIMessage(content="# Architecture\n\nTest architecture"),
        AIMessage(content='[{"id": "task-1", "description": "Task 1", "dependencies": []}]'),
    ]

    # Step 1: Run workflow to approval checkpoint
    result, thread_id = run_workflow(
        "Build a test app",
        thread_id="test-thread-1",
        checkpoint_path=checkpoint_path,
    )

    # Verify inception outputs
    assert result["requirements_doc"] is not None
    assert len(result["requirements_doc"]) > 0
    assert result["acceptance_criteria"] is not None
    assert len(result["acceptance_criteria"]) > 0
    assert result["architecture"] is not None
    assert len(result["architecture"]) > 0
    assert result["tasks"] is not None
    assert len(result["tasks"]) > 0

    # Store the original values
    original_reqs = result["requirements_doc"]
    original_criteria = result["acceptance_criteria"]
    original_arch = result["architecture"]
    original_tasks = result["tasks"]

    # Step 2: Get state from checkpoint
    state = get_workflow_state(thread_id, checkpoint_path=checkpoint_path)
    assert state is not None

    # Step 3: Verify all inception outputs are preserved
    assert state["requirements_doc"] == original_reqs
    assert state["acceptance_criteria"] == original_criteria
    assert state["architecture"] == original_arch
    assert state["tasks"] == original_tasks


@patch("agents.inception_agent.InceptionAgent._initialize_llm")
@patch("agents.planning_agent.PlanningAgent._initialize_llm")
@patch("agents.construction_agent.ConstructionAgent._initialize_llm")
@patch("agents.testing_agent.check_docker_ready")
def test_checkpoint_resume_with_planning(mock_check, mock_construction_init, mock_planning_init, mock_inception_init, checkpoint_path):
    """Test that workflow can resume and execute Planning Agent after approval."""
    mock_llm = Mock()
    mock_inception_init.return_value = mock_llm
    mock_planning_init.return_value = mock_llm
    mock_construction_init.return_value = mock_llm
    mock_check.return_value = False  # Docker unavailable to stop at construction
    mock_llm.invoke.side_effect = [
        # Inception responses
        AIMessage(content="# Requirements\n\nTest requirements document"),
        AIMessage(content='["Criterion 1", "Criterion 2"]'),
        AIMessage(content="# Architecture\n\nTest architecture"),
        AIMessage(content='[{"id": "task-1", "description": "Task 1", "dependencies": []}]'),
        # Planning response
        AIMessage(content='{"subtasks": [], "execution_order": [], "parallel_groups": {}, "critical_path": [], "total_estimated_hours": 0.0, "technical_dependencies": []}'),
    ]

    # Step 1: Run workflow to approval checkpoint
    result, thread_id = run_workflow(
        "Build a test app",
        thread_id="test-thread-2",
        checkpoint_path=checkpoint_path,
    )

    # Verify inception outputs
    assert result["requirements_doc"] is not None
    assert result["tasks"] is not None

    # Step 2: Resume with approval
    final_result = resume_workflow(
        thread_id=thread_id,
        approval_decision="approved",
        checkpoint_path=checkpoint_path,
    )

    # Step 3: Verify Planning Agent executed
    assert final_result["execution_plan"] is not None
    # Workflow may continue past planning due to Docker unavailable stopping at testing
    assert final_result["current_step"] in ["planning_complete", "construction_complete", "testing_complete"]


@patch("agents.inception_agent.InceptionAgent._initialize_llm")
def test_tasks_serialization_as_dicts(mock_init, checkpoint_path):
    """Test that tasks are stored as dicts in checkpoint for serialization compatibility."""
    mock_llm = Mock()
    mock_init.return_value = mock_llm
    mock_llm.invoke.side_effect = [
        AIMessage(content="# Requirements\n\nTest requirements document"),
        AIMessage(content='["Criterion 1", "Criterion 2"]'),
        AIMessage(content="# Architecture\n\nTest architecture"),
        AIMessage(content='[{"id": "task-1", "description": "Task 1", "dependencies": []}]'),
    ]

    # Run workflow to approval checkpoint
    result, thread_id = run_workflow(
        "Build a test app",
        thread_id="test-thread-3",
        checkpoint_path=checkpoint_path,
    )

    # Verify tasks are dicts (not Pydantic objects)
    assert result["tasks"] is not None
    assert isinstance(result["tasks"], list)
    if result["tasks"]:
        assert isinstance(result["tasks"][0], dict)
        assert "id" in result["tasks"][0]
        assert "description" in result["tasks"][0]


@patch("agents.inception_agent.InceptionAgent._initialize_llm")
@patch("agents.planning_agent.PlanningAgent._initialize_llm")
def test_planning_reconstructs_task_objects(mock_planning_init, mock_inception_init, checkpoint_path):
    """Test that Planning Agent reconstructs Task objects from dicts."""
    mock_llm = Mock()
    mock_inception_init.return_value = mock_llm
    mock_planning_init.return_value = mock_llm
    mock_llm.invoke.side_effect = [
        # Inception responses
        AIMessage(content="# Requirements\n\nTest requirements document"),
        AIMessage(content='["Criterion 1", "Criterion 2"]'),
        AIMessage(content="# Architecture\n\nTest architecture"),
        AIMessage(content='[{"id": "task-1", "description": "Task 1", "dependencies": []}]'),
        # Planning response
        AIMessage(content='{"subtasks": [], "execution_order": [], "parallel_groups": {}, "critical_path": [], "total_estimated_hours": 0.0, "technical_dependencies": []}'),
    ]

    # Run workflow to approval checkpoint
    result, thread_id = run_workflow(
        "Build a test app",
        thread_id="test-thread-4",
        checkpoint_path=checkpoint_path,
    )

    # Resume with approval (Planning Agent will reconstruct Task objects)
    final_result = resume_workflow(
        thread_id=thread_id,
        approval_decision="approved",
        checkpoint_path=checkpoint_path,
    )

    # Verify Planning Agent successfully processed
    assert final_result["execution_plan"] is not None
