"""CLI entrypoint: ingest, search, stats."""

import argparse
import sys
from pathlib import Path

from shard.ingest import ingest_dir
from shard.search import export_csv, search_email, stats


def cmd_ingest(args) -> int:
    root = Path(args.path)
    if not root.exists():
        print(f"path not found: {root}", file=sys.stderr)
        return 1
    files, rows = ingest_dir(root)
    print(f"done. {files} files, {rows} credential rows ingested.")
    return 0


def cmd_search(args) -> int:
    rows = search_email(args.query, limit=args.limit, exact=args.exact)
    if not rows:
        print("no results")
        return 0
    for r in rows:
        print(f"{r['email']}	{r.get('password') or ''}	{r.get('source') or ''}")
    print(f"\n{len(rows)} results")
    return 0


def cmd_stats(args) -> int:
    s = stats()
    print(f"emails:      {s['emails']}")
    print(f"credentials: {s['credentials']}")
    print(f"sources:     {s['sources']}")
    return 0


def cmd_export(args) -> int:
    rows = search_email(args.query, limit=args.limit, exact=args.exact)
    sys.stdout.write(export_csv(rows))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="shard", description="self-hosted breach search engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="ingest a directory of dumps")
    p_ingest.add_argument("path", help="directory containing dumps")
    p_ingest.set_defaults(func=cmd_ingest)

    p_search = sub.add_parser("search", help="search emails")
    p_search.add_argument("query", help="email or prefix")
    p_search.add_argument("--limit", type=int, default=50)
    p_search.add_argument("--exact", action="store_true", help="exact match only")
    p_search.set_defaults(func=cmd_search)

    p_stats = sub.add_parser("stats", help="show index stats")
    p_stats.set_defaults(func=cmd_stats)

    p_export = sub.add_parser("export", help="export search results as CSV")
    p_export.add_argument("query")
    p_export.add_argument("--limit", type=int, default=500)
    p_export.add_argument("--exact", action="store_true")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
