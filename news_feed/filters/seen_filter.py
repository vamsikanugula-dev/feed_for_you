"""Filter to drop articles already seen by a user."""
from typing import Dict, Any, Set
from .base import BaseFilter


class SeenFilter(BaseFilter):
    """Drop articles that a user has already seen.

    Tracks seen article IDs per user. In production, this would
    query the database events table.
    """

    def __init__(self, seen_ids: Set[int] = None):
        """Initialize the filter.

        Args:
            seen_ids: Set of article IDs already seen by the user
        """
        self.seen_ids = seen_ids or set()

    def set_seen_ids(self, seen_ids: Set[int]):
        """Update the set of seen article IDs."""
        self.seen_ids = seen_ids

    async def should_keep(self, article: Dict[str, Any]) -> bool:
        """Check if article has not been seen.

        Args:
            article: Article dict with 'id' field

        Returns:
            True if article has not been seen by this user
        """
        article_id = article.get('id')
        if article_id is None:
            # No ID, can't check, keep it
            return True

        return article_id not in self.seen_ids
