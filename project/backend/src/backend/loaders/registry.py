from __future__ import annotations

from pathlib import Path

from backend.domain.models import DocumentFormat
from backend.interfaces.document_loader import DocumentLoader
from backend.loaders.markdown_loader import MarkdownLoader
from backend.loaders.pdf_loader import PdfLoader
from backend.loaders.text_loader import TextLoader
from backend.loaders.word_loader import WordLoader

_EXTENSION_TO_FORMAT: dict[str, DocumentFormat] = {
    ".pdf": DocumentFormat.PDF,
    ".docx": DocumentFormat.WORD,
    ".txt": DocumentFormat.TEXT,
    ".md": DocumentFormat.MARKDOWN,
}


def format_from_filename(filename: str) -> DocumentFormat:
    suffix = Path(filename).suffix.lower()
    try:
        return _EXTENSION_TO_FORMAT[suffix]
    except KeyError:
        raise ValueError(f"Unsupported file extension: {suffix or filename!r}") from None


class DocumentLoaderRegistry:
    def __init__(self) -> None:
        self._loaders: dict[DocumentFormat, DocumentLoader] = {}

    def register(self, format: DocumentFormat, loader: DocumentLoader) -> None:
        self._loaders[format] = loader

    def get_loader(self, format: DocumentFormat) -> DocumentLoader:
        try:
            return self._loaders[format]
        except KeyError:
            raise ValueError(f"No loader registered for format: {format}") from None


def default_registry() -> DocumentLoaderRegistry:
    """Registry pre-populated with the built-in loaders for all launch formats."""
    registry = DocumentLoaderRegistry()
    registry.register(DocumentFormat.PDF, PdfLoader())
    registry.register(DocumentFormat.WORD, WordLoader())
    registry.register(DocumentFormat.TEXT, TextLoader())
    registry.register(DocumentFormat.MARKDOWN, MarkdownLoader())
    return registry
