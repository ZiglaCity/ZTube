# ZTube

ZTube is a desktop YouTube search and download app built with Python and Tkinter.
The maintained app code lives in `desktop/ztube_desktop/`; the root `main.py`
file is a small compatibility launcher.

## Current Desktop App

- Search YouTube by keyword or paste a direct YouTube video URL.
- Show 25 search results with titles and asynchronously loaded thumbnails.
- Keep the UI responsive while searching, loading thumbnails, loading quality
  options, and downloading.
- Select a video from the results list with a visible blue highlight.
- List available progressive MP4 quality options with format, resolution, and
  estimated file size.
- Download the selected video to a local folder.
- Show download state and progress.
- Persist desktop settings such as download folder and theme mode.
- Support light and dark themes.
- Handle missing API keys, unavailable videos, network failures, thumbnail
  failures, and pytubefix bot-detection errors with user-facing messages.

## Repository Layout

- `main.py`: root launcher for the desktop app.
- `desktop/ztube_desktop/app.py`: Tkinter desktop UI and app startup.
- `desktop/ztube_desktop/config.py`: `.env`, environment, and user settings.
- `desktop/ztube_desktop/services/youtube_search.py`: YouTube Data API search
  and URL resolution.
- `desktop/ztube_desktop/services/downloader.py`: pytubefix quality lookup and
  downloads.
- `desktop/ztube_desktop/ui/themes.py`: light/dark theme helpers.
- `desktop/tests/`: unit and smoke tests.
- `web/`: reserved for a future web version.

## Requirements

- Python 3.13.
- Tkinter, usually bundled with desktop Python installs.
- A YouTube Data API key for search.

Install runtime dependencies:

```powershell
pip install -r requirements.txt
```

For development checks:

```powershell
pip install -r requirements-dev.txt
```

## Configuration

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Set your YouTube Data API key:

```text
YOUTUBE_API_KEY=your_youtube_data_api_key_here
```

You can also set the key in your shell instead of using `.env`:

```powershell
$env:YOUTUBE_API_KEY = "your_youtube_data_api_key_here"
```

Some videos may trigger YouTube bot detection when pytubefix reads stream
metadata. ZTube tries multiple pytubefix clients first. If YouTube still blocks
the request, optional local PoToken values can be provided:

```text
YOUTUBE_VISITOR_DATA=your_visitor_data_here
YOUTUBE_PO_TOKEN=your_po_token_here
```

Never commit real API keys, visitor data, PoToken values, OAuth/cache files, or
local `.env` files.

Desktop settings are stored outside the repository at:

```text
~/.ztube/desktop-settings.json
```

## Run

```powershell
python main.py
```

or:

```powershell
python -m desktop.ztube_desktop
```

## Checks

Fast local verification:

```powershell
python -m py_compile main.py desktop\ztube_desktop\app.py desktop\ztube_desktop\config.py desktop\ztube_desktop\services\youtube_search.py desktop\ztube_desktop\services\downloader.py desktop\ztube_desktop\ui\themes.py
ruff check main.py desktop
pytest
```

The repository still contains Black configuration for release/CI formatting
checks, but day-to-day cleanup work currently uses compile, Ruff, and pytest.

## Current Limitations

- High-resolution downloads above the progressive MP4 set usually require
  separate video/audio streams and ffmpeg merging. ZTube currently downloads
  progressive MP4 streams only.
- MP3/audio-only conversion is not implemented yet.
- Download cancellation is not implemented; the UI shows an in-progress state
  while the worker runs.
- The desktop UI is still Tkinter-based and has remaining controller/widget
  refactor work tracked in `TODO.md`.
- Packaged executable releases are not published yet.

## Future Web Version

The future web app will live separately under `web/`. Its architecture is not
chosen yet. Any web implementation must keep API keys server-side only; private
keys must never be exposed in browser JavaScript, client bundles, public env
files, logs, screenshots, or error payloads.

## Legal Notice

Use ZTube responsibly. Respect YouTube's terms, copyright law, and local rules.
Only download content when you have the right to do so.

## License

This project is licensed under the MIT License. See `LICENSE`.
