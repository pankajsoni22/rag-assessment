"""Supplementary end-to-end sanity check — not a replacement for the
Playwright suite (test_ingestion_flow.py / test_qa_flow.py / test_not_found_flow.py),
which drives the real browser UI. This script starts the same real
backend + real frontend (only Gemini/Groq faked) and drives the full
user journey through real HTTP calls instead, so the whole system can
still be verified end-to-end in environments where a browser can't be
launched (see "Status" in specs/011-phase-9-integration-and-hardening.md).

Run with: uv run --package rag-e2e python3 tests/e2e/manual_final_run.py
"""

from __future__ import annotations

import io
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "project" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "project" / "storage" / "src"))

from backend.api.dependencies import (  # noqa: E402
    get_document_set_service,
    get_ingestion_service,
    get_rag_orchestrator,
)
from backend.loaders.registry import default_registry  # noqa: E402
from backend.main import app  # noqa: E402
from backend.services.chunking_service import ChunkingService  # noqa: E402
from backend.services.conversation_service import ConversationService  # noqa: E402
from backend.services.document_set_service import DocumentSetService  # noqa: E402
from backend.services.embedding_service import EmbeddingService  # noqa: E402
from backend.services.generation_service import GenerationService  # noqa: E402
from backend.services.ingestion_service import IngestionService  # noqa: E402
from backend.services.rag_orchestrator import RAGOrchestrator  # noqa: E402
from backend.services.retrieval_service import RetrievalService  # noqa: E402
from storage.chroma_vector_store import ChromaVectorStore  # noqa: E402

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, condition, detail))
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not condition else ""))


class FakeEmbeddingClient:
    def embed_texts(self, texts):
        return [[1.0, 0.0] for _ in texts]


