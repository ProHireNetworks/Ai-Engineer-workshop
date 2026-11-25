# TripMate AI Agent Workflow

## LangGraph Multi-Agent Orchestration

The system employs LangGraph `StateGraph` to manage multi-agent state progression, conditional decision making, error loops, and human-in-the-loop pauses.

### Agents Roster
1. **Research Agent**: Scours destinations, tourist attractions, local culture, climate considerations, and activities.
2. **Budget Agent**: Performs strictly deterministic arithmetic for transportation, lodging, food, and activity costs against user budget constraints.
3. **Itinerary Agent**: Schedules day-wise activities optimized for geographical clustering, realistic pacing, and rest periods.
4. **Booking Assistant Agent**: Formulates lodging and transit recommendations with external reference links, requiring explicit user authorization before actions.

### State Transitions
- **Parallel Fan-out**: Research Agent and Budget Agent begin concurrently upon request submission.
- **Join & Synthesis**: Itinerary Agent consumes findings from both Research and Budget agents.
- **RAG Enrichment**: Retrieves curated local knowledge documents to enhance the itinerary.
- **Validation Node**: Verifies schema compliance, budget feasibility, and timing realism.
- **Conditional Routing**:
  - If budget constraint violated -> route back to refinement.
  - If schema or schedule invalid -> route to revision.
  - If valid -> route to human approval pause.
- **Human Approval**: Interrupts execution, emits pending approval event, and resumes upon user confirmation.

