#!/usr/bin/env python3
"""HISTORICAL/SUPERSEDED: reproduce the exploratory deck-cost sampling v0.1.

This script intentionally preserves the old method for audit history. It credits
partial combo-tag intersections and omits leader/relic costs; do NOT use it to
recommend or approve the current deck budget. Use sample-deck-cost-v0.2.py.
It samples card lists and cost totals only, not matches or win rates.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve()
DOCS = HERE.parents[1]


def load_json(name: str) -> dict:
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def build_costable_models(trace: dict, effect_catalog: dict) -> tuple[list[dict], list[str]]:
    skill_scores = {item["id"]: item["efp_provisional"] for item in effect_catalog["generic_skills"]}
    identity_scores = {item["card_id"]: item["efp_provisional"] for item in effect_catalog["identity_effects"]}
    combos = effect_catalog["combos"]
    models: list[dict] = []
    skipped: list[str] = []

    for card in trace["cards"]:
        tags = set(card.get("tags_combo") or [])
        combo_score = 0.0
        for combo in combos:
            if tags.intersection(combo.get("required_tags") or []):
                participants = combo.get("minimum") or max(1, len(combo.get("required_tags") or []))
                share = 0.5 * (combo.get("bonus", 0) + 2 * combo.get("team_bonus", 0)) / participants
                combo_score += min(2.0, share)
        combo_score = min(2.0, combo_score)

        if card.get("identidade_id_ativa"):
            individual_score = identity_scores.get(card["card_id"])
        elif card.get("habilidade_id_runtime"):
            skill_id = card["habilidade_id_runtime"]
            individual_score = skill_scores.get(skill_id) if skill_id in skill_scores else None
        else:
            # No individual skill or identity: this is a zero-effect card for this estimate.
            individual_score = 0.0

        if individual_score is None:
            skipped.append(card["card_id"])
            continue

        effect_score = min(10.0, float(individual_score) + combo_score)
        is_unit = card["categoria"] == "Unidade"
        base_power = int(card["poder_base_runtime"]) if is_unit else 0
        cost = clamp(math.ceil((base_power + 2 * effect_score) / 3.5), 1, 10)
        rarity_score = 2 * base_power + 3 * effect_score + 0.5 * (10 - cost)
        models.append({
            "card_id": card["card_id"],
            "category": "unit" if is_unit else "special",
            "power_base_for_formula": base_power,
            "effect_points_estimate": round(effect_score, 2),
            "deck_cost_estimate": cost,
            "rarity_score_estimate": round(rarity_score, 2),
        })
    return models, skipped


def sample(models: list[dict], samples: int, seed: int) -> dict:
    units = [item for item in models if item["category"] == "unit"]
    specials = [item for item in models if item["category"] == "special"]
    if len(units) < 12 or len(specials) < 4:
        raise ValueError("Not enough scored models to sample the current 8–12 unit / 0–4 special deck constraints")

    rng = random.Random(seed)
    totals: list[int] = []
    for _ in range(samples):
        unit_count = rng.randint(8, 12)
        chosen = rng.sample(units, unit_count) + rng.sample(specials, 12 - unit_count)
        totals.append(sum(item["deck_cost_estimate"] for item in chosen))

    ordered = sorted(totals)
    acceptance = {
        str(budget): round(sum(value <= budget for value in ordered) / samples * 100, 1)
        for budget in (28, 30, 32, 34, 36, 38, 40, 42)
    }
    return {
        "sample_seed": seed,
        "sample_decks": samples,
        "scoreable_models": len(models),
        "scoreable_units": len(units),
        "scoreable_specials": len(specials),
        "deck_constraints_simulated": "12 unique models; 8–12 units; 0–4 specials",
        "mean_cost": round(statistics.mean(totals), 2),
        "median_cost": statistics.median(totals),
        "min_cost": ordered[0],
        "max_cost": ordered[-1],
        "percentiles": {str(q): ordered[int(q * samples)] for q in (0.10, 0.25, 0.50, 0.75, 0.90, 0.95)},
        "acceptance_by_budget_percent": acceptance,
        "limitations": [
            "This is random deck-list sampling, not a match/gameplay simulation.",
            "It excludes cards with unresolved or unscored skill IDs.",
            "It does not model faction restrictions, ownership, leader, relic, draw order, combos actually activating, win rates or player strategy.",
            "EFP values are provisional design estimates and are not validated combat outcomes.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DOCS / "card-game-deck-cost-sampling-v0.1.json")
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be at least 1")

    trace = load_json("card-game-card-traceability.json")
    effect_catalog = load_json("card-game-effect-score-catalog.json")
    models, skipped = build_costable_models(trace, effect_catalog)
    result = sample(models, args.samples, args.seed)
    result["unscored_models_excluded"] = len(skipped)
    result["unscored_card_ids"] = skipped
    result["interpretation"] = "Exploratory cost-distribution estimate only; does not demonstrate game balance."
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
