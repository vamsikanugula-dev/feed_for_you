"""Tests for Stage 3: hydrators and filters."""
import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from news_feed.hydrators.summary_hydrator import SummaryHydrator
from news_feed.filters.age_filter import AgeFilter
from news_feed.filters.seen_filter import SeenFilter
from news_feed.filters.duplicate_filter import DuplicateFilter


# ===== SummaryHydrator Tests =====

class TestSummaryHydrator:
    """Test the summary hydrator."""

    @pytest.mark.asyncio
    async def test_extract_summary_from_html(self):
        """Test extracting summary from HTML content."""
        hydrator = SummaryHydrator(max_summary_length=100)
        article = {
            'url': 'https://example.com/article',
            'snippet': 'A short snippet',
            '_html': '<html><body><p>This is the main article content that should be extracted as a summary for the reader.</p></body></html>'
        }
        result = await hydrator.hydrate(article)
        assert 'summary' in result
        assert 'main article content' in result['summary']

    @pytest.mark.asyncio
    async def test_strip_scripts_and_styles(self):
        """Test that scripts and styles are stripped."""
        hydrator = SummaryHydrator(max_summary_length=200)
        article = {
            'url': 'https://example.com/article',
            '_html': '<html><head><script>alert("xss")</script><style>.foo{}</style></head><body><p>Real content here.</p></body></html>'
        }
        result = await hydrator.hydrate(article)
        assert 'alert' not in result['summary']
        assert '.foo' not in result['summary']
        assert 'Real content here' in result['summary']

    @pytest.mark.asyncio
    async def test_uses_snippet_when_no_html(self):
        """Test fallback to snippet when no HTML provided."""
        hydrator = SummaryHydrator()
        article = {
            'url': 'https://example.com/article',
            'snippet': 'This is a snippet from the RSS feed.'
        }
        result = await hydrator.hydrate(article)
        assert result['summary'] == 'This is a snippet from the RSS feed.'

    @pytest.mark.asyncio
    async def test_skip_if_has_summary(self):
        """Test that existing summary is preserved."""
        hydrator = SummaryHydrator()
        article = {
            'url': 'https://example.com/article',
            'summary': 'Pre-existing summary'
        }
        result = await hydrator.hydrate(article)
        assert result['summary'] == 'Pre-existing summary'

    @pytest.mark.asyncio
    async def test_truncates_long_content(self):
        """Test that long content is truncated."""
        hydrator = SummaryHydrator(max_summary_length=50)
        long_text = 'a' * 100
        article = {
            'url': 'https://example.com/article',
            '_html': f'<p>{long_text}</p>'
        }
        result = await hydrator.hydrate(article)
        assert len(result['summary']) <= 53  # 50 + '...'
        assert result['summary'].endswith('...')


# ===== AgeFilter Tests =====

class TestAgeFilter:
    """Test the age filter."""

    @pytest.mark.asyncio
    async def test_keep_recent_article(self):
        """Test that recent articles are kept."""
        filter = AgeFilter(max_age_hours=48)
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        article = {'published_at': recent_date}
        assert await filter.should_keep(article) is True

    @pytest.mark.asyncio
    async def test_drop_old_article(self):
        """Test that old articles are dropped."""
        filter = AgeFilter(max_age_hours=48)
        old_date = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
        article = {'published_at': old_date}
        assert await filter.should_keep(article) is False

    @pytest.mark.asyncio
    async def test_keep_article_at_boundary(self):
        """Test article at exactly max age."""
        filter = AgeFilter(max_age_hours=48)
        boundary_date = (datetime.now(timezone.utc) - timedelta(hours=47)).isoformat()
        article = {'published_at': boundary_date}
        assert await filter.should_keep(article) is True

    @pytest.mark.asyncio
    async def test_keep_article_without_date(self):
        """Test that articles without date are kept."""
        filter = AgeFilter()
        article = {'url': 'https://example.com/article'}
        assert await filter.should_keep(article) is True

    @pytest.mark.asyncio
    async def test_uses_ingested_at_as_fallback(self):
        """Test that ingested_at is used if published_at missing."""
        filter = AgeFilter(max_age_hours=48)
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        article = {'ingested_at': recent_date}
        assert await filter.should_keep(article) is True


