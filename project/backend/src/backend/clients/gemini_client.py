from __future__ import annotations

from google import genai
from google.genai import types

_MODEL = "text-embedding-004"
# Gemini's embed_content endpoint accepts a batch, but a full document's
# worth of chunks in one request risks exceeding request size/rate limits
# and makes any single failure lose all prior work in that call. Batching
# keeps each request small and lets earlier batches succeed independently.
_BATCH_SIZE = 20
# The SDK's own default is short relative to a real embedding call under
# normal internet latency; matches the generous client-side timeout the
# frontend now uses for the same reason.
_TIMEOUT_MS = 120_000


class GeminiEmbeddingClient:
    """Thin wrapper around the Gemini embeddings API. Not unit-tested against the
    live API (requires a real key) — verify manually once GOOGLE_API_KEY is set.
    """

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=_TIMEOUT_MS)
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            response = self._client.models.embed_content(model=_MODEL, contents=batch)
            vectors.extend(embedding.values for embedding in response.embeddings)
        return vectors
