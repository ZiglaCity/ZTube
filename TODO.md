# ZTube Cleanup TODO

This is the working roadmap for turning ZTube from an old personal prototype into a clean, maintainable open-source app. The current refactor targets the desktop app first; once the desktop version is stable, the project will grow a separate web app. Keep this file honest: move items to done only after the code, docs, and basic verification are handled.

## Phase 0: Stop The Bleeding

- [ ] Revoke the Google API key that was hardcoded in `ZTube.py`.
- [x] Decide the canonical entry point: use `desktop/ztube_desktop/app.py`, with root `main.py` as a compatibility launcher.
- [x] Remove generated artifacts from the repo/worktree: `build/`, `dist/`, `__pycache__/`, and packaged executable outputs.
- [x] Expand `.gitignore` for Python/editor/build noise: `__pycache__/`, `*.py[cod]`, `.venv/`, `.env`, `.idea/`, `.vscode/`, `*.spec`, and local secret files.
- [x] Add an `.env.example` or documented config file showing how to provide `YOUTUBE_API_KEY` without committing secrets.
- [x] Add a license file that matches the README's MIT claim.
- [x] Replace the loose lowercase `todo` file with this `TODO.md` once all useful notes are migrated.

## Phase 1: Make The App Reliable

- [x] Guard the app startup with `if __name__ == "__main__":` so imports do not launch Tkinter.
- [x] Handle a missing API key gracefully instead of crashing at `with open("api_key.txt", "r")`.
- [x] Initialize app state explicitly: selected video URL, download path, theme, current screen, progress, and API key.
- [x] Fix thread-safety issues: all Tkinter widget updates and message boxes from download/background work should be scheduled through `root.after`.
- [x] Keep search result rendering responsive by loading thumbnails off the Tkinter UI thread.
- [x] Keep video selection responsive by loading quality options off the Tkinter UI thread.
- [x] Prevent duplicate downloads by disabling the download button while a download is running.
- [x] Validate the selected download directory before starting a download.
- [x] Fix empty folder selection: canceling the folder picker should keep the existing folder.
- [ ] Stop using broad `except Exception` for user-facing flows where specific errors can produce clearer messages.
- [x] Add timeouts and error handling for thumbnail requests.
- [x] Cache thumbnails during a search result render so the UI does not re-download the same images unnecessarily.
- [x] Decide how direct YouTube URLs should work: direct video URLs resolve to that video; other input runs a YouTube search.
- [ ] Fix quality selection for high resolutions. Progressive MP4 streams often stop at lower resolutions; 1080p+ usually needs separate video/audio streams and merging. Current behavior often shows only one quality option, which is likely due to progressive-only stream filtering.
- [ ] Add audio-only/MP3 support deliberately, including the ffmpeg requirement if conversion is needed. This can also support video-to-audio conversion for users who only need audio.
- [x] Add cancellation or at least clear in-progress status for long downloads.
- [x] Improve progress reporting smoothness; current stream chunks can be large enough that the progress bar updates feel jumpy.

## Phase 2: Restructure The Codebase

- [x] Split the repository into clear product surfaces:
  - `desktop/` for the Tkinter desktop app and desktop-specific packaging.
  - `web/` for the future web version.
  - `shared/` or `packages/` only if we identify logic that can genuinely be reused across both.
- [x] Treat the desktop app as the first refactor target; do not block desktop cleanup on web architecture decisions.
- [x] Create a package layout, for example:
  - `desktop/ztube_desktop/app.py` for desktop startup.
  - `desktop/ztube_desktop/ui/main_window.py` for Tkinter screens and widgets.
  - `desktop/ztube_desktop/services/youtube_search.py` for YouTube Data API calls.
  - `desktop/ztube_desktop/services/downloader.py` for pytubefix download logic.
  - `desktop/ztube_desktop/config.py` for settings and environment variables.
  - `desktop/tests/` for desktop unit tests.
- [x] Replace global business state with an `AppState` object.
- [ ] Move remaining widget globals into a controller/window class.
- [x] Separate UI rendering from network/download logic so services can be tested without Tkinter.
- [x] Remove duplicate nested functions such as local `select_video` handlers that are no longer used.
- [x] Replace repeated theme dictionaries and recursive styling logic with one theme manager.
- [x] Introduce type hints for service functions and shared state.
- [x] Add a logging setup and remove leftover debug `print` calls.
- [x] Pick consistent naming: `openSettings`/`openSearchedResults` should become snake_case.
- [x] Add project lint/format configuration and lint with `ruff`.
- [x] Create a project-local virtual environment so latest ZTube dependencies do not conflict with unrelated global Python packages.

