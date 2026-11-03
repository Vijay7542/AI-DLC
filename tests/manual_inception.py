from pprint import pprint

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
pprint(state)


# 3. Run the Inception Agent
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
    print("Value:")
    pprint(value)


# 5. Check which fields contain values
print("\n========== FIELD VALIDATION ==========")

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