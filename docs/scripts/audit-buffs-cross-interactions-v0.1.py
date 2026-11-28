#!/usr/bin/env python3
"""Cross-interaction audit for buffs, movement, protection, status, weather and combos.

Diagnostic only: invokes real legacy engine functions with synthetic in-memory fixtures.
Does not modify runtime modules, production data, database, API or frontend.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import gwent

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("buff_cross_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-buffs-cross-interactions-v0.1.json"
CASES: list[dict[str, Any]] = []


def run_case(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        CASES.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:
        CASES.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


def test_weakest_target_uses_effective_power_with_weather_and_status() -> dict[str, Any]:
    card = smoke.unit("gwent_v75_ordem_veterano_juramento", row="melee", faction="Ordem Áurea")
    high_base_but_debuffed = smoke.unit(
        "high_base_debuffed", row="melee", power=8, geada=2, bonus=0
    )
    lower_base_clean = smoke.unit("lower_base_clean", row="melee", power=7, bonus=0)
    player = {"board": [high_base_but_debuffed, lower_base_clean]}
    other = {"board": []}
    state = {"weather": {"melee": 1, "ranged": 0, "siege": 0}}
    before = {
        "high_base_but_debuffed": gwent._poder_efetivo(high_base_but_debuffed, state["weather"]),
        "lower_base_clean": gwent._poder_efetivo(lower_base_clean, state["weather"]),
    }
    gwent._aplicar_habilidade_identidade(player, other, card, state, "melee")
    assert high_base_but_debuffed["bonus"] == 1, {
        "before": before,
        "bonuses": [high_base_but_debuffed["bonus"], lower_base_clean["bonus"]],
    }
    assert lower_base_clean["bonus"] == 0
    return {
        "effective_power_before": before,
        "selected": "high_base_but_debuffed",
        "reason": "the 8-power unit falls below the 6-power unit after Geada and current-row weather",
    }


def test_grace_mender_cleans_lowest_effective_status_targets_without_consuming_shield() -> dict[str, Any]:
    card = smoke.unit("gwent_v75_ordem_confessora_graca", row="siege", faction="Ordem Áurea")
    low = smoke.unit("low_status_shielded", row="siege", power=5, geada=2, escudo=1, bonus=0)
    high = smoke.unit("higher_status", row="siege", power=7, sangramento=1, bonus=0)
    clean = smoke.unit("clean_unit", row="siege", power=3, bonus=0)
    player = {"board": [high, low, clean]}
    other = {"board": []}
    state = {"weather": {"melee": 0, "ranged": 0, "siege": 1}}
    effective = {u["id"]: gwent._poder_efetivo(u, state["weather"]) for u in player["board"]}
    gwent._aplicar_habilidade_identidade(player, other, card, state, "siege")
    assert low["geada"] == 0 and high["sangramento"] == 0
    assert low["bonus"] == 1 and high["bonus"] == 1
    assert low["escudo"] == 1
    assert clean["bonus"] == 0
    return {
        "effective_power_before": effective,
        "purified_targets": ["low_status_shielded", "higher_status"],
        "shield_after_purification": low["escudo"],
        "finding": "purification clears statuses and grants buffs; it neither consumes nor depends on shield",
    }


def test_star_gravity_selects_by_source_effective_power_then_applies_destination_weather() -> dict[str, Any]:
    card = smoke.unit("chefe_radahn_flagelo_estrelas", row="melee", faction="Ordem Áurea")
    source_debuffed = smoke.unit(
        "high_base_source_debuffed", row="ranged", power=12, geada=2, weather_resist=0, bonus=0
    )
    selected = smoke.unit(
        "highest_effective_source", row="siege", power=9, geada=0, weather_resist=1, bonus=0
    )
    player = {"board": []}
    other = {"board": [source_debuffed, selected]}
    state = {"weather": {"melee": 2, "ranged": 3, "siege": 0}}
    source_effective = {
        u["id"]: gwent._poder_efetivo(u, state["weather"]) for u in other["board"]
    }
    gwent._aplicar_habilidade_identidade(player, other, card, state, "melee")
    assert selected["row"] == "melee" and selected["fileira"] == "siege"
    assert selected["bonus"] == -2
    destination_effective = gwent._poder_efetivo(selected, state["weather"])
    assert destination_effective == 6, {"selected": selected, "effective": destination_effective}
    return {
        "source_effective_power": source_effective,
        "selected": selected["id"],
        "current_row_after": selected["row"],
        "base_fileira_after": selected["fileira"],
        "destination_weather_resistance": selected["weather_resist"],
        "effective_power_after_move_and_debuff": destination_effective,
    }


def test_combo_team_bonus_uses_current_row_not_original_fileira() -> dict[str, Any]:
    moved_ally = smoke.unit(
        "gwent_unidade_portaestandarte", row="melee", faction="Ordem Áurea", bonus=0
    )
    moved_ally["fileira"] = "ranged"  # represents a unit previously repositioned from Ranged
    played = smoke.unit(
        "gwent_unidade_sentinela_rubra", row="melee", faction="Ordem Áurea", bonus=0
    )
    player = {"board": [moved_ally], "synergy_used": {}}
    result = gwent._aplicar_combo_de_cartas(player, played)
    assert result == "Juramento da Árvore Áurea"
    assert moved_ally["bonus"] == 1 and played["bonus"] == 2
    return {
        "combo": result,
        "ally_current_row": moved_ally["row"],
        "ally_original_fileira": moved_ally["fileira"],
        "ally_team_bonus": moved_ally["bonus"],
        "played_card_combo_bonus": played["bonus"],
        "finding": "team_bonus selection reads current row; original fileira does not exclude a moved ally",
    }


def test_combo_rarity_and_faction_passive_resolve_in_distinct_order() -> dict[str, Any]:
    moved_ally = smoke.unit(
        "gwent_unidade_portaestandarte", row="melee", faction="Ordem Áurea", bonus=0
    )
    moved_ally["fileira"] = "ranged"
    card = smoke.unit(
        "gwent_unidade_sentinela_rubra", skill="", row="melee", faction="Ordem Áurea",
        power=4, rarity="Rara", bonus=0,
    )
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["board"] = [moved_ally]
    p1["hand"] = [card, smoke.unit("cross_combo_reserve", power=1)]
    p1["faction"] = "Ordem Áurea"
    p1["faction_boost_used"] = False
    p2["board"] = []
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    after = result["state"]["players"]["1"]
    ally = next(u for u in after["board"] if u["id"] == moved_ally["id"])
    played = next(u for u in after["board"] if u["id"] == card["id"])
    assert ally["bonus"] == 1
    assert played["bonus"] == 4, played  # combo +2, rarity +1, faction passive +1
    return {
        "combo": played.get("combo_ativado"),
        "moved_ally_team_bonus": ally["bonus"],
        "played_card_bonus": played["bonus"],
        "faction_boost_used": after["faction_boost_used"],
        "decomposition": {"combo": 2, "rarity": 1, "faction_passive": 1},
    }


def test_passo_move_changes_future_row_buff_target_but_not_last_row() -> dict[str, Any]:
    card = smoke.unit("audit_cross_passo", skill="gwent_passo", special=True, rarity="Comum")
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    moved = smoke.unit("moved_from_ranged", row="ranged", faction="Lua Negra")
    p1["board"] = [moved]
    p1["hand"] = [card, smoke.unit("reserve_after_move", power=1)]
    p1["last_row"] = "siege"
    p1["faction"] = "Véu Carmesim"
    p1["faction_boost_used"] = True
    p2["passed"] = True
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
    assert "error" not in result, result
    after = result["state"]["players"]["1"]
    moved_after = next(u for u in after["board"] if u["id"] == moved["id"])
    assert moved_after["row"] == "melee" and after["last_row"] == "siege"
    # Apply the next row buff directly to make the current-row criterion observable.
    chifre = smoke.unit("audit_cross_chifre", skill="gwent_chifre", special=True, rarity="Comum")
    p1_after = after
    p1_after["hand"] = [chifre, smoke.unit("reserve_after_buff", power=1)]
    result2 = gwent.aplicar_jogada(result["state"], 1, card_id=chifre["id"], action="play", row="melee")
    assert "error" not in result2, result2
    final_ally = next(u for u in result2["state"]["players"]["1"]["board"] if u["id"] == moved["id"])
    assert final_ally["bonus"] == 2
    return {
        "moved_row": final_ally["row"],
        "base_fileira": final_ally["fileira"],
        "last_row_after_movement": result2["state"]["players"]["1"]["last_row"],
        "bonus_from_following_same_row_buff": final_ally["bonus"],
        "finding": "movement changes current-row targeting but does not rewrite the player's last played row",
    }


def test_blood_price_sacrifices_shielded_status_target_and_uses_effective_power_for_gain() -> dict[str, Any]:
    card = smoke.unit("gwent_v75_veu_carrasco_preco", row="melee", faction="Véu Carmesim")
    victim = smoke.unit(
        "shielded_status_victim", row="melee", power=4, bonus=0, escudo=1,
        geada=1, sangramento=1, podrida=0, loucura=0,
    )
    survivor = smoke.unit("strong_survivor", row="melee", power=7, bonus=0)
    player = {"board": [victim, survivor], "discard": [], "baixas": 0}
    other = {"board": []}
    state = {"weather": {"melee": 1, "ranged": 0, "siege": 0}}
    effective_before = gwent._poder_efetivo(victim, state["weather"])
    gwent._aplicar_habilidade_identidade(player, other, card, state, "melee")
    assert victim not in player["board"] and victim in player["discard"]
    assert "escudo" not in victim and all(victim.get(k, 0) == 0 for k in ("geada", "sangramento", "podrida", "loucura"))
    assert card["bonus"] == min(3, max(1, effective_before)) == 2
    return {
        "victim_effective_power_before_sacrifice": effective_before,
        "victim_removed_despite_shield": True,
        "discarded_statuses_after_removal": {k: victim.get(k, 0) for k in ("geada", "sangramento", "podrida", "loucura")},
        "discarded_shield_field_present": "escudo" in victim,
        "card_gain": card["bonus"],
        "finding": "Blood Price uses effective power, then sacrifice bypasses shield and central removal clears statuses",
    }


def test_shielded_vengeance_target_does_not_trigger_on_failed_removal() -> dict[str, Any]:
    victim = smoke.unit("vengeance_shielded", skill="vinganca", row="melee", escudo=1)
    ally = smoke.unit("vengeance_survivor", row="melee", bonus=0)
    side = {"board": [victim, ally], "discard": [], "baixas": 0}
    message = gwent._remover_unidade(side, victim, "execucao")
    assert victim in side["board"] and ally["bonus"] == 0
    assert side["baixas"] == 0 and victim["escudo"] == 0
    return {
        "message": message,
        "victim_still_on_board": victim in side["board"],
        "ally_bonus": ally["bonus"],
        "removals_counted": side["baixas"],
        "finding": "Vengeance is downstream of successful removal, not a failed attempt",
    }


def test_combo_team_buff_is_not_applied_to_enemy_or_other_rows() -> dict[str, Any]:
    same_row = smoke.unit("gwent_unidade_portaestandarte", row="melee", faction="Ordem Áurea")
    other_row = smoke.unit("gwent_unidade_baluarte", row="ranged", faction="Ordem Áurea")
    enemy = smoke.unit("enemy_order_ally", row="melee", faction="Ordem Áurea")
    played = smoke.unit("gwent_unidade_sentinela_rubra", row="melee", faction="Ordem Áurea")
    player = {"board": [same_row, other_row], "synergy_used": {}}
    result = gwent._aplicar_combo_de_cartas(player, played)
    assert result == "Juramento da Árvore Áurea"
    assert same_row["bonus"] == 1 and other_row["bonus"] == 0 and enemy["bonus"] == 0
    return {
        "same_row_ally_bonus": same_row["bonus"],
        "other_row_ally_bonus": other_row["bonus"],
        "enemy_side_not_in_combo_resolver_input": True,
        "finding": "team_bonus is scoped to pre-existing allies on the played card's current row",
    }


for name, fn in [
    ("weakest_target_uses_effective_power_weather_and_status", test_weakest_target_uses_effective_power_with_weather_and_status),
    ("grace_mender_cleans_status_targets_and_preserves_shield", test_grace_mender_cleans_lowest_effective_status_targets_without_consuming_shield),
    ("star_gravity_source_selection_and_destination_weather", test_star_gravity_selects_by_source_effective_power_then_applies_destination_weather),
    ("combo_team_bonus_uses_current_row_after_movement", test_combo_team_bonus_uses_current_row_not_original_fileira),
    ("combo_rarity_and_faction_passive_order", test_combo_rarity_and_faction_passive_resolve_in_distinct_order),
    ("passo_changes_row_buff_scope_not_last_row", test_passo_move_changes_future_row_buff_target_but_not_last_row),
    ("blood_price_shield_status_weather_cross", test_blood_price_sacrifices_shielded_status_target_and_uses_effective_power_for_gain),
    ("shielded_vengeance_failed_removal_no_trigger", test_shielded_vengeance_target_does_not_trigger_on_failed_removal),
    ("combo_team_bonus_current_row_scope", test_combo_team_buff_is_not_applied_to_enemy_or_other_rows),
]:
    run_case(name, fn)

report = {
    "metadata": {
        "document": "Buffs cross-interaction audit v0.1",
        "status": "DIAGNOSTIC ONLY; LEGACY BEHAVIOR, NOT APPROVED DESIGN",
        "baseline": "soulsbo-main-updated.zip; runtime source preserved from supplied handoff baseline",
        "method": "Synthetic fixtures invoking sistemas.gwent identity handlers, aplicar_jogada, _aplicar_combo_de_cartas, _poder_efetivo and _remover_unidade; no database, HTTP, Discord, browser or production match used.",
    },
    "counts": {
        "assertions": len(CASES),
        "passed": sum(item["status"] == "passed" for item in CASES),
        "failed": sum(item["status"] == "failed" for item in CASES),
    },
    "cases": CASES,
    "limits": [
        "Assertions cover selected cross-interactions and do not exhaust all 54 candidate effect families, identities, combos, leaders or rarities.",
        "Results describe current legacy behavior only; they do not approve retaining the same behavior in the rebuilt engine.",
        "No full competitive simulation, HTTP dispatch, production database, Discord runtime or browser interaction was performed.",
        "The audit does not settle BUF-001 through BUF-014; it adds evidence for interaction boundaries and target-selection dependencies.",
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
for item in CASES:
    if item["status"] != "passed":
        print(json.dumps(item, ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]:
    raise SystemExit(1)
