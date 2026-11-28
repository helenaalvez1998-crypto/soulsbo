#!/usr/bin/env python3
"""Behavioral assertions for all current card combos and faction passive.

Exercises the real combo resolver and the real unit/special play path using
synthetic controlled states. This is not a full match or balance simulation.
"""
from __future__ import annotations
import importlib.util, itertools, json, sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import cartas, gwent  # noqa: E402

SP = ROOT / "docs/scripts/validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("combo_faction_smoke_helpers", SP)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)
OUT = ROOT / "docs/card-game-combo-faction-assertions-v0.1.json"

cases: list[dict[str, Any]] = []
def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        cases.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:
        cases.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})

def build_combo_pair(combo_id: str):
    combo = gwent.SYNERGY_COMBOS[combo_id]
    required = set(combo["tags"])
    provider_ids = list(gwent.CARD_SYNERGY_TAGS)
    minimum = int(combo.get("minimum", 1))
    # Search the real tag map and resolver; only retain a pair which activates
    # this exact combo first, not merely a pair with overlapping tags.
    for current_id in provider_ids:
        current_tags = set(gwent.CARD_SYNERGY_TAGS.get(current_id, set()))
        if not current_tags.intersection(required):
            continue
        other_ids_all = [x for x in provider_ids if x != current_id]
        for count in range(max(0, minimum - 1), 3):
            for partner_ids in itertools.combinations(other_ids_all, count):
                all_tags = set(current_tags)
                for partner_id in partner_ids:
                    all_tags.update(gwent.CARD_SYNERGY_TAGS.get(partner_id, set()))
                if not required.issubset(all_tags):
                    continue
                participants = [*partner_ids, current_id]
                qualifying = sum(
                    bool(set(gwent.CARD_SYNERGY_TAGS.get(card_id, set())).intersection(required))
                    for card_id in participants
                )
                if qualifying < minimum:
                    continue
                partner_cards = [smoke.unit(card_id, row="ranged", faction="Ordem Áurea") for card_id in partner_ids]
                # No-tag ally on the current card's row makes team_bonus observable.
                same_row_ally = smoke.unit(f"filler_{combo_id}", row="melee", faction="Ordem Áurea")
                board = [*partner_cards, same_row_ally]
                player = {"board": board, "synergy_used": {}}
                current = smoke.unit(current_id, row="melee", faction="Ordem Áurea")
                result = gwent._aplicar_combo_de_cartas(player, current)
                if result == combo["name"] and current.get("combo_ativado") == combo_id:
                    return current_id, partner_ids
    raise AssertionError(f"No activating pair found for {combo_id}; do not infer impossible combo without review")

def new_combo_state(combo_id: str, current_id: str, partner_ids: tuple[str, ...]):
    partners = [smoke.unit(card_id, row="ranged", faction="Ordem Áurea") for card_id in partner_ids]
    filler = smoke.unit(f"filler_{combo_id}", row="melee", faction="Ordem Áurea")
    player = {"board": [*partners, filler], "synergy_used": {}}
    current = smoke.unit(current_id, row="melee", faction="Ordem Áurea")
    return player, current, filler, partners

# Positive coverage of every declared combo and its team bonus semantics.
combo_pairs: dict[str, tuple[str, tuple[str, ...]]] = {}
for combo_id in gwent.SYNERGY_COMBOS:
    combo_pairs[combo_id] = build_combo_pair(combo_id)

def combo_positive(combo_id: str):
    combo = gwent.SYNERGY_COMBOS[combo_id]
    current_id, partner_ids = combo_pairs[combo_id]
    player, current, filler, partners = new_combo_state(combo_id, current_id, partner_ids)
    result = gwent._aplicar_combo_de_cartas(player, current)
    assert result == combo["name"], {"expected": combo["name"], "got": result}
    assert current.get("combo_ativado") == combo_id
    assert current["bonus"] == int(combo.get("bonus", 0))
    assert player["synergy_used"].get(combo_id) is True
    expected_team = int(combo.get("team_bonus", 0))
    assert filler["bonus"] == expected_team
    assert all(x["bonus"] == 0 for x in partners), "Partners on another row must not receive team_bonus"
    return {
        "combo_id": combo_id,
        "combo_name": combo["name"],
        "current_card_id": current_id,
        "partner_card_ids": list(partner_ids),
        "required_tags": sorted(combo["tags"]),
        "bonus_to_completing_card": combo.get("bonus", 0),
        "team_bonus_to_existing_same_row_ally": expected_team,
    }

