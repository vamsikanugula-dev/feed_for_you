"""Base interface for article hydrators."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseHydrator(ABC):
    """Abstract base class for article hydrators that enrich article data."""

    @abstractmethod
    async def hydrate(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich an article with additional data.

        Args:
            article: Article dictionary to enrich.

        Returns:
            Enriched article dictionary with additional fields.
        """
        pass
