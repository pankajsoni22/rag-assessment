from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    groq_api_key: str
    google_api_key: str
    chroma_persist_dir: str

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        # The .env is shared across all tiers by design (see .env.example) - e.g.
        # BACKEND_URL is frontend-only. Backend's Settings must tolerate keys it
        # doesn't recognize rather than fail validation because of them.
        extra="ignore",
    )
