"""Base interface for article scorers."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseScorer(ABC):
    """Abstract base class for article scorers that rank articles."""

    @abstractmethod
    async def score(self, article: Dict[str, Any]) -> float:
        """Calculate a relevance score for an article.

        Args:
            article: Article dictionary to score.

        Returns:
            Float score value (higher is better).
        """
        pass