for combo_id in gwent.SYNERGY_COMBOS:
    check(f"combo_positive_{combo_id}", lambda combo_id=combo_id: combo_positive(combo_id))

def combo_negative_missing_requirement(combo_id: str):
    combo = gwent.SYNERGY_COMBOS[combo_id]
    current_id, partner_ids = combo_pairs[combo_id]
    # Remove the partner set that is needed to complete this exact combo. Disable
    # unrelated combos to isolate the required-tag/minimum check under test.
    player = {"board": [], "synergy_used": {other: True for other in gwent.SYNERGY_COMBOS if other != combo_id}}
    current = smoke.unit(current_id, row="melee")
    result = gwent._aplicar_combo_de_cartas(player, current)
    assert result is None
    assert player["synergy_used"].get(combo_id) is not True
    assert current.get("combo_ativado") is None
    return {"combo_id": combo_id, "current_card_id": current_id, "omitted_partner_ids": list(partner_ids), "not_activated": True}

for combo_id in gwent.SYNERGY_COMBOS:
    check(f"combo_negative_incomplete_{combo_id}", lambda combo_id=combo_id: combo_negative_missing_requirement(combo_id))

def combo_once_per_round(combo_id: str):
    combo = gwent.SYNERGY_COMBOS[combo_id]
    current_id, partner_ids = combo_pairs[combo_id]
    player, first_card, filler, partners = new_combo_state(combo_id, current_id, partner_ids)
    first = gwent._aplicar_combo_de_cartas(player, first_card)
    assert first == combo["name"]
    second_card = smoke.unit(current_id, row="melee")
    second = gwent._aplicar_combo_de_cartas(player, second_card)
    # Other combinations may validly activate from the same tag set. The invariant
    # under test is that this exact combo cannot activate twice in one round.
    assert player["synergy_used"].get(combo_id) is True
    assert second_card.get("combo_ativado") != combo_id
    return {
        "combo_id": combo_id,
        "first_activation": True,
        "second_activation_of_same_combo_blocked": True,
        "other_combo_triggered_on_second_card": second_card.get("combo_ativado"),
        "resolver_return_on_second_card": second,
    }

for combo_id in gwent.SYNERGY_COMBOS:
    check(f"combo_once_per_round_{combo_id}", lambda combo_id=combo_id: combo_once_per_round(combo_id))

def test_empty_tag_card_does_not_trigger_combo():
    player = {"board": [], "synergy_used": {}}
    card = smoke.unit("no_synergy_tag_card")
    result = gwent._aplicar_combo_de_cartas(player, card)
    assert result is None and player["synergy_used"] == {}
    return {"no_tag_card": card["id"], "combo": None}
check("combo_empty_tag_card_does_not_trigger", test_empty_tag_card_does_not_trigger_combo)

# Faction passive: first matching unit gets +1; foreign faction neither receives
# nor consumes it; later own-faction units do not get a second activation.
FACTIONS = ["Ordem Áurea", "Lua Negra", "Véu Carmesim", "Os Esquecidos"]
def passive_state(faction: str):
    placeholder = smoke.unit("faction_passive_fixture")
    state = smoke.fixture(placeholder, "melee")
    state["phase"] = "battle"
    state["round"] = 1
    state["turn"] = "1"
    state["weather"] = {"melee": 0, "ranged": 0, "siege": 0}
    p, o = state["players"]["1"], state["players"]["2"]
    p["faction"] = faction
    p["faction_boost_used"] = False
    p["synergy_used"] = {}
    p["passed"] = False
    p["board"] = []
    p["hand"] = [
        smoke.unit(f"foreign_{faction}", faction=next(x for x in FACTIONS if x != faction), power=3),
        smoke.unit(f"first_{faction}", faction=faction, power=3),
        smoke.unit(f"second_{faction}", faction=faction, power=3),
        smoke.unit(f"reserve_{faction}", faction=faction, power=2),
    ]
    o["board"] = [smoke.unit(f"opponent_{faction}", faction=next(x for x in FACTIONS if x != faction), power=1)]
    o["passed"] = False
    return state

def play_one(state, card_id):
    result = gwent.aplicar_jogada(state, 1, action="play", card_id=card_id, row="melee")
    assert "error" not in result, result
    return result["state"]

