from __future__ import annotations

from groq import Groq

_MODEL = "llama-3.3-70b-versatile"
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
        response = self._client.chat.completions.create(
            model=_MODEL, messages=messages, temperature=_TEMPERATURE
        )
        return response.choices[0].message.content
