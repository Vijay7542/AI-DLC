"""LangGraph workflow for Mini AI-DLC.

Defines the workflow graph that orchestrates agents through the AI-DLC phases.
Designed to be modular for future approval gates, requirement change detection,
and task replanning.
"""

import os
import uuid
from typing import Dict, Literal, Optional, Tuple
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from graph.state import WorkflowState
from agents.inception_agent import InceptionAgent
from agents.planning_agent import PlanningAgent
from agents.construction_agent import ConstructionAgent
from agents.testing_agent import TestingAgent
from agents.operations_agent import OperationsAgent

# Suppress msgpack warnings for custom types
os.environ["LANGGRAPH_STRICT_MSGPACK"] = "true"


def create_initial_state(user_requirements: str, thread_id: Optional[str] = None) -> WorkflowState:
    """Create initial workflow state.

    Args:
        user_requirements: User's natural language requirements
        thread_id: Optional thread ID for checkpointing (auto-generated if not provided)

    Returns:
        Initial workflow state
    """
    if thread_id is None:
        thread_id = str(uuid.uuid4())

    return WorkflowState(
        workflow_id=str(uuid.uuid4()),
        thread_id=thread_id,
        user_requirements=user_requirements,
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
        execution_plan=None,
        workspace_path=None,
        task_execution_records=None,
        generated_files=None,
        file_versions=None,
        construction_status="not_started",
        test_report=None,
        test_cases=None,
        bug_reports=None,
        testing_status="not_started",
        correction_retry_count=0,
        deployment_config=None,
        build_report=None,
        deployment_report=None,
        health_check_result=None,
        rollback_report=None,
        operations_status="not_started",
        deployment_approval_needed=False,
        deployment_approval_status="pending",
        metadata=None,
    )


def inception_node(state: WorkflowState) -> Dict:
    """Node for the Inception Agent.

    Args:
        state: Current workflow state

    Returns:
        State updates from Inception Agent
    """
    agent = InceptionAgent()
    return agent.process(state)


def human_approval_node(state: WorkflowState) -> Dict:
    """Node for human approval checkpoint.

    This node is a checkpoint where the workflow pauses and waits for human input.
    The actual approval decision is set by the human via update_state() before resuming.

    Args:
        state: Current workflow state

    Returns:
        State updates for approval checkpoint
    """
    # This node sets the approval checkpoint
    # The actual decision is made by updating state before resuming
    return {
        "human_approval_needed": True,
        "current_step": "awaiting_approval",
    }


def planning_node(state: WorkflowState) -> Dict:
    """Node for the Planning Agent.

    Args:
        state: Current workflow state

    Returns:
        State updates from Planning Agent
    """
    agent = PlanningAgent()
    return agent.process(state)


def construction_node(state: WorkflowState) -> Dict:
    """Node for the Construction Agent.

    Args:
        state: Current workflow state

    Returns:
        State updates from Construction Agent
    """
    agent = ConstructionAgent()
    return agent.process(state)


def testing_node(state: WorkflowState) -> Dict:
    """Node for the Testing Agent.

    Args:
        state: Current workflow state

    Returns:
        State updates from Testing Agent
    """
    agent = TestingAgent()
    return agent.process(state)


def operations_node(state: WorkflowState) -> Dict:
    """Node for the Operations Agent.

    Args:
        state: Current workflow state

    Returns:
        State updates from Operations Agent
    """
    agent = OperationsAgent()
    return agent.process(state)


def deployment_approval_node(state: WorkflowState) -> Dict:
    """Node for deployment approval checkpoint.

    This node pauses and waits for human approval before deployment.

    Args:
        state: Current workflow state

    Returns:
        State updates for deployment approval checkpoint
    """
    return {
        "deployment_approval_needed": True,
        "current_step": "awaiting_deployment_approval",
    }


def deployment_node(state: WorkflowState) -> Dict:
    """Node for actual deployment execution.

    Args:
        state: Current workflow state

    Returns:
        State updates from deployment
    """
    agent = OperationsAgent()
    return agent.deploy_application(state)


def route_after_approval(state: WorkflowState) -> Literal["inception", "planning", "end"]:
    """Route workflow based on approval decision.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    approval_status = state.get("approval_status", "pending")

    if approval_status == "approved":
        # Approved - continue to planning phase
        return "planning"
    elif approval_status == "rejected":
        # Rejected - stop workflow
        return "end"
    elif approval_status == "pending" and state.get("human_feedback"):
        # Changes requested - go back to inception with feedback
        return "inception"
    else:
        # Still pending (waiting for human) or other state - end
        return "end"


def route_after_testing(state: WorkflowState) -> Literal["construction", "operations", "end"]:
    """Route workflow based on test results.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    testing_status = state.get("testing_status")
    correction_count = state.get("correction_retry_count", 0)

    if testing_status == "completed":
        # All tests passed - go to operations
        return "operations"
    elif testing_status == "failed" and correction_count < 3:
        # Tests failed but retries available - go back to construction
        return "construction"
    else:
        # Max retries reached or sandbox unavailable - go to END
        return "end"


