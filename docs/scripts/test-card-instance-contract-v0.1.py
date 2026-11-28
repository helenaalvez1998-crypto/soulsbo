#!/usr/bin/env python3
"""Validate the candidate CardInstance contract without importing production runtime.

Run from repository root:
    python docs/scripts/test-card-instance-contract-v0.1.py

The harness is deliberately isolated. It validates a candidate in-memory state
model and a reference atomic zone-move operation; it does not alter or import
sistemas.gwent, persistence, HTTP routes, or the frontend.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs" / "card-game-card-instance-match.schema.v1.json"
EXAMPLE_PATH = ROOT / "docs" / "examples" / "card-instance-match.example.v1.json"
RESULT_PATH = ROOT / "docs" / "card-game-card-instance-contract-validation-v0.1.json"
ZONES = ("hand", "draw_pile", "board", "discard")
ROWS = {"melee", "ranged", "siege"}
KINDS = {"unit", "special", "relic"}
ORIGINS = {
    "deck_exemplar", "catalog_deck", "generated_token",
    "equipped_relic_activation", "legacy_migration",
}
STATUSES = (
    "status.bleeding", "status.frost", "status.scarlet_rot", "status.madness"
)
UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


class ContractError(ValueError):
    pass


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_uuid4(value: Any) -> bool:
    if not isinstance(value, str) or not UUID4_RE.fullmatch(value):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and parsed.variant == uuid.RFC_4122 and str(parsed) == value


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"chave JSON duplicada: {key}")
        result[key] = value
    return result


def strict_json_loads(raw: str) -> Any:
    return json.loads(raw, object_pairs_hook=strict_object)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def validate_instance(instance_key: str, instance: Any, player_ids: set[str]) -> None:
    _require(isinstance(instance, dict), f"instância {instance_key}: registro deve ser objeto")
    required = {
        "schema_version", "instance_id", "card_id", "exemplar_id", "owner_player_id",
        "origin_type", "definition_snapshot", "state",
    }
    _require(required.issubset(instance), f"instância {instance_key}: campos obrigatórios ausentes")
    _require(instance.get("schema_version") == 1, f"instância {instance_key}: schema_version inválida")
    _require(is_uuid4(instance.get("instance_id")), f"instância {instance_key}: instance_id deve ser UUIDv4 canônico")
    _require(instance_key == instance.get("instance_id"), f"instância {instance_key}: chave do registry difere de instance_id")
    _require(isinstance(instance.get("card_id"), str) and 1 <= len(instance["card_id"]) <= 120,
             f"instância {instance_key}: card_id inválido")
    owner = instance.get("owner_player_id")
    _require(isinstance(owner, str) and re.fullmatch(r"-?(?:0|[1-9][0-9]*)", owner) is not None,
             f"instância {instance_key}: owner_player_id inválido")
    _require(owner in player_ids, f"instância {instance_key}: owner_player_id não participa da partida")
    origin = instance.get("origin_type")
    _require(origin in ORIGINS, f"instância {instance_key}: origin_type desconhecido")
    exemplar = instance.get("exemplar_id")
    _require(exemplar is None or (is_int(exemplar) and exemplar > 0),
             f"instância {instance_key}: exemplar_id deve ser inteiro positivo ou null")
    if origin == "deck_exemplar":
        _require(is_int(exemplar) and exemplar > 0,
                 f"instância {instance_key}: deck_exemplar exige exemplar_id positivo")

    definition = instance.get("definition_snapshot")
    _require(isinstance(definition, dict), f"instância {instance_key}: definition_snapshot deve ser objeto")
    definition_required = {
        "catalog_version", "balance_rules_version", "card_id", "kind", "faction_id",
        "printed_row", "power_base", "rarity_id", "effect_id", "effect_params", "combo_tags",
    }
    _require(definition_required.issubset(definition), f"instância {instance_key}: snapshot incompleto")
    _require(definition.get("card_id") == instance.get("card_id"),
             f"instância {instance_key}: card_id diverge do snapshot")
    _require(isinstance(definition.get("catalog_version"), str) and definition["catalog_version"],
             f"instância {instance_key}: catalog_version inválida")
    _require(isinstance(definition.get("balance_rules_version"), str) and definition["balance_rules_version"],
             f"instância {instance_key}: balance_rules_version inválida")
    _require(definition.get("kind") in KINDS, f"instância {instance_key}: kind inválido")
    _require(definition.get("faction_id") in {"golden_order", "crimson_veil", "dark_moon", "the_forgotten"},
             f"instância {instance_key}: faction_id inválido")
    _require(isinstance(definition.get("effect_params"), dict),
             f"instância {instance_key}: effect_params deve ser objeto")
    tags = definition.get("combo_tags")
    _require(isinstance(tags, list) and all(isinstance(tag, str) and tag for tag in tags),
             f"instância {instance_key}: combo_tags inválidas")
    _require(len(tags) == len(set(tags)), f"instância {instance_key}: combo_tags duplicadas")

    kind = definition["kind"]
    printed_row = definition.get("printed_row")
    power_base = definition.get("power_base")
    if kind == "unit":
        _require(printed_row in ROWS, f"instância {instance_key}: unidade exige printed_row válida")
        _require(is_int(power_base) and 1 <= power_base <= 15,
                 f"instância {instance_key}: unidade exige power_base de 1 a 15")
    else:
        _require(printed_row is None and power_base is None,
                 f"instância {instance_key}: especial/relíquia deve ter printed_row e power_base null")

    state = instance.get("state")
    _require(isinstance(state, dict), f"instância {instance_key}: state deve ser objeto")
    state_required = {
        "current_row", "bonus", "shield_charges", "statuses", "weather_resistance",
        "activated_combo_ids", "effect_state",
    }
    _require(state_required.issubset(state), f"instância {instance_key}: state incompleto")
    current_row = state.get("current_row")
    if kind == "unit":
        _require(current_row in ROWS, f"instância {instance_key}: unidade exige current_row válida")
    else:
        _require(current_row is None, f"instância {instance_key}: carta não-unidade deve ter current_row null")
    _require(is_int(state.get("bonus")), f"instância {instance_key}: bonus deve ser inteiro")
    _require(is_int(state.get("shield_charges")) and state["shield_charges"] >= 0,
             f"instância {instance_key}: shield_charges inválido")
    _require(is_int(state.get("weather_resistance")) and state["weather_resistance"] >= 0,
             f"instância {instance_key}: weather_resistance inválida")
    statuses = state.get("statuses")
    _require(isinstance(statuses, dict) and set(statuses) == set(STATUSES),
             f"instância {instance_key}: conjunto de statuses inválido")
    for status_id, marks in statuses.items():
        _require(is_int(marks) and 0 <= marks <= 2,
                 f"instância {instance_key}: contador inválido para {status_id}")
    combos = state.get("activated_combo_ids")
    _require(isinstance(combos, list) and all(isinstance(c, str) and c for c in combos),
             f"instância {instance_key}: activated_combo_ids inválido")
    _require(len(combos) == len(set(combos)), f"instância {instance_key}: activated_combo_ids duplicados")
    _require(isinstance(state.get("effect_state"), dict),
             f"instância {instance_key}: effect_state deve ser objeto")


def validate_match_state(state: Any) -> None:
    _require(isinstance(state, dict), "match state deve ser objeto")
    required = {"schema_version", "match_id", "state_revision", "status", "players", "instances", "operations"}
    _require(required.issubset(state), "match state: campos obrigatórios ausentes")
    _require(state.get("schema_version") == 1, "match state: schema_version inválida")
    _require(is_int(state.get("match_id")) and state["match_id"] > 0, "match_id inválido")
    _require(is_int(state.get("state_revision")) and state["state_revision"] >= 0, "state_revision inválida")
    _require(state.get("status") in {"active", "finished"}, "status de partida inválido")
    players = state.get("players")
    instances = state.get("instances")
    operations = state.get("operations")
    _require(isinstance(players, dict) and len(players) >= 2, "players exige pelo menos dois participantes")
    _require(isinstance(instances, dict), "instances deve ser registry")
    _require(isinstance(operations, dict), "operations deve ser ledger")
    player_ids = set(players)
    _require(all(isinstance(pid, str) and re.fullmatch(r"-?(?:0|[1-9][0-9]*)", pid) for pid in player_ids),
             "chave de participante inválida")

    locations: dict[str, list[tuple[str, str]]] = {}
    for player_id, player in players.items():
        _require(isinstance(player, dict) and isinstance(player.get("zones"), dict),
                 f"player {player_id}: zones ausente")
        zones = player["zones"]
        _require(set(zones) == set(ZONES), f"player {player_id}: conjunto de zonas deve ser {ZONES}")
        for zone in ZONES:
            refs = zones[zone]
            _require(isinstance(refs, list), f"player {player_id}/{zone}: zona deve ser lista")
            _require(all(isinstance(ref, str) for ref in refs), f"player {player_id}/{zone}: referência não textual")
            _require(len(refs) == len(set(refs)), f"player {player_id}/{zone}: referência duplicada na zona")
            for ref in refs:
                locations.setdefault(ref, []).append((player_id, zone))

    for key, instance in instances.items():
        validate_instance(key, instance, player_ids)
    for ref, occurrences in locations.items():
        _require(ref in instances, f"referência de zona sem instância: {ref}")
        _require(len(occurrences) == 1, f"instance_id aparece em mais de uma zona: {ref}")
        player_id, zone = occurrences[0]
        instance = instances[ref]
        _require(instance["owner_player_id"] == player_id,
                 f"instance_id {ref}: owner diverge do dono da zona")
        if zone == "board":
            _require(instance["definition_snapshot"]["kind"] == "unit",
                     f"board contém carta não-unidade: {ref}")
    for instance_id in instances:
        _require(len(locations.get(instance_id, [])) == 1,
                 f"instância órfã ou fora de exatamente uma zona: {instance_id}")

    seen_exemplars: set[tuple[str, int]] = set()
    for instance in instances.values():
        exemplar = instance.get("exemplar_id")
        if exemplar is not None:
            key = (instance["owner_player_id"], exemplar)
            _require(key not in seen_exemplars,
                     f"exemplar físico duplicado para o mesmo proprietário: {key}")
            seen_exemplars.add(key)

    for operation_id, record in operations.items():
        _require(is_uuid4(operation_id), f"operation_id inválido: {operation_id}")
        _require(isinstance(record, dict), f"operation {operation_id}: registro inválido")
        _require(re.fullmatch(r"[0-9a-f]{64}", str(record.get("fingerprint", ""))) is not None,
                 f"operation {operation_id}: fingerprint inválido")
        _require(record.get("instance_id") in instances,
                 f"operation {operation_id}: instance_id desconhecido")
        _require(record.get("player_id") in player_ids,
                 f"operation {operation_id}: player_id desconhecido")
        _require(record.get("from_zone") in ZONES and record.get("to_zone") in ZONES,
                 f"operation {operation_id}: zona inválida")
        _require(record.get("state_policy_id") == "policy.identity_only",
                 f"operation {operation_id}: state_policy_id ainda não suportado")
        _require(record.get("result") == "applied", f"operation {operation_id}: result inválido")
        _require(is_int(record.get("expected_revision")) and record["expected_revision"] >= 0,
                 f"operation {operation_id}: expected_revision inválida")
        _require(is_int(record.get("revision_before")) and record["revision_before"] == record["expected_revision"],
                 f"operation {operation_id}: revision_before diverge de expected_revision")
        _require(is_int(record.get("revision_after")) and record["revision_after"] == record["revision_before"] + 1,
                 f"operation {operation_id}: revision_after inválida")


def transition_instance(
    state: dict[str, Any], *, operation_id: str, instance_id: str,
    player_id: str, expected_from_zone: str, to_zone: str, expected_revision: int,
    state_policy_id: str = "policy.identity_only",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reference implementation of an atomic same-owner zone move in memory."""
    validate_match_state(state)
    _require(is_uuid4(operation_id), "operation_id deve ser UUIDv4 canônico")
    _require(instance_id in state["instances"], "instance_id desconhecido")
    _require(player_id in state["players"], "player_id não participa da partida")
    _require(expected_from_zone in ZONES and to_zone in ZONES, "zona de origem/destino inválida")
    _require(expected_from_zone != to_zone, "origem e destino não podem ser iguais")
    _require(state_policy_id == "policy.identity_only", "state_policy_id não aprovado/suportado no harness")
    instance = state["instances"][instance_id]
    _require(instance["owner_player_id"] == player_id, "transferência entre proprietários não suportada")
    fingerprint_payload = {
        "instance_id": instance_id, "player_id": player_id,
        "from_zone": expected_from_zone, "to_zone": to_zone,
        "state_policy_id": state_policy_id,
        "expected_revision": expected_revision,
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if operation_id in state["operations"]:
        prior = state["operations"][operation_id]
        _require(prior.get("fingerprint") == fingerprint,
                 "operation_id reutilizado com argumentos diferentes")
        replay_state = copy.deepcopy(state)
        return replay_state, {"status": "already_applied", "replayed": True}

    _require(is_int(expected_revision) and expected_revision >= 0,
             "expected_revision deve ser inteiro não negativo")
    _require(expected_revision == state["state_revision"],
             "snapshot desatualizado: state_revision diverge de expected_revision")
    zones = state["players"][player_id]["zones"]
    _require(zones[expected_from_zone].count(instance_id) == 1,
             "instance_id não está exatamente uma vez na zona de origem esperada")
    if to_zone == "board":
        _require(instance["definition_snapshot"]["kind"] == "unit",
                 "apenas unidade pode entrar em board")

    candidate = copy.deepcopy(state)
    candidate_zones = candidate["players"][player_id]["zones"]
    candidate_zones[expected_from_zone].remove(instance_id)
    candidate_zones[to_zone].append(instance_id)
    revision_before = candidate["state_revision"]
    candidate["state_revision"] = revision_before + 1
    candidate["operations"][operation_id] = {
        "fingerprint": fingerprint,
        "instance_id": instance_id,
        "player_id": player_id,
        "from_zone": expected_from_zone,
        "to_zone": to_zone,
        "state_policy_id": state_policy_id,
        "result": "applied",
        "expected_revision": expected_revision,
        "revision_before": revision_before,
        "revision_after": revision_before + 1,
    }
    validate_match_state(candidate)
    return candidate, {"status": "applied", "replayed": False}


def fixed_id(n: int) -> str:
    return f"00000000-0000-4000-8000-{n:012x}"


def make_instance(n: int, player_id: str, card_id: str = "wolf_guardian", exemplar_id: int | None = 500,
                  kind: str = "unit", origin: str = "deck_exemplar") -> dict[str, Any]:
    row = "melee" if kind == "unit" else None
    power = 5 if kind == "unit" else None
    if origin == "deck_exemplar" and exemplar_id is None:
        exemplar_id = 500 + n
    return {
        "schema_version": 1,
        "instance_id": fixed_id(n),
        "card_id": card_id,
        "exemplar_id": exemplar_id,
        "owner_player_id": player_id,
        "origin_type": origin,
        "definition_snapshot": {
            "catalog_version": "soulsbo-catalog-v1",
            "balance_rules_version": "balance-v0.2",
            "card_id": card_id,
            "kind": kind,
            "faction_id": "golden_order",
            "printed_row": row,
            "power_base": power,
            "rarity_id": "rare" if kind == "unit" else None,
            "effect_id": None,
            "effect_params": {},
            "combo_tags": [],
        },
        "state": {
            "current_row": row,
            "bonus": 2,
            "shield_charges": 1,
            "statuses": {
                "status.bleeding": 1,
                "status.frost": 0,
                "status.scarlet_rot": 0,
                "status.madness": 0,
            },
            "weather_resistance": 1,
            "activated_combo_ids": ["formation.alpha"] if kind == "unit" else [],
            "effect_state": {"audit_fixture": True},
        },
    }


def make_fixture() -> dict[str, Any]:
    instances = {
        fixed_id(1): make_instance(1, "1001", "wolf_guardian", 501),
        fixed_id(2): make_instance(2, "1001", "wolf_guardian", 502),
        fixed_id(3): make_instance(3, "1001", "golden_knight", 503),
        fixed_id(4): make_instance(4, "2002", "wolf_guardian", 501),
        fixed_id(5): make_instance(5, "1001", "tactical_special", 504, kind="special"),
        fixed_id(6): make_instance(6, "1001", "scarlet_scout", 505),
    }
    return {
        "schema_version": 1,
        "match_id": 9001,
        "state_revision": 0,
        "status": "active",
        "players": {
            "1001": {"zones": {
                "hand": [fixed_id(1), fixed_id(5)],
                "draw_pile": [],
                "board": [fixed_id(3)],
                "discard": [fixed_id(2), fixed_id(6)],
            }},
            "2002": {"zones": {
                "hand": [fixed_id(4)],
                "draw_pile": [],
                "board": [],
                "discard": [],
            }},
        },
        "instances": instances,
        "operations": {},
    }


def run_tests() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def case(name: str, fn: Callable[[], None], expected: str = "pass") -> None:
        try:
            fn()
        except Exception as exc:
            if expected == "reject":
                cases.append({"case": name, "status": "passed", "expected": "rejection", "detail": str(exc)})
            else:
                cases.append({"case": name, "status": "failed", "detail": f"{type(exc).__name__}: {exc}"})
        else:
            if expected == "reject":
                cases.append({"case": name, "status": "failed", "detail": "invalid state was accepted"})
            else:
                cases.append({"case": name, "status": "passed"})

    def assert_rejected(mutator: Callable[[dict[str, Any]], None]) -> None:
        state = make_fixture()
        mutator(state)
        validate_match_state(state)

    case("example_file_validates", lambda: validate_match_state(json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))))
    case("same_card_model_multiple_instances_allowed", lambda: _assert_duplicate_model_ok())
    case("same_exemplar_integer_allowed_across_players", lambda: _assert_same_exemplar_cross_owner_ok())
    case("instance_id_duplicate_across_zones_rejected", lambda: assert_rejected(lambda s: s["players"]["1001"]["zones"]["hand"].append(fixed_id(2))), "reject")
    case("duplicate_reference_within_zone_rejected", lambda: assert_rejected(lambda s: s["players"]["1001"]["zones"]["hand"].append(fixed_id(1))), "reject")
    case("unknown_zone_reference_rejected", lambda: assert_rejected(lambda s: s["players"]["1001"]["zones"]["hand"].append(fixed_id(99))), "reject")
    case("orphan_instance_rejected", lambda: assert_rejected(lambda s: s["players"]["1001"]["zones"]["discard"].remove(fixed_id(2))), "reject")
    case("registry_key_must_match_instance_id", lambda: _assert_key_mismatch_rejected(), "reject")
    case("owner_must_match_zone_owner", lambda: assert_rejected(lambda s: s["instances"][fixed_id(1)].update(owner_player_id="2002")), "reject")
    case("instance_id_must_be_canonical_uuid4", lambda: assert_rejected(lambda s: _set_bad_instance_id(s)), "reject")
    case("deck_exemplar_requires_exemplar_id", lambda: assert_rejected(lambda s: _set_exemplar_none(s, fixed_id(1))), "reject")
    case("same_owner_exemplar_cannot_be_used_twice", lambda: assert_rejected(lambda s: _duplicate_exemplar(s)), "reject")
    case("board_rejects_special_cards", lambda: assert_rejected(lambda s: _move_special_to_board_fixture(s)), "reject")
    case("unit_requires_valid_current_row", lambda: assert_rejected(lambda s: s["instances"][fixed_id(1)]["state"].update(current_row="sky")), "reject")
    case("non_unit_requires_null_current_row", lambda: assert_rejected(lambda s: s["instances"][fixed_id(5)]["state"].update(current_row="melee")), "reject")
    case("shield_charges_must_be_nonnegative_integer", lambda: assert_rejected(lambda s: s["instances"][fixed_id(1)]["state"].update(shield_charges=-1)), "reject")
    case("boolean_is_not_valid_status_counter", lambda: assert_rejected(lambda s: s["instances"][fixed_id(1)]["state"]["statuses"].update({"status.frost": True})), "reject")
    case("status_counter_respects_registry_limit", lambda: assert_rejected(lambda s: s["instances"][fixed_id(1)]["state"]["statuses"].update({"status.madness": 3})), "reject")
    case("snapshot_card_id_must_match_instance_card_id", lambda: assert_rejected(lambda s: s["instances"][fixed_id(1)]["definition_snapshot"].update(card_id="other_model")), "reject")
    case("duplicate_json_object_keys_rejected", lambda: strict_json_loads('{"instances":{"x":1,"x":2}}'), "reject")
    case("transition_moves_same_instance_and_preserves_state", lambda: _assert_transition_preserves_state())
    case("transition_replay_is_idempotent", lambda: _assert_idempotent_replay())
    case("operation_id_reuse_with_different_args_rejected", lambda: _assert_operation_conflict(), "reject")
    case("wrong_expected_source_fails_atomically", lambda: _assert_wrong_source_atomic(), "reject")
    case("special_cannot_enter_board_transition", lambda: _assert_special_to_board_atomic(), "reject")
    case("cross_owner_zone_transfer_rejected", lambda: _assert_cross_owner_rejected(), "reject")
    case("discard_to_hand_preserves_all_runtime_fields", lambda: _assert_discard_to_hand_preserves())
    case("same_zone_transition_rejected", lambda: _assert_same_zone_rejected(), "reject")
    case("stale_state_revision_fails_atomically", lambda: _assert_stale_revision_atomic(), "reject")
    case("zone_order_is_preserved_and_destination_appends", lambda: _assert_zone_order())

    passed = sum(item["status"] == "passed" for item in cases)
    failed = len(cases) - passed
    report = {
        "metadata": {
            "document": "CardInstance match envelope and zone transition validation v0.1",
            "status": "CANDIDATE_NOT_APPROVED; ISOLATED_REFERENCE_HARNESS",
            "baseline": "soulsbo-main-continuity-2026-11-27-rev3.zip",
            "runtime_imported": False,
            "schema": "docs/card-game-card-instance-match.schema.v1.json",
            "example": "docs/examples/card-instance-match.example.v1.json",
        },
        "counts": {"assertions": len(cases), "passed": passed, "failed": failed},
        "cases": cases,
        "limitations": [
            "Validates a candidate in-memory envelope and a reference transition function only.",
            "Does not import or modify sistemas.gwent, the legacy candidate resolver, bot.py, database.py, or site/app.js.",
            "Does not test SQLite transaction isolation, HTTP/API integration, browser serialization, Discord, R2, production matches, or concurrent requests.",
            "Passing assertions validate the prototype contract only; all CI-001 through CI-013 decisions remain open.",
        ],
    }
    RESULT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CardInstance contract: {passed}/{len(cases)} passed; {failed} failed")
    for item in cases:
        if item["status"] != "passed":
            print(f"FAIL {item['case']}: {item.get('detail', '')}")
    print(f"Report: {RESULT_PATH.relative_to(ROOT)}")
    return report


