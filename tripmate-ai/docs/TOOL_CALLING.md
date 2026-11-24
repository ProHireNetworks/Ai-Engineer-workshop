# TripMate AI Tool Calling & Function Calling Framework

## 1. Overview
TripMate AI features a centralized, vendor-agnostic tool calling framework decoupled from individual agents. Models can inspect available tools, decide which tools to invoke, emit argument payloads, have them validated through Pydantic v2, execute them via a secured `ToolExecutor`, and consume the results in iterative reasoning loops.

```
+-------------------------------------------------------------+
|                     User Travel Request                     |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|           LLM Invocation with Registered Tools              |
|        (OpenAI function calling / Ollama / Mock)            |
+------------------------------+------------------------------+
                               |
                               v (Decision: Tool calls required)
+-------------------------------------------------------------+
|                   Tool Execution Engine                     |
|  1. Lookup in ToolRegistry                                  |
|  2. Validate arguments via Pydantic                         |
|  3. Verify authorization (requires_auth)                    |
|  4. Concurrently execute independent tools                  |
|  5. Wrap result in standardized ToolCallResult              |
+------------------------------+------------------------------+
                               |
                               v (Tool Results fed to model)
+-------------------------------------------------------------+
|              LLM Follow-up / Multi-Turn Loop                |
|      (Repeats up to max_rounds safety threshold)            |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|          Synthesized Output or Validated Schema             |
+-------------------------------------------------------------+
```

---

## 2. Standard Registered Tools

| Tool Name | Purpose | Key Parameters | Output |
| :--- | :--- | :--- | :--- |
| `search_destination` | Discover regional culture, highlights, and climate | `destination`, `interests` | Overview, currency, best time |
| `search_attractions` | Look up tourist sights, monuments, and duration | `destination`, `category`, `limit` | List of `Attraction` objects |
| `get_weather` | Seasonal forecast and temperature suitability | `destination`, `travel_date` | `WeatherInformation` |
| `calculate_trip_budget` | Pure deterministic financial arithmetic | `transportation`, `accommodation`, `food`, `activities`, `miscellaneous`, `currency` | Exact totals, budget variance |
| `estimate_travel_time` | Point-to-point distance and travel duration | `origin`, `destination`, `mode` | Distance in km, minutes, notes |
| `search_accommodation` | Lodging options by budget tier | `destination`, `guests`, `budget_tier` | List of `AccommodationOption` |

---

## 3. Tool Calling Workflow & Examples

### A. Executing a Tool Ad-Hoc via API

**Endpoint**: `POST /api/v1/tools/execute`

**Request Payload**:
```json
{
  "tool_name": "calculate_trip_budget",
  "arguments": {
    "transportation": 3000.0,
    "accommodation": 6000.0,
    "food": 4000.0,
    "activities": 2000.0,
    "miscellaneous": 1000.0,
    "currency": "INR",
    "target_budget": 20000.0,
    "days": 3,
    "travelers": 2
  }
}
```

**Response Payload**:
```json
{
  "execution_id": "api_bf389e22",
  "tool_name": "calculate_trip_budget",
  "status": "success",
  "result": {
    "destination": "Trip Target",
    "days": 3,
    "travelers": 2,
    "currency": "INR",
    "transportation": 3000.0,
    "accommodation": 6000.0,
    "food": 4000.0,
    "activities": 2000.0,
    "miscellaneous": 1000.0,
    "total_estimated_cost": 16000.0,
    "target_budget": 20000.0,
    "is_within_budget": true,
    "savings_or_deficit": 4000.0,
    "calculation_method": "deterministic_python",
    "daily_average": 5333.33,
    "per_traveler_cost": 8000.0,
    "is_mock": false
  },
  "error": null,
  "latency_ms": 0.2
}
```

---

### B. Chat with Multi-Turn Tool Calling

**Endpoint**: `POST /api/v1/llm/chat`

**Request Payload**:
```json
{
  "message": "Plan a 3-day budget trip to Jaipur under 20000 INR",
  "enable_tools": true
}
```

**Response Payload**:
```json
{
  "response": "Here is a proposed 3-day trip to Jaipur incorporating historical highlights and budget-friendly activities...",
  "tool_calls_executed": [
    {
      "tool_call_id": "call_a0964015",
      "tool_name": "search_destination",
      "status": "success",
      "result": { ... },
      "error": null,
      "latency_ms": 0.4,
      "is_mock": true
    },
    {
      "tool_call_id": "call_8a6f9e6e",
      "tool_name": "get_weather",
      "status": "success",
      "result": { ... },
      "error": null,
      "latency_ms": 0.3,
      "is_mock": true
    },
    {
      "tool_call_id": "call_70069227",
      "tool_name": "calculate_trip_budget",
      "status": "success",
      "result": { ... },
      "error": null,
      "latency_ms": 0.2,
      "is_mock": false
    }
  ],
  "token_usage": {
    "prompt_tokens": 120,
    "completion_tokens": 85,
    "total_tokens": 205,
    "estimated_cost_usd": 0.00115
  }
}
```

---

## 4. Error Handling & Safety

1. **Argument Validation**: All arguments are validated using Pydantic `args_schema`. Malformed types or missing fields trigger `ToolValidationError` without crashing the application.
2. **Timeout Enforcement**: Every tool execution is bounded by `timeout_seconds` using `asyncio.wait_for`. Exceeded limits return `ToolCallResult(status="timeout")`.
3. **Authorization Isolation**: Any tool marked `requires_auth=True` checks permissions prior to execution. Unauthorized calls return `status="unauthorized"`.
4. **Loop Protection**: `ToolCallingService` enforces a `max_rounds=5` threshold to prevent infinite LLM recursion.
5. **Code Execution Guard**: Arbitrary Python code execution (`eval`, `exec`, shell scripts) is strictly prohibited.

