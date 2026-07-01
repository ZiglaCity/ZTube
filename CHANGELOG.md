# Changelog

All notable changes to ZTube will be documented here.

## Unreleased

- Refactored the desktop app into the `desktop/ztube_desktop` package with
  root `main.py` kept as a launcher.
- Added environment and `.env` configuration for `YOUTUBE_API_KEY`, optional
  pytubefix PoToken values, and persisted desktop settings.
- Added YouTube keyword search and direct video URL resolution.
- Increased search results to 25 items.
- Added asynchronous search-result thumbnail loading and asynchronous quality
  lookup so the Tkinter UI stays responsive.
- Added thumbnail caching, failed-thumbnail placeholders, no-result states,
  search loading state, offline status, mouse-wheel scrolling, and blue
  selected-video highlighting.
- Added progressive MP4 quality labels with format, resolution, and estimated
  file size.
- Added clearer download state and progress feedback.
- Added light/dark theme coverage for the main screen, search results,
  settings, and ttk widgets.
- Added safer pytubefix downloader error handling for bot detection,
  unavailable videos, and network failures.
- Added tests for configuration, YouTube URL parsing/search wrapping,
  downloader helpers, and import smoke behavior.
- Added open-source project docs, security notes, issue templates, and desktop
  CI configuration.
