"""Manual test for workflow with human approval using real Groq API."""

import sys
sys.path.insert(0, '.')

from graph.workflow import run_workflow, resume_workflow, get_workflow_state


# 1. Run workflow to approval checkpoint
print("========== STEP 1: RUN WORKFLOW ==========")
requirements = """
Build a simple task management application with the following features:
1. Create tasks
2. Mark tasks as complete
3. Delete tasks
4. List all tasks
"""

print(f"Requirements: {requirements[:100]}...")
print("\nRunning workflow (this will make real Groq API calls)...")

result, thread_id = run_workflow(
    requirements,
    checkpoint_path="manual_checkpoints.db"
)

print(f"\nWorkflow paused at approval checkpoint")
print(f"Thread ID: {thread_id}")
print(f"Current Step: {result['current_step']}")
print(f"Approval Needed: {result['human_approval_needed']}")
print(f"Approval Status: {result['approval_status']}")

print("\n========== GENERATED OUTPUTS ==========")
print(f"Requirements Doc: {len(result['requirements_doc']) if result['requirements_doc'] else 0} chars")
print(f"Acceptance Criteria: {len(result['acceptance_criteria']) if result['acceptance_criteria'] else 0} items")
print(f"Architecture: {len(result['architecture']) if result['architecture'] else 0} chars")
print(f"Tasks: {len(result['tasks']) if result['tasks'] else 0} items")

# 2. Check workflow state
print("\n========== STEP 2: CHECK WORKFLOW STATE ==========")
state = get_workflow_state(thread_id, checkpoint_path="manual_checkpoints.db")
print(f"State retrieved: {state is not None}")
if state:
    print(f"Current Step: {state['current_step']}")

# 3. Resume with approval
print("\n========== STEP 3: RESUME WITH APPROVAL ==========")
print("Approving the workflow...")

final_result = resume_workflow(
    thread_id=thread_id,
    approval_decision="approved",
    checkpoint_path="manual_checkpoints.db"
)

print(f"\nFinal Approval Status: {final_result['approval_status']}")
print(f"Human Approval Needed: {final_result['human_approval_needed']}")
print(f"Workflow completed successfully!")

print("\n========== TEST COMPLETE ==========")