class FakeGenerationClient:
    def complete(self, messages):
        return "This is a fake grounded answer for the final run."


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_up(url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            httpx.get(url, timeout=1.0)
            return
        except httpx.TransportError:
            time.sleep(0.2)
    raise RuntimeError(f"{url} did not come up in time")


def main() -> int:
    chroma_dir = REPO_ROOT / "tests" / "e2e" / ".final_run_chroma"
    if chroma_dir.exists():
        import shutil

        shutil.rmtree(chroma_dir)

    vector_store = ChromaVectorStore(persist_dir=chroma_dir)
    doc_set_service = DocumentSetService(vector_store=vector_store)
    embedder = EmbeddingService(FakeEmbeddingClient())
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
        generation_service=GenerationService(FakeGenerationClient()),
    )
    app.dependency_overrides[get_document_set_service] = lambda: doc_set_service
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    app.dependency_overrides[get_rag_orchestrator] = lambda: orchestrator

    backend_port = free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=backend_port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    backend_url = f"http://127.0.0.1:{backend_port}"
    wait_up(f"{backend_url}/health")
    print(f"Backend up at {backend_url}")

    frontend_port = free_port()
    frontend_app = REPO_ROOT / "project" / "frontend" / "src" / "frontend" / "app.py"
    env = os.environ.copy()
    env["BACKEND_URL"] = backend_url
    frontend_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(frontend_app),
            "--server.headless",
            "true",
            "--server.port",
            str(frontend_port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(REPO_ROOT),
    )
    frontend_url = f"http://127.0.0.1:{frontend_port}"
    wait_up(frontend_url)
    print(f"Frontend up at {frontend_url}")

    client = httpx.Client(base_url=backend_url)

    try:
        # --- Frontend pages render ---
        check("frontend root page returns 200", client.get(frontend_url).status_code == 200)
        # (avoid an extra request object; use plain httpx for the frontend, different base_url)
        r = httpx.get(f"{frontend_url}/chat")
        check("frontend /chat page returns 200", r.status_code == 200)

        # --- A2: create a set ---
        r = client.post("/sets", json={"name": "Final Run Set"})
        check("create set -> 201", r.status_code == 201, r.text)
        set_id = r.json()["id"]

        r = client.get("/sets")
        check(
            "list sets includes the new set",
            any(s["id"] == set_id for s in r.json()),
        )

        # --- A1: upload a document (PDF path via the real loader, not just text) ---
        r = client.post(
            "/documents",
            params={"set_id": set_id},
            files={
                "file": (
                    "answer.txt",
                    io.BytesIO(b"The secret number is 42."),
                    "text/plain",
                )
            },
        )
        check("upload document -> 201", r.status_code == 201, r.text)
        document = r.json()
        check("document status is ready", document["status"] == "ready", document["status"])

        r = client.get("/documents", params={"set_id": set_id})
        check("document appears in list", any(d["id"] == document["id"] for d in r.json()))

        # --- A1.4: empty file is rejected clearly, not silently accepted ---
        r = client.post(
            "/documents",
            params={"set_id": set_id},
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        check(
            "empty file upload -> 422 with plain-language detail",
            r.status_code == 422 and "empty.txt" in r.json().get("detail", ""),
            r.text,
        )

        # --- A4: ask a grounded question, scoped to the set ---
        r = client.post(
            "/query",
            json={"question": "What is the secret number?", "set_id": set_id, "session_id": "final-run-1"},
        )
        check("query -> 200", r.status_code == 200, r.text)
        answer = r.json()
        check("answer is grounded", answer["grounded"] is True, str(answer))
        check("answer has a citation", len(answer["citations"]) >= 1, str(answer))
        check(
            "citation references the uploaded file",
            any(c["filename"] == "answer.txt" for c in answer["citations"]),
            str(answer),
        )

        # --- A4.19: follow-up question uses conversation history (same session_id) ---
        r = client.post(
            "/query",
            json={"question": "And what about for contractors?", "set_id": set_id, "session_id": "final-run-1"},
        )
        check("follow-up query -> 200", r.status_code == 200, r.text)

        # --- A4.18/B7: not-found case, scoped to a fresh empty set ---
        r = client.post("/sets", json={"name": "Empty Set"})
        empty_set_id = r.json()["id"]
        r = client.post(
            "/query",
            json={"question": "Anything at all?", "set_id": empty_set_id, "session_id": "final-run-2"},
        )
        check("not-found query -> 200", r.status_code == 200, r.text)
        not_found_answer = r.json()
        check(
            "not-found answer is explicitly not grounded",
            not_found_answer["grounded"] is False,
            str(not_found_answer),
        )

        # --- A2.10/A1.6: remove document, delete set ---
        r = client.delete(f"/documents/{document['id']}")
        check("remove document -> 204", r.status_code == 204)
        r = client.get("/documents", params={"set_id": set_id})
        remaining_ids = [d["id"] for d in r.json()]
        check(
            "removed document no longer in list",
            document["id"] not in remaining_ids,
            f"remaining docs: {r.json()}",
        )

        r = client.delete(f"/sets/{set_id}")
        check("delete set -> 204", r.status_code == 204)
        r = client.get("/sets")
        check("deleted set gone from list", all(s["id"] != set_id for s in r.json()))

        # --- B4/B6: unsupported format and corrupt file handled without leaking internals ---
        r = client.post(
            "/documents",
            params={"set_id": empty_set_id},
            files={"file": ("virus.exe", io.BytesIO(b"x"), "application/octet-stream")},
        )
        check("unsupported extension -> 400", r.status_code == 400)

        r = client.post(
            "/documents",
            params={"set_id": empty_set_id},
            files={"file": ("bad.pdf", io.BytesIO(b"not a real pdf"), "application/pdf")},
        )
        check(
            "corrupt pdf -> 422, no internal leak",
            r.status_code == 422 and "PdfStreamError" not in r.text,
            r.text,
        )

    finally:
        server.should_exit = True
        thread.join(timeout=5)
        frontend_process.terminate()
        frontend_process.wait(timeout=5)
        import shutil

        shutil.rmtree(chroma_dir, ignore_errors=True)

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    total = len(CHECKS)
    print(f"{passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
