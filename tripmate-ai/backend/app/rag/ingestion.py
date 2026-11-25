"""
TripMate AI - RAG Document Ingestion Pipeline
Parses, splits, embeds, and stores documents from Markdown, TXT, and PDF files into the vector store.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.rag.chunking import DocumentChunker, TextChunk
from app.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from app.rag.vector_store import BaseVectorStore, get_vector_store
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentIngestionService:
    """Manages file extraction, chunking, vector generation, and vector store indexing."""

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
    ) -> None:
        self.vector_store = vector_store or get_vector_store()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    async def ingest_text(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Chunks, embeds, and indexes a raw string of text or markdown."""
        if not content.strip():
            return 0

        chunks: List[TextChunk] = self.chunker.split_text(content, metadata=metadata)
        if not chunks:
            return 0

        texts = [c.content for c in chunks]
        embeddings = await self.embedding_provider.embed_documents(texts)

        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

        return await self.vector_store.add_chunks(chunks)

    async def ingest_file(
        self,
        file_path: str,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Reads a file (.md, .txt, .pdf), extracts text, and indexes into vector store."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        meta = {
            "source_file": p.name,
            "file_ext": p.suffix.lower(),
            **(custom_metadata or {}),
        }

        # Infer destination if not explicitly provided
        stem_lower = p.stem.lower()
        if "destination" not in meta:
            for dest in ["jaipur", "goa", "kerala", "manali", "delhi", "mumbai", "agra"]:
                if dest in stem_lower:
                    meta["destination"] = dest.capitalize()
                    break

        content = ""
        suffix = p.suffix.lower()
        if suffix in [".md", ".txt"]:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        elif suffix == ".pdf":
            # Extract PDF using pypdf if installed, else fallback error
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(p))
                pages = [page.extract_text() or "" for page in reader.pages]
                content = "\n\n".join(pages)
            except ImportError:
                logger.warning("pypdf not installed, cannot ingest PDF: %s", file_path)
                return 0
        else:
            logger.warning("Unsupported file type '%s' for RAG ingestion: %s", suffix, file_path)
            return 0

        return await self.ingest_text(content, metadata=meta)

    async def ingest_directory(
        self,
        dir_path: str,
        extensions: Optional[List[str]] = None,
    ) -> int:
        """Recursively ingests all supported files within a directory."""
        target_exts = set(extensions or [".md", ".txt", ".pdf"])
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            logger.warning("Directory does not exist for RAG ingestion: %s", dir_path)
            return 0

        total_indexed = 0
        for root, _, files in os.walk(p):
            for filename in sorted(files):
                file_p = Path(root) / filename
                if file_p.suffix.lower() in target_exts:
                    try:
                        indexed = await self.ingest_file(str(file_p))
                        total_indexed += indexed
                    except Exception as exc:
                        logger.error("Failed ingesting %s: %s", file_p, exc)

        logger.info("Completed directory ingestion for '%s': %d total chunks stored", dir_path, total_indexed)
        return total_indexed


# Global ingestion service
_global_ingestion_service = DocumentIngestionService()


def get_ingestion_service() -> DocumentIngestionService:
    return _global_ingestion_service

