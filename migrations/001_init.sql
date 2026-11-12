-- Initial schema (SQLite version for development)
-- For production PostgreSQL, add: CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    feed_url TEXT,
    quality REAL DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    snippet TEXT,
    source_id INTEGER REFERENCES sources(id),
    published_at TEXT,  -- ISO 8601 timestamp string
    summary TEXT,
    tags TEXT,  -- JSON array or comma-separated
    cluster_id INTEGER,
    popularity REAL DEFAULT 0,
    -- embedding BLOB,  -- todo: add when embeddings stage is built
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    interest_vec TEXT  -- JSON array, later: vector(384)
);

CREATE TABLE IF NOT EXISTS user_topics (
    user_id INTEGER,
    topic TEXT
);

CREATE TABLE IF NOT EXISTS user_hidden (
    user_id INTEGER,
    kind TEXT,  -- 'topic' or 'source'
    value TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    article_id INTEGER,
    kind TEXT,  -- 'impression', 'click', 'dwell', 'save', 'hide', 'not_interested'
    value REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_article ON events(article_id);
