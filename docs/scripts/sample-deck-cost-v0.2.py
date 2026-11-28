#!/usr/bin/env python3
"""Reproduce revised exploratory deck-cost sampling for balance proposal v0.1.

Unlike v0.1, this version:
- does not assign guaranteed combo EFP merely because a card has one matching tag;
- includes the selected faction-compatible leader load;
- samples a separate equipped-relic scenario and excludes that relic from the 12 deck slots;
- makes assumptions and limitations explicit.

It remains cost-list sampling, NOT match/gameplay or win-rate simulation.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
DOCS = HERE.parents[1]
RELIC_IDS = {
    "reliquia_grande_runa_godrick",
    "reliquia_runa_nao_nascidos",
    "reliquia_runa_morte",
    "reliquia_noite_chama",
    "reliquia_lamina_negra",
    "reliquia_algemas_margit",
}
BUDGETS = (28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48)


def load_json(name: str) -> dict:
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def card_cost(power: int, effect_points: float) -> int:
    return clamp(math.ceil((power + 2 * effect_points) / 3.5), 1, 10)


def leader_load(effect_points: float) -> int:
    return clamp(math.ceil(effect_points / 2), 1, 5)


def build_models(trace: dict, effect_catalog: dict) -> tuple[list[dict], list[str]]:
    skill_scores = {item["id"]: item["efp_provisional"] for item in effect_catalog["generic_skills"]}
    identity_scores = {item["card_id"]: item["efp_provisional"] for item in effect_catalog["identity_effects"]}
    models: list[dict] = []
    skipped: list[str] = []

    for card in trace["cards"]:
        if card.get("identidade_id_ativa"):
            effect = identity_scores.get(card["card_id"])
        elif card.get("habilidade_id_runtime"):
            effect = skill_scores.get(card["habilidade_id_runtime"])
        else:
            effect = 0.0
        if effect is None:
            skipped.append(card["card_id"])
            continue

        is_unit = card["categoria"] == "Unidade"
        power = int(card.get("poder_base_runtime") or 0) if is_unit else 0
        cost = card_cost(power, float(effect))
        models.append({
            "card_id": card["card_id"],
            "category": "unit" if is_unit else "special",
            "faction": card.get("faccao_atual") if is_unit else None,
            "power_base_for_formula": power if is_unit else None,
            "effect_points_estimate": round(float(effect), 2),
            "deck_cost_estimate": cost,
        })
    return models, skipped


def summarize(totals: list[int], samples: int) -> dict:
    ordered = sorted(totals)
    return {
        "mean_cost": round(statistics.mean(ordered), 2),
        "median_cost": statistics.median(ordered),
        "min_cost": ordered[0],
        "max_cost": ordered[-1],
        "percentiles": {str(q): ordered[int(q * samples)] for q in (0.10, 0.25, 0.50, 0.75, 0.90, 0.95)},
        "acceptance_by_budget_percent": {
            str(budget): round(sum(value <= budget for value in ordered) / samples * 100, 1)
            for budget in BUDGETS
        },
    }


def sample_scenario(
    models: list[dict], leaders: list[dict], samples: int, seed: int, *, equipped_relic: bool
) -> dict:
    rng = random.Random(seed)
    units = [item for item in models if item["category"] == "unit"]
    specials = [item for item in models if item["category"] == "special"]
    relics = [item for item in specials if item["card_id"] in RELIC_IDS]
    specials_by_id = {item["card_id"]: item for item in specials}
    leaders_by_faction: dict[str, list[dict]] = defaultdict(list)
    for leader in leaders:
        leaders_by_faction[leader["faction"]].append(leader)
    if len(units) < 12 or len(specials) < 4 or len(relics) != 6:
        raise ValueError("Catalog does not satisfy the expected unit/special/relic baseline")

    totals: list[int] = []
    leader_loads: list[int] = []
    relic_costs: list[int] = []
    leader_selections: Counter[str] = Counter()
    faction_selections: Counter[str] = Counter()
    for _ in range(samples):
        relic = rng.choice(relics) if equipped_relic else None
        available_specials = [item for item in specials if relic is None or item["card_id"] != relic["card_id"]]
        unit_count = rng.randint(8, 12)
        deck = rng.sample(units, unit_count) + rng.sample(available_specials, 12 - unit_count)

        faction_counts = Counter(item["faction"] for item in deck if item["category"] == "unit")
        maximum = max(faction_counts.values())
        valid_factions = sorted(faction for faction, count in faction_counts.items() if count == maximum)
        faction = rng.choice(valid_factions)
        eligible_leaders = leaders_by_faction.get(faction, [])
        if not eligible_leaders:
            raise ValueError(f"No leader is mapped to dominant faction {faction}")
        leader = rng.choice(eligible_leaders)
        leader_cost = leader_load(float(leader["efp_provisional"]))
        relic_cost = int(relic["deck_cost_estimate"]) if relic else 0
        total = sum(int(item["deck_cost_estimate"]) for item in deck) + leader_cost + relic_cost
        totals.append(total)
        leader_loads.append(leader_cost)
        relic_costs.append(relic_cost)
        leader_selections[leader["id"]] += 1
        faction_selections[faction] += 1

    summary = summarize(totals, samples)
    summary.update({
        "scenario": "12 cards + faction-compatible leader load + equipped relic" if equipped_relic else "12 cards + faction-compatible leader load; no equipped relic",
        "equipped_relic_assumption": "uniform random among six relics; that same relic is excluded from the 12 deck slots" if equipped_relic else "no equipped relic",
        "leader_assumption": "uniform random among leaders belonging to a faction tied for the highest unit count in the sampled deck",
        "leader_load_distribution": dict(sorted(Counter(leader_loads).items())),
        "relic_cost_distribution": dict(sorted(Counter(relic_costs).items())),
        "leader_selection_counts": dict(sorted(leader_selections.items())),
        "dominant_faction_counts": dict(sorted(faction_selections.items())),
    })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DOCS / "card-game-deck-cost-sampling-v0.2.json")
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be at least 1")

    trace = load_json("card-game-card-traceability.json")
    effect_catalog = load_json("card-game-effect-score-catalog.json")
    models, skipped = build_models(trace, effect_catalog)
    leaders = effect_catalog["leaders"]
    results = {
        "metadata": {
            "document": "Deck cost sampling v0.2",
            "status": "EXPLORATORY ESTIMATE; BALANCE PROPOSAL NOT APPROVED",
            "sample_seed": args.seed,
            "sample_decks_per_scenario": args.samples,
            "cost_formula": "clamp(ceil((P + 2E) / 3.5), 1, 10); special uses P=0",
            "leader_load_formula": "clamp(ceil(E_leader / 2), 1, 5)",
            "combo_scoring": "excluded from card cost; separate random-order activation frequency is measured, but expected board swing and participant-level EFP are not calibrated",
            "deck_constraints": "12 unique models; 8-12 units; 0-4 specials",
            "dominant_faction": "choose any faction tied for the highest number of units; matching leader sampled uniformly from that faction",
        },
        "scoreable_models": len(models),
        "scoreable_units": sum(item["category"] == "unit" for item in models),
        "scoreable_specials": sum(item["category"] == "special" for item in models),
        "unscored_models_excluded": len(skipped),
        "unscored_card_ids": skipped,
        "scoreable_unit_faction_distribution": dict(sorted(Counter(item["faction"] for item in models if item["category"] == "unit").items())),
        "scenarios": {
            "without_equipped_relic": sample_scenario(models, leaders, args.samples, args.seed, equipped_relic=False),
            "with_equipped_relic": sample_scenario(models, leaders, args.samples, args.seed, equipped_relic=True),
        },
        "limitations": [
            "Random deck-list cost sampling, not matches, combat outcomes, or win-rate simulation.",
            "EFP values for card effects and leaders remain subjective provisional estimates.",
            "Combos are excluded from card cost. A separate random-order report measures trigger frequency, but not expected score swing or competitive value; no combo EFP is assigned.",
            "The model uniformly samples cards and leader choices; actual ownership, rarity/power exemplars, player choice and faction-specific strategy are not modeled.",
            "Nine unresolved card models are excluded, so this is not a complete 137-model sample.",
            "The six suspected faction assignments in the Forgotten expansion remain uncorrected in this baseline; faction distribution will change after their approved reassignment.",
            "The equipped relic is modeled as an extra cost and excluded from the 12 deck slots, matching the current backend validation rule.",
            "This model does not validate whether a 32-point cap is competitively fair.",
        ],
        "interpretation": "Use only to compare budget sensitivity under stated assumptions; do not approve or implement a budget based on this sample alone.",
    }
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "without_equipped_relic": results["scenarios"]["without_equipped_relic"]["acceptance_by_budget_percent"],
        "with_equipped_relic": results["scenarios"]["with_equipped_relic"]["acceptance_by_budget_percent"],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
