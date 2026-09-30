"""Tests for the helper functions in ``app_quiz.utils``."""

from django.test import SimpleTestCase

from app_quiz.utils import normalize_youtube_url

STANDARD_URL = "https://www.youtube.com/watch?v=vu3xGr-lNVI"


class NormalizeYoutubeUrlTests(SimpleTestCase):
    """Convert YouTube video URLs to the standard form."""

    def test_normalize_returns_standard_url_for_video_urls(self):
        video_urls = (
            "https://www.youtube.com/watch?v=vu3xGr-lNVI",
            "https://youtube.com/watch?v=vu3xGr-lNVI&t=42s",
            "https://m.youtube.com/watch?v=vu3xGr-lNVI",
            "https://www.youtube.com/watch?v=vu3xGr-lNVI&list=PL123&index=2",
            "https://youtu.be/vu3xGr-lNVI",
            "https://youtu.be/vu3xGr-lNVI?si=abc",
            "https://www.youtube.com/shorts/vu3xGr-lNVI",
            "https://www.youtube.com/embed/vu3xGr-lNVI",
            "https://www.youtube.com/live/vu3xGr-lNVI",
        )

        for video_url in video_urls:
            with self.subTest(video_url=video_url):
                self.assertEqual(normalize_youtube_url(video_url), STANDARD_URL)

    def test_normalize_returns_none_for_other_urls(self):
        other_urls = (
            "https://example.com/watch?v=vu3xGr-lNVI",
            "https://www.youtube.com/",
            "https://www.youtube.com/watch?v=short",
            "https://www.youtube.com/watch",
            "https://youtu.be/",
            "https://www.youtube.com/playlist?list=PL123",
            "https://www.youtube.com/channel/UC1234567890",
            "not-a-url",
        )

        for other_url in other_urls:
            with self.subTest(other_url=other_url):
                self.assertIsNone(normalize_youtube_url(other_url))
