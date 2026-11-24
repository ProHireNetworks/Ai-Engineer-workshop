# TripMate AI – Multi-Agent Travel Planning Assistant

TripMate AI is an enterprise-grade, backend-only multi-agent system designed to automate intelligent travel itinerary generation, real-time budget calculation, accommodation recommendations, and contextual travel knowledge retrieval (RAG).

Orchestrated with **LangGraph**, **FastAPI**, **Pydantic v2**, and **PostgreSQL with pgvector**, TripMate AI utilizes specialized autonomous agents cooperating to satisfy complex traveler constraints with human-in-the-loop governance.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Client (cURL / Postman)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   FastAPI REST API (/v1)    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Pydantic v2 Input Guard    |
                      +--------------+--------------+
                                     |
                                     v
                 +---------------------------------------+
                 | LangGraph Multi-Agent Orchestrator   |
                 |                                       |
                 |   +-------------------------------+   |
                 |   |  Parallel Execution Branch   |   |
                 |   |  - Research Agent             |   |
                 |   |  - Budget Agent (Deterministic)|   |
                 |   +---------------+---------------+   |
                 |                   |                   |
                 |                   v                   |
                 |   +-------------------------------+   |
                 |   |  Itinerary Agent              |   |
                 |   +---------------+---------------+   |
                 |                   |                   |
                 |                   v                   |
                 |   +-------------------------------+   |
                 |   |  Booking Assistant & RAG      |   |
                 |   +---------------+---------------+   |
                 |                   |                   |
                 |                   v                   |
                 |   +-------------------------------+   |
                 |   |  Validation & Conditional Hop |   |
                 |   +---------------+---------------+   |
                 |                   |                   |
                 |                   v                   |
                 |   +-------------------------------+   |
                 |   |  Human Approval (Pause/Resume)|   |
                 |   +-------------------------------+   |
                 +-------------------+-------------------+
                                     |
                                     v
                      +-----------------------------+
                      | PostgreSQL / pgvector Store |
                      +-----------------------------+