# ===== SeenFilter Tests =====

class TestSeenFilter:
    """Test the seen filter."""

    @pytest.mark.asyncio
    async def test_keep_unseen_article(self):
        """Test that unseen articles are kept."""
        filter = SeenFilter(seen_ids={1, 2, 3})
        article = {'id': 4}
        assert await filter.should_keep(article) is True

    @pytest.mark.asyncio
    async def test_drop_seen_article(self):
        """Test that seen articles are dropped."""
        filter = SeenFilter(seen_ids={1, 2, 3})
        article = {'id': 2}
        assert await filter.should_keep(article) is False

    @pytest.mark.asyncio
    async def test_keep_article_without_id(self):
        """Test that articles without ID are kept."""
        filter = SeenFilter(seen_ids={1, 2, 3})
        article = {'url': 'https://example.com/article'}
        assert await filter.should_keep(article) is True

    @pytest.mark.asyncio
    async def test_update_seen_ids(self):
        """Test updating seen IDs."""
        filter = SeenFilter(seen_ids={1})
        article = {'id': 2}
        assert await filter.should_keep(article) is True
        filter.set_seen_ids({1, 2})
        assert await filter.should_keep(article) is False


# ===== DuplicateFilter Tests =====

class TestDuplicateFilter:
    """Test the duplicate filter."""

    @pytest.mark.asyncio
    async def test_keep_first_occurrence(self):
        """Test that first URL occurrence is kept."""
        filter = DuplicateFilter()
        article = {'url': 'https://example.com/article'}
        assert await filter.should_keep(article) is True

    @pytest.mark.asyncio
    async def test_drop_duplicate_url(self):
        """Test that duplicate URLs are dropped."""
        filter = DuplicateFilter()
        article1 = {'url': 'https://example.com/article'}
        article2 = {'url': 'https://example.com/article'}
        assert await filter.should_keep(article1) is True
        assert await filter.should_keep(article2) is False

    @pytest.mark.asyncio
    async def test_drop_article_without_url(self):
        """Test that articles without URL are dropped."""
        filter = DuplicateFilter()
        article = {'title': 'No URL'}
        assert await filter.should_keep(article) is False

    @pytest.mark.asyncio
    async def test_reset_clears_seen_urls(self):
        """Test that reset clears seen URLs."""
        filter = DuplicateFilter()
        article1 = {'url': 'https://example.com/article'}
        article2 = {'url': 'https://example.com/article'}
        await filter.should_keep(article1)
        filter.reset()
        assert await filter.should_keep(article2) is True

    @pytest.mark.asyncio
    async def test_different_urls_both_kept(self):
        """Test that different URLs are both kept."""
        filter = DuplicateFilter()
        article1 = {'url': 'https://example.com/article1'}
        article2 = {'url': 'https://example.com/article2'}
        assert await filter.should_keep(article1) is True
        assert await filter.should_keep(article2) is True


# ===== Integration Test =====

class TestHydrateAndFilterPipeline:
    """Test the full hydrate + filter pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_processes_articles(self):
        """Test that pipeline hydrates and filters correctly."""
        hydrator = SummaryHydrator()
        age_filter = AgeFilter(max_age_hours=48)
        seen_filter = SeenFilter(seen_ids={100})
        duplicate_filter = DuplicateFilter()

        articles = [
            {
                'id': 1,
                'url': 'https://example.com/article1',
                'published_at': (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
                '_html': '<p>Content for article 1.</p>'
            },
            {
                'id': 2,
                'url': 'https://example.com/article2',
                'published_at': (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat(),
                '_html': '<p>Content for article 2.</p>'
            },
            {
                'id': 100,
                'url': 'https://example.com/article3',
                'published_at': datetime.now(timezone.utc).isoformat(),
                '_html': '<p>Content for article 3.</p>'
            },
        ]

        results = []
        for article in articles:
            # Hydrate
            article = await hydrator.hydrate(article)
            # Apply filters
            if not await age_filter.should_keep(article):
                continue
            if not await seen_filter.should_keep(article):
                continue
            if not await duplicate_filter.should_keep(article):
                continue
            results.append(article)

        # Only article 1 should pass all filters
        assert len(results) == 1
        assert results[0]['id'] == 1
        assert 'summary' in results[0]
