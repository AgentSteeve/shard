"""Ingest raw dumps from a directory into the SQLite index."""

import sqlite3
from pathlib import Path
from typing import Iterator

from tqdm import tqdm

from shard.config import BATCH_SIZE
from shard.db import connect, init
from shard.normalize import hash_str, normalize, split_pair

SUPPORTED_EXT = {".txt", ".csv", ".tsv", ".lst", ".dat", ".log"}


def iter_files(root: Path) -> Iterator[Path]:
    """Yield all supported dump files under root."""
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXT:
            yield p


def iter_lines(path: Path) -> Iterator[str]:
    """Yield stripped lines, tolerant to encodings."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line
    except (OSError, UnicodeError):
        return


def insert_batch(conn: sqlite3.Connection, batch: list) -> int:
    """Insert a batch of credential rows."""
    cur = conn.cursor()
    inserted = 0
    for email, domain, email_hash, password, source, raw in batch:
        try:
            cur.execute(
                "INSERT OR IGNORE INTO emails (email, domain, email_hash) VALUES (?, ?, ?)",
                (email, domain, email_hash),
            )
            cur.execute("SELECT id FROM emails WHERE email_hash = ?", (email_hash,))
            row = cur.fetchone()
            if row is None:
                continue
            email_id = row[0]
            pwd_hash = hash_str(password) if password else None
            cur.execute(
                "INSERT INTO credentials (email_id, password, password_hash, source, raw_line) VALUES (?, ?, ?, ?, ?)",
                (email_id, password, pwd_hash, source, raw),
            )
            inserted += 1
        except sqlite3.Error:
            continue
    conn.commit()
    return inserted


def register_source(conn: sqlite3.Connection, name: str, path: str, count: int) -> None:
    conn.execute(
        """INSERT INTO sources (name, path, line_count)
           VALUES (?, ?, ?)
           ON CONFLICT(name) DO UPDATE SET
             line_count = line_count + excluded.line_count,
             ingested_at = strftime('%s','now')""",
        (name, path, count),
    )
    conn.commit()


def ingest_file(conn: sqlite3.Connection, path: Path, show_progress: bool = True) -> int:
    """Ingest one file. Returns number of credential rows inserted."""
    source = path.name
    total_lines = 0
    inserted = 0
    batch = []

    iterator = iter_lines(path)
    if show_progress:
        iterator = tqdm(iterator, desc=source, unit=" lines")

    for line in iterator:
        total_lines += 1
        email, password = split_pair(line)
        if not email:
            continue
        email, domain, email_hash = normalize(email)
        batch.append((email, domain, email_hash, password, source, line))
        if len(batch) >= BATCH_SIZE:
            inserted += insert_batch(conn, batch)
            batch.clear()

    if batch:
        inserted += insert_batch(conn, batch)

    register_source(conn, source, str(path), total_lines)
    return inserted


def ingest_dir(root: Path, show_progress: bool = True) -> tuple[int, int]:
    """Ingest every supported file under root. Returns (files, rows)."""
    init()
    conn = connect()
    files = 0
    rows = 0
    try:
        for path in iter_files(root):
            files += 1
            rows += ingest_file(conn, path, show_progress)
    finally:
        conn.close()
    return files, rows
