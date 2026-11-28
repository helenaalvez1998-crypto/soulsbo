"""Small smoke-test command for the isolated v2 repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .repository import SQLiteMatchRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a dedicated Card Engine v2 SQLite file")
    parser.add_argument("database", type=Path, help="dedicated SQLite path; never pass the legacy DB")
    args = parser.parse_args()
    repo = SQLiteMatchRepository(args.database)
    print(json.dumps(repo.verify_integrity(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
