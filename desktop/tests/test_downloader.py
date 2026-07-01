from pathlib import Path

import pytest

from desktop.ztube_desktop.services.downloader import (
    format_quality_option,
    get_quality_options,
    validate_output_path,
)


class DummyStream:
    resolution = "720p"
    filesize = 52 * 1024 * 1024


class MissingMetadataStream:
    resolution = None
    filesize = None


def test_format_quality_option_includes_resolution_and_size():
    assert format_quality_option(DummyStream()) == "MP4 video - 720p - 52 MB"


def test_format_quality_option_handles_missing_metadata():
    assert (
        format_quality_option(MissingMetadataStream()) == "MP4 video - unknown - 0 MB"
    )


def test_validate_output_path_accepts_existing_directory():
    assert validate_output_path(Path.cwd()) == Path.cwd()


def test_validate_output_path_rejects_missing_directory():
    missing_path = Path.cwd() / "__ztube_missing_download_dir__"

    with pytest.raises(ValueError, match="Download folder does not exist"):
        validate_output_path(missing_path)


def test_get_quality_options_uses_pytubefix_streams(monkeypatch):
    class FakeStreamQuery:
        def filter(self, progressive: bool, file_extension: str):
            assert progressive is True
            assert file_extension == "mp4"
            return [DummyStream()]

    class FakeYouTube:
        def __init__(self, url: str, client: str):
            assert url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            assert client
            self.streams = FakeStreamQuery()

    monkeypatch.setattr(
        "desktop.ztube_desktop.services.downloader.YouTube",
        FakeYouTube,
    )

    assert get_quality_options("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == [
        "MP4 video - 720p - 52 MB"
    ]
