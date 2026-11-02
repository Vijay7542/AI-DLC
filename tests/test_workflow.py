"""Tests for LangGraph workflow with mocked LLM."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from graph.workflow import create_initial_state, create_workflow, run_workflow
from graph.state import WorkflowState
from agents.inception_agent import InceptionAgent


def test_create_initial_state():
    """Test creating initial workflow state."""
    state = create_initial_state("Build a calculator")

    assert state["workflow_id"] is not None
    assert state["user_requirements"] == "Build a calculator"
    assert state["phase"] == "inception"
    assert state["current_step"] == "start"
    assert state["human_approval_needed"] is False
    assert state["approval_status"] == "pending"
    assert state["requirements_doc"] is None
    assert state["tasks"] is None


def test_create_workflow():
    """Test creating the workflow graph."""
    workflow = create_workflow()
    assert workflow is not None


@patch("graph.workflow.InceptionAgent")
def test_workflow_execution(mock_inception_agent_class):
    """Test executing the workflow with mocked Inception Agent."""
    # Mock the InceptionAgent
    mock_agent = Mock()
    mock_agent.process.return_value = {
        "requirements_doc": "# Requirements",
        "acceptance_criteria": ["Criterion 1"],
        "architecture": "# Architecture",
        "tasks": [],
        "human_approval_needed": True,
        "approval_status": "pending",
        "current_step": "inception_complete",
    }
    mock_inception_agent_class.return_value = mock_agent

    # Run workflow
    result = run_workflow("Build a calculator")

    assert result["requirements_doc"] == "# Requirements"
    assert result["human_approval_needed"] is True
    assert result["approval_status"] == "pending"
    assert result["current_step"] == "inception_complete"


@patch("graph.workflow.InceptionAgent")
def test_workflow_execution_with_tasks(mock_inception_agent_class):
    """Test workflow execution with task generation."""
    from graph.state import Task

    # Mock the InceptionAgent
    mock_agent = Mock()
    mock_agent.process.return_value = {
        "requirements_doc": "# Requirements",
        "acceptance_criteria": ["Criterion 1"],
        "architecture": "# Architecture",
        "tasks": [Task(id="task-1", description="Task 1", status="pending")],
        "human_approval_needed": True,
        "approval_status": "pending",
        "current_step": "inception_complete",
    }
    mock_inception_agent_class.return_value = mock_agent

    # Run workflow
    result = run_workflow("Build a calculator")

    assert result["tasks"] is not None
    assert len(result["tasks"]) == 1
    assert result["tasks"][0].id == "task-1"


def test_workflow_graph_structure():
    """Test that the workflow graph has the correct structure."""
    workflow = create_workflow()

    # Compile the workflow
    app = workflow.compile()

    # Check that the graph can be compiled
    assert app is not None


def test_initial_state_has_all_required_fields():
    """Test that initial state has all required fields."""
    state = create_initial_state("Test requirements")

    required_fields = [
        "workflow_id",
        "user_requirements",
        "phase",
        "current_step",
        "human_approval_needed",
        "approval_status",
        "human_feedback",
        "requirements_doc",
        "acceptance_criteria",
        "architecture",
        "tasks",
        "generated_code",
        "test_results",
        "code_changes_pending",
        "deployment_docs",
        "monitoring_plan",
        "errors",
        "retry_count",
        "requirement_changes",
        "impact_analysis",
        "replanned_tasks",
        "replanning_reason",
        "metadata",
    ]

    for field in required_fields:
        assert field in state
