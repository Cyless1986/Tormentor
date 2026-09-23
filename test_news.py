import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import news


class NewsFeedTest(unittest.TestCase):
    def test_only_public_metadata_is_extracted_and_unsafe_links_rejected(self):
        raw = b'''<rss><channel><item><title>A new adventure</title><link>http://www.dndbeyond.com/posts/2244-example</link><pubDate>Fri, 11 Sep 2026 21:22:03 GMT</pubDate><description>FULL ARTICLE MUST NOT BE COPIED</description></item><item><title>Unsafe link</title><link>javascript:alert(1)</link><pubDate>Fri, 11 Sep 2026 21:22:03 GMT</pubDate></item></channel></rss>'''
        entries = news.parse_feed(raw, "D&D Beyond", "news")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["url"], "https://www.dndbeyond.com/posts/2244-example")
        self.assertNotIn("FULL ARTICLE", json.dumps(entries))
        with self.assertRaises(ValueError):
            news.parse_feed(b'<!DOCTYPE rss><rss/>', "D&D Beyond", "news")

    def test_videos_are_interleaved_and_load_only_after_click(self):
        entries = [{"kind": "news", "published": str(i), "title": "Article", "url": "https://www.dndbeyond.com/posts/2244-example", "source": "D&D Beyond"} for i in range(5)]
        entries += [{"kind": "video", "published": "2026-09-10T12:00:00+00:00", "video_id": "gb10T_B-skU", "title": "Video", "url": "https://www.youtube.com/watch?v=gb10T_B-skU", "source": "Dungeons & Dragons"}]
        self.assertEqual(news.mixed_entries(entries)[2]["kind"], "video")
        self.assertTrue(all(item["kind"] == "video" for item in news.mixed_entries(entries, "video")))
        with patch.object(news, "snapshot", return_value={"entries": entries, "updated_at": 0}), patch.dict(os.environ, {"TORMENTOR_NEWS_OFFLINE": "1"}):
            html = news.render_feed("video")
        self.assertIn('data-video="gb10T_B-skU"', html)
        self.assertNotIn("<iframe", html)
        self.assertIn("/media/feed.js", html)

    def test_unavailable_sources_preserve_last_snapshot(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(news, "CACHE", Path(directory) / "cache.json"), patch("urllib.request.urlopen", side_effect=OSError("offline")):
            before = news.snapshot()
            news.refresh()
            after = news.snapshot()
            self.assertEqual(len(after["entries"]), len(before["entries"]))
            self.assertEqual(after["updated_at"], before["updated_at"])
            self.assertEqual(len(after["errors"]), len(news.SOURCES))


if __name__ == "__main__":
    unittest.main()
