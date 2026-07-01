"""Configuration helpers for the ZTube desktop app."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

API_KEY_ENV_VAR = "YOUTUBE_API_KEY"
VISITOR_DATA_ENV_VAR = "YOUTUBE_VISITOR_DATA"
PO_TOKEN_ENV_VAR = "YOUTUBE_PO_TOKEN"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = Path.home() / ".ztube" / "desktop-settings.json"


@dataclass(frozen=True)
class AppConfig:
    youtube_api_key: str | None
    youtube_visitor_data: str | None
    youtube_po_token: str | None
    default_download_path: Path
    dark_theme_enabled: bool
    loaded_from: str


@dataclass(frozen=True)
class UserSettings:
    download_path: Path
    dark_theme_enabled: bool = False


def _strip_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = _strip_env_value(value)

    return values


def _load_value(name: str) -> tuple[str | None, str]:
    env_value = os.getenv(name)
    if env_value and env_value.strip():
        return env_value.strip(), "environment"

    env_paths = [
        PROJECT_ROOT / ".env",
        Path(__file__).resolve().parent / ".env",
    ]
    for env_path in env_paths:
        file_value = _read_env_file(env_path).get(name)
        if file_value and file_value.strip():
            return file_value.strip(), str(env_path)

    return None, "not configured"


def load_user_settings(settings_path: Path = SETTINGS_PATH) -> UserSettings:
    default_settings = UserSettings(download_path=Path.home() / "Downloads")
    if not settings_path.is_file():
        return default_settings

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_settings

    download_path = Path(data.get("download_path") or default_settings.download_path)
    dark_theme_enabled = bool(data.get("dark_theme_enabled", False))
    return UserSettings(
        download_path=download_path,
        dark_theme_enabled=dark_theme_enabled,
    )


def save_user_settings(
    settings: UserSettings, settings_path: Path = SETTINGS_PATH
) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "download_path": str(settings.download_path),
                "dark_theme_enabled": settings.dark_theme_enabled,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_config() -> AppConfig:
    """Load configuration from the environment or local .env files."""
    api_key, loaded_from = _load_value(API_KEY_ENV_VAR)
    visitor_data, _ = _load_value(VISITOR_DATA_ENV_VAR)
    po_token, _ = _load_value(PO_TOKEN_ENV_VAR)
    user_settings = load_user_settings()

    return AppConfig(
        youtube_api_key=api_key,
        youtube_visitor_data=visitor_data,
        youtube_po_token=po_token,
        default_download_path=user_settings.download_path,
        dark_theme_enabled=user_settings.dark_theme_enabled,
        loaded_from=loaded_from,
    )
