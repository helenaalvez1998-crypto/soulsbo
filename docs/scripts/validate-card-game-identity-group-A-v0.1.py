#!/usr/bin/env python3
"""Read-only validation harness for identity decision Group A.

Run from repository root:
    python docs/scripts/validate-card-game-identity-group-A-v0.1.py

Validates the proposed identity invariants using synthetic fixtures and checks
selected source-level facts in the current legacy code. It does not import or
modify the game runtime, database, HTTP handlers, or frontend.
"""
from __future__ import annotations

import copy
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
RESULT_PATH = DOCS / "card-game-identity-group-A-validation-v0.1.json"

I1 = "00000000-0000-4000-8000-000000000001"
I2 = "00000000-0000-4000-8000-000000000002"
I3 = "00000000-0000-4000-8000-000000000003"
I4 = "00000000-0000-4000-8000-000000000004"


class ContractError(ValueError):
    pass


def is_uuid4(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return (
        parsed.version == 4
        and parsed.variant == uuid.RFC_4122
        and str(parsed) == value
        and value == value.lower()
    )


def make_instance(
    instance_id: str,
    card_id: str,
    owner: str,
    origin: str,
    exemplar_id: int | None,
    kind: str = "unit",
) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "card_id": card_id,
        "owner_player_id": owner,
        "origin_type": origin,
        "exemplar_id": exemplar_id,
        "definition_snapshot": {"card_id": card_id, "kind": kind},
    }


def build_fixture() -> tuple[dict[str, Any], dict[int, dict[str, str]]]:
    instances = {
        I1: make_instance(I1, "wolf_guardian", "1001", "deck_exemplar", 501),
        # Same model, separate generated occurrence: no collection exemplar.
        I2: make_instance(I2, "wolf_guardian", "1001", "generated_token", None),
        I3: make_instance(I3, "golden_knight", "1001", "deck_exemplar", 503),
        I4: make_instance(I4, "wolf_guardian", "2002", "deck_exemplar", 504),
    }
    state = {
        "players": {
            "1001": {"zones": {"hand": [], "draw_pile": [], "board": [I1, I2], "discard": [I3]}},
            "2002": {"zones": {"hand": [I4], "draw_pile": [], "board": [], "discard": []}},
        },
        "instances": instances,
    }
    exemplar_rows = {
        501: {"owner_player_id": "1001", "card_id": "wolf_guardian"},
        503: {"owner_player_id": "1001", "card_id": "golden_knight"},
        504: {"owner_player_id": "2002", "card_id": "wolf_guardian"},
    }
    return state, exemplar_rows


