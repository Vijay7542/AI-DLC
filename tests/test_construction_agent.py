"""Tests for Construction Agent with mocked LLM."""

import pytest
import os
import shutil
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from graph.state import WorkflowState, Task, Subtask, ExecutionPlan
from agents.construction_agent import ConstructionAgent


@pytest.fixture
def temp_workspace(tmp_path):
    """Provide a temporary workspace for testing."""
    workspace = os.path.join(tmp_path, "workspace")
    yield workspace
    if os.path.exists(workspace):
        shutil.rmtree(workspace)


def test_construction_agent_initialization():
    """Test ConstructionAgent initialization."""
    mock_llm = Mock()
    agent = ConstructionAgent(llm=mock_llm)
    assert agent.llm == mock_llm
    assert agent.workspace_root == "workspace"


def test_construction_agent_requires_execution_plan():
    """Test that Construction Agent requires execution plan."""
    mock_llm = Mock()
    agent = ConstructionAgent(llm=mock_llm)

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="planning",
        current_step="planning_complete",
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
        deployment_docs=None,
        monitoring_plan=None,
        errors=[],
        retry_count=0,
        requirement_changes=None,
        impact_analysis=None,
        replanned_tasks=None,
        replanning_reason=None,
        execution_plan=None,  # Missing
        workspace_path=None,
        task_execution_records=None,
        generated_files=None,
        file_versions=None,
        construction_status="not_started",
        metadata=None,
    )

    with pytest.raises(ValueError, match="requires approved execution plan"):
        agent.process(state)


def test_construction_agent_creates_workspace(temp_workspace):
    """Test workspace creation."""
    mock_llm = Mock()
    agent = ConstructionAgent(llm=mock_llm, workspace_root=temp_workspace)

    workspace_path = agent._create_workspace("test-wf-123")

    assert os.path.exists(workspace_path)
    assert "test-wf-123" in workspace_path


def test_python_syntax_validation():
    """Test Python syntax validation."""
    agent = ConstructionAgent()

    # Valid Python
    valid_code = "def hello():\n    return 'world'"
    assert agent._validate_python_syntax(valid_code) is True

    # Invalid Python
    invalid_code = "def hello(\n    return 'world'"
    assert agent._validate_python_syntax(invalid_code) is False


def test_safe_path_validation():
    """Test safe path validation."""
    agent = ConstructionAgent()

    # Safe paths
    assert agent._is_safe_path("app/models/user.py") is True
    assert agent._is_safe_path("test_file.py") is True

    # Unsafe paths
    assert agent._is_safe_path("../etc/passwd") is False
    assert agent._is_safe_path("/etc/passwd") is False
    assert agent._is_safe_path("../../etc/passwd") is False


def test_dependencies_satisfied():
    """Test dependency checking."""
    agent = ConstructionAgent()

    subtask = Subtask(
        id="subtask-2",
        parent_task_id="task-1",
        description="Test",
        dependencies=["subtask-1"],
    )

    # Dependencies not satisfied
    task_records = {}
    assert agent._dependencies_satisfied(subtask, task_records) is False

    # Dependencies satisfied
    task_records = {
        "subtask-1": {"status": "completed"}
    }
    assert agent._dependencies_satisfied(subtask, task_records) is True


