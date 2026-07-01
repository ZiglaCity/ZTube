from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from urllib.error import URLError

from pytubefix import YouTube
from pytubefix.exceptions import (
    AgeCheckRequiredAccountError,
    AgeCheckRequiredError,
    AgeRestrictedError,
    BotDetection,
    LoginRequired,
    MembersOnly,
    PoTokenRequired,
    RecordingUnavailable,
    VideoPrivate,
    VideoRegionBlocked,
    VideoUnavailable,
)

ProgressCallback = Callable[[object, bytes, int], None]
PoTokenPair = tuple[str, str]
YOUTUBE_CLIENTS = ("ANDROID_VR", "WEB_EMBED", "MWEB", "IOS", "ANDROID_MUSIC", "TV")


class YouTubeBotBlockedError(RuntimeError):
    """Raised when YouTube requires a proof-of-origin token for stream data."""


class YouTubeVideoUnavailableError(RuntimeError):
    """Raised when YouTube reports that a selected video cannot be downloaded."""


class YouTubeNetworkError(RuntimeError):
    """Raised when pytubefix cannot reach YouTube stream metadata."""


BOT_BLOCKED_ERRORS = (BotDetection, PoTokenRequired)


UNAVAILABLE_ERRORS = (
    AgeCheckRequiredAccountError,
    AgeCheckRequiredError,
    AgeRestrictedError,
    LoginRequired,
    MembersOnly,
    RecordingUnavailable,
    VideoPrivate,
    VideoRegionBlocked,
    VideoUnavailable,
)


def _po_token_verifier(po_token_pair: PoTokenPair):
    def verifier() -> PoTokenPair:
        return po_token_pair

    return verifier


def _create_po_token_youtube(
    url: str,
    on_progress: ProgressCallback | None,
    po_token_pair: PoTokenPair,
) -> YouTube:
    return YouTube(
        url,
        on_progress_callback=on_progress,
        use_po_token=True,
        po_token_verifier=_po_token_verifier(po_token_pair),
    )


def _bot_blocked_error(cause: Exception | None) -> YouTubeBotBlockedError:
    error = YouTubeBotBlockedError(
        "YouTube blocked stream metadata for this video. Add "
        "YOUTUBE_VISITOR_DATA and YOUTUBE_PO_TOKEN to your local .env file "
        "to enable pytubefix PoToken mode."
    )
    if cause:
        return error.with_traceback(cause.__traceback__)
    return error


def _video_unavailable_error(cause: Exception) -> YouTubeVideoUnavailableError:
    return YouTubeVideoUnavailableError(
        "This video is unavailable for download. It may be private, region "
        "blocked, age restricted, members-only, removed, or unsupported by "
        "YouTube's current stream metadata."
    ).with_traceback(cause.__traceback__)


def _network_error(cause: Exception) -> YouTubeNetworkError:
    return YouTubeNetworkError(
        "Could not reach YouTube stream metadata. Check your connection, VPN, "
        "proxy, firewall, or try again in a moment."
    ).with_traceback(cause.__traceback__)


def format_quality_option(stream: object) -> str:
    resolution = getattr(stream, "resolution", None) or "unknown"
    filesize = getattr(stream, "filesize", 0) or 0
    size_mb = filesize // (1024 * 1024)
    return f"MP4 video - {resolution} - {size_mb} MB"


def validate_output_path(output_path: Path) -> Path:
    if not output_path.is_dir():
        raise ValueError(f"Download folder does not exist: {output_path}")
    return output_path


def get_quality_options(
    url: str, po_token_pair: PoTokenPair | None = None
) -> list[str]:
    last_bot_error: Exception | None = None
    last_network_error: URLError | None = None

    for client in YOUTUBE_CLIENTS:
        try:
            yt = YouTube(url, client=client)
            streams = yt.streams.filter(progressive=True, file_extension="mp4")
            break
        except BOT_BLOCKED_ERRORS as error:
            last_bot_error = error
        except UNAVAILABLE_ERRORS as error:
            raise _video_unavailable_error(error)
        except URLError as error:
            last_network_error = error
    else:
        if po_token_pair:
            yt = _create_po_token_youtube(url, None, po_token_pair)
            try:
                streams = yt.streams.filter(progressive=True, file_extension="mp4")
            except UNAVAILABLE_ERRORS as error:
                raise _video_unavailable_error(error)
            except URLError as error:
                raise _network_error(error)
        elif last_network_error and not last_bot_error:
            raise _network_error(last_network_error)
        else:
            raise _bot_blocked_error(last_bot_error)

    if not streams:
        return []

    return [format_quality_option(stream) for stream in streams]


def download_video(
    url: str,
    resolution: str,
    output_path: Path,
    on_progress: ProgressCallback,
    po_token_pair: PoTokenPair | None = None,
) -> None:
    output_path = validate_output_path(output_path)
    last_bot_error: Exception | None = None
    last_network_error: URLError | None = None

    for client in YOUTUBE_CLIENTS:
        try:
            yt = YouTube(url, client=client, on_progress_callback=on_progress)
            stream = yt.streams.filter(
                res=resolution,
                progressive=True,
                file_extension="mp4",
            ).first()
            break
        except BOT_BLOCKED_ERRORS as error:
            last_bot_error = error
        except UNAVAILABLE_ERRORS as error:
            raise _video_unavailable_error(error)
        except URLError as error:
            last_network_error = error
    else:
        if po_token_pair:
            yt = _create_po_token_youtube(url, on_progress, po_token_pair)
            try:
                stream = yt.streams.filter(
                    res=resolution,
                    progressive=True,
                    file_extension="mp4",
                ).first()
            except UNAVAILABLE_ERRORS as error:
                raise _video_unavailable_error(error)
            except URLError as error:
                raise _network_error(error)
        elif last_network_error and not last_bot_error:
            raise _network_error(last_network_error)
        else:
            raise _bot_blocked_error(last_bot_error)

    if not stream:
        raise ValueError(f"No stream found for resolution {resolution}.")

    stream.download(output_path=str(output_path), skip_existing=False, max_retries=5)
