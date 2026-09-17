class RateLimitedError(Exception):
    """Raised when an external LLM API (Gemini or Groq) reports rate-limit or
    quota exhaustion. Kept provider-agnostic so callers (routes) only need to
    handle one exception type regardless of which upstream service hit it.
    """
