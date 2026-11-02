# Mini AI-DLC Requirements

## Project Overview

Mini AI-DLC is an AI Software Delivery Assistant that demonstrates an AI-Driven Development Life Cycle (AI-DLC) using Agentic AI. The system automates software development through three phases: Inception (requirements analysis), Construction (code generation), and Operations (deployment preparation), with human-in-the-loop approval gates at critical decision points.

## Technology Stack

- **Python**: Core programming language
- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration framework
- **Groq**: LLM provider for fast inference
- **FastAPI**: Backend API for workflow interaction
- **SQLite**: Workflow state persistence and checkpointing
- **Pydantic**: Data validation and schema definition
- **Pytest**: Automated testing framework
- **RAG** (later phase): Retrieval of software engineering guidelines

## Functional Requirements

### Phase 1: Inception

1. **Requirements Analysis**
   - Parse natural language user requirements
   - Generate structured requirements document
   - Define acceptance criteria for the project

2. **Architecture Design**
   - Design high-level application architecture
   - Identify key components and their relationships
   - Document technology choices and rationale

3. **Task Breakdown**
   - Decompose project into small, testable implementation tasks
   - Define task dependencies and execution order
   - Assign unique identifiers to each task

4. **Human Approval Gate**
   - Present requirements, architecture, and task list for human review
   - Collect approval or feedback for revisions
   - If rejected, revise based on human feedback and resubmit

### Phase 2: Construction

5. **Code Generation**
   - Generate Python code based on approved tasks
   - Follow coding standards and best practices
   - Include appropriate error handling

6. **Test Generation**
   - Create pytest unit tests for generated code
   - Generate test fixtures where appropriate
   - Ensure tests are executable and meaningful

7. **Code Approval Gate**
   - Require human approval before each batch of code changes is written to disk
   - Present generated code and tests for review
   - If rejected, collect feedback and regenerate

8. **Test Execution**
   - Execute generated tests using pytest
   - Analyze test failures and iterate on code
   - Ensure all tests pass before proceeding

### Phase 3: Operations

9. **Deployment Documentation**
   - Generate deployment instructions
   - Document environment setup and configuration
   - Create runbooks for common operations

10. **Monitoring and Evaluation**
    - Plan application monitoring strategy
    - Define model evaluation metrics
    - Document error handling and logging approach

## Non-Functional Requirements

### 11. State Persistence
- Workflow state must persist to SQLite after each agent execution
- Support checkpoint recovery to resume from interruptions
- Use LangGraph's built-in checkpointing mechanism

### 12. Human-in-the-Loop
- Approval gates before phase transitions (Inception → Construction)
- Approval gates before code modifications are written to disk
- Ability to provide feedback and request revisions
- Workflow pauses when approval is needed and resumes after feedback

### 13. Security
- API keys must be read from environment variables
- No hardcoded secrets in source code
- Generated code must not execute without approval and safeguards
- Audit trail of approvals and code changes

### 14. Testability
- Every major component must have automated tests
- Support mocked LLM responses for workflow tests
- Integrate actual Groq API calls when appropriate
- No requirement for live Groq API call in every automated test

### 15. Incremental Delivery
- Implement project incrementally across phases
- Introduce RAG and FastAPI when their implementation stages are reached
- Each phase must be testable independently
- Avoid unnecessary complexity in early stages

## Acceptance Criteria

### Inception Phase
- [ ] Inception Agent generates valid requirements document from user input
- [ ] Architecture design is coherent and addresses requirements
- [ ] Task breakdown produces small, testable units
- [ ] Human can approve or reject the inception output
- [ ] Rejection triggers revision based on feedback

### Construction Phase
- [ ] Construction Agent generates syntactically correct Python code
- [ ] Generated tests can be executed with pytest
- [ ] Human approval is required before code is written to disk
- [ ] Test failures are analyzed and code is iterated
- [ ] All tests pass before moving to next task

### Operations Phase
- [ ] Operations Agent generates deployment documentation
- [ ] Monitoring plan is defined and actionable
- [ ] Documentation is comprehensive and clear

### System-Wide
- [ ] Workflow state persists to SQLite and can be resumed
- [ ] Human approval gates function correctly at all checkpoints
- [ ] API keys are loaded from environment variables only
- [ ] No secrets are hardcoded in the codebase
- [ ] End-to-end workflow completes for a simple example (e.g., calculator function)
- [ ] All components have corresponding automated tests

## Workflow State Requirements

The shared workflow state must track:

- **Workflow Identification**: Unique workflow ID for each session
- **User Input**: Original requirements provided by user
- **Phase Control**: Current phase (inception, construction, operations, completed)
- **Approval Status**: Explicit approval status at each gate
- **Inception Outputs**: Requirements document, acceptance criteria, architecture, tasks
- **Construction Outputs**: Generated code, test results, pending code changes
- **Operations Outputs**: Deployment documentation, monitoring plan
- **Error Handling**: Error messages, retry count
- **Human Feedback**: Feedback collected during approval gates

## External Dependencies

- Groq API key (environment variable: `GROQ_API_KEY`)
- Python 3.8+
- SQLite (included in Python standard library)

## Out of Scope (Initial Implementation)

- RAG (Retrieval-Augmented Generation) - to be added in later phase
- Streamlit UI - future enhancement
- Complex vector search for RAG - simple keyword matching when implemented
- Real-time dashboard - FastAPI endpoints only for MVP
- Multi-user support - single workflow at a time
- Version control integration - manual workflow