def faction_passive_case(faction: str):
    state = passive_state(faction)
    foreign_id, first_id, second_id = (f"foreign_{faction}", f"first_{faction}", f"second_{faction}")
    state = play_one(state, foreign_id)
    player = state["players"]["1"]
    foreign = next(x for x in player["board"] if x["id"] == foreign_id)
    assert foreign["bonus"] == 0 and player["faction_boost_used"] is False
    state["turn"] = "1"
    state = play_one(state, first_id)
    player = state["players"]["1"]
    first = next(x for x in player["board"] if x["id"] == first_id)
    assert first["bonus"] == 1 and player["faction_boost_used"] is True
    state["turn"] = "1"
    state = play_one(state, second_id)
    player = state["players"]["1"]
    second = next(x for x in player["board"] if x["id"] == second_id)
    assert second["bonus"] == 0 and player["faction_boost_used"] is True
    # Resolve a deliberately won round to verify the passive resets for the next round.
    state["players"]["2"]["board"] = [smoke.unit(f"weak_enemy_{faction}", faction=next(x for x in FACTIONS if x != faction), power=1)]
    gwent._resolve_round(state)
    player = state["players"]["1"]
    assert player["faction_boost_used"] is False
    assert player["synergy_used"] == {}
    return {"faction": faction, "foreign_unit_did_not_consume_passive": True, "first_matching_unit_bonus": 1, "second_matching_unit_bonus": 0, "reset_after_round": True}

for faction in FACTIONS:
    check(f"faction_passive_{faction.casefold().replace(' ', '_')}", lambda faction=faction: faction_passive_case(faction))

def test_special_does_not_consume_unit_passive():
    special_id = "gwent_especial_chifre"
    special = cartas.CARTAS_POR_ID[special_id].para_dict()
    state = passive_state("Ordem Áurea")
    player = state["players"]["1"]
    # Put the real catalog special first in hand and no units on board.
    player["hand"] = [special, smoke.unit("special_passive_reserve", faction="Ordem Áurea")]
    result = gwent.aplicar_jogada(state, 1, action="play", card_id=special_id, row="melee")
    assert "error" not in result, result
    resolved = result["state"]["players"]["1"]
    assert resolved["faction_boost_used"] is False
    used = next(x for x in resolved["discard"] if x["id"] == special_id)
    assert int(used.get("bonus", 0) or 0) == 0
    return {"special_card_id": special_id, "passive_consumed": False, "passive_bonus_applied": 0}
check("special_cards_do_not_consume_unit_faction_passive", test_special_does_not_consume_unit_passive)

report = {
    "metadata": {
        "document": "Combo and faction passive behavior assertions v0.1",
        "status": "DIAGNOSTIC ONLY; ALL DECLARED COMBOS AND FOUR FACTION PASSIVES IN SYNTHETIC STATES",
        "baseline": "soulsbo-main(1).zip",
        "engine": "sistemas.gwent._aplicar_combo_de_cartas, aplicar_jogada, _resolve_round",
    },
    "counts": {"assertions": len(cases), "passed": sum(x["status"] == "passed" for x in cases), "failed": sum(x["status"] == "failed" for x in cases)},
    "combo_count": len(gwent.SYNERGY_COMBOS),
    "combo_ids": list(gwent.SYNERGY_COMBOS),
    "cases": cases,
    "limitations": [
        "Each combo has one concrete activating card pair discovered from the current tag map and verified against the actual resolver; alternate card combinations and all tag permutations are not exhausted.",
        "The negative combo cases isolate the tested combo by marking other combos used; they verify missing partner/participant behavior, not all overlapping-combo precedence permutations.",
        "Faction passive tests cover each faction's foreign-card, first matching unit, second matching unit and round-reset behavior; they do not test every faction-specific card identity or rarity modifier.",
        "The special-card test confirms the separate special branch does not consume the unit-only faction passive in the tested catalog card.",
        "Synthetic fixtures are not complete matches and do not measure win rate, effect EV or competitive balance; no DB/API/frontend/Discord/R2 integration is exercised.",
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["counts"], ensure_ascii=False))
for case in cases:
    if case["status"] != "passed":
        print(json.dumps(case, ensure_ascii=False))
print(f"wrote {OUT}")
if report["counts"]["failed"]:
    raise SystemExit(1)
