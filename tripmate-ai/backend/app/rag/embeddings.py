"""
TripMate AI - RAG Embeddings Layer
Abstract embedding interface with OpenAI and Deterministic Mock providers.
"""

from abc import ABC, abstractmethod
import hashlib
import math
from typing import List, Optional

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract base class for vector embedding generation."""

    dimension: int

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generates embedding vector for a single query string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of document strings."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic pseudo-semantic embedding generator for offline testing and CI.
    Generates normalized 128-dimensional vectors based on word frequencies and SHA-256 hash seeds.
    """

    dimension: int = 128

    def _generate_vector(self, text: str) -> List[float]:
        clean_text = text.strip().lower()
        if not clean_text:
            return [0.0] * self.dimension

        # Generate deterministic floats from tokens and sha256
        vec = [0.0] * self.dimension
        words = clean_text.split()
        for idx, word in enumerate(words):
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            slot = (h + idx) % self.dimension
            vec[slot] += 1.0 + (h % 100) / 100.0

        # L2 normalize
        magnitude = math.sqrt(sum(x * x for x in vec))
        if magnitude > 0:
            vec = [round(x / magnitude, 6) for x in vec]
        return vec

    async def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Official OpenAI embedding provider supporting text-embedding-3-small."""

    dimension: int = 1536

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small") -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.client = None
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key, timeout=settings.LLM_TIMEOUT)
            except ImportError:
                logger.warning("openai package not available for OpenAIEmbeddingProvider")

    async def embed_query(self, text: str) -> List[float]:
        if not self.client:
            raise RuntimeError("OpenAI client not configured or API key missing.")
        res = await self.client.embeddings.create(input=[text], model=self.model)
        return res.data[0].embedding

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            raise RuntimeError("OpenAI client not configured or API key missing.")
        res = await self.client.embeddings.create(input=texts, model=self.model)
        return [d.embedding for d in res.data]


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory selecting the embedding provider based on application configuration."""
    if settings.LLM_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
        try:
            return OpenAIEmbeddingProvider()
        except Exception as exc:
            logger.warning("Falling back to MockEmbeddingProvider: %s", exc)
            return MockEmbeddingProvider()
    return MockEmbeddingProvider()

