from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_runs_without_error():
    app_path = Path(__file__).resolve().parents[1] / "src" / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.run()
    assert not at.exception
