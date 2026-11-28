from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog
from sistemas.card_engine_v2.match import AlphaMatchController
from sistemas.card_engine_v2.repository import HandlerResult, SQLiteMatchRepository
from sistemas.card_engine_v2.zones import transition_instance_zone
from tests.card_engine_v2.support import mechanics_catalog

PLAYER_A = "1001"
PLAYER_B = "2002"
MATCH_ID = 202611280221
UNIT_CARD = "arma_lanca_fornalha"


class RuntimeDeckFatigueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repository = SQLiteMatchRepository(Path(self.temp.name) / "deck-fatigue.sqlite3")
        self.catalog = mechanics_catalog(self.temp.name)
        self.controller = AlphaMatchController(self.repository, self.catalog)
        deck = [UNIT_CARD] * 10
        self.controller.create_match(
            match_id=MATCH_ID,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck, PLAYER_B: deck},
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def view(self) -> dict:
        return self.controller.view(MATCH_ID)

    def first_hand_unit(self, player_id: str) -> str:
        state = self.repository.get_match(MATCH_ID)
        for instance_id in state["players"][player_id]["zones"]["hand"]:
            if state["instances"][instance_id]["definition_snapshot"]["kind"] == "unit":
                return instance_id
        raise AssertionError(f"player {player_id} has no unit in hand")

    def play(self, player_id: str):
        return self.controller.play_unit(
            MATCH_ID,
            actor_player_id=player_id,
            instance_id=self.first_hand_unit(player_id),
        )

    def pass_turn(self, player_id: str):
        return self.controller.pass_turn(MATCH_ID, actor_player_id=player_id)

    def _fixture_operation(self, action: str, mutator, payload: dict) -> None:
        state = self.repository.get_match(MATCH_ID)
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "deck-fatigue-test-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": action,
            "payload": payload,
        }

        def handler(working: dict, body: dict) -> HandlerResult:
            runtime = body["_runtime_context"]
            mutator(working, runtime)
            event = {
                "event_id": str(uuid.uuid4()),
                "kind": "test_fixture_updated",
                "effect_scope": "system",
                "source_effect_id": None,
                "source_instance_id": None,
                "target_instance_ids": [],
                "caused_by_event_ids": [],
                "payload": payload,
            }
            return HandlerResult(outcome="applied", state=working, events=[event], runtime_state=runtime)

        receipt = self.repository.execute_operation(MATCH_ID, request, handler)
        self.assertEqual(receipt.result["outcome"], "applied")

    def set_draw_pile_size(self, player_id: str, size: int) -> None:
        def mutator(state: dict, _runtime: dict) -> None:
            zone = state["players"][player_id]["zones"]["draw_pile"]
            if size < 0 or size > len(zone):
                raise AssertionError("invalid fixture draw-pile size")
            for instance_id in list(zone[size:]):
                transition_instance_zone(state, instance_id, "discard")

        self._fixture_operation(
            "test.set_draw_pile_size", mutator, {"player_id": player_id, "size": size}
        )

    def set_life(self, player_id: str, life: int) -> None:
        def mutator(_state: dict, runtime: dict) -> None:
            runtime["life_by_player"][player_id] = life

        self._fixture_operation(
            "test.set_player_life", mutator, {"player_id": player_id, "life": life}
        )

    def events(self) -> list[dict]:
        return self.repository.get_events(MATCH_ID)

    def test_default_setup_uses_official_four_card_initial_hand(self) -> None:
        view = self.view()
        self.assertEqual(len(view["players"][PLAYER_A]["hand"]), 4)
        self.assertEqual(view["players"][PLAYER_A]["draw_pile_count"], 6)
        self.assertEqual(view["players"][PLAYER_B]["hand"].__len__(), 4)
        self.assertEqual(self.catalog.definition_manifest()["ruleset_release_id"], "alpha-test-only.ruleset.v0.5")
        self.assertEqual(view["players"][PLAYER_A]["deck_fatigue_count"], 0)

    def test_fatigue_increases_each_empty_deck_turn_with_independent_player_counters(self) -> None:
        self.set_draw_pile_size(PLAYER_A, 0)
        self.set_draw_pile_size(PLAYER_B, 0)

        # Each player receives one fatigue-exempt opening turn.
        self.play(PLAYER_A)
        self.assertEqual(self.view()["current_player_id"], PLAYER_B)
        self.play(PLAYER_B)
        self.assertEqual(self.view()["players"][PLAYER_A]["life"], 19)
        self.assertEqual(self.view()["players"][PLAYER_B]["life"], 20)

        # Their next turns apply one point; the following turns apply two.
        self.play(PLAYER_A)
        self.assertEqual(self.view()["players"][PLAYER_B]["life"], 19)
        self.play(PLAYER_B)
        self.assertEqual(self.view()["players"][PLAYER_A]["life"], 17)
        self.play(PLAYER_A)
        self.assertEqual(self.view()["players"][PLAYER_B]["life"], 17)

        view = self.view()
        self.assertEqual(view["deck_fatigue_count_by_player"], {PLAYER_A: 2, PLAYER_B: 2})
        fatigue_events = [event for event in self.events() if event["kind"] == "deck_fatigue_applied"]
        self.assertEqual(
            [(event["payload"]["player_id"], event["payload"]["damage"]) for event in fatigue_events],
            [(PLAYER_A, 1), (PLAYER_B, 1), (PLAYER_A, 2), (PLAYER_B, 2)],
        )
        self.assertTrue(all(event["effect_scope"] == "system" for event in fatigue_events))

    def test_nonempty_draw_pile_does_not_apply_fatigue(self) -> None:
        self.play(PLAYER_A)
        self.play(PLAYER_B)
        view = self.view()
        self.assertEqual(view["players"][PLAYER_A]["life"], 20)
        self.assertEqual(view["players"][PLAYER_B]["life"], 20)
        self.assertEqual(view["deck_fatigue_count_by_player"], {PLAYER_A: 0, PLAYER_B: 0})
        self.assertFalse(any(event["kind"] == "deck_fatigue_applied" for event in self.events()))

    def test_partial_round_draw_then_empty_deck_applies_one_fatigue_before_action(self) -> None:
        # B's opening turn is exempt. At the next round, one remaining card is
        # drawn from the two-card alpha draw request, then fatigue applies once.
        self.set_draw_pile_size(PLAYER_B, 1)
        self.pass_turn(PLAYER_A)
        self.assertEqual(self.view()["current_player_id"], PLAYER_B)
        self.pass_turn(PLAYER_B)

        view = self.view()
        self.assertEqual(view["round_number"], 2)
        self.assertEqual(view["current_player_id"], PLAYER_B)
        self.assertEqual(len(view["players"][PLAYER_B]["hand"]), 5)
        self.assertEqual(view["players"][PLAYER_B]["draw_pile_count"], 0)
        self.assertEqual(view["players"][PLAYER_B]["life"], 19)
        self.assertEqual(view["players"][PLAYER_B]["deck_fatigue_count"], 1)

        events = self.events()
        round_started_index = next(i for i, event in enumerate(events) if event["kind"] == "round_started")
        fatigue_index = next(i for i, event in enumerate(events) if event["kind"] == "deck_fatigue_applied")
        self.assertLess(round_started_index, fatigue_index)
        fatigue_events = [event for event in events if event["kind"] == "deck_fatigue_applied"]
        self.assertEqual(len(fatigue_events), 1)

    def test_lethal_fatigue_finishes_match_before_player_can_act(self) -> None:
        self.set_draw_pile_size(PLAYER_A, 0)
        self.set_life(PLAYER_A, 1)
        self.play(PLAYER_A)
        receipt = self.play(PLAYER_B)
        self.assertEqual(receipt.result["outcome"], "applied")

        view = self.view()
        self.assertEqual(view["status"], "finished")
        self.assertEqual(view["phase"], "finished")
        self.assertIsNone(view["current_player_id"])
        self.assertEqual(view["players"][PLAYER_A]["life"], 0)
        self.assertEqual(view["match_winner_player_id"], PLAYER_B)
        self.assertEqual(view["match_finish_reason"], "deck_fatigue")

        events = self.events()
        kinds = [event["kind"] for event in events]
        self.assertLess(kinds.index("deck_fatigue_applied"), kinds.index("player_damage_applied"))
        self.assertLess(kinds.index("player_damage_applied"), kinds.index("player_defeated"))
        self.assertLess(kinds.index("player_defeated"), kinds.index("match_finished"))
        damage_event = next(event for event in events if event["kind"] == "player_damage_applied")
        fatigue_event = next(event for event in events if event["kind"] == "deck_fatigue_applied")
        self.assertEqual(damage_event["caused_by_event_ids"], [fatigue_event["event_id"]])

        after = self.controller.play_unit(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            instance_id=self.first_hand_unit(PLAYER_A),
        )
        self.assertEqual(after.result["outcome"], "rejected")
        self.assertEqual(after.result["reason_code"], "not_current_player")


if __name__ == "__main__":
    unittest.main()
