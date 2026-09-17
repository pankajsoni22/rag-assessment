from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    backend_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        # The .env is shared across all tiers by design (see .env.example) - e.g.
        # GROQ_API_KEY/GOOGLE_API_KEY/CHROMA_PERSIST_DIR are backend-only.
        # Frontend's Settings must tolerate keys it doesn't recognize.
        extra="ignore",
    )
