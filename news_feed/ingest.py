"""Ingest articles into the database."""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class IngestStore:
    """SQLite-based article store for development."""

    def __init__(self, db_path: str = ':memory:'):
        """Initialize the store.

        Args:
            db_path: Path to SQLite database file, or ':memory:' for in-memory DB
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Connect to the database and create tables if needed."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._run_migrations()

    def _run_migrations(self):
        """Run database migrations."""
        migrations_path = Path(__file__).parent.parent / 'migrations' / '001_init.sql'
        if migrations_path.exists():
            schema = migrations_path.read_text()
            self.conn.executescript(schema)
        else:
            # Inline minimal schema
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, feed_url TEXT, quality REAL DEFAULT 0.5
                );
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE, title TEXT, snippet TEXT,
                    source_id INTEGER, published_at TEXT,
                    summary TEXT, tags TEXT, cluster_id INTEGER,
                    popularity REAL DEFAULT 0, ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _get_or_create_source(self, source_name: str, quality: float = 0.5) -> int:
        """Get existing source ID or create a new one."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM sources WHERE name = ?', (source_name,))
        row = cursor.fetchone()
        if row:
            return row['id']

        cursor.execute(
            'INSERT INTO sources (name, quality) VALUES (?, ?)',
            (source_name, quality)
        )
        self.conn.commit()
        return cursor.lastrowid

    def ingest(self, articles: List[Dict[str, Any]]) -> int:
        """Ingest a list of articles.

        Args:
            articles: List of article dicts with url, title, snippet, etc.

        Returns:
            Number of new articles inserted
        """
        if not self.conn:
            self.connect()

        inserted = 0
        for article in articles:
            try:
                source_id = self._get_or_create_source(
                    article.get('source_name', 'unknown'),
                    article.get('source_quality', 0.5)
                )

                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO articles
                    (url, title, snippet, source_id, published_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article.get('url', ''),
                    article.get('title', ''),
                    article.get('snippet', ''),
                    source_id,
                    article.get('published_at', ''),
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except sqlite3.IntegrityError:
                # URL already exists, skip
                pass

        self.conn.commit()
        return inserted

    def get_all_articles(self) -> List[Dict[str, Any]]:
        """Retrieve all articles from the store."""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, s.name as source_name
            FROM articles a
            LEFT JOIN sources s ON a.source_id = s.id
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_article_count(self) -> int:
        """Get total article count."""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM articles')
        return cursor.fetchone()[0]


async def ingest_articles(articles: List[Dict[str, Any]], db_path: str = ':memory:') -> int:
    """Convenience function to ingest articles.

    Args:
        articles: List of article dicts to ingest
        db_path: Database path (in-memory by default)

    Returns:
        Number of new articles inserted
    """
    store = IngestStore(db_path)
    count = store.ingest(articles)
    store.close()
    return count
