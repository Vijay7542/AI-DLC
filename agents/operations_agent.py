"""Operations Agent for Mini AI-DLC.

Handles build management, deployment configuration, Docker image building,
deployment to staging, health checks, and rollback.
"""

import os
import json
import uuid
import subprocess
from typing import Any, List, Dict, Optional
from datetime import datetime
from graph.state import (
    WorkflowState,
    DeploymentConfig,
    BuildReport,
    DeploymentReport,
    HealthCheckResult,
    RollbackReport,
)
from agents.base_agent import BaseAgent
from agents.docker_utils import convert_path_for_docker, check_docker_ready
from langchain_core.messages import BaseMessage


class OperationsAgent(BaseAgent):
    """Agent for the Operations phase of AI-DLC.

    Handles:
    - Build management
    - Deployment configuration generation
    - Docker image building
    - Deployment to local/staging
    - Health checks
    - Rollback
    """

    def __init__(self, llm=None, use_test_config=False, max_rollbacks: int = 3):
        """Initialize the Operations Agent.

        Args:
            llm: Optional LLM instance for testing
            use_test_config: If True, use TestConfig
            max_rollbacks: Maximum number of rollback attempts
        """
        super().__init__(llm=llm, use_test_config=use_test_config)
        self.max_rollbacks = max_rollbacks

    def process(self, state: WorkflowState) -> Dict[str, Any]:
        """Process the Operations phase.

        Args:
            state: Current workflow state with tested application

        Returns:
            State updates with operations outputs
        """
        workspace_path = state.get("workspace_path")
        if not workspace_path:
            raise ValueError("Operations Agent requires constructed application")

        # Check if Docker is available
        if not check_docker_ready():
            return {
                "operations_status": "docker_unavailable",
                "phase": "operations",
                "current_step": "operations_complete",
                "errors": ["Docker not available - cannot perform operations"],
            }

        # Generate deployment configuration
        deployment_config = self._generate_deployment_config(state)

        # Build Docker image
        build_report = self._build_docker_image(workspace_path, deployment_config)

        # If build failed, return error
        if build_report.status == "failed":
            return {
                "deployment_config": deployment_config.model_dump(),
                "build_report": build_report.model_dump(),
                "operations_status": "failed",
                "phase": "operations",
                "current_step": "operations_complete",
            }

        # Request deployment approval
        result = {
            "deployment_config": deployment_config.model_dump(),
            "build_report": build_report.model_dump(),
            "deployment_approval_needed": True,
            "deployment_approval_status": "pending",
            "operations_status": "in_progress",
            "phase": "operations",
            "current_step": "awaiting_deployment_approval",
        }

        return result

    def _generate_deployment_config(self, state: WorkflowState) -> DeploymentConfig:
        """Generate deployment configuration.

        Args:
            state: Current workflow state

        Returns:
            Deployment configuration
        """
        workflow_id = state["workflow_id"]
        architecture = state.get("architecture", "")

        # Generate Dockerfile and docker-compose.yml using LLM
        dockerfile_content = self._generate_dockerfile(architecture)
        docker_compose_content = self._generate_docker_compose()

        # Save to workspace
        workspace_path = state["workspace_path"]
        with open(os.path.join(workspace_path, "Dockerfile"), "w") as f:
            f.write(dockerfile_content)
        with open(os.path.join(workspace_path, "docker-compose.yml"), "w") as f:
            f.write(docker_compose_content)

        return DeploymentConfig(
            environment="staging",
            docker_image_name=f"mini-ai-dlc-{workflow_id}",
            docker_image_tag="latest",
            port=8000,
            environment_variables={
                "ENV": "staging",
                "PORT": "8000",
            },
            health_check_path="/health",
        )

    def _generate_dockerfile(self, architecture: str) -> str:
        """Generate Dockerfile for the application.

        Args:
            architecture: Application architecture description

        Returns:
            Dockerfile content
        """
        system_prompt = self.create_system_prompt(
            """You are a DevOps expert.
            Generate a production-ready Dockerfile for a Python application.
            
            The Dockerfile should:
            - Use python:3.14-slim as base image
            - Set working directory to /app
            - Copy requirements.txt and install dependencies
            - Copy application code
            - Expose port 8000
            - Run the application with python main.py or similar
            
            Return only the Dockerfile content, no markdown code fences."""
        )

        user_prompt = self.create_user_prompt(
            f"Generate a Dockerfile for the following application:\n\n{architecture[:1000]}..."
        )

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

        return content if content else self._get_default_dockerfile()

    def _get_default_dockerfile(self) -> str:
        """Get default Dockerfile as fallback.

        Returns:
            Default Dockerfile content
        """
        return """FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
"""

    def _generate_docker_compose(self) -> str:
        """Generate docker-compose.yml.

        Returns:
            docker-compose.yml content
        """
        return """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=staging
      - PORT=8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
"""

    def _build_docker_image(self, workspace_path: str, config: DeploymentConfig) -> BuildReport:
        """Build Docker image for the application.

        Args:
            workspace_path: Path to workspace
            config: Deployment configuration

        Returns:
            Build report
        """
        build_report = BuildReport(
            build_id=f"build-{uuid.uuid4()}",
            status="building",
            started_at=datetime.now(),
        )

        try:
            # Convert workspace path to Docker-compatible format
            docker_workspace_path = convert_path_for_docker(workspace_path)
            
            result = subprocess.run(
                [
                    "docker", "build",
                    "-t", f"{config.docker_image_name}:{config.docker_image_tag}",
                    docker_workspace_path
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            build_report.completed_at = datetime.now()
            build_report.build_time = (build_report.completed_at - build_report.started_at).total_seconds()
            build_report.build_logs = result.stdout.split("\n")[:100]  # Limit log size

            if result.returncode == 0:
                build_report.status = "success"
                # Get image ID
                try:
                    inspect_result = subprocess.run(
                        ["docker", "inspect", f"{config.docker_image_name}:{config.docker_image_tag}"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if inspect_result.returncode == 0:
                        inspect_data = json.loads(inspect_result.stdout)
                        build_report.docker_image_id = inspect_data[0].get("Id", "")
                except Exception:
                    pass
            else:
                build_report.status = "failed"
                build_report.errors = result.stderr.split("\n")[:20]

        except subprocess.TimeoutExpired:
            build_report.status = "failed"
            build_report.completed_at = datetime.now()
            build_report.errors = ["Build timeout"]
        except Exception as e:
            build_report.status = "failed"
            build_report.completed_at = datetime.now()
            build_report.errors = [str(e)]

        return build_report

    def deploy_application(self, state: WorkflowState) -> Dict[str, Any]:
        """Deploy the application to staging.

        Args:
            state: Current workflow state

        Returns:
            State updates with deployment report
        """
        workspace_path = state.get("workspace_path")
        deployment_config_data = state.get("deployment_config")
        if not deployment_config_data:
            raise ValueError("Deployment config not found")

        deployment_config = DeploymentConfig(**deployment_config_data)

        deployment_report = self._deploy_container(workspace_path, deployment_config)

        # Perform health check
        health_check = self._perform_health_check(deployment_report)

        result = {
            "deployment_report": deployment_report.model_dump(),
            "health_check_result": health_check.model_dump(),
            "operations_status": "completed" if health_check.status == "healthy" else "failed",
            "phase": "operations",
            "current_step": "operations_complete",
        }

        return result

    def _deploy_container(self, workspace_path: str, config: DeploymentConfig) -> DeploymentReport:
        """Deploy Docker container.

        Args:
            workspace_path: Path to workspace
            config: Deployment configuration

        Returns:
            Deployment report
        """
        deployment_report = DeploymentReport(
            deployment_id=f"deploy-{uuid.uuid4()}",
            environment=config.environment,
            status="deploying",
            started_at=datetime.now(),
        )

        try:
            # Stop existing container if running
            subprocess.run(
                ["docker", "stop", config.docker_image_name],
                capture_output=True,
                timeout=30,
            )
            subprocess.run(
                ["docker", "rm", config.docker_image_name],
                capture_output=True,
                timeout=30,
            )
        except Exception:
            pass  # Container may not exist

        try:
            result = subprocess.run(
                [
                    "docker", "run", "-d",
                    "--name", config.docker_image_name,
                    "-p", f"{config.port}:{config.port}",
                    "-e", f"ENV={config.environment}",
                    f"{config.docker_image_name}:{config.docker_image_tag}"
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            deployment_report.completed_at = datetime.now()
            deployment_report.deployment_time = (deployment_report.completed_at - deployment_report.started_at).total_seconds()
            deployment_report.deployment_logs = result.stdout.split("\n")[:50]

            if result.returncode == 0:
                deployment_report.status = "success"
                deployment_report.container_id = result.stdout.strip()
            else:
                deployment_report.status = "failed"
                deployment_report.errors = result.stderr.split("\n")[:20]

        except subprocess.TimeoutExpired:
            deployment_report.status = "failed"
            deployment_report.completed_at = datetime.now()
            deployment_report.errors = ["Deployment timeout"]
        except Exception as e:
            deployment_report.status = "failed"
            deployment_report.completed_at = datetime.now()
            deployment_report.errors = [str(e)]

        return deployment_report

    def _perform_health_check(self, deployment_report: DeploymentReport) -> HealthCheckResult:
        """Perform health check on deployed application.

        Args:
            deployment_report: Deployment report

        Returns:
            Health check result
        """
        health_check = HealthCheckResult(
            check_id=f"health-{uuid.uuid4()}",
            deployment_id=deployment_report.deployment_id,
            status="unknown",
        )

        if deployment_report.status != "success" or not deployment_report.container_id:
            health_check.status = "unhealthy"
            health_check.error_message = "Deployment failed or no container ID"
            return health_check

        try:
            result = subprocess.run(
                ["docker", "inspect", "--format={{.State.Health.Status}}", deployment_report.container_id],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if "healthy" in result.stdout.lower():
                health_check.status = "healthy"
            else:
                health_check.status = "unhealthy"
                health_check.error_message = f"Container health: {result.stdout.strip()}"

        except Exception as e:
            health_check.status = "unhealthy"
            health_check.error_message = str(e)

        return health_check

    def rollback_deployment(self, state: WorkflowState) -> Dict[str, Any]:
        """Rollback to previous deployment.

        Args:
            state: Current workflow state

        Returns:
            State updates with rollback report
        """
        # Placeholder implementation
        # In full implementation, this would:
        # 1. Identify previous successful deployment
        # 2. Stop current container
        # 3. Start previous container
        # 4. Verify health

        rollback_report = RollbackReport(
            rollback_id=f"rollback-{uuid.uuid4()}",
            deployment_id="placeholder",
            previous_deployment_id="placeholder",
            status="failed",
            errors=["Rollback not implemented"],
        )

        return {
            "rollback_report": rollback_report.model_dump(),
            "operations_status": "failed",
        }
