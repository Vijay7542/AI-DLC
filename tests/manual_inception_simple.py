"""Simple manual test for Inception Agent with real Groq API."""

import sys
sys.path.insert(0, '.')

from graph.workflow import create_initial_state
from agents.inception_agent import InceptionAgent


# 1. Provide a sample business requirement
requirements = """
Build an employee management system.

Features:
1. Add employees.
2. Search employees by employee ID.
3. Update employee details.
4. Store employee information securely.
"""


# 2. Create the initial workflow state
state = create_initial_state(requirements)

print("\n========== INITIAL STATE ==========")
print(f"Workflow ID: {state['workflow_id']}")
print(f"User Requirements: {state['user_requirements'][:50]}...")


# 3. Run the Inception Agent
print("\n========== RUNNING INCEPTION AGENT ==========")
print("This will make 4 sequential LLM calls to Groq API...")
print("Each call has a 30-second timeout with retry logic.")

agent = InceptionAgent()
result = agent.process(state)


# 4. Inspect the four generated fields
fields = [
    "requirements_doc",
    "acceptance_criteria",
    "architecture",
    "tasks",
]

print("\n========== INCEPTION AGENT OUTPUT ==========")

for field in fields:
    value = result.get(field)

    print(f"\nField: {field}")
    print(f"Generated: {value is not None}")

    if value is not None:
        if isinstance(value, str):
            print(f"Length: {len(value)} characters")
            # Avoid unicode encoding issues
            preview = value[:100].encode('ascii', 'ignore').decode('ascii')
            print(f"Preview: {preview}...")
        elif isinstance(value, list):
            print(f"Count: {len(value)} items")
            if value:
                first_item = str(value[0])[:100].encode('ascii', 'ignore').decode('ascii')
                print(f"First item: {first_item}...")
    else:
        print("Value: None")


# 5. Check which fields contain values
print("\n========== FIELD VALIDATION ==========")

success_count = 0
for field in fields:
    value = result.get(field)

    if value is None:
        print(f"FAIL: {field} is None")
    elif isinstance(value, str) and not value.strip():
        print(f"FAIL: {field} is empty")
    elif isinstance(value, list) and not value:
        print(f"FAIL: {field} is empty")
    else:
        print(f"PASS: {field} contains data")
        success_count += 1

# Check for errors
if "errors" in result and result["errors"]:
    print(f"\n========== ERRORS ({len(result['errors'])}) ==========")
    for error in result["errors"]:
        print(f"- {error}")

print(f"\n========== SUMMARY ==========")
print(f"Fields generated successfully: {success_count}/{len(fields)}")
print(f"Test {'PASSED' if success_count == len(fields) else 'FAILED'}")
