"""Dedicated SQLite persistence for saved Card Engine v2 alpha deck lists.

This file is intentionally separate from the legacy Soulsbo database and from
the match snapshot database. Ownership is revalidated at matchmaking time by
the application service; saving a deck never grants cards to a player.
"""

from __future__ import annotations

import json
from contextlib import closing
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .errors import InvalidOperation, PersistenceConflict
from .deck_builder import DECK_RULES_VERSION

DECK_REPOSITORY_SCHEMA_VERSION = 2


class SQLiteDeckRepository:
    def __init__(self, database_path: str | os.PathLike[str], *, busy_timeout_ms: int = 10_000) -> None:
        if str(database_path) == ":memory:":
            raise ValueError("use a dedicated file path; each operation opens its own SQLite connection")
        if busy_timeout_ms < 1:
            raise ValueError("busy_timeout_ms must be positive")
        self.database_path = Path(database_path).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout_ms = busy_timeout_ms
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def _initialize(self) -> None:
        if self.database_path.exists() and self.database_path.stat().st_size:
            with closing(self._connect()) as conn:
                tables = {
                    row[0] for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                }
                if tables and "card_engine_v2_deck_marker" not in tables:
                    raise ValueError("refusing to open a non-empty unmarked deck database")
                if "card_engine_v2_deck_marker" in tables:
                    marker = conn.execute(
                        "SELECT engine_id,schema_version FROM card_engine_v2_deck_marker WHERE marker_id=1"
                    ).fetchone()
                    if (
                        marker is None
                        or marker[0] != "soulsbo-card-engine-v2-decks"
                        or marker[1] not in (1, DECK_REPOSITORY_SCHEMA_VERSION)
                    ):
                        raise ValueError("invalid Card Engine v2 deck database marker")
        with closing(self._connect()) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS card_engine_v2_deck_marker (
                        marker_id INTEGER PRIMARY KEY CHECK(marker_id=1),
                        engine_id TEXT NOT NULL,
                        schema_version INTEGER NOT NULL
                    )"""
                )
                conn.execute(
                    "INSERT OR IGNORE INTO card_engine_v2_deck_marker(marker_id,engine_id,schema_version) "
                    "VALUES(1,'soulsbo-card-engine-v2-decks',2)"
                )
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS saved_alpha_decks (
                        owner_player_id TEXT NOT NULL,
                        deck_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        card_ids_json TEXT NOT NULL,
                        exemplar_ids_json TEXT NOT NULL DEFAULT '[]',
                        faction_id TEXT,
                        leader_id TEXT,
                        rules_version TEXT NOT NULL,
                        version INTEGER NOT NULL CHECK(version >= 1),
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY(owner_player_id, deck_id)
                    )"""
                )
                columns = {row[1] for row in conn.execute("PRAGMA table_info(saved_alpha_decks)")}
                if "exemplar_ids_json" not in columns:
                    # Existing v1 rows receive an empty list, not fabricated exemplar IDs.
                    conn.execute(
                        "ALTER TABLE saved_alpha_decks ADD COLUMN exemplar_ids_json TEXT NOT NULL DEFAULT '[]'"
                    )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_saved_alpha_decks_owner "
                    "ON saved_alpha_decks(owner_player_id, updated_at DESC)"
                )
                conn.execute(
                    "UPDATE card_engine_v2_deck_marker SET schema_version=? WHERE marker_id=1",
                    (DECK_REPOSITORY_SCHEMA_VERSION,),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def _validate_identity(owner_player_id: str | int, deck_id: str, name: str) -> tuple[str, str, str]:
        owner = str(owner_player_id)
        if not owner.isdigit():
            raise InvalidOperation("owner_player_id must be a numeric player ID")
        if not isinstance(deck_id, str) or not deck_id.strip() or len(deck_id) > 80:
            raise InvalidOperation("deck_id must be a non-empty string of at most 80 characters")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            raise InvalidOperation("deck name must contain 1 to 80 characters")
        return owner, deck_id.strip(), name.strip()

    def save_deck(
        self,
        *,
        owner_player_id: str | int,
        deck_id: str,
        name: str,
        card_ids: Sequence[str],
        exemplar_ids: Sequence[int],
        faction_id: str | None = None,
        leader_id: str | None = None,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        owner, deck_key, deck_name = self._validate_identity(owner_player_id, deck_id, name)
        if isinstance(card_ids, (str, bytes)) or not isinstance(card_ids, Sequence):
            raise InvalidOperation("card_ids must be a sequence")
        if any(not isinstance(card_id, str) or not card_id for card_id in card_ids):
            raise InvalidOperation("card_ids must contain non-empty strings")
        if isinstance(exemplar_ids, (str, bytes)) or not isinstance(exemplar_ids, Sequence):
            raise InvalidOperation("exemplar_ids must be a sequence")
        if len(exemplar_ids) != len(card_ids) or any(
            not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in exemplar_ids
        ):
            raise InvalidOperation("exemplar_ids must contain one positive ID per card slot")
        if len(set(exemplar_ids)) != len(exemplar_ids):
            raise InvalidOperation("a physical exemplar cannot occupy multiple deck slots")
        if expected_version is not None and (
            not isinstance(expected_version, int) or isinstance(expected_version, bool) or expected_version < 1
        ):
            raise InvalidOperation("expected_version must be a positive integer or None for create-only")

        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(list(card_ids), ensure_ascii=False, separators=(",", ":"))
        exemplar_payload = json.dumps(list(exemplar_ids), ensure_ascii=False, separators=(",", ":"))
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                current = conn.execute(
                    "SELECT version,created_at FROM saved_alpha_decks WHERE owner_player_id=? AND deck_id=?",
                    (owner, deck_key),
                ).fetchone()
                if current is None:
                    if expected_version is not None:
                        raise PersistenceConflict("deck_does_not_exist_for_expected_version")
                    version = 1
                    created_at = now
                    conn.execute(
                        """INSERT INTO saved_alpha_decks(
                            owner_player_id,deck_id,name,card_ids_json,exemplar_ids_json,faction_id,leader_id,
                            rules_version,version,created_at,updated_at
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (owner, deck_key, deck_name, payload, exemplar_payload, faction_id, leader_id,
                         DECK_RULES_VERSION, version, created_at, now),
                    )
                else:
                    if expected_version is None or current["version"] != expected_version:
                        raise PersistenceConflict("saved_deck_version_conflict")
                    version = int(current["version"]) + 1
                    created_at = str(current["created_at"])
                    updated = conn.execute(
                        """UPDATE saved_alpha_decks SET name=?,card_ids_json=?,exemplar_ids_json=?,
                           faction_id=?,leader_id=?,rules_version=?,version=?,updated_at=?
                           WHERE owner_player_id=? AND deck_id=? AND version=?""",
                        (deck_name, payload, exemplar_payload, faction_id, leader_id, DECK_RULES_VERSION,
                         version, now, owner, deck_key, expected_version),
                    )
                    if updated.rowcount != 1:
                        raise PersistenceConflict("saved_deck_version_conflict")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return {
            "owner_player_id": owner,
            "deck_id": deck_key,
            "name": deck_name,
            "card_ids": list(card_ids),
            "exemplar_ids": list(exemplar_ids),
            "faction_id": faction_id,
            "leader_id": leader_id,
            "rules_version": DECK_RULES_VERSION,
            "version": version,
            "created_at": created_at,
            "updated_at": now,
        }

    @staticmethod
    def _decode_row(row: sqlite3.Row) -> dict[str, Any]:
        try:
            card_ids = json.loads(row["card_ids_json"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise InvalidOperation("saved deck contains invalid card_ids_json") from exc
        if not isinstance(card_ids, list) or any(not isinstance(item, str) for item in card_ids):
            raise InvalidOperation("saved deck card list is malformed")
        try:
            exemplar_ids = json.loads(row["exemplar_ids_json"])
        except (TypeError, json.JSONDecodeError, IndexError) as exc:
            raise InvalidOperation("saved deck exemplar list is malformed") from exc
        if not isinstance(exemplar_ids, list) or any(
            not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in exemplar_ids
        ):
            raise InvalidOperation("saved deck exemplar list is malformed")
        if exemplar_ids and (len(exemplar_ids) != len(card_ids) or len(set(exemplar_ids)) != len(exemplar_ids)):
            raise InvalidOperation("saved deck exemplar slots do not align with card slots")
        return {
            "owner_player_id": row["owner_player_id"],
            "deck_id": row["deck_id"],
            "name": row["name"],
            "card_ids": card_ids,
            "exemplar_ids": exemplar_ids,
            "faction_id": row["faction_id"],
            "leader_id": row["leader_id"],
            "rules_version": row["rules_version"],
            "version": int(row["version"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def get_deck(self, owner_player_id: str | int, deck_id: str) -> dict[str, Any] | None:
        owner = str(owner_player_id)
        if not owner.isdigit() or not isinstance(deck_id, str) or not deck_id:
            raise InvalidOperation("invalid deck owner or deck_id")
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM saved_alpha_decks WHERE owner_player_id=? AND deck_id=?",
                (owner, deck_id),
            ).fetchone()
        return self._decode_row(row) if row else None

    def list_decks(self, owner_player_id: str | int) -> list[dict[str, Any]]:
        owner = str(owner_player_id)
        if not owner.isdigit():
            raise InvalidOperation("owner_player_id must be numeric")
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM saved_alpha_decks WHERE owner_player_id=? ORDER BY updated_at DESC,deck_id",
                (owner,),
            ).fetchall()
        return [self._decode_row(row) for row in rows]

    def delete_deck(
        self, owner_player_id: str | int, deck_id: str, *, expected_version: int
    ) -> bool:
        owner = str(owner_player_id)
        if not owner.isdigit() or not isinstance(deck_id, str) or not deck_id:
            raise InvalidOperation("invalid deck owner or deck_id")
        if not isinstance(expected_version, int) or isinstance(expected_version, bool) or expected_version < 1:
            raise InvalidOperation("expected_version must be positive")
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute(
                    "DELETE FROM saved_alpha_decks WHERE owner_player_id=? AND deck_id=? AND version=?",
                    (owner, deck_id, expected_version),
                )
                if cur.rowcount != 1:
                    raise PersistenceConflict("saved_deck_version_conflict")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return True

    def verify_integrity(self) -> dict[str, Any]:
        with closing(self._connect()) as conn:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
            count = conn.execute("SELECT COUNT(*) FROM saved_alpha_decks").fetchone()[0]
            provenance_missing = conn.execute(
                "SELECT COUNT(*) FROM saved_alpha_decks WHERE exemplar_ids_json='[]'"
            ).fetchone()[0]
        return {
            "integrity_check": integrity,
            "foreign_key_violations": len(foreign_keys),
            "deck_count": int(count),
            "decks_missing_exemplar_provenance": int(provenance_missing),
            "schema_version": DECK_REPOSITORY_SCHEMA_VERSION,
        }
