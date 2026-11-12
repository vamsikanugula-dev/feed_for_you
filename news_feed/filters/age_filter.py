"""Age filter to drop old articles."""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from .base import BaseFilter


class AgeFilter(BaseFilter):
    """Drop articles older than a maximum age.

    Default: 48 hours from published_at or ingested_at.
    """

    def __init__(self, max_age_hours: int = 48):
        """Initialize the filter.

        Args:
            max_age_hours: Maximum age in hours before article is dropped
        """
        self.max_age = timedelta(hours=max_age_hours)

    async def should_keep(self, article: Dict[str, Any]) -> bool:
        """Check if article is within age limit.

        Args:
            article: Article dict with 'published_at' or 'ingested_at'

        Returns:
            True if article is recent enough to keep
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Try published_at first
        date_str = article.get('published_at') or article.get('ingested_at')
        if not date_str:
            # No date, keep it (or could filter out)
            return True

        # Parse ISO 8601 date
        try:
            # Handle both with and without timezone
            date_str = date_str.replace('Z', '+00:00')
            if '+' in date_str or date_str.endswith('Z'):
                pub_date = datetime.fromisoformat(date_str.replace('+00:00', ''))
            else:
                pub_date = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            # Can't parse date, keep article
            return True

        age = now - pub_date
        return age <= self.max_age