def _assert_duplicate_model_ok() -> None:
    state = make_fixture()
    a = state["instances"][fixed_id(1)]
    b = state["instances"][fixed_id(2)]
    assert a["card_id"] == b["card_id"]
    assert a["instance_id"] != b["instance_id"]
    assert a["exemplar_id"] != b["exemplar_id"]
    validate_match_state(state)


def _assert_same_exemplar_cross_owner_ok() -> None:
    state = make_fixture()
    assert state["instances"][fixed_id(1)]["exemplar_id"] == state["instances"][fixed_id(4)]["exemplar_id"]
    validate_match_state(state)


def _assert_key_mismatch_rejected() -> None:
    state = make_fixture()
    wrong_key = fixed_id(99)
    state["instances"][wrong_key] = state["instances"].pop(fixed_id(1))
    validate_match_state(state)


def _set_bad_instance_id(state: dict[str, Any]) -> None:
    instance = state["instances"].pop(fixed_id(1))
    instance["instance_id"] = "not-a-uuid"
    state["instances"]["not-a-uuid"] = instance


def _set_exemplar_none(state: dict[str, Any], instance_id: str) -> None:
    state["instances"][instance_id]["exemplar_id"] = None


def _duplicate_exemplar(state: dict[str, Any]) -> None:
    state["instances"][fixed_id(2)]["exemplar_id"] = state["instances"][fixed_id(1)]["exemplar_id"]


