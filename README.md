# shard

Self-hosted breach search engine. Ingest raw dumps, normalize, index, search — all local, no external service, no signup.

## What it does

- Parses multiple dump formats: `email:password`, CSV, TSV, SQLite, JSON lines
- Normalizes and deduplicates by SHA-256
- Indexes into SQLite with FTS5 (full-text search, typo-tolerant via prefix queries)
- Serves a web UI on `localhost:8000`
- Searches by email, partial email, domain
- Exports results as CSV

## Stack

- Python 3.11
- SQLite + FTS5
- FastAPI + Jinja2
- Docker Compose

## Quick start

### 1. Clone

git clone https://github.com/AgentSteeve/shard.git
cd shard

### 2. Put your dumps in `data/`

Supported: `.txt`, `.csv`, `.tsv`, `.sqlite`, `.jsonl`
Formats auto-detected per line.

### 3. Run

docker compose up --build

Open http://localhost:8000

### 4. Ingest

docker compose exec shard python -m shard.cli ingest /app/data

### 5. Search

Use the web UI, or the CLI:

docker compose exec shard python -m shard.cli search user@example.com

## Layout

shard/          # core: db, ingest, normalize, search
api/            # FastAPI + web UI
data/           # your dumps go here (gitignored except .gitkeep)
scripts/        # helper scripts

## Legal

You are responsible for what you ingest. Do not ingest data you are not authorized to hold.
