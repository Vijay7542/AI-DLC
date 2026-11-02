"""Tests for workflow state schema."""

import pytest
from graph.state import Task, WorkflowState


def test_task_creation():
    """Test creating a Task instance."""
    task = Task(
        id="task-1",
        description="Implement feature X",
        status="pending",
        dependencies=[],
    )
    assert task.id == "task-1"
    assert task.description == "Implement feature X"
    assert task.status == "pending"
    assert task.dependencies == []


def test_task_with_dependencies():
    """Test creating a Task with dependencies."""
    task = Task(
        id="task-2",
        description="Implement feature Y",
        status="pending",
        dependencies=["task-1"],
    )
    assert task.dependencies == ["task-1"]


def test_task_status_validation():
    """Test that Task status accepts valid values."""
    valid_statuses = ["pending", "in_progress", "completed", "failed"]
    for status in valid_statuses:
        task = Task(id="test", description="test", status=status)
        assert task.status == status


def test_workflow_state_creation():
    """Test creating a WorkflowState instance."""
    state = WorkflowState(
        workflow_id="wf-123",
        user_requirements="Build a calculator",
        phase="inception",
        current_step="start",
        human_approval_needed=False,
        approval_status="pending",
        human_feedback=None,
        requirements_doc=None,
        acceptance_criteria=None,
        architecture=None,
        tasks=None,
        generated_code=None,
        test_results=None,
        code_changes_pending=False,
        deployment_docs=None,
        monitoring_plan=None,
        errors=[],
        retry_count=0,
        requirement_changes=None,
        impact_analysis=None,
        replanned_tasks=None,
        replanning_reason=None,
        metadata=None,
    )
    assert state["workflow_id"] == "wf-123"
    assert state["user_requirements"] == "Build a calculator"
    assert state["phase"] == "inception"


def test_workflow_state_with_tasks():
    """Test WorkflowState with tasks."""
    tasks = [
        Task(id="task-1", description="Task 1", status="pending"),
        Task(id="task-2", description="Task 2", status="pending"),
    ]
    state = WorkflowState(
        workflow_id="wf-123",
        user_requirements="Build a calculator",
        phase="inception",
        current_step="start",
        human_approval_needed=False,
        approval_status="pending",
        human_feedback=None,
        requirements_doc=None,
        acceptance_criteria=None,
        architecture=None,
        tasks=tasks,
        generated_code=None,
        test_results=None,
        code_changes_pending=False,
        deployment_docs=None,
        monitoring_plan=None,
        errors=[],
        retry_count=0,
        requirement_changes=None,
        impact_analysis=None,
        replanned_tasks=None,
        replanning_reason=None,
        metadata=None,
    )
    assert len(state["tasks"]) == 2
    assert state["tasks"][0].id == "task-1"


def test_task_serialization():
    """Test that Task can be serialized to dict."""
    task = Task(id="task-1", description="Test task", status="pending")
    task_dict = task.model_dump()
    assert task_dict["id"] == "task-1"
    assert task_dict["description"] == "Test task"
    assert task_dict["status"] == "pending"


def test_task_deserialization():
    """Test that Task can be deserialized from dict."""
    task_dict = {
        "id": "task-1",
        "description": "Test task",
        "status": "pending",
        "dependencies": [],
    }
    task = Task(**task_dict)
    assert task.id == "task-1"
    assert task.description == "Test task"
