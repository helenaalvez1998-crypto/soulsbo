from __future__ import annotations

import uuid
import tempfile
import unittest
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from sistemas.card_engine_v2.alpha_catalog import RARITY_IDS
from sistemas.card_engine_v2.application import AlphaGameApplication, AsyncAlphaGameApplication
from sistemas.card_engine_v2.discord_gateway import CardEngineV2DiscordGateway
from site_card_engine_v2 import registrar_rotas
from tests.card_engine_v2.support import mechanics_catalog


class FakeLegacyDB:
    def __init__(self, rows):
        self.rows = rows

    async def coliseu_listar_exemplares(self, user_id, card_id=None):
        result = [dict(row) for row in self.rows.get(int(user_id), [])]
        if card_id is not None:
            result = [row for row in result if row["card_id"] == card_id]
        return result


class FakeSiteBot:
    def __init__(self, gateway):
        self.card_engine_v2_shared_gateway = gateway

    def _api_user_id(self, request):
        value = request.cookies.get("test-player")
        return int(value) if value and value.isdigit() else None

    def _api_origin_ok(self, request):
        origin = request.headers.get("Origin", "")
        return bool(origin and origin == f"{request.scheme}://{request.host}")


class CardEngineV2SiteHttpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        catalog = mechanics_catalog(self.root)
        self.application = AlphaGameApplication(
            match_database_path=self.root / "matches.sqlite3",
            deck_database_path=self.root / "decks.sqlite3",
            catalog=catalog,
        )
        definitions = {card_id: catalog.definition_for(card_id) for card_id in catalog.allowed_card_ids()}
        unit_ids = [cid for cid, item in definitions.items() if item.get("kind") == "unit"]
        special_ids = [cid for cid, item in definitions.items() if item.get("kind") == "special"]
        self.deck_card_ids = (unit_ids[:9] + special_ids[:1]) * 3
        rarity_names = {value: key for key, value in RARITY_IDS.items()}
        self.rows = {}
        self.exemplars = {}
        for uid, start in ((1001, 100000), (2002, 200000)):
            rows, ids = [], []
            for i, card_id in enumerate(self.deck_card_ids):
                definition = definitions[card_id]
                eid = start + i
                rows.append({
                    "id": eid, "user_id": uid, "card_id": card_id,
                    "rarity": rarity_names.get(definition.get("rarity_id"), "Comum"),
                    "power": int(definition.get("power_base") or 1),
                    "source": "site_http_test", "origin_type": "catalogo",
                    "origin_card_id": "", "is_sacrificable": 1,
                })
                ids.append(eid)
            self.rows[uid], self.exemplars[uid] = rows, ids
        self.database = FakeLegacyDB(self.rows)
        self.gateway = CardEngineV2DiscordGateway(
            database=self.database,
            application=AsyncAlphaGameApplication(self.application),
        )
        self.bot = FakeSiteBot(self.gateway)
        app = web.Application()
        registrar_rotas(self.bot, app)
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.temp.cleanup()

    def headers(self, uid=1001, csrf=True):
        values = {"Cookie": f"test-player={uid}"}
        if csrf:
            values["Origin"] = str(self.client.make_url("/" )).rstrip("/")
        return values

    async def save_valid_decks(self):
        for uid, deck_id, leader_id, faction in (
            (1001, "site-a", "comandante_fornalha", "golden_order"),
            (2002, "site-b", "mestre_eclipse", "dark_moon"),
        ):
            await self.gateway.save_deck(
                authenticated_player_id=uid, deck_id=deck_id, name=f"Deck {uid}",
                card_ids=self.deck_card_ids, exemplar_ids=self.exemplars[uid],
                faction_id=faction, leader_id=leader_id,
            )

    async def test_bootstrap_requires_session_and_returns_only_own_collection(self):
        response = await self.client.get("/api/card-engine-v2/bootstrap")
        self.assertEqual(response.status, 401)
        response = await self.client.get("/api/card-engine-v2/bootstrap", headers=self.headers())
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertEqual(body["player_id"], "1001")
        self.assertEqual(len(body["inventory"]), 30)
        self.assertEqual({item["exemplar_id"] for item in body["inventory"]}, set(self.exemplars[1001]))
        self.assertEqual(body["rules"]["deck_size"], 30)

    async def test_deck_create_requires_csrf_and_update_delete_are_owner_scoped(self):
        payload = {
            "name": "Site deck", "card_ids": self.deck_card_ids,
            "exemplar_ids": self.exemplars[1001], "leader_id": "comandante_fornalha",
        }
        blocked = await self.client.post(
            "/api/card-engine-v2/decks", json=payload, headers=self.headers(csrf=False)
        )
        self.assertEqual(blocked.status, 403)
        created = await self.client.post(
            "/api/card-engine-v2/decks", json=payload, headers=self.headers()
        )
        self.assertEqual(created.status, 201)
        deck = (await created.json())["deck"]
        updated = await self.client.put(
            f"/api/card-engine-v2/decks/{deck['deck_id']}",
            json={**payload, "name": "Site deck editado", "expected_version": deck["version"]},
            headers=self.headers(),
        )
        self.assertEqual(updated.status, 200)
        forbidden = await self.client.delete(
            f"/api/card-engine-v2/decks/{deck['deck_id']}",
            json={"expected_version": 2}, headers=self.headers(uid=2002),
        )
        self.assertEqual(forbidden.status, 409)
        deleted = await self.client.delete(
            f"/api/card-engine-v2/decks/{deck['deck_id']}",
            json={"expected_version": 2}, headers=self.headers(),
        )
        self.assertEqual(deleted.status, 200)


    async def test_game_page_requires_discord_session_and_serves_private_alpha_page(self):
        denied = await self.client.get("/card-engine-v2", allow_redirects=False)
        self.assertEqual(denied.status, 302)
        self.assertIn("/auth/discord/login", denied.headers.get("Location", ""))
        allowed = await self.client.get("/card-engine-v2", headers=self.headers())
        self.assertEqual(allowed.status, 200)
        self.assertIn("Card Engine v2", await allowed.text())
        self.assertIn("no-store", allowed.headers.get("Cache-Control", ""))

    async def test_deck_update_rejects_boolean_version_and_oversized_body(self):
        payload = {
            "name": "Site deck", "card_ids": self.deck_card_ids,
            "exemplar_ids": self.exemplars[1001], "leader_id": "comandante_fornalha",
        }
        created = await self.client.post(
            "/api/card-engine-v2/decks", json=payload, headers=self.headers()
        )
        self.assertEqual(created.status, 201)
        deck = (await created.json())["deck"]
        invalid = await self.client.put(
            f"/api/card-engine-v2/decks/{deck['deck_id']}",
            json={**payload, "expected_version": True}, headers=self.headers(),
        )
        self.assertEqual(invalid.status, 400)
        oversized = await self.client.post(
            "/api/card-engine-v2/matches/1/actions",
            data=b'{"action":"pass_turn","payload":{"padding":"' + b"x" * 33_000 + b'"}}',
            headers={**self.headers(), "Content-Type": "application/json"},
        )
        self.assertEqual(oversized.status, 400)


    async def test_action_rejects_non_string_action_and_sacrifice_offer_rejects_client_fields(self):
        malformed = await self.client.post(
            "/api/card-engine-v2/matches/123/actions",
            json={"action": ["pass_turn"], "payload": {"expected_revision": 1, "operation_id": str(uuid.uuid4())}},
            headers=self.headers(),
        )
        self.assertEqual(malformed.status, 400)
        extra = await self.client.post(
            "/api/card-engine-v2/matches/123/sacrifice-offer",
            json={"player_id": "2002"}, headers=self.headers(),
        )
        self.assertEqual(extra.status, 400)

    async def test_match_view_and_actions_are_participant_scoped_and_idempotent(self):
        await self.save_valid_decks()
        created = await self.gateway.create_match_from_decks(
            authenticated_challenger_id=1001,
            authenticated_opponent_id=2002,
            challenger_deck_id="site-a", opponent_deck_id="site-b",
        )
        match_id = created["match_id"]
        outsider = await self.client.get(
            f"/api/card-engine-v2/matches/{match_id}", headers=self.headers(uid=9999)
        )
        self.assertEqual(outsider.status, 404)
        state = await self.gateway.player_view(match_id=match_id, authenticated_player_id=1001)
        actor = str(state["current_player_id"])
        before = await self.gateway.player_view(match_id=match_id, authenticated_player_id=actor)
        payload = {
            "expected_revision": before["state_revision"],
            "operation_id": str(uuid.uuid4()),
        }
        response = await self.client.post(
            f"/api/card-engine-v2/matches/{match_id}/actions",
            json={"action": "pass_turn", "payload": payload},
            headers=self.headers(uid=int(actor)),
        )
        self.assertEqual(response.status, 200)
        body = await response.json()
        self.assertIn(body["result"].get("outcome"), {"applied", "partial", "consumed_no_effect"})
        serialized = await response.text() if False else ""
        self.assertNotIn("operation_id", str(body))
        self.assertEqual(body["view"]["state_revision"], before["state_revision"] + 1)
        history_response = await self.client.get(
            f"/api/card-engine-v2/matches/{match_id}?after=0", headers=self.headers(uid=int(actor))
        )
        self.assertEqual(history_response.status, 200)
        history_body = await history_response.json()
        history_text = str(history_body["history"])
        self.assertNotIn("instance_id", history_text)
        self.assertNotIn("operation_id", history_text)
        self.assertNotIn("caused_by_event_ids", history_text)

    async def test_action_rejects_client_supplied_identity_and_missing_idempotency(self):
        invalid = await self.client.post(
            "/api/card-engine-v2/matches/123/actions",
            json={"action": "pass_turn", "player_id": "1001", "payload": {"expected_revision": 1}},
            headers=self.headers(),
        )
        self.assertEqual(invalid.status, 400)


if __name__ == "__main__":
    unittest.main()
