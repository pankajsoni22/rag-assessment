from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from backend.domain.models import DocumentFormat


class PdfLoader:
    def supports(self, format: DocumentFormat) -> bool:
        return format == DocumentFormat.PDF

    def parse(self, file: Path) -> str:
        reader = PdfReader(str(file))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
