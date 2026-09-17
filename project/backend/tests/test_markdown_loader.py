from backend.domain.models import DocumentFormat
from backend.loaders.markdown_loader import MarkdownLoader


def test_supports_only_markdown_format():
    loader = MarkdownLoader()
    assert loader.supports(DocumentFormat.MARKDOWN) is True
    assert loader.supports(DocumentFormat.TEXT) is False


def test_parse_reads_file_contents(tmp_path):
    file = tmp_path / "readme.md"
    file.write_text("# Title\n\nSome body text.", encoding="utf-8")

    assert MarkdownLoader().parse(file) == "# Title\n\nSome body text."
