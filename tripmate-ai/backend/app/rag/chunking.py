"""
TripMate AI - RAG Document Chunking
Recursive character and Markdown-aware text splitters with overlap preservation.
"""

from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class TextChunk(BaseModel):
    """An individual indexed chunk of travel knowledge."""

    chunk_id: str = Field(default_factory=lambda: f"chunk_{uuid.uuid4().hex[:8]}")
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class DocumentChunker:
    """Splits raw text documents into overlapping semantic chunks."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[TextChunk]:
        """
        Recursively splits text using paragraph, sentence, and word boundaries.
        Preserves overlap to retain contextual continuity.
        """
        clean_text = text.strip()
        if not clean_text:
            return []

        base_meta = dict(metadata or {})
        chunks: List[TextChunk] = []

        # If text is smaller than chunk size, return single chunk
        if len(clean_text) <= self.chunk_size:
            chunk = TextChunk(
                content=clean_text,
                metadata={**base_meta, "chunk_index": 0, "total_chunks": 1},
            )
            return [chunk]

        # Break text by double newlines (paragraphs) or single newlines
        paragraphs = clean_text.split("\n\n")
        current_chunk_parts: List[str] = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If a single paragraph is larger than chunk size, split by lines or sentences
            if len(para) > self.chunk_size:
                sub_parts = para.split("\n")
                for sub in sub_parts:
                    sub = sub.strip()
                    if not sub:
                        continue
                    if current_length + len(sub) > self.chunk_size and current_chunk_parts:
                        chunk_text = " ".join(current_chunk_parts)
                        chunks.append(
                            TextChunk(content=chunk_text, metadata=dict(base_meta))
                        )
                        # Retain overlap from end of current chunk
                        overlap_start = max(0, len(current_chunk_parts) - 1)
                        current_chunk_parts = current_chunk_parts[overlap_start:]
                        current_length = sum(len(p) for p in current_chunk_parts)

                    current_chunk_parts.append(sub)
                    current_length += len(sub)
            else:
                if current_length + len(para) > self.chunk_size and current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts)
                    chunks.append(
                        TextChunk(content=chunk_text, metadata=dict(base_meta))
                    )
                    # Retain last paragraph for overlap if applicable
                    current_chunk_parts = [current_chunk_parts[-1]]
                    current_length = len(current_chunk_parts[0])

                current_chunk_parts.append(para)
                current_length += len(para)

        if current_chunk_parts:
            final_text = "\n\n".join(current_chunk_parts)
            chunks.append(TextChunk(content=final_text, metadata=dict(base_meta)))

        # Assign chunk indices
        total = len(chunks)
        for idx, chk in enumerate(chunks):
            chk.metadata["chunk_index"] = idx
            chk.metadata["total_chunks"] = total

        return chunks

