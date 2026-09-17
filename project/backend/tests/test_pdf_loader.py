from backend.domain.models import DocumentFormat
from backend.loaders.pdf_loader import PdfLoader


def test_supports_only_pdf_format():
    loader = PdfLoader()
    assert loader.supports(DocumentFormat.PDF) is True
    assert loader.supports(DocumentFormat.WORD) is False


def test_parse_extracts_text(make_pdf):
    file = make_pdf("doc.pdf", "Hello PDF")

    assert "Hello PDF" in PdfLoader().parse(file)
