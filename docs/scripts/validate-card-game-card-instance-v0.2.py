#!/usr/bin/env python3
"""Validate CardInstance v0.2 (approved Group A; other groups remain open).

Run from repository root:
    python docs/scripts/validate-card-game-card-instance-v0.2.py

Uses synthetic fixtures and reads database.py statically. Does not import or
modify game runtime, database, HTTP/API, Discord or frontend.
"""
from __future__ import annotations

import copy
import json
import re
import uuid
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SCHEMA_PATH = DOCS / "schemas/card-game-card-instance-match.schema.v2.json"
TARGET_SCHEMA_PATH = DOCS / "schemas/card-game-target-selection.schema.v1.json"
EXAMPLE_PATH = DOCS / "examples/card-instance-match.example.v2.json"
RESULT_PATH = DOCS / "card-game-card-instance-contract-validation-v0.2.json"

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
ZONES = ("hand", "draw_pile", "board", "discard")


class ContractError(ValueError):
    pass


def is_uuid4(value: Any) -> bool:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return parsed.version == 4 and parsed.variant == uuid.RFC_4122 and str(parsed) == value


def schema_errors(instance: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [e.message for e in sorted(validator.iter_errors(instance), key=lambda e: list(map(str, e.path)))]


def exemplar_rows() -> dict[int, dict[str, str]]:
    return {
        501: {"user_id": "1001", "card_id": "wolf_guardian"},
        503: {"user_id": "1001", "card_id": "golden_knight"},
        504: {"user_id": "2002", "card_id": "wolf_guardian"},
    }


def validate_semantics(match: dict[str, Any], rows: dict[int, dict[str, str]]) -> None:
    players = match.get("players")
    instances = match.get("instances")
    if not isinstance(players, dict) or len(players) < 2:
        raise ContractError("match requires at least two players")
    if not isinstance(instances, dict):
        raise ContractError("instances registry missing")

    locations: dict[str, list[tuple[str, str, int]]] = {}
    for player_id, player in players.items():
        zones = player.get("zones") if isinstance(player, dict) else None
        if not isinstance(zones, dict) or set(zones) != set(ZONES):
            raise ContractError(f"invalid zones for player {player_id}")
        for zone_name in ZONES:
            refs = zones[zone_name]
            if not isinstance(refs, list):
                raise ContractError(f"zone must be an ordered list: {player_id}/{zone_name}")
            if len(refs) != len(set(refs)):
                raise ContractError(f"duplicate reference inside zone: {player_id}/{zone_name}")
            for index, instance_id in enumerate(refs):
                locations.setdefault(instance_id, []).append((player_id, zone_name, index))

    used_exemplars: set[int] = set()
    for registry_key, card in instances.items():
        if not is_uuid4(registry_key) or card.get("instance_id") != registry_key:
            raise ContractError(f"invalid UUIDv4 or registry key mismatch: {registry_key}")
        if card.get("schema_version") != 2:
            raise ContractError(f"unexpected CardInstance schema version: {registry_key}")
        if card.get("owner_player_id") not in players:
            raise ContractError(f"owner is not a match participant: {registry_key}")
        definition = card.get("definition_snapshot") or {}
        if definition.get("card_id") != card.get("card_id"):
            raise ContractError(f"card_id differs from frozen definition snapshot: {registry_key}")
        origin = card.get("origin_type")
        exemplar_id = card.get("exemplar_id")
        if origin == "deck_exemplar":
            if not isinstance(exemplar_id, int) or isinstance(exemplar_id, bool) or exemplar_id <= 0:
                raise ContractError(f"deck_exemplar requires positive exemplar_id: {registry_key}")
        elif origin in {"catalog_deck", "generated_token", "equipped_relic_activation"}:
            if exemplar_id is not None:
                raise ContractError(f"origin {origin} must have null exemplar_id: {registry_key}")
        elif origin == "legacy_migration":
            if exemplar_id is not None and (not isinstance(exemplar_id, int) or isinstance(exemplar_id, bool) or exemplar_id <= 0):
                raise ContractError(f"invalid legacy exemplar_id: {registry_key}")
        else:
            raise ContractError(f"unknown origin_type: {origin}")

        if exemplar_id is not None:
            if exemplar_id in used_exemplars:
                raise ContractError(f"exemplar_id reused in match: {exemplar_id}")
            used_exemplars.add(exemplar_id)
            row = rows.get(exemplar_id)
            if row is None:
                raise ContractError(f"exemplar_id not proven in collection registry: {exemplar_id}")
            if str(row.get("user_id")) != card.get("owner_player_id"):
                raise ContractError(f"exemplar owner mismatch: {exemplar_id}")
            if row.get("card_id") != card.get("card_id"):
                raise ContractError(f"exemplar card_id mismatch: {exemplar_id}")

    # Every instance must be referenced exactly once; no unknown zone refs.
    if set(locations) != set(instances):
        missing = set(instances) - set(locations)
        unknown = set(locations) - set(instances)
        raise ContractError(f"registry/zone mismatch; orphan={sorted(missing)}, unknown={sorted(unknown)}")
    for instance_id, refs in locations.items():
        if len(refs) != 1:
            raise ContractError(f"instance appears in more than one zone: {instance_id}")
        player_id, zone_name, _index = refs[0]
        card = instances[instance_id]
        if card.get("owner_player_id") != player_id:
            raise ContractError(f"owner/zone mismatch: {instance_id}")
        if zone_name == "board" and (card.get("definition_snapshot") or {}).get("kind") != "unit":
            raise ContractError(f"only units may be in board: {instance_id}")


def choose_by_metric(candidates: list[dict[str, Any]], metric: str, strongest: bool = True) -> dict[str, Any]:
    if not candidates:
        raise ContractError("no eligible candidates")
    # The caller supplies zone_order from the persisted ordered candidate list.
    return sorted(candidates, key=lambda c: ((-c[metric]) if strongest else c[metric], c["zone_order"], c["instance_id"]))[0]


def must_reject(fn) -> bool:
    try:
        fn()
    except (ContractError, ValueError):
        return True
    return False


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    target_schema = json.loads(TARGET_SCHEMA_PATH.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    rows = exemplar_rows()
    cases: list[dict[str, Any]] = []

    def check(case_id: str, desc: str, passed: bool) -> None:
        cases.append({"id": case_id, "description": desc, "passed": bool(passed)})

    match_schema_ok = not schema_errors(example, schema)
    check("CI20-01", "v2 example validates against Draft 2020-12 match schema", match_schema_ok)
    target_single = {"schema_version": 1, "target_instance_id": "00000000-0000-4000-8000-000000000001"}
    target_multi = {"schema_version": 1, "target_instance_ids": ["00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000002"]}
    check("CI20-02", "single physical target uses target_instance_id", not schema_errors(target_single, target_schema))
    check("CI20-03", "multiple physical targets use unique target_instance_ids", not schema_errors(target_multi, target_schema))
    dup_multi = {"schema_version": 1, "target_instance_ids": [target_multi["target_instance_ids"][0], target_multi["target_instance_ids"][0]]}
    check("CI20-04", "duplicate target_instance_ids are rejected", bool(schema_errors(dup_multi, target_schema)))
    old_target = {"schema_version": 1, "target_id": "wolf_guardian"}
    check("CI20-05", "legacy target_id is not accepted by the new target selector schema", bool(schema_errors(old_target, target_schema)))
    both_forms = {"schema_version": 1, "target_instance_id": target_single["target_instance_id"], "target_instance_ids": target_multi["target_instance_ids"]}
    check("CI20-06", "single and multiple selector forms cannot be mixed", bool(schema_errors(both_forms, target_schema)))

    try:
        validate_semantics(example, rows)
        valid_semantics = True
    except ContractError:
        valid_semantics = False
    check("CI20-07", "example satisfies global identity, zone, ownership and provenance invariants", valid_semantics)

    ids = list(example["instances"])
    duplicate_models = [i for i in example["instances"].values() if i["card_id"] == "wolf_guardian"]
    check("CI20-08", "same card_id is valid across distinct physical instances", len(duplicate_models) == 3 and len({i["instance_id"] for i in duplicate_models}) == 3)
    check("CI20-09", "example assigns globally distinct exemplar IDs to collection-backed instances", len({i["exemplar_id"] for i in example["instances"].values() if i["exemplar_id"] is not None}) == 3)
    check("CI20-10", "ordered zone arrays preserve list order", example["players"]["1001"]["zones"]["board"] == [ids[2]])

    bad = copy.deepcopy(example)
    bad["instances"][ids[0]]["instance_id"] = ids[1]
    check("CI20-11", "registry key and embedded instance_id must match", must_reject(lambda: validate_semantics(bad, rows)))
    bad = copy.deepcopy(example)
    bad["players"]["2002"]["zones"]["hand"].append(ids[0])
    check("CI20-12", "one physical instance cannot occur in two zones", must_reject(lambda: validate_semantics(bad, rows)))
    bad = copy.deepcopy(example)
    bad["players"]["1001"]["zones"]["board"].remove(ids[2])
    check("CI20-13", "registry entries cannot be orphaned from all zones", must_reject(lambda: validate_semantics(bad, rows)))
    bad = copy.deepcopy(example)
    bad["instances"][ids[0]]["owner_player_id"] = "2002"
    check("CI20-14", "owner must match the participant whose zone contains the instance", must_reject(lambda: validate_semantics(bad, rows)))
    bad = copy.deepcopy(example)
    bad["instances"][ids[0]]["exemplar_id"] = 504
    check("CI20-15", "a collection exemplar cannot be reused and must match owner/model", must_reject(lambda: validate_semantics(bad, rows)))
    bad = copy.deepcopy(example)
    bad["instances"][ids[0]]["exemplar_id"] = 999999
    check("CI20-16", "unknown exemplar IDs are rejected", must_reject(lambda: validate_semantics(bad, rows)))
    bad = copy.deepcopy(example)
    bad["instances"][ids[1]]["exemplar_id"] = 999
    check("CI20-17", "generated token cannot claim collection provenance", bool(schema_errors(bad, schema)))
    bad = copy.deepcopy(example)
    bad["instances"][ids[0]]["definition_snapshot"]["card_id"] = "different_model"
    check("CI20-18", "instance card_id must match frozen definition snapshot", must_reject(lambda: validate_semantics(bad, rows)))
    bad = copy.deepcopy(example)
    bad["instances"][ids[0]]["instance_id"] = "wolf_guardian"
    check("CI20-19", "non-UUIDv4 instance IDs are rejected by schema", bool(schema_errors(bad, schema)))
    bad = copy.deepcopy(example)
    bad["instances"][ids[0]]["origin_type"] = "deck_exemplar"
    bad["instances"][ids[0]]["exemplar_id"] = None
    check("CI20-20", "deck_exemplar requires positive exemplar_id", bool(schema_errors(bad, schema)))
    bad = copy.deepcopy(example)
    # Non-unit in board is a semantic invariant (schema cannot look up instance kind by zone reference).
    bad["instances"][ids[2]]["definition_snapshot"]["kind"] = "special"
    bad["instances"][ids[2]]["definition_snapshot"]["printed_row"] = None
    bad["instances"][ids[2]]["definition_snapshot"]["power_base"] = None
    bad["instances"][ids[2]]["state"]["current_row"] = None
    check("CI20-21", "board rejects special/relic instances", must_reject(lambda: validate_semantics(bad, rows)))

    # Revalidate the approved Group A record and the static DB DDL evidence.
    approval = json.loads((DOCS / "card-game-identity-group-A-approval-v0.1.json").read_text(encoding="utf-8"))
    approved_ids = {d["id"] for d in approval["approved_decisions"]}
    expected = {"CI-001","CI-002","CI-003","CI-004","CI-006","CI-010","BUF-013","RSRX-09"}
    check("CI20-22", "owner approval record contains exactly the eight Group A decisions", approved_ids == expected and approval["metadata"]["status"] == "APPROVED_BY_OWNER")
    database_text = (ROOT / "database.py").read_text(encoding="utf-8")
    ddl_pattern = re.compile(r"CREATE TABLE IF NOT EXISTS cartas_exemplares\s*\(\s*id INTEGER PRIMARY KEY AUTOINCREMENT,\s*user_id INTEGER NOT NULL,\s*card_id TEXT NOT NULL", re.S)
    check("CI20-23", "current DDL supports global exemplar PK and owner/model validation", bool(ddl_pattern.search(database_text)))

    # Deterministic tie rule: metric first, then persisted list order, then UUID.
    tie_candidates = [
        {"instance_id":"00000000-0000-4000-8000-000000000003","power":5,"zone_order":2},
        {"instance_id":"00000000-0000-4000-8000-000000000002","power":5,"zone_order":1},
        {"instance_id":"00000000-0000-4000-8000-000000000001","power":5,"zone_order":1},
    ]
    winner = choose_by_metric(tie_candidates, "power", strongest=True)
    check("CI20-24", "metric ties use persisted zone order then instance_id fallback", winner["instance_id"] == "00000000-0000-4000-8000-000000000001")
    winner = choose_by_metric(tie_candidates, "power", strongest=False)
    check("CI20-25", "weakest metric selection follows the same deterministic tie rule", winner["instance_id"] == "00000000-0000-4000-8000-000000000001")

    # Source-level guardrails: this work must remain docs-only.
    for rel, cid in [("sistemas/gwent.py","CI20-26"),("sistemas/cartas.py","CI20-27"),("bot.py","CI20-28"),("database.py","CI20-29"),("site/app.js","CI20-30")]:
        # The specific baseline hashes are recorded separately in the package manifest.
        check(cid, f"runtime file is present for integrity comparison: {rel}", (ROOT / rel).is_file())

    passed = sum(1 for c in cases if c["passed"])
    result = {
        "metadata": {
            "document":"CardInstance v0.2 validation",
            "version":"0.2",
            "date":"2026-11-27",
            "status":"GROUP_A_APPROVED_CONTRACT_DRAFT_NOT_FROZEN",
            "schemas":[str(SCHEMA_PATH.relative_to(ROOT)),str(TARGET_SCHEMA_PATH.relative_to(ROOT))],
            "harness":str(Path(__file__).relative_to(ROOT)),
            "scope":"Draft 2020-12 schemas, synthetic invariants, target selection and static DDL evidence; no runtime/DB integration"
        },
        "summary":{"passed":passed,"failed":len(cases)-passed,"total":len(cases)},
        "cases":cases
    }
    RESULT_PATH.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"CardInstance v0.2: {passed}/{len(cases)} passed")
    for case in cases:
        print(f"{'PASS' if case['passed'] else 'FAIL'} {case['id']} — {case['description']}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
