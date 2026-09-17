from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument

from backend.domain.models import DocumentFormat


class WordLoader:
    def supports(self, format: DocumentFormat) -> bool:
        return format == DocumentFormat.WORD

    def parse(self, file: Path) -> str:
        document = DocxDocument(str(file))
        return "\n\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)
