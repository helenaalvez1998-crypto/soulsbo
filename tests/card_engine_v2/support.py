"""Shared test fixtures for mechanics tests that must not measure balance tuning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog


def mechanics_catalog(temp_dir: str | Path, *, uniform_energy_cost: int = 1) -> AlphaCatalog:
    """Build the same allowlist with a simple explicit cost fixture.

    The gameplay-mechanics suites test effects, targeting and match flow rather
    than the provisional price schedule. A uniform price keeps the real energy
    checks active without making those suites dependent on balance proposals.
    Dedicated economy tests use the production alpha price schedule.
    """
    root = Path(__file__).resolve().parents[2]
    data_dir = root / "data/card_game"
    ruleset = json.loads((data_dir / "card-engine-v2-alpha-ruleset.v0.5.json").read_text(encoding="utf-8"))
    schedule = json.loads((data_dir / "card-engine-v2-alpha-energy-cost-schedule.v0.1.json").read_text(encoding="utf-8"))
    ruleset_energy = ruleset["energy_economy"]
    card_costs = {card_id: uniform_energy_cost for card_id in ruleset_energy["card_energy_cost_by_card_id"]}
    leader_costs = {leader_id: uniform_energy_cost for leader_id in ruleset_energy["leader_activation_energy_cost_by_leader_id"]}
    ruleset_energy["card_energy_cost_by_card_id"] = card_costs
    ruleset_energy["leader_activation_energy_cost_by_leader_id"] = leader_costs
    for card_id, cost in card_costs.items():
        schedule["card_energy_cost_by_card_id"][card_id]["energy_cost"] = cost
    for leader_id, cost in leader_costs.items():
        schedule["leader_activation_energy_cost_by_leader_id"][leader_id]["energy_cost"] = cost
    base = Path(temp_dir)
    ruleset_path = base / "mechanics-ruleset.json"
    schedule_path = base / "mechanics-cost-schedule.json"
    ruleset_path.write_text(json.dumps(ruleset, ensure_ascii=False, indent=2), encoding="utf-8")
    schedule_path.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
    return AlphaCatalog(ruleset_path=ruleset_path, cost_schedule_path=schedule_path)
