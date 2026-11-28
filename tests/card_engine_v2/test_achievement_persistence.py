from __future__ import annotations

import sqlite3
import unittest
from contextlib import asynccontextmanager

from sistemas.card_game_achievements import get_user_achievements
from sistemas.cartas import CARTAS_POR_ID


class _AsyncConnection:
    def __init__(self, conn):
        self.conn = conn

    async def execute(self, sql, args=()):
        return self.conn.execute(sql, args)


class _TransactionSession:
    def __init__(self, conn):
        self.conn = _AsyncConnection(conn)

    async def _one(self, sql, args=()):
        return self.conn.conn.execute(sql, args).fetchone()


class _AchievementDatabase:
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
            yield _TransactionSession(self.conn)
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise


class AchievementPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = _AchievementDatabase()
        self.uid = 1001

    async def asyncTearDown(self):
        self.db.conn.close()

    async def test_progress_is_derived_and_unlocked_achievement_is_permanent(self):
        common_ids = [
            str(card.id) for card in CARTAS_POR_ID.values()
            if str(getattr(card, "raridade", "")).casefold() in {"comum", "common"}
        ]
        exemplars = [(i + 1, card_id, "Comum") for i, card_id in enumerate(common_ids)]
        for index in range(60):
            card_id = common_ids[index % len(common_ids)] if common_ids else "fixture_card"
            exemplars.append((len(exemplars) + 1, card_id, "Singular" if index == 0 else "Comum"))
        self.db.conn.executemany(
            "INSERT INTO cartas_exemplares(id,user_id,card_id,rarity,power) VALUES(?,?,?, ?,5)",
            [(eid, self.uid, card_id, rarity) for eid, card_id, rarity in exemplars],
        )
        self.db.conn.executemany(
            "INSERT INTO cartas_movimentacoes(user_id,action,exemplar_id) VALUES(?,?,?)",
            [(self.uid, "evolucao", i) for i in range(1, 11)],
        )
        self.db.conn.execute(
            "INSERT INTO cartas_gwent_rankings(user_id,wins,losses,draws) VALUES(?,?,?,?)",
            (self.uid, 1, 10, 2),
        )
        self.db.conn.commit()

        result = await get_user_achievements(
            self.db, self.uid, v2_match_stats={"played": 87, "wins": 1}
        )
        by_key = {item["key"]: item for item in result["achievements"]}
        self.assertTrue(by_key["first_blood"]["unlocked"])
        self.assertTrue(by_key["collector"]["unlocked"])
        self.assertTrue(by_key["forger"]["unlocked"])
        self.assertTrue(by_key["legend"]["unlocked"])
        self.assertTrue(by_key["dedicado"]["unlocked"])
        self.assertEqual(result["metrics"]["completed_matches"], 100)

        self.db.conn.execute("DELETE FROM cartas_exemplares WHERE user_id=?", (self.uid,))
        self.db.conn.commit()
        second = await get_user_achievements(self.db, self.uid)
        collector = next(item for item in second["achievements"] if item["key"] == "collector")
        self.assertTrue(collector["unlocked"])
        self.assertEqual(collector["progress"], collector["total"])

    async def test_client_cannot_supply_progress_and_untracked_goals_are_not_persisted(self):
        result = await get_user_achievements(self.db, self.uid)
        keys = {row[0] for row in self.db.conn.execute("SELECT conquista FROM cartas_conquistas").fetchall()}
        self.assertNotIn("apostador", keys)
        self.assertNotIn("survivor", keys)
        self.assertIn("first_blood", keys)
        self.assertFalse(next(item for item in result["achievements"] if item["key"] == "apostador")["unlocked"])


if __name__ == "__main__":
    unittest.main()
