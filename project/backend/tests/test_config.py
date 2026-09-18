from backend.config import Settings


def test_settings_ignores_env_vars_meant_for_other_tiers(monkeypatch, tmp_path):
    # The .env file is shared across all tiers by design (see .env.example) -
    # BACKEND_URL is frontend-only. Backend's Settings must not fail just
    # because it's present in the same file.
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=test-groq-key\n"
        "GOOGLE_API_KEY=test-google-key\n"
        "CHROMA_PERSIST_DIR=/tmp/chroma\n"
        "BACKEND_URL=http://127.0.0.1:8000\n"
    )
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": env_file})

    settings = Settings()

    assert settings.groq_api_key == "test-groq-key"
    assert settings.google_api_key == "test-google-key"
    assert settings.chroma_persist_dir == "/tmp/chroma"


def test_chroma_host_defaults_to_empty_for_embedded_mode(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=test-groq-key\n"
        "GOOGLE_API_KEY=test-google-key\n"
        "CHROMA_PERSIST_DIR=/tmp/chroma\n"
    )
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": env_file})

    settings = Settings()

    assert settings.chroma_host == ""
    assert settings.chroma_port == 8000


def test_chroma_host_and_port_read_from_env(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=test-groq-key\n"
        "GOOGLE_API_KEY=test-google-key\n"
        "CHROMA_PERSIST_DIR=/tmp/chroma\n"
        "CHROMA_HOST=chroma\n"
        "CHROMA_PORT=9000\n"
    )
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": env_file})

    settings = Settings()

    assert settings.chroma_host == "chroma"
    assert settings.chroma_port == 9000