def _move_special_to_board_fixture(state: dict[str, Any]) -> None:
    state["players"]["1001"]["zones"]["hand"].remove(fixed_id(5))
    state["players"]["1001"]["zones"]["board"].append(fixed_id(5))


def _assert_transition_preserves_state() -> None:
    state = make_fixture()
    before = copy.deepcopy(state["instances"][fixed_id(1)])
    moved, result = transition_instance(
        state, operation_id=fixed_id(90), instance_id=fixed_id(1), player_id="1001",
        expected_from_zone="hand", to_zone="board", expected_revision=0,
    )
    assert result["status"] == "applied" and not result["replayed"]
    assert moved["instances"][fixed_id(1)] == before
    assert moved["state_revision"] == state["state_revision"] + 1
    op_record = moved["operations"][fixed_id(90)]
    assert op_record["expected_revision"] == op_record["revision_before"] == 0
    assert op_record["revision_after"] == moved["state_revision"]
    assert fixed_id(1) not in moved["players"]["1001"]["zones"]["hand"]
    assert moved["players"]["1001"]["zones"]["board"].count(fixed_id(1)) == 1
    assert state["players"]["1001"]["zones"]["hand"].count(fixed_id(1)) == 1


def _assert_idempotent_replay() -> None:
    state = make_fixture()
    first, first_result = transition_instance(
        state, operation_id=fixed_id(91), instance_id=fixed_id(1), player_id="1001",
        expected_from_zone="hand", to_zone="board", expected_revision=0,
    )
    second, second_result = transition_instance(
        first, operation_id=fixed_id(91), instance_id=fixed_id(1), player_id="1001",
        expected_from_zone="hand", to_zone="board", expected_revision=0,
    )
    assert first_result["replayed"] is False
    assert second_result["replayed"] is True
    assert second == first
    assert len(second["operations"]) == 1
    assert second["state_revision"] == 1


