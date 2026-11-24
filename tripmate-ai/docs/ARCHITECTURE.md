# TripMate AI Architecture

## 1. Overview
TripMate AI is an agentic backend designed for travel planning. It coordinates multiple specialized AI agents using LangGraph, provides REST APIs through FastAPI, validates data with Pydantic v2, and persists states and checkpoints in PostgreSQL with pgvector.

```
USER / EXTERNAL CLIENT
        |
        v
FASTAPI REST API (/api/v1)
        |
        v
REQUEST VALIDATION (Pydantic v2)
        |
        v
TRIP PLANNING SERVICE
        |
        v
LANGGRAPH ORCHESTRATOR (StateGraph)
        |
        +----------------------+
        |                      |
        v                      v
   RESEARCH AGENT         BUDGET AGENT
  (Attractions, POIs)   (Deterministic Math)
        |                      |
        +----------+-----------+
                   |
                   v
             ITINERARY AGENT
        (Daily Schedule & Routes)
                   |
                   v
             BOOKING ASSISTANT
         (Lodging & Transport Recs)
                   |
                   v
             RAG RETRIEVAL
        (Curated Travel Context)
                   |
                   v
           VALIDATION ENGINE
                   |
          CONDITIONAL ROUTING
             +-----+-----+
             |           |
             v           v
          APPROVE      REVISE
             |
             v
        HUMAN APPROVAL
        (Interrupt & Resume)
             |
             v
      POSTGRESQL STORAGE
             |
             v
      STRUCTURED JSON OUTPUT
```

## 2. Core Modules
- **API Layer (`backend/app/api/`)**: FastAPI versioned endpoints (`/api/v1`) for health, llm status, tools catalog, tool execution, trips validation, approvals, agent status, and knowledge ingestion.
- **LLM Abstraction (`backend/app/llm/`)**: Pluggable provider interface (`BaseLLMProvider`) with adapters for `OpenAIProvider`, `OllamaProvider`, and `MockLLMProvider`, coordinated by `get_llm_provider()` factory. Includes token accounting (`TokenUsage`) and granular error translation.
- **Prompts & Guardrails (`backend/app/prompts/`)**: Authoritative system prompts and parameter templates for Research, Budget, Itinerary, Booking Assistant, and Prompt Guard.
- **Tools & Function Calling (`backend/app/tools/`)**: Tool schemas, registry (`ToolRegistry`), and execution engine (`ToolExecutor`) providing deterministic budget math, weather forecasts, attraction searches, and transit estimation.
- **Tool Calling Service (`backend/app/services/tool_calling_service.py`)**: Multi-turn reasoning loop driving model tool requests, parallel tool execution, and synthesized response generation.
- **Pydantic Validation (`backend/app/schemas/`)**: Schemas for trips (`TripRequest`, `TripResponse`, `BudgetBreakdown`, `Attraction`, `DailyItinerary`), tools (`ToolDefinition`, `ToolCall`, `ToolCallResult`), and execution results (`AgentExecutionResult`).
- **Agents (`backend/app/agents/`)**: Specialized autonomous workers (Research, Budget, Itinerary, Booking).
- **Graph (`backend/app/graph/`)**: LangGraph StateGraph, conditional edges, retry policies, and checkpointing.
- **RAG (`backend/app/rag/`)**: Knowledge ingestion, chunking, embeddings, vector storage, and similarity retrieval.
- **Security (`backend/app/security/`)**: Prompt guard, input sanitization, JWT authentication, and authorization checks.
- **Database (`backend/app/database/`)**: SQLAlchemy 2.0 async models and Alembic migrations.

## 3. LLM Provider Architecture
The LLM module shields agent code from vendor-specific libraries:
```
           +-----------------------+
           | Agent / Service Logic |
           +-----------+-----------+
                       |
                       v
           +-----------------------+
           |    BaseLLMProvider    |
           |  (generate, parse)    |
           +-----------+-----------+
                       |
        +--------------+---------------+
        |              |               |
        v              v               v
+---------------+ +----------+ +---------------+
| OpenAIProvider| |  Ollama  | | MockProvider  |
| (AsyncOpenAI) | | (HTTPX)  | | (Offline Test)|
+---------------+ +----------+ +---------------+
```

## 4. Tool Execution & Reasoning Architecture
The tool calling framework enables autonomous multi-turn gathering of ground truth:
```
         +-----------------------+
         | ToolCallingService    |
         +-----------+-----------+
                     |
                     v
         +-----------------------+
         | Provider with Tools   |
         | (emits ToolCall list) |
         +-----------+-----------+
                     |
                     v
         +-----------------------+
         |     ToolExecutor      |
         | (concurrent & guarded)|
         +-----------+-----------+
                     |
         +-----------+-----------+
         |           |           |
         v           v           v
    [Weather]    [Budget]   [Attractions]
         |           |           |
         +-----------+-----------+
                     |
                     v
         +-----------------------+
         | Model Follow-up Turn  |
         | (Synthesized Response)|
         +-----------------------+
```
