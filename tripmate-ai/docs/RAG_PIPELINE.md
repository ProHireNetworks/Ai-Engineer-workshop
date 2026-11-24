# TripMate AI RAG Pipeline

## Architectural Stages
1. **Document Ingestion (`rag/ingestion.py`)**: Loads structured markdown, PDF, or text destination guides.
2. **Text Chunking**: Recursively splits documents with appropriate chunk sizes and overlap to preserve semantic context.
3. **Embeddings (`rag/embeddings.py`)**: Generates vector representations using OpenAI Embeddings or local sentence transformers.
4. **Vector Storage (`rag/vector_store.py`)**: Stores vectors in PostgreSQL pgvector (production) or in-memory fallback (local development/testing).
5. **Retrieval & Context Building (`rag/retrieval.py`)**: Executes similarity search with metadata filtering (e.g. by destination and category) and formats prompt context with verified citations.

