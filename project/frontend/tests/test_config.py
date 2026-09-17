from frontend.config import Settings


def test_settings_ignores_env_vars_meant_for_other_tiers(monkeypatch, tmp_path):
    # The .env file is shared across all tiers by design (see .env.example) -
    # GROQ_API_KEY/GOOGLE_API_KEY/CHROMA_PERSIST_DIR are backend-only.
    # Frontend's Settings must not fail just because they're present in the
    # same file.
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GROQ_API_KEY=test-groq-key\n"
        "GOOGLE_API_KEY=test-google-key\n"
        "CHROMA_PERSIST_DIR=/tmp/chroma\n"
        "BACKEND_URL=http://127.0.0.1:9000\n"
    )
    monkeypatch.setattr(Settings, "model_config", {**Settings.model_config, "env_file": env_file})

    settings = Settings()

    assert settings.backend_url == "http://127.0.0.1:9000"
