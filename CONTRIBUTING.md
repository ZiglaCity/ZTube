# Contributing

Thanks for helping improve ZTube. The current supported surface is the Tkinter
desktop app under `desktop/ztube_desktop/`. The `web/` surface is reserved for a
future app and should stay separate from desktop changes.

## Setup

Use a project-local virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Create local configuration:

```powershell
Copy-Item .env.example .env
```

Set `YOUTUBE_API_KEY` in `.env`. Optional pytubefix PoToken values may also be
stored there for local testing. Do not commit real API keys, visitor data,
PoToken values, OAuth/cache files, or local settings.

## Run

```powershell
python main.py
```

or:

```powershell
python -m desktop.ztube_desktop
```

## Verify Changes

Use these checks for normal local work:

```powershell
python -m py_compile main.py desktop\ztube_desktop\app.py desktop\ztube_desktop\config.py desktop\ztube_desktop\services\youtube_search.py desktop\ztube_desktop\services\downloader.py desktop\ztube_desktop\ui\themes.py
ruff check main.py desktop
pytest
```

Avoid mixing formatting-only churn into feature or bug-fix changes.

## Pull Request Expectations

- Keep desktop app changes under `desktop/` unless changing docs, root launch
  files, or project configuration.
- Keep web work under `web/` once that surface starts.
- Prefer small, reviewable PRs.
- Update `TODO.md` when finishing roadmap items.
- Update user-facing docs when behavior, setup, limitations, or security
  guidance changes.
- Do not commit generated files such as `build/`, `dist/`, `__pycache__/`,
  `.pytest_cache/`, pytest temp folders, or local virtual environments.
- Do not commit secrets.
