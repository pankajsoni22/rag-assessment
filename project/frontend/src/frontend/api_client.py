from __future__ import annotations

from datetime import datetime

import httpx
import streamlit as st

from frontend.config import Settings
from frontend.models import AnswerView, CitationView, DocumentSetView, DocumentView


class ApiClient:
    def __init__(self, base_url: str) -> None:
        # httpx's default timeout (5s total) is far too short for
        # upload_document/ask, which trigger real Gemini/Groq API calls on
        # the backend that can legitimately take well over that for a real
        # multi-chunk document. Generous timeout applies to every call.
        self._client = httpx.Client(base_url=base_url, timeout=180.0)

    def create_set(self, name: str) -> DocumentSetView:
        response = self._client.post("/sets", json={"name": name})
        response.raise_for_status()
        return self._parse_set(response.json())

    def list_sets(self) -> list[DocumentSetView]:
        response = self._client.get("/sets")
        response.raise_for_status()
        return [self._parse_set(item) for item in response.json()]

    def delete_set(self, set_id: str) -> None:
        response = self._client.delete(f"/sets/{set_id}")
        response.raise_for_status()

    def list_documents(self, set_id: str | None = None) -> list[DocumentView]:
        params = {"set_id": set_id} if set_id else {}
        response = self._client.get("/documents", params=params)
        response.raise_for_status()
        return [self._parse_document(item) for item in response.json()]

    def upload_document(self, set_id: str, filename: str, content: bytes) -> DocumentView:
        response = self._client.post(
            "/documents",
            params={"set_id": set_id},
            files={"file": (filename, content)},
        )
        response.raise_for_status()
        return self._parse_document(response.json())

    def remove_document(self, document_id: str) -> None:
        response = self._client.delete(f"/documents/{document_id}")
        response.raise_for_status()

    def ask(self, question: str, set_id: str | None, session_id: str) -> AnswerView:
        response = self._client.post(
            "/query", json={"question": question, "set_id": set_id, "session_id": session_id}
        )
        response.raise_for_status()
        data = response.json()
        return AnswerView(
            answer=data["answer"],
            citations=[CitationView(**item) for item in data["citations"]],
            grounded=data["grounded"],
        )

    @staticmethod
    def _parse_set(data: dict) -> DocumentSetView:
        return DocumentSetView(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    @staticmethod
    def _parse_document(data: dict) -> DocumentView:
        return DocumentView(
            id=data["id"],
            set_id=data["set_id"],
            filename=data["filename"],
            format=data["format"],
            status=data["status"],
            uploaded_at=datetime.fromisoformat(data["uploaded_at"]),
        )


@st.cache_resource
def get_api_client() -> ApiClient:
    return ApiClient(base_url=Settings().backend_url)
