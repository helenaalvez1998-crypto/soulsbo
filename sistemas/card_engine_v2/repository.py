"""SQLite persistence vertical for the isolated Soulsbo Card Engine v2.

The repository owns transactional persistence. Gameplay handlers are pure
callbacks: they receive a detached state copy and must not perform network,
Discord, file, or other external side effects. External delivery is represented
as transactional outbox rows and happens after commit.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from .canonical import sha256_json, sha256_text, storage_json_bytes
from .errors import (
    IdempotencyConflict,
    InvalidMatchState,
    InvalidOperation,
    MatchNotFound,
    MigrationChecksumMismatch,
    OutboxStateError,
    PersistenceConflict,
)
from .validation import REMOVAL_CAUSES, is_uuid4, validate_match_state, validate_operation_request


MIGRATION_ID = "0001_card_engine_v2_persistence_core"
APP_VERSION = "card-engine-v2-alpha.3"

MIGRATION_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS card_game_schema_migrations (
        migration_id TEXT PRIMARY KEY,
        checksum_sha256 TEXT NOT NULL,
        applied_at TEXT NOT NULL,
        app_version TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS card_engine_v2_database_marker (
        marker_id INTEGER PRIMARY KEY CHECK(marker_id = 1),
        engine_id TEXT NOT NULL UNIQUE,
        schema_version INTEGER NOT NULL CHECK(schema_version = 7)
    )""",
    """CREATE TABLE IF NOT EXISTS cartas_gwent_matches (
        match_id INTEGER PRIMARY KEY CHECK(match_id > 0),
        schema_version INTEGER NOT NULL CHECK(schema_version = 7),
        status TEXT NOT NULL CHECK(status IN ('active', 'finished')),
        state_json TEXT NOT NULL,
        state_revision INTEGER NOT NULL CHECK(state_revision >= 0),
        event_watermark INTEGER NOT NULL CHECK(event_watermark >= 0),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS cartas_gwent_match_operations (
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        fingerprint_sha256 TEXT NOT NULL,
        actor_json TEXT NOT NULL,
        expected_revision INTEGER NOT NULL CHECK(expected_revision >= 0),
        revision_before INTEGER NOT NULL CHECK(revision_before >= 0),
        revision_after INTEGER NOT NULL CHECK(revision_after >= 0),
        outcome TEXT NOT NULL CHECK(outcome IN ('applied','partial','blocked','consumed_no_effect','rejected')),
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY(match_id, operation_id),
        FOREIGN KEY(match_id) REFERENCES cartas_gwent_matches(match_id) ON DELETE RESTRICT
    )""",
    """CREATE TABLE IF NOT EXISTS cartas_gwent_match_events (
        event_id TEXT PRIMARY KEY,
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        sequence INTEGER NOT NULL CHECK(sequence > 0),
        kind TEXT NOT NULL,
        effect_scope TEXT NOT NULL CHECK(effect_scope IN ('direct','reactive','system')),
        source_effect_id TEXT,
        source_instance_id TEXT,
        target_instance_ids_json TEXT NOT NULL,
        caused_by_event_ids_json TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(match_id, sequence),
        FOREIGN KEY(match_id, operation_id)
            REFERENCES cartas_gwent_match_operations(match_id, operation_id) ON DELETE RESTRICT
    )""",
    """CREATE TABLE IF NOT EXISTS cartas_gwent_match_rewards (
        reward_id TEXT PRIMARY KEY,
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        player_id TEXT NOT NULL,
        reward_key TEXT NOT NULL,
        reward_type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(match_id, reward_key),
        FOREIGN KEY(match_id, operation_id)
            REFERENCES cartas_gwent_match_operations(match_id, operation_id) ON DELETE RESTRICT
    )""",
    """CREATE TABLE IF NOT EXISTS cartas_gwent_outbox (
        outbox_id TEXT PRIMARY KEY,
        match_id INTEGER NOT NULL,
        operation_id TEXT NOT NULL,
        source_event_id TEXT,
        topic TEXT NOT NULL,
        idempotency_key TEXT NOT NULL UNIQUE,
        payload_json TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','in_flight','delivered','dead_letter')),
        attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
        next_attempt_at TEXT NOT NULL,
        lease_until TEXT,
        delivered_at TEXT,
        last_error TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(match_id, operation_id)
            REFERENCES cartas_gwent_match_operations(match_id, operation_id) ON DELETE RESTRICT,
        FOREIGN KEY(source_event_id)
            REFERENCES cartas_gwent_match_events(event_id) ON DELETE RESTRICT
    )""",
    """CREATE TABLE IF NOT EXISTS card_engine_v2_legacy_archive (
        archive_id TEXT PRIMARY KEY,
        legacy_match_id INTEGER NOT NULL,
        source_sha256 TEXT NOT NULL,
        source_state_json TEXT NOT NULL,
        target_schema_version INTEGER NOT NULL,
        migration_id TEXT NOT NULL,
        occurrence_mapping_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(legacy_match_id, source_sha256)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_cartas_gwent_match_events_match_sequence ON cartas_gwent_match_events(match_id, sequence)",
    "CREATE INDEX IF NOT EXISTS idx_cartas_gwent_outbox_due ON cartas_gwent_outbox(status, next_attempt_at, lease_until)",
    """CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_events_no_update
       BEFORE UPDATE ON cartas_gwent_match_events
       BEGIN SELECT RAISE(ABORT, 'domain event journal is append-only'); END""",
    """CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_events_no_delete
       BEFORE DELETE ON cartas_gwent_match_events
       BEGIN SELECT RAISE(ABORT, 'domain event journal is append-only'); END""",
    """CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_operations_no_update
       BEFORE UPDATE ON cartas_gwent_match_operations
       BEGIN SELECT RAISE(ABORT, 'operation ledger is immutable'); END""",
    """CREATE TRIGGER IF NOT EXISTS cartas_gwent_match_operations_no_delete
       BEFORE DELETE ON cartas_gwent_match_operations
       BEGIN SELECT RAISE(ABORT, 'operation ledger is immutable'); END""",
)
MIGRATION_CHECKSUM = hashlib.sha256("\n-- statement --\n".join(MIGRATION_STATEMENTS).encode("utf-8")).hexdigest()

# Additive migration: turn/round/weather state is stored beside the CardInstance
# snapshot and committed under the same state_revision/CAS transaction.
MIGRATION_2_ID = "0002_card_engine_v2_match_runtime"
MIGRATION_2_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS card_engine_v2_match_runtime (
        match_id INTEGER PRIMARY KEY,
        state_revision INTEGER NOT NULL CHECK(state_revision >= 0),
        runtime_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(match_id) REFERENCES cartas_gwent_matches(match_id) ON DELETE RESTRICT
    )""",
)
MIGRATION_2_CHECKSUM = hashlib.sha256("\n-- statement --\n".join(MIGRATION_2_STATEMENTS).encode("utf-8")).hexdigest()


@dataclass(slots=True)
class HandlerResult:
    """Output of a pure gameplay handler, before persistence metadata is added."""

    outcome: str
    state: dict[str, Any] | None = None
    target_results: list[dict[str, Any]] = field(default_factory=list)
    costs: dict[str, Any] = field(default_factory=dict)
    reason_code: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    rewards: list[dict[str, Any]] = field(default_factory=list)
    outbox: list[dict[str, Any]] = field(default_factory=list)
    runtime_state: dict[str, Any] | None = None


@dataclass(slots=True)
class OperationReceipt:
    result: dict[str, Any]
    replayed: bool = False