def test_construction_agent_generates_files(temp_workspace):
    """Test file generation with mocked LLM."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content='{"app/models/user.py": "class User:\\n    pass", "app/main.py": "from app.models import User"}'
    )

    agent = ConstructionAgent(llm=mock_llm, workspace_root=temp_workspace)

    execution_plan = ExecutionPlan(
        subtasks=[
            Subtask(
                id="subtask-1",
                parent_task_id="task-1",
                description="Create user model",
                dependencies=[],
            )
        ],
        execution_order=["subtask-1"],
        parallel_groups={},
        critical_path=["subtask-1"],
    )

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="planning",
        current_step="planning_complete",
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
        deployment_docs=None,
        monitoring_plan=None,
        errors=[],
        retry_count=0,
        requirement_changes=None,
        impact_analysis=None,
        replanned_tasks=None,
        replanning_reason=None,
        execution_plan=execution_plan.model_dump(),
        workspace_path=None,
        task_execution_records={},
        generated_files={},
        file_versions={},
        construction_status="not_started",
        metadata=None,
    )

    result = agent.process(state)

    assert result["workspace_path"] is not None
    assert os.path.exists(result["workspace_path"])
    assert "subtask-1" in result["task_execution_records"]
    assert result["task_execution_records"]["subtask-1"]["status"] == "completed"


def test_construction_agent_handles_invalid_json(temp_workspace):
    """Test fallback when LLM returns invalid JSON."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content="```python\ndef hello():\n    return 'world'\n```"
    )

    agent = ConstructionAgent(llm=mock_llm, workspace_root=temp_workspace)

    execution_plan = ExecutionPlan(
        subtasks=[
            Subtask(
                id="subtask-1",
                parent_task_id="task-1",
                description="Create user model",
                dependencies=[],
            )
        ],
        execution_order=["subtask-1"],
        parallel_groups={},
        critical_path=["subtask-1"],
    )

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="planning",
        current_step="planning_complete",
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
        deployment_docs=None,
        monitoring_plan=None,
        errors=[],
        retry_count=0,
        requirement_changes=None,
        impact_analysis=None,
        replanned_tasks=None,
        replanning_reason=None,
        execution_plan=execution_plan.model_dump(),
        workspace_path=None,
        task_execution_records={},
        generated_files={},
        file_versions={},
        construction_status="not_started",
        metadata=None,
    )

    result = agent.process(state)

    # Should use markdown extraction fallback
    assert result["workspace_path"] is not None
    assert "subtask-1" in result["task_execution_records"]


def test_construction_agent_respects_dependencies(temp_workspace):
    """Test that dependencies are respected."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content='{"test.py": "# code"}'
    )

    agent = ConstructionAgent(llm=mock_llm, workspace_root=temp_workspace)

    execution_plan = ExecutionPlan(
        subtasks=[
            Subtask(
                id="subtask-1",
                parent_task_id="task-1",
                description="Task 1",
                dependencies=[],
            ),
            Subtask(
                id="subtask-2",
                parent_task_id="task-1",
                description="Task 2",
                dependencies=["subtask-1"],
            ),
        ],
        execution_order=["subtask-1", "subtask-2"],
        parallel_groups={},
        critical_path=["subtask-1", "subtask-2"],
    )

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="planning",
        current_step="planning_complete",
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
        deployment_docs=None,
        monitoring_plan=None,
        errors=[],
        retry_count=0,
        requirement_changes=None,
        impact_analysis=None,
        replanned_tasks=None,
        replanning_reason=None,
        execution_plan=execution_plan.model_dump(),
        workspace_path=None,
        task_execution_records={},
        generated_files={},
        file_versions={},
        construction_status="not_started",
        metadata=None,
    )

    result = agent.process(state)

    # Both should complete (dependencies are satisfied in order)
    assert "subtask-1" in result["task_execution_records"]
    assert "subtask-2" in result["task_execution_records"]


def test_construction_agent_prevents_path_traversal(temp_workspace):
    """Test that path traversal is prevented."""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content='{"../../etc/passwd": "malicious"}'
    )

    agent = ConstructionAgent(llm=mock_llm, workspace_root=temp_workspace)

    execution_plan = ExecutionPlan(
        subtasks=[
            Subtask(
                id="subtask-1",
                parent_task_id="task-1",
                description="Task 1",
                dependencies=[],
            )
        ],
        execution_order=["subtask-1"],
        parallel_groups={},
        critical_path=["subtask-1"],
    )

    state = WorkflowState(
        workflow_id="wf-123",
        thread_id="thread-123",
        user_requirements="Test",
        phase="planning",
        current_step="planning_complete",
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
        deployment_docs=None,
        monitoring_plan=None,
        errors=[],
        retry_count=0,
        requirement_changes=None,
        impact_analysis=None,
        replanned_tasks=None,
        replanning_reason=None,
        execution_plan=execution_plan.model_dump(),
        workspace_path=None,
        task_execution_records={},
        generated_files={},
        file_versions={},
        construction_status="not_started",
        metadata=None,
    )

    result = agent.process(state)

    # Should have error for unsafe path
    assert "errors" in result
    assert len(result["errors"]) > 0
