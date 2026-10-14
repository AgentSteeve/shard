"""Query the FTS5 index. Search by email, prefix, domain."""

from shard.config import DEFAULT_LIMIT, MAX_LIMIT
from shard.db import connect


def search_email(query: str, limit: int = DEFAULT_LIMIT, exact: bool = False) -> list[dict]:
    """Search emails. exact=False uses FTS5 prefix match."""
    limit = min(max(1, limit), MAX_LIMIT)
    conn = connect()
    try:
        cur = conn.cursor()
        if exact:
            cur.execute(
                """SELECT e.email, e.domain, c.password, c.source, c.ingested_at
                   FROM emails e
                   JOIN credentials c ON c.email_id = e.id
                   WHERE e.email = ?
                   ORDER BY c.ingested_at DESC
                   LIMIT ?""",
                (query.strip().lower(), limit),
            )
        else:
            fts_query = " ".join(f"{tok}*" for tok in query.strip().lower().split())
            cur.execute(
                """SELECT e.email, e.domain, c.password, c.source, c.ingested_at
                   FROM emails_fts fts
                   JOIN emails e ON e.id = fts.rowid
                   JOIN credentials c ON c.email_id = e.id
                   WHERE emails_fts MATCH ?
                   ORDER BY c.ingested_at DESC
                   LIMIT ?""",
                (fts_query, limit),
            )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def search_domain(domain: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """List all emails under a domain."""
    limit = min(max(1, limit), MAX_LIMIT)
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT e.email, e.domain, c.password, c.source
               FROM emails e
               JOIN credentials c ON c.email_id = e.id
               WHERE e.domain = ?
               ORDER BY e.email
               LIMIT ?""",
            (domain.strip().lower(), limit),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def stats() -> dict:
    """Return counts for the UI header."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM emails")
        emails = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM credentials")
        creds = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sources")
        sources = cur.fetchone()[0]
        return {"emails": emails, "credentials": creds, "sources": sources}
    finally:
        conn.close()


def export_csv(rows: list[dict]) -> str:
    """Render results as CSV text."""
    if not rows:
        return "email,password,source\n"
    lines = ["email,password,source"]
    for r in rows:
        email = (r.get("email") or "").replace(",", "\\,")
        pwd = (r.get("password") or "").replace(",", "\\,").replace("\n", " ")
        src = (r.get("source") or "").replace(",", "\\,")
        lines.append(f"{email},{pwd},{src}")
    return "\n".join(lines) + "\n"
