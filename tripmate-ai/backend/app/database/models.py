"""
TripMate AI - SQLAlchemy 2.0 Database Models
Defines persistent ORM schemas for users, trips, requests, itineraries, budgets,
accommodations, agent executions, human reviews, documents, and evaluations.
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    """User account entity managing authentication and trip ownership."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    trips: Mapped[List["Trip"]] = relationship("Trip", back_populates="user", cascade="all, delete-orphan")


class Trip(Base):
    """Top-level trip entity correlating requirements, itineraries, budgets, and executions."""

    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PLANNED", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="trips")
    trip_request: Mapped[Optional["TripRequestRecord"]] = relationship(
        "TripRequestRecord", back_populates="trip", uselist=False, cascade="all, delete-orphan"
    )
    itinerary: Mapped[Optional["ItineraryRecord"]] = relationship(
        "ItineraryRecord", back_populates="trip", uselist=False, cascade="all, delete-orphan"
    )
    budget: Mapped[Optional["BudgetRecord"]] = relationship(
        "BudgetRecord", back_populates="trip", uselist=False, cascade="all, delete-orphan"
    )
    accommodations: Mapped[List["AccommodationRecord"]] = relationship(
        "AccommodationRecord", back_populates="trip", cascade="all, delete-orphan"
    )
    agent_executions: Mapped[List["AgentExecutionRecord"]] = relationship(
        "AgentExecutionRecord", back_populates="trip", cascade="all, delete-orphan"
    )
    approvals: Mapped[List["ApprovalRecord"]] = relationship(
        "ApprovalRecord", back_populates="trip", cascade="all, delete-orphan"
    )


class TripRequestRecord(Base):
    """Normalized record of the user's raw trip planning request."""

    __tablename__ = "trip_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), index=True, nullable=False)
    destination: Mapped[str] = mapped_column(String(100), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    travelers: Mapped[int] = mapped_column(Integer, default=1)
    interests_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    travel_dates: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    special_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    trip: Mapped["Trip"] = relationship("Trip", back_populates="trip_request")


class DestinationRecord(Base):
    """Destination profile and regional travel metadata."""

    __tablename__ = "destinations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(100), default="Unknown")
    overview: Mapped[str] = mapped_column(Text, nullable=False)
    best_time_to_visit: Mapped[str] = mapped_column(String(100), default="October to March")
    local_currency: Mapped[str] = mapped_column(String(10), default="INR")
    attractions_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ItineraryRecord(Base):
    """Parent itinerary entity representing the multi-day plan schedule."""

    __tablename__ = "itineraries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), index=True, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False)
    total_estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    trip: Mapped["Trip"] = relationship("Trip", back_populates="itinerary")
    days: Mapped[List["ItineraryDayRecord"]] = relationship(
        "ItineraryDayRecord", back_populates="itinerary", cascade="all, delete-orphan"
    )


class ItineraryDayRecord(Base):
    """Day-wise schedule breakdown with time slot activities."""

    __tablename__ = "itinerary_days"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    itinerary_id: Mapped[str] = mapped_column(ForeignKey("itineraries.id"), index=True, nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str] = mapped_column(String(200), default="Exploration")
    morning_activities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    afternoon_activities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evening_activities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meal_recommendations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_daily_cost: Mapped[float] = mapped_column(Float, default=0.0)
    transit_tips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    itinerary: Mapped["ItineraryRecord"] = relationship("ItineraryRecord", back_populates="days")


class AccommodationRecord(Base):
    """Vetted lodging recommendations for a trip."""

    __tablename__ = "accommodations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), default="hotel")
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    price_per_night: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    rating: Mapped[float] = mapped_column(Float, default=4.0)
    amenities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    booking_reference_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="accommodations")


class BudgetRecord(Base):
    """Deterministic categorical budget breakdown."""

    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), index=True, nullable=False)
    transportation: Mapped[float] = mapped_column(Float, nullable=False)
    accommodation: Mapped[float] = mapped_column(Float, nullable=False)
    food: Mapped[float] = mapped_column(Float, nullable=False)
    activities: Mapped[float] = mapped_column(Float, nullable=False)
    miscellaneous: Mapped[float] = mapped_column(Float, nullable=False)
    total_estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    target_budget: Mapped[float] = mapped_column(Float, nullable=False)
    is_within_budget: Mapped[bool] = mapped_column(Boolean, nullable=False)
    savings_or_deficit: Mapped[float] = mapped_column(Float, nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(50), default="deterministic_python")

    trip: Mapped["Trip"] = relationship("Trip", back_populates="budget")


class AgentExecutionRecord(Base):
    """Audit log of an individual agent node execution turn."""

    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    trip: Mapped["Trip"] = relationship("Trip", back_populates="agent_executions")
    messages: Mapped[List["AgentMessageRecord"]] = relationship(
        "AgentMessageRecord", back_populates="execution", cascade="all, delete-orphan"
    )


class AgentMessageRecord(Base):
    """Prompt, response, or tool message generated during agent reasoning."""

    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(ForeignKey("agent_executions.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    execution: Mapped["AgentExecutionRecord"] = relationship("AgentExecutionRecord", back_populates="messages")


class ApprovalRecord(Base):
    """Audit record of human-in-the-loop authorization decisions."""

    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="approvals")


class TravelDocumentRecord(Base):
    """Vector database document record for knowledge base indexing."""

    __tablename__ = "travel_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    embedding_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EvaluationResultRecord(Base):
    """Persistent benchmark evaluation score records."""

    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False)
    budget_accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    errors_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

