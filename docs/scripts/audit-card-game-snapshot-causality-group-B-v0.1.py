#!/usr/bin/env python3
"""Read-only audit of Group B: definition snapshot and effect causality.

Uses static source inspection plus synthetic executions against the legacy engine.
It does not modify runtime/gameplay source, catalog data, or the database schema.
Run from repository root:
    python docs/scripts/audit-card-game-snapshot-causality-group-B-v0.1.py
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT = DOCS / "card-game-snapshot-causality-group-B-audit-v0.1.json"
sys.path.insert(0, str(ROOT))

from sistemas import gwent  # noqa: E402

SMOKE_PATH = DOCS / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("group_b_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

GWENT = (ROOT / "sistemas/gwent.py").read_text(encoding="utf-8")
DB = (ROOT / "database.py").read_text(encoding="utf-8")
BASELINE = json.loads((ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json").read_text(encoding="utf-8"))
EFFECT_REGISTRY = json.loads((ROOT / "data/card_game/effect-registry-candidate.v1.json").read_text(encoding="utf-8"))
EXAMPLE_V2 = json.loads((DOCS / "examples/card-instance-match.example.v2.json").read_text(encoding="utf-8"))

cases: list[dict[str, Any]] = []

def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        cases.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:
        cases.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})

def need(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def section(source: str, start: str, end: str) -> str:
    a = source.index(start)
    b = source.index(end, a + len(start))
    return source[a:b]


def test_legacy_baseline_is_historical_not_runtime_authority() -> dict[str, Any]:
    need(BASELINE.get("snapshot_type") == "legacy_catalog_baseline", "unexpected snapshot_type")
    need(BASELINE.get("status") == "historical_snapshot_not_runtime_source_of_truth", "baseline status changed")
    need(bool(BASELINE.get("source_files_sha256")), "source file provenance hashes missing")
    need(BASELINE.get("snapshot_version") == "0.1", "historical snapshot version changed")
    return {"snapshot_type": BASELINE["snapshot_type"], "baseline_status": BASELINE["status"], "source_hash_count": len(BASELINE["source_files_sha256"])}


def test_source_hashes_are_provenance_not_definition_manifest() -> dict[str, Any]:
    hashes = BASELINE["source_files_sha256"]
    need(all(re.fullmatch(r"[0-9a-f]{64}", v or "") for v in hashes.values()), "invalid source SHA-256")
    forbidden = {"catalog_release_id", "effect_registry_release_id", "balance_rules_release_id", "definition_digest", "ruleset_manifest_digest"}
    present = forbidden.intersection(BASELINE)
    need(not present, f"historical baseline unexpectedly contains release fields: {sorted(present)}")
    return {"hashes_are_source_provenance": True, "missing_release_fields": sorted(forbidden)}


def test_effect_registry_is_candidate_without_immutable_release_metadata() -> dict[str, Any]:
    need(EFFECT_REGISTRY.get("schema_version") == 1, "effect registry schema version changed")
    need(isinstance(EFFECT_REGISTRY.get("effects"), list) and len(EFFECT_REGISTRY["effects"]) > 0, "candidate effects missing")
    fields = {"release_id", "catalog_release_id", "effect_registry_release_id", "content_digest", "sha256"}
    present = fields.intersection(EFFECT_REGISTRY)
    need(not present, f"candidate registry has unexpected release metadata: {sorted(present)}")
    return {"schema_version": EFFECT_REGISTRY["schema_version"], "effect_count": len(EFFECT_REGISTRY["effects"]), "release_metadata_present": False}


def test_balance_rules_are_specified_as_future_compiler_output_not_current_release() -> dict[str, Any]:
    spec_text = (DOCS / "card-game-balance-spec-v0.1.md").read_text(encoding="utf-8")
    canonical_text = (DOCS / "card-game-canonical-model-v1.md").read_text(encoding="utf-8")
    need("balance_rules_version" in canonical_text, "balance_rules_version reference missing from canonical model")
    need("Depois de aprovada" in canonical_text or "Depois de aprovado" in canonical_text, "canonical model no longer marks compiler output as future/conditional")
    need("RARITY_EFFECT_BUDGET" in (ROOT / "sistemas/gwent.py").read_text(encoding="utf-8"), "legacy rarity budget constant disappeared; review the current behavior")
    need("Raridade é classificação, não multiplicador de habilidade" in spec_text, "balance spec no longer states rarity should not amplify effect magnitude")
    need(not any(p.name.startswith("balance-rules-release") for p in (ROOT / "data/card_game").iterdir()), "unexpected balance release artifact exists")
    return {"balance_rules_version": "future compiler output described by spec", "approved_release_artifact_found": False}


def test_v2_example_uses_placeholder_version_labels() -> dict[str, Any]:
    instances = EXAMPLE_V2.get("instances", {})
    need(bool(instances), "v2 example has no instances")
    labels = {(v.get("definition_snapshot", {}).get("catalog_version"), v.get("definition_snapshot", {}).get("balance_rules_version")) for v in instances.values()}
    need(labels == {("soulsbo-catalog-v1", "balance-v0.2")}, f"unexpected example version labels: {labels}")
    return {"version_labels": [{"catalog_version": a, "balance_rules_version": b} for a, b in sorted(labels)], "interpretation": "example placeholders, not evidence of published releases"}


def test_legacy_engine_does_not_build_definition_snapshot() -> dict[str, Any]:
    need("definition_snapshot" not in GWENT, "legacy engine now references definition_snapshot; inspect audit baseline")
    constructor = section(GWENT, "def novo_estado(", "def _registrar_evento(")
    need("catalog_release_id" not in constructor and "definition_digest" not in constructor, "match constructor unexpectedly writes manifest")
    return {"definition_snapshot_in_legacy_engine": False, "manifest_in_novo_estado": False}


def test_novo_estado_has_no_catalog_or_ruleset_manifest() -> dict[str, Any]:
    constructor = section(GWENT, "def novo_estado(", "def _registrar_evento(")
    forbidden = ("catalog_version", "balance_rules_version", "catalog_release_id", "effect_registry_release_id", "balance_rules_release_id", "definition_digest")
    present = [key for key in forbidden if key in constructor]
    need(not present, f"novo_estado unexpectedly includes manifest keys: {present}")
    return {"manifest_fields_in_match_constructor": present, "match_state_fields": ["match_id", "status", "phase", "round", "players", "weather", "rounds", "event_log"]}


def test_aplicar_jogada_has_no_operation_or_causal_context_parameters() -> dict[str, Any]:
    sig = section(GWENT, "def aplicar_jogada(", ") -> dict:")
    need("operation_id" not in sig and "event_id" not in sig and "parent_event_id" not in sig, "operation/causal params appeared; revise audit")
    need("operation_id" not in GWENT and "parent_event_id" not in GWENT and "source_effect_id" not in GWENT, "causal metadata now appears in runtime; revise audit")
    return {"legacy_signature": sig.strip(), "operation_id_supported": False, "causal_event_fields_found": False}


def test_event_log_is_short_descriptive_text_not_causal_ledger() -> dict[str, Any]:
    registrar = section(GWENT, "def _registrar_evento(", "def ")
    need("event_log" in registrar and "history[-20:]" in registrar, "event log behavior changed")
    need("event_id" not in registrar and "parent_event_id" not in registrar and "source_effect_id" not in registrar, "event_log now contains causal fields")
    need('"last_event"' in GWENT and "str(state.get(\"last_event\"" in registrar, "last_event string behavior not found")
    return {"event_log_type": "bounded list of descriptive strings", "retention": 20, "causal_links": False}


def test_rarity_amplifier_uses_global_bonus_delta_scan_and_python_object_identity() -> dict[str, Any]:
    rarity = section(GWENT, "def _aplicar_potencia_raridade(", "def preparar_carta(")
    need("for side in (player, other)" in rarity, "rarity scan no longer traverses both sides")
    need("old = bonus_antes.get(id(unit))" in rarity, "rarity scan object identity implementation changed")
    need("changes.append((unit, delta))" in rarity, "rarity scan does not collect global bonus changes")
    return {"scan_scope": "both player boards plus played card", "tracking_key": "id(unit)", "effect_source_attribution": False}


def test_removal_triggers_vengeance_synchronously_without_event_context() -> dict[str, Any]:
    remove = section(GWENT, "def _remover_unidade(", "def pontuacao(")
    need('if unit.get("habilidade") == "vinganca"' in remove, "Vingança trigger branch changed")
    need('aliado["bonus"] = int(aliado.get("bonus", 0)) + 1' in remove, "Vingança bonus application changed")
    need("event_id" not in remove and "parent_event_id" not in remove, "removal now carries causal event metadata")
    return {"trigger": "synchronous inside _remover_unidade", "bonus_delta": 1, "causal_event_record": False}


def test_chama_negra_calls_removal_before_global_rarity_pass() -> dict[str, Any]:
    special_branch = section(GWENT, 'elif skill == "gwent_queima":', 'elif skill == "gwent_purificar":')
    need("_remover_unidade(side, strongest)" in special_branch, "Chama Negra no longer calls removal helper")
    apply_pos = GWENT.index("_aplicar_potencia_raridade(card, player, other, bonus_antes, bonus_card_antes)")
    special_pos = GWENT.index('elif skill == "gwent_queima":')
    need(special_pos < apply_pos, "rarity amplifier now occurs before Chama Negra resolution")
    return {"sequence": ["Chama Negra selects strongest units", "_remover_unidade triggers Vingança synchronously", "rarity amplifier scans all bonus deltas"], "causal_attribution": "not represented"}


def test_rykard_is_sacrifice_then_vengeance_then_direct_plus_two() -> dict[str, Any]:
    rykard = section(GWENT, 'elif effect == "rykard_devour":', 'elif effect == "esgar_blood_priest":')
    need('_remover_unidade(player, victim, "sacrificio")' in rykard, "Rykard no longer uses sacrifice removal helper")
    need('unit["bonus"] = int(unit.get("bonus", 0)) + 2' in rykard, "Rykard +2 direct bonus changed")
    need("_aplicar_potencia_raridade" not in rykard, "Rykard leader branch unexpectedly calls rarity amplifier")
    return {"sequence": ["leader selects weakest ally", "sacrifice removal", "reactive Vingança if victim has it", "Rykard +2 to surviving allies in selected row"], "rarity_budget_on_leader_action": False}


def test_match_table_persists_state_json_without_revision_or_idempotency_ledger() -> dict[str, Any]:
    table = section(DB, "CREATE TABLE IF NOT EXISTS cartas_gwent_matches (", ");")
    columns = re.findall(r"^\s*([a-z_]+)\s+(?:INTEGER|TEXT|REAL|BLOB)", table, flags=re.M)
    need("state_json" in columns, "state_json column missing")
    forbidden = {"state_revision", "operation_id", "idempotency_key", "event_log_id", "definition_digest"}
    present = forbidden.intersection(columns)
    need(not present, f"match table now has some new fields; review audit: {sorted(present)}")
    return {"match_columns": columns, "revision_or_idempotency_columns": sorted(present), "persisted_state_container": "state_json"}


def test_chama_negra_runtime_reproduces_indirect_rarity_amplification() -> dict[str, Any]:
    card = smoke.unit("group_b_queima", skill="gwent_queima", special=True, rarity="Épica")
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["board"] = [
        smoke.unit("group_b_vengeance_victim", skill="vinganca", power=9, row="melee"),
        smoke.unit("group_b_first_survivor", power=3, row="melee"),
        smoke.unit("group_b_second_survivor", power=4, row="melee"),
    ]
    p1["hand"] = [card, smoke.unit("group_b_reserve")]
    p1["faction"] = "Lua Negra"
    p1["faction_boost_used"] = True
    p2["board"] = [smoke.unit("group_b_enemy_strongest", power=10), smoke.unit("group_b_enemy_survivor", power=2)]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    need("error" not in result, f"Chama Negra failed: {result}")
    board = result["state"]["players"]["1"]["board"]
    bonuses = {unit["id"]: int(unit.get("bonus", 0)) for unit in board}
    need(bonuses.get("group_b_first_survivor") == 2 and bonuses.get("group_b_second_survivor") == 1, f"unexpected bonus deltas: {bonuses}")
    return {"observed_survivor_bonuses": {"first": bonuses["group_b_first_survivor"], "second": bonuses["group_b_second_survivor"]}, "vengeance_only_expected": {"first": 1, "second": 1}, "interpretation": "rarity budget is applied to a Vingança delta that is not directly produced by Chama Negra"}


def test_rykard_runtime_reproduces_plus_three_composition() -> dict[str, Any]:
    base = smoke.unit("group_b_rykard_fixture")
    state = smoke.fixture(base, "melee")
    player = state["players"]["1"]
    player["faction"] = "Véu Carmesim"
    player["leader_id"] = "sombra_caminhante"
    player["leader_used"] = False
    victim = smoke.unit("group_b_rykard_victim", skill="vinganca", row="melee", power=1)
    ally_a = smoke.unit("group_b_rykard_ally_a", row="melee", power=3, bonus=0)
    ally_b = smoke.unit("group_b_rykard_ally_b", row="melee", power=4, bonus=0)
    player["board"] = [victim, ally_a, ally_b]
    player["hand"] = [smoke.unit("group_b_rykard_reserve")]
    result = gwent.aplicar_jogada(state, 1, action="leader", row="melee")
    need("error" not in result, f"Rykard failed: {result}")
    after = result["state"]["players"]["1"]
    bonuses = {item["id"]: int(item.get("bonus", 0)) for item in after["board"]}
    need(bonuses.get("group_b_rykard_ally_a") == 3 and bonuses.get("group_b_rykard_ally_b") == 3, f"unexpected Rykard result: {bonuses}")
    need(any(item.get("id") == "group_b_rykard_victim" for item in after["discard"]), "Vingança victim was not sacrificed")
    return {"survivor_bonuses": {"ally_a": bonuses["group_b_rykard_ally_a"], "ally_b": bonuses["group_b_rykard_ally_b"]}, "composition": {"reactive_vengeance": 1, "direct_rykard_bonus": 2, "total": 3}}


def make_causal_fixture() -> dict[str, Any]:
    operation_id = str(uuid.uuid4())
    root_event = str(uuid.uuid4())
    removal_event = str(uuid.uuid4())
    vengeance_event = str(uuid.uuid4())
    followup_event = str(uuid.uuid4())
    return {
        "operation_id": operation_id,
        "expected_revision": 12,
        "definition_manifest": {
            "catalog_release_id": "catalog-release-example-01",
            "effect_registry_release_id": "effects-release-example-01",
            "balance_rules_release_id": "balance-release-example-01",
            "definition_digest": "sha256:" + "a" * 64,
        },
        "events": [
            {"event_id": root_event, "caused_by_event_ids": [], "sequence": 1, "kind": "operation_started", "effect_scope": "none"},
            {"event_id": removal_event, "caused_by_event_ids": [root_event], "sequence": 2, "kind": "unit_removed", "effect_scope": "direct", "source_effect_id": "special.remove_units", "source_instance_id": str(uuid.uuid4()), "target_instance_ids": [str(uuid.uuid4())]},
            {"event_id": vengeance_event, "caused_by_event_ids": [removal_event], "sequence": 3, "kind": "revenge_bonus_applied", "effect_scope": "reactive", "source_effect_id": "unit.death_revenge", "source_instance_id": str(uuid.uuid4()), "target_instance_ids": [str(uuid.uuid4())], "rarity_inheritance": "none"},
            {"event_id": followup_event, "caused_by_event_ids": [removal_event], "sequence": 4, "kind": "survivor_bonus_applied", "effect_scope": "direct", "source_effect_id": "leader.rykard_devour", "source_instance_id": str(uuid.uuid4()), "target_instance_ids": [str(uuid.uuid4())]},
        ],
        "rarity_scope": "direct_effect_outputs_only",
    }


def validate_causal_fixture(value: dict[str, Any]) -> None:
    manifest = value.get("definition_manifest")
    need(isinstance(manifest, dict), "definition_manifest missing")
    for key in ("catalog_release_id", "effect_registry_release_id", "balance_rules_release_id", "definition_digest"):
        need(bool(manifest.get(key)), f"manifest field {key} missing")
    need(re.fullmatch(r"sha256:[0-9a-f]{64}", manifest["definition_digest"]) is not None, "invalid definition_digest")
    need(uuid.UUID(value["operation_id"]).version == 4, "operation_id must be UUIDv4")
    events = value.get("events")
    ids = [e.get("event_id") for e in events]
    need(len(ids) == len(set(ids)), "event_id collision")
    for event_id in ids:
        need(uuid.UUID(event_id).version == 4, "event_id must be UUIDv4")
    seqs = [e.get("sequence") for e in events]
    need(seqs == sorted(seqs) and len(seqs) == len(set(seqs)), "event sequence must be unique and monotonic")
    known = set(ids)
    parents: dict[str, list[str]] = {}
    for event in events:
        causes = event.get("caused_by_event_ids")
        need(isinstance(causes, list) and len(causes) == len(set(causes)), "causal parents must be a unique array")
        need(all(parent in known for parent in causes), "event parent missing")
        need(event["event_id"] not in causes, "event cannot cause itself")
        parents[event["event_id"]] = causes
        if event.get("effect_scope") == "reactive":
            need(event.get("source_effect_id") == "unit.death_revenge", "reactive effect source incorrectly inherited")
            need(event.get("rarity_inheritance") == "none", "reactive event inherited root rarity")
    # Causal links form a DAG; a sequence number alone is not a causal explanation.
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(event_id: str) -> None:
        if event_id in visiting:
            raise AssertionError("causal graph contains cycle")
        if event_id in visited:
            return
        visiting.add(event_id)
        for parent in parents[event_id]:
            visit(parent)
        visiting.remove(event_id)
        visited.add(event_id)
    for event_id in ids:
        visit(event_id)
    need(value.get("rarity_scope") == "direct_effect_outputs_only", "rarity scope not explicit")


def test_candidate_causal_event_graph_is_well_formed() -> dict[str, Any]:
    fixture = make_causal_fixture()
    validate_causal_fixture(fixture)
    need(len({fixture["operation_id"], *[event["event_id"] for event in fixture["events"]]}) == len(fixture["events"]) + 1, "operation_id and event IDs must be distinct")
    return {"event_count": len(fixture["events"]), "operation_id_distinct_from_event_ids": True, "manifest_fields": list(fixture["definition_manifest"]), "rarity_scope": fixture["rarity_scope"]}


def test_reject_causal_event_with_missing_parent() -> dict[str, Any]:
    fixture = make_causal_fixture()
    fixture["events"][2]["caused_by_event_ids"] = [str(uuid.uuid4())]
    try:
        validate_causal_fixture(fixture)
    except AssertionError as exc:
        need("parent" in str(exc), f"unexpected rejection reason: {exc}")
        return {"invalid_parent_rejected": True}
    raise AssertionError("event with missing parent was accepted")


def test_reject_causal_cycle() -> dict[str, Any]:
    fixture = make_causal_fixture()
    fixture["events"][0]["caused_by_event_ids"] = [fixture["events"][1]["event_id"]]
    try:
        validate_causal_fixture(fixture)
    except AssertionError as exc:
        need("cycle" in str(exc), f"unexpected rejection reason: {exc}")
        return {"causal_cycle_rejected": True}
    raise AssertionError("causal cycle was accepted")


def test_reject_reactive_event_inheriting_source_rarity() -> dict[str, Any]:
    fixture = make_causal_fixture()
    fixture["events"][2]["rarity_inheritance"] = "root_card"
    try:
        validate_causal_fixture(fixture)
    except AssertionError as exc:
        need("rarity" in str(exc), f"unexpected rejection reason: {exc}")
        return {"implicit_rarity_inheritance_rejected": True}
    raise AssertionError("reactive event inheriting root rarity was accepted")


checks = [
    ("legacy_catalog_baseline_is_historical_not_runtime_authority", test_legacy_baseline_is_historical_not_runtime_authority),
    ("source_hashes_are_provenance_not_definition_manifest", test_source_hashes_are_provenance_not_definition_manifest),
    ("effect_registry_is_candidate_without_immutable_release_metadata", test_effect_registry_is_candidate_without_immutable_release_metadata),
    ("balance_rules_are_future_compiler_output_not_current_release", test_balance_rules_are_specified_as_future_compiler_output_not_current_release),
    ("v2_example_uses_placeholder_version_labels", test_v2_example_uses_placeholder_version_labels),
    ("legacy_engine_does_not_build_definition_snapshot", test_legacy_engine_does_not_build_definition_snapshot),
    ("novo_estado_has_no_catalog_or_ruleset_manifest", test_novo_estado_has_no_catalog_or_ruleset_manifest),
    ("aplicar_jogada_has_no_operation_or_causal_context_parameters", test_aplicar_jogada_has_no_operation_or_causal_context_parameters),
    ("event_log_is_short_descriptive_text_not_causal_ledger", test_event_log_is_short_descriptive_text_not_causal_ledger),
    ("rarity_amplifier_uses_global_bonus_delta_scan_and_python_object_identity", test_rarity_amplifier_uses_global_bonus_delta_scan_and_python_object_identity),
    ("removal_triggers_vengeance_synchronously_without_event_context", test_removal_triggers_vengeance_synchronously_without_event_context),
    ("chama_negra_calls_removal_before_global_rarity_pass", test_chama_negra_calls_removal_before_global_rarity_pass),
    ("rykard_is_sacrifice_then_vengeance_then_direct_plus_two", test_rykard_is_sacrifice_then_vengeance_then_direct_plus_two),
    ("match_table_persists_state_json_without_revision_or_idempotency_ledger", test_match_table_persists_state_json_without_revision_or_idempotency_ledger),
    ("chama_negra_runtime_reproduces_indirect_rarity_amplification", test_chama_negra_runtime_reproduces_indirect_rarity_amplification),
    ("rykard_runtime_reproduces_plus_three_composition", test_rykard_runtime_reproduces_plus_three_composition),
    ("candidate_causal_event_graph_is_well_formed", test_candidate_causal_event_graph_is_well_formed),
    ("reject_causal_event_with_missing_parent", test_reject_causal_event_with_missing_parent),
    ("reject_causal_cycle", test_reject_causal_cycle),
    ("reject_reactive_event_inheriting_source_rarity", test_reject_reactive_event_inheriting_source_rarity),
]
for name, fn in checks:
    check(name, fn)

report = {
    "metadata": {
        "document": "Group B — snapshot and causality audit v0.1",
        "baseline": "soulsbo-main-continuity-2026-11-27-rev7.zip",
        "status": "READ_ONLY_AUDIT; DESIGN_CANDIDATE_NOT_APPROVED",
        "method": "Static inspection of legacy engine/DB/catalog artifacts plus synthetic match fixtures invoking legacy aplicar_jogada and validating a proposed causal-event envelope.",
        "runtime_modified": False,
        "production_database_used": False,
        "scope": ["CI-005", "CI-011", "BUF-001", "BUF-002", "BUF-012", "RSRX-03", "RSRX-05"],
    },
    "passed": sum(c["status"] == "passed" for c in cases),
    "failed": sum(c["status"] == "failed" for c in cases),
    "cases": cases,
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": report["passed"], "failed": report["failed"], "output": str(OUT.relative_to(ROOT))}, ensure_ascii=False))
if report["failed"]:
    for item in cases:
        if item["status"] == "failed":
            print(f"FAIL {item['case']}: {item['error']}")
    raise SystemExit(1)
