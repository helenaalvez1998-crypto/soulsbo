#!/usr/bin/env python3
"""Targeted behavioral assertions for representative Gwent effects.

Uses real engine functions with controlled fixtures. Diagnostic only: this is
not full branch coverage, a match simulator, or a production migration test.
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
spec = importlib.util.spec_from_file_location("card_effect_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-effect-behavior-assertions-v0.1.json"


def play(skill: str, *, special: bool = False, row: str = "melee", target_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    card = smoke.unit(
        f"assert_{skill}", skill=skill, special=special,
        faction="Véu Carmesim", row=row, power=4, rarity="Comum",
    )
    state = smoke.fixture(card, row)
    state["round"] = 1
    p1 = state["players"]["1"]
    p2 = state["players"]["2"]
    p1["faction"] = "Lua Negra"  # do not add a faction passiva to the tested effect
    p1["hand"] = [card, smoke.unit(f"reserve_{skill}", power=1)]
    p1["draw_pile"] = [smoke.unit("assert_draw_a", power=2), smoke.unit("assert_draw_b", power=3)]
    p1["synergy_used"] = {}
    p1["faction_boost_used"] = True
    p2["faction"] = "Ordem Áurea"
    result = gwent.aplicar_jogada(
        state, 1, card_id=card["id"], action="play", row=row, target_id=target_id
    )
    if "error" in result:
        raise AssertionError(result["error"])
    after = result["state"]
    return after, after["players"]["1"], after["players"]["2"]


def find(items: list[dict[str, Any]], card_id: str) -> dict[str, Any] | None:
    return next((x for x in items if x.get("id") == card_id), None)


cases: list[dict[str, Any]] = []


def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        details = fn()
        cases.append({"case": name, "status": "passed", **details})
    except Exception as exc:  # report every case instead of hiding later failures
        cases.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


def test_primeira_luz() -> dict[str, Any]:
    state, own, _ = play("primeira_luz")
    card = find(own["board"], "assert_primeira_luz")
    assert card is not None and int(card.get("bonus", 0)) == 1, card
    return {"expected": "played unit bonus +1 on round 1", "observed_bonus": card["bonus"]}


def test_drenagem() -> dict[str, Any]:
    before = [2, 1, 2, 2]
    state, _, enemy = play("drenagem")
    after = [int(x.get("bonus", 0)) for x in enemy["board"]]
    expected = [max(-2, x - 1) for x in before]
    assert after == expected, {"expected": expected, "actual": after}
    return {"expected_enemy_bonuses": expected, "observed_enemy_bonuses": after}


def test_batedor_draw() -> dict[str, Any]:
    _, own, _ = play("gwent_batedor", special=True)
    drawn = find(own["hand"], "assert_draw_a")
    assert drawn is not None and len(own["draw_pile"]) == 1, {"hand": [x["id"] for x in own["hand"]], "draw": own["draw_pile"]}
    return {"expected": "one card drawn at common rarity", "drawn_card": drawn["id"], "draw_pile_remaining": len(own["draw_pile"])}


def test_egide_shield() -> dict[str, Any]:
    _, own, _ = play("gwent_egide", special=True)
    shields = [x["id"] for x in own["board"] if int(x.get("escudo", 0)) > 0]
    assert len(shields) == 1, shields
    return {"expected_shielded_units": 1, "observed_shielded_units": shields}


def test_requiem_revive() -> dict[str, Any]:
    _, own, _ = play("gwent_requiem", special=True)
    revived = find(own["board"], "discard_unit_4")
    assert revived is not None and not find(own["discard"], "discard_unit_4"), {"board": [x["id"] for x in own["board"]], "discard": [x["id"] for x in own["discard"]]}
    return {"expected": "highest eligible discarded unit returned to board", "revived": revived["id"], "revived_power": revived["poder"]}


def test_passo_move() -> dict[str, Any]:
    _, own, _ = play("gwent_passo", special=True, row="melee")
    moved = [x["id"] for x in own["board"] if x["id"] in {"ally_ranged", "ally_siege"} and x.get("row") == "melee"]
    assert len(moved) == 1, {"moved": moved, "board": [(x["id"], x.get("row")) for x in own["board"]]}
    return {"expected": "one unit moved into selected row at common rarity", "moved": moved}


def test_invocacao_token() -> dict[str, Any]:
    _, own, _ = play("gwent_invocacao", special=True, row="ranged")
    token = next((x for x in own["board"] if x.get("nome") == "Lobos Espirituais"), None)
    assert token is not None and int(token["poder"]) == 3 and token.get("row") == "ranged", token
    return {"expected": "3-power token in ranged row at common rarity", "token_id": token["id"], "power": token["poder"], "row": token["row"]}


def test_queima_removes_both_sides() -> dict[str, Any]:
    _, own, enemy = play("gwent_queima", special=True)
    assert len(own["board"]) == 3 and len(enemy["board"]) == 3, {"own": len(own["board"]), "enemy": len(enemy["board"])}
    return {"expected_board_counts": [3, 3], "observed_board_counts": [len(own["board"]), len(enemy["board"])]}


def test_purificar_clears_weather() -> dict[str, Any]:
    state, _, _ = play("gwent_purificar", special=True)
    observed = state["weather"]
    assert all(int(observed.get(r, 0)) == 0 for r in gwent.ROWS), observed
    return {"expected_weather": {r: 0 for r in gwent.ROWS}, "observed_weather": observed}


def test_sangramento_marks_row() -> dict[str, Any]:
    _, _, enemy = play("gwent_sangramento", special=True, row="melee")
    observed = [int(x.get("sangramento", 0)) for x in enemy["board"] if x.get("row") == "melee"]
    assert observed == [1, 1], observed
    return {"expected_marks_on_melee": [1, 1], "observed_marks_on_melee": observed}


def test_execucao_removes_eligible_enemy() -> dict[str, Any]:
    _, _, enemy = play("gwent_execucao", special=True, row="melee")
    assert len([x for x in enemy["board"] if x.get("row") == "melee"]) == 1, [x["id"] for x in enemy["board"]]
    return {"expected_enemy_melee_remaining": 1, "observed_enemy_melee_remaining": 1}


def test_chifre_buffs_row() -> dict[str, Any]:
    _, own, _ = play("gwent_chifre", special=True, row="melee")
    observed = [int(x.get("bonus", 0)) for x in own["board"] if x.get("row") == "melee"]
    assert observed == [2, 2], observed
    return {"expected_melee_ally_bonuses": [2, 2], "observed_melee_ally_bonuses": observed}


for name, fn in [
    ("primeira_luz_round1_buff", test_primeira_luz),
    ("drenagem_reduces_enemy_bonus", test_drenagem),
    ("gwent_batedor_draws_one_card", test_batedor_draw),
    ("gwent_egide_adds_one_shield", test_egide_shield),
    ("gwent_requiem_revives_best_eligible", test_requiem_revive),
    ("gwent_passo_moves_one_unit", test_passo_move),
    ("gwent_invocacao_creates_token", test_invocacao_token),
    ("gwent_queima_removes_strongest_each_side", test_queima_removes_both_sides),
    ("gwent_purificar_clears_weather", test_purificar_clears_weather),
    ("gwent_sangramento_marks_selected_row", test_sangramento_marks_row),
    ("gwent_execucao_removes_eligible_target", test_execucao_removes_eligible_enemy),
    ("gwent_chifre_buffs_selected_row", test_chifre_buffs_row),
]:
    check(name, fn)

# One focused identity assertion: Last Bell should gain +2 when its side is behind.
def test_identity_last_bell() -> dict[str, Any]:
    model = cartas.get_carta("arma_grande_sino")
    assert model is not None
    card = model.para_dict()
    card["raridade"] = "Comum"
    row = str(card.get("fileira") or model.fileira or "melee")
    state = smoke.fixture(card, row)
    p1 = state["players"]["1"]
    p1["hand"].append(smoke.unit("reserve_last_bell"))
    p1["faction"] = "Véu Carmesim" if card.get("faccao") != "Véu Carmesim" else "Ordem Áurea"
    before = smoke.side_swing(p1, state["players"]["2"], state["weather"])
    base_power = max(1, int(card.get("poder", 1)))
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row=row)
    assert "error" not in result, result
    after_p1 = result["state"]["players"]["1"]
    played = find(after_p1["board"], "arma_grande_sino")
    assert played is not None and int(played.get("bonus", 0)) == 2, played
    after = smoke.side_swing(after_p1, result["state"]["players"]["2"], result["state"]["weather"])
    return {"expected_identity_bonus": 2, "observed_identity_bonus": played["bonus"], "observed_field_swing_delta_excluding_base_power": after - before - base_power}

check("identity_last_bell_gets_plus_two_while_behind", test_identity_last_bell)

report = {
    "metadata": {
        "document": "Targeted behavioral assertions v0.1",
        "status": "DIAGNOSTIC ONLY; SELECTED EFFECTS, NOT FULL COVERAGE",
        "baseline": "soulsbo-main(1).zip",
        "method": "Controlled fixtures and assertions against sistemas.gwent.aplicar_jogada; no production DB, full match simulation, or strategy optimization.",
    },
    "counts": {
        "assertions": len(cases),
        "passed": sum(x["status"] == "passed" for x in cases),
        "failed": sum(x["status"] == "failed" for x in cases),
    },
    "cases": cases,
    "limits": [
        "Only representative effects are asserted; other generic handlers, all conditions, all rarity levels, leader actions, relic targeting, status ticks, and round-end interactions remain to be covered.",
        "The fixtures are synthetic and establish local behavior only; they do not estimate condition frequency, expected game value, or win rate.",
        "All tested cards use Common rarity to isolate effect behavior from RARITY_EFFECT_BUDGET.",
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
