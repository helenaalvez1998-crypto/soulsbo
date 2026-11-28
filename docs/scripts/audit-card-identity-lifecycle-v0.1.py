#!/usr/bin/env python3
"""Read-only audit of physical card identity and discard/return lifecycle.

Runs controlled cases against the legacy Gwent resolver and the isolated
removal/resurrection candidate. It does not edit runtime code, DB, API or UI.
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import cartas, gwent  # noqa: E402
from sistemas import card_removal_resurrection_candidate as candidate  # noqa: E402

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("identity_lifecycle_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-identity-lifecycle-audit-v0.1.json"
BOT_SOURCE = (ROOT / "bot.py").read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def function_source(name: str) -> str:
    matches = [n for n in ast.walk(BOT_TREE)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(matches) != 1:
        raise AssertionError(f"Esperava uma função {name}; encontrei {len(matches)}")
    return ast.get_source_segment(BOT_SOURCE, matches[0]) or ""


def battle_state(hand: list[dict[str, Any]], *, board=None, discard=None,
                 leader_id="voz_caidos", faction="Véu Carmesim") -> dict[str, Any]:
    seed = hand[0] if hand else smoke.unit("seed")
    state = smoke.fixture(seed, str(seed.get("row") or "melee"))
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = hand
    p1["board"] = list(board or [])
    p1["discard"] = list(discard or [])
    p1["leader_id"] = leader_id
    p1["faction"] = faction
    p1["leader_used"] = False
    p1["passed"] = False
    p1["mulligan_done"] = True
    p1["faction_boost_used"] = True
    p1["synergy_used"] = {}
    p2["hand"] = [smoke.unit("enemy_reserve")]
    p2["board"] = [smoke.unit("enemy_board", power=1)]
    p2["discard"] = []
    p2["mulligan_done"] = True
    p2["faction_boost_used"] = True
    state["phase"] = "battle"
    state["round"] = 1
    state["turn"] = "1"
    state["weather"] = {"melee": 0, "ranged": 0, "siege": 0}
    state["rounds"] = []
    state["crowns"] = {"1": 0, "2": 0}
    return state


cases: list[dict[str, Any]] = []

def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        cases.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:
        cases.append({"case": name, "status": "failed",
                      "error": f"{type(exc).__name__}: {exc}"})


# 01-06: instance identity plumbing and legal-deck assumptions.
def test_deck_save_blocks_duplicate_model_ids():
    src = function_source("_api_gwent_deck_save")
    assert "len(entries) != 12" in src and "len(set(ids)) != 12" in src
    return {"finding": "new deck-save endpoint requires 12 distinct card_id models",
            "duplicate_models_allowed_by_current_save": False}


def test_snapshot_loader_does_not_revalidate_distinct_ids():
    src = function_source("_gwent_deck_snapshots")
    assert "return cards if len(cards) == 12 else None" in src
    assert "len(set(ids))" not in src
    return {"finding": "stored deck snapshot loader checks count, not card_id uniqueness",
            "legacy_or_malformed_saved_deck_can_reach_match_snapshot": True}


def test_standard_card_drops_exemplar_id_at_preparation():
    model = cartas.get_carta("chefe_guardiao_cinzas")
    assert model is not None
    payload = model.para_dict()
    payload["exemplar_id"] = 654321
    prepared = gwent.preparar_carta(payload)
    assert prepared["id"] == model.id
    assert "exemplar_id" not in prepared and "instance_id" not in prepared
    return {"card_id": prepared["id"], "source_exemplar_id": 654321,
            "prepared_exemplar_id": prepared.get("exemplar_id"),
            "prepared_instance_id": prepared.get("instance_id")}


def test_personal_card_uses_composite_id_but_no_instance_id():
    definition = {
        "card_id": "transmutacao_audit_0001", "nome": "Sentinela de Auditoria",
        "categoria": "Unidade", "faccao": "Ordem Áurea", "raridade": "Comum",
        "poder": 3, "custo": 0, "habilidade": "", "habilidades": [],
        "descricao": "Definição sintética de auditoria.", "arquetipo": "Sentinela",
        "epiteto": "da Graça Velada", "afinidades": ["sagrado"],
        "afinidade_dominante": "sagrado", "funcao_tatica": "defesa",
        "fileira": "melee", "origem_tipo": "transmutacao", "owner_scoped": True,
        "is_sacrificable": False,
        "ingredientes": [
            {"exemplar_id": "101", "card_id": "x1", "nome": "A", "raridade": "Comum", "faccao": "Ordem Áurea"},
            {"exemplar_id": "102", "card_id": "x2", "nome": "B", "raridade": "Comum", "faccao": "Ordem Áurea"},
            {"exemplar_id": "103", "card_id": "x3", "nome": "C", "raridade": "Comum", "faccao": "Ordem Áurea"},
        ],
    }
    exemplar = {"id": 654322, "card_id": definition["card_id"], "origin_type": "transmutacao",
                "is_sacrificable": 0, "user_id": 44, "rarity": "Comum", "power": 3}
    prepared = gwent.preparar_carta_pessoal(definition, exemplar, owner_id=44)
    assert prepared is not None
    assert prepared["id"] == f'{definition["card_id"]}::654322'
    assert prepared["exemplar_id"] == 654322 and "instance_id" not in prepared
    return {"card_id": prepared["card_id"], "runtime_id": prepared["id"],
            "exemplar_id": prepared["exemplar_id"], "instance_id": prepared.get("instance_id")}


def test_match_initializer_does_not_assign_instance_id():
    a = smoke.unit("ordinary_card", power=3, exemplar_id=111)
    filler = [smoke.unit(f"filler_{i}") for i in range(11)]
    state = gwent.novo_estado(99001, 1, 2, {"1": [a, *filler], "2": [smoke.unit(f"enemy_{i}") for i in range(12)]})
    match_card = state["players"]["1"]["hand"][0]
    assert match_card["id"] == "ordinary_card" and match_card.get("exemplar_id") == 111
    assert "instance_id" not in match_card
    return {"id": match_card["id"], "exemplar_id": match_card.get("exemplar_id"),
            "instance_id": match_card.get("instance_id")}


def test_target_summary_omits_physical_identity():
    unit = smoke.unit("same_model", exemplar_id=500, instance_id="match-1-player-1-500")
    summary = gwent._resumo_alvo(unit)
    assert summary["id"] == "same_model"
    assert "exemplar_id" not in summary and "instance_id" not in summary
    return {"serialized_fields": sorted(summary), "id_only": True}


# 07-10: real legacy lifecycle behavior.
def test_legacy_removal_uses_structural_equality():
    first = smoke.unit("duplicated_model", power=4, bonus=2)
    second = copy.deepcopy(first)
    assert first is not second and first == second
    side = {"board": [first, second], "discard": [], "baixas": 0}
    event = gwent._remover_unidade(side, second, "remocao")
    assert side["board"] == [second] and side["board"][0] is second
    assert side["discard"] == [second] and side["discard"][0] is second
    assert first not in side["board"] and first not in side["discard"]
    return {"event": event, "intended_object": "second", "object_left_on_board": "second",
            "object_sent_to_discard": "second", "first_equal_object_removed": True}


def test_legacy_removal_state_cleanup_is_partial():
    victim = smoke.unit("removal_victim", bonus=4, escudo=0, sangramento=1, geada=1,
                        podrida=1, loucura=1, weather_resist=2, combo_ativado="combo-x")
    side = {"board": [victim], "discard": [], "baixas": 0}
    event = gwent._remover_unidade(side, victim, "remocao")
    archived = side["discard"][0]
    assert archived["bonus"] == 4
    assert all(archived[k] == 0 for k in ("sangramento", "geada", "podrida", "loucura"))
    assert "escudo" not in archived and archived["weather_resist"] == 2
    assert archived["combo_ativado"] == "combo-x"
    return {"event": event, "bonus_retained": archived["bonus"], "statuses": {k: archived[k] for k in ("sangramento", "geada", "podrida", "loucura")},
            "shield_present": "escudo" in archived, "weather_resist_retained": archived["weather_resist"],
            "combo_marker_retained": archived.get("combo_ativado")}


def test_round_end_cleanup_resets_combat_state_not_weather_resistance():
    ally = smoke.unit("round_fallen", power=2, bonus=4, escudo=1, sangramento=1,
                      geada=1, podrida=1, loucura=1, weather_resist=2,
                      combo_ativado="combo-x", instance_id="persisted-inst-1")
    enemy = smoke.unit("round_winner", power=9)
    state = smoke.fixture(ally, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["board"], p2["board"] = [ally], [enemy]
    p1["discard"], p2["discard"] = [], []
    state["round"] = 1
    state["crowns"] = {"1": 0, "2": 0}
    state["rounds"] = []
    gwent._resolve_round(state)
    archived = p1["discard"][0]
    assert archived["bonus"] == 0 and archived["escudo"] == 0
    assert all(archived[k] == 0 for k in ("sangramento", "geada", "podrida", "loucura"))
    assert "combo_ativado" not in archived and archived["weather_resist"] == 2
    assert archived["instance_id"] == "persisted-inst-1"
    return {"bonus": archived["bonus"], "shield": archived["escudo"],
            "statuses": {k: archived[k] for k in ("sangramento", "geada", "podrida", "loucura")},
            "weather_resist": archived["weather_resist"], "combo_marker_present": "combo_ativado" in archived,
            "instance_id_preserved": archived["instance_id"]}


def test_medico_recovers_removed_unit_to_hand_with_bonus():
    victim = smoke.unit("medico_victim", power=3, bonus=4, escudo=0, sangramento=0,
                        geada=0, podrida=0, loucura=0, weather_resist=2)
    seed = smoke.unit("gwent_medico", skill="gwent_medico", power=0, special=True)
    state = battle_state([seed, smoke.unit("reserve")], board=[victim])
    removal_event = gwent._remover_unidade(state["players"]["1"], victim, "remocao")
    result = gwent.aplicar_jogada(state, 1, card_id="gwent_medico", action="play", row="melee", target_id="medico_victim")
    assert "error" not in result, result
    player = result["state"]["players"]["1"]
    returned = next(c for c in player["hand"] if c["id"] == "medico_victim")
    assert returned["bonus"] == 4 and returned["weather_resist"] == 2
    assert not any(c.get("id") == "medico_victim" for c in player["board"])
    assert not any(c.get("id") == "medico_victim" for c in player["discard"])
    assert any(c.get("id") == "gwent_medico" for c in player["discard"])
    return {"removal_event": removal_event, "destination": "hand", "bonus": returned["bonus"], "weather_resist": returned["weather_resist"],
            "statuses": {k: returned[k] for k in ("sangramento", "geada", "podrida", "loucura")}}


def test_requiem_resets_bonus_but_does_not_clear_stale_status():
    victim = smoke.unit("requiem_victim", power=4, bonus=5, escudo=1, sangramento=1,
                        geada=1, podrida=1, loucura=1, weather_resist=2, row="siege")
    card = smoke.unit("gwent_requiem", skill="gwent_requiem", power=0, special=True)
    result = gwent.aplicar_jogada(battle_state([card, smoke.unit("reserve")], discard=[victim]),
                                  1, card_id="gwent_requiem", action="play", row="ranged", target_id="requiem_victim")
    assert "error" not in result, result
    player = result["state"]["players"]["1"]
    returned = next(c for c in player["board"] if c["id"] == "requiem_victim")
    assert returned["bonus"] == 0 and "escudo" not in returned
    assert all(returned[k] == 1 for k in ("sangramento", "geada", "podrida", "loucura"))
    assert returned["row"] == "siege" and returned["weather_resist"] == 2
    return {"destination": "board", "bonus": returned["bonus"], "shield_present": "escudo" in returned,
            "statuses_preserved": {k: returned[k] for k in ("sangramento", "geada", "podrida", "loucura")},
            "row": returned["row"], "weather_resist": returned["weather_resist"]}


def test_ressurgir_resets_bonus_but_does_not_clear_stale_status():
    victim = smoke.unit("ressurgir_victim", power=4, bonus=5, escudo=1, sangramento=1,
                        geada=1, podrida=1, loucura=1, weather_resist=2, row="siege")
    card = smoke.unit("synthetic_ressurgir", skill="ressurgir", power=4, row="melee")
    result = gwent.aplicar_jogada(battle_state([card, smoke.unit("reserve")], discard=[victim]),
                                  1, card_id="synthetic_ressurgir", action="play", row="melee")
    assert "error" not in result, result
    player = result["state"]["players"]["1"]
    returned = next(c for c in player["board"] if c["id"] == "ressurgir_victim")
    assert returned["bonus"] == 0 and "escudo" not in returned
    assert all(returned[k] == 1 for k in ("sangramento", "geada", "podrida", "loucura"))
    assert returned["row"] == "siege" and returned["weather_resist"] == 2
    return {"destination": "board", "bonus": returned["bonus"], "shield_present": "escudo" in returned,
            "statuses_preserved": {k: returned[k] for k in ("sangramento", "geada", "podrida", "loucura")},
            "row": returned["row"], "weather_resist": returned["weather_resist"]}


def test_esgar_removes_every_discard_entry_with_same_id():
    first = smoke.unit("esgar_same_model", power=5, bonus=3, escudo=1, sangramento=1,
                       geada=1, podrida=1, loucura=1, exemplar_id=7001)
    second = copy.deepcopy(first)
    second["exemplar_id"] = 7002
    card = smoke.unit("reserve", power=1)
    result = gwent.aplicar_jogada(battle_state([card], discard=[first, second]),
                                  1, action="leader", row="ranged")
    assert "error" not in result, result
    player = result["state"]["players"]["1"]
    returned = next(c for c in player["board"] if c["id"] == "esgar_same_model")
    assert not any(c["id"] == "esgar_same_model" for c in player["discard"])
    assert returned["bonus"] == 4 and returned["row"] == "ranged" and "escudo" not in returned
    assert all(returned[k] == 0 for k in ("sangramento", "geada", "podrida", "loucura"))
    return {"same_model_discard_entries_before": 2, "same_model_discard_entries_after": 0,
            "one_returned": True, "bonus_after": returned["bonus"], "row": returned["row"],
            "statuses_after": {k: returned[k] for k in ("sangramento", "geada", "podrida", "loucura")}}


# 11-14: candidate's identity safeguards and remaining validation gaps.
def test_candidate_removes_exact_equal_but_distinct_object():
    first = smoke.unit("equal_copy", instance_id="copy-1")
    second = copy.deepcopy(first)
    second["instance_id"] = "copy-2"
    # Keep every other field equal, but distinct physical identities.
    side = {"board": [first, second], "discard": [], "baixas": 0}
    result = candidate.attempt_removal(side, second, "normal_removal")
    assert result.removed and side["board"][0] is first and side["discard"][0] is second
    return {"selected_instance_id": result.unit_id, "board_instance_id": side["board"][0]["instance_id"],
            "discard_instance_id": side["discard"][0]["instance_id"]}


def test_candidate_does_not_reject_duplicate_instance_id_on_board():
    one = {"id": "card-a", "instance_id": "collision-1", "kind": "unit", "power_base": 3, "row": "melee", "bonus": 0}
    two = {"id": "card-b", "instance_id": "collision-1", "kind": "unit", "power_base": 4, "row": "melee", "bonus": 0}
    side = {"board": [one, two], "discard": [], "baixas": 0}
    result = candidate.attempt_removal(side, two, "normal_removal")
    assert result.removed and side["board"][0]["instance_id"] == side["discard"][0]["instance_id"]
    return {"duplicate_instance_id": "collision-1", "remaining_on_board": True,
            "also_in_discard": True, "candidate_detected_collision": False}


def test_candidate_resurrection_does_not_check_cross_zone_collision():
    existing = {"id": "card-existing", "instance_id": "collision-2", "kind": "unit", "power_base": 2, "row": "melee", "bonus": 0}
    fallen = {"id": "card-fallen", "instance_id": "collision-2", "kind": "unit", "power_base": 3, "row": "melee", "bonus": 1}
    side = {"board": [existing], "discard": [fallen], "hand": [], "draw_pile": []}
    result = candidate.resurrect_from_discard(side, max_power=5, row="ranged", target_instance_id="collision-2")
    assert result.resurrected["instance_id"] == existing["instance_id"]
    assert len([u for u in side["board"] if u["instance_id"] == "collision-2"]) == 2
    return {"instance_id": "collision-2", "copies_on_board_after": 2,
            "candidate_detected_collision": False}


def test_candidate_rejects_ambiguous_duplicate_instance_id_in_discard():
    d1 = {"id": "card", "instance_id": "dup-discard", "kind": "unit", "power_base": 3, "row": "melee"}
    d2 = copy.deepcopy(d1)
    side = {"board": [], "discard": [d1, d2]}
    try:
        candidate.resurrect_from_discard(side, max_power=5, row="melee", target_instance_id="dup-discard")
    except candidate.RemovalResurrectionError as exc:
        assert "não identifica exatamente" in str(exc)
        return {"duplicate_instance_id": "dup-discard", "ambiguous_target_rejected": True}
    raise AssertionError("O candidato deveria rejeitar um instance_id ambíguo")


for name, fn in [
    ("deck_save_blocks_duplicate_model_ids", test_deck_save_blocks_duplicate_model_ids),
    ("snapshot_loader_does_not_revalidate_distinct_ids", test_snapshot_loader_does_not_revalidate_distinct_ids),
    ("standard_card_drops_exemplar_id_at_preparation", test_standard_card_drops_exemplar_id_at_preparation),
    ("personal_card_uses_composite_id_but_no_instance_id", test_personal_card_uses_composite_id_but_no_instance_id),
    ("match_initializer_does_not_assign_instance_id", test_match_initializer_does_not_assign_instance_id),
    ("target_summary_omits_physical_identity", test_target_summary_omits_physical_identity),
    ("legacy_removal_uses_structural_equality", test_legacy_removal_uses_structural_equality),
    ("legacy_removal_state_cleanup_is_partial", test_legacy_removal_state_cleanup_is_partial),
    ("round_end_cleanup_resets_combat_state_not_weather_resistance", test_round_end_cleanup_resets_combat_state_not_weather_resistance),
    ("medico_recovers_removed_unit_to_hand_with_bonus", test_medico_recovers_removed_unit_to_hand_with_bonus),
    ("requiem_resets_bonus_but_does_not_clear_stale_status", test_requiem_resets_bonus_but_does_not_clear_stale_status),
    ("ressurgir_resets_bonus_but_does_not_clear_stale_status", test_ressurgir_resets_bonus_but_does_not_clear_stale_status),
    ("esgar_removes_every_discard_entry_with_same_id", test_esgar_removes_every_discard_entry_with_same_id),
    ("candidate_removes_exact_equal_but_distinct_object", test_candidate_removes_exact_equal_but_distinct_object),
    ("candidate_does_not_reject_duplicate_instance_id_on_board", test_candidate_does_not_reject_duplicate_instance_id_on_board),
    ("candidate_resurrection_does_not_check_cross_zone_collision", test_candidate_resurrection_does_not_check_cross_zone_collision),
    ("candidate_rejects_ambiguous_duplicate_instance_id_in_discard", test_candidate_rejects_ambiguous_duplicate_instance_id_in_discard),
]:
    check(name, fn)

passed = sum(c["status"] == "passed" for c in cases)
failed = len(cases) - passed
report = {
    "metadata": {
        "document": "Card identity and lifecycle audit v0.1",
        "date": "2026-11-27",
        "status": "READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED",
        "baseline": "soulsbo-main-continuity-2026-11-27-rev2.zip",
        "legacy_engine": "sistemas.gwent",
        "candidate_engine": "sistemas.card_removal_resurrection_candidate",
        "method": "Direct controlled fixtures plus static AST checks of deck-save/snapshot functions; no DB or production session.",
        "source_references": {
            "deck_save": "bot.py:_api_gwent_deck_save",
            "deck_snapshot": "bot.py:_gwent_deck_snapshots",
            "card_preparation": "sistemas/gwent.py:preparar_carta/preparar_carta_pessoal",
            "match_initialization": "sistemas/gwent.py:novo_estado",
            "legacy_removal": "sistemas/gwent.py:_remover_unidade",
            "target_payload": "sistemas/gwent.py:_resumo_alvo",
            "round_cleanup": "sistemas/gwent.py:_resolve_round",
            "return_to_hand": "sistemas/gwent.py:gwent_medico",
            "resurrection": "sistemas/gwent.py:gwent_requiem/ressurgir",
            "leader_resurrection": "sistemas/gwent.py:voz_caidos (Esgar)",
            "candidate_resolver": "sistemas/card_removal_resurrection_candidate.py",
        },
    },
    "counts": {"assertions": len(cases), "passed": passed, "failed": failed},
    "cases": cases,
    "limitations": [
        "Synthetic states reproduce edge cases; they do not establish that a live user database currently contains duplicate card IDs.",
        "The current deck-save endpoint rejects repeated card_id models, but legacy saved decks and direct snapshot construction are not revalidated for uniqueness.",
        "No real SQLite, HTTP, Discord, browser, R2 or production match was accessed.",
        "Status carry-over in Requiem/Ressurgir is proven for a deliberately pre-populated stale discard record. The central removal path clears those status counters first.",
        "A passed case means the asserted behavior or gap was reproduced; it does not mean the observed behavior is desirable or an approved design rule.",
        "The audit does not approve a design rule or integrate the candidate resolver into the legacy runtime.",
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
for case in cases:
    if case["status"] != "passed":
        print(json.dumps(case, ensure_ascii=False))
print(f"wrote {OUT}")
if failed:
    raise SystemExit(1)
