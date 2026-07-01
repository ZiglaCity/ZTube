from desktop.ztube_desktop import config

FIXTURES_DIR = config.PROJECT_ROOT / "desktop" / "tests" / "fixtures"


def test_strip_env_value_removes_matching_quotes():
    assert config._strip_env_value(' "abc123" ') == "abc123"
    assert config._strip_env_value(" 'abc123' ") == "abc123"


def test_read_env_file_ignores_comments_and_empty_lines():
    values = config._read_env_file(FIXTURES_DIR / "sample.env")

    assert values["YOUTUBE_API_KEY"] == "secret"
    assert values["EMPTY"] == ""
    assert "INVALID" not in values


def test_load_value_prefers_environment(monkeypatch):
    monkeypatch.setenv(config.API_KEY_ENV_VAR, "from-env")

    value, source = config._load_value(config.API_KEY_ENV_VAR)

    assert value == "from-env"
    assert source == "environment"


def test_save_and_load_user_settings():
    settings_path = FIXTURES_DIR / "generated-settings.json"
    settings = config.UserSettings(
        download_path=FIXTURES_DIR,
        dark_theme_enabled=True,
    )

    try:
        config.save_user_settings(settings, settings_path=settings_path)
        loaded = config.load_user_settings(settings_path=settings_path)
    finally:
        settings_path.unlink(missing_ok=True)

    assert loaded == settings