def validate_identity_state(
    state: dict[str, Any], exemplar_rows: dict[int, dict[str, str]]
) -> None:
    players = state.get("players")
    instances = state.get("instances")
    if not isinstance(players, dict) or len(players) < 2:
        raise ContractError("match must contain at least two players")
    if not isinstance(instances, dict):
        raise ContractError("instances registry missing")

    locations: dict[str, list[tuple[str, str]]] = {}
    for player_id, player in players.items():
        zones = player.get("zones") if isinstance(player, dict) else None
        if not isinstance(zones, dict) or set(zones) != {"hand", "draw_pile", "board", "discard"}:
            raise ContractError(f"invalid zones for player {player_id}")
        for zone_name, refs in zones.items():
            if not isinstance(refs, list) or len(refs) != len(set(refs)):
                raise ContractError(f"duplicate/invalid references in {player_id}/{zone_name}")
            for instance_id in refs:
                locations.setdefault(instance_id, []).append((player_id, zone_name))

    seen_exemplar_ids: set[int] = set()
    for key, instance in instances.items():
        if not is_uuid4(key) or instance.get("instance_id") != key:
            raise ContractError(f"invalid instance UUID/key: {key}")
        if instance.get("owner_player_id") not in players:
            raise ContractError(f"owner does not participate: {key}")
        if instance.get("definition_snapshot", {}).get("card_id") != instance.get("card_id"):
            raise ContractError(f"model ID mismatch in snapshot: {key}")
        exemplar_id = instance.get("exemplar_id")
        origin = instance.get("origin_type")
        if origin == "deck_exemplar":
            if not isinstance(exemplar_id, int) or isinstance(exemplar_id, bool) or exemplar_id <= 0:
                raise ContractError(f"deck_exemplar requires positive exemplar_id: {key}")
            if exemplar_id in seen_exemplar_ids:
                raise ContractError(f"globally reused exemplar_id: {exemplar_id}")
            seen_exemplar_ids.add(exemplar_id)
            row = exemplar_rows.get(exemplar_id)
            if row is None:
                raise ContractError(f"unknown exemplar_id: {exemplar_id}")
            if row.get("owner_player_id") != instance.get("owner_player_id"):
                raise ContractError(f"exemplar owner mismatch: {exemplar_id}")
            if row.get("card_id") != instance.get("card_id"):
                raise ContractError(f"exemplar model mismatch: {exemplar_id}")
        elif origin in {"generated_token", "equipped_relic_activation", "catalog_deck"}:
            if exemplar_id is not None:
                raise ContractError(f"origin {origin} must not invent exemplar_id: {key}")
        elif origin == "legacy_migration":
            if exemplar_id is not None:
                if not isinstance(exemplar_id, int) or exemplar_id <= 0 or exemplar_id in seen_exemplar_ids:
                    raise ContractError(f"invalid/duplicate migrated exemplar_id: {key}")
                seen_exemplar_ids.add(exemplar_id)
                row = exemplar_rows.get(exemplar_id)
                if row is None or row.get("owner_player_id") != instance.get("owner_player_id") or row.get("card_id") != instance.get("card_id"):
                    raise ContractError(f"unproven migrated exemplar_id: {key}")
        else:
            raise ContractError(f"unknown origin_type: {origin}")

    for instance_id, refs in locations.items():
        if instance_id not in instances:
            raise ContractError(f"zone points to missing instance: {instance_id}")
        if len(refs) != 1:
            raise ContractError(f"instance appears in multiple zones: {instance_id}")
        player_id, zone = refs[0]
        instance = instances[instance_id]
        if instance.get("owner_player_id") != player_id:
            raise ContractError(f"owner/zone mismatch: {instance_id}")
        if zone == "board" and instance.get("definition_snapshot", {}).get("kind") != "unit":
            raise ContractError(f"non-unit in board: {instance_id}")
    for instance_id in instances:
        if len(locations.get(instance_id, [])) != 1:
            raise ContractError(f"orphan instance: {instance_id}")


