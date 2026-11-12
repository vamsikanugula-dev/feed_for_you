# DESIGN: For You style tech-news feed (about 100 users)

Inspired by X's open-source For You pipeline. Same stage shape, simpler tools.
Rule: articles are ingested in the background; ranking reads only our own database.

## Stages
| # | Stage | Job |
|---|---|---|
| 0 | Ingest (background, every 15-30 min) | Pull articles from RSS, Hacker News, arXiv, search APIs. Store title, url, snippet, source, published time. |
| 1 | Query hydration | Load user topics, interest vector, hidden topics/sources, read history, saved items. |
| 2 | Candidate sources | (a) user's chosen sources/topics (b) nearest to interest vector (c) trending clusters (d) global top stories |
| 3 | Candidate hydration | Add summary, tags, source quality, story cluster id. |
| 4 | Filters | Drop: older than 48h, duplicate stories, already seen, hidden topics/sources. |
| 5 | Scoring | score = w1*relevance + w2*freshness + w3*source_quality + w4*popularity + w5*cluster_size - penalties |
| 6 | Selection | Keep top K by score. |
| 7 | Diversity | MMR reorder + decaying penalty for repeated sources. |
| 8 | Blending | Reserve slots for global top stories and exploration topics. |
| 9 | Logging | Record impressions, clicks, dwell time, saves, hides, not-interested. |

## Stack
Python + FastAPI, PostgreSQL + pgvector, APScheduler (or cron) for ingest,
small embedding model (bge-small, 384 dims) or an embedding API, LLM for summaries/tags once per article at ingest.
Frontend later (Next.js PWA). Link out to articles; store only title, snippet, our own summary.

## Database tables (first version)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE sources (
  id SERIAL PRIMARY KEY, name TEXT, feed_url TEXT, quality REAL DEFAULT 0.5
);
CREATE TABLE articles (
  id SERIAL PRIMARY KEY, url TEXT UNIQUE, title TEXT, snippet TEXT,
  source_id INT REFERENCES sources(id), published_at TIMESTAMPTZ,
  summary TEXT, tags TEXT[], cluster_id INT, popularity REAL DEFAULT 0,
  embedding vector(384), ingested_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT UNIQUE, interest_vec vector(384));
CREATE TABLE user_topics (user_id INT, topic TEXT);
CREATE TABLE user_hidden (user_id INT, kind TEXT, value TEXT);  -- kind: topic or source
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY, user_id INT, article_id INT,
  kind TEXT,  -- impression, click, dwell, save, hide, not_interested
  value REAL, created_at TIMESTAMPTZ DEFAULT now()
);
```

## Interfaces (src/pipeline/base.py)
```python
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class Query:           # filled by query hydration
    user_id: int
    topics: list = field(default_factory=list)
    interest_vec: list | None = None
    hidden: dict = field(default_factory=dict)
    seen_ids: set = field(default_factory=set)

@dataclass
class Candidate:       # one article moving through the pipeline
    article_id: int
    origin: str = ""   # which source returned it
    data: dict = field(default_factory=dict)
    score: float = 0.0

class Source(ABC):
    @abstractmethod
    def fetch(self, q: Query) -> list[Candidate]: ...
class Hydrator(ABC):
    @abstractmethod
    def hydrate(self, q: Query, cands: list[Candidate]) -> list[Candidate]: ...
class Filter(ABC):
    @abstractmethod
    def keep(self, q: Query, c: Candidate) -> bool: ...
class Scorer(ABC):
    @abstractmethod
    def score(self, q: Query, cands: list[Candidate]) -> list[Candidate]: ...
class Selector(ABC):
    @abstractmethod
    def select(self, q: Query, cands: list[Candidate]) -> list[Candidate]: ...
```
Pipeline runner order: query hydration -> sources (parallel) -> dedupe -> hydrate -> filters -> scorers -> selector -> diversity -> blend -> log.

## Build order
1. Skeleton + interfaces + import test
2. One RSS source + DB tables + ingest job
3. Hydration + filters (age, seen, duplicate)
4. Scoring formula + top-K
5. Diversity (MMR) + blending
6. Event logging; later, learn weights from clicks

## Rules
- Each stage is a small class behind the interfaces above; stages must be swappable.
- Duplicate stories: cluster by url and embedding similarity, keep the best source.
- Log every impression and click from day one.
- Do not build stages out of order.