from __future__ import annotations

from pathlib import Path

from backend.domain.models import DocumentFormat


class TextLoader:
    def supports(self, format: DocumentFormat) -> bool:
        return format == DocumentFormat.TEXT

    def parse(self, file: Path) -> str:
        return file.read_text(encoding="utf-8")
