"""Tests for InceptionAgent with mocked LLM."""

import pytest
from unittest.mock import Mock
from langchain_core.messages import AIMessage
from graph.state import WorkflowState, Task
from agents.inception_agent import InceptionAgent


def test_inception_agent_initialization():
    """Test InceptionAgent initialization with mocked LLM."""
    mock_llm = Mock()
    agent = InceptionAgent(llm=mock_llm)
    assert agent.llm == mock_llm


def test_inception_agent_process():
    """Test InceptionAgent process method with mocked LLM."""
    mock_llm = Mock()

    # Mock responses for different prompts
    mock_llm.invoke.side_effect = [
        AIMessage(content="# Requirements Document\n\nThis is a test requirements document."),
        AIMessage(content='["Criterion 1", "Criterion 2", "Criterion 3"]'),
        AIMessage(content="# Architecture\n\nThis is a test architecture."),
        AIMessage(
            content='[{"id": "task-1", "description": "Task 1", "dependencies": []}, '
            '{"id": "task-2", "description": "Task 2", "dependencies": ["task-1"]}]'
        ),
    ]

    agent = InceptionAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        user_requirements="Build a simple calculator",
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

    result = agent.process(state)

    assert result["requirements_doc"] is not None
    assert result["acceptance_criteria"] is not None
    assert result["architecture"] is not None
    assert result["tasks"] is not None
    assert result["human_approval_needed"] is True
    assert result["approval_status"] == "pending"
    assert result["current_step"] == "inception_complete"


def test_inception_agent_generates_requirements_doc():
    """Test requirements document generation."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content="# Requirements\n\nTest requirements document"
    )

    agent = InceptionAgent(llm=mock_llm)
    result = agent._generate_requirements_doc("Build a calculator")

    assert result == "# Requirements\n\nTest requirements document"
    mock_llm.invoke.assert_called_once()


def test_inception_agent_generates_acceptance_criteria():
    """Test acceptance criteria generation."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content='["Criterion 1", "Criterion 2", "Criterion 3"]'
    )

    agent = InceptionAgent(llm=mock_llm)
    result = agent._generate_acceptance_criteria("Build a calculator")

    assert isinstance(result, list)
    assert len(result) == 3
    assert "Criterion 1" in result


def test_inception_agent_generates_architecture():
    """Test architecture generation."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content="# Architecture\n\nTest architecture"
    )

    agent = InceptionAgent(llm=mock_llm)
    result = agent._generate_architecture("Build a calculator")

    assert result == "# Architecture\n\nTest architecture"


def test_inception_agent_generates_tasks():
    """Test task generation."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content='[{"id": "task-1", "description": "Task 1", "dependencies": []}]'
    )

    agent = InceptionAgent(llm=mock_llm)
    result = agent._generate_tasks("Build a calculator")

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Task)
    assert result[0].id == "task-1"


def test_inception_agent_handles_invalid_json_in_acceptance_criteria():
    """Test handling of invalid JSON in acceptance criteria."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content="Criterion 1\nCriterion 2\nCriterion 3"
    )

    agent = InceptionAgent(llm=mock_llm)
    result = agent._generate_acceptance_criteria("Build a calculator")

    # Should fallback to splitting by newlines
    assert isinstance(result, list)
    assert len(result) >= 1


def test_inception_agent_handles_invalid_json_in_tasks():
    """Test handling of invalid JSON in task generation."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="Invalid JSON")

    agent = InceptionAgent(llm=mock_llm)
    result = agent._generate_tasks("Build a calculator")

    # Should fallback to a single default task
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].description == "Implement the project based on requirements"


def test_inception_agent_process_with_partial_failures():
    """Test that process continues even if some generations fail."""
    mock_llm = Mock()

    # Mock responses with one failure (use ValueError to avoid retries)
    mock_llm.invoke.side_effect = [
        AIMessage(content="# Requirements\n\nTest requirements"),
        ValueError("Authentication error for acceptance criteria"),
        AIMessage(content="# Architecture\n\nTest architecture"),
        AIMessage(content='[{"id": "task-1", "description": "Task 1", "dependencies": []}]'),
    ]

    agent = InceptionAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        user_requirements="Build a simple calculator",
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

    result = agent.process(state)

    # Should have generated some outputs despite one failure
    assert result["requirements_doc"] is not None
    assert result["architecture"] is not None
    assert result["tasks"] is not None
    # Acceptance criteria should be None due to error
    assert result["acceptance_criteria"] is None
    # Should have errors in the result
    assert "errors" in result
    assert len(result["errors"]) == 1
