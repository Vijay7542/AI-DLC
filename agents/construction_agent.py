"""Construction Agent for Mini AI-DLC.

Handles actual source code generation based on approved execution plan.
Generates files in isolated workspace with version management, syntax validation,
and recovery support.
"""

import os
import ast
import json
import uuid
import shutil
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple
from datetime import datetime
from graph.state import (
    WorkflowState,
    Subtask,
    ExecutionPlan,
    GeneratedFile,
    FileVersion,
    TaskExecutionRecord,
)
from agents.base_agent import BaseAgent
from agents.version_manager import VersionManager
from langchain_core.messages import BaseMessage


class ConstructionAgent(BaseAgent):
    """Agent for the Construction phase of AI-DLC.

    Consumes approved execution plan and generates actual application source code.
    Features:
    - Isolated workspace for generated code
    - Task dependency tracking
    - Code version management
    - Python syntax validation
    - Recovery and resume support
    - Task-to-file mapping
    """

    def __init__(self, llm=None, use_test_config=False, workspace_root: str = "workspace", version_db: str = "version_history.db"):
        """Initialize the Construction Agent.

        Args:
            llm: Optional LLM instance for testing
            use_test_config: If True, use TestConfig
            workspace_root: Root directory for generated workspaces
            version_db: Path to version history database
        """
        super().__init__(llm=llm, use_test_config=use_test_config)
        self.workspace_root = workspace_root
        self.version_manager = VersionManager(version_db)

    def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Process the Construction phase.

        Args:
            state: Current workflow state with approved execution plan

        Returns:
            State updates with construction outputs
        """
        # Ensure execution plan is available
        execution_plan_data = state.get("execution_plan")
        if not execution_plan_data:
            raise ValueError("Construction Agent requires approved execution plan")

        # Parse execution plan
        execution_plan = ExecutionPlan(**execution_plan_data)

        # Create or get workspace
        workspace_path = state.get("workspace_path")
        if not workspace_path:
            workspace_path = self._create_workspace(state["workflow_id"])
        else:
            # Verify workspace exists for recovery
            if not os.path.exists(workspace_path):
                workspace_path = self._create_workspace(state["workflow_id"])

        # Initialize tracking structures
        task_records = state.get("task_execution_records", {})
        generated_files = state.get("generated_files", {})
        file_versions = state.get("file_versions", {})

        # Execute subtasks respecting dependencies
        errors = []
        completed_subtasks = []

        for subtask_id in execution_plan.execution_order:
            # Skip if already completed
            if subtask_id in task_records and task_records[subtask_id] is not None and task_records[subtask_id].get("status") == "completed":
                completed_subtasks.append(subtask_id)
                continue

            # Check dependencies
            subtask = next((s for s in execution_plan.subtasks if s.id == subtask_id), None)
            if not subtask:
                errors.append(f"Subtask {subtask_id} not found in execution plan")
                continue

            if not self._dependencies_satisfied(subtask, task_records):
                # Dependencies not met, skip for now
                continue

            # Execute subtask
            try:
                record = self._execute_subtask(
                    subtask,
                    execution_plan,
                    workspace_path,
                    state,
                )
                task_records[subtask_id] = record.model_dump()
                completed_subtasks.append(subtask_id)
            except Exception as e:
                errors.append(f"Subtask {subtask_id} failed: {str(e)}")
                # Record failure
                task_records[subtask_id] = {
                    "subtask_id": subtask_id,
                    "description": subtask.description,
                    "status": "failed",
                    "generated_files": [],
                    "errors": [str(e)],
                    "retry_count": 0,
                }

        result = {
            "workspace_path": workspace_path,
            "task_execution_records": task_records,
            "generated_files": generated_files,
            "file_versions": file_versions,
            "phase": "construction",
            "current_step": "construction_complete",
            "construction_status": "completed" if len(completed_subtasks) == len(execution_plan.subtasks) else "in_progress",
        }

        if errors:
            result["errors"] = errors

        return result

    def _create_workspace(self, workflow_id: str) -> str:
        """Create an isolated workspace for the project.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Path to the created workspace
        """
        workspace_path = os.path.join(self.workspace_root, f"project_{workflow_id}")
        os.makedirs(workspace_path, exist_ok=True)
        return workspace_path

    def _dependencies_satisfied(self, subtask: Subtask, task_records: Dict) -> bool:
        """Check if subtask dependencies are satisfied.

        Args:
            subtask: Subtask to check
            task_records: Dictionary of task execution records

        Returns:
            True if all dependencies are completed
        """
        for dep_id in subtask.dependencies:
            if dep_id not in task_records:
                return False
            if task_records[dep_id].get("status") != "completed":
                return False
        return True

    def _execute_subtask(
        self,
        subtask: Subtask,
        execution_plan: ExecutionPlan,
        workspace_path: str,
        state: WorkflowState,
    ) -> TaskExecutionRecord:
        """Execute a single subtask and generate code.

        Args:
            subtask: Subtask to execute
            execution_plan: Full execution plan for context
            workspace_path: Path to workspace
            state: Current workflow state

        Returns:
            Task execution record
        """
        record = TaskExecutionRecord(
            subtask_id=subtask.id,
            description=subtask.description,
            status="in_progress",
            started_at=datetime.now(),
        )

        # Generate code for this subtask
        generated_files = self._generate_code_for_subtask(
            subtask,
            execution_plan,
            workspace_path,
            state,
        )

        record.generated_files = generated_files
        record.status = "completed"
        record.completed_at = datetime.now()

        return record

    def _generate_code_for_subtask(
        self,
        subtask: Subtask,
        execution_plan: ExecutionPlan,
        workspace_path: str,
        state: WorkflowState,
    ) -> List[str]:
        """Generate code files for a subtask.

        Args:
            subtask: Subtask to generate code for
            execution_plan: Full execution plan
            workspace_path: Path to workspace
            state: Current workflow state

        Returns:
            List of generated file paths
        """
        # Get context from state
        architecture = state.get("architecture", "")
        requirements_doc = state.get("requirements_doc", "")

        system_prompt = self.create_system_prompt(
            """You are an expert software developer.
            Generate production-ready Python source code based on the given task description and architecture.
            
            Rules:
            - Generate complete, functional code
            - Follow Python best practices
            - Include necessary imports
            - Use type hints where appropriate
            - Write clear, maintainable code
            - Return the code in a structured JSON format with file paths as keys and code as values
            
            Example response:
            {
                "app/models/user.py": "# User model code...",
                "app/services/auth.py": "# Auth service code..."
            }
            
            Only generate the files necessary for this specific task.
            Do not include markdown code fences.
            Return only the JSON object."""
        )

        user_prompt = self.create_user_prompt(
            f"""Generate code for the following task:

