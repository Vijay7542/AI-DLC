"""Tests for Testing Agent with mocked LLM."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from graph.state import WorkflowState, Task, TestCase, BugReport, TestReport
from agents.testing_agent import TestingAgent


def test_testing_agent_initialization():
    """Test TestingAgent initialization."""
    mock_llm = Mock()
    agent = TestingAgent(llm=mock_llm)
    assert agent.llm == mock_llm
    assert agent.max_corrections == 3


def test_testing_agent_requires_workspace():
    """Test that Testing Agent requires workspace."""
    mock_llm = Mock()
    agent = TestingAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="construction",
        current_step="construction_complete",
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
        testing_status="not_started",
        correction_retry_count=0,
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


@patch("agents.testing_agent.check_docker_ready")
def test_testing_agent_docker_unavailable(mock_check):
    """Test behavior when Docker is unavailable."""
    mock_check.return_value = False

    mock_llm = Mock()
    agent = TestingAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="construction",
        current_step="construction_complete",
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
        testing_status="not_started",
        correction_retry_count=0,
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

    assert result["testing_status"] == "sandbox_unavailable"
    assert "Docker sandbox not available" in result["errors"][0]


@patch("agents.testing_agent.check_docker_ready")
def test_testing_agent_generates_tests(mock_check):
    """Test test generation with Docker unavailable."""
    mock_check.return_value = False

    mock_llm = Mock()
    agent = TestingAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="construction",
        current_step="construction_complete",
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
        testing_status="not_started",
        correction_retry_count=0,
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

    assert result["testing_status"] == "sandbox_unavailable"


def test_failure_classification():
    """Test failure classification."""
    agent = TestingAgent()

    test_case = TestCase(
        test_id="test-1",
        test_name="Test",
        test_type="unit",
        file_path="test.py",
        function_name="test_func",
        description="Test",
    )

    # Syntax error
    bug = agent._classify_failure(test_case, "SyntaxError: invalid syntax")
    assert bug.failure_type == "syntax_error"

    # Dependency error
    bug = agent._classify_failure(test_case, "ModuleNotFoundError: No module")
    assert bug.failure_type == "dependency_error"

    # Runtime error (catches Exception)
    bug = agent._classify_failure(test_case, "RuntimeError: error")
    assert bug.failure_type == "runtime_error"


def test_max_corrections_limit():
    """Test that correction loop respects max retry limit."""
    agent = TestingAgent(max_corrections=2)
    assert agent.max_corrections == 2


def test_correction_loop_not_implemented():
    """Test that correction returns False (placeholder)."""
    agent = TestingAgent()
    bug_reports = []
    state = {}

    result = agent._request_corrections(bug_reports, state)
    assert result is False  # Placeholder implementation