def _assert_operation_conflict() -> None:
    state = make_fixture()
    first, _ = transition_instance(
        state, operation_id=fixed_id(92), instance_id=fixed_id(1), player_id="1001",
        expected_from_zone="hand", to_zone="board", expected_revision=0,
    )
    transition_instance(
        first, operation_id=fixed_id(92), instance_id=fixed_id(2), player_id="1001",
        expected_from_zone="discard", to_zone="hand", expected_revision=0,
    )


def _assert_wrong_source_atomic() -> None:
    state = make_fixture()
    before = copy.deepcopy(state)
    try:
        transition_instance(
            state, operation_id=fixed_id(93), instance_id=fixed_id(1), player_id="1001",
            expected_from_zone="discard", to_zone="hand",
        )
    finally:
        assert state == before


def _assert_special_to_board_atomic() -> None:
    state = make_fixture()
    before = copy.deepcopy(state)
    try:
        transition_instance(
            state, operation_id=fixed_id(94), instance_id=fixed_id(5), player_id="1001",
            expected_from_zone="hand", to_zone="board",
        )
    finally:
        assert state == before


def _assert_cross_owner_rejected() -> None:
    state = make_fixture()
    transition_instance(
        state, operation_id=fixed_id(95), instance_id=fixed_id(1), player_id="2002",
        expected_from_zone="hand", to_zone="discard", expected_revision=0,
    )


