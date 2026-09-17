from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn

from backend.api.dependencies import (
    get_document_set_service,
    get_ingestion_service,
    get_rag_orchestrator,
)
from backend.loaders.registry import default_registry
from backend.main import app
from backend.services.chunking_service import ChunkingService
from backend.services.conversation_service import ConversationService
from backend.services.document_set_service import DocumentSetService
from backend.services.embedding_service import EmbeddingService
from backend.services.generation_service import GenerationService
from backend.services.ingestion_service import IngestionService
from backend.services.rag_orchestrator import RAGOrchestrator
from backend.services.retrieval_service import RetrievalService
from storage.chroma_vector_store import ChromaVectorStore

_REPO_ROOT = Path(__file__).resolve().parents[2]


class _FakeEmbeddingClient:
    """Deterministic stand-in for Gemini. E2E tests exercise the real FastAPI
    app, real routing, real ChromaVectorStore, real loaders/chunking -
    everything except the two paid LLM calls (see specs/011, "what stays
    manual"). Real Gemini/Groq integration needs a manual check with a real
    API key, not this automated suite.
    """

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class _FakeGenerationClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "This is a fake grounded answer from the E2E test double."


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_up(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            httpx.get(url, timeout=1.0)
            return
        except httpx.TransportError as exc:
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"Server at {url} did not start in time") from last_error


@pytest.fixture(scope="session")
def backend_url(tmp_path_factory):
    chroma_dir = tmp_path_factory.mktemp("e2e_chroma")
    vector_store = ChromaVectorStore(persist_dir=chroma_dir)
    doc_set_service = DocumentSetService(vector_store=vector_store)
    embedder = EmbeddingService(_FakeEmbeddingClient())
    ingestion_service = IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=embedder,
        vector_store=vector_store,
        doc_set_service=doc_set_service,
    )
    orchestrator = RAGOrchestrator(
        conversation_service=ConversationService(),
        retrieval_service=RetrievalService(embedder=embedder, vector_store=vector_store),
        generation_service=GenerationService(_FakeGenerationClient()),
    )

    app.dependency_overrides[get_document_set_service] = lambda: doc_set_service
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    app.dependency_overrides[get_rag_orchestrator] = lambda: orchestrator

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    _wait_until_up(f"{url}/health")

    yield url

    server.should_exit = True
    thread.join(timeout=5)
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def frontend_url(backend_url: str):
    port = _free_port()
    frontend_app = (
        _REPO_ROOT / "project" / "frontend" / "src" / "frontend" / "app.py"
    )

    env = os.environ.copy()
    env["BACKEND_URL"] = backend_url

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(frontend_app),
            "--server.headless",
            "true",
            "--server.port",
            str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_up(url)
    except RuntimeError:
        process.terminate()
        output = process.stdout.read() if process.stdout else ""
        raise RuntimeError(f"Frontend failed to start:\n{output}") from None

    yield url

    process.terminate()
    process.wait(timeout=5)
