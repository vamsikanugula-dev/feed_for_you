# PROGRESS

## Goal (verbatim)
Build a For You style tech-news feed for about 100 users, inspired by X's open-source For You pipeline: ingest -> hydrate -> filter -> score -> diversify -> blend. See DESIGN.md for the stage li

## Done (with evidence)
- Claude Code runs on GLM 5 via LiteLLM on Bedrock (/context shows CLAUDE.md and PROGRESS.md loaded)
- Project skeleton created (news_feed/ with sources, hydrators, filters, scorers, selectors - tests/test_imports.py passes)
- Stage 2 (ingest) implemented: migrations/001_init.sql (SQLite schema), news_feed/sources/rss_source.py (RSS/Atom parsing), news_feed/ingest.py (IngestStore), config/feeds.yaml (5 feeds) - tests/test_rss_and_ingest.py passes (10 tests)
- Stage 3 (hydrate + filters) implemented: news_feed/hydrators/summary_hydrator.py (HTML summary extraction), news_feed/filters/age_filter.py (48-hour default), news_feed/filters/seen_filter.py (user-seen tracking), news_feed/filters/duplicate_filter.py (batch-level URL dedup) - tests/test_hydrate_and_filter.py passes (20 tests)

## In progress
- (none)

## Decisions (and why)
- Python + FastAPI + Postgres/pgvector: small scale, ML-friendly
- Ingest articles in the background, rank from our own database
- GLM 5 for large tasks, GLM 4.7 Flash (haiku tier) for small tasks
- Link out to articles and store only titles, snippets and our own summaries
- Sources to start: Hacker News API plus RSS feeds
- Embeddings: local bge-small (384 dims), added in a later stage

## Failed approaches (do NOT retry)
- (none yet)

## Next step
- Build stage 4 (score): implement relevance scoring for articles
-