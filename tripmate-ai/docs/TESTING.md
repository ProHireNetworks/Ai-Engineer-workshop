# TripMate AI Testing Strategy

## Test Layers
1. **Unit Tests**:
   - Pydantic schema validation (`TripRequest`, `DestinationResearch`, `BudgetBreakdown`, `Attraction`, `DailyItinerary`).
   - LLM provider abstraction, factory selection, token usage math, and error translation.
   - Mock provider deterministic generation and dynamic Pydantic object synthesis.
   - Mocked OpenAI provider tests (completions, structured output parsing, tool calling, rate limits, timeouts).
   - Mocked Ollama provider tests (JSON chat completions, tool calling, connection refusal, version health check).
   - Tool registry tests (registration, duplicate prevention, unknown tool rejection, schema exports).
   - Tool execution engine tests (pure deterministic budget calculations, weather, destinations, timeouts, retries, authorization).
   - Tool argument validation tests (Pydantic type checks, positive bounds, empty input rejection).
   - Multi-turn tool calling loop tests (autonomous tool execution, max rounds termination).
   - Prompt guard security sanitizer.
2. **Integration Tests**:
   - FastAPI endpoints:
     - `GET /api/v1/health`
     - `GET /api/v1/llm/status`
     - `POST /api/v1/llm/chat` (multi-turn tool calling chat)
     - `GET /api/v1/tools` (catalog discovery)
     - `POST /api/v1/tools/execute` (ad-hoc tool execution)
     - `POST /api/v1/trips/validate` (trip parameter validation)
   - LangGraph StateGraph traversal with mocked LLM outputs (Phase 5).
   - Database model operations with test database (Phase 10).
3. **Security Tests**:
   - Known prompt injection payloads and malformed JSON resistance.
   - Authentication token tampering and unauthorized trip access.
4. **Agent Quality Evaluation**:
   - 30-case benchmark dataset evaluating plan feasibility, budget accuracy, and itinerary completeness.

## Running Tests Locally
```powershell
.\scripts\run_tests.ps1
```
Or directly:
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```

