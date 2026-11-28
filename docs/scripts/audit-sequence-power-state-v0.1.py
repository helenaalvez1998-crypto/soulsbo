#!/usr/bin/env python3
"""Read-only diagnostic audit for sequence-power effects and last_row semantics.

Uses real legacy engine functions with synthetic in-memory fixtures. It does not
modify runtime source, persistent data, databases, APIs, Discord or production.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import gwent  # noqa: E402

SMOKE_PATH = ROOT / "docs" / "scripts" / "validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("sequence_power_smoke_helpers", SMOKE_PATH)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs" / "card-game-sequence-power-state-audit-v0.1.json"
CASES: list[dict[str, Any]] = []


def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        CASES.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:  # retain failures as evidence
        CASES.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


def play_skill(skill: str, *, row: str, own_last_row: str | None = None,
               enemy_last_row: str | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    card = smoke.unit(f"sequence_{skill}", skill=skill, row=row, power=4, rarity="Comum", faction="Véu Carmesim")
    state = smoke.fixture(card, row)
    own, enemy = state["players"]["1"], state["players"]["2"]
    own["board"] = []
    enemy["board"] = []
    own["last_row"] = own_last_row
    enemy["last_row"] = enemy_last_row
    own["hand"] = [card, smoke.unit(f"reserve_{skill}", power=1)]
    own["faction"] = "Lua Negra"
    own["faction_boost_used"] = True
    enemy["faction_boost_used"] = True
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row=row)
    assert "error" not in result, result
    after = result["state"]
    placed = next((u for u in after["players"]["1"]["board"] if u["id"] == card["id"]), None)
    assert placed is not None, after["players"]["1"]["board"]
    return after, placed, after["players"]["1"]


def test_encadeamento_same_row_reads_previous_unit_play() -> dict[str, Any]:
    after, card, own = play_skill("encadeamento", row="melee", own_last_row="melee")
    assert card["bonus"] == 2 and own["last_row"] == "melee", (card, own)
    return {"previous_last_row": "melee", "played_row": "melee", "bonus": card["bonus"], "last_row_after": own["last_row"]}


def test_encadeamento_different_row_no_bonus() -> dict[str, Any]:
    after, card, own = play_skill("encadeamento", row="melee", own_last_row="ranged")
    assert card["bonus"] == 0 and own["last_row"] == "melee", (card, own)
    return {"previous_last_row": "ranged", "played_row": "melee", "bonus": card["bonus"], "last_row_after": own["last_row"]}


def test_adaptacao_other_row_requires_existing_history() -> dict[str, Any]:
    after, card, own = play_skill("adaptacao", row="melee", own_last_row="ranged")
    assert card["bonus"] == 1 and own["last_row"] == "melee", (card, own)
    return {"previous_last_row": "ranged", "played_row": "melee", "bonus": card["bonus"], "last_row_after": own["last_row"]}


def test_adaptacao_first_unit_play_no_bonus() -> dict[str, Any]:
    after, card, own = play_skill("adaptacao", row="melee", own_last_row=None)
    assert card["bonus"] == 0 and own["last_row"] == "melee", (card, own)
    return {"previous_last_row": None, "played_row": "melee", "bonus": card["bonus"], "last_row_after": own["last_row"]}


def test_quebra_ritmo_reads_opponent_last_unit_play() -> dict[str, Any]:
    after, card, own = play_skill("quebra_ritmo", row="melee", own_last_row="siege", enemy_last_row="melee")
    assert card["bonus"] == 1, card
    return {"opponent_last_row": "melee", "played_row": "melee", "bonus": card["bonus"]}


def test_quebra_ritmo_opponent_different_row_no_bonus() -> dict[str, Any]:
    after, card, own = play_skill("quebra_ritmo", row="melee", own_last_row="siege", enemy_last_row="ranged")
    assert card["bonus"] == 0, card
    return {"opponent_last_row": "ranged", "played_row": "melee", "bonus": card["bonus"]}


def test_movement_does_not_rewrite_last_played_row_used_by_next_sequence() -> dict[str, Any]:
    first = smoke.unit("last_unit_played", row="melee", power=4, rarity="Comum", faction="Lua Negra")
    step = smoke.unit("step_special", skill="gwent_passo", row="ranged", power=0, special=True, rarity="Comum")
    adapt = smoke.unit("adapt_after_move", skill="adaptacao", row="ranged", power=4, rarity="Comum", faction="Véu Carmesim")
    state = smoke.fixture(first, "melee")
    own, enemy = state["players"]["1"], state["players"]["2"]
    own["board"] = []
    own["hand"] = [first, step, adapt, smoke.unit("own_reserve", row="siege", power=1)]
    own["last_row"] = None
    own["faction"] = "Lua Negra"
    own["faction_boost_used"] = True
    enemy["board"] = []
    enemy["hand"] = [
        smoke.unit("opponent_first", row="siege", power=2, faction="Ordem Áurea"),
        smoke.unit("opponent_second", row="melee", power=2, faction="Ordem Áurea"),
        smoke.unit("opponent_reserve", row="ranged", power=1, faction="Ordem Áurea"),
    ]
    enemy["faction_boost_used"] = True

    # Player 1 plays a unit in melee; this sets last_row to melee.
    r1 = gwent.aplicar_jogada(state, 1, card_id=first["id"], action="play", row="melee")
    assert "error" not in r1, r1
    state = r1["state"]
    assert state["players"]["1"]["last_row"] == "melee"

    # Alternate turn with an opponent unit.
    opponent_first = state["players"]["2"]["hand"][0]
    r2 = gwent.aplicar_jogada(state, 2, card_id=opponent_first["id"], action="play", row="siege")
    assert "error" not in r2, r2
    state = r2["state"]

    # Passo moves the last-played unit from melee to ranged; it must not rewrite last_row.
    r3 = gwent.aplicar_jogada(state, 1, card_id=step["id"], action="play", row="ranged", target_id=first["id"])
    assert "error" not in r3, r3
    state = r3["state"]
    moved = next(u for u in state["players"]["1"]["board"] if u["id"] == first["id"])
    assert moved["row"] == "ranged" and state["players"]["1"]["last_row"] == "melee", (moved, state["players"]["1"])

    opponent_second = next(u for u in state["players"]["2"]["hand"] if u["id"] == "opponent_second")
    r4 = gwent.aplicar_jogada(state, 2, card_id=opponent_second["id"], action="play", row="melee")
    assert "error" not in r4, r4
    state = r4["state"]

    r5 = gwent.aplicar_jogada(state, 1, card_id=adapt["id"], action="play", row="ranged")
    assert "error" not in r5, r5
    state = r5["state"]
    played = next(u for u in state["players"]["1"]["board"] if u["id"] == adapt["id"])
    assert played["bonus"] == 1 and state["players"]["1"]["last_row"] == "ranged", (played, state["players"]["1"])
    return {
        "original_unit_row_after_move": moved["row"],
        "stored_last_unit_play_row_after_move": "melee",
        "next_adaptacao_played_row": "ranged",
        "next_adaptacao_bonus": played["bonus"],
        "last_row_after_next_unit_play": state["players"]["1"]["last_row"],
    }


def test_special_action_does_not_update_last_row() -> dict[str, Any]:
    card = smoke.unit("climate_special", skill="gwent_clima", row="ranged", special=True, power=0, rarity="Comum")
    state = smoke.fixture(card, "ranged")
    own = state["players"]["1"]
    own["board"] = [smoke.unit("existing_melee", row="melee")]
    own["hand"] = [card, smoke.unit("reserve_special")]
    own["last_row"] = "melee"
    own["faction"] = "Lua Negra"
    own["faction_boost_used"] = True
    result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="ranged")
    assert "error" not in result, result
    after = result["state"]["players"]["1"]
    assert after["last_row"] == "melee", after
    return {"special_selected_row": "ranged", "last_unit_play_row_after_special": after["last_row"]}


def test_removal_does_not_clear_last_row_history() -> dict[str, Any]:
    removed = smoke.unit("removed_last_play", row="melee")
    own = {"board": [removed], "discard": [], "baixas": 0, "last_row": "melee"}
    msg = gwent._remover_unidade(own, removed, "remocao")
    assert not own["board"] and len(own["discard"]) == 1 and own["last_row"] == "melee", (own, msg)
    return {"removed_unit": removed["id"], "last_row_after_removal": own["last_row"], "removal_event": msg}


def test_round_transition_resets_both_players_last_row() -> dict[str, Any]:
    card = smoke.unit("round_marker", row="melee")
    state = smoke.fixture(card, "melee")
    p1, p2 = state["players"]["1"], state["players"]["2"]
    p1["last_row"] = "melee"
    p2["last_row"] = "siege"
    state["round"] = 1
    state["crowns"] = {"1": 0, "2": 0}
    gwent._resolve_round(state)
    assert state["round"] == 2 and p1["last_row"] is None and p2["last_row"] is None, (state["round"], p1, p2)
    return {"round_after_resolution": state["round"], "player_1_last_row": p1["last_row"], "player_2_last_row": p2["last_row"]}


for name, fn in [
    ("encadeamento_same_row_uses_previous_play", test_encadeamento_same_row_reads_previous_unit_play),
    ("encadeamento_different_row_no_bonus", test_encadeamento_different_row_no_bonus),
    ("adaptacao_other_row_uses_previous_play", test_adaptacao_other_row_requires_existing_history),
    ("adaptacao_without_previous_play_no_bonus", test_adaptacao_first_unit_play_no_bonus),
    ("quebra_ritmo_matches_opponent_previous_play", test_quebra_ritmo_reads_opponent_last_unit_play),
    ("quebra_ritmo_different_opponent_row_no_bonus", test_quebra_ritmo_opponent_different_row_no_bonus),
    ("movement_preserves_last_play_row_and_changes_next_sequence_result", test_movement_does_not_rewrite_last_played_row_used_by_next_sequence),
    ("special_action_does_not_update_last_play_row", test_special_action_does_not_update_last_row),
    ("removal_does_not_clear_last_play_row", test_removal_does_not_clear_last_row_history),
    ("round_transition_resets_last_play_row", test_round_transition_resets_both_players_last_row),
]:
    check(name, fn)

report = {
    "metadata": {
        "document": "Sequence power and last_row state audit v0.1",
        "status": "READ_ONLY_LEGACY_AUDIT; CANDIDATE_NOT_APPROVED",
        "engine": "sistemas.gwent.aplicar_jogada, _remover_unidade, _resolve_round",
        "baseline": "soulsbo-main-updated.zip",
        "method": "Synthetic in-memory fixtures exercising the three active generic sequence skills and player last_row lifecycle. No persistent state or runtime source is changed.",
    },
    "counts": {
        "assertions": len(CASES),
        "passed": sum(c["status"] == "passed" for c in CASES),
        "failed": sum(c["status"] == "failed" for c in CASES),
    },
    "cases": CASES,
    "limits": [
        "Covers the three active generic sequence skills encadeamento, adaptacao and quebra_ritmo; archived identity aliases veil_shift, pilgrim_duel and mist_trail are not reactivated or tested as active card abilities.",
        "Tests the existing last_row player field, not a proposed canonical schema or a complete 12-card game sequence.",
        "Fixtures are synthetic and do not assess balance, frequency of trigger conditions, UI copy, persisted-match migrations or production behavior.",
        "Results describe legacy behavior only; they do not approve preserving this behavior in the replacement engine.",
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
for case in CASES:
    if case["status"] != "passed":
        print(json.dumps(case, ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]:
    raise SystemExit(1)
