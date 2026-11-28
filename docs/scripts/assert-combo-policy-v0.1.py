#!/usr/bin/env python3
"""Regression tests for the approved deterministic combo policy.

Runs the real in-memory resolver with controlled unit fixtures. This is not a
full match, production integration test, or competitive-balance simulation.
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

HELPER = ROOT / "docs/scripts/validate-card-effect-smoke-v0.1.py"
spec = importlib.util.spec_from_file_location("combo_policy_smoke_helpers", HELPER)
smoke = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(smoke)

OUT = ROOT / "docs/card-game-combo-policy-assertions-v0.1.json"
cases: list[dict[str, Any]] = []


def check(name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        cases.append({"case": name, "status": "passed", **fn()})
    except Exception as exc:  # preserve all failures in the report
        cases.append({"case": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})


def unit(card_id: str, row: str = "melee") -> dict[str, Any]:
    return smoke.unit(card_id, row=row, faction="Ordem Áurea")


def test_catalog_contract():
    combos = gwent.SYNERGY_COMBOS
    priorities = [combo.get("priority") for combo in combos.values()]
    missing = [combo_id for combo_id, combo in combos.items() if "minimum" not in combo]
    assert len(combos) == 27
    assert all(isinstance(value, int) for value in priorities)
    assert len(set(priorities)) == len(priorities), "priority values must be unique"
    assert not missing, f"combos without explicit minimum: {missing}"
    assert all(int(combo["minimum"]) == 2 for combo in combos.values())
    return {
        "combo_count": len(combos),
        "explicit_minimum": 2,
        "unique_priorities": sorted(priorities),
        "lower_priority_number_resolves_first": True,
    }


check("catalog_has_explicit_unique_priorities_and_two_participants", test_catalog_contract)


# Every combo must reject a one-card attempt, including the formerly solo-eligible
# `eco_convergente` hybrid card. At least one real tag provider is tested per combo.
for combo_id, combo in gwent.SYNERGY_COMBOS.items():
    required = set(combo["tags"])
    candidate_id = next(
        card_id
        for card_id, tags in gwent.CARD_SYNERGY_TAGS.items()
        if set(tags) & required
    )

    def single_card_cannot_activate(combo_id=combo_id, candidate_id=candidate_id):
        player = {"board": [], "synergy_used": {other: True for other in gwent.SYNERGY_COMBOS if other != combo_id}}
        card = unit(candidate_id)
        result = gwent._aplicar_combo_de_cartas(player, card)
        assert result is None
        assert card.get("combo_ativado") is None
        assert player["synergy_used"].get(combo_id) is not True
        return {"combo_id": combo_id, "single_card_id": candidate_id, "minimum": int(gwent.SYNERGY_COMBOS[combo_id]["minimum"]), "solo_activation_blocked": True}

    check(f"single_card_blocked_{combo_id}", single_card_cannot_activate)


def overlapping_combos_use_declared_priority_not_mapping_order():
    original = gwent.SYNERGY_COMBOS
    try:
        # Deliberately reverse insertion order. Explicit priority must still win.
        gwent.SYNERGY_COMBOS = dict(reversed(list(original.items())))
        first = unit("chefe_guardiao_cinzas", row="ranged")
        current = unit("gwent_unidade_baluarte", row="melee")
        player = {"board": [first], "synergy_used": {}}
        result = gwent._aplicar_combo_de_cartas(player, current)
        assert result == original["cinzas_fornalha"]["name"]
        assert current.get("combo_ativado") == "cinzas_fornalha"
        assert player["synergy_used"] == {"cinzas_fornalha": True}
        return {
            "eligible_overlap": ["cinzas_fornalha", "juramento_erdtree"],
            "activated": current["combo_ativado"],
            "priority": original["cinzas_fornalha"]["priority"],
            "reverse_insertion_order_tested": True,
            "one_combo_only": True,
        }
    finally:
        gwent.SYNERGY_COMBOS = original


check("overlap_uses_explicit_priority_and_one_combo_per_play", overlapping_combos_use_declared_priority_not_mapping_order)


def pending_combo_requires_new_participant_and_rewards_that_participant():
    # First two distinct units complete two combos at once. Explicit priority
    # activates cinzas_fornalha and leaves juramento_erdtree pending.
    first = unit("chefe_guardiao_cinzas", row="melee")
    second = unit("gwent_unidade_baluarte", row="ranged")
    player = {"board": [first], "synergy_used": {}}
    first_result = gwent._aplicar_combo_de_cartas(player, second)
    assert first_result == gwent.SYNERGY_COMBOS["cinzas_fornalha"]["name"]
    assert player["synergy_used"] == {"cinzas_fornalha": True}
    player["board"].append(second)

    # This third unit has a synergy tag, but not the required ordem_dourada tag.
    nonparticipant = unit("covenant_irmandade_ferro", row="melee")
    nonparticipant_result = gwent._aplicar_combo_de_cartas(player, nonparticipant)
    assert nonparticipant_result is None
    assert nonparticipant.get("combo_ativado") is None
    assert player["synergy_used"].get("juramento_erdtree") is not True
    player["board"].append(nonparticipant)

    # A later distinct unit contributes ordem_dourada and can collect the pending
    # combo. Its own bonus is rewarded, and team_bonus affects only same-row allies.
    participant = unit("gwent_unidade_mestre_forja", row="melee")
    participant_result = gwent._aplicar_combo_de_cartas(player, participant)
    assert participant_result == gwent.SYNERGY_COMBOS["juramento_erdtree"]["name"]
    assert participant.get("combo_ativado") == "juramento_erdtree"
    assert participant["bonus"] == 2
    assert first["bonus"] == 1
    assert nonparticipant["bonus"] == 1
    assert second["bonus"] == 2  # retains only its earlier combo bonus; different row gets no team bonus
    assert player["synergy_used"].get("juramento_erdtree") is True

    return {
        "first_combo": "cinzas_fornalha",
        "pending_combo": "juramento_erdtree",
        "unrelated_tag_card": nonparticipant["id"],
        "unrelated_card_did_not_collect_pending_combo": True,
        "later_participant": participant["id"],
        "individual_bonus_awarded_to_participant": participant["bonus"],
        "team_bonus_same_row_only": True,
    }


check("pending_combo_requires_contribution_and_rewards_participant", pending_combo_requires_new_participant_and_rewards_that_participant)


def actual_play_path_uses_the_approved_combo_policy():
    # Exercise the public play resolver, not only the private combo helper.
    first = unit("chefe_guardiao_cinzas", row="melee")
    current = unit("gwent_unidade_baluarte", row="melee")
    state = smoke.fixture(current, "melee")
    player = state["players"]["1"]
    player["board"] = [first]
    player["hand"] = [current, smoke.unit("integration_reserve", power=1)]
    player["synergy_used"] = {}
    player["faction"] = "Lua Negra"  # avoid the Order passive in this assertion
    player["faction_boost_used"] = True
    state["turn"] = "1"

    result = gwent.aplicar_jogada(state, 1, action="play", card_id=current["id"], row="melee")
    assert "error" not in result, result
    resolved_player = result["state"]["players"]["1"]
    resolved_card = next(card for card in resolved_player["board"] if card["id"] == current["id"])
    assert resolved_card.get("combo_ativado") == "cinzas_fornalha"
    assert resolved_card["bonus"] == 2
    assert resolved_player["synergy_used"].get("cinzas_fornalha") is True
    assert resolved_player["synergy_used"].get("juramento_erdtree") is not True
    return {
        "entrypoint": "aplicar_jogada(action='play')",
        "first_card_id": first["id"],
        "played_card_id": resolved_card["id"],
        "activated_combo": resolved_card["combo_ativado"],
        "individual_bonus": resolved_card["bonus"],
        "one_combo_only": True,
    }


check("actual_play_path_uses_the_approved_combo_policy", actual_play_path_uses_the_approved_combo_policy)


def same_unit_instance_is_not_counted_twice():
    # This intentionally malformed fixture places the exact same object in the
    # board and as the current card. It must count as one participant, not two.
    hybrid = unit("gwent_unidade_eco")
    player = {"board": [hybrid], "synergy_used": {other: True for other in gwent.SYNERGY_COMBOS if other != "eco_convergente"}}
    result = gwent._aplicar_combo_de_cartas(player, hybrid)
    assert result is None
    assert hybrid.get("combo_ativado") is None
    assert player["synergy_used"].get("eco_convergente") is not True
    return {"combo_id": "eco_convergente", "same_object_repeated": True, "distinct_participants_counted": 1, "activation_blocked": True}


check("same_unit_instance_is_not_counted_twice", same_unit_instance_is_not_counted_twice)


report = {
    "metadata": {
        "document": "Approved combo policy assertions v0.1",
        "status": "APPROVED POLICY REGRESSION TESTS; SYNTHETIC IN-MEMORY STATES; NOT A FULL MATCH OR BALANCE SIMULATION",
        "baseline": "soulsbo-main-handoff.zip at user approval on 2026-11-27",
        "engine": "sistemas.gwent._aplicar_combo_de_cartas",
        "policy": {
            "current_card_must_contribute_required_tag": True,
            "minimum_distinct_participants": 2,
            "one_combo_per_play": True,
            "explicit_priority_lower_number_first": True,
            "pending_combo_requires_later_contributing_participant": True,
            "individual_bonus_to_current_contributing_card": True,
        },
    },
    "counts": {
        "assertions": len(cases),
        "passed": sum(case["status"] == "passed" for case in cases),
        "failed": sum(case["status"] == "failed" for case in cases),
    },
    "combo_count": len(gwent.SYNERGY_COMBOS),
    "cases": cases,
    "limitations": [
        "Tests call the in-memory combo resolver with controlled fixtures; they are not full 12-card matches or production DB/API/frontend/Discord/R2 integration tests.",
        "One representative tag provider per combo is checked for a solo activation attempt; this does not exhaust every possible board sequence or alternate provider permutation.",
        "The pending-combo scenario covers one known overlap (`cinzas_fornalha` and `juramento_erdtree`); all 154 overlapping ordered pairs are not replayed as full stateful sequences here.",
        "The tests do not measure EFP, win rate, faction parity or competitive balance.",
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
