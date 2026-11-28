#!/usr/bin/env python3
"""Audit combo overlap, participant contribution and precedence with unique units.

Calls the current runtime resolver in deterministic catalog order. The scan is a
source-level/in-memory diagnostic, not a full match, ownership or balance test.
"""
from __future__ import annotations

import collections
import itertools
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sistemas import cartas, gwent  # noqa: E402

OUT = ROOT / "docs/card-game-combo-overlap-v0.2.json"
UNIT_IDS = [
    card_id for card_id in gwent.CARD_SYNERGY_TAGS
    if card_id in cartas.CARTAS_POR_ID
    and str(getattr(cartas.CARTAS_POR_ID[card_id], "categoria", "")).casefold() == "unidade"
]


def make_unit(card_id: str, row: str = "melee") -> dict[str, Any]:
    model = cartas.CARTAS_POR_ID[card_id]
    return {
        "id": card_id,
        "nome": str(getattr(model, "nome", card_id)),
        "row": row,
        "bonus": 0,
    }


def eligible_combos(participants: list[str]) -> list[str]:
    """Return all eligible combos in the runtime dictionary's precedence order."""
    tags_new = set(gwent.CARD_SYNERGY_TAGS.get(participants[-1], set()))
    if not tags_new:
        return []
    tags_total: set[str] = set()
    for card_id in participants:
        tags_total.update(gwent.CARD_SYNERGY_TAGS.get(card_id, set()))
    eligible: list[str] = []
    for combo_id, combo in sorted(
        gwent.SYNERGY_COMBOS.items(),
        key=lambda item: (int(item[1]["priority"]), str(item[0])),
    ):
        required = set(combo["tags"])
        # Match runtime: current played unit must contribute to this combo.
        if not (tags_new & required):
            continue
        if not required.issubset(tags_total):
            continue
        count = sum(
            bool(set(gwent.CARD_SYNERGY_TAGS.get(card_id, set())) & required)
            for card_id in participants
        )
        if count < int(combo.get("minimum", 2)):
            continue
        eligible.append(combo_id)
    return eligible


# Detect one-card activations using the actual resolver.
solo_activations: list[dict[str, Any]] = []
for card_id in UNIT_IDS:
    player = {"board": [], "synergy_used": {}}
    current = make_unit(card_id)
    name = gwent._aplicar_combo_de_cartas(player, current)
    if current.get("combo_ativado"):
        solo_activations.append({
            "card_id": card_id,
            "card_name": current["nome"],
            "combo_id": current["combo_ativado"],
            "combo_name": name,
            "card_tags": sorted(gwent.CARD_SYNERGY_TAGS[card_id]),
        })

# Ordered pair scan; card model IDs are distinct.
pair_overlap: list[dict[str, Any]] = []
pair_activation_counts: collections.Counter[str] = collections.Counter()
pair_ordered_count = 0
for first_id, current_id in itertools.permutations(UNIT_IDS, 2):
    pair_ordered_count += 1
    participants = [first_id, current_id]
    eligible = eligible_combos(participants)
    player = {"board": [make_unit(first_id, "ranged")], "synergy_used": {}}
    current = make_unit(current_id, "melee")
    resolved_name = gwent._aplicar_combo_de_cartas(player, current)
    actual_id = current.get("combo_ativado")
    if actual_id:
        pair_activation_counts[actual_id] += 1
    if len(eligible) > 1:
        pair_overlap.append({
            "played_order": participants,
            "eligible_in_precedence_order": eligible,
            "resolver_activated": actual_id,
            "resolver_name": resolved_name,
            "deferred_eligible_combos": eligible[1:],
        })
    expected = eligible[0] if eligible else None
    if actual_id != expected:
        raise AssertionError({"pair": participants, "expected": expected, "actual": actual_id})

# Ordered triple scan, using three distinct catalog unit IDs. Aggregate rather
# than storing all 287k permutations; retain only a compact set of examples.
triple_order_count = 0
multi_combo_sequences = 0
triple_combo_pair_counts: collections.Counter[tuple[str, str]] = collections.Counter()
triple_first_combo_counts: collections.Counter[str] = collections.Counter()
triple_later_combo_counts: collections.Counter[str] = collections.Counter()
later_contribution_counts: collections.Counter[str] = collections.Counter()
same_faction_multi_combo_sequences = 0
unrelated_trigger_examples: list[dict[str, Any]] = []
same_faction_examples: list[dict[str, Any]] = []
all_multi_combo_examples: list[dict[str, Any]] = []

