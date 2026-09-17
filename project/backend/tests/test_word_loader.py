from backend.domain.models import DocumentFormat
from backend.loaders.word_loader import WordLoader


def test_supports_only_word_format():
    loader = WordLoader()
    assert loader.supports(DocumentFormat.WORD) is True
    assert loader.supports(DocumentFormat.MARKDOWN) is False


def test_parse_extracts_paragraph_text(make_docx):
    file = make_docx("doc.docx", ["First paragraph.", "Second paragraph."])

    text = WordLoader().parse(file)

    assert "First paragraph." in text
    assert "Second paragraph." in text
