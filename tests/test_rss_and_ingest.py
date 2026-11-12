"""Tests for RSS source and article ingestion."""
import pytest
import tempfile
import os
from news_feed.sources.rss_source import RSSSource
from news_feed.ingest import IngestStore, ingest_articles


# Sample RSS feed (Hacker News style)
SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Hacker News</title>
    <link>https://news.ycombinator.com/</link>
    <item>
      <title>Show HN: I built a news feed ranking engine</title>
      <link>https://github.com/example/news-feed</link>
      <description>A For You style ranking pipeline in Python</description>
      <pubDate>Tue, 11 Nov 2025 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>PostgreSQL 17 Released</title>
      <link>https://www.postgresql.org/about/news/postgresql-17-released-1234/</link>
      <description>New version with improved performance and vector search</description>
      <pubDate>Tue, 11 Nov 2025 09:30:00 +0000</pubDate>
    </item>
    <item>
      <title>Understanding Rust async</title>
      <link>https://blog.example.com/rust-async</link>
      <description>Deep dive into async/await in Rust</description>
      <pubDate>Mon, 10 Nov 2025 15:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""

# Sample Atom feed (The Verge style)
SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>The Verge</title>
  <link href="https://www.theverge.com/"/>
  <entry>
    <title>Apple announces new M4 chip</title>
    <link href="https://www.theverge.com/apple-m4"/>
    <summary>New chip delivers 2x performance per watt</summary>
    <published>2025-11-11T08:00:00Z</published>
  </entry>
  <entry>
    <title>OpenAI releases GPT-5</title>
    <link href="https://www.theverge.com/openai-gpt5"/>
    <summary>The new model shows improved reasoning</summary>
    <published>2025-11-10T14:00:00Z</published>
  </entry>
</feed>
"""


class TestRSSSource:
    """Test RSS/Atom feed parsing."""

    def test_parse_rss_feed(self):
        """RSS <item> parsing should extract title, url, snippet."""
        source = RSSSource(name="Test RSS", feed_url="https://example.com/feed.rss")
        articles = source.parse_feed(SAMPLE_RSS)

        assert len(articles) == 3
        assert articles[0]['title'] == "Show HN: I built a news feed ranking engine"
        assert articles[0]['url'] == "https://github.com/example/news-feed"
        assert articles[0]['snippet'] == "A For You style ranking pipeline in Python"
        assert articles[0]['source_name'] == "Test RSS"

    def test_parse_atom_feed(self):
        """Atom <entry> parsing should extract title, url, snippet."""
        source = RSSSource(name="Test Atom", feed_url="https://example.com/atom.xml")
        articles = source.parse_feed(SAMPLE_ATOM)

        assert len(articles) == 2
        assert articles[0]['title'] == "Apple announces new M4 chip"
        assert articles[0]['url'] == "https://www.theverge.com/apple-m4"

    def test_date_parsing(self):
        """Dates should be normalized to ISO 8601."""
        source = RSSSource(name="Test", feed_url="https://example.com/feed")
        articles = source.parse_feed(SAMPLE_RSS)

        # Should be ISO format
        assert '2025' in articles[0]['published_at']

    async def test_health_check(self):
        """Health check should validate URL."""
        source = RSSSource(name="Test", feed_url="https://example.com/feed")
        assert await source.health_check() is True

    def test_empty_fetch(self):
        """Fetch should return empty list by default (patched in tests)."""
        source = RSSSource(name="Test", feed_url="https://example.com/feed")
        import asyncio
        articles = asyncio.run(source.fetch())
        assert articles == []


class TestIngestStore:
    """Test article storage."""

    def test_ingest_articles(self):
        """Ingesting articles should store them in the database."""
        store = IngestStore(':memory:')
        store.connect()

        articles = [
            {'url': 'https://example.com/1', 'title': 'Article 1', 'snippet': 'Test'},
            {'url': 'https://example.com/2', 'title': 'Article 2', 'snippet': 'Test'},
        ]

        count = store.ingest(articles)
        assert count == 2
        assert store.get_article_count() == 2

        store.close()

    def test_duplicate_articles(self):
        """Ingesting duplicate URLs should skip them."""
        store = IngestStore(':memory:')
        store.connect()

        articles = [
            {'url': 'https://example.com/1', 'title': 'Article 1'},
        ]
        store.ingest(articles)
        count = store.ingest(articles)  # Same URL

        assert count == 0  # No new insert
        store.close()

    def test_source_creation(self):
        """Articles should create sources automatically."""
        store = IngestStore(':memory:')
        store.connect()

        articles = [
            {'url': 'https://example.com/1', 'title': 'Test',
             'source_name': 'Hacker News', 'source_quality': 0.8},
        ]
        store.ingest(articles)

        all_articles = store.get_all_articles()
        assert all_articles[0]['source_name'] == 'Hacker News'

        store.close()

    def test_async_ingest_function(self):
        """Convenience async function should work."""
        import asyncio

        articles = [
            {'url': 'https://example.com/1', 'title': 'Test'},
        ]

        count = asyncio.run(ingest_articles(articles))
        assert count == 1


class TestIntegration:
    """Integration: parse RSS and ingest."""

    def test_parse_and_ingest(self):
        """Parse RSS and ingest into SQLite."""
        # Parse RSS
        source = RSSSource(name="HN", feed_url="https://hnrss.org/frontpage", quality=0.8)
        articles = source.parse_feed(SAMPLE_RSS)

        # Ingest
        store = IngestStore(':memory:')
        store.connect()
        count = store.ingest(articles)

        assert count == 3
        assert store.get_article_count() == 3

        # Verify content
        all_articles = store.get_all_articles()
        titles = [a['title'] for a in all_articles]
        assert "PostgreSQL 17 Released" in titles

        store.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
