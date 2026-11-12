"""Filter to drop duplicate articles by URL."""
from typing import Dict, Any, Set
from .base import BaseFilter


class DuplicateFilter(BaseFilter):
    """Drop articles with duplicate URLs within a batch.

    Tracks URLs seen in current processing batch. For cross-batch
    deduplication, the database UNIQUE constraint on articles.url
    handles it at ingest time.
    """

    def __init__(self):
        """Initialize the filter."""
        self._seen_urls: Set[str] = set()

    def reset(self):
        """Reset seen URLs for a new batch."""
        self._seen_urls.clear()

    async def should_keep(self, article: Dict[str, Any]) -> bool:
        """Check if article URL is unique in this batch.

        Args:
            article: Article dict with 'url' field

        Returns:
            True if article URL hasn't been seen in this batch
        """
        url = article.get('url')
        if not url:
            # No URL, filter it out
            return False

        if url in self._seen_urls:
            return False

        self._seen_urls.add(url)
        return True
