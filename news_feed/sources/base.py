"""Base interface for article sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseSource(ABC):
    """Abstract base class for all article sources."""

    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch articles from the source.

        Returns:
            List of article dictionaries with at least 'title' and 'url' fields.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the source is reachable and healthy.

        Returns:
            True if healthy, False otherwise.
        """
        pass
