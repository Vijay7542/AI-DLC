# Mini AI-DLC Architecture

## High-Level Architecture

Mini AI-DLC follows an agent-based architecture where specialized AI agents collaborate through a LangGraph workflow. The system consists of:

1. **Agents**: Specialized AI components for each development phase
2. **Workflow Orchestrator**: LangGraph manages state transitions and agent coordination
3. **State Management**: Shared workflow state persisted to SQLite
4. **API Layer**: FastAPI provides endpoints for human interaction
5. **RAG System** (later): Retrieves software engineering guidelines

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI API                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ /start       │  │ /feedback    │  │ /status      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Shared Workflow State                    │  │
│  │  (Requirements, Tasks, Code, Approval Status, etc.)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Inception   │───▶│ Construction │───▶│  Operations  │ │
│  │    Agent     │    │    Agent     │    │    Agent     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Approval    │    │   Code       │    │   Approval   │ │
│  │    Gate      │    │   Approval   │    │    Gate      │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Checkpoints Table (State Snapshots)         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

                           │
                           ▼ (later phase)
┌─────────────────────────────────────────────────────────────┐
│                       RAG System                             │
│  ┌──────────────┐    ┌──────────────┐                        │
│  │  Guidelines  │───▶│  Retriever   │                        │
│  │   (Files)    │    │ (Keyword)    │                        │
│  └──────────────┘    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Agents

#### Base Agent (`agents/base_agent.py`)
- Provides common utilities for all agents
- Initializes LLM connection (Groq via LangChain)
- Manages prompt templates
- Handles LLM error handling and retries

#### Inception Agent (`agents/inception_agent.py`)
- Parses natural language requirements
- Generates structured requirements document
- Defines acceptance criteria
- Designs high-level architecture
- Breaks down project into implementation tasks
- Sets `human_approval_needed = True` after completion

#### Construction Agent (`agents/construction_agent.py`)
- Generates Python code based on approved tasks
- Creates pytest unit tests
- Executes tests and analyzes failures
- Iterates on code to fix issues
- Sets `code_changes_pending = True` before writing to disk
- Sets `human_approval_needed = True` for code approval gate

#### Operations Agent (`agents/operations_agent.py`)
- Generates deployment documentation
- Creates monitoring plan
- Defines model evaluation metrics
- Documents error handling approach

### Workflow Orchestrator

#### LangGraph Workflow (`graph/workflow.py`)
- Defines the directed graph of agent nodes
- Implements conditional routing between nodes
- Manages state transitions through the graph
- Coordinates approval gates and pauses
- Integrates with SQLite checkpoint saver

#### State Schema (`graph/state.py`)
- Defines Pydantic models for workflow state
- Manages state validation
- Ensures type safety across the workflow

### State Management

#### SQLite Database (`db/connection.py`, `db/migrations.py`)
- Manages SQLite connection lifecycle
- Creates checkpoint table schema
- Provides state save/load operations
- Integrates with LangGraph's checkpoint saver

### API Layer

#### FastAPI Application (`api/main.py`, `api/routes.py`, `api/models.py`)
- Exposes HTTP endpoints for workflow interaction
- Manages workflow sessions
- Handles human feedback input
- Resumes paused workflows from checkpoints

### RAG System (Later Phase)

#### Retriever (`rag/retriever.py`)
- Implements keyword-based search over guidelines
- Retrieves relevant software engineering practices
- Injects context into Construction Agent prompts

#### Guidelines (`rag/guidelines/`)
- Markdown files with best practices
- Python coding standards
- Testing guidelines
- Security principles

## Data Flow

### 1. Workflow Initialization
```
User → FastAPI (/start) → LangGraph → Initialize State → SQLite
```

### 2. Inception Phase
```
State → Inception Agent → LLM (Groq) → Update State → SQLite
↓
Approval Gate → Pause → Human Feedback → Resume
```

### 3. Construction Phase
```
State → Construction Agent → LLM (Groq) → Generate Code
↓
Code Approval Gate → Pause → Human Feedback → Resume
↓
Write Code to Disk → Execute Tests → Update State → SQLite
```

### 4. Operations Phase
```
State → Operations Agent → LLM (Groq) → Generate Docs
↓
Update State → SQLite → Complete
```

## Workflow State Schema

The shared workflow state is defined in `graph/state.py`:

