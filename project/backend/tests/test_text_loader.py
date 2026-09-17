from backend.domain.models import DocumentFormat
from backend.loaders.text_loader import TextLoader


def test_supports_only_text_format():
    loader = TextLoader()
    assert loader.supports(DocumentFormat.TEXT) is True
    assert loader.supports(DocumentFormat.PDF) is False


def test_parse_reads_file_contents(tmp_path):
    file = tmp_path / "notes.txt"
    file.write_text("hello world", encoding="utf-8")

    assert TextLoader().parse(file) == "hello world"
