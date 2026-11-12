# PROGRESS

## Goal (verbatim)
Build a For You style tech-news feed for about 100 users, inspired by X's open-source For You pipeline: ingest -> hydrate -> filter -> score -> diversify -> blend. See DESIGN.md for the stage list.

## Done (with evidence)
- Claude Code runs on GLM 5 via LiteLLM on Bedrock (/context shows CLAUDE.md and PROGRESS.md loaded)
- Project skeleton created (news_feed/ with sources, hydrators, filters, scorers, selectors - tests/test_imports.py passes)

## In progress
- (none)

## Decisions (and why)
- Python + FastAPI + Postgres/pgvector: small scale, ML-friendly
- Ingest articles in the background, rank from our own database
- GLM 5 for large tasks, GLM 4.7 Flash (haiku tier) for small tasks
- Link out to articles and store only titles, snippets and our own summaries

## Failed approaches (do NOT retry)
- (none yet)

## Next step
- Decide on news sources and embedding model (answer open questions)

## Open questions
- Which news sources to start with?
- Which embedding model: local bge-small or an API
-