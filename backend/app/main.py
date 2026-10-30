
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.schemas.ingestion import IngestionRequest
from app.services.llm_service import (
    analyze_message,
    generate_contextual_response,
)
from app.services.database_service import (
    initialize_database,
    ensure_conversation,
    get_chat_history,
    add_chat_message,
    list_conversations,
    get_conversation_messages,
)
from app.utils.token_counter import estimate_tokens


app = FastAPI(
    title="Enterprise Ingestion Firewall",
    description="AI-powered message analysis and contextual assistance.",
    version="4.0.0",
)


@app.on_event("startup")
def startup_event():
    initialize_database()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Ingestion Firewall API is running",
        "database": "postgresql",
    }


@app.get("/api/conversations")
def get_conversations():
    try:
        return {"items": list_conversations()}
    except Exception as exc:
        print(f"Conversation list error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Could not load conversations.",
        ) from exc


@app.get("/api/conversations/{session_id}/messages")
def get_conversation(session_id: str):
    try:
        messages = get_conversation_messages(session_id)
        return {
            "session_id": session_id,
            "items": messages,
        }
    except Exception as exc:
        print(f"Conversation history error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Could not load conversation history.",
        ) from exc


@app.post("/api/analyze")
def analyze(request: IngestionRequest):
    message = request.message.strip()
    session_id = str(request.session_id or uuid4())

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    try:
        ensure_conversation(session_id, message[:70])

        result = analyze_message(message)

        history = get_chat_history(session_id)

        response_markdown = generate_contextual_response(
            message=message,
            intent=result.intent,
            summary=result.summary,
            chat_history=history,
        )

        add_chat_message(session_id, "user", message)
        add_chat_message(session_id, "assistant", response_markdown)

        result.token_metadata.estimated_input_tokens = estimate_tokens(
            message
        )

        return {
            **result.model_dump(),
            "session_id": session_id,
            "response_markdown": response_markdown,
        }

    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "The model response did not pass schema validation.",
                "validation_errors": exc.errors(),
            },
        ) from exc

    except Exception as exc:
        print(f"Analysis error: {exc}")
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI request failed. Check the database, API key, "
                "model name, and network."
            ),
        ) from exc
