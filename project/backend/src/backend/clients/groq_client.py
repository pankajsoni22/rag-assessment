from __future__ import annotations

import groq
from groq import Groq

from backend.clients.errors import RateLimitedError

# "llama-3.3-70b-versatile" (specs/007's original placeholder) 404s - not
# available on this account/catalog anymore. Confirmed via client.models.list()
# that openai/gpt-oss-120b is currently available and works.
_MODEL = "openai/gpt-oss-120b"
# Pinned low (not the API default) so the same question against the same
# documents gives a consistent, dependable answer — spec B1.2.
_TEMPERATURE = 0


class GroqClient:
    """Thin wrapper around the Groq chat completions API. Not unit-tested against
    the live API (requires a real key) — verify manually once GROQ_API_KEY is set.
    """

    def __init__(self, api_key: str) -> None:
        self._client = Groq(api_key=api_key)

    def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=_MODEL, messages=messages, temperature=_TEMPERATURE
            )
        except groq.APIStatusError as exc:
            # 429 (RateLimitError) = rate limit/quota. 503 (InternalServerError,
            # a separate subclass) = Groq temporarily overloaded - both are
            # "wait and retry", not a real failure worth a generic message.
            if exc.status_code in (429, 503):
                raise RateLimitedError("Groq generation rate limit or quota exceeded.") from exc
            raise
        return response.choices[0].message.content
