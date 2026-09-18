from unittest.mock import MagicMock, patch

from backend.api import dependencies
from backend.config import Settings


def _settings(**overrides) -> Settings:
    defaults = {
        "groq_api_key": "k",
        "google_api_key": "k",
        "chroma_persist_dir": "/tmp/chroma",
        "chroma_host": "",
        "chroma_port": 8000,
    }
    return Settings.model_construct(**{**defaults, **overrides})


def test_get_vector_store_uses_embedded_client_when_no_chroma_host():
    dependencies.get_settings.cache_clear()
    dependencies.get_vector_store.cache_clear()
    try:
        with (
            patch.object(dependencies, "get_settings", return_value=_settings()),
            patch.object(dependencies, "ChromaVectorStore") as embedded_cls,
            patch.object(dependencies, "ChromaHttpVectorStore") as http_cls,
        ):
            dependencies.get_vector_store()

        embedded_cls.assert_called_once_with(persist_dir="/tmp/chroma")
        http_cls.assert_not_called()
    finally:
        dependencies.get_vector_store.cache_clear()


def test_get_vector_store_uses_http_client_when_chroma_host_set():
    dependencies.get_settings.cache_clear()
    dependencies.get_vector_store.cache_clear()
    try:
        settings = _settings(chroma_host="chroma", chroma_port=9000)
        with (
            patch.object(dependencies, "get_settings", return_value=settings),
            patch.object(dependencies, "ChromaVectorStore") as embedded_cls,
            patch.object(dependencies, "ChromaHttpVectorStore") as http_cls,
        ):
            dependencies.get_vector_store()

        http_cls.assert_called_once_with(host="chroma", port=9000)
        embedded_cls.assert_not_called()
    finally:
        dependencies.get_vector_store.cache_clear()


def test_get_vector_store_result_is_cached():
    dependencies.get_settings.cache_clear()
    dependencies.get_vector_store.cache_clear()
    try:
        with (
            patch.object(dependencies, "get_settings", return_value=_settings()),
            patch.object(dependencies, "ChromaVectorStore", return_value=MagicMock()) as embedded_cls,
        ):
            first = dependencies.get_vector_store()
            second = dependencies.get_vector_store()

        assert first is second
        embedded_cls.assert_called_once()
    finally:
        dependencies.get_vector_store.cache_clear()
