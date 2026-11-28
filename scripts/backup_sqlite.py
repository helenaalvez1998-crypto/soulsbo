#!/usr/bin/env python3
"""Backup consistente de um SQLite ativo usando a API online backup do SQLite."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def backup_sqlite(source: Path, destination: Path) -> dict[str, str | int]:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if source == destination:
        raise ValueError("source_and_destination_must_differ")
    if not source.is_file():
        raise FileNotFoundError("source_database_not_found")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_conn = sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True, timeout=30)
    dest_conn = sqlite3.connect(destination, timeout=30)
    try:
        source_conn.backup(dest_conn, pages=256, sleep=0.05)
        result = dest_conn.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise sqlite3.DatabaseError("backup_integrity_check_failed")
        size = destination.stat().st_size
        return {"status": "ok", "destination": str(destination), "bytes": size, "integrity": "ok"}
    finally:
        dest_conn.close()
        source_conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        import json
        print(json.dumps(backup_sqlite(args.source, args.destination), ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"Backup não concluído: {type(exc).__name__}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
