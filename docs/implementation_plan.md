# Mini AI-DLC Implementation Plan

## Overview

This plan implements Mini AI-DLC incrementally across 8 phases. Each phase builds upon the previous one, introducing complexity gradually. RAG and FastAPI are introduced when their implementation stages are reached. Testing accompanies each phase to ensure quality.

## Phase 1: Core Foundation

**Goal**: Establish basic project structure, agents, and simple workflow.

### Tasks

1. **Create Project Structure**
   - Create directory structure: `agents/`, `graph/`, `tests/`, `docs/`
   - Initialize `__init__.py` files
   - Create `README.md` with project overview

2. **Define Dependencies**
   - Create `requirements.txt` with:
     - `langgraph`
     - `langchain`
     - `langchain-groq`
     - `pydantic`
     - `pytest`
     - `python-dotenv`
   - Document version constraints (no newly published packages)
   - Specify Python 3.8+ compatibility

3. **Configuration Management**
   - Create `config.py` to read environment variables
   - Load `GROQ_API_KEY` from environment
   - Provide default model configuration
   - Add `.env.example` file (without actual keys)

4. **State Schema Definition**
   - Create `graph/state.py`
   - Define `Task` Pydantic model
   - Define `WorkflowState` TypedDict with all required fields
   - Include workflow_id, approval_status, and other approved fields
   - Add validation logic

5. **Base Agent Implementation**
   - Create `agents/base_agent.py`
   - Implement LLM initialization using LangChain and Groq
   - Create prompt template utilities
   - Add error handling and retry logic
   - Mock LLM support for testing

6. **Inception Agent Implementation**
   - Create `agents/inception_agent.py`
   - Implement requirements analysis logic
   - Implement architecture design generation
   - Implement task breakdown logic
   - Set `human_approval_needed = True` after completion
   - Set appropriate approval status

7. **Basic Workflow Graph**
   - Create `graph/workflow.py`
   - Define LangGraph StateGraph with WorkflowState
   - Add Inception Agent node
   - Implement simple routing (no approval gates yet)
   - Add start and end nodes

8. **Testing - Phase 1**
   - Test state schema validation (`test_state.py`)
   - Test base agent with mocked LLM (`test_base_agent.py`)
   - Test inception agent with mocked LLM (`test_inception_agent.py`)
   - Test basic workflow execution (`test_workflow.py`)
   - All tests use mocked LLM responses

**Deliverable**: Working Inception Agent that can analyze requirements and produce task list.

**Acceptance Criteria**:
- [ ] Project structure created
- [ ] Dependencies defined
- [ ] Configuration loads from environment
- [ ] State schema validates correctly
- [ ] Base agent initializes LLM
- [ ] Inception agent generates requirements and tasks
- [ ] Basic workflow executes end-to-end
- [ ] All tests pass with mocked LLM

---

## Phase 2: Persistence Layer

**Goal**: Add SQLite database for workflow state persistence and checkpointing.

### Tasks

9. **Database Connection**
   - Create `db/` directory
   - Create `db/__init__.py`
   - Implement `db/connection.py` for SQLite connection management
   - Add connection pooling if needed
   - Handle connection errors gracefully

10. **Database Schema**
    - Create `db/migrations.py`
    - Define checkpoint table schema:
      - `thread_id` (workflow_id)
      - `checkpoint_id`
      - `timestamp`
      - `state_json`
      - `next_node`
    - Implement schema creation logic
    - Add migration support for future changes

11. **LangGraph Checkpoint Integration**
    - Update `graph/workflow.py`
    - Integrate LangGraph's SQLite checkpoint saver
    - Configure checkpoint after each node execution
    - Implement checkpoint configuration

12. **State Save/Load Logic**
    - Implement state serialization to JSON
    - Implement state deserialization from JSON
    - Add validation when loading state
    - Handle corrupted checkpoints

13. **Testing - Phase 2**
    - Test database connection (`test_db_connection.py`)
    - Test schema creation (`test_migrations.py`)
    - Test checkpoint save/load (`test_checkpoint.py`)
    - Test workflow with checkpoint recovery (`test_workflow_checkpoint.py`)
    - Verify state persistence across workflow interruptions

**Deliverable**: SQLite database that persists workflow state and supports checkpoint recovery.

