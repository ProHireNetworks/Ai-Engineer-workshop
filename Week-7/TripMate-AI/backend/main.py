import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

app = FastAPI(
    title="TripMate AI",
    description="Multi-Agent AI Travel Planning Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        *[
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
            if origin.strip()
        ],
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {
        "message": "Welcome to TripMate AI!",
        "status": "Running",
        "project": "Multi-Agent Travel Planning Assistant"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "TripMate AI"
    }
