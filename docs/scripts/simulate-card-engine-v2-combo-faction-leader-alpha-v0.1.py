#!/usr/bin/env python3
"""Run one isolated sequence proving combo, faction passive and leader activation."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog  # noqa: E402
from sistemas.card_engine_v2.match import AlphaMatchController  # noqa: E402
from sistemas.card_engine_v2.repository import SQLiteMatchRepository  # noqa: E402
from tests.card_engine_v2.support import mechanics_catalog  # noqa: E402

PLAYER_A = "1001"
PLAYER_B = "2002"
MATCH_ID = 2026112899

DECK_A = [
    "gwent_unidade_herdeiro_portao",
    "gwent_unidade_veterano_cercos",
    "arma_lanca_fornalha",
    "arma_cajado_marulho",
    "arma_martelo_fornalha",
    "arma_grande_sino",
    "arma_duas_luas",
    "magia_nevoa_antiga",
    "chefe_vigia_cinzento",
    "chefe_dama_vazio",
    "luterano_anjo",
    "luterano_papa",
]
DECK_B = [
    "chefe_vigia_cinzento",
    "arma_lanca_fornalha",
    "arma_cajado_marulho",
    "arma_martelo_fornalha",
    "arma_grande_sino",
    "arma_duas_luas",
    "magia_nevoa_antiga",
    "chefe_dama_vazio",
    "luterano_anjo",
    "luterano_papa",
    "chefe_vigia_cinzento",
    "arma_lanca_fornalha",
]


def main() -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="soulsbo-combo-leader-alpha-") as directory:
        repository = SQLiteMatchRepository(Path(directory) / "combo-leader.sqlite3")
        catalog = mechanics_catalog(directory)
        controller = AlphaMatchController(repository, catalog)
        controller.create_match(
            match_id=MATCH_ID,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: DECK_A, PLAYER_B: DECK_B},
            initial_hand_size=12,
            player_factions={PLAYER_A: "golden_order"},
            leaders={PLAYER_A: "comandante_fornalha"},
        )

        def hand_instance(player_id: str, card_id: str) -> str:
            state = repository.get_match(MATCH_ID)
            return next(
                instance_id for instance_id in state["players"][player_id]["zones"]["hand"]
                if state["instances"][instance_id]["card_id"] == card_id
            )

        def record(label: str, player_id: str, receipt: Any) -> None:
            actions.append({
                "step": len(actions) + 1,
                "label": label,
                "player_id": player_id,
                "outcome": receipt.result["outcome"],
                "reason_code": receipt.result.get("reason_code"),
                "costs": receipt.result.get("costs", {}),
                "revision": repository.get_match(MATCH_ID)["state_revision"],
            })
            if receipt.result["outcome"] != "applied":
                raise RuntimeError(f"scenario action failed: {label}: {receipt.result}")

        record(
            "A plays Godwyn; first Golden Order unit receives faction passive +1",
            PLAYER_A,
            controller.play_unit(MATCH_ID, actor_player_id=PLAYER_A, instance_id=hand_instance(PLAYER_A, "gwent_unidade_herdeiro_portao")),
        )
        record(
            "B plays Grey Watcher",
            PLAYER_B,
            controller.play_unit(MATCH_ID, actor_player_id=PLAYER_B, instance_id=hand_instance(PLAYER_B, "chefe_vigia_cinzento")),
        )
        record(
            "A plays Dragon Knight; Muralha combo grants +2 to activator and +1 to prior same-row ally",
            PLAYER_A,
            controller.play_unit(MATCH_ID, actor_player_id=PLAYER_A, instance_id=hand_instance(PLAYER_A, "gwent_unidade_veterano_cercos")),
        )
        record(
            "B plays Fornalha Lancer",
            PLAYER_B,
            controller.play_unit(MATCH_ID, actor_player_id=PLAYER_B, instance_id=hand_instance(PLAYER_B, "arma_lanca_fornalha")),
        )
        record(
            "A activates Godfrey; all A melee units receive +2",
            PLAYER_A,
            controller.activate_leader(MATCH_ID, actor_player_id=PLAYER_A),
        )
        record("B passes", PLAYER_B, controller.pass_turn(MATCH_ID, actor_player_id=PLAYER_B))
        record("A passes and closes the round", PLAYER_A, controller.pass_turn(MATCH_ID, actor_player_id=PLAYER_A))

        events = repository.get_events(MATCH_ID)
        counts = Counter(event["kind"] for event in events)
        state = repository.get_match(MATCH_ID)
        runtime = repository.get_match_runtime(MATCH_ID)
        integrity = repository.verify_integrity()
        history = runtime["round_history"]
        if len(history) != 1 or history[0]["winner_player_id"] != PLAYER_A:
            raise RuntimeError(f"expected A to win the demo round: {history}")
        if counts["card_combo_activated"] != 1 or counts["faction_passive_applied"] != 1 or counts["leader_activated"] != 1:
            raise RuntimeError(f"missing combo/passive/leader event: {counts}")
        if integrity.get("ok") is not True:
            raise RuntimeError(f"SQLite integrity failure: {integrity}")

        return {
            "scenario": "combo_faction_passive_leader_sequence_alpha",
            "energy_cost_fixture": "uniform_1_for_mechanics_simulation_only; not_a_balance_validation",
            "catalog_release_id": catalog.definition_manifest()["catalog_release_id"],
            "player_factions": {PLAYER_A: "golden_order", PLAYER_B: None},
            "leaders": {PLAYER_A: "comandante_fornalha", PLAYER_B: None},
            "actions": actions,
            "event_count": len(events),
            "event_counts": dict(sorted(counts.items())),
            "combo_ids_activated": [event["payload"]["combo_id"] for event in events if event["kind"] == "card_combo_activated"],
            "round_history": history,
            "round_winner": history[0]["winner_player_id"],
            "round_scores": history[0]["scores"],
            "player_a_state": state["players"][PLAYER_A]["round_state"],
            "sqlite_integrity": integrity,
            "runtime_integration": False,
            "production_database_access": False,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="Optional path to save the JSON result")
    args = parser.parse_args()
    report = main()
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
