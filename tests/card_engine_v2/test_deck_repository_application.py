from __future__ import annotations

import asyncio
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import RARITY_IDS
from sistemas.card_engine_v2.application import (
    AlphaGameApplication,
    AsyncAlphaGameApplication,
    legacy_collection_counts,
    legacy_collection_exemplars,
)
from sistemas.card_engine_v2.errors import InvalidOperation, PersistenceConflict
from sistemas.card_engine_v2.deck_repository import SQLiteDeckRepository
from tests.card_engine_v2.support import mechanics_catalog

PLAYER_A = "1001"
PLAYER_B = "2002"
DECK_A_ID = "alpha-main"
DECK_B_ID = "alpha-control"


class DeckRepositoryApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog = mechanics_catalog(self.root)
        self.app = AlphaGameApplication(
            match_database_path=self.root / "matches.sqlite3",
            deck_database_path=self.root / "decks.sqlite3",
            catalog=self.catalog,
        )
        definitions = {card_id: self.catalog.definition_for(card_id) for card_id in self.catalog.allowed_card_ids()}
        units = sorted(card_id for card_id, item in definitions.items() if item.get("kind") == "unit")
        specials = sorted(card_id for card_id, item in definitions.items() if item.get("kind") == "special")
        self.unique_cards = units[:7] + specials[:3]
        self.card_ids = self.unique_cards * 3
        self.rarity_names = {value: key for key, value in RARITY_IDS.items()}
        self.exemplar_ids_by_player: dict[str, list[int]] = {}
        self.inventories_by_player: dict[str, dict[int, dict]] = {}
        for owner, start in ((PLAYER_A, 10000), (PLAYER_B, 20000)):
            ids: list[int] = []
            inventory: dict[int, dict] = {}
            for index, card_id in enumerate(self.card_ids):
                exemplar_id = start + index
                definition = definitions[card_id]
                base_power = definition.get("power_base")
                # Three physical copies of a unit intentionally carry different
                # individual powers, simulating evolved/upgraded exemplars.
                power = (base_power + (index % 3)) if definition.get("kind") == "unit" else 1
                rarity_id = definition.get("rarity_id") or "common"
                ids.append(exemplar_id)
                inventory[exemplar_id] = {
                    "exemplar_id": exemplar_id,
                    "owner_player_id": owner,
                    "user_id": int(owner),
                    "card_id": card_id,
                    "rarity": self.rarity_names[rarity_id],
                    "power": power,
                    "source": "test_fixture",
                    "origin_type": "catalogo",
                    "origin_card_id": "",
                    "is_sacrificable": True,
                }
            self.exemplar_ids_by_player[owner] = ids
            self.inventories_by_player[owner] = inventory

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _save(self, owner: str, deck_id: str, faction: str, leader: str):
        return self.app.save_deck(
            owner_player_id=owner,
            deck_id=deck_id,
            name=f"Deck {owner}",
            card_ids=list(self.card_ids),
            exemplar_ids=list(self.exemplar_ids_by_player[owner]),
            faction_id=faction,
            leader_id=leader,
            owned_exemplars=self.inventories_by_player[owner],
        )

    def test_save_update_get_list_delete_persists_exact_exemplars_with_optimistic_version(self):
        created = self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        self.assertEqual(created["version"], 1)
        self.assertEqual(created["validation"]["card_count"], 30)
        self.assertEqual(created["validation"]["exemplar_count"], 30)
        loaded = self.app.get_deck(PLAYER_A, DECK_A_ID)
        self.assertEqual(loaded["card_ids"], self.card_ids)
        self.assertEqual(loaded["exemplar_ids"], self.exemplar_ids_by_player[PLAYER_A])
        self.assertEqual(len(self.app.list_decks(PLAYER_A)), 1)

        updated = self.app.save_deck(
            owner_player_id=PLAYER_A,
            deck_id=DECK_A_ID,
            name="Deck atualizado",
            card_ids=list(self.card_ids),
            exemplar_ids=list(self.exemplar_ids_by_player[PLAYER_A]),
            faction_id="golden_order",
            leader_id="comandante_fornalha",
            owned_exemplars=self.inventories_by_player[PLAYER_A],
            expected_version=1,
        )
        self.assertEqual(updated["version"], 2)
        with self.assertRaises(PersistenceConflict):
            self.app.save_deck(
                owner_player_id=PLAYER_A,
                deck_id=DECK_A_ID,
                name="Update obsoleto",
                card_ids=list(self.card_ids),
                exemplar_ids=list(self.exemplar_ids_by_player[PLAYER_A]),
                faction_id="golden_order",
                leader_id="comandante_fornalha",
                owned_exemplars=self.inventories_by_player[PLAYER_A],
                expected_version=1,
            )
        self.assertTrue(self.app.delete_deck(PLAYER_A, DECK_A_ID, expected_version=2))
        self.assertIsNone(self.app.get_deck(PLAYER_A, DECK_A_ID))

    def test_save_rejects_missing_physical_exemplar(self):
        insufficient = dict(self.inventories_by_player[PLAYER_A])
        insufficient.pop(self.exemplar_ids_by_player[PLAYER_A][0])
        with self.assertRaises(InvalidOperation):
            self.app.save_deck(
                owner_player_id=PLAYER_A,
                deck_id=DECK_A_ID,
                name="Deck inválido",
                card_ids=list(self.card_ids),
                exemplar_ids=list(self.exemplar_ids_by_player[PLAYER_A]),
                faction_id="golden_order",
                leader_id="comandante_fornalha",
                owned_exemplars=insufficient,
            )
        self.assertIsNone(self.app.get_deck(PLAYER_A, DECK_A_ID))

    def test_competitive_match_uses_the_exact_saved_exemplar_and_power_snapshot(self):
        self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        self._save(PLAYER_B, DECK_B_ID, "dark_moon", "mestre_eclipse")
        result = self.app.create_match_from_saved_decks(
            match_id=2026112801,
            player_ids=[PLAYER_A, PLAYER_B],
            deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
            owned_exemplars_by_player=self.inventories_by_player,
        )
        expected_starter = result["starting_player_id"]
        self.assertIn(expected_starter, [PLAYER_A, PLAYER_B])
        self.assertEqual(result["first_player_selection"], "server_random")
        self.assertEqual(result["initial_hand_size"], 4)
        self.assertTrue(result["exact_exemplar_provenance"])
        self.assertEqual(result["selected_exemplar_count"], 60)
        state = self.app.match_repository.get_match(2026112801)
        self.assertEqual(len(state["instances"]), 60)
        instance_by_exemplar = {
            item["exemplar_id"]: item
            for item in state["instances"].values()
            if item["exemplar_id"] is not None
        }
        expected_ids = set(self.exemplar_ids_by_player[PLAYER_A] + self.exemplar_ids_by_player[PLAYER_B])
        self.assertEqual(set(instance_by_exemplar), expected_ids)
        for owner in (PLAYER_A, PLAYER_B):
            expected_inventory = self.inventories_by_player[owner]
            for exemplar_id in self.exemplar_ids_by_player[owner]:
                instance = instance_by_exemplar[exemplar_id]
                record = expected_inventory[exemplar_id]
                self.assertEqual(instance["owner_player_id"], owner)
                self.assertEqual(instance["card_id"], record["card_id"])
                self.assertEqual(instance["origin_type"], "deck_exemplar")
                if self.catalog.definition_for(record["card_id"])["kind"] == "unit":
                    self.assertEqual(instance["exemplar_snapshot"]["power_base"], record["power"])
                else:
                    self.assertIsNone(instance["exemplar_snapshot"]["power_base"])
                self.assertEqual(
                    instance["exemplar_snapshot"]["rarity_id"],
                    RARITY_IDS[record["rarity"]],
                )
        runtime_view = self.app.view_match(2026112801)
        self.assertEqual(len(runtime_view["players"][PLAYER_A]["hand"]), 4)
        self.assertEqual(len(runtime_view["players"][PLAYER_B]["hand"]), 4)
        self.assertEqual(runtime_view["players"][PLAYER_A]["draw_pile_count"], 26)
        self.assertEqual(runtime_view["players"][PLAYER_B]["draw_pile_count"], 26)
        self.assertEqual(runtime_view["current_player_id"], expected_starter)
        self.assertEqual(runtime_view["energy_by_player"][expected_starter], 1)
        other_player = PLAYER_B if expected_starter == PLAYER_A else PLAYER_A
        self.assertEqual(runtime_view["energy_by_player"][other_player], 0)
        self.assertEqual(runtime_view["match_setup"]["exemplar_snapshot_policy"], "current_power_and_display_rarity_at_match_creation_v1")

    def test_competitive_stats_are_aggregated_per_participant_without_exposing_match_state(self):
        self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        self._save(PLAYER_B, DECK_B_ID, "dark_moon", "mestre_eclipse")
        self.app.create_match_from_saved_decks(
            match_id=2026112899,
            player_ids=[PLAYER_A, PLAYER_B],
            deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
            owned_exemplars_by_player=self.inventories_by_player,
        )
        runtime = self.app.match_repository.get_match_runtime(2026112899)
        runtime["match_winner_player_id"] = PLAYER_A
        with sqlite3.connect(self.root / "matches.sqlite3") as conn:
            conn.execute(
                "UPDATE cartas_gwent_matches SET status='finished' WHERE match_id=?",
                (2026112899,),
            )
            conn.execute(
                "UPDATE card_engine_v2_match_runtime SET runtime_json=? WHERE match_id=?",
                (json.dumps(runtime), 2026112899),
            )
        self.assertEqual(
            self.app.match_repository.get_competitive_stats_for_player(PLAYER_A),
            {"played": 1, "wins": 1, "losses": 0, "draws": 0},
        )
        self.assertEqual(
            self.app.match_repository.get_competitive_stats_for_player(PLAYER_B),
            {"played": 1, "wins": 0, "losses": 1, "draws": 0},
        )
        with self.assertRaises(InvalidOperation):
            self.app.match_repository.get_competitive_stats_for_player("not-a-player")
        async_result = asyncio.run(
            AsyncAlphaGameApplication(self.app).get_competitive_stats_for_player(PLAYER_A)
        )
        self.assertEqual(async_result["wins"], 1)

    def test_primordial_exemplar_is_snapshotted_without_changing_its_power(self):
        inventory_a = {key: dict(value) for key, value in self.inventories_by_player[PLAYER_A].items()}
        exemplar_id = self.exemplar_ids_by_player[PLAYER_A][0]
        original_power = inventory_a[exemplar_id]["power"]
        inventory_a[exemplar_id]["rarity"] = "Primordial"
        self.app.save_deck(
            owner_player_id=PLAYER_A,
            deck_id=DECK_A_ID,
            name="Deck Primordial",
            card_ids=list(self.card_ids),
            exemplar_ids=list(self.exemplar_ids_by_player[PLAYER_A]),
            faction_id="golden_order",
            leader_id="comandante_fornalha",
            owned_exemplars=inventory_a,
        )
        self._save(PLAYER_B, DECK_B_ID, "dark_moon", "mestre_eclipse")
        self.app.create_match_from_saved_decks(
            match_id=2026112806,
            player_ids=[PLAYER_A, PLAYER_B],
            deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
            owned_exemplars_by_player={PLAYER_A: inventory_a, PLAYER_B: self.inventories_by_player[PLAYER_B]},
        )
        state = self.app.match_repository.get_match(2026112806)
        instance = next(item for item in state["instances"].values() if item["exemplar_id"] == exemplar_id)
        self.assertEqual(instance["exemplar_snapshot"]["rarity_id"], "primordial")
        self.assertEqual(instance["exemplar_snapshot"]["power_base"], original_power)

    def test_match_creation_rejects_opponent_deck_lookup_under_wrong_owner(self):
        self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        with self.assertRaises(InvalidOperation):
            self.app.create_match_from_saved_decks(
                match_id=2026112802,
                player_ids=[PLAYER_A, PLAYER_B],
                deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_A_ID},
                owned_exemplars_by_player=self.inventories_by_player,
            )

    def test_matchmaking_rechecks_live_exemplar_inventory_after_deck_was_saved(self):
        self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        self._save(PLAYER_B, DECK_B_ID, "dark_moon", "mestre_eclipse")
        changed_a = dict(self.inventories_by_player[PLAYER_A])
        changed_a.pop(self.exemplar_ids_by_player[PLAYER_A][0])
        live = {PLAYER_A: changed_a, PLAYER_B: self.inventories_by_player[PLAYER_B]}
        with self.assertRaises(InvalidOperation):
            self.app.create_match_from_saved_decks(
                match_id=2026112803,
                player_ids=[PLAYER_A, PLAYER_B],
                deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
                owned_exemplars_by_player=live,
            )

    def test_saved_deck_from_old_schema_without_exemplar_ids_cannot_enter_matchmaking(self):
        # v1 deck databases are upgraded without inventing physical ownership.
        old_path = self.root / "legacy-v1-decks.sqlite3"
        conn = sqlite3.connect(old_path)
        conn.executescript(
            """CREATE TABLE card_engine_v2_deck_marker (
                   marker_id INTEGER PRIMARY KEY CHECK(marker_id=1), engine_id TEXT NOT NULL, schema_version INTEGER NOT NULL);
               INSERT INTO card_engine_v2_deck_marker VALUES(1,'soulsbo-card-engine-v2-decks',1);
               CREATE TABLE saved_alpha_decks (
                   owner_player_id TEXT NOT NULL, deck_id TEXT NOT NULL, name TEXT NOT NULL,
                   card_ids_json TEXT NOT NULL, faction_id TEXT, leader_id TEXT, rules_version TEXT NOT NULL,
                   version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                   PRIMARY KEY(owner_player_id,deck_id));
               INSERT INTO saved_alpha_decks VALUES('1001','old','Old deck','[]',NULL,NULL,'old-v1',1,'t','t');"""
        )
        conn.commit()
        conn.close()
        repo = SQLiteDeckRepository(old_path)
        old_deck = repo.get_deck(PLAYER_A, "old")
        self.assertEqual(old_deck["exemplar_ids"], [])
        self.assertEqual(repo.verify_integrity()["schema_version"], 2)

    def test_cross_player_duplicate_global_exemplar_id_is_rejected(self):
        self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        self._save(PLAYER_B, DECK_B_ID, "dark_moon", "mestre_eclipse")
        inventory_b = dict(self.inventories_by_player[PLAYER_B])
        shared_id = self.exemplar_ids_by_player[PLAYER_A][0]
        replaced_id = self.exemplar_ids_by_player[PLAYER_B][0]
        shared_record = dict(self.inventories_by_player[PLAYER_A][shared_id])
        # Simulate a corrupted/stale cross-user inventory projection carrying the
        # same global primary key twice. Per-player checks pass; global uniqueness
        # must reject the competitive match before any instance is created.
        shared_record["owner_player_id"] = PLAYER_B
        shared_record["user_id"] = int(PLAYER_B)
        inventory_b.pop(replaced_id)
        inventory_b[shared_id] = shared_record
        exemplar_ids_b = list(self.exemplar_ids_by_player[PLAYER_B])
        exemplar_ids_b[0] = shared_id
        self.app.save_deck(
            owner_player_id=PLAYER_B,
            deck_id=DECK_B_ID,
            name="Deck control",
            card_ids=list(self.card_ids),
            exemplar_ids=exemplar_ids_b,
            faction_id="dark_moon",
            leader_id="mestre_eclipse",
            owned_exemplars=inventory_b,
            expected_version=1,
        )
        with self.assertRaisesRegex(InvalidOperation, "exemplar_id_used_by_multiple_players"):
            self.app.create_match_from_saved_decks(
                match_id=2026112804,
                player_ids=[PLAYER_A, PLAYER_B],
                deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
                owned_exemplars_by_player={PLAYER_A: self.inventories_by_player[PLAYER_A], PLAYER_B: inventory_b},
            )

    def test_application_matchmaking_does_not_accept_client_shuffle_seeds(self):
        with self.assertRaises(TypeError):
            self.app.create_match_from_saved_decks(
                match_id=2026112807,
                player_ids=[PLAYER_A, PLAYER_B],
                deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
                owned_exemplars_by_player=self.inventories_by_player,
                shuffle_seeds_by_player={PLAYER_A: 1, PLAYER_B: 2},
            )
        async_app = AsyncAlphaGameApplication(self.app)

        async def run():
            await async_app.create_match_from_saved_decks(
                match_id=2026112808,
                player_ids=[PLAYER_A, PLAYER_B],
                deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
                owned_exemplars_by_player=self.inventories_by_player,
                shuffle_seeds_by_player={PLAYER_A: 1, PLAYER_B: 2},
            )

        with self.assertRaises(TypeError):
            asyncio.run(run())

    def test_player_view_exposes_own_physical_cards_and_hides_opponent_hand(self):
        self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        self._save(PLAYER_B, DECK_B_ID, "dark_moon", "mestre_eclipse")
        self.app.create_match_from_saved_decks(
            match_id=2026112805,
            player_ids=[PLAYER_A, PLAYER_B],
            deck_ids_by_player={PLAYER_A: DECK_A_ID, PLAYER_B: DECK_B_ID},
            owned_exemplars_by_player=self.inventories_by_player,
        )
        view = self.app.view_match_for_player(2026112805, PLAYER_A)
        own_hand = view["players"][PLAYER_A]["hand"]
        opponent = view["players"][PLAYER_B]
        self.assertEqual(len(own_hand), 4)
        self.assertEqual(len({item["instance_id"] for item in own_hand}), 4)
        self.assertTrue(all(item["exemplar_id"] in self.exemplar_ids_by_player[PLAYER_A] for item in own_hand))
        self.assertTrue(all(isinstance(item["exemplar_power_base"], int) or item["exemplar_power_base"] is None for item in own_hand))
        self.assertTrue(opponent["hand_hidden"])
        self.assertEqual(opponent["hand"], [])
        self.assertEqual(opponent["hand_count"], 4)
        self.assertNotIn("exemplar_id", view["players"][PLAYER_B]["board"][0] if opponent["board"] else {})

    def test_legacy_collection_adapters_are_read_only_and_return_exact_ids(self):
        class FakeLegacyDatabase:
            async def coliseu_listar_colecao(self, user_id):
                self.assert_user_id = user_id
                return [
                    {"card_id": "arma_lanca_fornalha", "quantidade": 2},
                    {"card_id": "gwent_especial_egide", "quantidade": 1},
                    {"card_id": "arma_martelo_fornalha", "quantidade": 0},
                ]

            async def coliseu_listar_exemplares(self, user_id):
                self.exemplar_user_id = user_id
                return [
                    {"id": 91, "user_id": user_id, "card_id": "arma_lanca_fornalha", "rarity": "Rara", "power": 5,
                     "source": "pack", "origin_type": "catalogo", "origin_card_id": "", "is_sacrificable": 1},
                    {"id": 92, "user_id": user_id, "card_id": "arma_lanca_fornalha", "rarity": "Épica", "power": 6,
                     "source": "forja", "origin_type": "catalogo", "origin_card_id": "", "is_sacrificable": 1},
                ]

        db = FakeLegacyDatabase()

        async def run():
            return await legacy_collection_counts(db, PLAYER_A), await legacy_collection_exemplars(db, PLAYER_A)

        counts, exemplars = asyncio.run(run())
        self.assertEqual(counts, {"arma_lanca_fornalha": 2, "gwent_especial_egide": 1})
        self.assertEqual(set(exemplars), {91, 92})
        self.assertEqual(exemplars[92]["power"], 6)
        self.assertEqual(exemplars[92]["owner_player_id"], PLAYER_A)

    def test_deck_repository_refuses_an_unmarked_nonempty_database(self):
        bad_path = self.root / "legacy-like.sqlite3"
        conn = sqlite3.connect(bad_path)
        conn.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        with self.assertRaises(ValueError):
            SQLiteDeckRepository(bad_path)

    def test_repository_integrity_is_green(self):
        result = self.app.verify_integrity()
        self.assertEqual(result["deck_repository"]["integrity_check"], "ok")
        self.assertEqual(result["deck_repository"]["foreign_key_violations"], 0)
        self.assertEqual(result["deck_repository"]["schema_version"], 2)
        self.assertEqual(result["match_repository"]["integrity_check"], "ok")

    def test_async_facade_offloads_operations(self):
        self._save(PLAYER_A, DECK_A_ID, "golden_order", "comandante_fornalha")
        async_app = AsyncAlphaGameApplication(self.app)

        async def run():
            deck = await async_app.get_deck(PLAYER_A, DECK_A_ID)
            listed = await async_app.list_decks(PLAYER_A)
            return deck, listed

        deck, listed = asyncio.run(run())
        self.assertEqual(deck["deck_id"], DECK_A_ID)
        self.assertEqual(deck["exemplar_ids"], self.exemplar_ids_by_player[PLAYER_A])
        self.assertEqual(len(listed), 1)

    def test_async_action_surface_rejects_private_or_unregistered_method_names(self):
        async_app = AsyncAlphaGameApplication(self.app)

        async def run():
            await async_app.execute_match_action("_close_round", 1)

        with self.assertRaises(InvalidOperation):
            asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
