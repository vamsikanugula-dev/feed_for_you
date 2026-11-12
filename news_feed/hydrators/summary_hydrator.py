"""Summary hydrator that fetches and extracts article content."""
import re
from typing import Dict, Any, Optional
from .base import BaseHydrator


class SummaryHydrator(BaseHydrator):
    """Fetch article content and extract a summary.

    In production, this would:
    1. HTTP GET the article URL
    2. Parse HTML to extract main text
    3. Use LLM to generate summary

    For development, accepts pre-fetched content via article['_html'].
    """

    def __init__(self, max_summary_length: int = 200):
        """Initialize the hydrator.

        Args:
            max_summary_length: Maximum characters for extracted summary
        """
        self.max_summary_length = max_summary_length

    async def hydrate(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich article with summary.

        Args:
            article: Article dict with 'url' and optional '_html' for testing

        Returns:
            Article with 'summary' field added
        """
        # Skip if already has summary
        if article.get('summary'):
            return article

        # In production, would fetch URL here
        # For now, use pre-fetched content from tests
        html = article.get('_html', '')
        if html:
            summary = self._extract_summary_from_html(html)
        else:
            # Use snippet as fallback
            summary = article.get('snippet', '')[:self.max_summary_length]

        article['summary'] = summary
        return article

    def _extract_summary_from_html(self, html: str) -> str:
        """Extract plain text summary from HTML.

        Simple extraction: strip tags, get first paragraph-like content.
        For production, use newspaper3k or Trafilatura.
        """
        # Strip HTML tags (simple version)
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)

        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Get first N chars
        if len(text) > self.max_summary_length:
            text = text[:self.max_summary_length].rsplit(' ', 1)[0] + '...'

        return text

    def _is_html(self, content: str) -> bool:
        """Check if content looks like HTML."""
        return '<' in content and '>' in content
