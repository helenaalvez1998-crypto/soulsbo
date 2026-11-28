#!/usr/bin/env python3
"""Estimate activation frequency of the live combo resolver under random deck/play scenarios.

Uses actual CARD_SYNERGY_TAGS, SYNERGY_COMBOS and _aplicar_combo_de_cartas.
This is a random-play diagnostic, not a gameplay/strategy/win-rate simulation.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import cartas, gwent  # noqa: E402

OUT_DEFAULT = ROOT / "docs" / "card-game-combo-activation-v0.1.json"


def model_ids() -> tuple[list[str], list[str]]:
    units = [card.id for card in cartas.CARTAS_POR_ID.values() if str(card.categoria).casefold() != "especial"]
    specials = [card.id for card in cartas.CARTAS_POR_ID.values() if str(card.categoria).casefold() == "especial"]
    return sorted(set(units)), sorted(set(specials))


def potential_combos(hand: list[str]) -> set[str]:
    tags_total = set()
    for card_id in hand:
        tags_total.update(gwent.CARD_SYNERGY_TAGS.get(card_id, set()))
    participants = hand
    potential = set()
    for combo_id, combo in gwent.SYNERGY_COMBOS.items():
        required = set(combo["tags"])
        if not required.issubset(tags_total):
            continue
        if "minimum" in combo:
            count = sum(bool(gwent.CARD_SYNERGY_TAGS.get(card_id, set()) & required) for card_id in participants)
            if count < int(combo["minimum"]):
                continue
        potential.add(combo_id)
    return potential


def simulate(samples: int, seed: int) -> dict:
    rng = random.Random(seed)
    units, specials = model_ids()
    combos = gwent.SYNERGY_COMBOS
    current_ids = set(units) | set(specials)
    tagged_ids = set(gwent.CARD_SYNERGY_TAGS)
    orphan_tag_ids = sorted(tagged_ids - current_ids)
    unit_tag_ids = sorted(set(units) & tagged_ids)

    if len(units) < 12 or len(specials) < 4:
        raise ValueError("Current card model catalog cannot satisfy the 12-card sampling constraint")

    potential_counts: Counter[str] = Counter()
    actual_counts: Counter[str] = Counter()
    completed_deck_count = 0
    total_actual = 0
    total_potential = 0
    actual_per_deck: list[int] = []
    first_trigger_cards: Counter[str] = Counter()

    for _ in range(samples):
        unit_count = rng.randint(8, 12)
        deck = rng.sample(units, unit_count) + rng.sample(specials, 12 - unit_count)
        opening_hand = rng.sample(deck, 10)  # the current match starts with 10 cards from a 12-card deck
        rng.shuffle(opening_hand)  # assume random play order, not optimal sequencing

        potential = potential_combos(opening_hand)
        potential_counts.update(potential)
        total_potential += len(potential)

        player = {"board": [], "synergy_used": {}}
        activated_this_deck = set()
        for card_id in opening_hand:
            card = {"id": card_id, "row": "melee", "bonus": 0}
            combo_name = gwent._aplicar_combo_de_cartas(player, card)
            if combo_name:
                combo_id = card.get("combo_ativado")
                activated_this_deck.add(combo_id)
                first_trigger_cards[card_id] += 1
            player["board"].append(card)
        actual_counts.update(activated_this_deck)
        total_actual += len(activated_this_deck)
        actual_per_deck.append(len(activated_this_deck))
        if activated_this_deck:
            completed_deck_count += 1

    def pct(n: int) -> float:
        return round(n / samples * 100, 2)

    per_combo = []
    for combo_id, combo in combos.items():
        potential_n = potential_counts[combo_id]
        actual_n = actual_counts[combo_id]
        per_combo.append({
            "id": combo_id,
            "name": combo["name"],
            "potential_in_opening_hand_percent": pct(potential_n),
            "actual_activation_random_order_percent": pct(actual_n),
            "potential_but_not_activated_percent": pct(max(0, potential_n - actual_n)),
            "actual_activation_given_potential_percent": round(actual_n / potential_n * 100, 2) if potential_n else None,
            "minimum_participants": combo.get("minimum"),
            "required_tags": sorted(combo["tags"]),
            "bonus": combo.get("bonus", 0),
            "team_bonus": combo.get("team_bonus", 0),
        })

    ordered_decks = sorted(actual_per_deck)
    return {
        "metadata": {
            "document": "Combo activation sampling v0.1",
            "status": "EXPLORATORY RANDOM-ORDER ESTIMATE; NOT GAME BALANCE APPROVAL",
            "sample_seed": seed,
            "sample_decks": samples,
            "deck_constraint": "12 unique models; 8-12 units; 0-4 specials",
            "initial_hand": 10,
            "play_order": "uniform random order; all 10 opening-hand cards assumed played in the same round",
            "resolver": "sistemas.gwent._aplicar_combo_de_cartas",
            "note": "The actual resolver's once-per-round rule and first-eligible-combo behavior are used. The card selection is random only for estimating current trigger frequency; it does not assign or generate new card mechanics.",
        },
        "catalog_coverage": {
            "units": len(units),
            "specials": len(specials),
            "combos": len(combos),
            "cards_with_synergy_tags_in_catalog": len(unit_tag_ids),
            "orphan_tag_card_ids": orphan_tag_ids,
        },
        "deck_level": {
            "decks_with_at_least_one_actual_combo_percent": pct(completed_deck_count),
            "mean_potential_combos_per_opening_hand": round(total_potential / samples, 3),
            "mean_actual_combos_per_opening_hand": round(total_actual / samples, 3),
            "actual_combos_per_deck_percentiles": {
                "p50": ordered_decks[int(0.50 * samples)],
                "p90": ordered_decks[int(0.90 * samples)],
                "p95": ordered_decks[int(0.95 * samples)],
                "max": ordered_decks[-1],
            },
            "most_frequent_triggering_cards": [
                {"card_id": card_id, "combo_completion_count": count}
                for card_id, count in first_trigger_cards.most_common(20)
            ],
        },
        "by_combo": per_combo,
        "limitations": [
            "Randomly selected decks are not filtered by ownership, chosen leader strategy, exemplar rarity/power, or actual faction distribution preferences.",
            "Assumes every one of the 10 opening-hand cards is played in one round; real players may pass early, change sequence, or draw more cards.",
            "A random play order is not an optimal play policy; activation frequencies are order-sensitive because only the first eligible combo can trigger per card play.",
            "Does not measure how often the combo changes match outcomes or the value of its buff at the final score.",
            "This is not a simulation of opposing effects, board removal, weather, or status conditions.",
        ],
        "interpretation": "Use the per-combo rates as a first calibration input for E_combo; do not treat them as competitive win-rate evidence.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be at least 1")
    result = simulate(args.samples, args.seed)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["deck_level"], ensure_ascii=False, indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