```

---

## Key Features

- **Coordinated Multi-Agent Architecture**: Discrete autonomous agents (Research, Budget, Itinerary, Booking Assistant) working in concert.
- **Deterministic Financial Computation**: Zero LLM hallucination for budgeting; strict mathematical accounting in Python.
- **Human-in-the-Loop (HITL)**: LangGraph checkpointed execution allows workflows to pause for traveler approval and resume safely.
- **RAG Knowledge Retrieval**: Curated destination guides, regional logistics, and attractions retrieved using semantic vector similarity.
- **Defense-in-Depth Security**: Prompt injection guards, untrusted input isolation, schema validation, and secret sanitization.
- **Production-Ready Observability**: Structured JSON logging, contextual request correlation IDs (`X-Request-ID`), and execution latency tracking.

---

## Technology Stack

- **Runtime**: Python 3.11+
- **API Framework**: FastAPI, Uvicorn, Starlette
- **Agent Orchestration**: LangGraph, LangChain Core
- **Data Validation**: Pydantic v2, Pydantic Settings
- **Database & Vectors**: PostgreSQL 16, SQLAlchemy 2.0 (Async), Alembic, pgvector
- **Testing**: Pytest, Pytest-Asyncio, HTTPX
- **Containerization**: Docker, Docker Compose

---

## Directory Structure

```
tripmate-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application entrypoint & middlewares
│   │   ├── config.py            # Pydantic Settings v2 configuration
│   │   ├── api/                 # Versioned REST API endpoints
│   │   │   ├── router.py        # Central API router
│   │   │   └── v1/
│   │   │       ├── health.py    # System health & readiness endpoint
│   │   │       ├── llm.py       # LLM diagnostics, status & chat endpoints
│   │   │       ├── tools.py     # Tool catalog & ad-hoc execution endpoints
│   │   │       └── trips.py     # Trip parameter validation endpoint
│   │   ├── llm/                 # Provider abstraction (OpenAI, Ollama, Mock)
│   │   │   ├── base.py          # BaseLLMProvider interface
│   │   │   ├── factory.py       # Provider instantiation factory
│   │   │   ├── openai_provider.py # Async OpenAI integration with function calling
│   │   │   ├── ollama_provider.py # Local Ollama REST client with tool calling
│   │   │   ├── mock_provider.py   # Deterministic offline mock provider
│   │   │   ├── usage.py         # Token accounting, messages & response models
│   │   │   └── exceptions.py    # Unified exception hierarchy
│   │   ├── prompts/             # Agent prompts & formatting templates
│   │   │   ├── system_prompts.py# Role definitions & safety guardrails
│   │   │   └── templates.py     # Prompt parameter formatters
│   │   ├── tools/               # External tools & mathematical engines
│   │   │   ├── base.py          # BaseTool abstract class with Pydantic validation
│   │   │   ├── registry.py      # Centralized ToolRegistry
│   │   │   ├── executor.py      # Async ToolExecutor with timeouts & retries
│   │   │   ├── schemas.py       # Pydantic v2 argument schemas
│   │   │   ├── exceptions.py    # Tool error classification
│   │   │   ├── travel_search.py # Destination, attraction & transit tools
│   │   │   ├── weather.py       # Weather & climate forecasting tool
│   │   │   ├── cost_calculator.py # Deterministic Python arithmetic budget calculator
│   │   │   └── accommodation.py # Lodging & hotel discovery tool
│   │   ├── schemas/             # Pydantic v2 domain schemas
│   │   │   ├── trip.py          # TripRequest, DestinationResearch, BudgetBreakdown
│   │   │   ├── tool.py          # ToolDefinition, ToolCall, ToolCallResult
│   │   │   ├── agent_output.py  # AgentExecutionResult envelope
│   │   │   ├── health.py        # HealthResponse schema
│   │   │   └── llm.py           # LLMStatusResponse schema
│   │   ├── services/            # Domain business logic
│   │   │   └── tool_calling_service.py # Multi-turn tool execution reasoning loop
│   │   ├── rag/                 # Retrieval Augmented Generation engine
│   │   ├── database/            # SQLAlchemy models & connection pool
│   │   ├── security/            # Prompt injection defense & auth
│   │   ├── evaluation/          # Benchmark eval & metrics
│   │   └── utils/               # Structured JSON logger & helpers
│   ├── tests/                   # Pytest test suite
│   ├── requirements.txt         # Pinned python dependencies
│   └── Dockerfile               # Production multi-stage Docker build
├── knowledge_base/              # Source travel documentation
├── benchmark/                   # Multi-scenario evaluation test cases
├── scripts/                     # PowerShell automation scripts
├── docs/                        # Detailed architecture & API docs
├── docker-compose.yml           # Local multi-service orchestration
└── .env.example                 # Environment variables template
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.11 or newer (Python 3.14 verified)
- Git
- Docker & Docker Compose (optional for local DB)

### 2. Create Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### 4. Configure Environment
```powershell
Copy-Item .env.example .env
```

### 5. LLM Provider Configuration

TripMate AI allows seamless switching between LLM backends via `.env`:

#### A. Offline Simulation / Mock Provider (Default)
```ini
LLM_PROVIDER=mock
OPENAI_MODEL=gpt-4o
```
*Zero API keys or external services required; produces deterministic mock responses clearly tagged with `[MOCK DATA]`.*

#### B. OpenAI Cloud Provider
```ini
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3
```

#### C. Ollama Local Models
1. Install [Ollama](https://ollama.com/) on your host machine.
2. Pull the desired model:
   ```bash
   ollama pull llama3.1
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```
4. Set `.env` to:
   ```ini
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1
   LLM_TIMEOUT=120
   ```

---

## Running the Application

### Local Development Server
```powershell
.\scripts\run_dev.ps1
```
Or directly using Uvicorn:
```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Verification & Documentation
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## Running Automated Tests

Run the complete test suite:
```powershell
.\scripts\run_tests.ps1
```
Or directly with Pytest:
```powershell
cd backend
python -m pytest tests/ -v
```

---

## Docker Deployment

To launch the backend alongside PostgreSQL and pgvector:
```powershell
docker-compose up --build -d
```
Inspect logs:
```powershell
docker-compose logs -f backend
```
Stop services:
```powershell
docker-compose down
```

