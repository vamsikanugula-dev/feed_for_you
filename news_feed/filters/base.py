"""Base interface for article filters."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseFilter(ABC):
    """Abstract base class for article filters."""

    @abstractmethod
    async def should_keep(self, article: Dict[str, Any]) -> bool:
        """Determine if an article should pass through the filter.

        Args:
            article: Article dictionary to evaluate.

        Returns:
            True if the article should be kept, False to filter it out.
        """
        pass
