"""
TripMate AI - RAG Knowledge Retrieval Tool
Tool interface allowing agents to query curated regional travel guides, attractions, and cultural advice.
"""

from typing import Any, Dict, List, Optional
from app.rag.retrieval import get_retriever
from app.tools.base import BaseTool
from app.tools.schemas import RAGSearchArgs


class RetrieveTravelKnowledgeTool(BaseTool):
    """Retrieves contextual travel knowledge from the vector store using semantic search."""

    name = "retrieve_travel_knowledge"
    description = (
        "Retrieve expert travel guide excerpts, cultural advice, regional etiquette, and insider tips "
        "from the curated knowledge base using semantic vector retrieval."
    )
    args_schema = RAGSearchArgs

    async def _run(
        self,
        query: str,
        destination: Optional[str] = None,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        retriever = get_retriever()
        results = await retriever.retrieve(query=query, destination=destination, top_k=top_k)

        formatted_context = retriever.format_context_for_prompt(results)
        sources = [
            {
                "source": r.source,
                "relevance_score": r.score,
                "destination": r.destination,
                "snippet": r.chunk.content[:200] + "...",
            }
            for r in results
        ]

        return {
            "query": query,
            "destination": destination,
            "results_count": len(results),
            "sources": sources,
            "formatted_context": formatted_context,
        }

