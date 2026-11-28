from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog
from sistemas.card_engine_v2.errors import InvalidOperation
from sistemas.card_engine_v2.match import AlphaMatchController
from sistemas.card_engine_v2.repository import HandlerResult, SQLiteMatchRepository
from sistemas.card_engine_v2.zones import transition_instance_zone

PLAYER_A = "1001"
PLAYER_B = "2002"
CARD = "luterano_anjo"
ABILITY_ID = "ability.alpha_test_rally"


def _ability_registry() -> dict:
    return {
        "artifact_type": "soulsbo_card_engine_v2_alpha_activated_ability_registry",
        "version": "0.1",
        "status": "alpha_test_only_not_a_published_registry",
        "supported_action_types": [
            "unit.grant_bonus",
            "unit.grant_protection",
            "unit.remove",
            "unit.move",
        ],
        "abilities": [
            {
                "ability_id": ABILITY_ID,
                "source_card_ids": [CARD],
                "action_type": "unit.grant_bonus",
                "target_policy": {
                    "policy_id": "policy.alpha_test.rally_allies",
                    "selection_mode": "manual_single",
                    "target_side": "allies",
                    "source_zone": "board",
                    "row_scope": "global",
                    "row_basis": "current_row",
                    "eligibility_metric": "none",
                    "display_metric": "base_power",
                    "sort_metric": "none",
                    "direction": "none",
                    "tie_breaker": "zone_order",
                    "minimum_targets": 1,
                    "maximum_targets": 1,
                    "on_no_target": "reject",
                    "predicates": [{"predicate_id": "instance.not_source", "params": {}}],
                    "secondary_selection": "none",
                },
                "params": {
                    "bonus_amount": 1,
                    "bonus_expires_on": "round_close",
                    "bonus_clamp_policy_id": "balance.alpha.raw_grants.v1",
                },
                "uses_per_match": 1,
            }
        ],
        "notes": ["Synthetic test fixture only; not a live card ability."],
    }


class ActivatedAbilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(__file__).resolve().parents[2]
        self.repository = SQLiteMatchRepository(Path(self.temp.name) / "activated-abilities.sqlite3")
        self.catalog = self._catalog_with_test_ability(cost=1)
        self.controller = AlphaMatchController(self.repository, self.catalog)
        self.match_id = 202611280251
        deck = [CARD] * 12
        self.controller.create_match(
            match_id=self.match_id,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck, PLAYER_B: deck},
        )
        self.source_id, self.target_id = self._install_two_allies_on_board()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _catalog_with_test_ability(self, *, cost: int) -> AlphaCatalog:
        ruleset = json.loads((self.root / "data/card_game/card-engine-v2-alpha-ruleset.v0.5.json").read_text(encoding="utf-8"))
        schedule = json.loads((self.root / "data/card_game/card-engine-v2-alpha-energy-cost-schedule.v0.1.json").read_text(encoding="utf-8"))
        registry = _ability_registry()
        ruleset["energy_economy"]["ability_activation_energy_cost_by_ability_id"] = {ABILITY_ID: cost}
        schedule["ability_activation_energy_cost_by_ability_id"] = {ABILITY_ID: cost}
        registry_path = Path(self.temp.name) / "abilities.json"
        ruleset_path = Path(self.temp.name) / "ruleset.json"
        schedule_path = Path(self.temp.name) / "schedule.json"
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
        ruleset_path.write_text(json.dumps(ruleset, ensure_ascii=False, indent=2), encoding="utf-8")
        schedule_path.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
        return AlphaCatalog(
            ruleset_path=ruleset_path,
            cost_schedule_path=schedule_path,
            activated_abilities_path=registry_path,
        )

    def _install_two_allies_on_board(self) -> tuple[str, str]:
        state = self.repository.get_match(self.match_id)
        cards = state["players"][PLAYER_A]["zones"]["hand"][:2]
        source_id, target_id = cards
        transition_instance_zone(state, source_id, "board", target_row="melee")
        transition_instance_zone(state, target_id, "board", target_row="ranged")
        runtime = self.repository.get_match_runtime(self.match_id)
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "activated-ability-test-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_ability_source_and_target",
            "payload": {"source_instance_id": source_id, "target_instance_id": target_id},
        }
        event = {
            "event_id": str(uuid.uuid4()),
            "kind": "test_ability_source_and_target_installed",
            "effect_scope": "system",
            "source_effect_id": None,
            "source_instance_id": source_id,
            "target_instance_ids": [source_id, target_id],
            "caused_by_event_ids": [],
            "payload": {"source_card_id": CARD, "target_card_id": CARD},
        }
        self.repository.execute_operation(
            self.match_id,
            request,
            lambda _working, _body: HandlerResult(
                outcome="applied", state=state, runtime_state=runtime, events=[event]
            ),
        )
        return source_id, target_id

    def test_registered_ability_uses_server_offer_costs_turn_and_once_limit(self) -> None:
        offer = self.controller.card_ability_target_offer(
            self.match_id,
            actor_player_id=PLAYER_A,
            source_instance_id=self.source_id,
            ability_id=ABILITY_ID,
        )
        self.assertEqual([item["target_instance_id"] for item in offer["candidates"]], [self.target_id])
        before_revision = self.controller.view(self.match_id)["state_revision"]
        operation_id = str(uuid.uuid4())
        receipt = self.controller.activate_card_ability(
            self.match_id,
            actor_player_id=PLAYER_A,
            source_instance_id=self.source_id,
            ability_id=ABILITY_ID,
            selection={"mode": "manual_single", "target_instance_id": self.target_id},
            expected_revision=before_revision,
            operation_id=operation_id,
        )
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual(receipt.result["costs"]["energy_spent"], 1)
        self.assertTrue(receipt.result["costs"]["turn_consumed"])
        self.assertEqual(self.controller.view(self.match_id)["players"][PLAYER_A]["energy"], 0)
        state = self.repository.get_match(self.match_id)
        self.assertEqual(len(state["instances"][self.target_id]["state"]["bonus_grants"]), 1)

        events = self.repository.get_events(self.match_id)
        self.assertEqual(len([item for item in events if item["kind"] == "card_ability_activated"]), 1)
        self.assertEqual(len([item for item in events if item["kind"] == "player_energy_spent"]), 1)
        replay = self.controller.activate_card_ability(
            self.match_id,
            actor_player_id=PLAYER_A,
            source_instance_id=self.source_id,
            ability_id=ABILITY_ID,
            selection={"mode": "manual_single", "target_instance_id": self.target_id},
            expected_revision=before_revision,
            operation_id=operation_id,
        )
        self.assertTrue(replay.replayed)

        # Give player B a legal action to return the turn to A.
        b_card = self.repository.get_match(self.match_id)["players"][PLAYER_B]["zones"]["hand"][0]
        b_play = self.controller.play_unit(self.match_id, actor_player_id=PLAYER_B, instance_id=b_card)
        self.assertEqual(b_play.result["outcome"], "applied")
        with self.assertRaisesRegex(InvalidOperation, "manual_ability_already_used"):
            self.controller.card_ability_target_offer(
                self.match_id,
                actor_player_id=PLAYER_A,
                source_instance_id=self.source_id,
                ability_id=ABILITY_ID,
            )
        retry = self.controller.activate_card_ability(
            self.match_id,
            actor_player_id=PLAYER_A,
            source_instance_id=self.source_id,
            ability_id=ABILITY_ID,
            selection={"mode": "manual_single", "target_instance_id": self.target_id},
        )
        self.assertEqual(retry.result["outcome"], "rejected")
        self.assertEqual(retry.result["reason_code"], "manual_ability_already_used")
        self.assertEqual(len([item for item in self.repository.get_events(self.match_id) if item["kind"] == "player_energy_spent" and item["payload"].get("source_id") == ABILITY_ID]), 1)

    def test_insufficient_energy_rejects_without_mutation(self) -> None:
        catalog = self._catalog_with_test_ability(cost=2)
        repository = SQLiteMatchRepository(Path(self.temp.name) / "insufficient.sqlite3")
        controller = AlphaMatchController(repository, catalog)
        match_id = 202611280252
        deck = [CARD] * 12
        controller.create_match(match_id=match_id, player_ids=[PLAYER_A, PLAYER_B], decks={PLAYER_A: deck, PLAYER_B: deck})
        state = repository.get_match(match_id)
        source_id, target_id = state["players"][PLAYER_A]["zones"]["hand"][:2]
        transition_instance_zone(state, source_id, "board", target_row="melee")
        transition_instance_zone(state, target_id, "board", target_row="ranged")
        runtime = repository.get_match_runtime(match_id)
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "ability-energy-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_board",
            "payload": {},
        }
        event = {
            "event_id": str(uuid.uuid4()), "kind": "test_board_installed", "effect_scope": "system",
            "source_effect_id": None, "source_instance_id": None, "target_instance_ids": [source_id, target_id],
            "caused_by_event_ids": [], "payload": {},
        }
        repository.execute_operation(match_id, request, lambda _working, _body: HandlerResult(outcome="applied", state=state, runtime_state=runtime, events=[event]))
        revision = repository.get_match(match_id)["state_revision"]
        receipt = controller.activate_card_ability(
            match_id,
            actor_player_id=PLAYER_A,
            source_instance_id=source_id,
            ability_id=ABILITY_ID,
            selection={"mode": "manual_single", "target_instance_id": target_id},
            expected_revision=revision,
        )
        with self.assertRaisesRegex(InvalidOperation, "insufficient_energy"):
            controller.card_ability_target_offer(
                match_id,
                actor_player_id=PLAYER_A,
                source_instance_id=source_id,
                ability_id=ABILITY_ID,
            )
        self.assertEqual(controller.view(match_id)["players"][PLAYER_A]["energy"], 1)
        receipt = controller.activate_card_ability(
            match_id,
            actor_player_id=PLAYER_A,
            source_instance_id=source_id,
            ability_id=ABILITY_ID,
            selection={"mode": "manual_single", "target_instance_id": target_id},
            expected_revision=revision,
        )
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "insufficient_energy")
        self.assertEqual(repository.get_match(match_id)["state_revision"], revision)
        self.assertEqual(len(repository.get_events(match_id)), 1)
        self.assertEqual(controller.view(match_id)["players"][PLAYER_A]["energy"], 1)

    def test_default_empty_registry_rejects_undeclared_manual_abilities(self) -> None:
        default_catalog = AlphaCatalog()
        repository = SQLiteMatchRepository(Path(self.temp.name) / "empty-registry.sqlite3")
        controller = AlphaMatchController(repository, default_catalog)
        match_id = 202611280253
        deck = [CARD] * 8
        controller.create_match(match_id=match_id, player_ids=[PLAYER_A, PLAYER_B], decks={PLAYER_A: deck, PLAYER_B: deck})
        source_id = repository.get_match(match_id)["players"][PLAYER_A]["zones"]["hand"][0]
        state = repository.get_match(match_id)
        transition_instance_zone(state, source_id, "board", target_row="melee")
        runtime = repository.get_match_runtime(match_id)
        request = {
            "operation_id": str(uuid.uuid4()), "actor": {"type": "system", "system_id": "empty-registry-fixture"},
            "expected_revision": state["state_revision"], "action_type": "test.install_source", "payload": {},
        }
        event = {
            "event_id": str(uuid.uuid4()), "kind": "test_source_installed", "effect_scope": "system",
            "source_effect_id": None, "source_instance_id": None, "target_instance_ids": [source_id],
            "caused_by_event_ids": [], "payload": {},
        }
        repository.execute_operation(match_id, request, lambda _working, _body: HandlerResult(outcome="applied", state=state, runtime_state=runtime, events=[event]))
        receipt = controller.activate_card_ability(
            match_id, actor_player_id=PLAYER_A, source_instance_id=source_id, ability_id=ABILITY_ID,
        )
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "manual_ability_not_registered")
        self.assertEqual(controller.view(match_id)["players"][PLAYER_A]["energy"], 1)


if __name__ == "__main__":
    unittest.main()
