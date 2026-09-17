import pytest

from backend.domain.models import DocumentFormat
from backend.loaders.markdown_loader import MarkdownLoader
from backend.loaders.registry import DocumentLoaderRegistry, default_registry


def test_default_registry_resolves_all_launch_formats():
    registry = default_registry()

    for format in DocumentFormat:
        loader = registry.get_loader(format)
        assert loader.supports(format)


def test_get_loader_raises_for_unregistered_format():
    registry = DocumentLoaderRegistry()

    with pytest.raises(ValueError, match="No loader registered"):
        registry.get_loader(DocumentFormat.MARKDOWN)


def test_register_and_get_loader_round_trip():
    registry = DocumentLoaderRegistry()
    loader = MarkdownLoader()

    registry.register(DocumentFormat.MARKDOWN, loader)

    assert registry.get_loader(DocumentFormat.MARKDOWN) is loader
