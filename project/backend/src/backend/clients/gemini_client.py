from __future__ import annotations

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from backend.clients.errors import RateLimitedError

# "text-embedding-004" (architecture.md's original placeholder) 404s against
# the live API - deprecated. Confirmed via client.models.list() (filtered to
# models supporting embedContent) that gemini-embedding-001 is the current
# stable embeddings model.
_MODEL = "gemini-embedding-001"
# Gemini's embed_content endpoint accepts a batch, but a full document's
# worth of chunks in one request risks exceeding request size/rate limits
# and makes any single failure lose all prior work in that call. Batching
# keeps each request bounded and lets earlier batches succeed independently.
# 100 is confirmed working against the live API (verified directly, not
# just assumed) and is the documented max for this endpoint - fewer,
# larger batches mean fewer round-trips, which matters more than per-call
# delay for a large document: free-tier limits are typically requests-per-
# minute, so the real lever for "will a 10MB+ document get through" is
# how many separate calls it needs, not how long any single call waits.
_BATCH_SIZE = 100
# The SDK's own default is short relative to a real embedding call under
# normal internet latency; matches the generous client-side timeout the
# frontend now uses for the same reason.
_TIMEOUT_MS = 120_000
# The SDK's exponential-backoff-with-jitter retry machinery only activates
# when retry_options is explicitly set - left as None (the default), it
# resolves to zero retries (stop_after_attempt(1)), which is exactly why a
# transient 429/503 was previously failing immediately instead of backing
# off and retrying. attempts=6/max_delay=45 gives each batch up to ~90s of
# total backoff (1+2+4+8+16+32+45s-ish with jitter) - enough to ride out a
# full per-minute rate-limit window, which a short retry budget cannot.
# Still bounded well inside the frontend's now-300s request timeout.
_RETRY_OPTIONS = types.HttpRetryOptions(attempts=6, initial_delay=1.0, max_delay=45.0)


class GeminiEmbeddingClient:
    """Thin wrapper around the Gemini embeddings API. Not unit-tested against the
    live API (requires a real key) — verify manually once GOOGLE_API_KEY is set.
    """

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=_TIMEOUT_MS, retry_options=_RETRY_OPTIONS),
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            try:
                response = self._client.models.embed_content(model=_MODEL, contents=batch)
            except genai_errors.APIError as exc:
                # 429 RESOURCE_EXHAUSTED = quota/rate limit. 503 UNAVAILABLE
                # (a separate ServerError subclass, not ClientError) = Gemini
                # temporarily overloaded - very common on the free tier under
                # load. Both are "wait and retry", not "your file is broken".
                if exc.code in (429, 503):
                    raise RateLimitedError(
                        "Gemini embedding rate limit or quota exceeded."
                    ) from exc
                raise
            vectors.extend(embedding.values for embedding in response.embeddings)
        return vectors