## Phase 3: Improve The UI

- [ ] Redesign the main screen around the actual workflow: search/input, results, selected video, quality, destination, and download status.
- [x] Keep search results and download controls in one flow, or make navigation clearer when switching screens.
- [x] Make the selected video visually obvious beyond blue title text.
- [x] Add placeholder/empty states for no search, no results, offline, loading, and failed thumbnail loading.
- [x] Add a loading state while search results are being fetched.
- [x] Improve dark mode coverage for every screen, including ttk widgets.
- [x] Replace emoji-only buttons with accessible labels or icons plus tooltips.
- [x] Make long video titles wrap or truncate cleanly inside the result area.
- [x] Show file size, format, and resolution in a more readable quality picker.
- [x] Show download destination near the download action, not only in settings.
- [x] Make settings actually persist before keeping a "Save Settings" button.
- [x] Add mouse-wheel scrolling to the search results list.
- [x] Return 20+ search results instead of stopping at the old small default.

## Phase 4: Open-Source Polish

- [x] Rewrite `README.md` so it explains the current desktop app, repository layout, setup, API key requirements, usage, checks, limitations, future `web/` boundary, and legal notes.
- [x] Add `CONTRIBUTING.md` with setup, tests, linting, branch, and PR expectations.
- [x] Add `SECURITY.md` explaining how to report vulnerabilities and reminding users not to commit API keys.
- [x] Add issue templates for bug reports and feature requests.
- [x] Add a changelog.
- [x] Replace the Google Drive executable link with reproducible release instructions or GitHub Releases.
- [ ] Add screenshot assets with consistent names and sizes, and remove stale screenshots if they no longer match the UI.
- [x] Add legal/disclaimer text about respecting YouTube terms, copyright, and local laws.
- [x] Add a clear supported Python version range.

## Phase 5: Testing And Automation

- [x] Add `pytest` and unit tests for configuration loading, URL parsing, quality option formatting, and download path validation.
- [x] Mock YouTube API and pytubefix calls in tests.
- [x] Add a smoke test that imports the package without starting the GUI.
- [x] Add lint/typecheck commands to project metadata.
- [x] Add GitHub Actions for linting and tests.
- [ ] Add packaging/build automation only after the app structure is stable.

## Phase 6: Web Version

- [ ] Start the `web/` version only after the desktop refactor reaches a stable baseline.
- [ ] Decide the web architecture: likely Flask full-stack or React frontend with FastAPI backend.
- [ ] Keep API keys server-side only in the web version; never expose the YouTube API key to browser JavaScript, public env files, logs, or client bundles.
- [ ] Decide hosting and whether downloads happen server-side or client-assisted.
- [ ] Reuse concepts from the desktop refactor where practical: search service boundaries, config conventions, validation rules, and legal/disclaimer language.
- [ ] Design a polished web UI from scratch instead of copying the Tkinter layout directly.
- [ ] Define web-specific safety, rate limiting, API key handling, and deployment requirements.
- [ ] Add separate web tests, linting, and build commands.

## Current Notes

- The exposed Google API key still needs to be revoked outside the repo.
- The maintained desktop app is `desktop/ztube_desktop`; root `main.py` is a compatibility launcher.
- `desktop/ztube_desktop/config.py` loads `YOUTUBE_API_KEY`, optional PoToken values, and persisted user settings.
- User settings are stored outside the repository at `~/.ztube/desktop-settings.json`.
- `desktop/ztube_desktop/services/downloader.py` tries multiple pytubefix clients and supports optional local PoToken config for videos that trigger YouTube bot detection.
- Search supports keywords and direct YouTube video URLs.
- Search results render 25 videos, load thumbnails asynchronously, and support mouse-wheel scrolling.
- Quality lookup and downloads run off the Tkinter UI thread.
- The desktop UI has light/dark themes, selected-result highlighting, and compact download controls, but `app.py` still has widget globals that should move into a controller/window class.
- High-resolution merged downloads and audio-only/MP3 conversion are not implemented yet.
- Generated build outputs are covered by `.gitignore`.
