"""
TripMate AI - Main API Router
Mounts all versioned routers under the designated API prefix.
"""

from fastapi import APIRouter
from app.api.v1 import approvals, health, knowledge, llm, tools, trips

api_router = APIRouter()

# Mount API v1 routers
api_router.include_router(health.router)
api_router.include_router(llm.router)
api_router.include_router(tools.router)
api_router.include_router(trips.router)
api_router.include_router(approvals.router)
api_router.include_router(knowledge.router)

