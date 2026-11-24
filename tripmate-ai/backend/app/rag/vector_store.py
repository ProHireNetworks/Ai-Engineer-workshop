"""
TripMate AI - RAG Vector Store
In-memory vector store with cosine similarity calculation, metadata filtering, and pgvector readiness.
"""

from abc import ABC, abstractmethod
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.rag.chunking import TextChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryResult(BaseModel):
    """Result of a vector similarity search with source attribution metadata."""

    chunk: TextChunk
    score: float = Field(..., ge=-1.0, le=1.0, description="Cosine similarity score")
    source: str = Field(default="knowledge_base", description="Attribution origin")
    destination: Optional[str] = None


class BaseVectorStore(ABC):
    """Abstract vector store contract for document indexing and nearest neighbor search."""

    @abstractmethod
    async def add_chunks(self, chunks: List[TextChunk]) -> int:
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[QueryResult]:
        pass

    @abstractmethod
    def count(self) -> int:
        pass


class InMemoryVectorStore(BaseVectorStore):
    """
    High-performance in-memory vector store using pure Python cosine distance math.
    Ideal for local development, fast testing, and single-instance deployments.
    """

    def __init__(self) -> None:
        self.chunks: List[TextChunk] = []

    def count(self) -> int:
        return len(self.chunks)

    def clear(self) -> None:
        self.chunks.clear()

    async def add_chunks(self, chunks: List[TextChunk]) -> int:
        added = 0
        for chunk in chunks:
            if chunk.embedding is not None:
                self.chunks.append(chunk)
                added += 1
        logger.info("Added %d vector chunks to InMemoryVectorStore (Total: %d)", added, len(self.chunks))
        return added

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return round(dot_product / (norm_a * norm_b), 4)

    async def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[QueryResult]:
        scored_results: List[QueryResult] = []

        for chunk in self.chunks:
            if not chunk.embedding:
                continue

            # Apply metadata filters if provided
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    val = chunk.metadata.get(k)
                    if val is None or str(val).lower() != str(v).lower():
                        match = False
                        break
                if not match:
                    continue

            score = self._cosine_similarity(query_vector, chunk.embedding)
            if score >= min_score:
                scored_results.append(
                    QueryResult(
                        chunk=chunk,
                        score=score,
                        source=chunk.metadata.get("source_file", "knowledge_base"),
                        destination=chunk.metadata.get("destination"),
                    )
                )

        # Sort descending by similarity score
        scored_results.sort(key=lambda r: r.score, reverse=True)
        return scored_results[:top_k]


# Process-level default vector store
_global_vector_store = InMemoryVectorStore()


def get_vector_store() -> InMemoryVectorStore:
    return _global_vector_store

