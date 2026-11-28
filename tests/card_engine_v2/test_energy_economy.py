from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog
from sistemas.card_engine_v2.errors import InvalidMatchState, InvalidOperation
from sistemas.card_engine_v2.match import AlphaMatchController
from sistemas.card_engine_v2.repository import HandlerResult, SQLiteMatchRepository
from sistemas.card_engine_v2.zones import transition_instance_zone

PLAYER_A = "1001"
PLAYER_B = "2002"
UNIT = "luterano_anjo"
SPECIAL = "gwent_especial_tempestade"
LEADER = "comandante_fornalha"


class EnergyEconomyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(__file__).resolve().parents[2]
        self.ruleset_path = self.root / "data/card_game/card-engine-v2-alpha-ruleset.v0.5.json"
        self.cost_schedule_path = self.root / "data/card_game/card-engine-v2-alpha-energy-cost-schedule.v0.1.json"
        self.repository = SQLiteMatchRepository(Path(self.temp.name) / "energy.sqlite3")
        self.catalog = AlphaCatalog()
        self.controller = AlphaMatchController(self.repository, self.catalog)
        deck = [UNIT] * 12
        self.controller.create_match(
            match_id=202611280241,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck, PLAYER_B: deck},
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def view(self, match_id: int = 202611280241) -> dict:
        return self.controller.view(match_id)

    def events(self, match_id: int = 202611280241) -> list[dict]:
        return self.repository.get_events(match_id)

    def _runtime_fixture(self, match_id: int, payload: dict, mutator) -> None:
        state = self.repository.get_match(match_id)
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "energy-economy-test-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_energy_fixture",
            "payload": payload,
        }

        def handler(working: dict, body: dict) -> HandlerResult:
            runtime = body["_runtime_context"]
            mutator(working, runtime)
            event = {
                "event_id": str(uuid.uuid4()),
                "kind": "test_energy_fixture_installed",
                "effect_scope": "system",
                "source_effect_id": None,
                "source_instance_id": None,
                "target_instance_ids": [],
                "caused_by_event_ids": [],
                "payload": payload,
            }
            return HandlerResult(outcome="applied", state=working, events=[event], runtime_state=runtime)

        receipt = self.repository.execute_operation(match_id, request, handler)
        self.assertEqual(receipt.result["outcome"], "applied")

    def _catalog_with_costs(self, card_costs: dict[str, int] | None = None, leader_costs: dict[str, int] | None = None) -> AlphaCatalog:
        data = json.loads(self.ruleset_path.read_text(encoding="utf-8"))
        schedule = json.loads(self.cost_schedule_path.read_text(encoding="utf-8"))
        card_map = dict(data["energy_economy"]["card_energy_cost_by_card_id"])
        leader_map = dict(data["energy_economy"]["leader_activation_energy_cost_by_leader_id"])
        card_map.update(card_costs or {})
        leader_map.update(leader_costs or {})
        data["energy_economy"]["card_energy_cost_by_card_id"] = card_map
        data["energy_economy"]["leader_activation_energy_cost_by_leader_id"] = leader_map
        for card_id, cost in (card_costs or {}).items():
            schedule["card_energy_cost_by_card_id"][card_id]["energy_cost"] = cost
        for leader_id, cost in (leader_costs or {}).items():
            schedule["leader_activation_energy_cost_by_leader_id"][leader_id]["energy_cost"] = cost
        ruleset_path = Path(self.temp.name) / f"ruleset-{uuid.uuid4().hex}.json"
        schedule_path = Path(self.temp.name) / f"schedule-{uuid.uuid4().hex}.json"
        ruleset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        schedule_path.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
        return AlphaCatalog(ruleset_path=ruleset_path, cost_schedule_path=schedule_path)

    def test_first_player_starts_with_one_energy_and_other_player_gains_on_turn_start(self) -> None:
        view = self.view()
        self.assertEqual(view["current_player_id"], PLAYER_A)
        self.assertEqual(view["players"][PLAYER_A]["energy"], 1)
        self.assertEqual(view["players"][PLAYER_B]["energy"], 0)
        self.assertEqual(view["players"][PLAYER_A]["maximum_energy"], 5)

        state = self.repository.get_match(202611280241)
        a_card = state["players"][PLAYER_A]["zones"]["hand"][0]
        receipt = self.controller.play_unit(
            202611280241, actor_player_id=PLAYER_A, instance_id=a_card
        )
        self.assertEqual(receipt.result["outcome"], "applied")
        view = self.view()
        self.assertEqual(view["current_player_id"], PLAYER_B)
        self.assertEqual(view["players"][PLAYER_B]["energy"], 1)
        gained = [event for event in self.events() if event["kind"] == "player_energy_gained"]
        self.assertEqual(gained[-1]["payload"]["player_id"], PLAYER_B)
        self.assertEqual(gained[-1]["payload"]["energy_gained"], 1)

    def test_energy_persists_across_rounds_and_caps_at_five(self) -> None:
        state = self.repository.get_match(202611280241)
        a_card = state["players"][PLAYER_A]["zones"]["hand"][0]
        b_card = state["players"][PLAYER_B]["zones"]["hand"][0]
        self.controller.play_unit(202611280241, actor_player_id=PLAYER_A, instance_id=a_card)
        self.controller.play_unit(202611280241, actor_player_id=PLAYER_B, instance_id=b_card)
        self.assertEqual(self.view()["players"][PLAYER_A]["energy"], 1)
        self.assertEqual(self.view()["players"][PLAYER_B]["energy"], 0)

        self.controller.pass_turn(202611280241, actor_player_id=PLAYER_A)
        self.controller.pass_turn(202611280241, actor_player_id=PLAYER_B)
        view = self.view()
        self.assertEqual(view["round_number"], 2)
        self.assertEqual(view["current_player_id"], PLAYER_B)
        self.assertEqual(view["players"][PLAYER_A]["energy"], 1)
        self.assertEqual(view["players"][PLAYER_B]["energy"], 2)

        def cap_fixture(_state: dict, runtime: dict) -> None:
            runtime["current_player_id"] = PLAYER_B
            runtime["passed_player_ids"] = []
            runtime["energy_by_player"][PLAYER_A] = 5

        self._runtime_fixture(202611280241, {"energy": 5, "current_player": PLAYER_A}, cap_fixture)
        self.controller.pass_turn(202611280241, actor_player_id=PLAYER_B)
        self.assertEqual(self.view()["players"][PLAYER_A]["energy"], 5)
        capped = [
            event for event in self.events()
            if event["kind"] == "player_energy_gained"
            and event["payload"]["player_id"] == PLAYER_A
            and event["payload"]["gain_capped"]
        ]
        self.assertTrue(capped, "the player at the cap should emit a capped energy-gain event")

    def test_all_alpha_cards_and_leaders_have_explicit_provisional_costs(self) -> None:
        self.assertEqual(set(self.catalog.card_energy_cost_by_id), self.catalog.allowlist)
        self.assertEqual(set(self.catalog.leader_energy_cost_by_id), set(self.catalog.leader_registry))
        self.assertTrue(all(1 <= cost <= 5 for cost in self.catalog.card_energy_cost_by_id.values()))
        self.assertTrue(all(1 <= cost <= 5 for cost in self.catalog.leader_energy_cost_by_id.values()))
        self.assertFalse(self.catalog.activated_abilities)
        self.assertFalse(self.catalog.ability_energy_cost_by_id)

    def test_every_provisional_price_is_accepted_at_exact_balance_and_rejected_below_it(self) -> None:
        runtime = {"energy_by_player": {PLAYER_A: 5}}
        for card_id, cost in sorted(self.catalog.card_energy_cost_by_id.items()):
            with self.subTest(kind="card", item_id=card_id, cost=cost):
                runtime["energy_by_player"][PLAYER_A] = cost
                self.assertEqual(self.controller._card_energy_check(runtime, PLAYER_A, card_id), (True, cost, cost, None))
                runtime["energy_by_player"][PLAYER_A] = cost - 1
                self.assertEqual(self.controller._card_energy_check(runtime, PLAYER_A, card_id), (False, cost, cost - 1, "insufficient_energy"))

        for leader_id, cost in sorted(self.catalog.leader_energy_cost_by_id.items()):
            with self.subTest(kind="leader", item_id=leader_id, cost=cost):
                runtime["energy_by_player"][PLAYER_A] = cost
                self.assertEqual(self.controller._leader_energy_check(runtime, PLAYER_A, leader_id), (True, cost, cost, None))
                runtime["energy_by_player"][PLAYER_A] = cost - 1
                self.assertEqual(self.controller._leader_energy_check(runtime, PLAYER_A, leader_id), (False, cost, cost - 1, "insufficient_energy"))

    def test_card_cost_is_stable_when_legacy_deck_cost_and_rarity_change(self) -> None:
        card_id = UNIT
        original = self.catalog.energy_cost_for_card(card_id)
        self.catalog._metadata[card_id]["legacy_deck_cost"] = 999
        self.catalog._metadata[card_id]["legacy_rarity"] = "Mítica"
        self.assertEqual(self.catalog.energy_cost_for_card(card_id), original)

    def test_configured_card_cost_rejects_insufficient_energy_without_consuming_card(self) -> None:
        catalog = self._catalog_with_costs({UNIT: 2})
        repository = SQLiteMatchRepository(Path(self.temp.name) / "priced-card.sqlite3")
        controller = AlphaMatchController(repository, catalog)
        match_id = 202611280242
        deck = [UNIT] * 10
        controller.create_match(
            match_id=match_id,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck, PLAYER_B: deck},
        )
        state = repository.get_match(match_id)
        instance_id = state["players"][PLAYER_A]["zones"]["hand"][0]
        before_revision = state["state_revision"]
        receipt = controller.play_unit(match_id, actor_player_id=PLAYER_A, instance_id=instance_id)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "insufficient_energy")
        after = repository.get_match(match_id)
        self.assertEqual(after["state_revision"], before_revision)
        self.assertIn(instance_id, after["players"][PLAYER_A]["zones"]["hand"])
        self.assertEqual(controller.view(match_id)["players"][PLAYER_A]["energy"], 1)

    def test_explicit_card_cost_is_charged_and_traced_after_successful_play(self) -> None:
        catalog = self._catalog_with_costs({UNIT: 2})
        repository = SQLiteMatchRepository(Path(self.temp.name) / "priced-card-success.sqlite3")
        controller = AlphaMatchController(repository, catalog)
        match_id = 202611280243
        deck = [UNIT] * 10
        controller.create_match(
            match_id=match_id,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck, PLAYER_B: deck},
        )
        self._runtime_fixture_for(repository, match_id, PLAYER_A, 2)
        instance_id = repository.get_match(match_id)["players"][PLAYER_A]["zones"]["hand"][0]
        original_revision = repository.get_match(match_id)["state_revision"]
        operation_id = str(uuid.uuid4())
        receipt = controller.play_unit(
            match_id, actor_player_id=PLAYER_A, instance_id=instance_id,
            expected_revision=original_revision, operation_id=operation_id,
        )
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual(receipt.result["costs"]["energy_spent"], 2)
        self.assertTrue(receipt.result["costs"]["energy_cost_configured"])
        self.assertEqual(receipt.result["costs"]["energy_remaining"], 0)
        self.assertEqual(controller.view(match_id)["players"][PLAYER_A]["energy"], 0)
        payment_events = [event for event in repository.get_events(match_id) if event["kind"] == "player_energy_spent"]
        self.assertEqual(len(payment_events), 1)
        payment = payment_events[0]
        self.assertEqual(payment["payload"]["energy_spent"], 2)
        self.assertEqual(payment["payload"]["action"], "play_unit")
        replay = controller.play_unit(
            match_id, actor_player_id=PLAYER_A, instance_id=instance_id,
            expected_revision=original_revision, operation_id=operation_id,
        )
        self.assertTrue(replay.replayed)
        self.assertEqual(len([event for event in repository.get_events(match_id) if event["kind"] == "player_energy_spent"]), 1)

    def test_runtime_energy_balance_survives_repository_reopen(self) -> None:
        path = self.repository.database_path
        state = self.repository.get_match(202611280241)
        instance_id = state["players"][PLAYER_A]["zones"]["hand"][0]
        self.controller.play_unit(202611280241, actor_player_id=PLAYER_A, instance_id=instance_id)
        reopened_repository = SQLiteMatchRepository(path)
        reopened_controller = AlphaMatchController(reopened_repository, AlphaCatalog())
        view = reopened_controller.view(202611280241)
        self.assertEqual(view["players"][PLAYER_A]["energy"], 0)
        self.assertEqual(view["players"][PLAYER_B]["energy"], 1)
        self.assertEqual(view["players"][PLAYER_A]["energy_turns_started"], 1)
        self.assertEqual(view["players"][PLAYER_B]["energy_turns_started"], 1)

    def test_explicit_special_cost_is_checked_and_spent(self) -> None:
        catalog = self._catalog_with_costs({SPECIAL: 2})
        repository = SQLiteMatchRepository(Path(self.temp.name) / "priced-special.sqlite3")
        controller = AlphaMatchController(repository, catalog)
        match_id = 202611280244
        deck_a = [SPECIAL, UNIT, UNIT, UNIT, UNIT, UNIT]
        deck_b = [UNIT] * 6
        controller.create_match(
            match_id=match_id,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck_a, PLAYER_B: deck_b},
        )
        state = repository.get_match(match_id)
        special_id = state["players"][PLAYER_A]["zones"]["hand"][0]
        rejected = controller.play_special(
            match_id, actor_player_id=PLAYER_A, source_instance_id=special_id, selected_row="melee"
        ).result
        self.assertEqual(rejected["outcome"], "rejected")
        self.assertEqual(rejected["reason_code"], "insufficient_energy")
        self._runtime_fixture_for(repository, match_id, PLAYER_A, 2)
        paid = controller.play_special(
            match_id, actor_player_id=PLAYER_A, source_instance_id=special_id, selected_row="melee"
        ).result
        self.assertIn(paid["outcome"], ("applied", "partial", "consumed_no_effect"))
        self.assertEqual(paid["costs"]["energy_spent"], 2)
        self.assertEqual(controller.view(match_id)["players"][PLAYER_A]["energy"], 0)
        payment = next(event for event in repository.get_events(match_id) if event["kind"] == "player_energy_spent")
        self.assertEqual(payment["payload"]["action"], "play_special")

    def test_explicit_leader_cost_is_checked_and_spent(self) -> None:
        catalog = self._catalog_with_costs({}, {LEADER: 2})
        repository = SQLiteMatchRepository(Path(self.temp.name) / "priced-leader.sqlite3")
        controller = AlphaMatchController(repository, catalog)
        match_id = 202611280245
        deck = [UNIT] * 8
        controller.create_match(
            match_id=match_id,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck, PLAYER_B: deck},
            leaders={PLAYER_A: LEADER},
        )
        state = repository.get_match(match_id)
        board_instance = state["players"][PLAYER_A]["zones"]["hand"][0]
        transition_instance_zone(state, board_instance, "board", target_row="melee")
        self._install_state_for_test(repository, match_id, state)

        rejected = controller.activate_leader(match_id, actor_player_id=PLAYER_A).result
        self.assertEqual(rejected["outcome"], "rejected")
        self.assertEqual(rejected["reason_code"], "insufficient_energy")
        self.assertFalse(repository.get_match(match_id)["players"][PLAYER_A]["leader_used"])

        self._runtime_fixture_for(repository, match_id, PLAYER_A, 2)
        paid = controller.activate_leader(match_id, actor_player_id=PLAYER_A).result
        self.assertEqual(paid["outcome"], "applied")
        self.assertEqual(paid["costs"]["energy_spent"], 2)
        self.assertEqual(controller.view(match_id)["players"][PLAYER_A]["energy"], 0)
        payment = next(event for event in repository.get_events(match_id) if event["kind"] == "player_energy_spent")
        self.assertEqual(payment["payload"]["action"], "activate_leader")

    @staticmethod
    def _runtime_fixture_for(repository, match_id: int, player_id: str, energy: int) -> None:
        state = repository.get_match(match_id)
        runtime = repository.get_match_runtime(match_id)
        runtime["energy_by_player"][player_id] = energy
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "energy-payment-test-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_energy_balance",
            "payload": {"player_id": player_id, "energy": energy},
        }
        event = {
            "event_id": str(uuid.uuid4()),
            "kind": "test_energy_balance_installed",
            "effect_scope": "system",
            "source_effect_id": None,
            "source_instance_id": None,
            "target_instance_ids": [],
            "caused_by_event_ids": [],
            "payload": {"player_id": player_id, "energy": energy},
        }
        repository.execute_operation(
            match_id,
            request,
            lambda working, _body: HandlerResult(
                outcome="applied", state=working, runtime_state=runtime, events=[event]
            ),
        )

    @staticmethod
    def _install_state_for_test(repository, match_id: int, state: dict) -> None:
        runtime = repository.get_match_runtime(match_id)
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "energy-board-test-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_leader_board",
            "payload": {},
        }
        event = {
            "event_id": str(uuid.uuid4()),
            "kind": "test_leader_board_installed",
            "effect_scope": "system",
            "source_effect_id": None,
            "source_instance_id": None,
            "target_instance_ids": [],
            "caused_by_event_ids": [],
            "payload": {},
        }
        repository.execute_operation(
            match_id,
            request,
            lambda _working, _body: HandlerResult(
                outcome="applied", state=state, runtime_state=runtime, events=[event]
            ),
        )

    def test_catalog_rejects_unknown_card_ids_and_boolean_costs(self) -> None:
        data = json.loads(self.ruleset_path.read_text(encoding="utf-8"))
        data["energy_economy"]["card_energy_cost_by_card_id"] = {"unknown-card": 1}
        path = Path(self.temp.name) / "unknown-card-cost.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(InvalidOperation):
            AlphaCatalog(ruleset_path=path)

        data["energy_economy"]["card_energy_cost_by_card_id"] = {UNIT: True}
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(InvalidOperation):
            AlphaCatalog(ruleset_path=path)

    def test_runtime_rejects_energy_above_cap(self) -> None:
        state = self.repository.get_match(202611280241)
        runtime = self.repository.get_match_runtime(202611280241)
        runtime["energy_by_player"][PLAYER_A] = 6
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "invalid-energy-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.invalid_energy_balance",
            "payload": {},
        }
        event = {
            "event_id": str(uuid.uuid4()),
            "kind": "test_invalid_energy_fixture",
            "effect_scope": "system",
            "source_effect_id": None,
            "source_instance_id": None,
            "target_instance_ids": [],
            "caused_by_event_ids": [],
            "payload": {},
        }
        with self.assertRaises(InvalidMatchState):
            self.repository.execute_operation(
                202611280241,
                request,
                lambda working, _body: HandlerResult(
                    outcome="applied", state=working, runtime_state=runtime, events=[event]
                ),
            )
        self.assertEqual(self.view()["players"][PLAYER_A]["energy"], 1)


if __name__ == "__main__":
    unittest.main()
