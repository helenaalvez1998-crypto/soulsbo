#!/usr/bin/env python3
"""Run a complete isolated best-of-three Card Engine v2 alpha match.

Uses a temporary SQLite database and the explicit alpha catalog allowlist.
This is a reproducible sandbox scenario, not a production game integration.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog  # noqa: E402
from sistemas.card_engine_v2.match import AlphaMatchController  # noqa: E402
from sistemas.card_engine_v2.repository import SQLiteMatchRepository  # noqa: E402

PLAYER_A = "1001"
PLAYER_B = "2002"
MATCH_ID = 202611270001

DECK_A = [
    "gwent_v75_ordem_veterano_juramento",
    "arma_lanca_fornalha",
    "gwent_especial_tempestade",
    "gwent_especial_execucao",
    "gwent_especial_egide",
    "elden_especial_geada",
    "arma_martelo_fornalha",
    "arma_cajado_marulho",
]
DECK_B = [
    "gwent_unidade_herdeiro_portao",
    "chefe_vigia_cinzento",
    "arma_lanca_fornalha",
    "arma_martelo_fornalha",
    "arma_cajado_marulho",
    "gwent_especial_egide",
    "arma_lanca_fornalha",
    "arma_martelo_fornalha",
]


def main() -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="soulsbo-card-engine-v2-match-") as temp_dir:
        db_path = Path(temp_dir) / "card-engine-v2-alpha-match.sqlite3"
        repository = SQLiteMatchRepository(db_path)
        catalog = AlphaCatalog()
        controller = AlphaMatchController(repository, catalog)
        controller.create_match(
            match_id=MATCH_ID,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: DECK_A, PLAYER_B: DECK_B},
        )

        def record(label: str, player_id: str, receipt: Any) -> Any:
            result = receipt.result
            actions.append(
                {
                    "step": len(actions) + 1,
                    "label": label,
                    "player_id": player_id,
                    "outcome": result.get("outcome"),
                    "reason_code": result.get("reason_code"),
                    "target_results": result.get("target_results", []),
                    "costs": result.get("costs", {}),
                    "state_revision_after": repository.get_match(MATCH_ID)["state_revision"],
                    "replayed": receipt.replayed,
                }
            )
            return receipt

        def hand_instance(player_id: str, card_id: str) -> str:
            view = controller.view(MATCH_ID)
            candidates = [
                item["instance_id"]
                for item in view["players"][player_id]["hand"]
                if item["card_id"] == card_id
            ]
            if not candidates:
                raise RuntimeError(f"Card {card_id} is not in player {player_id}'s hand")
            return candidates[0]

        def play_unit(player_id: str, card_id: str, label: str | None = None) -> None:
            instance_id = hand_instance(player_id, card_id)
            receipt = controller.play_unit(
                MATCH_ID,
                actor_player_id=player_id,
                instance_id=instance_id,
            )
            record(label or f"play_unit:{card_id}", player_id, receipt)

        def play_targeted_special(
            player_id: str,
            card_id: str,
            *,
            target_name: str,
            row: str | None = None,
        ) -> None:
            source_id = hand_instance(player_id, card_id)
            offer = controller.target_offer(
                MATCH_ID,
                actor_player_id=player_id,
                source_instance_id=source_id,
                selected_row=row,
            )
            matches = [
                item["target_instance_id"]
                for item in offer["candidates"]
                if item["display_name"] == target_name
            ]
            if not matches:
                available = [item["display_name"] for item in offer["candidates"]]
                raise RuntimeError(f"Target {target_name!r} not offered; available={available}")
            receipt = controller.play_special(
                MATCH_ID,
                actor_player_id=player_id,
                source_instance_id=source_id,
                selected_row=row,
                selection={"mode": "manual_single", "target_instance_id": matches[0]},
                expected_revision=offer["state_revision"],
            )
            record(f"{card_id} -> {target_name}", player_id, receipt)

        def play_row_special(player_id: str, card_id: str, row: str, label: str) -> None:
            source_id = hand_instance(player_id, card_id)
            receipt = controller.play_special(
                MATCH_ID,
                actor_player_id=player_id,
                source_instance_id=source_id,
                selected_row=row,
            )
            record(label, player_id, receipt)

        def pass_turn(player_id: str) -> None:
            receipt = controller.pass_turn(MATCH_ID, actor_player_id=player_id)
            record("pass_round", player_id, receipt)

        # Round 1: weather + Frost lower the enemy's effective power;
        # Execution removes Godwyn and triggers Vengeance on the survivor.
        play_unit(PLAYER_A, "arma_lanca_fornalha", "A plays Lanceiro")
        play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao", "B plays Godwyn (Vingança)")
        play_unit(PLAYER_A, "gwent_v75_ordem_veterano_juramento", "A plays Veterano and buffs the weakest ally")
        play_unit(PLAYER_B, "chefe_vigia_cinzento", "B plays Cavaleiro de Leyndell")
        play_row_special(PLAYER_A, "gwent_especial_tempestade", "melee", "A applies Tempestade to melee")
        pass_turn(PLAYER_B)
        play_row_special(PLAYER_A, "elden_especial_geada", "melee", "A applies Frost to enemy melee units")
        play_targeted_special(
            PLAYER_A,
            "gwent_especial_execucao",
            row="melee",
            target_name="Godwyn, o Dourado",
        )
        play_targeted_special(
            PLAYER_A,
            "gwent_especial_egide",
            target_name="Lanceiro da Árvore Áurea",
        )
        pass_turn(PLAYER_A)

        # Round 2: B wins with a six-power unit.
        play_unit(PLAYER_B, "arma_martelo_fornalha", "B plays Ferreiro de Volcano Manor")
        pass_turn(PLAYER_A)
        pass_turn(PLAYER_B)

        # Round 3: A wins the decider, 2-1.
        play_unit(PLAYER_A, "arma_martelo_fornalha", "A plays Ferreiro de Volcano Manor")
        pass_turn(PLAYER_B)
        pass_turn(PLAYER_A)

        final_view = controller.view(MATCH_ID)
        events = repository.get_events(MATCH_ID)
        event_counts = Counter(event["kind"] for event in events)
        integrity = repository.verify_integrity()
        report = {
            "scenario": "isolated_best_of_three_alpha_match",
            "match_id": MATCH_ID,
            "catalog_release": catalog.definition_manifest(),
            "players": {PLAYER_A: "Player A", PLAYER_B: "Player B"},
            "status": final_view["status"],
            "winner_player_id": final_view["match_winner_player_id"],
            "round_wins": final_view["round_wins"],
            "round_history": final_view["round_history"],
            "round_one_event_proof": {
                "weather_applied": event_counts.get("weather_applied", 0),
                "status_applied": event_counts.get("status_applied", 0),
                "unit_removed": event_counts.get("unit_removed", 0),
                "vengeance_bonus_applied": event_counts.get("vengeance_bonus_applied", 0),
                "protection_grant_applied": event_counts.get("protection_grant_applied", 0),
            },
            "actions": actions,
            "event_count": len(events),
            "event_kind_counts": dict(sorted(event_counts.items())),
            "final_state_revision": final_view["state_revision"],
            "sqlite_integrity": integrity,
            "scope_notes": [
                "Uses the explicit 10-card alpha allowlist, not the full production catalog.",
                "Runs in a disposable SQLite database created by this script.",
                "Does not connect to Discord, HTTP, frontend, or the published database.",
                "No production migration or legacy-engine replacement is performed.",
            ],
        }
        if integrity.get("ok") is not True:
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
        if final_view["status"] != "finished" or final_view["match_winner_player_id"] != PLAYER_A:
            raise RuntimeError(f"Playable match did not finish with expected winner: {final_view}")
        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, help="Optional path to save the JSON result")
    args = parser.parse_args()
    result = main()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
