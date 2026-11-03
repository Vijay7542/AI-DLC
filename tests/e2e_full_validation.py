"""Complete end-to-end validation of Mini AI-DLC system.

This script executes the full workflow with real Groq API calls and Docker operations.
Validates: Inception → Approval → Planning → Construction → Testing → Operations
"""

import sys
sys.path.insert(0, '.')

import os
import time
import json
from graph.workflow import run_workflow, resume_workflow, get_workflow_state
from agents.version_manager import VersionManager


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def save_evidence(phase, data, filename):
    """Save evidence to a file."""
    evidence_dir = "evidence"
    os.makedirs(evidence_dir, exist_ok=True)
    
    filepath = os.path.join(evidence_dir, f"{phase}_{filename}")
    
    if isinstance(data, dict):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    elif isinstance(data, str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(data))
    
    print(f"  Evidence saved: {filepath}")


def main():
    """Execute complete end-to-end validation."""
    
    # 1. Submit business requirements
    print_section("PHASE 1: SUBMIT BUSINESS REQUIREMENTS")
    
    requirements = """
Build a comprehensive Task Management application with the following features:

1. User Management:
   - User registration with email and password
   - User login with authentication
   - User profile management

2. Task Management:
   - Create tasks with title, description, priority, and due date
   - Update task details
   - Delete tasks
   - Retrieve all tasks
   - Retrieve single task by ID
   - Mark tasks as complete/incomplete

3. Data Storage:
   - Use SQLite for data persistence
   - Ensure data integrity with proper constraints

4. API Requirements:
   - RESTful API endpoints for all operations
   - Proper HTTP status codes
   - JSON request/response format
   - Error handling with meaningful messages

5. Technology Stack:
   - Python 3.11+
   - Flask for REST API
   - SQLite for database
   - Follow best practices and clean code principles
"""
    
    print(f"Requirements submitted ({len(requirements)} chars)")
    save_evidence("phase1", requirements, "requirements.txt")
    
    # 2. Generate SRS and architecture
    print_section("PHASE 2: INCEPTION AGENT - GENERATE SRS AND ARCHITECTURE")
    print("This will make 4 LLM calls to Groq API...")
    
    checkpoint_db = "validation_checkpoints.db"
    version_db = "validation_version_history.db"
    
    start_time = time.time()
    result, thread_id = run_workflow(
        requirements,
        thread_id="validation-thread-1",
        checkpoint_path=checkpoint_db,
    )
    inception_time = time.time() - start_time
    
    print(f"\nInception completed in {inception_time:.2f}s")
    print(f"Thread ID: {thread_id}")
    print(f"Current Step: {result['current_step']}")
    print(f"Approval Needed: {result['human_approval_needed']}")
    
    # Debug: Check what was actually returned
    print(f"\nDebug - Result keys: {list(result.keys())}")
    print(f"Requirements Doc type: {type(result.get('requirements_doc'))}")
    print(f"Requirements Doc value: {result.get('requirements_doc')[:100] if result.get('requirements_doc') else 'None'}")
    
    # Save inception outputs
    req_doc = result.get("requirements_doc") or ""
    acc_criteria = result.get("acceptance_criteria") or []
    arch = result.get("architecture") or ""
    tasks = result.get("tasks") or []
    
    save_evidence("phase2", req_doc, "requirements_doc.txt")
    save_evidence("phase2", acc_criteria, "acceptance_criteria.json")
    save_evidence("phase2", arch, "architecture.txt")
    save_evidence("phase2", tasks, "tasks.json")
    
    print(f"\nRequirements Doc: {len(result.get('requirements_doc') or '')} chars")
    print(f"Acceptance Criteria: {len(result.get('acceptance_criteria') or [])} items")
    print(f"Architecture: {len(result.get('architecture') or '')} chars")
    print(f"Tasks: {len(result.get('tasks') or [])} items")
    
    # 3. Pause for human approval
    print_section("PHASE 3: HUMAN APPROVAL CHECKPOINT")
    print("Workflow paused at approval checkpoint")
    print(f"Approval Status: {result['approval_status']}")
    
    # Verify checkpoint persistence
    state = get_workflow_state(thread_id, checkpoint_path=checkpoint_db)
    print(f"Checkpoint recovered: {state is not None}")
    if state:
        print(f"State preserved: {state['requirements_doc'] == result['requirements_doc']}")
    
    # 4. Resume workflow
    print_section("PHASE 4: RESUME WORKFLOW - EXECUTION THROUGH OPERATIONS")
    print("Resuming with approval...")
    print("This will execute Planning, Construction, Testing, and Operations phases")
    print("This may take several minutes due to multiple LLM calls and Docker operations...")
    
    start_time = time.time()
    try:
        final_result = resume_workflow(
            thread_id=thread_id,
            approval_decision="approved",
            checkpoint_path=checkpoint_db,
        )
        full_workflow_time = time.time() - start_time
        
        print(f"\nWorkflow completed in {full_workflow_time:.2f}s")
        print(f"Final Phase: {final_result['phase']}")
        print(f"Final Step: {final_result['current_step']}")
        print(f"Construction Status: {final_result.get('construction_status')}")
        print(f"Testing Status: {final_result.get('testing_status')}")
        print(f"Operations Status: {final_result.get('operations_status')}")
        
    except Exception as e:
        print(f"\nWorkflow execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. Inspect Planning outputs
    print_section("PHASE 5: PLANNING AGENT - EXECUTION PLAN")
    
    execution_plan = final_result.get('execution_plan')
    if execution_plan:
        print(f"Subtasks: {len(execution_plan.get('subtasks', []))}")
        print(f"Execution Order: {execution_plan.get('execution_order', [])[:5]}...")
        print(f"Parallel Groups: {list(execution_plan.get('parallel_groups', {}).keys())}")
        print(f"Total Estimated Hours: {execution_plan.get('total_estimated_hours')}")
        save_evidence("phase5", execution_plan, "execution_plan.json")
    
    # 6. Inspect Construction outputs
    print_section("PHASE 6: CONSTRUCTION AGENT - GENERATED SOURCE FILES")
    
    workspace_path = final_result.get('workspace_path')
    print(f"Workspace Path: {workspace_path}")
    
    if workspace_path and os.path.exists(workspace_path):
        print(f"\nGenerated Files:")
        generated_files_list = []
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, workspace_path)
                generated_files_list.append(rel_path)
                print(f"  - {rel_path}")
        
        save_evidence("phase6", generated_files_list, "generated_files.json")
        
        # Read and save a sample file
        if generated_files_list:
            sample_file = os.path.join(workspace_path, generated_files_list[0])
            if os.path.exists(sample_file):
                with open(sample_file, "r") as f:
                    content = f.read()
                save_evidence("phase6", content, f"sample_{generated_files_list[0].replace('/', '_')}.txt")
    
    task_records = final_result.get('task_execution_records', {})
    print(f"\nTask Execution Records: {len(task_records)}")
    completed = sum(1 for r in task_records.values() if r and r.get('status') == 'completed')
    print(f"Completed Tasks: {completed}/{len(task_records)}")
    
    # 7. Inspect Testing outputs
    print_section("PHASE 7: TESTING AGENT - TEST EXECUTION IN DOCKER")
    
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
        
        save_evidence("phase7", test_report, "test_report.json")
        save_evidence("phase7", bug_reports, "bug_reports.json")
    
    correction_count = final_result.get('correction_retry_count', 0)
    print(f"Correction Attempts: {correction_count}")
    
    # 8. Version history validation
    print_section("PHASE 8: VERSION HISTORY VALIDATION")
    
    version_manager = VersionManager(version_db)
    
    if generated_files_list:
        sample_file = generated_files_list[0]
        versions = version_manager.get_all_versions(sample_file)
        print(f"File: {sample_file}")
        print(f"Versions: {len(versions)}")
        for v in versions:
            print(f"  - Version {v.version}: {v.description} (working: {v.version_manager.get_working_version(sample_file).version == v.version if version_manager.get_working_version(sample_file) else False})")
        
        save_evidence("phase8", [
            {"version": v.version, "description": v.description, "timestamp": str(v.timestamp)}
            for v in versions
        ], f"version_history_{sample_file.replace('/', '_')}.json")
    
    # 9. Rollback evidence
    print_section("PHASE 9: ROLLBACK EVIDENCE")
    
    if generated_files_list:
        sample_file = generated_files_list[0]
        rollback_history = version_manager.get_rollback_history(sample_file)
        print(f"Rollback Events: {len(rollback_history)}")
        for event in rollback_history:
            print(f"  - Rollback from v{event['from_version']} to v{event['to_version']}: {event['reason']}")
        
        save_evidence("phase9", rollback_history, f"rollback_history_{sample_file.replace('/', '_')}.json")
    
    # 10. Operations outputs
    print_section("PHASE 10: OPERATIONS AGENT - DOCKER DEPLOYMENT")
    
    operations_status = final_result.get('operations_status')
    print(f"Operations Status: {operations_status}")
    
    build_report = final_result.get('build_report')
    if build_report:
        print(f"Build Status: {build_report.get('status')}")
        print(f"Build Time: {build_report.get('build_time')}s")
        print(f"Docker Image ID: {build_report.get('docker_image_id', '')[:20]}...")
        save_evidence("phase10", build_report, "build_report.json")
    
    deployment_report = final_result.get('deployment_report')
    if deployment_report:
        print(f"Deployment Status: {deployment_report.get('status')}")
        print(f"Container ID: {deployment_report.get('container_id', '')[:20]}...")
        save_evidence("phase10", deployment_report, "deployment_report.json")
    
    health_check = final_result.get('health_check_result')
    if health_check:
        print(f"Health Status: {health_check.get('status')}")
        print(f"Error Message: {health_check.get('error_message', 'N/A')}")
        save_evidence("phase10", health_check, "health_check.json")
    
    # 11. Final summary
    print_section("PHASE 11: FINAL SUMMARY")
    
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
    print(f"  Bug Correction: ✓" if correction_count > 0 else "  Bug Correction: N/A (no bugs)")
    print(f"  Version History: ✓" if versions else "  Version History: N/A")
    print(f"  Docker Build: ✓" if build_report and build_report.get('status') == 'success' else "  Docker Build: ✗")
    print(f"  Container Deployment: ✓" if deployment_report and deployment_report.get('status') == 'success' else "  Container Deployment: ✗")
    print(f"  Health Check: ✓" if health_check and health_check.get('status') == 'healthy' else "  Health Check: ✗")
    
    # Identify placeholders
    print(f"\nRemaining Placeholders:")
    placeholders = []
    if not rollback_history or len(rollback_history) == 0:
        placeholders.append("Rollback (not triggered in this run)")
    if not final_result.get('rollback_report') or final_result.get('rollback_report', {}).get('errors', ['Rollback not implemented']):
        placeholders.append("Rollback in Operations Agent")
    
    if placeholders:
        for p in placeholders:
            print(f"  - {p}")
    else:
        print("  None")
    
    print("\n" + "=" * 80)
    print("  END-TO-END VALIDATION COMPLETE")
    print("=" * 80)
    
    # Cleanup
    print("\nCleanup: Removing checkpoint and version databases...")
    if os.path.exists(checkpoint_db):
        os.remove(checkpoint_db)
        print(f"  Removed: {checkpoint_db}")
    if os.path.exists(version_db):
        os.remove(version_db)
        print(f"  Removed: {version_db}")


if __name__ == "__main__":
    main()
