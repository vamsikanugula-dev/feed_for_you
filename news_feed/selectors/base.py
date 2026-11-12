"""Base interface for article selectors."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseSelector(ABC):
    """Abstract base class for selectors that diversify and blend article feeds."""

    @abstractmethod
    async def select(self, articles: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Select and diversify articles for the final feed.

        Args:
            articles: List of scored articles to select from.
            limit: Maximum number of articles to return.

        Returns:
            Diversified list of selected articles.
        """
        pass
