from unittest.mock import MagicMock

import groq
import httpx
import pytest

from backend.clients.errors import RateLimitedError
from backend.clients.groq_client import GroqClient


def test_complete_returns_message_content():
    client = GroqClient(api_key="fake")
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content="hello there"))]
    client._client.chat.completions.create = MagicMock(return_value=response)

    assert client.complete([{"role": "user", "content": "hi"}]) == "hello there"


def test_complete_raises_rate_limited_error_on_groq_rate_limit():
    client = GroqClient(api_key="fake")
    request = httpx.Request("POST", "http://test")
    response = httpx.Response(429, request=request)
    error = groq.RateLimitError("rate limited", response=response, body=None)
    client._client.chat.completions.create = MagicMock(side_effect=error)

    with pytest.raises(RateLimitedError):
        client.complete([{"role": "user", "content": "hi"}])
