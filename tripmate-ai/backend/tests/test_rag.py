"""
TripMate AI - Travel RAG Pipeline Tests
Tests chunking, mock embeddings, cosine similarity vector search, document ingestion, and API endpoints.
"""

from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rag.chunking import DocumentChunker
from app.rag.embeddings import MockEmbeddingProvider
from app.rag.ingestion import DocumentIngestionService
from app.rag.retrieval import RAGRetriever
from app.rag.vector_store import InMemoryVectorStore
from app.schemas.tool import ToolCall
from app.tools.executor import ToolExecutor
from app.tools.rag_search import RetrieveTravelKnowledgeTool


def test_document_chunker_boundaries_and_overlap():
    """Verify chunker creates overlapping segments preserving paragraph structure."""
    chunker = DocumentChunker(chunk_size=150, chunk_overlap=30)
    sample_text = (
        "Jaipur is the historic capital of Rajasthan, celebrated for royal palaces and majestic forts.\n\n"
        "Amber Fort sits high upon a rugged hill, constructed from pale yellow and pink sandstone with white marble.\n\n"
        "Inside Amber Fort lies the Sheesh Mahal, where thousands of tiny mirrors reflect light across the hall."
    )
    chunks = chunker.split_text(sample_text, metadata={"source": "test_guide.md"})

    assert len(chunks) >= 2
    for c in chunks:
        assert len(c.content) > 0
        assert c.metadata["source"] == "test_guide.md"
        assert "chunk_index" in c.metadata
        assert "total_chunks" in c.metadata


@pytest.mark.asyncio
async def test_mock_embedding_provider_properties():
    """Verify mock embeddings generate deterministic, L2-normalized 128-dimensional vectors."""
    provider = MockEmbeddingProvider()
    vec1 = await provider.embed_query("Amber Palace Jaipur")
    vec2 = await provider.embed_query("Amber Palace Jaipur")
    vec3 = await provider.embed_query("Calangute Beach Goa")

    assert len(vec1) == 128
    assert vec1 == vec2  # Determinism
    assert vec1 != vec3  # Discrimination

    # Check approximate unit length
    magnitude = sum(x * x for x in vec1) ** 0.5
    assert abs(magnitude - 1.0) < 0.01


@pytest.mark.asyncio
async def test_vector_store_similarity_and_metadata_filtering():
    """Verify in-memory vector store cosine search and metadata filtering."""
    store = InMemoryVectorStore()
    provider = MockEmbeddingProvider()

    chunker = DocumentChunker(chunk_size=200)
    c1 = chunker.split_text("Amber Fort Jaipur Rajasthan", metadata={"destination": "Jaipur"})[0]
    c2 = chunker.split_text("Baga Beach Goa nightlife and shacks", metadata={"destination": "Goa"})[0]

    c1.embedding = await provider.embed_query(c1.content)
    c2.embedding = await provider.embed_query(c2.content)

    await store.add_chunks([c1, c2])
    assert store.count() == 2

    # Query matching Jaipur
    query_vec = await provider.embed_query("Jaipur fort palaces")
    results = await store.similarity_search(query_vec, top_k=2)
    assert len(results) >= 1
    assert results[0].chunk.metadata["destination"] == "Jaipur"

    # Query with metadata filter
    goa_filtered = await store.similarity_search(
        query_vec, top_k=2, filter_metadata={"destination": "Goa"}
    )
    assert len(goa_filtered) == 1
    assert goa_filtered[0].chunk.metadata["destination"] == "Goa"


@pytest.mark.asyncio
async def test_document_ingestion_and_retrieval_pipeline():
    """Test full pipeline: ingestion of guide files into store and contextual retrieval."""
    store = InMemoryVectorStore()
    provider = MockEmbeddingProvider()
    ingestion_service = DocumentIngestionService(vector_store=store, embedding_provider=provider)
    retriever = RAGRetriever(vector_store=store, embedding_provider=provider)

    # Ingest text guide
    guide_text = (
        "# Kerala Backwaters Guide\n\n"
        "Alleppey is famous for traditional kettuvallam houseboats cruising peaceful lagoons.\n\n"
        "Munnar offers breathtaking tea estates and the endangered Nilgiri Tahr."
    )
    indexed = await ingestion_service.ingest_text(
        guide_text,
        metadata={"source_file": "kerala_test.md", "destination": "Kerala"},
    )
    assert indexed >= 1

    # Retrieve context
    results = await retriever.retrieve("houseboats in backwaters", destination="Kerala")
    assert len(results) >= 1
    assert results[0].source == "kerala_test.md"

    # Context formatting with attribution
    context_str = retriever.format_context_for_prompt(results)
    assert "Reference Document" in context_str
    assert "kerala_test.md" in context_str


@pytest.mark.asyncio
async def test_retrieve_travel_knowledge_tool():
    """Verify registered tool retrieve_travel_knowledge executes properly via ToolExecutor."""
    executor = ToolExecutor()
    tool = RetrieveTravelKnowledgeTool()
    executor.registry.register(tool, override=True)

    call = ToolCall(
        id="rag_call_1",
        name="retrieve_travel_knowledge",
        arguments={"query": "best sights in Jaipur", "destination": "Jaipur", "top_k": 2},
    )
    result = await executor.execute_call(call)
    assert result.status == "success"
    assert "results_count" in result.result
    assert "sources" in result.result
    assert "formatted_context" in result.result


@pytest.mark.asyncio
async def test_rag_api_endpoints():
    """Test REST API endpoints for loading defaults, ingesting, and searching."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Ingest endpoint
        ingest_resp = await client.post(
            "/api/v1/knowledge/ingest",
            json={
                "content": "Manali is renowned for Solang Valley adventure sports and the Hadimba Temple.",
                "destination": "Manali",
                "source_file": "manali_brief.md",
                "category": "Adventure",
            },
        )
        assert ingest_resp.status_code == 201
        ingest_data = ingest_resp.json()
        assert ingest_data["status"] == "success"
        assert ingest_data["chunks_indexed"] >= 1

        # Search endpoint
        search_resp = await client.post(
            "/api/v1/knowledge/search",
            json={
                "query": "adventure sports in Solang",
                "destination": "Manali",
                "top_k": 2,
            },
        )
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert search_data["results_count"] >= 1
        assert len(search_data["sources"]) >= 1
        assert "Solang" in search_data["formatted_context"]
