"""Tests for Operations Agent with mocked LLM and Docker."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from graph.state import WorkflowState, Task
from agents.operations_agent import OperationsAgent


def test_operations_agent_initialization():
    """Test OperationsAgent initialization."""
    mock_llm = Mock()
    agent = OperationsAgent(llm=mock_llm)
    assert agent.llm == mock_llm
    assert agent.max_rollbacks == 3


def test_operations_agent_requires_workspace():
    """Test that Operations Agent requires workspace."""
    mock_llm = Mock()
    agent = OperationsAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="testing",
        current_step="testing_complete",
        human_approval_needed=False,
        approval_status="approved",
        human_feedback=None,
        requirements_doc="Test requirements",
        acceptance_criteria=["Criterion 1"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1")],
        generated_code=None,
        test_results=None,
        code_changes_pending=False,
        workspace_path=None,  # Missing
        task_execution_records={},
        generated_files={},
        file_versions={},
        construction_status="completed",
        test_report=None,
        test_cases=None,
        bug_reports=None,
        testing_status="completed",
        correction_retry_count=0,
        deployment_config=None,
        build_report=None,
        deployment_report=None,
        health_check_result=None,
        rollback_report=None,
        operations_status="not_started",
        deployment_approval_needed=False,
        deployment_approval_status="pending",
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

    with pytest.raises(ValueError, match="requires constructed application"):
        agent.process(state)


@patch("agents.operations_agent.check_docker_ready")
def test_operations_agent_docker_unavailable(mock_check):
    """Test behavior when Docker is unavailable."""
    mock_check.return_value = False

    mock_llm = Mock()
    agent = OperationsAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="testing",
        current_step="testing_complete",
        human_approval_needed=False,
        approval_status="approved",
        human_feedback=None,
        requirements_doc="Test requirements",
        acceptance_criteria=["Criterion 1"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1")],
        generated_code=None,
        test_results=None,
        code_changes_pending=False,
        workspace_path="workspace/test",
        task_execution_records={},
        generated_files={},
        file_versions={},
        construction_status="completed",
        test_report=None,
        test_cases=None,
        bug_reports=None,
        testing_status="completed",
        correction_retry_count=0,
        deployment_config=None,
        build_report=None,
        deployment_report=None,
        health_check_result=None,
        rollback_report=None,
        operations_status="not_started",
        deployment_approval_needed=False,
        deployment_approval_status="pending",
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

    assert result["operations_status"] == "docker_unavailable"
    assert "Docker not available" in result["errors"][0]


@patch("agents.operations_agent.check_docker_ready")
def test_operations_agent_generates_deployment_config(mock_check):
    """Test deployment configuration generation with Docker unavailable."""
    mock_check.return_value = False

    mock_llm = Mock()
    agent = OperationsAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="testing",
        current_step="testing_complete",
        human_approval_needed=False,
        approval_status="approved",
        human_feedback=None,
        requirements_doc="Test requirements",
        acceptance_criteria=["Criterion 1"],
        architecture="Test architecture",
        tasks=[Task(id="task-1", description="Task 1")],
        generated_code=None,
        test_results=None,
        code_changes_pending=False,
        workspace_path="workspace/test",
        task_execution_records={},
        generated_files={},
        file_versions={},
        construction_status="completed",
        test_report=None,
        test_cases=None,
        bug_reports=None,
        testing_status="completed",
        correction_retry_count=0,
        deployment_config=None,
        build_report=None,
        deployment_report=None,
        health_check_result=None,
        rollback_report=None,
        operations_status="not_started",
        deployment_approval_needed=False,
        deployment_approval_status="pending",
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

    assert result["operations_status"] == "docker_unavailable"


def test_max_rollbacks_limit():
    """Test that max rollbacks limit is configurable."""
    agent = OperationsAgent(max_rollbacks=5)
    assert agent.max_rollbacks == 5


def test_rollback_placeholder():
    """Test that rollback returns placeholder implementation."""
    agent = OperationsAgent()
    state = {}

    result = agent.rollback_deployment(state)
    assert result["rollback_report"]["status"] == "failed"
    assert "not implemented" in result["rollback_report"]["errors"][0]
