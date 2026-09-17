from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document as DocxDocument
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def _make_pdf(path: Path, text: str) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)

    font = DictionaryObject()
    font[NameObject("/Type")] = NameObject("/Font")
    font[NameObject("/Subtype")] = NameObject("/Type1")
    font[NameObject("/BaseFont")] = NameObject("/Helvetica")
    font_ref = writer._add_object(font)

    fonts = DictionaryObject()
    fonts[NameObject("/F1")] = font_ref
    resources = DictionaryObject()
    resources[NameObject("/Font")] = fonts
    page[NameObject("/Resources")] = resources

    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 24 Tf 20 100 Td ({text}) Tj ET".encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)

    with open(path, "wb") as f:
        writer.write(f)


@pytest.fixture
def make_pdf(tmp_path):
    def _make(filename: str, text: str) -> Path:
        path = tmp_path / filename
        _make_pdf(path, text)
        return path

    return _make


@pytest.fixture
def make_docx(tmp_path):
    def _make(filename: str, paragraphs: list[str]) -> Path:
        path = tmp_path / filename
        document = DocxDocument()
        for paragraph in paragraphs:
            document.add_paragraph(paragraph)
        document.save(path)
        return path

    return _make
