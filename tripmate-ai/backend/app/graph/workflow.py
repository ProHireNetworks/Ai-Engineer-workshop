"""
TripMate AI - LangGraph Workflow Definition
Constructs the multi-agent StateGraph connecting Research, Budget, Itinerary,
Booking, Validation, Human Approval, and Finalization with checkpointing.
"""

from typing import Any, Dict, List, Literal, Optional
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes import (
    approval_node,
    booking_node,
    budget_node,
    finalize_node,
    itinerary_node,
    research_node,
    validation_node,
)
from app.graph.state import TripState
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Global checkpointer instance supporting both synchronous and asynchronous invocations
_default_checkpointer: Optional[BaseCheckpointSaver] = None


def get_default_checkpointer() -> BaseCheckpointSaver:
    """
    Returns the checkpointer for the LangGraph StateGraph.
    Uses MemorySaver to ensure full compatibility with both synchronous
    and asynchronous graph invocations (ainvoke / astream / aget_tuple).
    Persistent trip and execution states are persisted to the database via TripRepository.
    """
    global _default_checkpointer
    if _default_checkpointer is None:
        _default_checkpointer = MemorySaver()
        logger.info("Initialized MemorySaver checkpointer supporting sync and async execution")
    return _default_checkpointer


def route_after_validation(state: TripState) -> Literal["itinerary", "approval", "finalize"]:
    """
    Conditional routing edge evaluating validation state:
    - Retries itinerary generation if invalid and revision limit not reached.
    - Routes to approval if valid and approval is pending.
    - Routes directly to finalize if approved or approval not required.
    """
    is_valid = state.get("is_valid", True)
    revision_count = state.get("revision_count", 0)
    approval_status = state.get("approval_status", "NOT_REQUIRED")

    if not is_valid:
        if revision_count < 3:
            logger.info("Validation failed, routing to 'itinerary' for revision %d", revision_count)
            return "itinerary"
        else:
            logger.warning("Max revisions reached, proceeding to 'finalize' with errors")
            return "finalize"

    if approval_status == "PENDING":
        logger.info("Validation passed, routing to 'approval' for human sign-off")
        return "approval"

    logger.info("Validation passed and approved, routing to 'finalize'")
    return "finalize"


def build_trip_graph(
    checkpointer: Optional[BaseCheckpointSaver] = None,
    require_approval: bool = True,
) -> CompiledStateGraph:
    """
    Builds and compiles the complete LangGraph StateGraph for TripMate AI.
    
    Args:
        checkpointer: Checkpoint saver for state persistence and recovery.
        require_approval: Whether to interrupt before the approval node.
    """
    builder = StateGraph(TripState)

    # 1. Add all functional nodes
    builder.add_node("research", research_node)
    builder.add_node("budget", budget_node)
    builder.add_node("itinerary", itinerary_node)
    builder.add_node("booking", booking_node)
    builder.add_node("validation", validation_node)
    builder.add_node("approval", approval_node)
    builder.add_node("finalize", finalize_node)

    # 2. Add structural edges
    # Fan-out: parallel execution of research and budget
    builder.add_edge(START, "research")
    builder.add_edge(START, "budget")

    # Fan-in: both feed into itinerary
    builder.add_edge("research", "itinerary")
    builder.add_edge("budget", "itinerary")

    # Sequential: itinerary -> booking -> validation
    builder.add_edge("itinerary", "booking")
    builder.add_edge("booking", "validation")

    # Conditional branching from validation
    builder.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "itinerary": "itinerary",
            "approval": "approval",
            "finalize": "finalize",
        },
    )

    # Post-approval flow
    builder.add_edge("approval", "finalize")
    builder.add_edge("finalize", END)

    # Checkpoint persistence and interrupt configuration
    saver = checkpointer or get_default_checkpointer()
    interrupt_nodes = ["approval"] if require_approval else []

    logger.info(
        "Compiling TripMate StateGraph (interrupt_before=%s, checkpointer=%s)",
        interrupt_nodes,
        saver.__class__.__name__,
    )

    return builder.compile(
        checkpointer=saver,
        interrupt_before=interrupt_nodes if interrupt_nodes else None,
    )


# Pre-compiled workflow instances for reuse
trip_graph_with_approval = build_trip_graph(require_approval=True)
trip_graph_direct = build_trip_graph(require_approval=False)