**Acceptance Criteria**:
- [ ] Database connection established
- [ ] Checkpoint table created
- [ ] State saves to SQLite after each node
- [ ] State loads correctly from checkpoint
- [ ] Workflow can resume from interruption
- [ ] All persistence tests pass

---

## Phase 3: Human Approval Gates

**Goal**: Implement approval gates with pause/resume functionality.

### Tasks

14. **Approval Check Node**
    - Add "check_approval" node to workflow graph
    - Implement logic to check `human_approval_needed` flag
    - Implement conditional routing based on approval status

15. **Conditional Routing**
    - Implement routing function:
      - If `human_approval_needed = True`: route to human_input
      - If `human_approval_needed = False`: route to next agent
    - Add edge from Inception Agent to check_approval
    - Add conditional edges from check_approval

16. **Human Input Placeholder**
    - Add "human_input" node (in-memory for now)
    - Implement pause mechanism (return special command)
    - Set workflow to wait state
    - Store current step in state

17. **Update Inception Agent**
    - Modify Inception Agent to set `human_approval_needed = True`
    - Set `approval_status = "pending"` after completion
    - Clear previous approval status on retry

18. **Feedback Processing**
    - Implement logic to process human feedback
    - Update state with `human_feedback`
    - Set `approval_status` based on feedback
    - Clear `human_approval_needed` after processing

19. **Testing - Phase 3**
    - Test approval check logic (`test_approval_gate.py`)
    - Test conditional routing (`test_routing.py`)
    - Test workflow pause on approval needed (`test_pause.py`)
    - Test workflow resume after feedback (`test_resume.py`)
    - Test rejection and revision flow (`test_rejection.py`)

**Deliverable**: Working approval gates that pause workflow and wait for human input.

**Acceptance Criteria**:
- [ ] Approval check node evaluates flag correctly
- [ ] Workflow pauses when approval needed
- [ ] Workflow continues when not needed
- [ ] Human feedback updates state
- [ ] Rejection triggers revision
- [ ] All approval gate tests pass

---

## Phase 4: Construction Agent

**Goal**: Implement Construction Agent for code generation with approval gates.

### Tasks

20. **Construction Agent Implementation**
    - Create `agents/construction_agent.py`
    - Implement code generation logic based on tasks
    - Implement test generation logic
    - Use prompt templates for code generation
    - Add task execution tracking

21. **Add Construction Node**
    - Add Construction Agent node to workflow graph
    - Implement edge from approval gate to Construction
    - Add Construction to conditional routing

22. **Code Approval Gate**
    - Add "check_code_changes" node
    - Implement check for `code_changes_pending` flag
    - Set `human_approval_needed = True` before code approval
    - Add conditional routing for code approval

23. **Code Write Logic**
    - Implement code writing to disk (only after approval)
    - Implement test file creation
    - Add file system error handling
    - Track written files in state

24. **Test Execution**
    - Implement pytest execution logic
    - Capture test results
    - Update state with test results
    - Analyze failures and iterate if needed
    - Require re-approval if code changes after test failures

25. **Testing - Phase 4**
    - Test Construction Agent with mocked LLM (`test_construction_agent.py`)
    - Test code generation prompts
    - Test code approval gate (`test_code_approval.py`)
    - Test code writing to disk
    - Test test execution and result capture
    - Test full Inception → Construction flow

**Deliverable**: Construction Agent that generates code and tests with approval before writing to disk.

**Acceptance Criteria**:
- [ ] Construction Agent generates code
- [ ] Construction Agent generates tests
- [ ] Code approval gate triggers before write
- [ ] Code writes to disk only after approval
- [ ] Tests execute and results captured
- [ ] All Construction tests pass

---

## Phase 5: RAG Integration

**Goal**: Add Retrieval-Augmented Generation for code generation guidance.

### Tasks

26. **Create Guidelines**
    - Create `rag/` directory
    - Create `rag/guidelines/` directory
    - Add sample guidelines:
      - `python_best_practices.md`
      - `testing_guidelines.md`
      - `security_principles.md`

27. **Retriever Implementation**
    - Create `rag/retriever.py`
    - Implement keyword-based search
    - Load guidelines from files
    - Implement relevance scoring
    - Return top N relevant guidelines

