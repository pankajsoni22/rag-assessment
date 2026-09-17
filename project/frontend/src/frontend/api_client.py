from __future__ import annotations

from datetime import datetime

import httpx
import streamlit as st

from frontend.config import Settings
from frontend.models import DocumentSetView, DocumentView


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.Client(base_url=base_url)

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
