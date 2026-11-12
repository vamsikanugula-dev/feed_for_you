"""RSS feed source implementation."""
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List
from .base import BaseSource


class RSSSource(BaseSource):
    """Fetch articles from an RSS/Atom feed."""

    def __init__(self, name: str, feed_url: str, quality: float = 0.5):
        """Initialize RSS source.

        Args:
            name: Human-readable source name
            feed_url: URL of the RSS/Atom feed
            quality: Quality score for this source (0.0-1.0)
        """
        self.name = name
        self.feed_url = feed_url
        self.quality = quality

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed.
        Use sample data for tests; in production this would HTTP GET the feed.

        Returns:
            List of article dicts with title, url, snippet, published_at, source_name
        """
        # This method should be patched in tests to return sample data
        # For now, return empty list as placeholder
        return []

    def parse_feed(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse RSS/Atom XML content into article dicts.

        Args:
            xml_content: Raw XML string from RSS/Atom feed

        Returns:
            List of article dicts
        """
        articles = []
        root = ET.fromstring(xml_content)

        # Detect RSS vs Atom
        if root.tag == 'rss':
            items = root.findall('.//item')
            for item in items:
                article = self._parse_rss_item(item)
                if article:
                    articles.append(article)
        elif root.tag in ('feed', '{http://www.w3.org/2005/Atom}feed'):
            entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            for entry in entries:
                article = self._parse_atom_entry(entry)
                if article:
                    articles.append(article)

        return articles

    def _parse_rss_item(self, item) -> Dict[str, Any]:
        """Parse a single RSS <item> element."""
        title = item.findtext('title', '')
        url = item.findtext('link', '')
        snippet = item.findtext('description', '')
        pub_date = item.findtext('pubDate', '')

        if not url:
            return None

        return {
            'url': url,
            'title': title,
            'snippet': snippet,
            'published_at': self._parse_date(pub_date),
            'source_name': self.name,
            'source_quality': self.quality,
        }

    def _parse_atom_entry(self, entry) -> Dict[str, Any]:
        """Parse a single Atom <entry> element."""
        ns = '{http://www.w3.org/2005/Atom}'
        title = entry.findtext(f'{ns}title', '')
        link_elem = entry.find(f'{ns}link')
        url = link_elem.get('href', '') if link_elem is not None else ''
        snippet_elem = entry.find(f'{ns}summary')
        if snippet_elem is None:
            snippet_elem = entry.find(f'{ns}content')
        snippet = snippet_elem.text if snippet_elem is not None else ''
        pub_date = entry.findtext(f'{ns}published', '') or entry.findtext(f'{ns}updated', '')

        if not url:
            return None

        return {
            'url': url,
            'title': title,
            'snippet': snippet,
            'published_at': self._parse_date(pub_date),
            'source_name': self.name,
            'source_quality': self.quality,
        }

    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to ISO 8601 string."""
        if not date_str:
            return ''
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        return date_str  # Return as-is if parsing fails

    async def health_check(self) -> bool:
        """Check if the feed URL is valid."""
        return self.feed_url.startswith('http')