28. **Integrate with Construction Agent**
    - Update Construction Agent to call retriever
    - Inject retrieved guidelines into prompts
    - Format guidelines for LLM consumption
    - Add fallback if no guidelines found

29. **Testing - Phase 5**
    - Test retriever functionality (`test_retriever.py`)
    - Test keyword search accuracy
    - Test guideline loading
    - Test Construction Agent with RAG context
    - Verify generated code follows guidelines

**Deliverable**: RAG system that retrieves and injects software engineering guidelines.

**Acceptance Criteria**:
- [ ] Guidelines files created
- [ ] Retriever loads guidelines
- [ ] Keyword search returns relevant results
- [ ] Construction Agent uses RAG context
- [ ] Generated code reflects guidelines
- [ ] All RAG tests pass

---

## Phase 6: FastAPI Backend

**Goal**: Add FastAPI endpoints for workflow interaction and human feedback.

### Tasks

30. **API Models**
    - Create `api/` directory
    - Create `api/models.py`
    - Define Pydantic models for requests:
      - `WorkflowStartRequest` (user_requirements)
      - `FeedbackRequest` (workflow_id, feedback, approved)
      - `StatusResponse` (workflow state)
    - Define response models

31. **FastAPI Application**
    - Create `api/main.py`
    - Initialize FastAPI app
    - Add CORS middleware if needed
    - Configure API documentation

32. **Workflow Start Endpoint**
    - Implement `POST /start` endpoint
    - Validate user requirements
    - Initialize workflow state
    - Start LangGraph workflow
    - Return workflow_id

33. **Feedback Endpoint**
    - Implement `POST /feedback` endpoint
    - Validate workflow_id and feedback
    - Load workflow state from SQLite
    - Update state with feedback and approval status
    - Resume workflow execution
    - Return updated status

34. **Status Endpoint**
    - Implement `GET /status/{workflow_id}` endpoint
    - Load workflow state from SQLite
    - Return current state (sanitized)
    - Hide sensitive information

35. **Integrate with Workflow**
    - Update human_input node to use API instead of in-memory
    - Remove in-memory placeholder
    - Ensure workflow waits for API call
    - Handle concurrent requests if needed

36. **Testing - Phase 6**
    - Test API models validation (`test_api_models.py`)
    - Test workflow start endpoint (`test_api_start.py`)
    - Test feedback endpoint (`test_api_feedback.py`)
    - Test status endpoint (`test_api_status.py`)
    - Test FastAPI integration with workflow
    - Use TestClient for all API tests

**Deliverable**: FastAPI backend with endpoints for workflow start, feedback, and status.

**Acceptance Criteria**:
- [ ] API models validate correctly
- [ ] `/start` endpoint initializes workflow
- [ ] `/feedback` endpoint resumes workflow
- [ ] `/status` endpoint returns state
- [ ] FastAPI integrates with LangGraph
- [ ] All API tests pass

---

## Phase 7: Operations Agent

**Goal**: Implement Operations Agent for deployment documentation.

### Tasks

37. **Operations Agent Implementation**
    - Create `agents/operations_agent.py`
    - Implement deployment documentation generation
    - Implement monitoring plan generation
    - Define model evaluation metrics
    - Document error handling approach

38. **Add Operations Node**
    - Add Operations Agent node to workflow graph
    - Implement edge from Construction completion to Operations
    - Add to conditional routing

39. **Final Approval Gate**
    - Add approval check after Operations
    - Require approval before marking workflow complete
    - Allow final review of all outputs

40. **Testing - Phase 7**
    - Test Operations Agent with mocked LLM (`test_operations_agent.py`)
    - Test deployment documentation generation
    - Test monitoring plan generation
    - Test full three-phase workflow
    - Test final approval gate

**Deliverable**: Operations Agent that generates deployment and monitoring documentation.

**Acceptance Criteria**:
- [ ] Operations Agent generates deployment docs
- [ ] Operations Agent generates monitoring plan
- [ ] Operations node added to workflow
- [ ] Final approval gate works
- [ ] Full three-phase workflow executes
- [ ] All Operations tests pass

---

## Phase 8: End-to-End Integration

