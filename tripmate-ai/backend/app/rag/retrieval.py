"""
TripMate AI - RAG Retrieval Pipeline
Retrieval orchestration with query vectorization, metadata filtering, and formatted source attribution.
"""

from typing import Any, Dict, List, Optional
from app.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.rag.vector_store import BaseVectorStore, QueryResult, get_vector_store
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGRetriever:
    """Orchestrates query vectorization, similarity search, and context formatting with attribution."""

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ) -> None:
        self.vector_store = vector_store or get_vector_store()
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def retrieve(
        self,
        query: str,
        destination: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 4,
        min_score: float = 0.05,
    ) -> List[QueryResult]:
        """
        Embeds the query and queries vector store with optional destination/category filters.
        """
        query_vec = await self.embedding_provider.embed_query(query)
        filters: Dict[str, Any] = {}
        if destination:
            filters["destination"] = destination
        if category:
            filters["category"] = category

        results = await self.vector_store.similarity_search(
            query_vector=query_vec,
            top_k=top_k,
            filter_metadata=filters if filters else None,
            min_score=min_score,
        )

        logger.info(
            "RAG retrieved %d chunks for query='%s' (destination=%s)",
            len(results),
            query,
            destination,
        )
        return results

    def format_context_for_prompt(self, results: List[QueryResult]) -> str:
        """
        Synthesizes retrieved chunks into a prompt-ready context block with clear source attribution.
        """
        if not results:
            return "No relevant context found in local knowledge base."

        formatted_sections: List[str] = []
        for idx, res in enumerate(results, start=1):
            source = res.source
            score = res.score
            chunk_idx = res.chunk.metadata.get("chunk_index", 0)
            content = res.chunk.content.strip()

            section = (
                f"--- Reference Document #{idx} ---\n"
                f"Source: {source} (Chunk {chunk_idx}, Relevance: {score:.2f})\n"
                f"{content}\n"
            )
            formatted_sections.append(section)

        return "\n".join(formatted_sections)


# Global retriever instance
_global_retriever = RAGRetriever()


def get_retriever() -> RAGRetriever:
    return _global_retriever

