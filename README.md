# Mini AI-DLC

An AI Software Delivery Assistant that demonstrates an AI-Driven Development Life Cycle (AI-DLC) using Agentic AI.

## Overview

Mini AI-DLC automates software development through three phases:
- **Inception**: Requirements analysis, architecture design, and task breakdown
- **Construction**: Code generation and testing with human approval
- **Operations**: Deployment documentation and monitoring planning

The system features human-in-the-loop approval gates at critical decision points.

## Technology Stack

- **Python 3.8+** (tested with Python 3.14.6)
- **LangGraph**: Workflow orchestration and state management
- **LangChain**: LLM integration framework
- **Groq**: LLM provider for fast inference
- **Pydantic**: Data validation and schema definition
- **Pytest**: Automated testing framework

## Phase 1 Implementation (Current)

Phase 1 establishes the core foundation with:
- Project structure and configuration
- State schema with extensible fields for future features
- Base Agent with LLM initialization
- Inception Agent for requirements analysis
- Basic LangGraph workflow
- Comprehensive test suite with mocked LLM responses

### Features

- Modular architecture designed for future enhancements:
  - Business requirement change detection
  - Impact analysis
  - Task replanning
  - Human approval workflows
- All tests use mocked LLM responses (no API key required for testing)
- API keys loaded from environment variables only
- `.gitignore` configured to exclude sensitive files

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
# Edit .env and add your GROQ_API_KEY
```

## Running Tests

All tests use mocked LLM responses and do not require a real Groq API key:

```bash
pytest tests/ -v
```

Expected output: 28 passed in ~0.4s

## Project Structure

```
Mini AI-DLC/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Base agent with LLM initialization
│   └── inception_agent.py     # Requirements analysis agent
├── graph/
│   ├── __init__.py
│   ├── state.py               # Workflow state schema
│   └── workflow.py            # LangGraph workflow definition
├── tests/
│   ├── __init__.py
│   ├── test_state.py          # State schema tests
│   ├── test_base_agent.py     # Base agent tests
│   ├── test_inception_agent.py
│   └── test_workflow.py       # Workflow tests
├── docs/
│   ├── requirements.md        # Project requirements
│   ├── architecture.md        # System architecture
│   └── implementation_plan.md  # Implementation phases
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
- Generated code never executes without human approval (future phases)

## Documentation

- [Requirements](docs/requirements.md) - Detailed project requirements
- [Architecture](docs/architecture.md) - System architecture and design
- [Implementation Plan](docs/implementation_plan.md) - Phase-by-phase implementation plan

## Future Phases

The implementation plan includes 8 phases:
- Phase 1: Core Foundation ✓ (completed)
- Phase 2: Persistence Layer (SQLite checkpointing)
- Phase 3: Human Approval Gates
- Phase 4: Construction Agent
- Phase 5: RAG Integration
- Phase 6: FastAPI Backend
- Phase 7: Operations Agent
- Phase 8: End-to-End Integration

See [implementation_plan.md](docs/implementation_plan.md) for details.

## License

MIT
