"""
TripMate AI - Travel Knowledge RAG Endpoints
Endpoints for ingesting travel documents, indexing guides, and semantic similarity search.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.rag.ingestion import get_ingestion_service
from app.rag.retrieval import get_retriever
from app.rag.vector_store import get_vector_store
from app.utils.logger import get_logger

router = APIRouter(prefix="/knowledge", tags=["Travel Knowledge & RAG"])
logger = get_logger(__name__)


class IngestTextRequest(BaseModel):
    """Payload to ingest raw text or Markdown into the vector store."""

    content: str = Field(..., min_length=10, description="Text or Markdown content to index")
    destination: Optional[str] = Field(default=None, description="Associated destination city or country")
    source_file: str = Field(default="api_input.md", description="Document label or source name")
    category: Optional[str] = Field(default="General", description="Category classification")


class IngestResponse(BaseModel):
    """Response returned upon successful document ingestion."""

    status: str = "success"
    chunks_indexed: int
    total_vectors_in_store: int
    message: str


class SearchKnowledgeRequest(BaseModel):
    """Query payload for RAG semantic search."""

    query: str = Field(..., min_length=2, description="Natural language search query")
    destination: Optional[str] = Field(default=None, description="Optional destination filter")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results to retrieve")
    min_score: float = Field(default=0.0, ge=-1.0, le=1.0, description="Minimum similarity threshold")


class SearchKnowledgeResponse(BaseModel):
    """Search results response with source attribution."""

    query: str
    destination: Optional[str] = None
    results_count: int
    sources: List[Dict[str, Any]]
    formatted_context: str


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Text / Markdown Document",
    description="Chunks, generates embeddings, and indexes content into the vector store.",
)
async def ingest_document(req: IngestTextRequest) -> IngestResponse:
    """Ingests text content into the RAG knowledge base."""
    service = get_ingestion_service()
    store = get_vector_store()
    meta = {
        "source_file": req.source_file,
        "destination": req.destination,
        "category": req.category,
    }
    indexed = await service.ingest_text(req.content, metadata=meta)
    return IngestResponse(
        chunks_indexed=indexed,
        total_vectors_in_store=store.count(),
        message=f"Successfully indexed {indexed} chunks into the vector store.",
    )


@router.post(
    "/load-defaults",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Load Default Knowledge Base",
    description="Scans the knowledge_base/travel_documents directory and indexes all markdown guides.",
)
async def load_default_knowledge() -> IngestResponse:
    """Loads and indexes the pre-packaged markdown travel guides."""
    service = get_ingestion_service()
    store = get_vector_store()

    # Locate knowledge_base/travel_documents
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "knowledge_base" / "travel_documents"
    if not base_dir.exists():
        # Fallback relative
        base_dir = Path("knowledge_base/travel_documents")

    indexed = await service.ingest_directory(str(base_dir))
    return IngestResponse(
        chunks_indexed=indexed,
        total_vectors_in_store=store.count(),
        message=f"Indexed {indexed} chunks from {base_dir}",
    )


@router.post(
    "/search",
    response_model=SearchKnowledgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Vector Search",
    description="Searches knowledge base chunks using cosine similarity and returns attributed excerpts.",
)
async def search_knowledge(req: SearchKnowledgeRequest) -> SearchKnowledgeResponse:
    """Performs semantic vector search across indexed travel documents."""
    retriever = get_retriever()
    results = await retriever.retrieve(
        query=req.query,
        destination=req.destination,
        top_k=req.top_k,
        min_score=req.min_score,
    )
    formatted = retriever.format_context_for_prompt(results)
    sources = [
        {
            "source": r.source,
            "relevance_score": r.score,
            "destination": r.destination,
            "snippet": r.chunk.content[:200] + "...",
            "metadata": r.chunk.metadata,
        }
        for r in results
    ]

    return SearchKnowledgeResponse(
        query=req.query,
        destination=req.destination,
        results_count=len(results),
        sources=sources,
        formatted_context=formatted,
    )