def route_after_deployment_approval(state: WorkflowState) -> Literal["deployment", "end"]:
    """Route workflow based on deployment approval decision.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    approval_status = state.get("deployment_approval_status", "pending")

    if approval_status == "approved":
        # Approved - deploy
        return "deployment"
    else:
        # Rejected or pending - stop
        return "end"


def create_workflow(checkpointer: Optional[SqliteSaver] = None) -> StateGraph:
    """Create the LangGraph workflow.

    Includes:
    - Inception Agent node
    - Human approval checkpoint
    - Planning Agent node
    - Construction Agent node
    - Testing Agent node
    - Operations Agent node
    - Deployment approval checkpoint
    - Conditional routing based on approval, test results, and deployment
    - Checkpointing support for workflow persistence

    Args:
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("inception", inception_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("construction", construction_node)
    workflow.add_node("testing", testing_node)
    workflow.add_node("operations", operations_node)
    workflow.add_node("deployment_approval", deployment_approval_node)
    workflow.add_node("deployment", deployment_node)

    # Add edges
    workflow.set_entry_point("inception")
    workflow.add_edge("inception", "human_approval")

    # Add conditional routing from approval checkpoint
    workflow.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "inception": "inception",
            "planning": "planning",
            "end": END,
        }
    )

    # Planning goes to construction
    workflow.add_edge("planning", "construction")

    # Construction goes to testing
    workflow.add_edge("construction", "testing")

    # Add conditional routing from testing
    workflow.add_conditional_edges(
        "testing",
        route_after_testing,
        {
            "construction": "construction",
            "operations": "operations",
            "end": END,
        }
    )

    # Operations goes to deployment approval
    workflow.add_edge("operations", "deployment_approval")

    # Add conditional routing from deployment approval
    workflow.add_conditional_edges(
        "deployment_approval",
        route_after_deployment_approval,
        {
            "deployment": "deployment",
            "end": END,
        }
    )

    # Deployment goes to END
    workflow.add_edge("deployment", END)

    return workflow


def run_workflow(
    user_requirements: str,
    thread_id: Optional[str] = None,
    checkpoint_path: str = "checkpoints.db",
) -> Tuple[WorkflowState, str]:
    """Run the workflow with user requirements.

    Args:
        user_requirements: User's natural language requirements
        thread_id: Optional thread ID for checkpointing (auto-generated if not provided)
        checkpoint_path: Path to SQLite checkpoint database

    Returns:
        Tuple of (final_workflow_state, thread_id)
    """
    initial_state = create_initial_state(user_requirements, thread_id)

    with SqliteSaver.from_conn_string(checkpoint_path) as checkpointer:
        workflow = create_workflow(checkpointer)

        # Compile and run the workflow
        app = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": initial_state["thread_id"]}}

        # Run until human approval checkpoint
        result = app.invoke(initial_state, config)

    return result, initial_state["thread_id"]


def resume_workflow(
    thread_id: str,
    approval_decision: Literal["approved", "rejected"],
    human_feedback: Optional[str] = None,
    checkpoint_path: str = "checkpoints.db",
) -> WorkflowState:
    """Resume a paused workflow with human approval decision.

    Args:
        thread_id: Thread ID of the paused workflow
        approval_decision: Human's approval decision ("approved" or "rejected")
        human_feedback: Optional feedback if changes are requested
        checkpoint_path: Path to SQLite checkpoint database

    Returns:
        Final workflow state after resuming
    """
    with SqliteSaver.from_conn_string(checkpoint_path) as checkpointer:
        workflow = create_workflow(checkpointer)
        app = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        # Update state with approval decision
        state_update = {
            "approval_status": approval_decision,
            "human_feedback": human_feedback,
            "human_approval_needed": False,
        }

        # Resume workflow with updated state
        result = app.update_state(config, state_update)
        result = app.invoke(None, config)

    return result


def get_workflow_state(thread_id: str, checkpoint_path: str = "checkpoints.db") -> Optional[WorkflowState]:
    """Get the current state of a workflow by thread ID.

    Args:
        thread_id: Thread ID of the workflow
        checkpoint_path: Path to SQLite checkpoint database

    Returns:
        Current workflow state or None if not found
    """
    with SqliteSaver.from_conn_string(checkpoint_path) as checkpointer:
        workflow = create_workflow(checkpointer)
        app = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        try:
            state = app.get_state(config)
            if state and state.values:
                return state.values
        except Exception:
            pass

    return None
