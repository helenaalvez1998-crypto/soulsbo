from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog
from sistemas.card_engine_v2.errors import IdempotencyConflict, InvalidOperation
from sistemas.card_engine_v2.match import AlphaMatchController
from sistemas.card_engine_v2.power import effective_power
from sistemas.card_engine_v2.repository import HandlerResult, SQLiteMatchRepository
from tests.card_engine_v2.support import mechanics_catalog

PLAYER_A = "1001"
PLAYER_B = "2002"
MATCH_ID = 2026112701

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


class PlayableAlphaMatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "alpha-match.sqlite3"
        self.repository = SQLiteMatchRepository(self.db_path)
        self.catalog = mechanics_catalog(self.temp.name)
        self.controller = AlphaMatchController(self.repository, self.catalog)
        self.controller.create_match(
            match_id=MATCH_ID,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: list(DECK_A), PLAYER_B: list(DECK_B)},
            # Preserve this file's six-card integration fixtures. The
            # production-facing alpha default is four cards in ruleset v0.4.
            initial_hand_size=6,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def view(self):
        return self.controller.view(MATCH_ID)

    def hand_card(self, player_id: str, card_id: str, occurrence: int = 0) -> str:
        matches = [
            item["instance_id"]
            for item in self.view()["players"][player_id]["hand"]
            if item["card_id"] == card_id
        ]
        return matches[occurrence]

    def play_unit(self, player_id: str, card_id: str):
        return self.controller.play_unit(
            MATCH_ID,
            actor_player_id=player_id,
            instance_id=self.hand_card(player_id, card_id),
        )

    def pass_turn(self, player_id: str):
        return self.controller.pass_turn(MATCH_ID, actor_player_id=player_id)

    def set_life_fixture(self, life_by_player: dict[str, int]) -> None:
        runtime = self.repository.get_match_runtime(MATCH_ID)
        runtime["life_by_player"] = dict(life_by_player)
        state = self.repository.get_match(MATCH_ID)
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "test-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.set_player_life",
            "payload": {},
        }
        event = {
            "event_id": str(uuid.uuid4()),
            "kind": "test_player_life_installed",
            "effect_scope": "system",
            "source_effect_id": None,
            "source_instance_id": None,
            "target_instance_ids": [],
            "caused_by_event_ids": [],
            "payload": {"life_by_player": life_by_player},
        }
        self.repository.execute_operation(
            MATCH_ID,
            request,
            lambda working, body: HandlerResult(
                outcome="applied", state=working, events=[event], runtime_state=runtime
            ),
        )

    def test_catalog_is_explicit_allowlist_and_manifest_is_hashed(self):
        self.assertEqual(len(self.catalog.allowed_card_ids()), 27)
        self.assertEqual(
            self.catalog.definition_for("gwent_unidade_herdeiro_portao")["effect_id"],
            "effect.vengeance_on_removal",
        )
        self.assertFalse(self.catalog.balance["rarity_scaling"])
        self.assertEqual(
            self.catalog.definition_manifest()["ruleset_release_id"],
            "alpha-test-only.ruleset.v0.5",
        )
        with self.assertRaises(InvalidOperation):
            self.catalog.definition_for("arma_agulha_astro")
        self.assertEqual(self.catalog.definition_for("chefe_rei_afogado")["effect_id"], "effect.discard_advantage_power")
        self.assertEqual(len(self.catalog.definition_manifest()["definition_digest"]), 64)

    def test_duplicate_models_get_distinct_physical_instances(self):
        # The same model is intentionally included twice in one test deck.
        self.assertEqual(DECK_B.count("arma_lanca_fornalha"), 2)
        state = self.repository.get_match(MATCH_ID)
        ids = [
            instance_id
            for instance_id, instance in state["instances"].items()
            if instance["owner_player_id"] == PLAYER_B and instance["card_id"] == "arma_lanca_fornalha"
        ]
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)
        self.assertTrue(all(state["instances"][item]["exemplar_id"] is None for item in ids))

    def test_initial_deal_and_turn_order(self):
        view = self.view()
        self.assertEqual(view["current_player_id"], PLAYER_A)
        self.assertEqual(len(view["players"][PLAYER_A]["hand"]), 6)
        self.assertEqual(view["players"][PLAYER_A]["draw_pile_count"], 2)
        self.assertEqual(view["players"][PLAYER_A]["life"], 20)
        self.assertEqual(view["players"][PLAYER_B]["life"], 20)
        receipt = self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertTrue(receipt.result["costs"]["turn_consumed"])
        self.assertEqual(self.view()["current_player_id"], PLAYER_B)

    def test_veterano_on_play_bonus_applies_to_self_and_weakest_same_row_ally(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        veteran_id = self.hand_card(PLAYER_A, "gwent_v75_ordem_veterano_juramento")
        result = self.controller.play_unit(MATCH_ID, actor_player_id=PLAYER_A, instance_id=veteran_id)
        self.assertEqual(result.result["outcome"], "applied")
        state = self.repository.get_match(MATCH_ID)
        veteran = state["instances"][veteran_id]
        lancer_id = next(
            item for item in state["players"][PLAYER_A]["zones"]["board"]
            if state["instances"][item]["card_id"] == "arma_lanca_fornalha"
        )
        self.assertEqual(sum(x["amount"] for x in veteran["state"]["bonus_grants"]), 1)
        self.assertEqual(sum(x["amount"] for x in state["instances"][lancer_id]["state"]["bonus_grants"]), 1)
        self.assertEqual(self.view()["players"][PLAYER_A]["score"], 11)

    def test_effective_power_combines_bonus_weather_frost_and_floor(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        state = self.repository.get_match(MATCH_ID)
        lancer_id = state["players"][PLAYER_A]["zones"]["board"][0]
        unit = state["instances"][lancer_id]
        unit["state"]["bonus_grants"].append(
            {
                "grant_id": str(uuid.uuid4()),
                "amount": 2,
                "source_effect_id": "test.alpha_bonus",
                "source_instance_id": None,
                "applied_event_id": str(uuid.uuid4()),
                "expires_on": "round_close",
                "clamp_policy_id": "balance.alpha.raw_grants.v1",
            }
        )
        unit["state"]["status_applications"].append(
            {
                "application_id": str(uuid.uuid4()),
                "status_id": "status.frost",
                "source_effect_id": "gwent_geada_cariana",
                "source_instance_id": None,
                "applied_event_id": str(uuid.uuid4()),
                "expires_on": "round_close",
            }
        )
        unit["state"]["status_applications"].append(
            {
                "application_id": str(uuid.uuid4()),
                "status_id": "status.madness",
                "source_effect_id": "test.alpha_status",
                "source_instance_id": None,
                "applied_event_id": str(uuid.uuid4()),
                "expires_on": "round_close",
            }
        )
        self.assertEqual(effective_power(state, unit, {"melee": 1, "ranged": 0, "siege": 0}), 4)
        self.assertEqual(effective_power(state, unit, {"melee": 99, "ranged": 0, "siege": 0}), 1)
        unit["definition_snapshot"]["intrinsic_weather_resistance"] = 2
        self.assertEqual(effective_power(state, unit, {"melee": 1, "ranged": 0, "siege": 0}), 5)

    def test_weather_special_changes_both_sides_effective_power(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        weather_id = self.hand_card(PLAYER_A, "gwent_especial_tempestade")
        result = self.controller.play_special(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=weather_id,
            selected_row="melee",
        )
        self.assertEqual(result.result["outcome"], "applied")
        view = self.view()
        self.assertEqual(view["players"][PLAYER_A]["score"], 4)
        self.assertEqual(view["players"][PLAYER_B]["score"], 5)
        state = self.repository.get_match(MATCH_ID)
        self.assertIn(weather_id, state["players"][PLAYER_A]["zones"]["discard"])

    def test_frost_special_applies_status_marks_and_reduces_power(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        frost_id = self.hand_card(PLAYER_A, "elden_especial_geada")
        result = self.controller.play_special(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=frost_id,
            selected_row="melee",
        )
        self.assertEqual(result.result["outcome"], "applied")
        state = self.repository.get_match(MATCH_ID)
        enemy_id = state["players"][PLAYER_B]["zones"]["board"][0]
        enemy = state["instances"][enemy_id]
        self.assertEqual(sum(x["status_id"] == "status.frost" for x in enemy["state"]["status_applications"]), 1)
        self.assertEqual(self.view()["players"][PLAYER_B]["score"], 5)

    def test_execution_offer_uses_current_effective_power_after_weather(self):
        weather_id = self.hand_card(PLAYER_A, "gwent_especial_tempestade")
        self.controller.play_special(MATCH_ID, actor_player_id=PLAYER_A, source_instance_id=weather_id, selected_row="melee")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        execution_id = self.hand_card(PLAYER_A, "gwent_especial_execucao")
        offer = self.controller.target_offer(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=execution_id,
            selected_row="melee",
        )
        self.assertEqual(len(offer["candidates"]), 1)
        self.assertEqual(offer["candidates"][0]["effective_power"], 5)

    def test_egide_shield_blocks_execution_consumes_both_costs_and_no_vengeance(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        self.play_unit(PLAYER_A, "gwent_v75_ordem_veterano_juramento")
        aegis_id = self.hand_card(PLAYER_B, "gwent_especial_egide")
        enemy = self.repository.get_match(MATCH_ID)["players"][PLAYER_B]["zones"]["board"][0]
        offer = self.controller.target_offer(MATCH_ID, actor_player_id=PLAYER_B, source_instance_id=aegis_id)
        self.controller.play_special(
            MATCH_ID,
            actor_player_id=PLAYER_B,
            source_instance_id=aegis_id,
            selection={"mode": "manual_single", "target_instance_id": enemy},
            expected_revision=offer["state_revision"],
        )
        self.assertEqual(self.view()["players"][PLAYER_B]["board"][0]["protection_charges"], 1)
        execution_id = self.hand_card(PLAYER_A, "gwent_especial_execucao")
        offer = self.controller.target_offer(
            MATCH_ID, actor_player_id=PLAYER_A, source_instance_id=execution_id, selected_row="melee"
        )
        result = self.controller.play_special(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=execution_id,
            selected_row="melee",
            selection={"mode": "manual_single", "target_instance_id": enemy},
            expected_revision=offer["state_revision"],
        )
        self.assertEqual(result.result["outcome"], "blocked")
        self.assertTrue(result.result["costs"]["source_consumed"])
        self.assertEqual(len(result.result["costs"]["protection_grants_consumed"]), 1)
        self.assertEqual(result.result["target_results"][0]["outcome"], "blocked")
        state = self.repository.get_match(MATCH_ID)
        self.assertIn(enemy, state["players"][PLAYER_B]["zones"]["board"])
        self.assertNotIn(execution_id, state["players"][PLAYER_A]["zones"]["hand"])
        self.assertFalse(any(event["kind"] == "vengeance_bonus_applied" for event in self.repository.get_events(MATCH_ID)))

    def test_execution_removes_vengeance_unit_then_buffs_only_survivors(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        self.play_unit(PLAYER_A, "gwent_v75_ordem_veterano_juramento")
        self.play_unit(PLAYER_B, "chefe_vigia_cinzento")
        self.play_special(
            PLAYER_A,
            "gwent_especial_execucao",
            row="melee",
            target_name="Godwyn, o Dourado",
        )
        state = self.repository.get_match(MATCH_ID)
        remaining_enemy = state["players"][PLAYER_B]["zones"]["board"][0]
        discarded = next(
            instance_id for instance_id in state["players"][PLAYER_B]["zones"]["discard"]
            if state["instances"][instance_id]["card_id"] == "gwent_unidade_herdeiro_portao"
        )
        self.assertEqual(len(state["instances"][remaining_enemy]["state"]["bonus_grants"]), 1)
        self.assertEqual(state["instances"][remaining_enemy]["state"]["bonus_grants"][0]["source_effect_id"], "effect.vengeance_on_removal")
        self.assertEqual(state["instances"][remaining_enemy]["state"]["bonus_grants"][0]["source_instance_id"], discarded)
        events = self.repository.get_events(MATCH_ID)
        removed = next(event for event in events if event["kind"] == "unit_removed")
        vengeance = next(event for event in events if event["kind"] == "vengeance_bonus_applied")
        self.assertEqual(vengeance["caused_by_event_ids"], [removed["event_id"]])

    def test_sacrifice_is_a_revision_bound_turn_action_and_replays_idempotently(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "arma_lanca_fornalha")
        state_before = self.repository.get_match(MATCH_ID)
        target_id = state_before["players"][PLAYER_A]["zones"]["board"][0]

        offer = self.controller.sacrifice_target_offer(
            MATCH_ID,
            actor_player_id=PLAYER_A,
        )
        self.assertEqual(offer["state_revision"], state_before["state_revision"])
        self.assertEqual(
            [candidate["target_instance_id"] for candidate in offer["candidates"]],
            [target_id],
        )

        operation_id = str(uuid.uuid4())
        receipt = self.controller.sacrifice_unit(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            target_instance_id=target_id,
            expected_revision=offer["state_revision"],
            operation_id=operation_id,
        )
        replay = self.controller.sacrifice_unit(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            target_instance_id=target_id,
            expected_revision=offer["state_revision"],
            operation_id=operation_id,
        )

        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertTrue(receipt.result["costs"]["turn_consumed"])
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.result, receipt.result)

        state_after = self.repository.get_match(MATCH_ID)
        runtime_after = self.repository.get_match_runtime(MATCH_ID)
        self.assertNotIn(target_id, state_after["players"][PLAYER_A]["zones"]["board"])
        self.assertIn(target_id, state_after["players"][PLAYER_A]["zones"]["discard"])
        self.assertEqual(state_after["players"][PLAYER_A]["counters"]["sacrifice_count"], 1)
        self.assertEqual(state_after["players"][PLAYER_A]["counters"]["board_removal_count"], 0)
        self.assertEqual(runtime_after["current_player_id"], PLAYER_B)

        events = self.repository.get_events(MATCH_ID)
        removal = next(event for event in events if event["kind"] == "unit_removed")
        turn_event = next(
            event for event in events
            if event["kind"] == "turn_action_completed"
            and event["payload"].get("action") == "sacrifice_unit"
        )
        self.assertEqual(removal["payload"]["cause_id"], "sacrifice")
        self.assertEqual(removal["target_instance_ids"], [target_id])
        self.assertEqual(turn_event["caused_by_event_ids"], [removal["event_id"]])
        self.assertEqual(len([event for event in events if event["kind"] == "unit_removed"]), 1)

    def test_sacrifice_bypasses_egide_and_triggers_vengeance_for_survivors(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        self.play_unit(PLAYER_A, "gwent_v75_ordem_veterano_juramento")
        self.play_unit(PLAYER_B, "arma_lanca_fornalha")
        self.pass_turn(PLAYER_A)

        state_before_aegis = self.repository.get_match(MATCH_ID)
        vengeance_id = next(
            instance_id for instance_id in state_before_aegis["players"][PLAYER_B]["zones"]["board"]
            if state_before_aegis["instances"][instance_id]["card_id"] == "gwent_unidade_herdeiro_portao"
        )
        aegis_id = self.hand_card(PLAYER_B, "gwent_especial_egide")
        aegis_offer = self.controller.target_offer(
            MATCH_ID,
            actor_player_id=PLAYER_B,
            source_instance_id=aegis_id,
        )
        self.controller.play_special(
            MATCH_ID,
            actor_player_id=PLAYER_B,
            source_instance_id=aegis_id,
            selection={"mode": "manual_single", "target_instance_id": vengeance_id},
            expected_revision=aegis_offer["state_revision"],
        )

        sacrifice_offer = self.controller.sacrifice_target_offer(
            MATCH_ID,
            actor_player_id=PLAYER_B,
        )
        self.assertIn(
            vengeance_id,
            [candidate["target_instance_id"] for candidate in sacrifice_offer["candidates"]],
        )
        result = self.controller.sacrifice_unit(
            MATCH_ID,
            actor_player_id=PLAYER_B,
            target_instance_id=vengeance_id,
            expected_revision=sacrifice_offer["state_revision"],
        )

        self.assertEqual(result.result["outcome"], "applied")
        state = self.repository.get_match(MATCH_ID)
        ally_survivors = state["players"][PLAYER_B]["zones"]["board"]
        self.assertNotIn(vengeance_id, ally_survivors)
        self.assertIn(vengeance_id, state["players"][PLAYER_B]["zones"]["discard"])
        survivor_id = next(
            instance_id for instance_id in ally_survivors
            if state["instances"][instance_id]["state"]["current_row"]
            == state["instances"][vengeance_id]["state"]["last_board_row"]
        )
        grants = state["instances"][survivor_id]["state"]["bonus_grants"]
        vengeance_grant = next(
            grant for grant in grants
            if grant["source_effect_id"] == "effect.vengeance_on_removal"
            and grant["source_instance_id"] == vengeance_id
        )
        self.assertEqual(vengeance_grant["amount"], 1)
        # Sacrifice bypasses the shield; it does not consume the unused charge.
        self.assertEqual(len(state["instances"][vengeance_id]["state"]["protection_grants"]), 1)
        self.assertEqual(
            state["instances"][vengeance_id]["state"]["protection_grants"][0]["charges"],
            1,
        )

        events = self.repository.get_events(MATCH_ID)
        removal = next(
            event for event in events
            if event["kind"] == "unit_removed" and vengeance_id in event["target_instance_ids"]
        )
        vengeance_event = next(
            event for event in events
            if event["kind"] == "vengeance_bonus_applied"
            and event["source_instance_id"] == vengeance_id
        )
        self.assertEqual(removal["payload"]["cause_id"], "sacrifice")
        self.assertEqual(vengeance_event["caused_by_event_ids"], [removal["event_id"]])
        self.assertFalse(any(event["kind"] == "unit_removal_blocked" for event in events))

    def test_stale_sacrifice_offer_is_rejected_without_removing_target(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "arma_lanca_fornalha")
        target_id = self.repository.get_match(MATCH_ID)["players"][PLAYER_A]["zones"]["board"][0]
        offer = self.controller.sacrifice_target_offer(MATCH_ID, actor_player_id=PLAYER_A)

        # Both players make another legal action; A is current again, but the
        # original server offer is stale and must not be accepted.
        self.play_unit(PLAYER_A, "gwent_v75_ordem_veterano_juramento")
        self.play_unit(PLAYER_B, "chefe_vigia_cinzento")
        before = self.repository.get_match(MATCH_ID)
        receipt = self.controller.sacrifice_unit(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            target_instance_id=target_id,
            expected_revision=offer["state_revision"],
        )
        after = self.repository.get_match(MATCH_ID)

        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "revision_conflict")
        self.assertEqual(after, before)
        self.assertIn(target_id, after["players"][PLAYER_A]["zones"]["board"])

    def play_special(self, player_id: str, card_id: str, *, row: str, target_name: str):
        source_id = self.hand_card(player_id, card_id)
        offer = self.controller.target_offer(
            MATCH_ID,
            actor_player_id=player_id,
            source_instance_id=source_id,
            selected_row=row,
        )
        target_id = next(
            item["target_instance_id"] for item in offer["candidates"] if item["display_name"] == target_name
        )
        return self.controller.play_special(
            MATCH_ID,
            actor_player_id=player_id,
            source_instance_id=source_id,
            selected_row=row,
            selection={"mode": "manual_single", "target_instance_id": target_id},
            expected_revision=offer["state_revision"],
        )


    def test_targeted_special_requires_revision_from_server_offer(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        source_id = self.hand_card(PLAYER_A, "gwent_especial_execucao")
        offer = self.controller.target_offer(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=source_id,
            selected_row="melee",
        )
        target_id = offer["candidates"][0]["target_instance_id"]
        before = self.repository.get_match(MATCH_ID)
        with self.assertRaises(InvalidOperation):
            self.controller.play_special(
                MATCH_ID,
                actor_player_id=PLAYER_A,
                source_instance_id=source_id,
                selected_row="melee",
                selection={"mode": "manual_single", "target_instance_id": target_id},
            )
        after = self.repository.get_match(MATCH_ID)
        self.assertEqual(after["state_revision"], before["state_revision"])
        self.assertIn(source_id, after["players"][PLAYER_A]["zones"]["hand"])

    def test_stale_target_offer_is_rejected_without_consuming_source(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        source_id = self.hand_card(PLAYER_A, "gwent_especial_execucao")
        offer = self.controller.target_offer(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=source_id,
            selected_row="melee",
        )
        target_id = offer["candidates"][0]["target_instance_id"]
        # Change the match revision and return control to A. The old target
        # offer must not be usable even though A is current again.
        self.play_unit(PLAYER_A, "gwent_v75_ordem_veterano_juramento")
        self.pass_turn(PLAYER_B)
        before = self.repository.get_match(MATCH_ID)
        receipt = self.controller.play_special(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=source_id,
            selected_row="melee",
            selection={"mode": "manual_single", "target_instance_id": target_id},
            expected_revision=offer["state_revision"],
        )
        after = self.repository.get_match(MATCH_ID)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "revision_conflict")
        self.assertEqual(after["state_revision"], before["state_revision"])
        self.assertIn(source_id, after["players"][PLAYER_A]["zones"]["hand"])
        self.assertIn(target_id, after["players"][PLAYER_B]["zones"]["board"])

    def test_round_close_expires_all_zones_archives_without_vengeance(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        godwyn_id = self.repository.get_match(MATCH_ID)["players"][PLAYER_B]["zones"]["board"][0]
        # Put a round-scoped grant on a card that is already in discard; the
        # global round-close sweep must expire it too.
        state = self.repository.get_match(MATCH_ID)
        off_board_id = state["players"][PLAYER_B]["zones"]["hand"][0]
        state["players"][PLAYER_B]["zones"]["hand"].remove(off_board_id)
        state["players"][PLAYER_B]["zones"]["discard"].append(off_board_id)
        state["instances"][off_board_id]["state"]["bonus_grants"].append(
            {
                "grant_id": str(uuid.uuid4()),
                "amount": 1,
                "source_effect_id": "test.offboard_bonus",
                "source_instance_id": None,
                "applied_event_id": str(uuid.uuid4()),
                "expires_on": "round_close",
                "clamp_policy_id": "balance.alpha.raw_grants.v1",
            }
        )
        # Use repository internal operation path only in this test to install
        # the prepared fixture as a single valid state transition.
        from sistemas.card_engine_v2.repository import HandlerResult
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "test-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_offboard_grant",
            "payload": {},
        }
        self.repository.execute_operation(
            MATCH_ID,
            request,
            lambda working, body: HandlerResult(outcome="applied", state=state, events=[{
                "event_id": str(uuid.uuid4()),
                "kind": "test_fixture_installed",
                "effect_scope": "system",
                "source_effect_id": None,
                "source_instance_id": None,
                "target_instance_ids": [off_board_id],
                "caused_by_event_ids": [],
                "payload": {"fixture": "offboard-round-close-grant"},
            }]),
        )
        self.pass_turn(PLAYER_A)
        self.pass_turn(PLAYER_B)
        state_after = self.repository.get_match(MATCH_ID)
        self.assertEqual(state_after["instances"][off_board_id]["state"]["bonus_grants"], [])
        self.assertEqual(state_after["players"][PLAYER_B]["round_state"]["last_unit_play_row"], None)
        self.assertIn(godwyn_id, state_after["players"][PLAYER_B]["zones"]["discard"])
        events = self.repository.get_events(MATCH_ID)
        archives = [event for event in events if event["kind"] == "unit_archived"]
        self.assertTrue(archives)
        self.assertTrue(all(event["effect_scope"] == "system" for event in archives))
        self.assertFalse(any(event["kind"] == "vengeance_bonus_applied" for event in events))

    def test_round_close_applies_row_damage_to_player_life(self):
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "arma_cajado_marulho")
        self.pass_turn(PLAYER_A)
        self.pass_turn(PLAYER_B)

        view = self.view()
        self.assertEqual(view["players"][PLAYER_A]["life"], 14)
        # The round's row damage leaves B at 15; the next round starts with
        # B's draw pile empty, so turn-start deck fatigue then removes one.
        self.assertEqual(view["players"][PLAYER_B]["life"], 14)
        history = view["round_history"][0]
        self.assertEqual(history["damage_by_player"], {PLAYER_A: 6, PLAYER_B: 5})
        self.assertEqual(history["life_by_player"], {PLAYER_A: 14, PLAYER_B: 15})
        self.assertEqual(history["row_power_by_player"][PLAYER_A]["melee"], 5)
        self.assertEqual(history["row_power_by_player"][PLAYER_B]["ranged"], 6)
        self.assertEqual(history["winner_player_id"], PLAYER_B)

        events = self.repository.get_events(MATCH_ID)
        row_events = [event for event in events if event["kind"] == "combat_row_resolved"]
        damage_events = [event for event in events if event["kind"] == "player_damage_applied"]
        combat_damage_events = [event for event in damage_events if "damage_source" not in event["payload"]]
        fatigue_damage_events = [event for event in damage_events if event["payload"].get("damage_source") == "deck_fatigue"]
        self.assertEqual(len(row_events), 3)
        self.assertEqual(len(combat_damage_events), 2)
        self.assertEqual(len(fatigue_damage_events), 1)
        self.assertTrue(all(event["caused_by_event_ids"] for event in damage_events))
        score_frozen = next(event for event in events if event["kind"] == "round_score_frozen")
        self.assertEqual(set(score_frozen["caused_by_event_ids"]), {event["event_id"] for event in row_events})

    def test_lethal_combat_ends_match_before_best_of_three_limit(self):
        self.set_life_fixture({PLAYER_A: 5, PLAYER_B: 20})
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "arma_cajado_marulho")
        self.pass_turn(PLAYER_A)
        self.pass_turn(PLAYER_B)

        final = self.view()
        self.assertEqual(final["status"], "finished")
        self.assertEqual(final["match_winner_player_id"], PLAYER_B)
        self.assertEqual(final["match_finish_reason"], "life_depleted")
        self.assertEqual(final["players"][PLAYER_A]["life"], 0)
        self.assertEqual(final["players"][PLAYER_B]["life"], 15)
        self.assertEqual(final["round_number"], 1)
        self.assertTrue(any(event["kind"] == "player_defeated" for event in self.repository.get_events(MATCH_ID)))

    def test_simultaneous_lethal_combat_finishes_as_draw(self):
        self.set_life_fixture({PLAYER_A: 5, PLAYER_B: 5})
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "arma_cajado_marulho")
        self.pass_turn(PLAYER_A)
        self.pass_turn(PLAYER_B)

        final = self.view()
        self.assertEqual(final["status"], "finished")
        self.assertIsNone(final["match_winner_player_id"])
        self.assertEqual(final["match_finish_reason"], "simultaneous_lethal")
        self.assertEqual(final["players"][PLAYER_A]["life"], 0)
        self.assertEqual(final["players"][PLAYER_B]["life"], 0)

    def test_same_operation_replay_does_not_play_unit_twice(self):
        card_id = self.hand_card(PLAYER_A, "arma_lanca_fornalha")
        operation_id = str(uuid.uuid4())
        first = self.controller.play_unit(
            MATCH_ID, actor_player_id=PLAYER_A, instance_id=card_id, operation_id=operation_id
        )
        second = self.controller.play_unit(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            instance_id=card_id,
            expected_revision=0,
            operation_id=operation_id,
        )
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.result, second.result)
        self.assertEqual(self.view()["players"][PLAYER_A]["board"][0]["instance_id"], card_id)

    def test_invalid_turn_does_not_consume_card_or_advance_revision(self):
        before = self.view()
        card_id = self.hand_card(PLAYER_B, "gwent_unidade_herdeiro_portao")
        result = self.controller.play_unit(MATCH_ID, actor_player_id=PLAYER_B, instance_id=card_id)
        self.assertEqual(result.result["outcome"], "rejected")
        self.assertEqual(result.result["reason_code"], "not_current_player")
        after = self.view()
        self.assertEqual(after["state_revision"], before["state_revision"])
        self.assertIn(card_id, [item["instance_id"] for item in after["players"][PLAYER_B]["hand"]])

    def test_full_best_of_three_match_finishes_with_two_round_wins(self):
        # Round 1: A wins through two units, weather, Execution/Vingança and Égide.
        self.play_unit(PLAYER_A, "arma_lanca_fornalha")
        self.play_unit(PLAYER_B, "gwent_unidade_herdeiro_portao")
        self.play_unit(PLAYER_A, "gwent_v75_ordem_veterano_juramento")
        self.play_unit(PLAYER_B, "chefe_vigia_cinzento")
        self.controller.play_special(
            MATCH_ID,
            actor_player_id=PLAYER_A,
            source_instance_id=self.hand_card(PLAYER_A, "gwent_especial_tempestade"),
            selected_row="melee",
        )
        self.pass_turn(PLAYER_B)
        self.play_special(
            PLAYER_A,
            "gwent_especial_execucao",
            row="melee",
            target_name="Godwyn, o Dourado",
        )
        self.play_special(
            PLAYER_A,
            "gwent_especial_egide",
            row="melee",
            target_name="Lanceiro da Árvore Áurea",
        )
        self.pass_turn(PLAYER_A)
        self.assertEqual(self.view()["round_history"][0]["winner_player_id"], PLAYER_A)

        # Round 2: B answers with a higher single-unit score.
        self.play_unit(PLAYER_B, "arma_martelo_fornalha")
        self.pass_turn(PLAYER_A)
        self.pass_turn(PLAYER_B)
        self.assertEqual(self.view()["round_history"][1]["winner_player_id"], PLAYER_B)

        # Round 3: A wins the decider; best-of-three ends at 2-1.
        self.play_unit(PLAYER_A, "arma_martelo_fornalha")
        self.pass_turn(PLAYER_B)
        self.pass_turn(PLAYER_A)
        final = self.view()
        self.assertEqual(final["status"], "finished")
        self.assertEqual(final["phase"], "finished")
        self.assertEqual(final["round_wins"], {PLAYER_A: 2, PLAYER_B: 1})
        self.assertEqual([item["winner_player_id"] for item in final["round_history"]], [PLAYER_A, PLAYER_B, PLAYER_A])
        self.assertIsNone(final["current_player_id"])
        self.assertEqual(final["players"][PLAYER_A]["board"], [])
        self.assertEqual(final["players"][PLAYER_B]["board"], [])
        events = self.repository.get_events(MATCH_ID)
        self.assertTrue(any(item["kind"] == "match_finished" for item in events))
        self.assertGreaterEqual(sum(item["kind"] == "round_score_frozen" for item in events), 3)


if __name__ == "__main__":
    unittest.main()
