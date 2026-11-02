"""Workflow state schema for Mini AI-DLC."""

from typing import Optional, List, Dict, Literal, TypedDict
from pydantic import BaseModel, Field


class Task(BaseModel):
    """A task in the implementation plan."""

    id: str = Field(description="Unique task identifier")
    description: str = Field(description="Task description")
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        default="pending", description="Task status"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="List of task IDs this task depends on"
    )


class WorkflowState(TypedDict):
    """Shared workflow state that flows through the LangGraph workflow.

    Designed to be modular and extensible for future features:
    - Business requirement change detection
    - Impact analysis
    - Task replanning
    - Human approval workflows
    """

    # Workflow identification
    workflow_id: str

    # User input
    user_requirements: str

    # Workflow control
    phase: Literal["inception", "construction", "operations", "completed"]
    current_step: str
    human_approval_needed: bool
    approval_status: Literal["pending", "approved", "rejected"]
    human_feedback: Optional[str]

    # Inception outputs
    requirements_doc: Optional[str]
    acceptance_criteria: Optional[List[str]]
    architecture: Optional[str]
    tasks: Optional[List[Task]]

    # Construction outputs
    generated_code: Optional[Dict[str, str]]  # filename -> code
    test_results: Optional[Dict[str, bool]]  # test_name -> passed
    code_changes_pending: bool

    # Operations outputs
    deployment_docs: Optional[str]
    monitoring_plan: Optional[str]

    # Error handling
    errors: List[str]
    retry_count: int

    # Extensibility fields for future features
    # Requirement change tracking
    requirement_changes: Optional[List[Dict[str, str]]]  # Change history
    impact_analysis: Optional[Dict[str, str]]  # Impact assessment results

    # Task replanning
    replanned_tasks: Optional[List[Task]]  # Updated task list after replanning
    replanning_reason: Optional[str]  # Why replanning was triggered

    # Additional metadata
    metadata: Optional[Dict[str, str]]  # Flexible metadata for future extensions