def _assert_discard_to_hand_preserves() -> None:
    state = make_fixture()
    before = copy.deepcopy(state["instances"][fixed_id(2)])
    moved, result = transition_instance(
        state, operation_id=fixed_id(96), instance_id=fixed_id(2), player_id="1001",
        expected_from_zone="discard", to_zone="hand", expected_revision=0,
    )
    assert result["status"] == "applied"
    assert moved["instances"][fixed_id(2)] == before
    assert moved["players"]["1001"]["zones"]["hand"].count(fixed_id(2)) == 1


def _assert_same_zone_rejected() -> None:
    state = make_fixture()
    transition_instance(
        state, operation_id=fixed_id(97), instance_id=fixed_id(1), player_id="1001",
        expected_from_zone="hand", to_zone="hand", expected_revision=0,
    )


def _assert_stale_revision_atomic() -> None:
    state = make_fixture()
    before = copy.deepcopy(state)
    try:
        transition_instance(
            state, operation_id=fixed_id(98), instance_id=fixed_id(1), player_id="1001",
            expected_from_zone="hand", to_zone="board", expected_revision=5,
        )
    finally:
        assert state == before


def _assert_zone_order() -> None:
    state = make_fixture()
    original_discard_order = list(state["players"]["1001"]["zones"]["discard"])
    original_hand_order = list(state["players"]["1001"]["zones"]["hand"])
    moved, _ = transition_instance(
        state, operation_id=fixed_id(99), instance_id=fixed_id(2), player_id="1001",
        expected_from_zone="discard", to_zone="hand", expected_revision=0,
    )
    assert moved["players"]["1001"]["zones"]["discard"] == original_discard_order[1:]
    assert moved["players"]["1001"]["zones"]["hand"] == original_hand_order + [fixed_id(2)]
    assert state["players"]["1001"]["zones"]["discard"] == original_discard_order


def main() -> int:
    if not SCHEMA_PATH.exists() or not EXAMPLE_PATH.exists():
        print("Missing schema or example fixture", file=sys.stderr)
        return 2
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        print("Unexpected JSON Schema dialect", file=sys.stderr)
        return 2
    report = run_tests()
    return 0 if report["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
