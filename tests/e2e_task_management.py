"""End-to-end test for Mini AI-DLC with Task Management application.

This test demonstrates the complete workflow from requirements through deployment.
Uses real Groq API and real Docker operations.
"""

import sys
sys.path.insert(0, '.')

import os
import time
from graph.workflow import run_workflow, resume_workflow, get_workflow_state
from agents.inception_agent import InceptionAgent
from agents.planning_agent import PlanningAgent
from agents.construction_agent import ConstructionAgent
from agents.testing_agent import TestingAgent
from agents.operations_agent import OperationsAgent


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def main():
    """Run end-to-end test with Task Management application."""
    
    # 1. Input requirement
    print_section("STEP 1: SUBMIT REQUIREMENT")
    
    requirements = """
Build a simple Task Management application with the following features:

1. Add tasks with title and description
2. Mark tasks as complete
3. Delete tasks
4. List all tasks
5. Store tasks in memory (no database required for now)

The application should have a simple REST API with endpoints for each operation.
Use Python and Flask for implementation.
"""
    
    print(f"Requirements:\n{requirements}")
    
    # 2. Run workflow to approval checkpoint
    print_section("STEP 2: RUN WORKFLOW TO APPROVAL CHECKPOINT")
    print("This will make 4 LLM calls to Groq API...")
    
    start_time = time.time()
    result, thread_id = run_workflow(requirements, checkpoint_path="e2e_checkpoints.db")
    inception_time = time.time() - start_time
    
    print(f"\nWorkflow paused at approval checkpoint")
    print(f"Thread ID: {thread_id}")
    print(f"Inception Time: {inception_time:.2f}s")
    print(f"Current Step: {result['current_step']}")
    print(f"Approval Needed: {result['human_approval_needed']}")
    print(f"Approval Status: {result['approval_status']}")
    
    # 3. Inspect generated outputs
    print_section("STEP 3: INSPECT GENERATED OUTPUTS")
    
    print(f"\nRequirements Doc: {len(result['requirements_doc']) if result['requirements_doc'] else 0} chars")
    if result['requirements_doc']:
        preview = result['requirements_doc'][:200].encode('ascii', 'ignore').decode('ascii')
        print(f"Preview: {preview}...")
    
    print(f"\nAcceptance Criteria: {len(result['acceptance_criteria']) if result['acceptance_criteria'] else 0} items")
    if result['acceptance_criteria']:
        for i, criterion in enumerate(result['acceptance_criteria'][:3], 1):
            criterion_str = str(criterion).encode('ascii', 'ignore').decode('ascii')
            print(f"  {i}. {criterion_str}")
    
    print(f"\nArchitecture: {len(result['architecture']) if result['architecture'] else 0} chars")
    if result['architecture']:
        preview = result['architecture'][:200].encode('ascii', 'ignore').decode('ascii')
        print(f"Preview: {preview}...")
    
    print(f"\nTasks: {len(result['tasks']) if result['tasks'] else 0} items")
    if result['tasks']:
        for i, task in enumerate(result['tasks'][:3], 1):
            desc = str(task.description).encode('ascii', 'ignore').decode('ascii')
            print(f"  {i}. {desc}")
    
    # 4. Resume with approval
    print_section("STEP 4: RESUME WITH APPROVAL")
    print("Approving workflow to continue through Planning, Construction, Testing, and Operations...")
    
    start_time = time.time()
    final_result = resume_workflow(thread_id, "approved", checkpoint_path="e2e_checkpoints.db")
    full_workflow_time = time.time() - start_time
    
    print(f"\nWorkflow completed")
    print(f"Full Workflow Time: {full_workflow_time:.2f}s")
    print(f"Final Phase: {final_result['phase']}")
    print(f"Final Step: {final_result['current_step']}")
    
    # 5. Inspect Planning outputs
    print_section("STEP 5: INSPECT PLANNING OUTPUTS")
    
    execution_plan = final_result.get('execution_plan')
    if execution_plan:
        print(f"Subtasks: {len(execution_plan.get('subtasks', []))}")
        print(f"Execution Order: {execution_plan.get('execution_order', [])[:5]}...")
        print(f"Parallel Groups: {list(execution_plan.get('parallel_groups', {}).keys())}")
        print(f"Total Estimated Hours: {execution_plan.get('total_estimated_hours')}")
    
    # 6. Inspect Construction outputs
    print_section("STEP 6: INSPECT CONSTRUCTION OUTPUTS")
    
    workspace_path = final_result.get('workspace_path')
    print(f"Workspace Path: {workspace_path}")
    
    if workspace_path and os.path.exists(workspace_path):
        print(f"\nGenerated Files:")
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, workspace_path)
                print(f"  - {rel_path}")
    
    task_records = final_result.get('task_execution_records', {})
    print(f"\nTask Execution Records: {len(task_records)}")
    completed = sum(1 for r in task_records.values() if r.get('status') == 'completed')
    print(f"Completed Tasks: {completed}/{len(task_records)}")
    
    # 7. Inspect Testing outputs
    print_section("STEP 7: INSPECT TESTING OUTPUTS")
    
    testing_status = final_result.get('testing_status')
    print(f"Testing Status: {testing_status}")
    
    test_report = final_result.get('test_report')
    if test_report:
        print(f"Total Tests: {test_report.get('total_tests')}")
        print(f"Passed: {test_report.get('passed_tests')}")
        print(f"Failed: {test_report.get('failed_tests')}")
        print(f"Skipped: {test_report.get('skipped_tests')}")
        
        bug_reports = test_report.get('bug_reports', [])
        print(f"Bug Reports: {len(bug_reports)}")
        if bug_reports:
            for bug in bug_reports[:3]:
                print(f"  - {bug.get('failure_type')}: {bug.get('error_message', '')[:100]}")
    
    correction_count = final_result.get('correction_retry_count', 0)
    print(f"Correction Attempts: {correction_count}")
    
    # 8. Inspect Operations outputs
    print_section("STEP 8: INSPECT OPERATIONS OUTPUTS")
    
    operations_status = final_result.get('operations_status')
    print(f"Operations Status: {operations_status}")
    
    build_report = final_result.get('build_report')
    if build_report:
        print(f"Build Status: {build_report.get('status')}")
        print(f"Build Time: {build_report.get('build_time')}s")
        print(f"Docker Image ID: {build_report.get('docker_image_id', '')[:20]}...")
    
    deployment_report = final_result.get('deployment_report')
    if deployment_report:
        print(f"Deployment Status: {deployment_report.get('status')}")
        print(f"Container ID: {deployment_report.get('container_id', '')[:20]}...")
    
    health_check = final_result.get('health_check_result')
    if health_check:
        print(f"Health Status: {health_check.get('status')}")
        print(f"Error Message: {health_check.get('error_message', 'N/A')}")
    
    # 9. Summary
    print_section("STEP 9: SUMMARY")
    
    print(f"\nWorkflow ID: {thread_id}")
    print(f"Total Time: {inception_time + full_workflow_time:.2f}s")
    print(f"\nPhase Completion:")
    print(f"  Inception: ✓")
    print(f"  Approval: ✓")
    print(f"  Planning: ✓" if execution_plan else "  Planning: ✗")
    print(f"  Construction: ✓" if workspace_path else "  Construction: ✗")
    print(f"  Testing: ✓" if testing_status else "  Testing: ✗")
    print(f"  Operations: ✓" if operations_status else "  Operations: ✗")
    
    print(f"\nFunctionality Status:")
    print(f"  Requirements Generation: ✓")
    print(f"  Task Decomposition: ✓")
    print(f"  File Generation: ✓" if workspace_path else "  File Generation: ✗")
    print(f"  Test Execution: ✓" if testing_status == 'completed' else f"  Test Execution: {testing_status}")
    print(f"  Docker Build: ✓" if build_report and build_report.get('status') == 'success' else "  Docker Build: ✗")
    print(f"  Container Deployment: ✓" if deployment_report and deployment_report.get('status') == 'success' else "  Container Deployment: ✗")
    print(f"  Health Check: ✓" if health_check and health_check.get('status') == 'healthy' else "  Health Check: ✗")
    print(f"  Code Correction: ✗ (placeholder)")
    print(f"  Rollback: ✗ (placeholder)")
    
    print("\n" + "=" * 80)
    print("  END-TO-END TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