OperationHandler = Callable[[dict[str, Any], dict[str, Any]], HandlerResult]


def _default_match_runtime(state: dict[str, Any]) -> dict[str, Any]:
    player_ids = list(state.get("players", {}).keys())
    if len(player_ids) < 2:
        raise InvalidMatchState("gameplay runtime requires at least two players")
    return {
        "runtime_version": 1,
        "phase": "round",
        "round_number": 1,
        "round_starter_player_id": player_ids[0],
        "current_player_id": player_ids[0],
        "passed_player_ids": [],
        "round_wins": {player_id: 0 for player_id in player_ids},
        "life_by_player": {player_id: 20 for player_id in player_ids},
        "best_of": 3,
        "max_rounds": 3,
        "draw_per_round": 2,
        "turn_number": 0,
        "weather_by_row": {"melee": 0, "ranged": 0, "siege": 0},
        "round_history": [],
    }


def _validate_match_runtime(runtime: dict[str, Any], player_ids: list[str]) -> None:
    if not isinstance(runtime, dict) or runtime.get("runtime_version") != 1:
        raise InvalidMatchState("gameplay runtime must use runtime_version=1")
    if runtime.get("phase") not in ("round", "finished"):
        raise InvalidMatchState("gameplay runtime phase is invalid")
    for field_name in ("round_number", "turn_number", "best_of", "max_rounds", "draw_per_round"):
        value = runtime.get(field_name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidMatchState(f"gameplay runtime {field_name} must be a non-negative integer")
    if runtime["round_number"] < 1 or runtime["best_of"] < 1 or runtime["max_rounds"] < runtime["best_of"]:
        raise InvalidMatchState("gameplay runtime round/best-of configuration is invalid")
    if runtime.get("round_starter_player_id") not in player_ids:
        raise InvalidMatchState("gameplay runtime starter is not a participant")
    current_player = runtime.get("current_player_id")
    if current_player is not None and current_player not in player_ids:
        raise InvalidMatchState("gameplay runtime current player is not a participant")
    passed = runtime.get("passed_player_ids")
    if not isinstance(passed, list) or len(passed) != len(set(passed)) or any(item not in player_ids for item in passed):
        raise InvalidMatchState("gameplay runtime passed_player_ids is invalid")
    wins = runtime.get("round_wins")
    if not isinstance(wins, dict) or set(wins) != set(player_ids):
        raise InvalidMatchState("gameplay runtime round_wins must cover exactly the participants")
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in wins.values()):
        raise InvalidMatchState("gameplay runtime round wins must be non-negative integers")
    life_by_player = runtime.get("life_by_player")
    if life_by_player is not None:
        if not isinstance(life_by_player, dict) or set(life_by_player) != set(player_ids):
            raise InvalidMatchState("gameplay runtime life_by_player must cover exactly the participants")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in life_by_player.values()
        ):
            raise InvalidMatchState("gameplay runtime life values must be non-negative integers")
    weather = runtime.get("weather_by_row")
    if not isinstance(weather, dict) or set(weather) != {"melee", "ranged", "siege"}:
        raise InvalidMatchState("gameplay runtime weather_by_row must contain all rows")
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in weather.values()):
        raise InvalidMatchState("gameplay runtime weather values must be non-negative integers")
    if not isinstance(runtime.get("round_history"), list):
        raise InvalidMatchState("gameplay runtime round_history must be a list")
    fatigue_counts = runtime.get("deck_fatigue_count_by_player")
    if fatigue_counts is not None:
        if not isinstance(fatigue_counts, dict) or set(fatigue_counts) != set(player_ids):
            raise InvalidMatchState("deck_fatigue_count_by_player must cover exactly the participants")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in fatigue_counts.values()
        ):
            raise InvalidMatchState("deck fatigue counters must be non-negative integers")
    # Energy is stored in the match runtime sidecar, not CardInstance v7.
    energy_by_player = runtime.get("energy_by_player")
    maximum_energy = runtime.get("maximum_energy")
    energy_turns_started = runtime.get("energy_turns_started_by_player")
    if energy_by_player is not None or maximum_energy is not None or energy_turns_started is not None:
        if (
            not isinstance(maximum_energy, int)
            or isinstance(maximum_energy, bool)
            or maximum_energy < 1
        ):
            raise InvalidMatchState("gameplay runtime maximum_energy must be a positive integer")
        if not isinstance(energy_by_player, dict) or set(energy_by_player) != set(player_ids):
            raise InvalidMatchState("energy_by_player must cover exactly the participants")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > maximum_energy
            for value in energy_by_player.values()
        ):
            raise InvalidMatchState("player energy must be an integer within the configured cap")
        if not isinstance(energy_turns_started, dict) or set(energy_turns_started) != set(player_ids):
            raise InvalidMatchState("energy_turns_started_by_player must cover exactly the participants")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in energy_turns_started.values()
        ):
            raise InvalidMatchState("energy turn counters must be non-negative integers")
    ability_uses = runtime.get("card_ability_uses_by_instance", {})
    if not isinstance(ability_uses, dict):
        raise InvalidMatchState("card_ability_uses_by_instance must be an object")
    if any(
        not isinstance(key, str) or not key
        or not isinstance(value, int) or isinstance(value, bool) or value < 0
        for key, value in ability_uses.items()
    ):
        raise InvalidMatchState("manual card ability usage counters must be non-negative integer entries")
    initial_exemptions = runtime.get("initial_turn_exemption_pending_by_player")
    if initial_exemptions is not None:
        if not isinstance(initial_exemptions, dict) or set(initial_exemptions) != set(player_ids):
            raise InvalidMatchState("initial turn exemptions must cover exactly the participants")
        if any(not isinstance(value, bool) for value in initial_exemptions.values()):
            raise InvalidMatchState("initial turn exemptions must be booleans")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _parse_json(value: str) -> Any:
    return json.loads(value)


def _canonical_text(value: Any) -> str:
    return storage_json_bytes(value).decode("utf-8")