**Goal**: Comprehensive testing and refinement of the complete system.

### Tasks

41. **End-to-End Test**
    - Create comprehensive E2E test (`test_e2e.py`)
    - Test with simple example: "create a calculator function"
    - Verify Inception → Construction → Operations flow
    - Verify all approval gates
    - Verify state persistence

42. **Error Handling**
    - Add comprehensive error handling throughout
    - Add logging to all components
    - Handle LLM API failures gracefully
    - Handle database failures gracefully
    - Add user-friendly error messages

43. **Security Validation**
    - Verify no hardcoded secrets
    - Verify API keys loaded from environment
    - Verify code never executes without approval
    - Audit logging for approvals

44. **Performance Optimization**
    - Profile workflow execution
    - Optimize database queries if needed
    - Optimize LLM prompt sizes
    - Add caching if beneficial

45. **Documentation**
    - Update README with setup instructions
    - Add API documentation examples
    - Add troubleshooting guide
    - Document environment variables

46. **Final Testing**
    - Run all test suites
    - Verify test coverage
    - Manual testing with real Groq API
    - Fix any remaining issues

**Deliverable**: Production-ready Mini AI-DLC system.

**Acceptance Criteria**:
- [ ] E2E test passes with simple example
- [ ] Error handling works correctly
- [ ] Security validated
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] All tests pass
- [ ] Manual testing successful

---

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Use mocked LLM responses
- Fast execution (< 1 second per test)
- Run on every commit

### Integration Tests
- Test component interactions
- Test workflow through multiple phases
- Use mocked LLM responses
- Slower execution (~5-10 seconds per test)
- Run on every commit

### End-to-End Tests
- Test complete workflows
- Use simple, predictable examples
- Use mocked LLM responses for CI
- Optional real LLM for validation
- Run before deployment

### LLM Integration Tests
- Separate test suite
- Requires live Groq API key
- Not required for CI
- Run manually for validation

### Test Coverage Goals
- Agents: 80%+ coverage
- Workflow: 80%+ coverage
- API: 90%+ coverage
- Database: 90%+ coverage
- Overall: 75%+ coverage

---

## Risk Mitigation

### Complexity Risk
- **Mitigation**: Incremental implementation, each phase testable independently
- **Fallback**: Simplify RAG or skip if complexity too high

### LLM Reliability Risk
- **Mitigation**: Retry logic, fallback models, mocked responses for testing
- **Fallback**: Manual intervention if LLM fails consistently

### State Corruption Risk
- **Mitigation**: Pydantic validation, checkpoint versioning, recovery logic
- **Fallback**: Reset workflow from last known good state

### Approval Gate Bypass Risk
- **Mitigation**: Explicit flags, audit logging, validation at each gate
- **Fallback**: Manual review of workflow logs

### API Key Exposure Risk
- **Mitigation**: Environment variables only, no logging of secrets
- **Fallback**: Rotate keys if exposure suspected

---

## Milestones

1. **Milestone 1 (Phase 1-2)**: Core workflow with persistence
   - Deadline: End of Week 1
   - Demo: Inception agent runs, state persists

2. **Milestone 2 (Phase 3-4)**: Human approval and code generation
   - Deadline: End of Week 2
   - Demo: Full Inception → Construction flow with approvals

3. **Milestone 3 (Phase 5-6)**: RAG and API integration
   - Deadline: End of Week 3
   - Demo: FastAPI endpoints, RAG-guided code generation

4. **Milestone 4 (Phase 7-8)**: Complete system
   - Deadline: End of Week 4
   - Demo: Full three-phase workflow via API

---

## Dependencies Between Phases

- Phase 2 depends on Phase 1 (state schema must exist)
- Phase 3 depends on Phase 2 (checkpoints must work)
- Phase 4 depends on Phase 3 (approval gates must work)
- Phase 5 can be done in parallel with Phase 6 (RAG independent of API)
- Phase 7 depends on Phase 4 (Construction must work)
- Phase 8 depends on all previous phases

---

## Notes

- Each phase should be completed and tested before moving to the next
- Use Git branches for each phase (feature/phase-N)
- Merge to main only after phase is complete and tested
- Keep tests passing at all times
- Document any deviations from this plan
- Review and adjust plan based on learnings from implementation