for first_id, second_id, third_id in itertools.permutations(UNIT_IDS, 3):
    triple_order_count += 1
    player = {"board": [], "synergy_used": {}}
    events: list[dict[str, str]] = []
    for card_id in (first_id, second_id, third_id):
        current = make_unit(card_id)
        gwent._aplicar_combo_de_cartas(player, current)
        combo_id = current.get("combo_ativado")
        if combo_id:
            events.append({"combo_id": str(combo_id), "triggering_card_id": card_id})
        player["board"].append(current)

    distinct_combos = list(dict.fromkeys(event["combo_id"] for event in events))
    if len(distinct_combos) < 2:
        continue

    multi_combo_sequences += 1
    first_combo = distinct_combos[0]
    later_events = [event for event in events if event["combo_id"] != first_combo]
    all_checks: list[dict[str, Any]] = []
    for event in later_events:
        required = set(gwent.SYNERGY_COMBOS[event["combo_id"]]["tags"])
        current_tags = set(gwent.CARD_SYNERGY_TAGS.get(event["triggering_card_id"], set()))
        contributes = bool(required & current_tags)
        category = "contributed_required_tag" if contributes else "current_card_unrelated_to_required_tags"
        later_contribution_counts[category] += 1
        all_checks.append({
            **event,
            "current_card_tags": sorted(current_tags),
            "combo_required_tags": sorted(required),
            "current_card_contributes_required_tag": contributes,
        })
        if not contributes and len(unrelated_trigger_examples) < 100:
            unrelated_trigger_examples.append({
                "played_order": [first_id, second_id, third_id],
                "activation_events_in_order": events,
                "unrelated_later_trigger": all_checks[-1],
            })

    for later in later_events:
        triple_combo_pair_counts[(first_combo, later["combo_id"])] += 1
        triple_first_combo_counts[first_combo] += 1
        triple_later_combo_counts[later["combo_id"]] += 1

    factions = [str(getattr(cartas.CARTAS_POR_ID[x], "faccao", "")) for x in (first_id, second_id, third_id)]
    same_faction = len(set(factions)) == 1
    example = {
        "played_order": [first_id, second_id, third_id],
        "activation_events_in_order": events,
        "distinct_combos_in_order": distinct_combos,
        "later_combo_trigger_checks": all_checks,
        "same_faction": same_faction,
        "faction": factions[0] if same_faction else None,
    }
    if len(all_multi_combo_examples) < 100:
        all_multi_combo_examples.append(example)
    if same_faction:
        same_faction_multi_combo_sequences += 1
        if len(same_faction_examples) < 100:
            same_faction_examples.append(example)

# Example card metadata to make the issue understandable without code lookup.
example_ids = [
    "chefe_guardiao_cinzas",
    "gwent_unidade_baluarte",
    "covenant_irmandade_ferro",
    "gwent_unidade_eco",
]
example_card_metadata = {}
for card_id in example_ids:
    model = cartas.CARTAS_POR_ID[card_id]
    example_card_metadata[card_id] = {
        "name": str(getattr(model, "nome", card_id)),
        "faction": str(getattr(model, "faccao", "")),
        "category": str(getattr(model, "categoria", "")),
        "tags": sorted(gwent.CARD_SYNERGY_TAGS.get(card_id, set())),
    }

