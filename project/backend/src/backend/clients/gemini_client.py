from __future__ import annotations

from google import genai

_MODEL = "text-embedding-004"


class GeminiEmbeddingClient:
    """Thin wrapper around the Gemini embeddings API. Not unit-tested against the
    live API (requires a real key) — verify manually once GOOGLE_API_KEY is set.
    """

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self._client.models.embed_content(model=_MODEL, contents=texts)
        return [embedding.values for embedding in response.embeddings]
