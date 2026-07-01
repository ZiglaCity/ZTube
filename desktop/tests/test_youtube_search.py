from desktop.ztube_desktop.services import youtube_search
from desktop.ztube_desktop.services.youtube_search import extract_video_id


def test_extract_video_id_from_watch_url():
    assert (
        extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    )


def test_extract_video_id_from_short_url():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ?si=test") == "dQw4w9WgXcQ"


def test_extract_video_id_from_shorts_url():
    assert (
        extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    )


def test_extract_video_id_from_raw_id():
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_returns_none_for_search_text():
    assert extract_video_id("hello world") is None


def test_search_videos_uses_youtube_api(monkeypatch):
    class FakeRequest:
        def execute(self):
            return {
                "items": [
                    {
                        "snippet": {
                            "title": "Tom &amp; Jerry",
                            "thumbnails": {
                                "default": {"url": "https://thumb.test/a.jpg"}
                            },
                        },
                        "id": {"videoId": "dQw4w9WgXcQ"},
                    }
                ]
            }

    class FakeSearchResource:
        def list(self, q: str, part: str, type: str, maxResults: int):
            assert q == "cartoon"
            assert part == "snippet"
            assert type == "video"
            assert maxResults == 25
            return FakeRequest()

    class FakeYouTube:
        def search(self):
            return FakeSearchResource()

    def fake_build(service: str, version: str, developerKey: str):
        assert service == "youtube"
        assert version == "v3"
        assert developerKey == "api-key"
        return FakeYouTube()

    monkeypatch.setattr(youtube_search, "build", fake_build)

    assert youtube_search.search_videos("api-key", "cartoon") == [
        {
            "title": "Tom & Jerry",
            "videoId": "dQw4w9WgXcQ",
            "thumbnail": "https://thumb.test/a.jpg",
        }
    ]
