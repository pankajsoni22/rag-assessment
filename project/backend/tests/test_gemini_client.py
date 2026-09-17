from unittest.mock import MagicMock

import pytest
from google.genai import errors as genai_errors

from backend.clients.errors import RateLimitedError
from backend.clients.gemini_client import GeminiEmbeddingClient


def _fake_embed_response(batch: list[str]):
    response = MagicMock()
    response.embeddings = [MagicMock(values=[float(len(text)), 0.0]) for text in batch]
    return response


def test_embed_texts_splits_into_batches_and_preserves_order():
    client = GeminiEmbeddingClient(api_key="fake")
    texts = [f"text-{i}" for i in range(45)]  # 3 batches at _BATCH_SIZE=20

    calls: list[list[str]] = []

    def fake_embed_content(model, contents):
        calls.append(list(contents))
        return _fake_embed_response(contents)

    client._client.models.embed_content = fake_embed_content

    vectors = client.embed_texts(texts)

    assert len(calls) == 3
    assert [len(batch) for batch in calls] == [20, 20, 5]
    assert calls[0] + calls[1] + calls[2] == texts
    assert len(vectors) == len(texts)
    assert vectors[0] == [float(len(texts[0])), 0.0]


def test_embed_texts_empty_list_makes_no_calls():
    client = GeminiEmbeddingClient(api_key="fake")
    client._client.models.embed_content = MagicMock(
        side_effect=AssertionError("should not be called")
    )

    assert client.embed_texts([]) == []


def test_embed_texts_raises_rate_limited_error_on_429():
    client = GeminiEmbeddingClient(api_key="fake")
    error = genai_errors.ClientError(
        429, {"error": {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}}
    )
    client._client.models.embed_content = MagicMock(side_effect=error)

    with pytest.raises(RateLimitedError):
        client.embed_texts(["hello"])


def test_embed_texts_reraises_non_rate_limit_api_errors():
    client = GeminiEmbeddingClient(api_key="fake")
    error = genai_errors.ClientError(
        404, {"error": {"message": "not found", "status": "NOT_FOUND"}}
    )
    client._client.models.embed_content = MagicMock(side_effect=error)

    with pytest.raises(genai_errors.ClientError):
        client.embed_texts(["hello"])
