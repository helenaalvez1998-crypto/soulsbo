from __future__ import annotations

import ast
import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path

from sistemas.card_engine_v2.application import legacy_collection_exemplars


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _legacy_exemplar_sql() -> tuple[str, str]:
    """Extract the exact SQL string literals used by Database.coliseu_listar_exemplares."""
    tree = ast.parse((PROJECT_ROOT / "database.py").read_text(encoding="utf-8"))
    database_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Database"
    )
    method = next(
        node for node in database_class.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "coliseu_listar_exemplares"
    )
    sql_literals = []
    for node in ast.walk(method):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "_all" or not node.args:
            continue
        value = node.args[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            sql_literals.append(value.value)
    if len(sql_literals) != 2:
        raise AssertionError("Database.coliseu_listar_exemplares must retain its two explicit SELECT queries")
    # ast.walk traverses nested nodes breadth-first; order by bind shape, not walk order.
    filtered = next(sql for sql in sql_literals if "card_id=?" in sql)
    complete = next(sql for sql in sql_literals if "card_id=?" not in sql)
    return filtered, complete


class ReadOnlyLegacyDatabaseContract:
    def __init__(self, connection: sqlite3.Connection, queries: tuple[str, str]):
        self.connection = connection
        self.queries = queries

    async def coliseu_listar_exemplares(self, user_id: int, card_id: str | None = None):
        sql = self.queries[0] if card_id else self.queries[1]
        args = (int(user_id), str(card_id)) if card_id else (int(user_id),)
        return self.connection.execute(sql, args).fetchall()


class LegacyCollectionSqlContractTests(unittest.TestCase):
    def test_exact_legacy_query_projects_physical_exemplars_into_v2(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.sqlite3"
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            connection.execute(
                """CREATE TABLE cartas_exemplares (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    card_id TEXT NOT NULL,
                    rarity TEXT NOT NULL,
                    power INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    origin_type TEXT NOT NULL,
                    origin_card_id TEXT NOT NULL,
                    is_sacrificable INTEGER NOT NULL,
                    obtained_at TEXT NOT NULL
                )"""
            )
            connection.executemany(
                "INSERT INTO cartas_exemplares VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    (501, 1001, "unit_alpha", "Primordial", 9, "drop", "catalog", "", 1, "2026-11-28"),
                    (502, 1001, "unit_beta", "Rara", 4, "reward", "catalog", "", 1, "2026-11-28"),
                    (503, 2002, "unit_alpha", "Comum", 2, "drop", "catalog", "", 1, "2026-11-28"),
                ],
            )
            connection.commit()
            connection.execute("PRAGMA query_only=ON")
            legacy = ReadOnlyLegacyDatabaseContract(connection, _legacy_exemplar_sql())
            projection = asyncio.run(legacy_collection_exemplars(legacy, 1001))
            self.assertEqual(set(projection), {501, 502})
            self.assertEqual(projection[501]["owner_player_id"], "1001")
            self.assertEqual(projection[501]["card_id"], "unit_alpha")
            self.assertEqual(projection[501]["rarity"], "Primordial")
            self.assertEqual(projection[501]["power"], 9)
            self.assertEqual(projection[501]["exemplar_id"], 501)
            connection.close()

    def test_card_filter_uses_the_exact_filtered_query_and_does_not_cross_owners(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.sqlite3"
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            connection.execute(
                """CREATE TABLE cartas_exemplares (
                    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, card_id TEXT NOT NULL,
                    rarity TEXT NOT NULL, power INTEGER NOT NULL, source TEXT NOT NULL,
                    origin_type TEXT NOT NULL, origin_card_id TEXT NOT NULL,
                    is_sacrificable INTEGER NOT NULL, obtained_at TEXT NOT NULL
                )"""
            )
            connection.executemany(
                "INSERT INTO cartas_exemplares VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    (601, 1001, "unit_alpha", "Comum", 3, "drop", "catalog", "", 1, "2026-11-28"),
                    (602, 1001, "unit_beta", "Rara", 5, "drop", "catalog", "", 1, "2026-11-28"),
                    (603, 2002, "unit_alpha", "Comum", 7, "drop", "catalog", "", 1, "2026-11-28"),
                ],
            )
            connection.commit()
            connection.execute("PRAGMA query_only=ON")
            legacy = ReadOnlyLegacyDatabaseContract(connection, _legacy_exemplar_sql())
            rows = asyncio.run(legacy.coliseu_listar_exemplares(1001, "unit_alpha"))
            self.assertEqual([int(row["id"]) for row in rows], [601])
            self.assertEqual(int(rows[0]["user_id"]), 1001)
            connection.close()


if __name__ == "__main__":
    unittest.main()