```python
from typing import Optional, List, Dict, TypedDict, Literal
from pydantic import BaseModel

class Task(BaseModel):
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    dependencies: List[str] = []

class WorkflowState(TypedDict):
    # Workflow identification
    workflow_id: str
    
    # User input
    user_requirements: str
    
    # Workflow control
    phase: Literal["inception", "construction", "operations", "completed"]
    current_step: str
    human_approval_needed: bool
    approval_status: Literal["pending", "approved", "rejected"]
    human_feedback: Optional[str]
    
    # Inception outputs
    requirements_doc: Optional[str]
    acceptance_criteria: Optional[List[str]]
    architecture: Optional[str]
    tasks: Optional[List[Task]]
    
    # Construction outputs
    generated_code: Optional[Dict[str, str]]  # filename -> code
    test_results: Optional[Dict[str, bool]]   # test_name -> passed
    code_changes_pending: bool
    
    # Operations outputs
    deployment_docs: Optional[str]
    monitoring_plan: Optional[str]
    
    # Error handling
    errors: List[str]
    retry_count: int
```

## LangGraph Workflow Mechanics

### State Transitions

LangGraph manages state through a typed state object that flows through each node:

1. **Node Execution**: Each agent node receives the current state, processes it, and returns updates
2. **State Merging**: LangGraph automatically merges state updates using defined reducers
3. **Checkpointing**: After each node, a checkpoint is saved to SQLite
4. **Recovery**: If workflow is interrupted, it resumes from the last checkpoint

### Approval Pauses

Approval gates are implemented using conditional routing:

```
Agent Node → Check Approval Node
                     ↓
           ┌─────────┴─────────┐
           │                   │
    (approval needed)    (no approval needed)
           │                   │
           ▼                   ▼
    Human Input Node      Next Agent Node
           │
           ▼
    Resume after feedback
```

**Implementation:**
- Agent sets `human_approval_needed = True` in state
- Workflow routes to "check_approval" node
- Check node evaluates the flag and routes accordingly
- If approval needed, workflow pauses (returns special command)
- Human provides feedback via FastAPI endpoint
- API updates state in SQLite with feedback
- Workflow is resumed with updated state

### Checkpointing

LangGraph's checkpoint mechanism provides:

1. **Automatic State Saving**: After each node completion
2. **Version History**: Multiple checkpoints per workflow
3. **Time Travel**: Ability to inspect previous states
4. **Crash Recovery**: Resume from last checkpoint

**SQLite Schema:**
```sql
CREATE TABLE checkpoints (
    thread_id TEXT PRIMARY KEY,
    checkpoint_id TEXT,
    timestamp DATETIME,
    state_json TEXT,
    next_node TEXT
);
```

### Conditional Routing

Edges in the graph can be conditional based on state:

```python
def should_approve(state: WorkflowState) -> str:
    if state["human_approval_needed"]:
        return "human_input"
    return "next_agent"
```

## Security Considerations

### API Key Management
- All API keys read from environment variables via `config.py`
- No hardcoded secrets in source code
- `GROQ_API_KEY` required for Groq integration
- Keys never logged or exposed in error messages

### Code Execution Safety
- Generated code never executes without human approval
- Code approval gate required before writing to disk
- Tests run in isolated environment
- No arbitrary code execution from user input

### Data Privacy
- Workflow state stored locally in SQLite
- No data sent to external services except Groq API
- User requirements and generated code logged only locally
- Audit trail of all approvals and code changes

## Technology Rationale

### LangGraph
- Built-in state management and checkpointing
- Declarative workflow definition
- Excellent support for human-in-the-loop patterns
- Native Python integration

### LangChain
- Standard LLM integration framework
- Groq provider support
- Prompt template management
- Easy mocking for testing

### Groq
- Fast LLM inference
- Cost-effective for development
- Support for open-source models (Llama, Mixtral)
- Low latency for interactive workflows

### FastAPI
- Modern, async Python web framework
- Automatic API documentation
- Pydantic integration for validation
- Easy testing with TestClient

### SQLite
- No external database dependency
- Built-in Python support
- Sufficient for single-session workflows
- Easy backup and migration

### Pydantic
- Type safety and validation
- Clear schema definitions
- Automatic serialization
- Excellent error messages

## Error Handling Strategy

### LLM Errors
- Retry with exponential backoff
- Fallback to alternative model if available
- Log error details without exposing API keys
- Human notification if retries exhausted

### Database Errors
- Retry connection failures
- Validate state before saving
- Recovery from corrupted checkpoints
- Fallback to in-memory state if database unavailable

### Validation Errors
- Pydantic validates all state transitions
- Clear error messages for invalid state
- Reject invalid human feedback
- Prevent workflow corruption

## Testing Strategy

### Unit Tests
- Test each agent independently with mocked LLM responses
- Test state schema validation
- Test database operations
- Test API endpoints

### Integration Tests
- Test workflow through multiple phases
- Test approval gate functionality
- Test checkpoint recovery
- Test state persistence

### End-to-End Tests
- Test complete workflow with simple example
- Verify all approval gates work
- Verify state persistence across interruptions
- Use mocked LLM responses by default

### LLM Integration Tests
- Optional tests with real Groq API
- Separate test suite for live API calls
- Not required for every test run
- Used for validation before deployment
