"""
TripMate AI - Database & SQLAlchemy Persistence Tests
Tests async database initialization, user management, trip persistence,
relational foreign-key cascades, and execution audit logging.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.base import Base
from app.database.repository import TripRepository
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import (
    AccommodationOption,
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
    TripResponse,
)


@pytest_asyncio.fixture
async def db_session():
    """Provides an isolated in-memory SQLite database session for unit tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_creation_and_lookup(db_session: AsyncSession):
    """Verify creating a user and finding by email."""
    user = await TripRepository.create_user(
        db=db_session,
        email="traveler@example.com",
        full_name="Priya Sharma",
    )
    assert user.id is not None
    assert user.email == "traveler@example.com"

    fetched = await TripRepository.get_user_by_email(db_session, "traveler@example.com")
    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.full_name == "Priya Sharma"


@pytest.mark.asyncio
async def test_trip_creation_and_retrieval(db_session: AsyncSession):
    """Verify trip creation with attached TripRequestRecord."""
    req = TripRequest(
        destination="Jaipur",
        days=3,
        budget=30000.0,
        currency="INR",
        travelers=2,
        interests=["forts", "palaces"],
    )
    trip = await TripRepository.create_trip(db_session, req, custom_trip_id="trip_test_001")
    assert trip.id == "trip_test_001"
    assert trip.destination == "Jaipur"
    assert trip.status == "PLANNED"

    retrieved = await TripRepository.get_trip(db_session, "trip_test_001")
    assert retrieved is not None
    assert retrieved.trip_request is not None
    assert retrieved.trip_request.budget == 30000.0
    assert retrieved.trip_request.days == 3


@pytest.mark.asyncio
async def test_save_trip_response_relational_tree(db_session: AsyncSession):
    """Verify saving a full TripResponse populates itineraries, days, budget, and stays."""
    trip_id = "trip_full_002"
    research = DestinationResearch(
        destination="Goa",
        overview="Coastal paradise with vibrant beaches and colonial heritage.",
        country="India",
    )
    budget = BudgetBreakdown.calculate(
        destination="Goa",
        days=3,
        travelers=2,
        target_budget=28000.0,
        transportation=7000,
        accommodation=10000,
        food=6000,
        activities=3000,
        miscellaneous=2000,
    )
    itinerary = [
        DailyItinerary(
            day_number=1,
            theme="Beach arrival",
            morning_activities=["Check-in"],
            afternoon_activities=["Calangute beach"],
            evening_activities=["Shack dinner"],
            estimated_daily_cost=3000.0,
        ),
        DailyItinerary(
            day_number=2,
            theme="Heritage & Forts",
            morning_activities=["Aguada fort"],
            afternoon_activities=["Anjuna cliff"],
            evening_activities=["Sunset market"],
            estimated_daily_cost=3500.0,
        ),
    ]
    accommodations = [
        AccommodationOption(
            name="Seaside Palms Resort",
            property_type="resort",
            location="Candolim, Goa",
            price_per_night=3500.0,
            total_price=7000.0,
            rating=4.5,
        )
    ]

    response = TripResponse(
        trip_id=trip_id,
        destination="Goa",
        days=2,
        travelers=2,
        currency="INR",
        research=research,
        budget_analysis=budget,
        itinerary=itinerary,
        accommodation_options=accommodations,
        status="SUCCESS",
    )

    saved_trip = await TripRepository.save_trip_response(db_session, trip_id, response)
    assert saved_trip.status == "SUCCESS"

    # Query back
    fetched = await TripRepository.get_trip(db_session, trip_id)
    assert fetched is not None
    assert fetched.budget is not None
    assert fetched.budget.total_estimated_cost == 28000.0
    assert fetched.itinerary is not None
    assert len(fetched.itinerary.days) == 2
    assert len(fetched.accommodations) == 1
    assert fetched.accommodations[0].name == "Seaside Palms Resort"


@pytest.mark.asyncio
async def test_record_approval_and_execution_audits(db_session: AsyncSession):
    """Verify recording human review decisions and agent turn audits."""
    trip_id = "trip_audit_003"
    req = TripRequest(destination="Kerala", days=4, budget=40000.0)
    await TripRepository.create_trip(db_session, req, custom_trip_id=trip_id)

    # Record human approval
    appr = await TripRepository.record_approval(
        db_session,
        trip_id=trip_id,
        decision="APPROVED",
        comment="Reviewed and confirmed by traveler.",
        reviewer_id="human_agent_1",
    )
    assert appr.status == "APPROVED"
    assert appr.trip_id == trip_id

    # Record agent execution audit
    agent_res = AgentExecutionResult(
        agent_name="ResearchAgent",
        status="success",
        latency_ms=120.5,
    )
    exec_rec = await TripRepository.record_agent_execution(db_session, trip_id, agent_res)
    assert exec_rec.agent_name == "ResearchAgent"
    assert exec_rec.latency_ms == 120.5

    # Check via get_trip
    trip = await TripRepository.get_trip(db_session, trip_id)
    assert len(trip.approvals) == 1
    assert len(trip.agent_executions) == 1

