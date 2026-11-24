"""
TripMate AI - Database Repositories
Data access layer for trips, requests, itineraries, accommodations, and execution audits.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    AccommodationRecord,
    AgentExecutionRecord,
    AgentMessageRecord,
    ApprovalRecord,
    BudgetRecord,
    ItineraryDayRecord,
    ItineraryRecord,
    Trip,
    TripRequestRecord,
    User,
)
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import TripRequest, TripResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TripRepository:
    """Async repository managing trips and associated relational components."""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        full_name: str,
        api_key: Optional[str] = None,
    ) -> User:
        user = User(
            id=f"user_{uuid.uuid4().hex[:12]}",
            email=email,
            full_name=full_name,
            api_key=api_key or f"tk_{uuid.uuid4().hex}",
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_trip(
        db: AsyncSession,
        trip_request: TripRequest,
        custom_trip_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Trip:
        trip_id = custom_trip_id or f"trip_{uuid.uuid4().hex[:12]}"
        trip = Trip(
            id=trip_id,
            user_id=user_id,
            title=f"Trip to {trip_request.destination} ({trip_request.days} Days)",
            destination=trip_request.destination,
            status="PLANNED",
        )
        db.add(trip)

        req_record = TripRequestRecord(
            id=f"req_{uuid.uuid4().hex[:12]}",
            trip_id=trip_id,
            destination=trip_request.destination,
            days=trip_request.days,
            budget=trip_request.budget,
            currency=trip_request.currency,
            travelers=trip_request.travelers,
            interests_json=json.dumps(trip_request.interests),
            travel_dates=trip_request.travel_dates,
            special_requirements=trip_request.special_requirements,
        )
        db.add(req_record)
        await db.flush()
        logger.info("Persisted new Trip '%s' with Request in database", trip_id)
        return trip

    @staticmethod
    async def save_trip_response(
        db: AsyncSession,
        trip_id: str,
        response: TripResponse,
    ) -> Trip:
        stmt = select(Trip).where(Trip.id == trip_id)
        result = await db.execute(stmt)
        trip = result.scalar_one_or_none()
        if not trip:
            trip = Trip(
                id=trip_id,
                title=f"Trip to {response.destination}",
                destination=response.destination,
                status=response.status,
            )
            db.add(trip)

        trip.status = response.status

        # 1. Save Budget Breakdown
        if response.budget_analysis:
            b = response.budget_analysis
            budget_rec = BudgetRecord(
                id=f"bud_{uuid.uuid4().hex[:12]}",
                trip_id=trip_id,
                transportation=b.transportation,
                accommodation=b.accommodation,
                food=b.food,
                activities=b.activities,
                miscellaneous=b.miscellaneous,
                total_estimated_cost=b.total_estimated_cost,
                target_budget=b.target_budget,
                is_within_budget=b.is_within_budget,
                savings_or_deficit=b.savings_or_deficit,
                calculation_method=b.calculation_method,
            )
            db.add(budget_rec)

        # 2. Save Itinerary and Daily Schedule
        if response.itinerary:
            itin_rec = ItineraryRecord(
                id=f"itin_{uuid.uuid4().hex[:12]}",
                trip_id=trip_id,
                total_days=len(response.itinerary),
                total_estimated_cost=sum(d.estimated_daily_cost for d in response.itinerary),
                currency=response.currency,
            )
            db.add(itin_rec)
            await db.flush()

            for day in response.itinerary:
                day_rec = ItineraryDayRecord(
                    id=f"day_{uuid.uuid4().hex[:12]}",
                    itinerary_id=itin_rec.id,
                    day_number=day.day_number,
                    theme=day.theme,
                    morning_activities_json=json.dumps(day.morning_activities),
                    afternoon_activities_json=json.dumps(day.afternoon_activities),
                    evening_activities_json=json.dumps(day.evening_activities),
                    meal_recommendations_json=json.dumps(day.meal_recommendations),
                    estimated_daily_cost=day.estimated_daily_cost,
                    transit_tips=day.transit_tips,
                )
                db.add(day_rec)

        # 3. Save Accommodations
        if response.accommodation_options:
            for opt in response.accommodation_options:
                accom_rec = AccommodationRecord(
                    id=f"accom_{uuid.uuid4().hex[:12]}",
                    trip_id=trip_id,
                    name=opt.name,
                    property_type=opt.property_type,
                    location=opt.location,
                    price_per_night=opt.price_per_night,
                    total_price=opt.total_price,
                    currency=opt.currency,
                    rating=opt.rating,
                    amenities_json=json.dumps(opt.amenities),
                    booking_reference_url=opt.booking_reference_url,
                )
                db.add(accom_rec)

        await db.flush()
        logger.info("Saved complete multi-agent TripResponse into database for '%s'", trip_id)
        return trip

    @staticmethod
    async def get_trip(db: AsyncSession, trip_id: str) -> Optional[Trip]:
        stmt = (
            select(Trip)
            .where(Trip.id == trip_id)
            .options(
                selectinload(Trip.trip_request),
                selectinload(Trip.budget),
                selectinload(Trip.itinerary).selectinload(ItineraryRecord.days),
                selectinload(Trip.accommodations),
                selectinload(Trip.approvals),
                selectinload(Trip.agent_executions),
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_trips(db: AsyncSession, limit: int = 50) -> List[Trip]:
        stmt = select(Trip).order_by(desc(Trip.created_at)).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def record_approval(
        db: AsyncSession,
        trip_id: str,
        decision: str,
        comment: Optional[str] = None,
        reviewer_id: Optional[str] = None,
    ) -> ApprovalRecord:
        rec = ApprovalRecord(
            id=f"appr_{uuid.uuid4().hex[:12]}",
            trip_id=trip_id,
            status=decision,
            reviewer_id=reviewer_id or "reviewer",
            comment=comment,
            decided_at=datetime.now(timezone.utc),
        )
        db.add(rec)
        await db.flush()
        return rec

    @staticmethod
    async def record_agent_execution(
        db: AsyncSession,
        trip_id: str,
        execution_result: AgentExecutionResult,
    ) -> AgentExecutionRecord:
        tok = execution_result.token_usage
        exec_rec = AgentExecutionRecord(
            id=f"exec_{uuid.uuid4().hex[:12]}",
            trip_id=trip_id,
            agent_name=execution_result.agent_name,
            status=execution_result.status,
            latency_ms=execution_result.latency_ms,
            prompt_tokens=tok.prompt_tokens if tok else 0,
            completion_tokens=tok.completion_tokens if tok else 0,
            total_tokens=tok.total_tokens if tok else 0,
            estimated_cost_usd=tok.estimated_cost_usd if tok else 0.0,
        )
        db.add(exec_rec)
        await db.flush()
        return exec_rec