def _has_consumed_cost(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return value > 0
    if isinstance(value, list):
        return any(_has_consumed_cost(item) for item in value)
    if isinstance(value, dict):
        return any(_has_consumed_cost(item) for item in value.values())
    return False


def _validate_event(event: dict[str, Any]) -> None:
    required = {
        "kind",
        "effect_scope",
        "source_effect_id",
        "source_instance_id",
        "target_instance_ids",
        "caused_by_event_ids",
        "payload",
    }
    missing = required - event.keys()
    if missing:
        raise InvalidOperation(f"domain event missing keys: {sorted(missing)}")
    if not isinstance(event["kind"], str) or not event["kind"]:
        raise InvalidOperation("event kind is required")
    if event["effect_scope"] not in ("direct", "reactive", "system"):
        raise InvalidOperation("invalid event effect_scope")
    if event["effect_scope"] in ("direct", "reactive") and not event["source_effect_id"]:
        raise InvalidOperation("direct/reactive events require source_effect_id")
    if not isinstance(event["target_instance_ids"], list):
        raise InvalidOperation("event target_instance_ids must be a list")
    if any(not is_uuid4(item) for item in event["target_instance_ids"]):
        raise InvalidOperation("event target_instance_ids must contain UUIDv4 values")
    if len(event["target_instance_ids"]) != len(set(event["target_instance_ids"])):
        raise InvalidOperation("event target_instance_ids must be unique")
    if not isinstance(event["caused_by_event_ids"], list):
        raise InvalidOperation("event caused_by_event_ids must be a list")
    if any(not is_uuid4(item) for item in event["caused_by_event_ids"]):
        raise InvalidOperation("event caused_by_event_ids must contain UUIDv4 values")
    if len(event["caused_by_event_ids"]) != len(set(event["caused_by_event_ids"])):
        raise InvalidOperation("event caused_by_event_ids must be unique")
    if not isinstance(event["payload"], dict):
        raise InvalidOperation("event payload must be an object")
    source_instance_id = event["source_instance_id"]
    if source_instance_id is not None and not is_uuid4(source_instance_id):
        raise InvalidOperation("source_instance_id must be UUIDv4 or null")
    if event["kind"] == "unit_removed":
        payload = event["payload"]
        if (
            payload.get("cause_id") not in REMOVAL_CAUSES
            or payload.get("from_zone") != "board"
            or payload.get("to_zone") != "discard"
            or not payload.get("affected_player_id")
            or len(event["target_instance_ids"]) != 1
        ):
            raise InvalidOperation("unit_removed violates the canonical removal contract")
    elif event["kind"] == "unit_removal_blocked":
        if (
            event["payload"].get("cause_id") not in ("normal_removal", "execution")
            or len(event["target_instance_ids"]) != 1
        ):
            raise InvalidOperation("unit_removal_blocked violates the canonical protection contract")
    elif event["kind"] == "unit_archived":
        if event["effect_scope"] != "system" or event["payload"].get("transition_id") != "round_archive":
            raise InvalidOperation("unit_archived must be a round_archive system transition")
        if "cause_id" in event["payload"]:
            raise InvalidOperation("round_archive is not a removal cause")
    elif event["kind"] == "protection_grant_applied":
        payload = event["payload"]
        grant_ids = payload.get("grant_ids_by_target")
        if (
            event["effect_scope"] != "direct"
            or not isinstance(payload.get("profile_id"), str)
            or not payload.get("profile_id")
            or not isinstance(payload.get("charges"), int)
            or isinstance(payload.get("charges"), bool)
            or payload.get("charges", 0) < 1
            or payload.get("expires_on") not in ("round_close", "board_exit", "permanent_instance")
            or not isinstance(grant_ids, dict)
            or set(grant_ids) != set(event["target_instance_ids"])
            or any(not is_uuid4(item) for item in grant_ids.values())
            or len(set(grant_ids.values())) != len(grant_ids)
            or not event["target_instance_ids"]
        ):
            raise InvalidOperation("protection_grant_applied violates the canonical protection grant contract")
    elif event["kind"] == "vengeance_bonus_applied":
        if (
            event["source_effect_id"] != "effect.vengeance_on_removal"
            or event["effect_scope"] != "reactive"
        ):
            raise InvalidOperation("Vingança must use the canonical reactive effect id")


class SQLiteMatchRepository:
    """Standalone SQLite repository for the new engine.

    Use a dedicated local SQLite file. This repository does not open or migrate
    the legacy Soulsbo database and is not connected to bot.py/database.py.
    """

    def __init__(
        self,
        database_path: str | os.PathLike[str],
        *,
        busy_timeout_ms: int = 10_000,
        app_version: str = APP_VERSION,
    ) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        if str(database_path) == ":memory:":
            raise ValueError("use a temporary file; each operation uses an independent SQLite connection")
        if busy_timeout_ms < 1:
            raise ValueError("busy_timeout_ms must be positive")
        self.busy_timeout_ms = busy_timeout_ms
        self.app_version = app_version
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._preflight_dedicated_database()
        with self._managed_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
        self.apply_migrations()

    def _preflight_dedicated_database(self) -> None:
        """Refuse non-empty unmarked databases so the legacy DB cannot be modified by mistake."""
        if not self.database_path.exists() or self.database_path.stat().st_size == 0:
            return
        conn = sqlite3.connect(self.database_path)
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            }
            if not tables:
                return
            if "card_engine_v2_database_marker" not in tables:
                raise ValueError(
                    "refusing to initialize a non-empty unmarked SQLite file; "
                    "use a dedicated new Card Engine v2 database path, never the legacy Soulsbo DB"
                )
            marker = conn.execute(
                "SELECT engine_id,schema_version FROM card_engine_v2_database_marker WHERE marker_id=1"
            ).fetchone()
            if marker is None or marker[0] != "soulsbo-card-engine-v2" or marker[1] != 7:
                raise ValueError("SQLite file has an invalid Card Engine v2 database marker")
        finally:
            conn.close()

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

    @contextmanager
    def _managed_connection(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def apply_migrations(self) -> list[str]:
        """Apply checksummed migrations; repeated application is a no-op."""
        applied: list[str] = []
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(MIGRATION_STATEMENTS[0])
            row = conn.execute(
                "SELECT checksum_sha256 FROM card_game_schema_migrations WHERE migration_id=?",
                (MIGRATION_ID,),
            ).fetchone()
            if row:
                if row["checksum_sha256"] != MIGRATION_CHECKSUM:
                    raise MigrationChecksumMismatch(
                        f"{MIGRATION_ID} checksum differs from the applied migration"
                    )
                marker = conn.execute(
                    "SELECT engine_id,schema_version FROM card_engine_v2_database_marker WHERE marker_id=1"
                ).fetchone()
                if marker is None or marker["engine_id"] != "soulsbo-card-engine-v2" or marker["schema_version"] != 7:
                    raise InvalidOperation("Card Engine v2 database marker is missing or invalid")
            else:
                for statement in MIGRATION_STATEMENTS[1:]:
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO card_engine_v2_database_marker(marker_id,engine_id,schema_version) "
                    "VALUES(1,'soulsbo-card-engine-v2',7)"
                )
                conn.execute(
                    "INSERT INTO card_game_schema_migrations"
                    "(migration_id, checksum_sha256, applied_at, app_version) VALUES(?,?,?,?)",
                    (MIGRATION_ID, MIGRATION_CHECKSUM, _utc_now(), self.app_version),
                )
                applied.append(MIGRATION_ID)

            row2 = conn.execute(
                "SELECT checksum_sha256 FROM card_game_schema_migrations WHERE migration_id=?",
                (MIGRATION_2_ID,),
            ).fetchone()
            if row2:
                if row2["checksum_sha256"] != MIGRATION_2_CHECKSUM:
                    raise MigrationChecksumMismatch(
                        f"{MIGRATION_2_ID} checksum differs from the applied migration"
                    )
            else:
                for statement in MIGRATION_2_STATEMENTS:
                    conn.execute(statement)
                # Backfill legacy alpha matches deterministically. The first participant
                # in snapshot insertion order starts round 1; no card data is changed.
                existing_matches = conn.execute(
                    "SELECT match_id,state_json,state_revision FROM cartas_gwent_matches ORDER BY match_id"
                ).fetchall()
                for match_row in existing_matches:
                    snapshot = _parse_json(match_row["state_json"])
                    runtime = _default_match_runtime(snapshot)
                    conn.execute(
                        "INSERT INTO card_engine_v2_match_runtime(match_id,state_revision,runtime_json,updated_at) "
                        "VALUES(?,?,?,?)",
                        (match_row["match_id"], match_row["state_revision"], _canonical_text(runtime), _utc_now()),
                    )
                conn.execute(
                    "INSERT INTO card_game_schema_migrations"
                    "(migration_id, checksum_sha256, applied_at, app_version) VALUES(?,?,?,?)",
                    (MIGRATION_2_ID, MIGRATION_2_CHECKSUM, _utc_now(), self.app_version),
                )
                applied.append(MIGRATION_2_ID)
            conn.commit()
            return applied
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_match(self, state: dict[str, Any], runtime_state: dict[str, Any] | None = None) -> None:
        validate_match_state(state)
        if state["state_revision"] != 0 or state["event_watermark"] != 0:
            raise InvalidMatchState("new matches must start at revision=0 and event_watermark=0")
        runtime = copy.deepcopy(runtime_state) if runtime_state is not None else _default_match_runtime(state)
        _validate_match_runtime(runtime, list(state["players"].keys()))
        now = _utc_now()
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO cartas_gwent_matches"
                "(match_id,schema_version,status,state_json,state_revision,event_watermark,created_at,updated_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (
                    state["match_id"],
                    state["schema_version"],
                    state["status"],
                    _canonical_text(state),
                    state["state_revision"],
                    state["event_watermark"],
                    now,
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO card_engine_v2_match_runtime(match_id,state_revision,runtime_json,updated_at) VALUES(?,?,?,?)",
                (state["match_id"], state["state_revision"], _canonical_text(runtime), now),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_match(self, match_id: int) -> dict[str, Any]:
        with self._managed_connection() as conn:
            row = conn.execute(
                "SELECT state_json,state_revision,event_watermark FROM cartas_gwent_matches WHERE match_id=?",
                (match_id,),
            ).fetchone()
        if row is None:
            raise MatchNotFound(str(match_id))
        state = _parse_json(row["state_json"])
        if state["state_revision"] != row["state_revision"]:
            raise InvalidMatchState("database/state_json state_revision divergence")
        if state["event_watermark"] != row["event_watermark"]:
            raise InvalidMatchState("database/state_json event_watermark divergence")
        return state

    def list_matches_for_player(self, player_id: str | int, *, limit: int = 20) -> list[dict[str, Any]]:
        """List minimal match metadata for one participant; never returns match state."""
        normalized_player_id = str(player_id)
        if not normalized_player_id.isascii() or not normalized_player_id.isdigit() or int(normalized_player_id) <= 0:
            raise InvalidOperation("invalid_player_id")
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise InvalidOperation("match_list_limit_must_be_positive")
        limit = min(limit, 25)
        with self._managed_connection() as conn:
            rows = conn.execute(
                "SELECT match_id,status,created_at,updated_at,state_revision,event_watermark,state_json "
                "FROM cartas_gwent_matches ORDER BY updated_at DESC,match_id DESC"
            ).fetchall()
        matches: list[dict[str, Any]] = []
        for row in rows:
            state = _parse_json(row["state_json"])
            players = state.get("players", {})
            if normalized_player_id not in players:
                continue
            opponent_ids = [str(item) for item in players if str(item) != normalized_player_id]
            matches.append({
                "match_id": int(row["match_id"]),
                "status": str(row["status"]),
                "opponent_player_id": opponent_ids[0] if len(opponent_ids) == 1 else None,
                "created_at": str(row["created_at"]),
                "updated_at": str(row["updated_at"]),
                "state_revision": int(row["state_revision"]),
                "event_watermark": int(row["event_watermark"]),
            })
            if len(matches) >= limit:
                break
        return matches

    def get_competitive_stats_for_player(self, player_id: str | int) -> dict[str, int]:
        """Return aggregate finished-match stats for one player, without exposing matches."""
        normalized_player_id = str(player_id)
        if (
            not normalized_player_id.isascii()
            or not normalized_player_id.isdigit()
            or int(normalized_player_id) <= 0
        ):
            raise InvalidOperation("invalid_player_id")

        with self._managed_connection() as conn:
            rows = conn.execute(
                "SELECT m.state_json,m.state_revision,r.runtime_json,r.state_revision AS runtime_revision "
                "FROM cartas_gwent_matches m "
                "JOIN card_engine_v2_match_runtime r ON r.match_id=m.match_id "
                "WHERE m.status='finished' ORDER BY m.match_id"
            ).fetchall()

        stats = {"played": 0, "wins": 0, "losses": 0, "draws": 0}
        for row in rows:
            if int(row["state_revision"]) != int(row["runtime_revision"]):
                raise InvalidMatchState("finished match runtime/snapshot revision divergence")
            state = _parse_json(row["state_json"])
            players = state.get("players", {})
            if normalized_player_id not in players:
                continue
            runtime = _parse_json(row["runtime_json"])
            winner = runtime.get("match_winner_player_id")
            stats["played"] += 1
            if winner is None:
                stats["draws"] += 1
            elif str(winner) == normalized_player_id:
                stats["wins"] += 1
            else:
                stats["losses"] += 1
        return stats

    def get_event_history_for_player(
        self,
        match_id: int,
        player_id: str | int,
        *,
        after_sequence: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Return a public-safe event timeline only to a match participant.

        Physical instance IDs, event UUIDs, operation IDs, raw payloads and
        causal identifiers are intentionally omitted from this projection.
        """
        normalized_player_id = str(player_id)
        if (
            not normalized_player_id.isascii()
            or not normalized_player_id.isdigit()
            or int(normalized_player_id) <= 0
        ):
            raise InvalidOperation("invalid_player_id")
        if not isinstance(after_sequence, int) or isinstance(after_sequence, bool) or after_sequence < 0:
            raise InvalidOperation("history_cursor_must_be_non_negative")
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise InvalidOperation("history_limit_must_be_positive")
        limit = min(limit, 100)
        state = self.get_match(match_id)
        if normalized_player_id not in state.get("players", {}):
            raise InvalidOperation("viewer_not_a_match_participant")
        with self._managed_connection() as conn:
            rows = conn.execute(
                "SELECT sequence,kind,effect_scope,source_effect_id,target_instance_ids_json,"
                "caused_by_event_ids_json,payload_json,created_at "
                "FROM cartas_gwent_match_events WHERE match_id=? AND sequence>? "
                "ORDER BY sequence LIMIT ?",
                (match_id, after_sequence, limit + 1),
            ).fetchall()
        has_more = len(rows) > limit
        rows = rows[:limit]
        safe_payload_keys = {
            "action", "row", "round_number", "damage", "life_before", "life_after",
            "energy_before", "energy_spent", "energy_after", "source_kind", "amount",
            "score_before", "score_after", "reason", "finish_reason", "round_winner",
        }
        events: list[dict[str, Any]] = []
        for row in rows:
            try:
                payload = _parse_json(row["payload_json"])
            except (TypeError, ValueError, json.JSONDecodeError):
                payload = {}
            safe_payload = {
                key: payload[key]
                for key in safe_payload_keys
                if isinstance(payload, dict) and key in payload
                and isinstance(payload[key], (str, int, float, bool, type(None)))
            }
            actor_id = payload.get("player_id") if isinstance(payload, dict) else None
            if actor_id is None and isinstance(payload, dict):
                actor_id = payload.get("owner_player_id")
            subject = None
            if actor_id is not None:
                subject = "you" if str(actor_id) == normalized_player_id else (
                    "opponent" if str(actor_id) in state.get("players", {}) else None
                )
            target_ids = _parse_json(row["target_instance_ids_json"])
            causal_ids = _parse_json(row["caused_by_event_ids_json"])
            events.append({
                "sequence": int(row["sequence"]),
                "kind": str(row["kind"]),
                "effect_scope": str(row["effect_scope"]),
                "source_effect_id": row["source_effect_id"],
                "subject": subject,
                "target_count": len(target_ids) if isinstance(target_ids, list) else 0,
                "causal_depth": len(causal_ids) if isinstance(causal_ids, list) else 0,
                "payload": safe_payload,
                "created_at": str(row["created_at"]),
            })
        next_cursor = events[-1]["sequence"] if events else after_sequence
        return {
            "match_id": int(match_id),
            "events": events,
            "after_sequence": after_sequence,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

    def get_match_runtime(self, match_id: int) -> dict[str, Any]:
        """Return the transactionally coupled turn/round/weather sidecar."""
        with self._managed_connection() as conn:
            row = conn.execute(
                "SELECT r.runtime_json,r.state_revision,m.state_revision AS match_revision "
                "FROM card_engine_v2_match_runtime r JOIN cartas_gwent_matches m ON m.match_id=r.match_id "
                "WHERE r.match_id=?",
                (match_id,),
            ).fetchone()
        if row is None:
            raise MatchNotFound(str(match_id))
        if int(row["state_revision"]) != int(row["match_revision"]):
            raise InvalidMatchState("gameplay runtime/snapshot revision divergence")
        runtime = _parse_json(row["runtime_json"])
        _validate_match_runtime(runtime, list(self.get_match(match_id)["players"].keys()))
        return runtime

    def execute_operation(
        self,
        match_id: int,
        request: dict[str, Any],
        handler: OperationHandler,
    ) -> OperationReceipt:
        """Execute one operation with CAS, durable idempotency and atomic journal.

        A stale revision is itself durably recorded as a rejected operation,
        with the gameplay revision unchanged. Handler exceptions roll back the
        entire unit of work and do not reserve the operation_id.
        """
        validate_operation_request(match_id, request)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            match_row = conn.execute(
                "SELECT state_json,state_revision,event_watermark FROM cartas_gwent_matches WHERE match_id=?",
                (match_id,),
            ).fetchone()
            if match_row is None:
                raise MatchNotFound(str(match_id))
            current_state = _parse_json(match_row["state_json"])
            current_revision = int(match_row["state_revision"])
            if current_state["state_revision"] != current_revision:
                raise InvalidMatchState("database/state_json state_revision divergence")
            if current_state["event_watermark"] != int(match_row["event_watermark"]):
                raise InvalidMatchState("database/state_json event_watermark divergence")
            runtime_row = conn.execute(
                "SELECT runtime_json,state_revision FROM card_engine_v2_match_runtime WHERE match_id=?",
                (match_id,),
            ).fetchone()
            if runtime_row is None:
                raise InvalidMatchState("gameplay runtime row is missing")
            if int(runtime_row["state_revision"]) != current_revision:
                raise InvalidMatchState("gameplay runtime/snapshot revision divergence")
            current_runtime = _parse_json(runtime_row["runtime_json"])
            _validate_match_runtime(current_runtime, list(current_state["players"].keys()))

            if request["actor"]["type"] == "player":
                actor_player_id = str(request["actor"]["player_id"])
                if actor_player_id not in current_state["players"]:
                    raise InvalidOperation("player actor is not a participant in this match")

            fingerprint_basis = {
                "match_id": match_id,
                "actor": request["actor"],
                "expected_revision": request["expected_revision"],
                "action_type": request["action_type"],
                "payload": request["payload"],
                "ruleset_release_id": current_state["definition_manifest"]["ruleset_release_id"],
            }
            fingerprint = sha256_json(fingerprint_basis)
            operation_id = request["operation_id"]
            existing = conn.execute(
                "SELECT fingerprint_sha256,result_json FROM cartas_gwent_match_operations "
                "WHERE match_id=? AND operation_id=?",
                (match_id, operation_id),
            ).fetchone()
            if existing:
                if existing["fingerprint_sha256"] != fingerprint:
                    raise IdempotencyConflict("operation_id reused with a different request fingerprint")
                conn.commit()
                return OperationReceipt(_parse_json(existing["result_json"]), replayed=True)

            if request["expected_revision"] != current_revision:
                result = self._make_result(
                    operation_id,
                    "rejected",
                    current_revision,
                    current_revision,
                    reason_code="revision_conflict",
                )
                self._insert_operation(
                    conn,
                    match_id,
                    operation_id,
                    fingerprint,
                    request,
                    current_revision,
                    current_revision,
                    result,
                )
                conn.commit()
                return OperationReceipt(result)

            working_state = copy.deepcopy(current_state)
            handler_request = copy.deepcopy(request)
            handler_request["_runtime_context"] = copy.deepcopy(current_runtime)
            handler_result = handler(working_state, handler_request)
            if not isinstance(handler_result, HandlerResult):
                raise InvalidOperation("handler must return HandlerResult")
            if handler_result.outcome not in ("applied", "partial", "blocked", "consumed_no_effect", "rejected"):
                raise InvalidOperation(f"invalid handler outcome: {handler_result.outcome}")
            if not isinstance(handler_result.target_results, list) or not isinstance(handler_result.costs, dict):
                raise InvalidOperation("target_results must be a list and costs must be an object")
            _canonical_text(handler_result.costs)
            _canonical_text(handler_result.target_results)

            candidate_state = handler_result.state if handler_result.state is not None else working_state
            if not isinstance(candidate_state, dict):
                raise InvalidOperation("handler state must be an object")
            if candidate_state.get("match_id") != match_id:
                raise InvalidOperation("handler cannot change match_id")
            if candidate_state.get("definition_manifest") != current_state.get("definition_manifest"):
                raise InvalidOperation("DefinitionManifest is immutable during a match")
            if candidate_state.get("schema_version") != 7:
                raise InvalidOperation("handler cannot change schema_version")

            candidate_runtime = copy.deepcopy(
                handler_result.runtime_state if handler_result.runtime_state is not None else current_runtime
            )
            _validate_match_runtime(candidate_runtime, list(current_state["players"].keys()))

            if handler_result.outcome == "rejected":
                if candidate_state != current_state or candidate_runtime != current_runtime or handler_result.events or handler_result.rewards or handler_result.outbox:
                    raise InvalidOperation("rejected operation cannot mutate state/runtime or emit events/rewards/outbox")
                if handler_result.costs:
                    raise InvalidOperation("rejected operation cannot consume costs")
                result = self._make_result(
                    operation_id,
                    "rejected",
                    current_revision,
                    current_revision,
                    target_results=handler_result.target_results,
                    costs={},
                    reason_code=handler_result.reason_code or "action_rejected",
                )
                self._insert_operation(
                    conn,
                    match_id,
                    operation_id,
                    fingerprint,
                    request,
                    current_revision,
                    current_revision,
                    result,
                )
                conn.commit()
                return OperationReceipt(result)

            next_sequence = int(match_row["event_watermark"])
            prepared_events = self._prepare_events(
                conn,
                match_id,
                operation_id,
                next_sequence,
                handler_result.events,
            )
            prepared_outbox = self._prepare_outbox(handler_result.outbox, operation_id)
            prepared_rewards = self._prepare_rewards(handler_result.rewards, operation_id)

            # The event watermark lives in the snapshot as a checkpoint, while
            # the append-only event table remains the durable source of truth.
            candidate_state = copy.deepcopy(candidate_state)
            candidate_state["event_watermark"] = next_sequence + len(prepared_events)
            before_for_comparison = copy.deepcopy(current_state)
            before_for_comparison.pop("state_revision", None)
            candidate_for_comparison = copy.deepcopy(candidate_state)
            candidate_for_comparison.pop("state_revision", None)
            changed = (
                _canonical_text(before_for_comparison)
                != _canonical_text(candidate_for_comparison)
                or bool(prepared_events)
                or bool(prepared_rewards)
                or bool(prepared_outbox)
                or candidate_runtime != current_runtime
            )
            if _has_consumed_cost(handler_result.costs) and not changed:
                raise InvalidOperation("consumed costs must be reflected in the committed state, events, rewards or outbox")
            next_revision = current_revision + 1 if changed else current_revision
            candidate_state["state_revision"] = next_revision
            validate_match_state(candidate_state)

            result = self._make_result(
                operation_id,
                handler_result.outcome,
                current_revision,
                next_revision,
                target_results=handler_result.target_results,
                costs=handler_result.costs,
                event_ids=[event["event_id"] for event in prepared_events],
                reason_code=handler_result.reason_code,
            )

            if changed:
                cursor = conn.execute(
                    "UPDATE cartas_gwent_matches SET status=?,state_json=?,state_revision=?,"
                    "event_watermark=?,updated_at=? WHERE match_id=? AND state_revision=?",
                    (
                        candidate_state["status"],
                        _canonical_text(candidate_state),
                        next_revision,
                        candidate_state["event_watermark"],
                        _utc_now(),
                        match_id,
                        current_revision,
                    ),
                )
                if cursor.rowcount != 1:
                    raise PersistenceConflict("compare-and-swap failed; no state was committed")
                runtime_cursor = conn.execute(
                    "UPDATE card_engine_v2_match_runtime SET runtime_json=?,state_revision=?,updated_at=? "
                    "WHERE match_id=? AND state_revision=?",
                    (_canonical_text(candidate_runtime), next_revision, _utc_now(), match_id, current_revision),
                )
                if runtime_cursor.rowcount != 1:
                    raise PersistenceConflict("gameplay runtime compare-and-swap failed; no state was committed")

            self._insert_operation(
                conn,
                match_id,
                operation_id,
                fingerprint,
                request,
                current_revision,
                next_revision,
                result,
            )
            self._insert_events(conn, match_id, operation_id, prepared_events)
            self._insert_rewards(conn, match_id, operation_id, prepared_rewards)
            self._insert_outbox(conn, match_id, operation_id, prepared_outbox)
            conn.commit()
            return OperationReceipt(result)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _make_result(
        operation_id: str,
        outcome: str,
        revision_before: int,
        revision_after: int,
        *,
        target_results: list[dict[str, Any]] | None = None,
        costs: dict[str, Any] | None = None,
        event_ids: list[str] | None = None,
        reason_code: str | None = None,
    ) -> dict[str, Any]:
        normalized_costs: dict[str, Any] = {
            "turn_consumed": False,
            "source_consumed": False,
            "activation_consumed": False,
            "protection_grants_consumed": [],
            "other_costs": [],
        }
        if costs:
            normalized_costs.update(copy.deepcopy(costs))
        result: dict[str, Any] = {
            "schema_version": 1,
            "operation_id": operation_id,
            "outcome": outcome,
            "revision_before": revision_before,
            "revision_after": revision_after,
            "target_results": target_results or [],
            "costs": normalized_costs,
            "event_ids": event_ids or [],
        }
        if reason_code:
            result["reason_code"] = reason_code
        return result

    def _insert_operation(
        self,
        conn: sqlite3.Connection,
        match_id: int,
        operation_id: str,
        fingerprint: str,
        request: dict[str, Any],
        revision_before: int,
        revision_after: int,
        result: dict[str, Any],
    ) -> None:
        conn.execute(
            "INSERT INTO cartas_gwent_match_operations"
            "(match_id,operation_id,fingerprint_sha256,actor_json,expected_revision,revision_before,"
            "revision_after,outcome,result_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                match_id,
                operation_id,
                fingerprint,
                _canonical_text(request["actor"]),
                request["expected_revision"],
                revision_before,
                revision_after,
                result["outcome"],
                _canonical_text(result),
                _utc_now(),
            ),
        )

    def _prepare_events(
        self,
        conn: sqlite3.Connection,
        match_id: int,
        operation_id: str,
        previous_sequence: int,
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not isinstance(events, list):
            raise InvalidOperation("events must be a list")
        prepared: list[dict[str, Any]] = []
        known_ids: set[str] = set()
        for offset, source in enumerate(events, start=1):
            if not isinstance(source, dict):
                raise InvalidOperation("each event must be an object")
            event = copy.deepcopy(source)
            event_id = event.get("event_id") or str(uuid.uuid4())
            if not isinstance(event_id, str) or not event_id:
                raise InvalidOperation("event_id must be a non-empty string")
            event["event_id"] = event_id
            event["operation_id"] = operation_id
            event["sequence"] = previous_sequence + offset
            event.setdefault("caused_by_event_ids", [])
            event.setdefault("source_effect_id", None)
            event.setdefault("source_instance_id", None)
            event.setdefault("target_instance_ids", [])
            event.setdefault("payload", {})
            _validate_event(event)
            _canonical_text(event)
            if not is_uuid4(event_id):
                raise InvalidOperation("event_id must be UUIDv4")
            if event_id in known_ids:
                raise InvalidOperation("duplicate event_id within operation")
            known_ids.add(event_id)
            prepared.append(event)

        current_operation_positions = {
            event["event_id"]: event["sequence"] for event in prepared
        }
        for event in prepared:
            for parent_id in event["caused_by_event_ids"]:
                if parent_id in current_operation_positions:
                    if current_operation_positions[parent_id] >= event["sequence"]:
                        raise InvalidOperation("causal parents must precede their child event")
                    continue
                found = conn.execute(
                    "SELECT 1 FROM cartas_gwent_match_events WHERE match_id=? AND event_id=?",
                    (match_id, parent_id),
                ).fetchone()
                if found is None:
                    raise InvalidOperation(f"causal parent event not found: {parent_id}")
        return prepared

    @staticmethod
    def _prepare_rewards(rewards: list[dict[str, Any]], operation_id: str) -> list[dict[str, Any]]:
        if not isinstance(rewards, list):
            raise InvalidOperation("rewards must be a list")
        prepared: list[dict[str, Any]] = []
        for reward in rewards:
            if not isinstance(reward, dict):
                raise InvalidOperation("reward must be an object")
            player_id = str(reward.get("player_id", ""))
            reward_key = reward.get("reward_key")
            reward_type = reward.get("reward_type")
            amount = reward.get("amount")
            if not player_id or not isinstance(reward_key, str) or not reward_key:
                raise InvalidOperation("reward requires player_id and reward_key")
            if not isinstance(reward_type, str) or not reward_type:
                raise InvalidOperation("reward_type is required")
            if not isinstance(amount, int) or isinstance(amount, bool):
                raise InvalidOperation("reward amount must be an integer")
            prepared.append(
                {
                    "reward_id": str(uuid.uuid4()),
                    "player_id": player_id,
                    "reward_key": reward_key,
                    "reward_type": reward_type,
                    "amount": amount,
                    "operation_id": operation_id,
                }
            )
        return prepared

    @staticmethod
    def _prepare_outbox(outbox_items: list[dict[str, Any]], operation_id: str) -> list[dict[str, Any]]:
        if not isinstance(outbox_items, list):
            raise InvalidOperation("outbox must be a list")
        prepared: list[dict[str, Any]] = []
        for item in outbox_items:
            if not isinstance(item, dict):
                raise InvalidOperation("outbox item must be an object")
            topic = item.get("topic")
            idempotency_key = item.get("idempotency_key")
            payload = item.get("payload")
            if not isinstance(topic, str) or not topic:
                raise InvalidOperation("outbox topic is required")
            if not isinstance(idempotency_key, str) or not idempotency_key:
                raise InvalidOperation("outbox idempotency_key is required")
            if not isinstance(payload, dict):
                raise InvalidOperation("outbox payload must be an object")
            _canonical_text(payload)
            prepared.append(
                {
                    "outbox_id": str(uuid.uuid4()),
                    "operation_id": operation_id,
                    "source_event_id": item.get("source_event_id"),
                    "topic": topic,
                    "idempotency_key": idempotency_key,
                    "payload": payload,
                }
            )
        return prepared

    def _insert_events(
        self,
        conn: sqlite3.Connection,
        match_id: int,
        operation_id: str,
        events: list[dict[str, Any]],
    ) -> None:
        now = _utc_now()
        for event in events:
            conn.execute(
                "INSERT INTO cartas_gwent_match_events"
                "(event_id,match_id,operation_id,sequence,kind,effect_scope,source_effect_id,"
                "source_instance_id,target_instance_ids_json,caused_by_event_ids_json,payload_json,created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    event["event_id"],
                    match_id,
                    operation_id,
                    event["sequence"],
                    event["kind"],
                    event["effect_scope"],
                    event["source_effect_id"],
                    event["source_instance_id"],
                    _canonical_text(event["target_instance_ids"]),
                    _canonical_text(event["caused_by_event_ids"]),
                    _canonical_text(event["payload"]),
                    now,
                ),
            )

    def _insert_rewards(
        self,
        conn: sqlite3.Connection,
        match_id: int,
        operation_id: str,
        rewards: list[dict[str, Any]],
    ) -> None:
        now = _utc_now()
        for reward in rewards:
            conn.execute(
                "INSERT INTO cartas_gwent_match_rewards"
                "(reward_id,match_id,operation_id,player_id,reward_key,reward_type,amount,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (
                    reward["reward_id"],
                    match_id,
                    operation_id,
                    reward["player_id"],
                    reward["reward_key"],
                    reward["reward_type"],
                    reward["amount"],
                    now,
                ),
            )

    def _insert_outbox(
        self,
        conn: sqlite3.Connection,
        match_id: int,
        operation_id: str,
        outbox_items: list[dict[str, Any]],
    ) -> None:
        now = _utc_now()
        for item in outbox_items:
            conn.execute(
                "INSERT INTO cartas_gwent_outbox"
                "(outbox_id,match_id,operation_id,source_event_id,topic,idempotency_key,payload_json,"
                "status,attempt_count,next_attempt_at,created_at) VALUES(?,?,?,?,?,?,?,'pending',0,?,?)",
                (
                    item["outbox_id"],
                    match_id,
                    operation_id,
                    item["source_event_id"],
                    item["topic"],
                    item["idempotency_key"],
                    _canonical_text(item["payload"]),
                    now,
                    now,
                ),
            )

    def get_events(self, match_id: int, *, after_sequence: int = 0) -> list[dict[str, Any]]:
        with self._managed_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM cartas_gwent_match_events WHERE match_id=? AND sequence>? ORDER BY sequence",
                (match_id, after_sequence),
            ).fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "event_id": row["event_id"],
                    "operation_id": row["operation_id"],
                    "sequence": row["sequence"],
                    "kind": row["kind"],
                    "effect_scope": row["effect_scope"],
                    "source_effect_id": row["source_effect_id"],
                    "source_instance_id": row["source_instance_id"],
                    "target_instance_ids": _parse_json(row["target_instance_ids_json"]),
                    "caused_by_event_ids": _parse_json(row["caused_by_event_ids_json"]),
                    "payload": _parse_json(row["payload_json"]),
                }
            )
        return result

    def get_operation(self, match_id: int, operation_id: str) -> dict[str, Any] | None:
        with self._managed_connection() as conn:
            row = conn.execute(
                "SELECT result_json FROM cartas_gwent_match_operations WHERE match_id=? AND operation_id=?",
                (match_id, operation_id),
            ).fetchone()
        return _parse_json(row["result_json"]) if row else None

    def list_rewards(self, match_id: int) -> list[dict[str, Any]]:
        with self._managed_connection() as conn:
            rows = conn.execute(
                "SELECT player_id,reward_key,reward_type,amount,operation_id FROM cartas_gwent_match_rewards "
                "WHERE match_id=? ORDER BY created_at,reward_key",
                (match_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def claim_outbox(
        self,
        *,
        limit: int = 20,
        lease_seconds: int = 60,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if limit < 1 or lease_seconds < 1:
            raise ValueError("limit and lease_seconds must be positive")
        moment = now or datetime.now(timezone.utc)
        now_text = moment.astimezone(timezone.utc).isoformat(timespec="microseconds")
        lease_until = (moment + timedelta(seconds=lease_seconds)).astimezone(timezone.utc).isoformat(
            timespec="microseconds"
        )
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                "SELECT outbox_id FROM cartas_gwent_outbox "
                "WHERE (status='pending' AND next_attempt_at<=?) "
                "OR (status='in_flight' AND lease_until<=?) "
                "ORDER BY created_at,outbox_id LIMIT ?",
                (now_text, now_text, limit),
            ).fetchall()
            claimed: list[dict[str, Any]] = []
            for row in rows:
                outbox_id = row["outbox_id"]
                conn.execute(
                    "UPDATE cartas_gwent_outbox SET status='in_flight',attempt_count=attempt_count+1,"
                    "lease_until=? WHERE outbox_id=?",
                    (lease_until, outbox_id),
                )
                updated = conn.execute(
                    "SELECT * FROM cartas_gwent_outbox WHERE outbox_id=?", (outbox_id,)
                ).fetchone()
                claimed.append(
                    {
                        "outbox_id": updated["outbox_id"],
                        "topic": updated["topic"],
                        "idempotency_key": updated["idempotency_key"],
                        "payload": _parse_json(updated["payload_json"]),
                        "attempt_count": updated["attempt_count"],
                        "lease_until": updated["lease_until"],
                    }
                )
            conn.commit()
            return claimed
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def mark_outbox_delivered(self, outbox_id: str, *, now: datetime | None = None) -> None:
        delivered_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(
            timespec="microseconds"
        )
        with self._managed_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                "UPDATE cartas_gwent_outbox SET status='delivered',delivered_at=?,lease_until=NULL "
                "WHERE outbox_id=? AND status='in_flight'",
                (delivered_at, outbox_id),
            )
            if cursor.rowcount != 1:
                conn.rollback()
                raise OutboxStateError("outbox item is missing or not in_flight")
            conn.commit()

    def fail_outbox(
        self,
        outbox_id: str,
        error: str,
        *,
        next_attempt_at: datetime,
        max_attempts: int = 8,
    ) -> str:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT attempt_count,status FROM cartas_gwent_outbox WHERE outbox_id=?",
                (outbox_id,),
            ).fetchone()
            if row is None or row["status"] != "in_flight":
                raise OutboxStateError("outbox item is missing or not in_flight")
            new_status = "dead_letter" if row["attempt_count"] >= max_attempts else "pending"
            next_text = next_attempt_at.astimezone(timezone.utc).isoformat(timespec="microseconds")
            conn.execute(
                "UPDATE cartas_gwent_outbox SET status=?,next_attempt_at=?,lease_until=NULL,last_error=? "
                "WHERE outbox_id=?",
                (new_status, next_text, str(error)[:2000], outbox_id),
            )
            conn.commit()
            return new_status
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def archive_legacy_snapshot(
        self,
        *,
        legacy_match_id: int,
        source_state_json: str,
        occurrences: list[dict[str, Any]],
        target_schema_version: int = 7,
        migration_id: str = "legacy_snapshot_to_card_instance_v7",
    ) -> dict[str, Any]:
        """Archive an exact source snapshot and assign each occurrence one UUIDv4.

        This is a controlled migration primitive only. It does not read the
        legacy production database or convert a live match. Repeating the same
        (match id, source hash) returns the already-persisted mapping.
        """
        try:
            parsed_source = json.loads(source_state_json)
        except json.JSONDecodeError as exc:
            raise InvalidOperation("legacy source state_json is invalid JSON") from exc
        if not isinstance(parsed_source, (dict, list)):
            raise InvalidOperation("legacy source snapshot must be a JSON object or array")
        if not isinstance(occurrences, list):
            raise InvalidOperation("occurrences must be a list")
        source_hash = sha256_text(source_state_json)
        locators: set[str] = set()
        exemplar_ids: set[int] = set()
        normalized: list[dict[str, Any]] = []
        for occurrence in occurrences:
            if not isinstance(occurrence, dict):
                raise InvalidOperation("legacy occurrence must be an object")
            locator = occurrence.get("legacy_locator")
            card_id = occurrence.get("card_id")
            owner = occurrence.get("owner_player_id")
            zone = occurrence.get("zone")
            if (
                not isinstance(locator, str)
                or not locator
                or not isinstance(card_id, str)
                or not card_id
                or owner is None
                or not str(owner)
            ):
                raise InvalidOperation("legacy occurrence requires locator, card_id and owner")
            if locator in locators:
                raise InvalidOperation(f"duplicate legacy_locator: {locator}")
            locators.add(locator)
            if zone not in ("hand", "draw_pile", "board", "discard"):
                raise InvalidOperation(f"invalid legacy zone: {zone}")
            exemplar_id = occurrence.get("exemplar_id")
            if exemplar_id is not None and (
                not isinstance(exemplar_id, int) or isinstance(exemplar_id, bool) or exemplar_id <= 0
            ):
                raise InvalidOperation("legacy exemplar_id must be a positive integer or null")
            if exemplar_id is not None and exemplar_id in exemplar_ids:
                raise InvalidOperation(f"duplicate exemplar_id in legacy match: {exemplar_id}")
            if exemplar_id is not None:
                exemplar_ids.add(exemplar_id)
            normalized.append(
                {
                    "legacy_locator": locator,
                    "card_id": card_id,
                    "owner_player_id": str(owner),
                    "zone": zone,
                    "exemplar_id": exemplar_id,
                    "origin_type": "deck_exemplar" if exemplar_id is not None else "legacy_unknown",
                }
            )

        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT archive_id,occurrence_mapping_json FROM card_engine_v2_legacy_archive "
                "WHERE legacy_match_id=? AND source_sha256=?",
                (legacy_match_id, source_hash),
            ).fetchone()
            if existing:
                saved_mapping = _parse_json(existing["occurrence_mapping_json"])
                saved_inventory = [
                    {key: value for key, value in item.items() if key != "instance_id"}
                    for item in saved_mapping
                ]
                if saved_inventory != normalized:
                    raise InvalidOperation(
                        "legacy occurrence inventory changed for an already archived source snapshot"
                    )
                conn.commit()
                return {
                    "archive_id": existing["archive_id"],
                    "source_sha256": source_hash,
                    "mapping": saved_mapping,
                    "reused": True,
                }
            mapping = []
            for occurrence in normalized:
                item = dict(occurrence)
                item["instance_id"] = str(uuid.uuid4())
                mapping.append(item)
            archive_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO card_engine_v2_legacy_archive"
                "(archive_id,legacy_match_id,source_sha256,source_state_json,target_schema_version,"
                "migration_id,occurrence_mapping_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (
                    archive_id,
                    legacy_match_id,
                    source_hash,
                    source_state_json,
                    target_schema_version,
                    migration_id,
                    _canonical_text(mapping),
                    _utc_now(),
                ),
            )
            conn.commit()
            return {"archive_id": archive_id, "source_sha256": source_hash, "mapping": mapping, "reused": False}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_verified_backup(self, target_path: str | os.PathLike[str]) -> dict[str, Any]:
        """Create a SQLite Backup API copy, verify it, and return SHA-256/counts."""
        target = Path(target_path).expanduser().resolve()
        if target == self.database_path:
            raise ValueError("backup target must differ from source database")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(f"refusing to overwrite backup: {target}")
        source = self._connect()
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
            quick = destination.execute("PRAGMA quick_check").fetchone()[0]
            integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
            if quick != "ok" or integrity != "ok":
                raise sqlite3.DatabaseError(f"backup integrity failed: quick={quick}, integrity={integrity}")
            tables = [
                "cartas_gwent_matches",
                "cartas_gwent_match_operations",
                "cartas_gwent_match_events",
                "cartas_gwent_match_rewards",
                "cartas_gwent_outbox",
                "card_engine_v2_legacy_archive",
            ]
            counts = {
                table: int(destination.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in tables
            }
            match_counts_by_status = {
                row[0]: int(row[1])
                for row in destination.execute(
                    "SELECT status,COUNT(*) FROM cartas_gwent_matches GROUP BY status"
                ).fetchall()
            }
        except Exception:
            destination.close()
            source.close()
            if target.exists():
                target.unlink()
            raise
        destination.close()
        source.close()
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        return {
            "path": str(target),
            "sha256": digest,
            "quick_check": quick,
            "integrity_check": integrity,
            "row_counts": counts,
            "match_counts_by_status": match_counts_by_status,
        }

    def verify_integrity(self) -> dict[str, Any]:
        with self._managed_connection() as conn:
            quick = conn.execute("PRAGMA quick_check").fetchone()[0]
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
            match_rows = conn.execute(
                "SELECT match_id,state_json,state_revision,event_watermark "
                "FROM cartas_gwent_matches ORDER BY match_id"
            ).fetchall()
            state_revision_violations = 0
            event_sequence_violations = 0
            for match_row in match_rows:
                snapshot = _parse_json(match_row["state_json"])
                if snapshot.get("state_revision") != match_row["state_revision"]:
                    state_revision_violations += 1
                if snapshot.get("event_watermark") != match_row["event_watermark"]:
                    event_sequence_violations += 1
                event_sequences = [
                    int(row[0]) for row in conn.execute(
                        "SELECT sequence FROM cartas_gwent_match_events WHERE match_id=? ORDER BY sequence",
                        (match_row["match_id"],),
                    ).fetchall()
                ]
                expected_sequences = list(range(1, int(match_row["event_watermark"]) + 1))
                if event_sequences != expected_sequences:
                    event_sequence_violations += 1
            counts = {
                table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in (
                    "cartas_gwent_matches",
                    "cartas_gwent_match_operations",
                    "cartas_gwent_match_events",
                    "cartas_gwent_match_rewards",
                    "cartas_gwent_outbox",
                    "card_engine_v2_legacy_archive",
                )
            }
        return {
            "quick_check": quick,
            "integrity_check": integrity,
            "foreign_key_violations": len(foreign_keys),
            "state_revision_violations": state_revision_violations,
            "event_sequence_violations": event_sequence_violations,
            "row_counts": counts,
            "ok": (
                quick == "ok"
                and integrity == "ok"
                and not foreign_keys
                and state_revision_violations == 0
                and event_sequence_violations == 0
            ),
        }