Task: {subtask.description}
Priority: {subtask.priority}
Complexity: {subtask.complexity}

Architecture Context:
{architecture[:1000]}...

Requirements Context:
{requirements_doc[:1000]}...

Generate the necessary Python files to implement this task.
Return the result as a JSON object with file paths as keys and source code as values."""
        )

        response = self.invoke_llm([system_prompt, user_prompt])

        # Parse and validate response
        generated_files = self._parse_and_save_code(
            response.content,
            workspace_path,
            subtask.id,
        )

        return generated_files

    def _parse_and_save_code(
        self,
        response_content: str,
        workspace_path: str,
        subtask_id: str,
    ) -> List[str]:
        """Parse LLM response and save code files.

        Args:
            response_content: LLM response content
            workspace_path: Path to workspace
            subtask_id: Subtask ID for tracking

        Returns:
            List of generated file paths
        """
        generated_files = []

        try:
            # Try to parse as JSON
            code_files = json.loads(response_content)

            if not isinstance(code_files, dict):
                raise ValueError("Response is not a dictionary")

            for file_path, code_content in code_files.items():
                # Validate file path (prevent path traversal)
                if not self._is_safe_path(file_path):
                    raise ValueError(f"Unsafe file path: {file_path}")

                # Create directory structure
                full_path = os.path.join(workspace_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Validate syntax if Python file
                is_valid = True
                if file_path.endswith(".py"):
                    is_valid = self._validate_python_syntax(code_content)

                # Save file with version tracking
                self._save_file_with_version(
                    full_path,
                    code_content,
                    subtask_id,
                    is_valid,
                    description=f"Initial generation for subtask {subtask_id}",
                )

                generated_files.append(file_path)

        except json.JSONDecodeError:
            # Fallback: try to extract code from markdown
            generated_files = self._extract_code_from_markdown(
                response_content,
                workspace_path,
                subtask_id,
            )

        return generated_files

    def _is_safe_path(self, file_path: str) -> bool:
        """Validate that file path is safe (no path traversal).

        Args:
            file_path: File path to validate

        Returns:
            True if path is safe
        """
        # Normalize path
        normalized = os.path.normpath(file_path)

        # Check for path traversal attempts
        if ".." in normalized:
            return False

        # Check for absolute paths (both Unix and Windows style)
        if os.path.isabs(file_path) or file_path.startswith("/") or (len(file_path) > 1 and file_path[1] == ":"):
            return False

        return True

    def _validate_python_syntax(self, code: str) -> bool:
        """Validate Python syntax using AST parsing.

        Args:
            code: Python code to validate

        Returns:
            True if syntax is valid
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _save_file_with_version(
        self,
        file_path: str,
        content: str,
        subtask_id: str,
        syntax_valid: bool,
        description: str = "",
    ):
        """Save file with version tracking.

        Args:
            file_path: Full path to file
            content: File content
            subtask_id: Subtask ID generating this file
            syntax_valid: Whether syntax is valid
            description: Description of changes
        """
        # Get relative path for version tracking
        relative_path = os.path.relpath(file_path, self.workspace_root)

        # Get current version number
        latest_version = self.version_manager.get_latest_version(relative_path)
        next_version = (latest_version.version + 1) if latest_version else 1

        # Save version to database
        self.version_manager.save_version(
            file_path=relative_path,
            content=content,
            version=next_version,
            generated_by=subtask_id,
            description=description,
            syntax_valid=syntax_valid,
        )

        # Write new content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _extract_code_from_markdown(
        self,
        content: str,
        workspace_path: str,
        subtask_id: str,
    ) -> List[str]:
        """Extract code from markdown code fences as fallback.

        Args:
            content: Markdown content
            workspace_path: Path to workspace
            subtask_id: Subtask ID

        Returns:
            List of generated file paths
        """
        # Simple fallback: save as single file
        file_path = f"generated_{subtask_id}.py"
        full_path = os.path.join(workspace_path, file_path)

        # Remove markdown code fences if present
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned_content = "\n".join(lines)

        # Validate and save
        is_valid = self._validate_python_syntax(cleaned_content)
        self._save_file_with_version(full_path, cleaned_content, subtask_id, is_valid)

        return [file_path]

    def apply_corrections(
        self,
        bug_reports: List,
        state: WorkflowState,
    ) -> Dict[str, Any]:
        """Apply code corrections based on bug reports.

        Args:
            bug_reports: List of bug reports from Testing Agent
            state: Current workflow state

        Returns:
            State updates with corrected files
        """
        workspace_path = state.get("workspace_path")
        if not workspace_path:
            raise ValueError("Construction Agent requires workspace for corrections")

        architecture = state.get("architecture", "")
        requirements_doc = state.get("requirements_doc", "")

        corrected_files = []
        correction_errors = []

        for bug in bug_reports:
            failure_type = bug.get("failure_type")
            file_path = bug.get("file_path")

            if not file_path:
                continue

            full_path = os.path.join(workspace_path, file_path)
            if not os.path.exists(full_path):
                continue

            # Get relative path for version tracking
            relative_path = os.path.relpath(full_path, workspace_path)

            # Get the last known working version (if any)
            working_version = self.version_manager.get_working_version(relative_path)

            # Read current content
            with open(full_path, "r", encoding="utf-8") as f:
                current_content = f.read()

            # Generate corrected code based on failure type
            corrected_code = self._generate_correction(
                current_content,
                bug.get("error_message", ""),
                bug.get("stack_trace", ""),
                failure_type,
                architecture,
                requirements_doc,
            )

            # Validate syntax
            syntax_valid = self._validate_python_syntax(corrected_code)

            # Save corrected version
            self._save_file_with_version(
                full_path,
                corrected_code,
                "correction",
                syntax_valid,
                description=f"Correction for {failure_type}: {bug.get('error_message', '')[:50]}",
            )

            corrected_files.append(file_path)

        result = {
            "corrected_files": corrected_files,
            "correction_errors": correction_errors,
        }

        return result

    def rollback_file(self, file_path: str, version: int, reason: str) -> bool:
        """Rollback a file to a specific version.

        Args:
            file_path: Relative path to the file
            version: Version to rollback to
            reason: Reason for rollback

        Returns:
            True if rollback succeeded
        """
        full_path = os.path.join(self.workspace_root, file_path)

        # Get the version to rollback to
        target_version = self.version_manager.get_version(file_path, version)
        if not target_version:
            return False

        # Get current version
        current_version = self.version_manager.get_latest_version(file_path)
        if not current_version:
            return False

        # Record rollback event
        self.version_manager.record_rollback(
            file_path=file_path,
            from_version=current_version.version,
            to_version=version,
            reason=reason,
        )

        # Restore the file content
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(target_version.content)

        return True

    def _generate_correction(
        self,
        current_code: str,
        error_message: str,
        stack_trace: str,
        failure_type: str,
        architecture: str,
        requirements_doc: str,
    ) -> str:
        """Generate corrected code based on failure type.

        Args:
            current_code: Current code with error
            error_message: Error message from test failure
            stack_trace: Stack trace if available
            failure_type: Type of failure (syntax_error, runtime_error, etc.)
            architecture: Application architecture
            requirements_doc: Requirements document

        Returns:
            Corrected code
        """
        # Generate appropriate prompt based on failure type
        if failure_type == "syntax_error":
            system_prompt = self.create_system_prompt(
                """You are an expert software developer and debugger.
                Given Python code with a syntax error and the error message, fix the syntax error.
                Preserve the original logic and intent.
                Return only the corrected code, no explanations."""
            )
            user_prompt = f"""Fix the syntax error in this Python code:

Current code:
{current_code}

Error message:
{error_message}

Architecture context:
{architecture[:500] if architecture else 'N/A'}...

Requirements context:
{requirements_doc[:500] if requirements_doc else 'N/A'}...

Return only the corrected Python code, no explanations."""

        elif failure_type in ["runtime_error", "logical_error"]:
            system_prompt = self.create_system_prompt(
                """You are an expert software developer and debugger.
                Given Python code with a runtime or logical error, fix the bug.
                Preserve the original logic and intent.
                Return only the corrected code, no explanations."""
            )
            user_prompt = f"""Fix the bug in this Python code:

Current code:
{current_code}

Error message:
{error_message}

Stack trace:
{stack_trace}

Architecture context:
{architecture[:500] if architecture else 'N/A'}...

Requirements context:
{requirements_doc[:500] if requirements_doc else 'N/A'}...

Return only the corrected Python code, no explanations."""

        elif failure_type == "dependency_error":
            system_prompt = self.create_system_prompt(
                """You are an expert software developer.
                Given Python code with a missing import or dependency error, fix the import.
                Add the necessary import statement at the top of the file.
                Return only the corrected code, no explanations."""
            )
            user_prompt = f"""Fix the dependency error in this Python code:

Current code:
{current_code}

Error message:
{error_message}

Stack trace:
{stack_trace}

Return only the corrected Python code, no explanations."""

        else:
            # Default: generic correction
            system_prompt = self.create_system_prompt(
                """You are an expert software developer.
                Fix the error in this Python code.
                Preserve the original logic and intent.
                Return only the corrected code, no explanations."""
            )
            user_prompt = f"""Fix the error in this Python code:

Current code:
{current_code}

Error message:
{error_message}

Stack trace:
{stack_trace}

Return only the corrected Python code, no explanations."""

        response = self.invoke_llm([system_prompt, user_prompt])

        # Remove markdown code fences if present
        content = response.content
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines)

        return content if content else current_code
