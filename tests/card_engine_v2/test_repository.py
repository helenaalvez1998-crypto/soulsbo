from __future__ import annotations

import copy
import json
import sqlite3
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sistemas.card_engine_v2 import (
    HandlerResult,
    IdempotencyConflict,
    InvalidMatchState,
    InvalidOperation,
    MigrationChecksumMismatch,
    OutboxStateError,
    SQLiteMatchRepository,
    locate_instance,
    move_instance_row,
    transition_instance_zone,
)
from sistemas.card_engine_v2.models import make_card_instance, new_instance_id
from sistemas.card_engine_v2.validation import validate_match_state

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = ROOT / "docs" / "examples" / "card-instance-match.example.v7.json"


def uuid4() -> str:
    return str(uuid.uuid4())


def sample_state() -> dict:
    state = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    state["state_revision"] = 0
    state["event_watermark"] = 0
    return state


def request(*, operation_id: str | None = None, expected_revision: int = 0, amount: int = 1) -> dict:
    return {
        "operation_id": operation_id or uuid4(),
        "actor": {"type": "player", "player_id": "1001"},
        "expected_revision": expected_revision,
        "action_type": "test.increment_counter",
        "payload": {"amount": amount},
    }


def increment_handler(state: dict, req: dict) -> HandlerResult:
    state["players"]["1001"]["counters"]["board_removal_count"] += req["payload"]["amount"]
    return HandlerResult(
        outcome="applied",
        state=state,
        costs={"turn_consumed": True},
    )


def event_handler(state: dict, req: dict) -> HandlerResult:
    state["players"]["1001"]["counters"]["board_removal_count"] += 1
    removed_id = "00000000-0000-4000-8000-000000000002"
    state["players"]["2002"]["zones"]["board"].remove(removed_id)
    state["players"]["2002"]["zones"]["discard"].append(removed_id)
    state["instances"][removed_id]["state"]["current_row"] = None
    event_id = uuid4()
    return HandlerResult(
        outcome="applied",
        state=state,
        events=[
            {
                "event_id": event_id,
                "kind": "unit_removed",
                "effect_scope": "direct",
                "source_effect_id": "special.remove_units",
                "source_instance_id": "00000000-0000-4000-8000-000000000005",
                "target_instance_ids": [removed_id],
                "caused_by_event_ids": [],
                "payload": {
                    "cause_id": "normal_removal",
                    "from_zone": "board",
                    "to_zone": "discard",
                    "affected_player_id": "2002",
                },
            }
        ],
        rewards=[
            {"player_id": "1001", "reward_key": "win-token-1", "reward_type": "test_token", "amount": 3}
        ],
        outbox=[
            {
                "topic": "turn_notification",
                "idempotency_key": f"turn:{req['operation_id']}",
                "source_event_id": event_id,
                "payload": {"match_id": state["match_id"], "next_player_id": "2002"},
            }
        ],
        costs={"turn_consumed": True, "source_consumed": True},
    )


