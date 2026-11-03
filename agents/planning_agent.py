"""Planning Agent for Mini AI-DLC.

Handles detailed execution planning based on approved inception outputs.
Breaks down high-level tasks into actionable subtasks with dependencies,
priorities, and execution order.
"""

import json
import uuid
from typing import Any, List, Dict
from graph.state import WorkflowState, Task, Subtask, ExecutionPlan
from agents.base_agent import BaseAgent
from langchain_core.messages import BaseMessage


class PlanningAgent(BaseAgent):
    """Agent for the Planning phase of AI-DLC.

    Consumes human-approved inception outputs and generates:
    - Detailed subtasks for each high-level task
    - Task dependencies and execution order
    - Parallel execution groups
    - Priority and complexity assignments
    - Technical dependencies and blockers
    - Structured execution plan
    """

    def __init__(self, llm=None, use_test_config=False):
        """Initialize the Planning Agent."""
        super().__init__(llm=llm, use_test_config=use_test_config)

    def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Process the Planning phase.

        Args:
            state: Current workflow state with approved inception outputs

        Returns:
            State updates with planning outputs
        """
        # Ensure inception outputs are available and approved
        if state.get("approval_status") != "approved":
            raise ValueError("Planning Agent requires approved inception outputs")

        requirements_doc = state.get("requirements_doc")
        acceptance_criteria = state.get("acceptance_criteria")
        architecture = state.get("architecture")
        tasks = state.get("tasks")

        # Convert tasks from dicts to Task objects (workflow state uses dicts for serialization)
        if tasks and isinstance(tasks, list) and len(tasks) > 0:
            tasks = [Task(**task) if isinstance(task, dict) else task for task in tasks if task]

        if not all([requirements_doc, acceptance_criteria, architecture, tasks]):
            raise ValueError("Missing required inception outputs")

        # Generate execution plan with error handling
        errors = []

        try:
            execution_plan = self._generate_execution_plan(
                requirements_doc, acceptance_criteria, architecture, tasks
            )
        except Exception as e:
            execution_plan = None
            errors.append(f"Execution plan generation failed: {str(e)}")

        result = {
            "execution_plan": execution_plan.model_dump() if execution_plan else None,
            "phase": "planning",
            "current_step": "planning_complete",
        }

        if errors:
            result["errors"] = errors

        return result

    def _generate_execution_plan(
        self,
        requirements_doc: str,
        acceptance_criteria: List[str],
        architecture: str,
        tasks: List[Task],
    ) -> ExecutionPlan:
        """Generate a structured execution plan.

        Args:
            requirements_doc: Approved requirements document
            acceptance_criteria: Approved acceptance criteria
            architecture: Approved system architecture
            tasks: High-level tasks from inception

        Returns:
            Structured ExecutionPlan object
        """
        # Convert tasks to dict for LLM context
        tasks_context = [
            {
                "id": task.id,
                "description": task.description,
                "dependencies": task.dependencies,
            }
            for task in tasks
        ]

        system_prompt = self.create_system_prompt(
            """You are an expert software project planner and technical lead.
            Your task is to break down high-level implementation tasks into detailed,
            actionable subtasks with proper dependencies, priorities, and execution order.

            For each subtask, provide:
            - A detailed description of what needs to be done
            - Priority level (low, medium, high, critical)
            - Complexity level (simple, moderate, complex, very_complex)
            - Estimated effort in hours
            - Dependencies on other subtasks (by subtask ID)
            - Parallel group ID if this can run in parallel with other subtasks
            - Any blockers or technical dependencies

            Also provide:
            - Execution order (ordered list of subtask IDs)
            - Parallel groups (groups of subtask IDs that can run in parallel)
            - Critical path (subtasks that determine minimum project duration)
            - Total estimated hours
            - Technical dependencies that need to be resolved

            Return the entire plan as a JSON object with the following structure:
            {
                "subtasks": [
                    {
                        "id": "subtask-1",
                        "parent_task_id": "task-1",
                        "description": "Detailed description",
                        "priority": "high",
                        "complexity": "moderate",
                        "estimated_hours": 4.0,
                        "dependencies": [],
                        "parallel_group": "group-a",
                        "blockers": []
                    }
                ],
                "execution_order": ["subtask-1", "subtask-2", ...],
                "parallel_groups": {
                    "group-a": ["subtask-1", "subtask-2"],
                    "group-b": ["subtask-3", "subtask-4"]
                },
                "critical_path": ["subtask-1", "subtask-5", ...],
                "total_estimated_hours": 40.0,
                "technical_dependencies": ["dependency-1", "dependency-2"]
            }"""
        )

        user_prompt = self.create_user_prompt(
            f"""Generate a detailed execution plan for the following project:

