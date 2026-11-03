"""Tests for Planning Agent with mocked LLM."""

import pytest
from unittest.mock import Mock
from langchain_core.messages import AIMessage
from graph.state import WorkflowState, Task, Subtask, ExecutionPlan
from agents.planning_agent import PlanningAgent


def test_planning_agent_initialization():
    """Test PlanningAgent initialization with mocked LLM."""
    mock_llm = Mock()
    agent = PlanningAgent(llm=mock_llm)
    assert agent.llm == mock_llm


def test_planning_agent_requires_approval():
    """Test that Planning Agent requires approved inception outputs."""
    mock_llm = Mock()
    agent = PlanningAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="inception",
        current_step="inception_complete",
        human_approval_needed=False,
        approval_status="pending",  # Not approved
        human_feedback=None,
        requirements_doc="Test doc",
        acceptance_criteria=["Criterion 1"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1")],
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
        execution_plan=None,
        metadata=None,
    )

    with pytest.raises(ValueError, match="requires approved inception outputs"):
        agent.process(state)


def test_planning_agent_generates_execution_plan():
    """Test execution plan generation with mocked LLM."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content='{"subtasks": [{"id": "subtask-1", "parent_task_id": "task-1", "description": "Implement feature", "priority": "high", "complexity": "moderate", "estimated_hours": 4.0, "dependencies": [], "parallel_group": null, "blockers": []}], "execution_order": ["subtask-1"], "parallel_groups": {}, "critical_path": ["subtask-1"], "total_estimated_hours": 4.0, "technical_dependencies": []}'
    )

    agent = PlanningAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="inception",
        current_step="inception_complete",
        human_approval_needed=False,
        approval_status="approved",  # Approved
        human_feedback=None,
        requirements_doc="Test requirements document",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1", dependencies=[])],
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
        execution_plan=None,
        metadata=None,
    )

    result = agent.process(state)

    assert result["execution_plan"] is not None
    assert result["phase"] == "planning"
    assert result["current_step"] == "planning_complete"


def test_planning_agent_handles_invalid_json():
    """Test fallback when LLM returns invalid JSON."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="Invalid JSON response")

    agent = PlanningAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="inception",
        current_step="inception_complete",
        human_approval_needed=False,
        approval_status="approved",
        human_feedback=None,
        requirements_doc="Test requirements",
        acceptance_criteria=["Criterion 1"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1", dependencies=[])],
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
        execution_plan=None,
        metadata=None,
    )

    result = agent.process(state)

    # Should use fallback plan
    assert result["execution_plan"] is not None
    assert "subtasks" in result["execution_plan"]


def test_planning_agent_handles_missing_outputs():
    """Test error when inception outputs are missing."""
    mock_llm = Mock()
    agent = PlanningAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="inception",
        current_step="inception_complete",
        human_approval_needed=False,
        approval_status="approved",
        human_feedback=None,
        requirements_doc=None,  # Missing
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
        execution_plan=None,
        metadata=None,
    )

    with pytest.raises(ValueError, match="Missing required inception outputs"):
        agent.process(state)


def test_planning_agent_execution_plan_structure():
    """Test that execution plan has correct structure."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content='{"subtasks": [{"id": "subtask-1", "parent_task_id": "task-1", "description": "Implement", "priority": "high", "complexity": "moderate", "estimated_hours": 4.0, "dependencies": [], "parallel_group": "group-a", "blockers": []}, {"id": "subtask-2", "parent_task_id": "task-1", "description": "Test", "priority": "medium", "complexity": "simple", "estimated_hours": 2.0, "dependencies": ["subtask-1"], "parallel_group": null, "blockers": []}], "execution_order": ["subtask-1", "subtask-2"], "parallel_groups": {"group-a": ["subtask-1"]}, "critical_path": ["subtask-1", "subtask-2"], "total_estimated_hours": 6.0, "technical_dependencies": ["python"]}'
    )

    agent = PlanningAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="inception",
        current_step="inception_complete",
        human_approval_needed=False,
        approval_status="approved",
        human_feedback=None,
        requirements_doc="Test requirements",
        acceptance_criteria=["Criterion 1"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1", dependencies=[])],
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
        execution_plan=None,
        metadata=None,
    )

    result = agent.process(state)
    plan = result["execution_plan"]

    assert plan is not None
    assert len(plan["subtasks"]) == 2
    assert plan["subtasks"][0]["priority"] == "high"
    assert plan["subtasks"][0]["parallel_group"] == "group-a"
    assert plan["subtasks"][1]["dependencies"] == ["subtask-1"]
    assert len(plan["execution_order"]) == 2
    assert plan["total_estimated_hours"] == 6.0
    assert "python" in plan["technical_dependencies"]


def test_planning_agent_partial_failure():
    """Test that errors are collected when partial failures occur."""
    mock_llm = Mock()
    mock_llm.invoke.side_effect = Exception("LLM error")

    agent = PlanningAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="inception",
        current_step="inception_complete",
        human_approval_needed=False,
        approval_status="approved",
        human_feedback=None,
        requirements_doc="Test requirements",
        acceptance_criteria=["Criterion 1"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1", dependencies=[])],
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
        execution_plan=None,
        metadata=None,
    )

    result = agent.process(state)

    assert result["execution_plan"] is None
    assert "errors" in result
    assert len(result["errors"]) == 1
