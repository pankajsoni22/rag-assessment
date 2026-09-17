from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VectorStore(Protocol):
    """Persistence boundary the backend depends on for chunk storage and similarity search.

    Deliberately uses only plain types (dict/list/str), not backend domain classes,
    so any implementation (e.g. the storage tier's Chroma-backed one) never needs to
    import from backend — the two tiers stay splittable into separate deployments.

    A record is a dict shaped:
        {"id": str, "embedding": list[float], "text": str, "metadata": dict[str, Any]}
    A query result is a record dict plus a "distance" key (lower = more similar).
    """

    def upsert(self, records: list[dict[str, Any]]) -> None:
        """Insert new records or overwrite existing ones by id."""
        ...

    def query(
        self,
        embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return up to top_k records most similar to embedding, optionally filtered by metadata."""
        ...

    def delete(self, document_id: str) -> None:
        """Remove every record whose metadata document_id matches."""
        ...
