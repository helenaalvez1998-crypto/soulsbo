from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from typing import Any

from sistemas.card_engine_v2.alpha_catalog import RARITY_IDS
from sistemas.card_engine_v2.application import AlphaGameApplication, AsyncAlphaGameApplication
from sistemas.card_engine_v2.discord_gateway import CardEngineV2DiscordGateway
from sistemas.card_engine_v2.errors import InvalidOperation
from tests.card_engine_v2.support import mechanics_catalog


class FakeLegacyDatabase:
    def __init__(self, rows_by_user: dict[int, list[dict[str, Any]]]) -> None:
        self.rows_by_user = rows_by_user

    async def coliseu_listar_exemplares(self, user_id: int, card_id: str | None = None):
        rows = [dict(row) for row in self.rows_by_user.get(int(user_id), [])]
        if card_id is not None:
            rows = [row for row in rows if row["card_id"] == card_id]
        return rows


class DiscordGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        catalog = mechanics_catalog(self.root)
        self.application = AlphaGameApplication(
            match_database_path=self.root / "matches.sqlite3",
            deck_database_path=self.root / "decks.sqlite3",
            catalog=catalog,
        )
        self.async_application = AsyncAlphaGameApplication(self.application)
        definitions = {
            card_id: catalog.definition_for(card_id)
            for card_id in sorted(catalog.allowed_card_ids())
        }
        unit_ids = [card_id for card_id, item in definitions.items() if item.get("kind") == "unit"]
        special_ids = [card_id for card_id, item in definitions.items() if item.get("kind") == "special"]
        # Ten models x three distinct exemplars = one legal 30-card deck.
        self.deck_card_ids = (unit_ids[:9] + special_ids[:1]) * 3
        rarity_names = {value: key for key, value in RARITY_IDS.items()}
        self.rows_by_user: dict[int, list[dict[str, Any]]] = {}
        self.exemplar_ids: dict[int, list[int]] = {}
        for user_id, start in ((1001, 100_000), (2002, 200_000)):
            rows = []
            exemplar_ids = []
            for index, card_id in enumerate(self.deck_card_ids):
                definition = definitions[card_id]
                exemplar_id = start + index
                base_power = definition.get("power_base")
                power = int(base_power or 1) + (index % 2 if definition.get("kind") == "unit" else 0)
                rarity_id = definition.get("rarity_id") or "common"
                rows.append({
                    "id": exemplar_id,
                    "user_id": user_id,
                    "card_id": card_id,
                    "rarity": rarity_names[rarity_id],
                    "power": power,
                    "source": "discord_gateway_test",
                    "origin_type": "catalogo",
                    "origin_card_id": "",
                    "is_sacrificable": 1,
                })
                exemplar_ids.append(exemplar_id)
            self.rows_by_user[user_id] = rows
            self.exemplar_ids[user_id] = exemplar_ids
        self.database = FakeLegacyDatabase(self.rows_by_user)
        self.gateway = CardEngineV2DiscordGateway(
            database=self.database,
            application=self.async_application,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _run(self, coroutine):
        return asyncio.run(coroutine)

    def test_collection_projection_contains_only_allowlisted_physical_exemplars(self):
        inventory = self._run(self.gateway.collection_for_player(1001))
        self.assertEqual(set(inventory), set(self.exemplar_ids[1001]))
        self.assertTrue(all(item["owner_player_id"] == "1001" for item in inventory.values()))
        self.assertTrue(all(item["card_id"] in self.application.catalog.allowed_card_ids() for item in inventory.values()))

    def test_authenticated_users_save_decks_and_create_match_with_fresh_inventory(self):
        async def scenario():
            for user_id, deck_id, leader_id, faction_id in (
                (1001, "a-main", "comandante_fornalha", "golden_order"),
                (2002, "b-main", "mestre_eclipse", "dark_moon"),
            ):
                await self.gateway.save_deck(
                    authenticated_player_id=user_id,
                    deck_id=deck_id,
                    name=f"Deck {user_id}",
                    card_ids=self.deck_card_ids,
                    exemplar_ids=self.exemplar_ids[user_id],
                    faction_id=faction_id,
                    leader_id=leader_id,
                )

            result = await self.gateway.create_match_from_decks(
                authenticated_challenger_id=1001,
                authenticated_opponent_id=2002,
                challenger_deck_id="a-main",
                opponent_deck_id="b-main",
            )
            self.assertGreater(result["match_id"], 0)
            self.assertLess(result["match_id"], 1 << 53)
            self.assertEqual(result["selected_exemplar_count"], 60)
            self.assertEqual(result["first_player_selection"], "server_random")

            own_view = await self.gateway.player_view(match_id=result["match_id"], authenticated_player_id=1001)
            self.assertEqual(len(own_view["players"]["1001"]["hand"]), 4)
            matches_for_a = await self.gateway.list_matches(1001)
            matches_for_b = await self.gateway.list_matches(2002)
            matches_for_outsider = await self.gateway.list_matches(9999)
            self.assertEqual([item["match_id"] for item in matches_for_a], [result["match_id"]])
            self.assertEqual([item["match_id"] for item in matches_for_b], [result["match_id"]])
            self.assertEqual(matches_for_outsider, [])
            self.assertEqual(
                set(matches_for_a[0]),
                {"match_id", "status", "opponent_player_id", "created_at", "updated_at", "state_revision", "event_watermark"},
            )
            self.assertEqual(own_view["players"]["2002"]["hand"], [])
            self.assertTrue(own_view["players"]["2002"]["hand_hidden"])
            with self.assertRaises(InvalidOperation):
                await self.gateway.player_view(match_id=result["match_id"], authenticated_player_id=9999)

        self._run(scenario())

    def test_match_history_is_paginated_and_hides_physical_and_operation_identifiers(self):
        async def scenario():
            for user_id, deck_id, leader_id, faction_id in (
                (1001, "a-main", "comandante_fornalha", "golden_order"),
                (2002, "b-main", "mestre_eclipse", "dark_moon"),
            ):
                await self.gateway.save_deck(
                    authenticated_player_id=user_id,
                    deck_id=deck_id,
                    name=f"Deck {user_id}",
                    card_ids=self.deck_card_ids,
                    exemplar_ids=self.exemplar_ids[user_id],
                    faction_id=faction_id,
                    leader_id=leader_id,
                )
            result = await self.gateway.create_match_from_decks(
                authenticated_challenger_id=1001,
                authenticated_opponent_id=2002,
                challenger_deck_id="a-main",
                opponent_deck_id="b-main",
            )
            state = await self.gateway.player_view(
                match_id=result["match_id"], authenticated_player_id=1001
            )
            actor = str(state["current_player_id"])
            await self.gateway.execute_action(
                match_id=result["match_id"],
                authenticated_player_id=actor,
                action="pass_turn",
                expected_revision=state["state_revision"],
            )
            history = await self.gateway.match_history(
                match_id=result["match_id"], authenticated_player_id=1001, limit=1
            )
            self.assertEqual(len(history["events"]), 1)
            self.assertTrue(history["has_more"])
            event = history["events"][0]
            forbidden = {"event_id", "operation_id", "source_instance_id", "target_instance_ids", "caused_by_event_ids"}
            self.assertTrue(forbidden.isdisjoint(event))
            next_page = await self.gateway.match_history(
                match_id=result["match_id"],
                authenticated_player_id=1001,
                after_sequence=history["next_cursor"],
                limit=10,
            )
            self.assertGreaterEqual(len(next_page["events"]), 0)
            with self.assertRaises(InvalidOperation):
                await self.gateway.match_history(
                    match_id=result["match_id"], authenticated_player_id=9999
                )

        self._run(scenario())

    def test_deck_update_uses_expected_version_and_preserves_owner_boundary(self):
        async def scenario():
            first = await self.gateway.save_deck(
                authenticated_player_id=1001,
                deck_id="editable",
                name="Original",
                card_ids=self.deck_card_ids,
                exemplar_ids=self.exemplar_ids[1001],
                faction_id="golden_order",
                leader_id="comandante_fornalha",
            )
            updated = await self.gateway.save_deck(
                authenticated_player_id=1001,
                deck_id="editable",
                name="Atualizado",
                card_ids=self.deck_card_ids,
                exemplar_ids=self.exemplar_ids[1001],
                faction_id="golden_order",
                leader_id="comandante_fornalha",
                expected_version=first["version"],
            )
            self.assertEqual(updated["version"], first["version"] + 1)
            self.assertEqual(updated["name"], "Atualizado")
            self.assertIsNone(await self.gateway.get_deck(
                authenticated_player_id=2002, deck_id="editable"
            ))

        self._run(scenario())

    def test_matchmaking_rechecks_physical_ownership_and_rejects_stale_decks(self):
        async def scenario():
            await self.gateway.save_deck(
                authenticated_player_id=1001,
                deck_id="a-main",
                name="Deck A",
                card_ids=self.deck_card_ids,
                exemplar_ids=self.exemplar_ids[1001],
                faction_id="golden_order",
                leader_id="comandante_fornalha",
            )
            await self.gateway.save_deck(
                authenticated_player_id=2002,
                deck_id="b-main",
                name="Deck B",
                card_ids=self.deck_card_ids,
                exemplar_ids=self.exemplar_ids[2002],
                faction_id="dark_moon",
                leader_id="mestre_eclipse",
            )
            self.rows_by_user[2002] = self.rows_by_user[2002][1:]
            with self.assertRaises(InvalidOperation):
                await self.gateway.create_match_from_decks(
                    authenticated_challenger_id=1001,
                    authenticated_opponent_id=2002,
                    challenger_deck_id="a-main",
                    opponent_deck_id="b-main",
                )

        self._run(scenario())

    def test_player_cannot_challenge_themselves_or_use_invalid_platform_identity(self):
        async def scenario():
            with self.assertRaises(InvalidOperation):
                await self.gateway.create_match_from_decks(
                    authenticated_challenger_id=1001,
                    authenticated_opponent_id=1001,
                    challenger_deck_id="a",
                    opponent_deck_id="b",
                )
            with self.assertRaises(InvalidOperation):
                await self.gateway.list_decks("not-a-discord-id")
            with self.assertRaises(InvalidOperation):
                await self.gateway.list_decks("١٢٣٤٥٦")

        self._run(scenario())

    def test_pass_action_is_authenticated_and_returns_a_receipt(self):
        async def scenario():
            for user_id, deck_id, leader_id, faction_id in (
                (1001, "a-main", "comandante_fornalha", "golden_order"),
                (2002, "b-main", "mestre_eclipse", "dark_moon"),
            ):
                await self.gateway.save_deck(
                    authenticated_player_id=user_id,
                    deck_id=deck_id,
                    name=f"Deck {user_id}",
                    card_ids=self.deck_card_ids,
                    exemplar_ids=self.exemplar_ids[user_id],
                    faction_id=faction_id,
                    leader_id=leader_id,
                )
            result = await self.gateway.create_match_from_decks(
                authenticated_challenger_id=1001,
                authenticated_opponent_id=2002,
                challenger_deck_id="a-main",
                opponent_deck_id="b-main",
            )
            state = await self.gateway.player_view(match_id=result["match_id"], authenticated_player_id=1001)
            actor_id = int(state["current_player_id"])
            receipt = await self.gateway.execute_action(
                match_id=result["match_id"],
                authenticated_player_id=actor_id,
                action="pass_turn",
                expected_revision=state["state_revision"],
            )
            self.assertEqual(receipt.result["outcome"], "applied")
            with self.assertRaises(InvalidOperation):
                await self.gateway.execute_action(
                    match_id=result["match_id"],
                    authenticated_player_id=9999,
                    action="pass_turn",
                )

        self._run(scenario())


if __name__ == "__main__":
    unittest.main()