class CardEngineV2RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "engine-v2.sqlite3"
        self.repo = SQLiteMatchRepository(self.db_path)
        self.repo.create_match(sample_state())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_create_match_and_revision_envelope(self) -> None:
        state = self.repo.get_match(2026112701)
        self.assertEqual(state["schema_version"], 7)
        self.assertEqual(state["state_revision"], 0)
        self.assertEqual(state["event_watermark"], 0)
        self.assertNotIn("operations", state)
        self.assertNotIn("events", state)

    def test_idempotent_replay_does_not_call_handler_twice(self) -> None:
        req = request()
        calls = 0

        def handler(state: dict, body: dict) -> HandlerResult:
            nonlocal calls
            calls += 1
            return increment_handler(state, body)

        first = self.repo.execute_operation(2026112701, req, handler)
        second = self.repo.execute_operation(2026112701, req, handler)
        self.assertEqual(first.result["revision_after"], 1)
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.result, second.result)
        self.assertEqual(calls, 1)
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 1)

    def test_same_operation_id_different_fingerprint_conflicts(self) -> None:
        op_id = uuid4()
        self.repo.execute_operation(2026112701, request(operation_id=op_id), increment_handler)
        changed = request(operation_id=op_id, amount=2)
        with self.assertRaises(IdempotencyConflict):
            self.repo.execute_operation(2026112701, changed, increment_handler)
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 1)

    def test_stale_revision_is_durably_rejected_without_revision_increment(self) -> None:
        self.repo.execute_operation(2026112701, request(), increment_handler)
        stale = request(expected_revision=0)
        receipt = self.repo.execute_operation(2026112701, stale, increment_handler)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "revision_conflict")
        self.assertEqual(receipt.result["revision_before"], 1)
        self.assertEqual(receipt.result["revision_after"], 1)
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 1)
        self.assertIsNotNone(self.repo.get_operation(2026112701, stale["operation_id"]))

    def test_handler_rejection_is_recorded_without_gameplay_mutation(self) -> None:
        req = request()

        def rejected(state: dict, body: dict) -> HandlerResult:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_target")

        result = self.repo.execute_operation(2026112701, req, rejected).result
        self.assertEqual(result["outcome"], "rejected")
        self.assertEqual(result["revision_before"], result["revision_after"])
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)
        self.assertIsNotNone(self.repo.get_operation(2026112701, req["operation_id"]))

    def test_handler_exception_rolls_back_and_does_not_reserve_operation_id(self) -> None:
        req = request()

        def broken(state: dict, body: dict) -> HandlerResult:
            state["players"]["1001"]["counters"]["board_removal_count"] += 1
            raise RuntimeError("simulated failure")

        with self.assertRaises(RuntimeError):
            self.repo.execute_operation(2026112701, req, broken)
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)
        self.assertIsNone(self.repo.get_operation(2026112701, req["operation_id"]))
        self.repo.execute_operation(2026112701, req, increment_handler)
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 1)

    def test_snapshot_events_rewards_and_outbox_commit_atomically(self) -> None:
        receipt = self.repo.execute_operation(2026112701, request(), event_handler)
        state = self.repo.get_match(2026112701)
        events = self.repo.get_events(2026112701)
        rewards = self.repo.list_rewards(2026112701)
        self.assertEqual(state["state_revision"], 1)
        self.assertEqual(state["event_watermark"], 1)
        self.assertEqual(events[0]["kind"], "unit_removed")
        self.assertEqual(events[0]["sequence"], 1)
        self.assertEqual(receipt.result["event_ids"], [events[0]["event_id"]])
        self.assertEqual(len(rewards), 1)
        self.assertEqual(rewards[0]["amount"], 3)
        claimed = self.repo.claim_outbox(now=datetime.now(timezone.utc) + timedelta(seconds=1))
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0]["topic"], "turn_notification")

    def test_atomic_rollback_on_duplicate_reward_key(self) -> None:
        self.repo.execute_operation(2026112701, request(), event_handler)
        before = self.repo.get_match(2026112701)
        second = request(expected_revision=1)

        def duplicate_reward(state: dict, body: dict) -> HandlerResult:
            state["players"]["1001"]["counters"]["board_removal_count"] += 5
            return HandlerResult(
                outcome="applied",
                state=state,
                rewards=[
                    {"player_id": "1001", "reward_key": "win-token-1", "reward_type": "test_token", "amount": 9}
                ],
            )

        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.execute_operation(2026112701, second, duplicate_reward)
        after = self.repo.get_match(2026112701)
        self.assertEqual(after, before)
        self.assertIsNone(self.repo.get_operation(2026112701, second["operation_id"]))

    def test_rejected_operation_does_not_advance_event_watermark(self) -> None:
        req = request()

        def blocked(state: dict, body: dict) -> HandlerResult:
            return HandlerResult(outcome="rejected", state=state, reason_code="forbidden")

        self.repo.execute_operation(2026112701, req, blocked)
        state = self.repo.get_match(2026112701)
        self.assertEqual(state["state_revision"], 0)
        self.assertEqual(state["event_watermark"], 0)
        self.assertEqual(self.repo.get_events(2026112701), [])

    def test_append_only_event_trigger_rejects_mutation(self) -> None:
        self.repo.execute_operation(2026112701, request(), event_handler)
        conn = sqlite3.connect(self.db_path)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE cartas_gwent_match_events SET kind='tampered' WHERE sequence=1")
            conn.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM cartas_gwent_match_events WHERE sequence=1")
            conn.rollback()
        finally:
            conn.close()

    def test_outbox_retry_then_dead_letter(self) -> None:
        self.repo.execute_operation(2026112701, request(), event_handler)
        now = datetime.now(timezone.utc) + timedelta(minutes=1)
        first = self.repo.claim_outbox(now=now)[0]
        status = self.repo.fail_outbox(
            first["outbox_id"], "network down", next_attempt_at=now + timedelta(seconds=1), max_attempts=2
        )
        self.assertEqual(status, "pending")
        second = self.repo.claim_outbox(now=now + timedelta(seconds=2))[0]
        self.assertEqual(second["attempt_count"], 2)
        status = self.repo.fail_outbox(
            second["outbox_id"], "still down", next_attempt_at=now + timedelta(seconds=3), max_attempts=2
        )
        self.assertEqual(status, "dead_letter")
        self.assertEqual(self.repo.claim_outbox(now=now + timedelta(hours=1)), [])

    def test_outbox_requires_in_flight_before_delivered(self) -> None:
        self.repo.execute_operation(2026112701, request(), event_handler)
        conn = sqlite3.connect(self.db_path)
        try:
            outbox_id = conn.execute("SELECT outbox_id FROM cartas_gwent_outbox").fetchone()[0]
        finally:
            conn.close()
        with self.assertRaises(OutboxStateError):
            self.repo.mark_outbox_delivered(outbox_id)
        claimed = self.repo.claim_outbox(now=datetime.now(timezone.utc) + timedelta(seconds=1))[0]
        self.repo.mark_outbox_delivered(claimed["outbox_id"])
        with self.assertRaises(OutboxStateError):
            self.repo.mark_outbox_delivered(claimed["outbox_id"])

    def test_migration_is_idempotent_and_checksum_protected(self) -> None:
        self.assertEqual(self.repo.apply_migrations(), [])
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE card_game_schema_migrations SET checksum_sha256=? WHERE migration_id=?",
                ("0" * 64, "0001_card_engine_v2_persistence_core"),
            )
            conn.commit()
        finally:
            conn.close()
        with self.assertRaises(MigrationChecksumMismatch):
            SQLiteMatchRepository(self.db_path)

    def test_backup_api_returns_verified_hash_and_counts(self) -> None:
        self.repo.execute_operation(2026112701, request(), event_handler)
        backup = self.repo.create_verified_backup(Path(self.temp.name) / "verified-copy.sqlite3")
        self.assertEqual(backup["quick_check"], "ok")
        self.assertEqual(backup["integrity_check"], "ok")
        self.assertEqual(len(backup["sha256"]), 64)
        self.assertEqual(backup["row_counts"]["cartas_gwent_match_events"], 1)
        self.assertTrue(backup["path"].endswith("verified-copy.sqlite3"))

    def test_legacy_archive_mapping_is_persisted_and_reused(self) -> None:
        raw = json.dumps({"old": "snapshot"}, separators=(",", ":"))
        occurrences = [
            {"legacy_locator": "board:0", "card_id": "wolf_guardian", "owner_player_id": 1001, "zone": "board", "exemplar_id": 77},
            {"legacy_locator": "discard:0", "card_id": "wolf_guardian", "owner_player_id": 1001, "zone": "discard"},
        ]
        first = self.repo.archive_legacy_snapshot(
            legacy_match_id=88, source_state_json=raw, occurrences=occurrences
        )
        second = self.repo.archive_legacy_snapshot(
            legacy_match_id=88, source_state_json=raw, occurrences=occurrences
        )
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        self.assertEqual(first["mapping"], second["mapping"])
        self.assertEqual(first["mapping"][0]["exemplar_id"], 77)
        self.assertIsNone(first["mapping"][1]["exemplar_id"])
        self.assertEqual(first["mapping"][1]["origin_type"], "legacy_unknown")
        self.assertTrue(all(len(item["instance_id"]) == 36 for item in first["mapping"]))

    def test_invalid_legacy_source_is_rejected(self) -> None:
        with self.assertRaises(InvalidOperation):
            self.repo.archive_legacy_snapshot(
                legacy_match_id=89, source_state_json="{not-json", occurrences=[]
            )

    def test_two_connections_same_expected_revision_one_wins_one_rejects(self) -> None:
        repo_a = SQLiteMatchRepository(self.db_path)
        repo_b = SQLiteMatchRepository(self.db_path)
        barrier = threading.Barrier(2)

        def slow_increment(state: dict, req: dict) -> HandlerResult:
            state["players"]["1001"]["counters"]["board_removal_count"] += 1
            return HandlerResult(outcome="applied", state=state)

        req_a = request()
        req_b = request()

        def run(repo: SQLiteMatchRepository, req: dict) -> str:
            barrier.wait(timeout=5)
            return repo.execute_operation(2026112701, req, slow_increment).result["outcome"]

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = [pool.submit(run, repo_a, req_a), pool.submit(run, repo_b, req_b)]
            results = [future.result(timeout=10) for future in outcomes]
        self.assertCountEqual(results, ["applied", "rejected"])
        state = self.repo.get_match(2026112701)
        self.assertEqual(state["state_revision"], 1)
        self.assertEqual(state["players"]["1001"]["counters"]["board_removal_count"], 1)
        self.assertIsNotNone(self.repo.get_operation(2026112701, req_a["operation_id"]))
        self.assertIsNotNone(self.repo.get_operation(2026112701, req_b["operation_id"]))

    def test_direct_removal_and_reactive_vengeance_events_keep_distinct_sources(self) -> None:
        req = request()
        direct_event_id = uuid4()
        vengeance_event_id = uuid4()
        victim_id = "00000000-0000-4000-8000-000000000004"
        survivor_id = "00000000-0000-4000-8000-000000000002"

        def handler(state: dict, body: dict) -> HandlerResult:
            opponent = state["players"]["2002"]["zones"]
            opponent["discard"].remove(victim_id)
            opponent["board"].append(victim_id)
            state["instances"][victim_id]["state"]["current_row"] = "melee"
            opponent["board"].remove(victim_id)
            opponent["discard"].append(victim_id)
            state["instances"][victim_id]["state"]["current_row"] = None
            state["players"]["2002"]["counters"]["board_removal_count"] += 1
            state["instances"][survivor_id]["state"]["bonus_grants"].append({
                "grant_id": uuid4(),
                "amount": 1,
                "source_effect_id": "effect.vengeance_on_removal",
                "source_instance_id": victim_id,
                "applied_event_id": vengeance_event_id,
                "expires_on": "round_close",
                "clamp_policy_id": "test.clamp.vengeance",
            })
            return HandlerResult(
                outcome="applied",
                state=state,
                events=[
                    {
                        "event_id": direct_event_id,
                        "kind": "unit_removed",
                        "effect_scope": "direct",
                        "source_effect_id": "special.test_removal",
                        "source_instance_id": None,
                        "target_instance_ids": [victim_id],
                        "caused_by_event_ids": [],
                        "payload": {
                            "cause_id": "normal_removal",
                            "from_zone": "board",
                            "to_zone": "discard",
                            "affected_player_id": "2002",
                        },
                    },
                    {
                        "event_id": vengeance_event_id,
                        "kind": "vengeance_bonus_applied",
                        "effect_scope": "reactive",
                        "source_effect_id": "effect.vengeance_on_removal",
                        "source_instance_id": victim_id,
                        "target_instance_ids": [survivor_id],
                        "caused_by_event_ids": [direct_event_id],
                        "payload": {"amount": 1, "expires_on": "round_close"},
                    },
                ],
            )

        receipt = self.repo.execute_operation(2026112701, req, handler)
        events = self.repo.get_events(2026112701)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual([e["sequence"] for e in events], [1, 2])
        self.assertEqual(events[0]["effect_scope"], "direct")
        self.assertEqual(events[1]["effect_scope"], "reactive")
        self.assertEqual(events[1]["source_effect_id"], "effect.vengeance_on_removal")
        self.assertEqual(events[1]["caused_by_event_ids"], [direct_event_id])
        self.assertEqual(events[0]["source_effect_id"], "special.test_removal")

    def test_missing_causal_parent_rolls_back_entire_operation(self) -> None:
        req = request()
        missing_parent_id = uuid4()

        def handler(state: dict, body: dict) -> HandlerResult:
            state["players"]["1001"]["counters"]["board_removal_count"] += 1
            return HandlerResult(
                outcome="applied",
                state=state,
                events=[{
                    "event_id": uuid4(),
                    "kind": "test_reactive_event",
                    "effect_scope": "reactive",
                    "source_effect_id": "effect.test_reaction",
                    "source_instance_id": None,
                    "target_instance_ids": [],
                    "caused_by_event_ids": [missing_parent_id],
                    "payload": {},
                }],
            )

        with self.assertRaises(InvalidOperation):
            self.repo.execute_operation(2026112701, req, handler)
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)
        self.assertEqual(self.repo.get_events(2026112701), [])
        self.assertIsNone(self.repo.get_operation(2026112701, req["operation_id"]))

    def test_snapshot_validation_rejects_duplicate_zone_placement(self) -> None:
        state = sample_state()
        repeated = "00000000-0000-4000-8000-000000000001"
        state["players"]["1001"]["zones"]["discard"].append(repeated)
        with self.assertRaises(InvalidMatchState):
            validate_match_state(state)

    def test_duplicate_card_models_are_allowed_but_instance_ids_are_not(self) -> None:
        state = sample_state()
        wolf_ids = [
            instance_id for instance_id, instance in state["instances"].items()
            if instance["card_id"] == "wolf_guardian"
        ]
        self.assertGreaterEqual(len(wolf_ids), 2)
        validate_match_state(state)
        duplicate = copy.deepcopy(state)
        duplicate["players"]["1001"]["zones"]["hand"].append(wolf_ids[0])
        with self.assertRaises(InvalidMatchState):
            validate_match_state(duplicate)

    def test_new_card_instance_factory_generates_uuid4(self) -> None:
        state = sample_state()
        definition = copy.deepcopy(next(iter(state["instances"].values()))["definition_snapshot"])
        instance = make_card_instance(
            card_id="wolf_guardian",
            owner_player_id=1001,
            origin_type="catalog_deck",
            definition_snapshot=definition,
            initial_row="melee",
        )
        self.assertTrue(uuid.UUID(instance["instance_id"]).version == 4)
        self.assertEqual(instance["schema_version"], 7)
        self.assertEqual(instance["exemplar_id"], None)
        self.assertEqual(new_instance_id() != instance["instance_id"], True)

    def test_exact_instance_zone_transition_preserves_grants_and_provenance(self) -> None:
        state = sample_state()
        instance_id = "00000000-0000-4000-8000-000000000003"
        before_grants = copy.deepcopy(state["instances"][instance_id]["state"]["protection_grants"])
        before_modifiers = copy.deepcopy(state["instances"][instance_id]["state"]["weather_resistance_modifiers"])
        transition = transition_instance_zone(state, instance_id, "discard")
        self.assertEqual(transition["from_zone"], "board")
        self.assertEqual(transition["to_zone"], "discard")
        self.assertEqual(locate_instance(state, instance_id), ("1001", "discard"))
        runtime = state["instances"][instance_id]["state"]
        self.assertIsNone(runtime["current_row"])
        self.assertEqual(runtime["last_board_row"], "ranged")
        self.assertEqual(runtime["protection_grants"], before_grants)
        self.assertEqual(runtime["weather_resistance_modifiers"], before_modifiers)
        validate_match_state(state)

    def test_invalid_zone_transition_position_does_not_mutate_state(self) -> None:
        state = sample_state()
        before = copy.deepcopy(state)
        instance_id = "00000000-0000-4000-8000-000000000003"
        with self.assertRaises(InvalidOperation):
            transition_instance_zone(state, instance_id, "discard", position=99)
        self.assertEqual(state, before)

    def test_row_move_updates_current_and_last_board_row(self) -> None:
        state = sample_state()
        instance_id = "00000000-0000-4000-8000-000000000003"
        result = move_instance_row(state, instance_id, "siege")
        self.assertEqual(result["from_row"], "ranged")
        self.assertEqual(result["to_row"], "siege")
        self.assertEqual(state["instances"][instance_id]["state"]["current_row"], "siege")
        self.assertEqual(state["instances"][instance_id]["state"]["last_board_row"], "siege")
        validate_match_state(state)

    def test_legacy_archive_rejects_changed_occurrence_inventory_for_same_source(self) -> None:
        raw = json.dumps({"old": "snapshot"}, separators=(",", ":"))
        original = [
            {"legacy_locator": "hand:0", "card_id": "wolf_guardian", "owner_player_id": 1001, "zone": "hand"}
        ]
        self.repo.archive_legacy_snapshot(legacy_match_id=90, source_state_json=raw, occurrences=original)
        changed = [
            {"legacy_locator": "hand:0", "card_id": "different_model", "owner_player_id": 1001, "zone": "hand"}
        ]
        with self.assertRaises(InvalidOperation):
            self.repo.archive_legacy_snapshot(legacy_match_id=90, source_state_json=raw, occurrences=changed)

    def test_consumed_cost_requires_a_persisted_effect(self) -> None:
        req = request()

        def inconsistent(state: dict, body: dict) -> HandlerResult:
            return HandlerResult(
                outcome="consumed_no_effect",
                state=state,
                costs={"turn_consumed": True},
            )

        with self.assertRaises(InvalidOperation):
            self.repo.execute_operation(2026112701, req, inconsistent)
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)
        self.assertIsNone(self.repo.get_operation(2026112701, req["operation_id"]))

    def test_legacy_archive_rejects_duplicate_exemplar_provenance(self) -> None:
        with self.assertRaises(InvalidOperation):
            self.repo.archive_legacy_snapshot(
                legacy_match_id=91,
                source_state_json='{"old":true}',
                occurrences=[
                    {"legacy_locator": "deck:0", "card_id": "a", "owner_player_id": 1, "zone": "draw_pile", "exemplar_id": 500},
                    {"legacy_locator": "deck:1", "card_id": "b", "owner_player_id": 1, "zone": "draw_pile", "exemplar_id": 500},
                ],
            )

    def test_refuses_non_empty_unmarked_sqlite_file(self) -> None:
        legacy_path = Path(self.temp.name) / "legacy-soulsbo.sqlite3"
        conn = sqlite3.connect(legacy_path)
        try:
            conn.execute("CREATE TABLE cartas_gwent_matches (id INTEGER PRIMARY KEY, state_json TEXT)")
            conn.execute("INSERT INTO cartas_gwent_matches(id,state_json) VALUES(1,'{}')")
            conn.commit()
        finally:
            conn.close()
        with self.assertRaisesRegex(ValueError, "non-empty unmarked"):
            SQLiteMatchRepository(legacy_path)
        conn = sqlite3.connect(legacy_path)
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM cartas_gwent_matches").fetchone()[0], 1)
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='card_engine_v2_database_marker'").fetchone()[0],
                0,
            )
        finally:
            conn.close()

    def test_integrity_report(self) -> None:
        report = self.repo.verify_integrity()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["foreign_key_violations"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
