"""LangGraph workflow for Mini AI-DLC.

Defines the workflow graph that orchestrates agents through the AI-DLC phases.
Designed to be modular for future approval gates, requirement change detection,
and task replanning.
"""

import uuid
from typing import Dict
from langgraph.graph import StateGraph, END
from graph.state import WorkflowState
from agents.inception_agent import InceptionAgent


def create_initial_state(user_requirements: str) -> WorkflowState:
    """Create initial workflow state.

    Args:
        user_requirements: User's natural language requirements

    Returns:
        Initial workflow state
    """
    return WorkflowState(
        workflow_id=str(uuid.uuid4()),
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


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow.

    For Phase 1, this is a simple workflow with just the Inception Agent.
    Future phases will add:
    - Approval gates
    - Construction Agent
    - Operations Agent
    - Conditional routing
    - Checkpoint integration

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("inception", inception_node)

    # Add edges (simple linear flow for Phase 1)
    workflow.set_entry_point("inception")
    workflow.add_edge("inception", END)

    return workflow


def run_workflow(user_requirements: str) -> WorkflowState:
    """Run the workflow with user requirements.

    Args:
        user_requirements: User's natural language requirements

    Returns:
        Final workflow state
    """
    initial_state = create_initial_state(user_requirements)
    workflow = create_workflow()

    # Compile and run the workflow
    app = workflow.compile()
    result = app.invoke(initial_state)

    return result
