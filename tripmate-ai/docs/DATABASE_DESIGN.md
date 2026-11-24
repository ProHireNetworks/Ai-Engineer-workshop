# TripMate AI Database Design

## Technology: PostgreSQL 16 + pgvector + SQLAlchemy 2.0 (Async) + Alembic

### Entities & Relationships
1. **users**: Primary user entity with credential hashes and role flags.
2. **trips**: Main trip envelope containing destination, dates, currency, and overall status.
3. **trip_requests**: Raw validated initial user request parameters.
4. **destinations**: Destination metadata, coordinates, climate, and currency notes.
5. **itineraries**: Multi-day itinerary container linked to a trip.
6. **itinerary_days**: Daily breakdown with morning, afternoon, evening slots.
7. **accommodation_recommendations**: Lodging options with price tiers and links.
8. **budget_breakdowns**: Cost categories with deterministic breakdowns.
9. **agent_executions**: Audit logs of agent node runs and tool invocations.
10. **agent_messages**: Intermediate communication exchanges between agents.
11. **approval_requests**: Human approval records (PENDING, APPROVED, REJECTED).
12. **travel_documents**: RAG knowledge documents with embeddings in pgvector.
13. **evaluation_results**: Benchmark and performance evaluation records.

