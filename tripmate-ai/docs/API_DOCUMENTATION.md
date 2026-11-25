# TripMate AI API Documentation

TripMate AI exposes clean RESTful endpoints versioned under `/api/v1`.

## Endpoints Summary

### Health
- `GET /api/v1/health`
  - Summary: System health & subsystem status.
  - Returns: `200 OK` with JSON payload confirming API, database, and LLM provider readiness.

### LLM Provider
- `GET /api/v1/llm/status`
  - Summary: Live operational status of active LLM provider, model name, and reachability.
  - Returns: `200 OK` with `LLMStatusResponse` (never exposes secret keys).
- `POST /api/v1/llm/chat`
  - Summary: Conversational endpoint with multi-turn tool calling.
  - Request Body: `{"message": "Plan a 3-day trip to Goa", "enable_tools": true}`
  - Returns: `200 OK` with `ChatResponse` (assistant text, tool results audit, and token usage).

### Tools
- `GET /api/v1/tools`
  - Summary: List all registered tools, descriptions, and JSON parameter schemas.
  - Returns: `200 OK` with `List[ToolDefinition]`.
- `POST /api/v1/tools/execute`
  - Summary: Execute a registered tool ad-hoc with Pydantic argument validation.
  - Request Body: `{"tool_name": "calculate_trip_budget", "arguments": { ... }}`
  - Returns: `200 OK` with `ToolExecuteResponse`.

### Trips
- `POST /api/v1/trips/validate`
  - Summary: Validates `TripRequest` parameters against duration bounds, budget feasibility, and ISO currency rules.
  - Request Body: `TripRequest`
  - Returns: `200 OK` on validation success (`TripValidateResponse`) or `422 Unprocessable Entity` with error details.
- `POST /api/v1/trips/plan`: Submit travel requirements to generate a complete multi-agent trip plan (Phase 5).
- `GET /api/v1/trips/{trip_id}`: Retrieve a specific trip and its day-wise itinerary (Phase 5).
- `GET /api/v1/trips`: List existing trips for authenticated user (Phase 10).
- `POST /api/v1/trips/{trip_id}/modify`: Request itinerary revision (Phase 6).

### Human Approval
- `GET /api/v1/approvals/{trip_id}`: Check pending approval requests.
- `POST /api/v1/approvals/{trip_id}/approve`: Approve proposed itinerary and resume execution.
- `POST /api/v1/approvals/{trip_id}/reject`: Reject proposed itinerary or provide feedback.

### Agents
- `GET /api/v1/agents/status`: Status of available agent modules.
- `GET /api/v1/agents/{trip_id}/execution`: Detailed execution history and state graph trace.

### Knowledge / RAG
- `POST /api/v1/knowledge/ingest`: Ingest travel guide documents into vector store.
- `POST /api/v1/knowledge/search`: Query semantic vector store.

