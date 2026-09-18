from pathlib import Path

from streamlit.testing.v1 import AppTest

_PAGE = str(Path(__file__).resolve().parents[1] / "src" / "frontend" / "pages" / "home.py")


def test_landing_page_renders_call_to_action_and_steps():
    at = AppTest.from_file(_PAGE)
    at.run()

    assert not at.exception
    assert any(b.label == "Start With RAG Assessment Project" for b in at.button)
    rendered = " ".join(m.value for m in at.markdown)
    assert "How it works" in rendered
    for step in ("Create a set", "Select the set", "Upload documents", "Ask in Chat"):
        assert step in rendered