later_total = sum(later_contribution_counts.values())
report = {
    "metadata": {
        "document": "Combo overlap and precedence audit v0.2",
        "status": "POST-POLICY STATIC/IN-MEMORY RESOLVER DIAGNOSTIC; NOT A FULL MATCH OR BALANCE SIMULATION",
        "baseline": "post-policy runtime after V76 faction expansion (2026-11-28)",
        "runtime_modified": True,
        "resolver": "sistemas.gwent._aplicar_combo_de_cartas",
        "deck_constraint_reference": "bot.py::_api_gwent_deck_save (12 distinct card models)",
        "script": "docs/scripts/audit-combo-overlap-v0.2.py",
    },
    "catalog": {
        "unit_card_ids_with_synergy_tags": len(UNIT_IDS),
        "orphan_tag_ids_excluded": sorted(set(gwent.CARD_SYNERGY_TAGS) - set(UNIT_IDS)),
        "combo_definitions": len(gwent.SYNERGY_COMBOS),
        "combo_ids_without_explicit_minimum_participants": [
            combo_id for combo_id, combo in gwent.SYNERGY_COMBOS.items() if "minimum" not in combo
        ],
        "single_card_solo_activations": len(solo_activations),
        "ordered_two_card_plays_examined": pair_ordered_count,
        "ordered_three_card_sequences_examined": triple_order_count,
    },
    "single_card_activations": {"count": len(solo_activations), "cases": solo_activations},
    "two_card_overlap": {
        "ordered_plays_with_multiple_eligible_combos": len(pair_overlap),
        "unordered_distinct_card_pairs_with_multiple_eligible_combos": len({tuple(sorted(x["played_order"])) for x in pair_overlap}),
        "distinct_combos_involved_in_two_card_overlap": len({combo_id for item in pair_overlap for combo_id in item["eligible_in_precedence_order"]}),
        "percentage_of_ordered_two_card_plays": round(100 * len(pair_overlap) / pair_ordered_count, 4),
        "first_match_activation_counts_across_all_ordered_pairs": dict(pair_activation_counts),
        "examples_and_all_overlapping_ordered_pairs": pair_overlap,
    },
    "three_card_sequences": {
        "sequences_activating_at_least_two_distinct_combos": multi_combo_sequences,
        "percentage_of_ordered_three_card_sequences": round(100 * multi_combo_sequences / triple_order_count, 4),
        "distinct_ordered_combo_transition_pairs": len(triple_combo_pair_counts),
        "same_faction_sequences_activating_at_least_two_combos": same_faction_multi_combo_sequences,
        "later_combo_trigger_events": later_total,
        "later_combo_trigger_card_contribution": dict(later_contribution_counts),
        "later_combo_trigger_unrelated_card_percentage": round(
            100 * later_contribution_counts["current_card_unrelated_to_required_tags"] / max(1, later_total), 4
        ),
        "first_combo_counts": dict(triple_first_combo_counts),
        "second_combo_counts": dict(triple_later_combo_counts),
        "transition_pair_counts": [
            {"first_combo": a, "second_combo": b, "events": n}
            for (a, b), n in sorted(triple_combo_pair_counts.items())
        ],
        "sample_multi_combo_sequences": all_multi_combo_examples,
        "sample_same_faction_sequences": same_faction_examples,
        "sample_unrelated_later_triggers": unrelated_trigger_examples,
    },
    "example_card_metadata": example_card_metadata,
    "interpretation": [
        "The resolver sorts combo definitions by their unique priority and activates at most one combo per card play. Other eligible combos remain deferred until a later card play.",
        "The newly played card must contribute at least one tag required by the combo it activates. Participants are distinct unit instances, and each combo enforces its explicit minimum participant count.",
        "All 27 registered combos have an explicit minimum of two participants and unique integer priorities. The current catalog scan found zero single-card activations.",
        "The V76 scan uses 92 current catalog units with synergy tags; five orphan tag-map IDs absent from the catalog are excluded. It examines 8,372 ordered pairs and 753,480 ordered triples of distinct current unit IDs.",
        "The scans call the real in-memory resolver but do not instantiate complete legal 12-card decks, verify ownership, or simulate full matches, leaders, relics, weather, opponents, or persistent database state.",
        "Pair and triple frequencies describe the enumerated unit-ID universe only. They are not real-match activation rates, expected value, win rates, or proof of faction balance.",
    ],
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "unit_ids": len(UNIT_IDS),
    "combos": len(gwent.SYNERGY_COMBOS),
    "solo_activations": len(solo_activations),
    "ordered_pairs_examined": pair_ordered_count,
    "overlapping_ordered_pairs": len(pair_overlap),
    "overlapping_unordered_pairs": len({tuple(sorted(x["played_order"])) for x in pair_overlap}),
    "combos_involved_in_pair_overlap": len({combo_id for item in pair_overlap for combo_id in item["eligible_in_precedence_order"]}),
    "ordered_triples_examined": triple_order_count,
    "triples_with_two_or_more_combos": multi_combo_sequences,
    "same_faction_triples_with_two_or_more_combos": same_faction_multi_combo_sequences,
    "later_combo_trigger_card_contribution": dict(later_contribution_counts),
    "distinct_combo_transition_pairs": len(triple_combo_pair_counts),
}, ensure_ascii=False))
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