REQUIREMENTS:
{requirements_doc[:2000]}...

ACCEPTANCE CRITERIA:
{json.dumps(acceptance_criteria, indent=2)}

ARCHITECTURE:
{architecture[:2000]}...

HIGH-LEVEL TASKS:
{json.dumps(tasks_context, indent=2)}

Break down each high-level task into 2-5 detailed subtasks.
Ensure dependencies are correctly identified.
Identify which subtasks can run in parallel.
Prioritize critical path items."""
        )

        response = self.invoke_llm([system_prompt, user_prompt])

        try:
            plan_data = json.loads(response.content)
            return self._parse_execution_plan(plan_data, tasks)
        except json.JSONDecodeError:
            # Fallback: create a simple plan
            return self._create_fallback_plan(tasks)

    def _parse_execution_plan(
        self, plan_data: Dict, high_level_tasks: List[Task]
    ) -> ExecutionPlan:
        """Parse LLM response into ExecutionPlan object.

        Args:
            plan_data: Raw JSON data from LLM
            high_level_tasks: Original high-level tasks for reference

        Returns:
            Parsed ExecutionPlan object
        """
        subtasks = []
        for subtask_data in plan_data.get("subtasks", []):
            subtask = Subtask(
                id=subtask_data.get("id", f"subtask-{uuid.uuid4()}"),
                parent_task_id=subtask_data.get("parent_task_id", ""),
                description=subtask_data.get("description", ""),
                priority=subtask_data.get("priority", "medium"),
                complexity=subtask_data.get("complexity", "moderate"),
                estimated_hours=subtask_data.get("estimated_hours"),
                dependencies=subtask_data.get("dependencies", []),
                parallel_group=subtask_data.get("parallel_group"),
                blockers=subtask_data.get("blockers", []),
            )
            subtasks.append(subtask)

        return ExecutionPlan(
            subtasks=subtasks,
            execution_order=plan_data.get("execution_order", []),
            parallel_groups=plan_data.get("parallel_groups", {}),
            critical_path=plan_data.get("critical_path", []),
            total_estimated_hours=plan_data.get("total_estimated_hours"),
            technical_dependencies=plan_data.get("technical_dependencies", []),
        )

    def _create_fallback_plan(self, high_level_tasks: List[Task]) -> ExecutionPlan:
        """Create a simple fallback execution plan.

        Args:
            high_level_tasks: High-level tasks to break down

        Returns:
            Simple ExecutionPlan object
        """
        subtasks = []
        execution_order = []
        total_hours = 0.0

        for i, task in enumerate(high_level_tasks):
            subtask_id = f"subtask-{i+1}"
            estimated_hours = 4.0  # Default estimate

            subtask = Subtask(
                id=subtask_id,
                parent_task_id=task.id,
                description=f"Implement: {task.description}",
                priority="medium",
                complexity="moderate",
                estimated_hours=estimated_hours,
                dependencies=[],
                parallel_group=None,
                blockers=[],
            )
            subtasks.append(subtask)
            execution_order.append(subtask_id)
            total_hours += estimated_hours

        return ExecutionPlan(
            subtasks=subtasks,
            execution_order=execution_order,
            parallel_groups={},
            critical_path=execution_order,
            total_estimated_hours=total_hours,
            technical_dependencies=[],
        )
