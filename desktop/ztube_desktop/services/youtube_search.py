from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qs, urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import Error as GoogleApiError

VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class YouTubeSearchError(RuntimeError):
    """Raised when the YouTube Data API search/details request fails."""


def extract_video_id(value: str) -> str | None:
    value = value.strip()
    if VIDEO_ID_PATTERN.fullmatch(value):
        return value

    parsed = urlparse(value)
    if parsed.netloc in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/", 1)[0]
        return video_id if VIDEO_ID_PATTERN.fullmatch(video_id) else None

    if parsed.netloc.endswith("youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
            return (
                video_id if video_id and VIDEO_ID_PATTERN.fullmatch(video_id) else None
            )

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
            video_id = path_parts[1]
            return video_id if VIDEO_ID_PATTERN.fullmatch(video_id) else None

    return None


def _video_from_search_item(item: dict) -> dict[str, str]:
    return {
        "title": unescape(item["snippet"]["title"]),
        "videoId": item["id"]["videoId"],
        "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
    }


def _video_from_video_item(item: dict) -> dict[str, str]:
    return {
        "title": unescape(item["snippet"]["title"]),
        "videoId": item["id"],
        "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
    }


def get_video(api_key: str, video_id: str) -> dict[str, str] | None:
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        request = youtube.videos().list(
            id=video_id,
            part="snippet",
            maxResults=1,
        )
        response = request.execute()
    except GoogleApiError as error:
        raise YouTubeSearchError(f"YouTube video lookup failed: {error}") from error

    items = response.get("items", [])
    if not items:
        return None

    return _video_from_video_item(items[0])


def search_videos(
    api_key: str,
    query: str,
    max_results: int = 25,
) -> list[dict[str, str]]:
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
        )
        response = request.execute()
    except GoogleApiError as error:
        raise YouTubeSearchError(f"YouTube search failed: {error}") from error

    return [_video_from_search_item(item) for item in response["items"]]


def resolve_videos(
    api_key: str, query: str, max_results: int = 25
) -> list[dict[str, str]]:
    video_id = extract_video_id(query)
    if video_id:
        video = get_video(api_key, video_id)
        return [video] if video else []

    return search_videos(api_key, query, max_results=max_results)
