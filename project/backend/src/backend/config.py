from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    groq_api_key: str
    google_api_key: str
    chroma_persist_dir: str
    # Empty (the default) means embedded mode: Chroma runs as a local
    # library inside this process, persisting to chroma_persist_dir. Set
    # only when Chroma runs as its own server (e.g. via docker/), in which
    # case the backend connects over HTTP instead - see api/dependencies.py.
    chroma_host: str = ""
    chroma_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        # The .env is shared across all tiers by design (see .env.example) - e.g.
        # BACKEND_URL is frontend-only. Backend's Settings must tolerate keys it
        # doesn't recognize rather than fail validation because of them.
        extra="ignore",
    )
