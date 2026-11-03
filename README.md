# Mini AI-DLC

An AI Software Delivery Assistant that demonstrates an AI-Driven Development Life Cycle (AI-DLC) using Agentic AI.

## Overview

Mini AI-DLC automates software development through orchestrated phases:
- **Inception**: Requirements analysis, architecture design, and task breakdown
- **Planning**: Detailed execution planning with dependencies and parallel groups
- **Construction**: Code generation with version tracking and syntax validation
- **Testing**: Test generation, Docker-based execution, and autonomous bug correction
- **Operations**: Docker image building, container deployment, and health checks

The system features:
- Human-in-the-loop approval gates at critical decision points
- SQLite checkpointing for workflow recovery
- Persistent version history for code changes
- Autonomous bug-fixing with regression detection
- Multi-provider LLM support with automatic fallback
- Docker-based test execution (no host code execution)

## Technology Stack

- **Python 3.8+** (tested with Python 3.14.6)
- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration framework
- **Groq**: LLM provider for fast inference
- **OpenAI**: LLM provider (optional fallback)
- **Anthropic**: LLM provider (optional fallback)
- **Pydantic**: Data validation and schema definition
- **Pytest**: Automated testing framework
- **Docker**: Container-based test execution

## Current Implementation Status

**Completed:**
- ✓ Multi-provider LLM architecture (Groq, OpenAI, Anthropic)
- ✓ Inception Agent with requirements, architecture, and task generation
- ✓ Planning Agent with execution plans and dependencies
- ✓ Construction Agent with file generation and version tracking
- ✓ Testing Agent with Docker-based test execution
- ✓ Autonomous bug correction (syntax, runtime, dependency, logical errors)
- ✓ Regression detection and automatic rollback
- ✓ Persistent version history (SQLite)
- ✓ Operations Agent with Docker build and deployment
- ✓ Human approval gates with SQLite checkpointing
- ✓ Windows Docker compatibility
- ✓ Error classification and retry logic with exponential backoff
- ✓ Provider fallback on quota exhaustion

**Partially Implemented:**
- ⚠ Integration error correction (placeholder)
- ⚠ Full regression suite (specific tests only)
- ⚠ Operations Agent rollback (placeholder)

**Not Implemented:**
- ✗ Change Impact Agent
- ✗ Task replanning
- ✗ Cloud provider integration

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## LLM Provider Configuration

Mini AI-DLC supports multiple LLM providers with automatic fallback:

### Supported Providers

- **Groq** (default): Fast inference, good for development
- **OpenAI**: GPT models, production-ready
- **Anthropic**: Claude models, excellent for complex reasoning

### Environment Variables

Set these in your `.env` file:

```bash
# Primary provider
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b

# Fallback providers (comma-separated)
LLM_FALLBACK_PROVIDERS=openai,anthropic

# API keys (set at least one)
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Provider Switching

To switch providers, simply change the environment variable:

```bash
# Use OpenAI as primary
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o

# Use Anthropic as primary
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
```

### Fallback Behavior

The system automatically falls back to the next configured provider when:
- Daily token quota is exhausted (HTTP 429 with TPD/RPD limit)
- Authentication fails
- Invalid model specified

Rate limits (temporary HTTP 429) trigger retry with exponential backoff, not fallback.

### Error Handling

- **Rate limits**: Retry with exponential backoff (max 3 retries)
- **Quota exhaustion**: Automatic provider fallback
- **Authentication failures**: Automatic provider fallback
- **Network errors**: Retry with exponential backoff
- **Timeouts**: Retry with exponential backoff
- **Invalid responses**: Raise error immediately

## Running Tests

### Unit Tests (Mocked LLM)

All unit tests use mocked LLM responses and do not require real API keys:

```bash
pytest tests/ -v
```

Expected output: 108 passed, 1 skipped

### Provider Tests

Test the multi-provider architecture:

```bash
pytest tests/test_llm_provider.py -v
```

Expected output: 18 passed

### Docker Integration Tests

Test real Docker operations (requires Docker Desktop):

```bash
pytest tests/test_docker_integration.py -v
```

Tests will skip if Docker is not available.

## Project Structure

```
Mini AI-DLC/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent with multi-provider LLM
│   ├── llm_provider.py        # Multi-provider abstraction layer
│   ├── inception_agent.py     # Requirements analysis
│   ├── planning_agent.py      # Execution planning
│   ├── construction_agent.py  # Code generation
│   ├── testing_agent.py       # Test generation and execution
│   ├── operations_agent.py   # Docker build and deployment
│   ├── docker_utils.py        # Docker path conversion utilities
│   └── version_manager.py      # Persistent version history
├── graph/
│   ├── __init__.py
│   ├── state.py               # Workflow state schema
│   └── workflow.py            # LangGraph workflow definition
├── tests/
│   ├── test_base_agent.py
│   ├── test_inception_agent.py
│   ├── test_planning_agent.py
│   ├── test_construction_agent.py
│   ├── test_testing_agent.py
│   ├── test_operations_agent.py
│   ├── test_workflow.py
│   ├── test_workflow_approval.py
│   ├── test_checkpoint_recovery.py
│   ├── test_correction_loop.py
│   ├── test_version_history.py
│   ├── test_llm_provider.py
│   └── test_docker_integration.py
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Security

- API keys are read from environment variables only
- No hardcoded secrets in source code
- `.env` files are excluded via `.gitignore`
- Generated code never executes without human approval
- All test execution happens in Docker containers (no host execution)
- Version history tracks all code changes for auditability

## Known Limitations

1. **LLM API Dependencies**: System requires external LLM API access. Rate limits may affect availability.
2. **Integration Errors**: Not yet implemented (placeholder)
3. **Full Regression Suite**: Currently re-runs specific tests, not complete suite
4. **Operations Rollback**: Placeholder implementation
5. **Docker Required**: Test execution requires Docker Desktop

## License

MIT
