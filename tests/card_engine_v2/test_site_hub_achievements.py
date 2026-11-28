from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from site_hub import registrar_rotas


class _ConnProxy:
    def __init__(self, conn):
        self.conn = conn

    async def execute(self, sql, args=()):
        return self.conn.execute(sql, args)


class _Session:
    def __init__(self, conn):
        self.conn = _ConnProxy(conn)

    async def _one(self, sql, args=()):
        return self.conn.conn.execute(sql, args).fetchone()


class _FakeDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE cartas_exemplares(id INTEGER PRIMARY KEY,user_id INTEGER,card_id TEXT,rarity TEXT,power INTEGER);
            CREATE TABLE cartas_movimentacoes(id INTEGER PRIMARY KEY,user_id INTEGER,action TEXT,exemplar_id INTEGER);
            CREATE TABLE cartas_gwent_rankings(user_id INTEGER PRIMARY KEY,wins INTEGER,losses INTEGER,draws INTEGER);
            CREATE TABLE cartas_conquistas(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,conquista TEXT,progresso INTEGER,total INTEGER,desbloqueada_em TEXT NOT NULL DEFAULT '');
            """
        )

    async def _one(self, sql, args=()):
        return self.conn.execute(sql, args).fetchone()

    async def _all(self, sql, args=()):
        return self.conn.execute(sql, args).fetchall()

    @asynccontextmanager
    async def transaction(self):
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield _Session(self.conn)
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise

    def close(self):
        self.conn.close()


class _FakeBot:
    def __init__(self):
        self.db = _FakeDB()

    def _api_user_id(self, request):
        raw = request.cookies.get("test-uid", "")
        return int(raw) if raw.isdigit() else None

    def _api_origin_ok(self, request):
        return request.headers.get("Origin") == f"{request.scheme}://{request.host}"


class SiteHubAchievementsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = _FakeBot()
        self.app = web.Application()
        registrar_rotas(self.bot, self.app)
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.bot.db.close()

    async def test_authenticated_achievements_endpoint_returns_server_progress(self):
        self.client.session.cookie_jar.update_cookies({"test-uid": "1001"})
        response = await self.client.get("/api/gwent/conquistas/list")
        self.assertEqual(response.status, 200)
        persisted_before_sync = self.bot.db.conn.execute("SELECT COUNT(*) FROM cartas_conquistas").fetchone()[0]
        self.assertEqual(persisted_before_sync, 0, "GET de leitura não deve persistir progresso")
        payload = await response.json()
        keys = {item["key"] for item in payload["achievements"]}
        self.assertIn("first_blood", keys)
        self.assertIn("collector", keys)
        self.assertGreaterEqual(payload["summary"]["total"], 8)

    async def test_anonymous_achievements_endpoint_requires_discord_session(self):
        response = await self.client.get("/api/gwent/conquistas/list")
        self.assertEqual(response.status, 401)

    async def test_client_cannot_register_forged_progress(self):
        self.client.session.cookie_jar.update_cookies({"test-uid": "1001"})
        origin = str(self.client.make_url("/").origin())
        response = await self.client.post(
            "/api/gwent/conquistas/registrar",
            json={"key": "collector", "progress": 999999, "total": 1},
            headers={"Origin": origin},
        )
        self.assertEqual(response.status, 400)
        sync = await self.client.post(
            "/api/gwent/conquistas/registrar", json={}, headers={"Origin": origin}
        )
        self.assertEqual(sync.status, 200)

    async def test_malformed_achievement_sync_body_is_rejected(self):
        self.client.session.cookie_jar.update_cookies({"test-uid": "1001"})
        origin = str(self.client.make_url("/").origin())
        response = await self.client.post(
            "/api/gwent/conquistas/registrar",
            data="{invalid-json",
            headers={"Origin": origin, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status, 400)
        count = self.bot.db.conn.execute("SELECT COUNT(*) FROM cartas_conquistas").fetchone()[0]
        self.assertEqual(count, 0)

    async def test_incomplete_bets_and_risky_evolution_fail_closed_without_database_writes(self):
        self.client.session.cookie_jar.update_cookies({"test-uid": "1001"})
        origin = str(self.client.make_url("/").origin())
        for path in (
            "/api/gwent/apostas/denarios",
            "/api/gwent/apostas/cartas",
            "/api/gwent/apostas/torneio",
            "/api/gwent/evolucao",
            "/api/gwent/evolucao/protecao",
        ):
            response = await self.client.post(path, json={"value": 100}, headers={"Origin": origin})
            self.assertEqual(response.status, 503, path)
        count = self.bot.db.conn.execute("SELECT COUNT(*) FROM cartas_conquistas").fetchone()[0]
        self.assertEqual(count, 0)

    async def test_achievements_and_bets_pages_are_real_pages(self):
        achievements = await self.client.get("/conquistas")
        bets = await self.client.get("/apostas")
        self.assertEqual(achievements.status, 200)
        self.assertIn("Conquistas do Soulsbo", await achievements.text())
        self.assertEqual(bets.status, 200)
        self.assertIn("temporariamente fechado", (await bets.text()).lower())


if __name__ == "__main__":
    unittest.main()
