from __future__ import annotations

from groq import Groq

_MODEL = "llama-3.3-70b-versatile"


class GroqClient:
    """Thin wrapper around the Groq chat completions API. Not unit-tested against
    the live API (requires a real key) — verify manually once GROQ_API_KEY is set.
    """

    def __init__(self, api_key: str) -> None:
        self._client = Groq(api_key=api_key)

    def complete(self, messages: list[dict[str, str]]) -> str:
        response = self._client.chat.completions.create(model=_MODEL, messages=messages)
        return response.choices[0].message.content