def resolve_instance_target(target_instance_id: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [c for c in candidates if c.get("instance_id") == target_instance_id]
    if len(matches) != 1:
        raise ContractError("target_instance_id is missing, ineligible, or ambiguous")
    return matches[0]


def resolve_legacy_model_target(card_id: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [c for c in candidates if c.get("card_id") == card_id]
    if len(matches) == 0:
        raise ContractError("target_not_eligible")
    if len(matches) > 1:
        raise ContractError("ambiguous_legacy_target")
    return matches[0]


def stable_metric_selection(
    ordered_candidates: list[dict[str, Any]], metric: str, *, strongest: bool = True
) -> dict[str, Any]:
    if not ordered_candidates:
        raise ContractError("no eligible candidates")
    indexed = list(enumerate(ordered_candidates))
    indexed.sort(
        key=lambda pair: (
            -pair[1][metric] if strongest else pair[1][metric],
            pair[0],
            pair[1]["instance_id"],
        )
    )
    return indexed[0][1]


def expect_rejection(fn) -> bool:
    try:
        fn()
    except ContractError:
        return True
    return False


def main() -> int:
    cases: list[dict[str, Any]] = []

    def check(case_id: str, description: str, condition: bool) -> None:
        cases.append({"id": case_id, "description": description, "passed": bool(condition)})

    state, exemplar_rows = build_fixture()
    check("A-01", "UUIDv4 fixture IDs are canonical", all(is_uuid4(k) for k in state["instances"]))
    check("A-02", "non-UUIDv4 identifier is rejected", not is_uuid4("wolf_guardian"))
    try:
        validate_identity_state(state, exemplar_rows)
        valid_fixture = True
    except ContractError:
        valid_fixture = False
    check("A-03", "valid two-player fixture passes global identity invariants", valid_fixture)
    check("A-04", "same card_id can appear as separate instances", len([i for i in state["instances"].values() if i["card_id"] == "wolf_guardian"]) == 3)
    check("A-05", "deck exemplar IDs in fixture are globally distinct", len({501, 503, 504}) == 3)

    broken = copy.deepcopy(state)
    broken["players"]["2002"]["zones"]["hand"].append(I1)
    check("A-06", "same instance in two zones is rejected", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    broken = copy.deepcopy(state)
    broken["players"]["1001"]["zones"]["board"].remove(I2)
    check("A-07", "orphan registry instance is rejected", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    broken = copy.deepcopy(state)
    broken["instances"][I1]["owner_player_id"] = "2002"
    check("A-08", "owner inconsistent with containing zone is rejected", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    broken = copy.deepcopy(state)
    broken["instances"][I4]["exemplar_id"] = 501
    check("A-09", "exemplar ID reused across owners is rejected globally", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    broken = copy.deepcopy(state)
    broken["instances"][I1]["exemplar_id"] = None
    check("A-10", "deck_exemplar without exemplar_id is rejected", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    broken = copy.deepcopy(state)
    broken["instances"][I1]["exemplar_id"] = 504
    check("A-11", "exemplar owned by another player is rejected", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    broken = copy.deepcopy(state)
    broken["instances"][I1]["card_id"] = "golden_knight"
    check("A-12", "exemplar whose card_id differs from instance is rejected", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    token = copy.deepcopy(state)
    validate_identity_state(token, exemplar_rows)
    check("A-13", "generated token can have null exemplar_id", token["instances"][I2]["origin_type"] == "generated_token" and token["instances"][I2]["exemplar_id"] is None)

    broken = copy.deepcopy(state)
    broken["instances"][I2]["exemplar_id"] = 504
    check("A-14", "generated token cannot invent a collection exemplar", expect_rejection(lambda: validate_identity_state(broken, exemplar_rows)))

    candidates = [state["instances"][I1], state["instances"][I2]]
    check("A-15", "target_instance_id resolves exact occurrence among same-model copies", resolve_instance_target(I2, candidates)["instance_id"] == I2)
    check("A-16", "unknown/ineligible target_instance_id is rejected", expect_rejection(lambda: resolve_instance_target(I4, candidates)))
    check("A-17", "legacy card_id adapter resolves one eligible candidate", resolve_legacy_model_target("wolf_guardian", [state["instances"][I1]])["instance_id"] == I1)
    check("A-18", "legacy card_id adapter rejects ambiguous duplicate model", expect_rejection(lambda: resolve_legacy_model_target("wolf_guardian", candidates)))
    check("A-19", "legacy card_id adapter rejects no eligible candidate", expect_rejection(lambda: resolve_legacy_model_target("missing_model", candidates)))

    equal_metric = [
        {"instance_id": I2, "power": 5},
        {"instance_id": I1, "power": 5},
    ]
    check("A-20", "metric tie follows persisted zone order before UUID fallback", stable_metric_selection(equal_metric, "power")["instance_id"] == I2)
    check("A-21", "first/last selector semantics can use explicit zone order", equal_metric[0]["instance_id"] == I2 and equal_metric[-1]["instance_id"] == I1)

    db_source = (ROOT / "database.py").read_text(encoding="utf-8")
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    gwent_source = (ROOT / "sistemas" / "gwent.py").read_text(encoding="utf-8")
    schema_block = db_source[db_source.find("CREATE TABLE IF NOT EXISTS cartas_exemplares"):db_source.find("CREATE TABLE IF NOT EXISTS cartas_kit_inicial")]
    check("A-22", "current DB schema declares exemplar id as table-level primary key", "id INTEGER PRIMARY KEY AUTOINCREMENT" in schema_block)
    check("A-23", "current exemplar row ties id to user_id and card_id", "user_id INTEGER NOT NULL" in schema_block and "card_id TEXT NOT NULL" in schema_block)
    deck_save_start = bot_source.find("async def _api_gwent_deck_save")
    deck_save_end = bot_source.find("async def _api_gwent_deck_reset", deck_save_start)
    deck_save_block = bot_source[deck_save_start:deck_save_end]
    check("A-24", "current deck-save endpoint keeps the 12 distinct-model rule", "len(set(ids)) != 12" in deck_save_block)
    snapshot_start = bot_source.find("async def _gwent_deck_snapshots")
    snapshot_end = bot_source.find("async def _api_gwent_matches", snapshot_start)
    snapshot_block = bot_source[snapshot_start:snapshot_end]
    check("A-25", "current match snapshot path passes prepared card without restoring exemplar_id", "cards.append(preparar_carta(payload))" in snapshot_block and "cards.append(preparar_carta(payload))\n        return cards" in snapshot_block)
    prepare_start = gwent_source.find("def preparar_carta(card: dict)")
    prepare_end = gwent_source.find("def preparar_carta_pessoal", prepare_start)
    prepare_block = gwent_source[prepare_start:prepare_end]
    check("A-26", "standard preparar_carta return has no exemplar_id field", '"exemplar_id":' not in prepare_block)
    new_state_start = gwent_source.find("def novo_estado(")
    new_state_end = gwent_source.find("def _registrar_evento", new_state_start)
    new_state_block = gwent_source[new_state_start:new_state_end]
    check("A-27", "legacy novo_estado does not generate instance_id", "instance_id" not in new_state_block)
    summary_start = gwent_source.find("def _resumo_alvo(")
    summary_end = gwent_source.find("def opcoes_de_alvo", summary_start)
    summary_block = gwent_source[summary_start:summary_end]
    check("A-28", "legacy target summary serializes model id, not instance_id", '"id": str(unit["id"])' in summary_block and "instance_id" not in summary_block)
    check("A-29", "legacy relic activation materializes a temporary hand payload", 'player["hand"].append(relic_payload)' in gwent_source)
    check("A-30", "legacy target action is received as target_id", 'body.get("target_id"' in bot_source)

    passed = sum(1 for c in cases if c["passed"])
    failed = len(cases) - passed
    result = {
        "metadata": {
            "document": "Card-game physical identity Group A validation",
            "version": "0.1",
            "date": "2026-11-27",
            "baseline": "soulsbo-main-continuity-2026-11-27-rev5.zip",
            "status": "OWNER_APPROVED",
            "approval_record": "docs/card-game-identity-group-A-approval-v0.1.json",
            "runtime_integration": False,
            "production_database_access": False,
            "checks_are_synthetic_or_static": True,
        },
        "summary": {"total": len(cases), "passed": passed, "failed": failed},
        "cases": cases,
        "limitations": [
            "Synthetic match and exemplar fixtures; no production DB rows were read.",
            "Static source assertions are evidence checks, not end-to-end HTTP/runtime tests.",
            "Owner approval is recorded separately; this harness checks synthetic identity invariants and legacy-source evidence only.",
            "The harness does not implement identity, target selection, or migration in the live engine.",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Group A identity validation: {passed}/{len(cases)} passed; {failed} failed")
    for case in cases:
        print(f"[{'PASS' if case['passed'] else 'FAIL'}] {case['id']} — {case['description']}")
    print(f"Result: {RESULT_PATH.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
