from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from backend.domain.models import DocumentFormat


@runtime_checkable
class DocumentLoader(Protocol):
    """Strategy interface: one implementation per document format.

    Adding a new format means adding one new class and registering it
    (see loaders/registry.py) — existing loaders are never touched.
    """

    def supports(self, format: DocumentFormat) -> bool: ...

    def parse(self, file: Path) -> str: ...
