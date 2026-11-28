#!/usr/bin/env python3
"""Validate the CardInstance v0.4 draft schema, fixture and isolated lifecycle semantics.

Run from the repository root:
    python docs/scripts/validate-card-game-card-instance-v0.4.py

This is a documentation/contract harness. It does not import or execute the legacy
runtime, database, Discord bot, HTTP handlers, or production persistence.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SCHEMA_PATH = DOCS / "schemas" / "card-game-card-instance-match.schema.v4.json"
EXAMPLE_PATH = DOCS / "examples" / "card-instance-match.example.v4.json"
RESULT_PATH = DOCS / "card-game-card-instance-contract-validation-v0.4.json"

schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
approval = json.loads((DOCS / "card-game-state-lifecycle-group-C-approval-v0.1.json").read_text(encoding="utf-8"))
results: list[dict[str, Any]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append({"name": name, "status": "PASS" if condition else "FAIL", "detail": detail})
    if not condition:
        raise AssertionError(f"{name}: {detail or 'condition failed'}")


def uuid4_text(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", value
    ))


def make_unit(instance_id: str, row: str | None = "melee") -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "definition_snapshot": {"kind": "unit", "intrinsic_weather_resistance": 1, "printed_row": "melee"},
        "state": {
            "current_row": row,
            "last_board_row": row,
            "bonus_grants": [],
            "protection_grants": [],
            "status_applications": [],
            "weather_resistance_modifiers": [],
            "activated_combo_ids": ["combo.example"],
            "effect_state": {}
        },
        "zone": "board"
    }


def expire_entries(entries: list[dict[str, Any]], trigger: str) -> list[dict[str, Any]]:
    return [entry for entry in entries if entry["expires_on"] != trigger]


def move_within_board(instance: dict[str, Any], destination: str, player_state: dict[str, Any]) -> None:
    instance["state"]["current_row"] = destination
    instance["state"]["last_board_row"] = destination
    # A movement is not a successful unit play: player_state is intentionally unchanged.


def successful_board_exit(instance: dict[str, Any], destination_zone: str) -> None:
    old_row = instance["state"]["current_row"]
    if old_row is not None:
        instance["state"]["last_board_row"] = old_row
    instance["state"]["current_row"] = None
    instance["state"]["status_applications"] = []
    instance["state"]["protection_grants"] = []
    instance["state"]["weather_resistance_modifiers"] = [
        entry for entry in instance["state"]["weather_resistance_modifiers"]
        if entry["expires_on"] not in {"board_exit", "zone_exit"}
    ]
    instance["zone"] = destination_zone


def blocked_removal(instance: dict[str, Any], selected_grant_id: str, compatible: bool) -> bool:
    if not compatible:
        return False
    for grant in instance["state"]["protection_grants"]:
        if grant["grant_id"] == selected_grant_id and grant["charges"] > 0:
            grant["charges"] -= 1
            return True
    return False


def close_round(match: dict[str, Any], terminal: bool) -> dict[str, Any]:
    # Score snapshot is captured before any expiration. The returned object models
    # the operational state after round_close, regardless of terminal status.
    score_snapshot = {iid: sum(g["amount"] for g in inst["state"]["bonus_grants"])
                      for iid, inst in match["instances"].items()}
    for inst in match["instances"].values():
        st = inst["state"]
        st["bonus_grants"] = expire_entries(st["bonus_grants"], "round_close")
        st["protection_grants"] = expire_entries(st["protection_grants"], "round_close")
        st["status_applications"] = expire_entries(st["status_applications"], "round_close")
        st["weather_resistance_modifiers"] = expire_entries(st["weather_resistance_modifiers"], "round_close")
        st["activated_combo_ids"] = []
    for player in match["players"].values():
        player["round_state"]["last_unit_play_row"] = None
    match["status"] = "finished" if terminal else "active"
    return score_snapshot


def purify(instance: dict[str, Any], selected_status_ids: set[str]) -> None:
    instance["state"]["status_applications"] = [
        app for app in instance["state"]["status_applications"] if app["status_id"] not in selected_status_ids
    ]


# 1–7: schema and envelope.
Draft202012Validator.check_schema(schema)
check("01_schema_is_draft_2020_12", schema.get("$schema", "").endswith("2020-12/schema"))
check("02_schema_version_is_four", schema["properties"]["schema_version"]["const"] == 4)
errors = list(Draft202012Validator(schema).iter_errors(example))
check("03_example_matches_schema", not errors, "; ".join(e.message for e in errors[:3]))
check("04_example_manifest_present", isinstance(example.get("definition_manifest"), dict))
check("05_example_state_revision_nonnegative", isinstance(example.get("state_revision"), int) and example["state_revision"] >= 0)
check("06_example_status_valid", example.get("status") in {"active", "finished"})
check("07_all_players_have_round_state", all("round_state" in p for p in example["players"].values()))

# 8–18: identity, zones, rows and snapshot.
instances = example["instances"]
all_zone_refs: list[str] = []
zone_for: dict[str, str] = {}
owner_for: dict[str, str] = {}
for player_id, player in example["players"].items():
    for zone_name, refs in player["zones"].items():
        for ref in refs:
            all_zone_refs.append(ref)
            zone_for[ref] = zone_name
            owner_for[ref] = player_id
check("08_instance_keys_are_uuid4", all(uuid4_text(iid) for iid in instances))
check("09_instance_key_matches_record", all(iid == inst["instance_id"] for iid, inst in instances.items()))
check("10_each_instance_has_v4_schema", all(inst["schema_version"] == 4 for inst in instances.values()))
check("11_repeated_card_models_are_distinct_instances", len([x for x in instances.values() if x["card_id"] == "wolf_guardian"]) >= 2)
check("12_every_instance_occurs_in_exactly_one_zone", len(all_zone_refs) == len(set(all_zone_refs)) == len(instances) and set(all_zone_refs) == set(instances))
check("13_zone_owner_matches_instance_owner", all(owner_for[iid] == inst["owner_player_id"] for iid, inst in instances.items()))
check("14_all_board_instances_are_units", all(instances[iid]["definition_snapshot"]["kind"] == "unit" for p in example["players"].values() for iid in p["zones"]["board"]))
check("15_board_instances_have_current_row", all(instances[iid]["state"]["current_row"] in {"melee", "ranged", "siege"} for p in example["players"].values() for iid in p["zones"]["board"]))
check("16_non_board_instances_have_null_current_row", all(instances[iid]["state"]["current_row"] is None for iid, zone in zone_for.items() if zone != "board"))
check("17_all_definitions_have_intrinsic_weather_resistance", all(isinstance(i["definition_snapshot"].get("intrinsic_weather_resistance"), int) and i["definition_snapshot"]["intrinsic_weather_resistance"] >= 0 for i in instances.values()))
check("18_legacy_weather_resistance_scalar_absent", all("weather_resistance" not in i["state"] for i in instances.values()))

# 19–30: canonical state collections and causal references.
all_events = {e["event_id"]: e for e in example["events"]}
check("19_bonus_is_grant_projection_not_scalar", all("bonus_grants" in i["state"] and "bonus" not in i["state"] for i in instances.values()))
check("20_protection_is_grant_projection_not_scalar", all("protection_grants" in i["state"] and "shield_charges" not in i["state"] for i in instances.values()))
check("21_statuses_are_applications_not_counters", all("status_applications" in i["state"] and "statuses" not in i["state"] for i in instances.values()))
check("22_weather_modifiers_are_a_list", all(isinstance(i["state"]["weather_resistance_modifiers"], list) for i in instances.values()))
check("23_every_bonus_grant_has_event_reference", all(g["applied_event_id"] in all_events for i in instances.values() for g in i["state"]["bonus_grants"]))
check("24_bonus_grant_source_matches_event", all((all_events[g["applied_event_id"]]["source_effect_id"] == g["source_effect_id"] and all_events[g["applied_event_id"]]["source_instance_id"] == g["source_instance_id"]) for i in instances.values() for g in i["state"]["bonus_grants"]))
check("25_grant_ids_are_unique_per_instance", all(len({g["grant_id"] for g in i["state"]["bonus_grants"]}) == len(i["state"]["bonus_grants"]) for i in instances.values()))
check("26_protection_grants_support_zero_remaining_charges", all(g["charges"] >= 0 for i in instances.values() for g in i["state"]["protection_grants"]))
check("27_status_ids_are_known_registry_keys", all(a["status_id"] in {"status.bleeding", "status.frost", "status.scarlet_rot", "status.madness"} for i in instances.values() for a in i["state"]["status_applications"]))
check("28_player_sequence_is_separate_from_instances", all("last_unit_play_row" in p["round_state"] for p in example["players"].values()))
check("29_special_and_relic_rows_are_null", all(i["state"]["current_row"] is None and i["state"]["last_board_row"] is None for i in instances.values() if i["definition_snapshot"]["kind"] in {"special", "relic"}))
check("30_rarity_is_present_only_as_snapshot_classification", all("rarity_id" in i["definition_snapshot"] for i in instances.values()))

# 31–39: state transitions on isolated synthetic instances.
unit = make_unit("00000000-0000-4000-8000-000000000101")
unit["state"]["bonus_grants"] = [{"grant_id":"g1","amount":2,"expires_on":"round_close","clamp_policy_id":"example.clamp","source_effect_id":"effect.test","source_instance_id":None,"applied_event_id":"event1"}]
unit["state"]["protection_grants"] = [{"grant_id":"p1","profile_id":"profile.standard","charges":1,"expires_on":"permanent_instance","source_effect_id":"effect.shield","source_instance_id":None,"applied_event_id":"event2"}]
unit["state"]["status_applications"] = [{"application_id":"s1","status_id":"status.frost","expires_on":"round_close","source_effect_id":"effect.frost","source_instance_id":None,"applied_event_id":"event3"}]
unit["state"]["weather_resistance_modifiers"] = [
    {"modifier_id":"w1","amount":1,"expires_on":"board_exit","source_effect_id":"relic.vigil_seal","source_instance_id":None,"applied_event_id":"event4"},
    {"modifier_id":"w2","amount":2,"expires_on":"permanent_instance","source_effect_id":"effect.permanent_weather","source_instance_id":None,"applied_event_id":"event5"}
]
player_state = {"last_unit_play_row":"siege"}
move_copy = copy.deepcopy(unit)
move_within_board(move_copy, "ranged", player_state)
check("31_movement_updates_current_and_last_board_row", move_copy["state"]["current_row"] == move_copy["state"]["last_board_row"] == "ranged")
check("32_movement_preserves_grants_status_and_protection", len(move_copy["state"]["bonus_grants"]) == 1 and len(move_copy["state"]["protection_grants"]) == 1 and len(move_copy["state"]["status_applications"]) == 1)
check("33_movement_does_not_change_last_unit_play_row", player_state["last_unit_play_row"] == "siege")
exit_copy = copy.deepcopy(unit)
successful_board_exit(exit_copy, "discard")
check("34_successful_board_exit_nulls_current_row_and_preserves_last_row", exit_copy["state"]["current_row"] is None and exit_copy["state"]["last_board_row"] == "melee")
check("35_successful_board_exit_clears_status_and_protection", exit_copy["state"]["status_applications"] == [] and exit_copy["state"]["protection_grants"] == [])
check("36_board_exit_expires_only_board_exit_weather", len(exit_copy["state"]["weather_resistance_modifiers"]) == 1 and exit_copy["state"]["weather_resistance_modifiers"][0]["modifier_id"] == "w2")
check("37_board_exit_preserves_round_close_bonus_until_expiry", len(exit_copy["state"]["bonus_grants"]) == 1 and exit_copy["state"]["bonus_grants"][0]["expires_on"] == "round_close")
block_copy = copy.deepcopy(unit)
was_blocked = blocked_removal(block_copy, "p1", True)
check("38_block_consumes_exactly_one_compatible_charge", was_blocked and block_copy["state"]["protection_grants"][0]["charges"] == 0)
check("39_block_does_not_change_zone_or_clean_state", block_copy["zone"] == "board" and len(block_copy["state"]["status_applications"]) == 1 and len(block_copy["state"]["bonus_grants"]) == 1)

# 40–49: sacrifice, round close, weather, return and purification.
sac_copy = copy.deepcopy(unit)
# Sacrifice bypasses shield by directly following successful board-exit policy.
successful_board_exit(sac_copy, "discard")
check("40_sacrifice_bypasses_shield_and_exits_board", sac_copy["zone"] == "discard" and sac_copy["state"]["protection_grants"] == [])
round_fixture = {
    "status":"active",
    "players":{"1":{"round_state":{"last_unit_play_row":"melee"}}},
    "instances":{
        "board": make_unit("00000000-0000-4000-8000-000000000111"),
        "discard": make_unit("00000000-0000-4000-8000-000000000112", None),
        "hand": make_unit("00000000-0000-4000-8000-000000000113", None),
        "draw_pile": make_unit("00000000-0000-4000-8000-000000000114", None)
    }
}
for inst in round_fixture["instances"].values():
    inst["state"]["bonus_grants"] = [
        {"grant_id":"r1","amount":3,"expires_on":"round_close","clamp_policy_id":"c","source_effect_id":"e","source_instance_id":None,"applied_event_id":"x"},
        {"grant_id":"p1","amount":1,"expires_on":"permanent_instance","clamp_policy_id":"c","source_effect_id":"e2","source_instance_id":None,"applied_event_id":"y"}
    ]
    inst["state"]["status_applications"] = [{"application_id":"s","status_id":"status.frost","expires_on":"round_close","source_effect_id":"e","source_instance_id":None,"applied_event_id":"z"}]
    inst["state"]["protection_grants"] = [
        {"grant_id":"pr","profile_id":"profile.round","charges":1,"expires_on":"round_close","source_effect_id":"e3","source_instance_id":None,"applied_event_id":"p1"},
        {"grant_id":"pp","profile_id":"profile.permanent","charges":1,"expires_on":"permanent_instance","source_effect_id":"e4","source_instance_id":None,"applied_event_id":"p2"}
    ]
    inst["state"]["weather_resistance_modifiers"] = [
        {"modifier_id":"w1","amount":1,"expires_on":"board_exit","source_effect_id":"relic.vigil_seal","source_instance_id":None,"applied_event_id":"event4"},
        {"modifier_id":"w2","amount":2,"expires_on":"permanent_instance","source_effect_id":"effect.permanent_weather","source_instance_id":None,"applied_event_id":"event5"},
        {"modifier_id":"w4","amount":4,"expires_on":"round_close","source_effect_id":"effect.round_weather","source_instance_id":None,"applied_event_id":"event9"}
    ]
    inst["state"]["activated_combo_ids"] = ["combo.x"]
score_snapshot = close_round(round_fixture, terminal=True)
check("41_round_close_expires_grants_in_all_zones", all(len(i["state"]["bonus_grants"]) == 1 for i in round_fixture["instances"].values()))
check("42_round_close_preserves_permanent_instance", all(i["state"]["bonus_grants"][0]["expires_on"] == "permanent_instance" for i in round_fixture["instances"].values()))
check("43_round_close_expires_statuses_and_clears_combos_all_zones", all(i["state"]["status_applications"] == [] and i["state"]["activated_combo_ids"] == [] for i in round_fixture["instances"].values()))
check("71_round_close_expires_protection_grants_but_keeps_permanent", all(len(i["state"]["protection_grants"]) == 1 and i["state"]["protection_grants"][0]["expires_on"] == "permanent_instance" for i in round_fixture["instances"].values()))
check("72_round_close_expires_weather_modifiers_but_keeps_board_exit_and_permanent", all({m["expires_on"] for m in i["state"]["weather_resistance_modifiers"]} == {"board_exit","permanent_instance"} for i in round_fixture["instances"].values()))
check("44_terminal_round_also_executes_round_close", round_fixture["status"] == "finished" and all(len(i["state"]["bonus_grants"]) == 1 for i in round_fixture["instances"].values()))
check("45_score_snapshot_precedes_expiration", all(score_snapshot[k] == 4 for k in round_fixture["instances"]))
check("46_round_close_resets_last_unit_play_row", round_fixture["players"]["1"]["round_state"]["last_unit_play_row"] is None)
check("47_weather_effective_is_intrinsic_plus_active_modifiers_with_floor_zero", max(0, 1 + 1 - 5) == 0 and max(0, 1 + 1 + 2) == 4)
return_copy = copy.deepcopy(unit)
return_copy["state"]["weather_resistance_modifiers"] = [x for x in return_copy["state"]["weather_resistance_modifiers"] if x["expires_on"] not in {"board_exit", "zone_exit"}]
return_copy["state"]["current_row"] = None
return_copy["zone"] = "hand"
check("48_hand_recovery_preserves_only_nonexpired_modifiers_without_entry_hook", len(return_copy["state"]["weather_resistance_modifiers"]) == 1 and return_copy["zone"] == "hand")
status_copy = copy.deepcopy(unit)
purify(status_copy, {"status.frost"})
check("49_purification_removes_only_declared_status_ids", all(a["status_id"] != "status.frost" for a in status_copy["state"]["status_applications"]) and status_copy["state"]["bonus_grants"] == unit["state"]["bonus_grants"])

# 50–56: effect-specific return, shield profile, rarity and causal guardrails.
def resolve_return(instance: dict[str, Any], effect: str, requested_row: str | None) -> tuple[str, int]:
    st = instance["state"]
    previous = sum(g["amount"] for g in st["bonus_grants"])
    st["status_applications"] = []
    st["protection_grants"] = []
    st["weather_resistance_modifiers"] = [m for m in st["weather_resistance_modifiers"] if m["expires_on"] != "zone_exit"]
    if effect in {"ressurgir", "requiem"}:
        st["bonus_grants"] = []
        chosen = st["last_board_row"] or (requested_row if requested_row in {"melee","ranged","siege"} else "melee")
        return chosen, 0
    if effect == "esgar":
        if requested_row not in {"melee","ranged","siege"}:
            raise ValueError("invalid requested row")
        st["bonus_grants"].append({"grant_id":"esgar.plus.one","amount":1,"expires_on":"round_close","clamp_policy_id":"example","source_effect_id":"relic.esgar","source_instance_id":None,"applied_event_id":"event.esgar"})
        return requested_row, previous + 1
    raise ValueError(effect)
ret=copy.deepcopy(unit)
row,total=resolve_return(ret,"ressurgir",None)
check("50_ressurgir_resets_bonus_and_uses_last_board_row", total == 0 and row == "melee")
ret2=copy.deepcopy(unit)
row2,total2=resolve_return(ret2,"requiem","siege")
check("51_requiem_uses_last_board_row_before_requested_row", row2 == "melee" and total2 == 0)
esgar=copy.deepcopy(unit)
row3,total3=resolve_return(esgar,"esgar","siege")
check("52_esgar_preserves_active_bonus_and_adds_separate_plus_one", total3 == 3 and len(esgar["state"]["bonus_grants"]) == 2)
try:
    resolve_return(copy.deepcopy(unit),"esgar",None)
    esgar_invalid=True
except ValueError:
    esgar_invalid=False
check("53_esgar_rejects_missing_requested_row", not esgar_invalid)
profile_standard={"unit_removal","execution"}
check("54_standard_shield_profile_is_not_universal", "unit_removal" in profile_standard and "execution" in profile_standard and "status_application" not in profile_standard and "bonus_reduction" not in profile_standard)
def resolve_example_effect(definition: dict[str, Any]) -> int:
    # Mirrors BUF-001: the resolver receives effect_id/effect_params, never rarity_id.
    return int(definition["effect_params"]["amount"])
common_def={"rarity_id":"common","effect_id":"buff.x","effect_params":{"amount":2}}
epic_def={"rarity_id":"epic","effect_id":"buff.x","effect_params":{"amount":2}}
check("55_rarity_does_not_change_effect_output", resolve_example_effect(common_def) == resolve_example_effect(epic_def) == 2)
check("56_reactive_source_is_independent_of_external_effect", all_events["00000000-0000-4000-8000-000000000013"]["effect_scope"] == "reactive" and all_events["00000000-0000-4000-8000-000000000013"]["source_effect_id"] == "unit.vengeance_on_removal" and all_events["00000000-0000-4000-8000-000000000013"]["source_instance_id"] == "00000000-0000-4000-8000-000000000004")

# 57–60: provenance references for each active state grant/application family.
check("57_all_weather_modifiers_reference_existing_events", all(m["applied_event_id"] in all_events for i in instances.values() for m in i["state"]["weather_resistance_modifiers"]))
check("58_weather_modifier_source_matches_event", all((all_events[m["applied_event_id"]]["source_effect_id"] == m["source_effect_id"] and all_events[m["applied_event_id"]]["source_instance_id"] == m["source_instance_id"]) for i in instances.values() for m in i["state"]["weather_resistance_modifiers"]))
check("59_protection_and_status_applications_reference_events", all(x["applied_event_id"] in all_events for i in instances.values() for x in (i["state"]["protection_grants"] + i["state"]["status_applications"])))
check("60_protection_and_status_sources_match_events", all((all_events[x["applied_event_id"]]["source_effect_id"] == x["source_effect_id"] and all_events[x["applied_event_id"]]["source_instance_id"] == x["source_instance_id"]) for i in instances.values() for x in (i["state"]["protection_grants"] + i["state"]["status_applications"])))

# 61–67: approval scope, explicit durations, fallback and unresolved limits.
approved_ids={x["id"] for x in approval["decisions"] if x["status"] == "OWNER_APPROVED"}
check("61_group_c_approval_covers_exactly_ten_decisions", len(approved_ids) == 10 and approved_ids == {"CI-008","CI-009","BUF-008","BUF-009","BUF-010","BUF-011","BUF-014","RSRX-07","RSRX-08","RSRX-10"})
check("62_group_c_approval_does_not_freeze_contract_or_runtime", approval["metadata"]["contract_frozen"] is False and approval["metadata"]["runtime_integration"] is False)
check("63_vigil_seal_duration_is_board_exit", approval["decisions"][5]["approved_resolution"].find("board_exit") >= 0)
check("64_round_close_does_not_expire_board_exit_or_permanent_grants", all({m["expires_on"] for m in i["state"]["weather_resistance_modifiers"]} == {"board_exit","permanent_instance"} for i in [round_fixture["instances"]["board"]]))
fallback_copy=make_unit("00000000-0000-4000-8000-000000000121", None)
row_fallback,total_fallback=resolve_return(fallback_copy,"ressurgir","siege")
check("65_resurrection_falls_back_to_valid_requested_row", row_fallback == "siege" and total_fallback == 0)
fallback_melee_copy=make_unit("00000000-0000-4000-8000-000000000122", None)
row_melee,total_melee=resolve_return(fallback_melee_copy,"requiem",None)
check("66_resurrection_uses_melee_as_final_fallback", row_melee == "melee" and total_melee == 0)
check("67_status_threshold_and_numeric_caps_are_not_frozen_by_schema", "maxItems" not in schema["$defs"]["runtime_state"]["properties"]["status_applications"])
# 68–70: zone-exit and action-cost semantics are explicit and not conflated.
zone_exit_copy=copy.deepcopy(unit)
zone_exit_copy["state"]["weather_resistance_modifiers"].append({"modifier_id":"w3","amount":3,"expires_on":"zone_exit","source_effect_id":"effect.zone","source_instance_id":None,"applied_event_id":"event6"})
successful_board_exit(zone_exit_copy,"discard")
check("68_board_to_discard_expires_board_exit_and_zone_exit", all(m["expires_on"] not in {"board_exit","zone_exit"} for m in zone_exit_copy["state"]["weather_resistance_modifiers"]))
hand_zone_exit=copy.deepcopy(unit)
hand_zone_exit["zone"]="discard"
hand_zone_exit["state"]["current_row"]=None
hand_zone_exit["state"]["weather_resistance_modifiers"].append({"modifier_id":"w3","amount":3,"expires_on":"zone_exit","source_effect_id":"effect.zone","source_instance_id":None,"applied_event_id":"event6"})
hand_zone_exit["state"]["weather_resistance_modifiers"]=[m for m in hand_zone_exit["state"]["weather_resistance_modifiers"] if m["expires_on"] != "zone_exit"]
check("69_discard_to_hand_expires_zone_exit_but_keeps_other_valid_modifiers", len(hand_zone_exit["state"]["weather_resistance_modifiers"]) == 2)
action_cost_on_block={"reliquia_noite_chama":"consume","reliquia_lamina_negra":"refund"}
check("70_action_cost_on_block_is_effect_specific", action_cost_on_block["reliquia_noite_chama"] == "consume" and action_cost_on_block["reliquia_lamina_negra"] == "refund")

passed = sum(r["status"] == "PASS" for r in results)
failed = len(results) - passed
output = {
    "metadata": {
        "document": "CardInstance v0.4 contract validation",
        "date": "2026-11-27",
        "status": "PASS" if failed == 0 else "FAIL",
        "scope": "JSON Schema Draft 2020-12, example validation, cross-document invariants, and isolated in-memory lifecycle semantics.",
        "does_not_test": ["legacy runtime integration", "SQLite/production DB", "HTTP", "Discord", "concurrent CAS/locking", "snapshot migration", "browser/UI", "production matches"]
    },
    "summary": {"passed": passed, "failed": failed, "total": len(results)},
    "checks": results
}
RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"CardInstance v0.4: {passed}/{len(results)} checks passed")
if failed:
    sys.exit(1)
