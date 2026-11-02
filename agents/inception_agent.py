"""Inception Agent for Mini AI-DLC.

Handles requirements analysis, architecture design, and task breakdown.
Designed to be modular for future requirement change detection and impact analysis.
"""

import json
import uuid
from typing import Any, List
from graph.state import WorkflowState, Task
from agents.base_agent import BaseAgent
from langchain_core.messages import BaseMessage


class InceptionAgent(BaseAgent):
    """Agent for the Inception phase of AI-DLC.

    Analyzes user requirements and produces:
    - Structured requirements document
    - Acceptance criteria
    - High-level architecture
    - Implementation task breakdown
    """

    def __init__(self, llm=None, use_test_config=False):
        """Initialize the Inception Agent."""
        super().__init__(llm=llm, use_test_config=use_test_config)

    def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Process the Inception phase.

        Args:
            state: Current workflow state

        Returns:
            State updates with inception outputs
        """
        user_requirements = state["user_requirements"]

        # Generate inception outputs
        requirements_doc = self._generate_requirements_doc(user_requirements)
        acceptance_criteria = self._generate_acceptance_criteria(user_requirements)
        architecture = self._generate_architecture(user_requirements)
        tasks = self._generate_tasks(user_requirements)

        # Set approval flag for human review
        return {
            "requirements_doc": requirements_doc,
            "acceptance_criteria": acceptance_criteria,
            "architecture": architecture,
            "tasks": tasks,
            "human_approval_needed": True,
            "approval_status": "pending",
            "current_step": "inception_complete",
        }

    def _generate_requirements_doc(self, user_requirements: str) -> str:
        """Generate a structured requirements document.

        Args:
            user_requirements: User's natural language requirements

        Returns:
            Structured requirements document as string
        """
        system_prompt = self.create_system_prompt(
            """You are an expert software requirements analyst. 
            Given user requirements, generate a structured requirements document.
            Focus on clarity, completeness, and testability.
            Format the output in markdown with clear sections."""
        )

        user_prompt = self.create_user_prompt(
            f"Generate a requirements document for the following:\n\n{user_requirements}"
        )

        response = self.invoke_llm([system_prompt, user_prompt])
        return response.content

    def _generate_acceptance_criteria(self, user_requirements: str) -> List[str]:
        """Generate acceptance criteria for the project.

        Args:
            user_requirements: User's natural language requirements

        Returns:
            List of acceptance criteria strings
        """
        system_prompt = self.create_system_prompt(
            """You are an expert software requirements analyst.
            Generate specific, measurable, achievable, relevant, and testable (SMART)
            acceptance criteria based on user requirements.
            Return the criteria as a JSON array of strings."""
        )

        user_prompt = self.create_user_prompt(
            f"Generate acceptance criteria for:\n\n{user_requirements}"
        )

        response = self.invoke_llm([system_prompt, user_prompt])

        try:
            # Parse JSON response
            criteria = json.loads(response.content)
            if isinstance(criteria, list):
                return criteria
            # Fallback if not a list
            return [str(criteria)]
        except json.JSONDecodeError:
            # Fallback: split by newlines if JSON parsing fails
            return response.content.split("\n")

    def _generate_architecture(self, user_requirements: str) -> str:
        """Generate a high-level architecture design.

        Args:
            user_requirements: User's natural language requirements

        Returns:
            Architecture description as string
        """
        system_prompt = self.create_system_prompt(
            """You are an expert software architect.
            Design a high-level architecture for the given requirements.
            Include key components, their relationships, and technology choices.
            Format the output in markdown with clear sections."""
        )

        user_prompt = self.create_user_prompt(
            f"Design an architecture for:\n\n{user_requirements}"
        )

        response = self.invoke_llm([system_prompt, user_prompt])
        return response.content

    def _generate_tasks(self, user_requirements: str) -> List[Task]:
        """Generate a breakdown of implementation tasks.

        Args:
            user_requirements: User's natural language requirements

        Returns:
            List of Task objects
        """
        system_prompt = self.create_system_prompt(
            """You are an expert software project manager.
            Break down the project into small, testable implementation tasks.
            Each task should be specific and achievable.
            Return the tasks as a JSON array with each task having:
            - id: unique identifier (e.g., "task-1", "task-2")
            - description: clear task description
            - dependencies: array of task IDs this task depends on (empty if none)"""
        )

        user_prompt = self.create_user_prompt(
            f"Break down into implementation tasks:\n\n{user_requirements}"
        )

        response = self.invoke_llm([system_prompt, user_prompt])

        try:
            # Parse JSON response
            tasks_data = json.loads(response.content)
            if isinstance(tasks_data, list):
                tasks = []
                for task_data in tasks_data:
                    task = Task(
                        id=task_data.get("id", str(uuid.uuid4())),
                        description=task_data.get("description", ""),
                        status="pending",
                        dependencies=task_data.get("dependencies", []),
                    )
                    tasks.append(task)
                return tasks
        except (json.JSONDecodeError, Exception):
            # Fallback: create a single task
            return [
                Task(
                    id="task-1",
                    description="Implement the project based on requirements",
                    status="pending",
                    dependencies=[],
                )
            ]

        return []
