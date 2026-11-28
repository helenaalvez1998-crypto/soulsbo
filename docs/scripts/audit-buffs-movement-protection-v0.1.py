#!/usr/bin/env python3
"""Focused behavior audit for buffs, movement, protection and weather.

Diagnostic only. Uses synthetic, controlled match states and the legacy engine;
no production runtime, database, API, frontend or card data is modified.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("buff_movement_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-buffs-movement-protection-audit-v0.1.json"


def prepare_play(card: dict[str, Any], row: str = "melee", *, target_id: str | None = None) -> dict[str, Any]:
    state = smoke.fixture(card, row)
    p1 = state["players"]["1"]
    p1["hand"] = [card, smoke.unit("audit_reserve", power=1)]
    p1["faction"] = "Lua Negra"  # isolates tested effects from the faction passive
    p1["faction_boost_used"] = True
    result = gwent.aplicar_jogada(
        state, 1, card_id=card["id"], action="play", row=row, target_id=target_id
    )
    return result


cases: list[dict[str, Any]] = []


def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        cases.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:
        cases.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


def test_vinculo_requires_two_allies() -> dict[str, Any]:
    card = smoke.unit("audit_vinculo", skill="gwent_vinculo", special=True)
    state = smoke.fixture(card, "melee")
    p1 = state["players"]["1"]
    p1["board"] = [smoke.unit("only_ally", row="melee")]
    p1["hand"] = [card, smoke.unit("reserve")]
    p1["faction"] = "Lua Negra"
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" in result and "duas unidades" in result["error"], result
    return {"expected": "reject below minimum of two pre-existing allies", "observed_error": result["error"]}


def test_muralha_empty_row_is_consumed_without_effect() -> dict[str, Any]:
    card = smoke.unit("audit_muralha", skill="gwent_muralha", special=True)
    state = smoke.fixture(card, "melee")
    p1 = state["players"]["1"]
    p1["board"] = [smoke.unit("ally_elsewhere", row="ranged")]
    p1["hand"] = [card, smoke.unit("reserve")]
    p1["faction"] = "Lua Negra"
    p1["faction_boost_used"] = True
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    after = result["state"]["players"]["1"]
    assert any(c["id"] == card["id"] for c in after["discard"]), after
    ally = next(u for u in after["board"] if u["id"] == "ally_elsewhere")
    assert int(ally.get("bonus", 0)) == 0, ally
    return {"observed": "special moved to discard; no same-row ally was buffed", "ally_bonus": ally["bonus"]}


def test_egide_rare_grants_two_shields() -> dict[str, Any]:
    card = smoke.unit("audit_egide", skill="gwent_egide", special=True, rarity="Rara")
    result = prepare_play(card)
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    shielded = [u["id"] for u in board if int(u.get("escudo", 0)) > 0]
    assert len(shielded) == 2, shielded
    return {"expected_shields": 2, "observed_shielded_units": shielded, "reason": "Rara has budget 1; gwent_egide resolves min(3, 1 + budget) targets"}


def test_chifre_rarity_amplifies_only_first_changed_ally() -> dict[str, Any]:
    card = smoke.unit("audit_chifre", skill="gwent_chifre", special=True, rarity="Épica")
    result = prepare_play(card)
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    observed = [(u["id"], int(u.get("bonus", 0))) for u in board if u.get("row") == "melee"]
    assert observed == [("ally_melee_a", 3), ("ally_melee_b", 2)], observed
    return {"expected_same_row_bonuses": [3, 2], "observed_same_row_bonuses": observed, "reason": "base +2 to each; rarity budget 1 adds +1 to the first changed target in board order"}


def test_passo_rare_moves_two_units() -> dict[str, Any]:
    card = smoke.unit("audit_passo", skill="gwent_passo", special=True, rarity="Rara")
    result = prepare_play(card, row="melee")
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    moved = [u["id"] for u in board if u["id"] in {"ally_ranged", "ally_siege"} and u.get("row") == "melee"]
    assert len(moved) == 2, moved
    return {"expected_moved_count": 2, "observed_moved_units": moved, "reason": "Rara budget 1; movement cap is min(3, 1 + budget)"}


def test_gravity_reposition_recalculates_weather() -> dict[str, Any]:
    card = smoke.unit("chefe_radahn_flagelo_estrelas", skill="quebra_ritmo", row="melee", faction="Ordem Áurea", power=5)
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = [card, smoke.unit("reserve")]
    p1["faction"] = "Véu Carmesim"
    p1["faction_boost_used"] = True
    p2["board"] = [
        smoke.unit("target_enemy", power=7, row="siege", bonus=1),
        smoke.unit("other_enemy", power=3, row="melee"),
    ]
    state["weather"] = {"melee": 1, "ranged": 0, "siege": 0}
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    enemy = next(u for u in result["state"]["players"]["2"]["board"] if u["id"] == "target_enemy")
    effective = gwent._poder_efetivo(enemy, result["state"]["weather"])
    assert enemy["row"] == "melee" and effective == 5, {"enemy": enemy, "effective": effective}
    return {"expected": "strongest enemy moved from siege to melee; new melee weather applies immediately", "observed_row": enemy["row"], "printed_fileira": enemy["fileira"], "observed_effective_power": effective}


def test_vigil_seal_resists_weather_and_rarity_amplifies_ally_buff() -> dict[str, Any]:
    card = smoke.unit("magia_selo_vigilia", skill="adaptacao", row="melee", faction="Lua Negra", power=4, rarity="Rara")
    state = smoke.fixture(card, "melee")
    p1 = state["players"]["1"]
    p1["board"] = [smoke.unit("same_row_ally", row="melee", power=3)]
    p1["hand"] = [card, smoke.unit("reserve")]
    p1["faction"] = "Véu Carmesim"
    p1["faction_boost_used"] = True
    state["weather"] = {"melee": 1, "ranged": 0, "siege": 0}
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    played = next(u for u in board if u["id"] == card["id"])
    ally = next(u for u in board if u["id"] == "same_row_ally")
    assert int(played.get("weather_resist", 0)) == 1, played
    assert gwent._poder_efetivo(played, result["state"]["weather"]) == 4, played
    assert int(ally.get("bonus", 0)) == 2, ally
    return {"observed_weather_resist": played["weather_resist"], "observed_played_effective_power": gwent._poder_efetivo(played, result["state"]["weather"]), "observed_ally_bonus": ally["bonus"], "reason": "identity gives base +1 to first same-row ally; Rara budget 1 amplifies that changed bonus once"}


def test_chama_negra_rarity_amplifies_vengeance_trigger() -> dict[str, Any]:
    card = smoke.unit("audit_queima", skill="gwent_queima", special=True, rarity="Épica")
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["board"] = [
        smoke.unit("vengeance_victim", skill="vinganca", power=9, row="melee"),
        smoke.unit("first_survivor", power=3, row="melee"),
        smoke.unit("second_survivor", power=4, row="melee"),
    ]
    p1["hand"] = [card, smoke.unit("reserve")]
    p1["faction"] = "Lua Negra"
    p1["faction_boost_used"] = True
    p2["board"] = [smoke.unit("enemy_strongest", power=10), smoke.unit("enemy_survivor", power=2)]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    observed = {u["id"]: int(u.get("bonus", 0)) for u in board}
    assert observed["first_survivor"] == 2 and observed["second_survivor"] == 1, observed
    return {"expected_from_vengeance_alone": {"first_survivor": 1, "second_survivor": 1}, "observed_after_epic_rarity": observed, "finding": "the global rarity-diff scan treats a removal-triggered Vengeance bonus as a Chama Negra bonus target"}


def test_normal_removal_consumes_shield_and_blocks() -> dict[str, Any]:
    unit = smoke.unit("shielded_unit", escudo=1)
    side = {"board": [unit], "discard": [], "baixas": 0}
    message = gwent._remover_unidade(side, unit, "remocao")
    assert len(side["board"]) == 1 and len(side["discard"]) == 0 and side["baixas"] == 0 and unit["escudo"] == 0
    return {"observed_message": message, "board_remaining": len(side["board"]), "discard_count": len(side["discard"]), "baixas": side["baixas"], "shield_after": unit["escudo"]}


def test_sacrifice_ignores_shield() -> dict[str, Any]:
    unit = smoke.unit("shielded_sacrifice", escudo=1)
    side = {"board": [unit], "discard": [], "baixas": 0}
    message = gwent._remover_unidade(side, unit, "sacrificio")
    assert len(side["board"]) == 0 and len(side["discard"]) == 1 and side["baixas"] == 1
    return {"observed_message": message, "board_remaining": len(side["board"]), "discard_count": len(side["discard"]), "baixas": side["baixas"], "shield_field_present": "escudo" in unit}


def test_debuff_bypasses_shield() -> dict[str, Any]:
    card = smoke.unit("magia_trovao_oco", skill="drenagem", row="melee", faction="Lua Negra", rarity="Comum")
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["hand"] = [card, smoke.unit("reserve")]
    p1["faction"] = "Véu Carmesim"
    p1["faction_boost_used"] = True
    p2["board"] = [smoke.unit("shielded_enemy", row="melee", bonus=2, escudo=1)]
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    enemy = result["state"]["players"]["2"]["board"][0]
    assert int(enemy["bonus"]) == 1 and int(enemy["escudo"]) == 1, enemy
    return {"observed_bonus": enemy["bonus"], "shield_unchanged": enemy["escudo"], "finding": "shield is not a universal prevention layer for bonus/status effects"}


def test_round_end_clears_round_modifiers_but_keeps_weather_resist() -> dict[str, Any]:
    state = smoke.fixture(smoke.unit("unused_card"), "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["board"] = [smoke.unit("resistant_archived", bonus=3, escudo=1, geada=1, weather_resist=2)]
    p2["board"] = [smoke.unit("other_player_unit")]
    state["weather"] = {"melee": 1, "ranged": 0, "siege": 0}
    state["round"] = 1
    state["crowns"] = {"1": 0, "2": 0}
    gwent._resolve_round(state)
    archived = next(u for u in p1["discard"] if u["id"] == "resistant_archived")
    assert archived["bonus"] == 0 and archived["escudo"] == 0 and archived["geada"] == 0
    assert archived["weather_resist"] == 2
    assert all(v == 0 for v in state["weather"].values())
    return {"archived_bonus": archived["bonus"], "archived_shield": archived["escudo"], "archived_geada": archived["geada"], "archived_weather_resist": archived["weather_resist"], "next_round_weather": state["weather"], "decision_needed": "whether weather resistance is persistent card data or a round-scoped modifier"}


def test_combo_and_faction_passive_stack_in_separate_steps() -> dict[str, Any]:
    ally = smoke.unit("gwent_unidade_portaestandarte", skill="", faction="Ordem Áurea", row="melee", power=4)
    card = smoke.unit("gwent_unidade_sentinela_rubra", skill="", faction="Ordem Áurea", row="melee", power=4)
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["board"] = [ally]
    p1["hand"] = [card, smoke.unit("reserve")]
    p1["faction"] = "Ordem Áurea"
    p1["faction_boost_used"] = False
    p2["board"] = []
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    board = result["state"]["players"]["1"]["board"]
    old_ally = next(u for u in board if u["id"] == ally["id"])
    played = next(u for u in board if u["id"] == card["id"])
    assert old_ally["bonus"] == 1 and played["bonus"] == 3 and played["combo_ativado"] == "juramento_erdtree", board
    return {"existing_ally_team_bonus": old_ally["bonus"], "new_card_combo_plus_faction_bonus": played["bonus"], "combo": played["combo_ativado"], "faction_boost_used": result["state"]["players"]["1"]["faction_boost_used"]}


def test_current_catalog_does_not_assign_legacy_shield_or_resistance_skills() -> dict[str, Any]:
    shield_card = cartas.get_carta("gwent_unidade_sentinela_rubra")
    resist_card = cartas.get_carta("gwent_unidade_oraculo_clima")
    assert shield_card is not None and resist_card is not None
    assert shield_card.habilidade == "" and resist_card.habilidade == ""
    assert "gwent_unidade_sentinela_rubra" not in gwent.CARD_IDENTITY_ABILITIES
    assert "gwent_unidade_oraculo_clima" not in gwent.CARD_IDENTITY_ABILITIES
    return {"legacy_escudo_ferro_card_skill": shield_card.habilidade, "legacy_resistencia_climatica_card_skill": resist_card.habilidade, "active_weather_resistance_identity": "magia_selo_vigilia" in gwent.CARD_IDENTITY_ABILITIES}


for name, fn in [
    ("gwent_vinculo_enforces_two_ally_minimum", test_vinculo_requires_two_allies),
    ("gwent_muralha_empty_row_is_consumed_as_noop", test_muralha_empty_row_is_consumed_without_effect),
    ("gwent_egide_rare_grants_two_shields", test_egide_rare_grants_two_shields),
    ("gwent_chifre_rarity_targets_first_changed_ally", test_chifre_rarity_amplifies_only_first_changed_ally),
    ("gwent_passo_rare_moves_two_units", test_passo_rare_moves_two_units),
    ("star_gravity_reposition_recalculates_weather", test_gravity_reposition_recalculates_weather),
    ("vigil_seal_weather_resistance_and_rarity_buff", test_vigil_seal_resists_weather_and_rarity_amplifies_ally_buff),
    ("gwent_queima_rarity_amplifies_vengeance_trigger", test_chama_negra_rarity_amplifies_vengeance_trigger),
    ("normal_removal_is_blocked_by_consumed_shield", test_normal_removal_consumes_shield_and_blocks),
    ("sacrifice_bypasses_shield", test_sacrifice_ignores_shield),
    ("bonus_debuff_bypasses_shield", test_debuff_bypasses_shield),
    ("round_reset_keeps_weather_resistance_field", test_round_end_clears_round_modifiers_but_keeps_weather_resist),
    ("combo_team_bonus_and_faction_passive_stack", test_combo_and_faction_passive_stack_in_separate_steps),
    ("legacy_shield_and_resistance_skills_are_unassigned", test_current_catalog_does_not_assign_legacy_shield_or_resistance_skills),
]:
    check(name, fn)

report = {
    "metadata": {
        "document": "Buffs, movement, protection and weather audit v0.1",
        "status": "DIAGNOSTIC ONLY; LEGACY BEHAVIOR, NOT APPROVED DESIGN",
        "baseline": "soulsbo-main-handoff(1).zip",
        "method": "Synthetic fixtures invoking sistemas.gwent.aplicar_jogada, _remover_unidade, _resolve_round and _poder_efetivo; no database, HTTP, Discord, browser or production match used.",
    },
    "counts": {
        "assertions": len(cases),
        "passed": sum(item["status"] == "passed" for item in cases),
        "failed": sum(item["status"] == "failed" for item in cases),
    },
    "cases": cases,
    "limits": [
        "These assertions cover selected branches and interactions, not all 54 candidate effect families or all card/rarity combinations.",
        "They establish the current engine's behavior, not whether that behavior should be retained in the rebuilt engine.",
        "No full competitive simulation, HTTP dispatch, production database, Discord runtime, or browser interaction was performed.",
        "Target tie-breaking, physical instance identity, and duration of weather_resist remain design questions.",
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
for item in cases:
    if item["status"] != "passed":
        print(json.dumps(item, ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]:
    raise SystemExit(1)
