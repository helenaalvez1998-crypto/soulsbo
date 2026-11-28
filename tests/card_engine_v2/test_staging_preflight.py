from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.card_engine_v2_staging_preflight import EXPECTED_PACKAGES, run_preflight


class CardEngineV2StagingPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data_dir = self.root / "persistent-data"
        self.data_dir.mkdir()
        self.db_path = self.data_dir / "colizeu.db"
        conn = sqlite3.connect(self.db_path)
        conn.execute(
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
        conn.execute(
            "INSERT INTO cartas_exemplares VALUES (1, 123, 'card-a', 'Comum', 3, 'test', 'catalog', '', 1, '2026-11-28')"
        )
        conn.commit()
        conn.close()

        # Minimal project surface required by the preflight's static wiring checks.
        for rel in (
            "bot.py", "database.py", "site_hub.py", "site_card_engine_v2.py",
            "cogs/painel_jogo.py", "cogs/card_engine_v2_ui.py",
            "sistemas/card_engine_v2/discord_gateway.py",
            "site/card-engine-v2.html", "site/assets/card-engine-v2.js",
        ):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        (self.root / "bot.py").write_text(
            '"cogs.painel_jogo"\n"/auth/discord/callback"\n'
            "intents.message_content = True\nintents.members = True\nintents.presences = True\n",
            encoding="utf-8",
        )
        (self.root / "cogs/painel_jogo.py").write_text("/card-engine-v2", encoding="utf-8")
        (self.root / "site_hub.py").write_text("registrar_card_engine_v2", encoding="utf-8")
        self.env = {
            "DISCORD_TOKEN": "test-bot-token-not-a-real-secret",
            "DISCORD_OAUTH_CLIENT_ID": "123456789012345678",
            "DISCORD_OAUTH_CLIENT_SECRET": "test-oauth-secret",
            "DISCORD_OAUTH_REDIRECT_URI": "https://staging.example.com/auth/discord/callback",
            "SOULSBOT_WEB_SESSION_SECRET": "x" * 64,
            "SOULSBOT_PUBLIC_URL": "https://staging.example.com",
            "DATA_DIR": str(self.data_dir),
            "DB_PATH": str(self.db_path),
        }
        self.versions = dict(EXPECTED_PACKAGES)

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_staging_configuration_passes_without_printing_secrets(self):
        report = run_preflight(self.root, environ=self.env, installed_versions=self.versions, discord_probe={"ok": True})
        self.assertTrue(report["ready"], report["checks"])
        self.assertEqual(report["summary"]["blockers"], 0)
        self.assertTrue(report["security"]["database_opened_read_only"])
        self.assertFalse(report["security"]["secrets_printed"])
        self.assertFalse(report["security"]["writes_to_application_database"])
        self.assertTrue(any(item["name"] == "database:collection_schema" and item["status"] == "pass" for item in report["checks"]))

    def test_missing_dependencies_and_discord_credentials_block_readiness(self):
        versions = dict(self.versions)
        versions["discord.py"] = None
        versions["aiosqlite"] = None
        env = dict(self.env)
        for key in ("DISCORD_TOKEN", "DISCORD_OAUTH_CLIENT_SECRET"):
            env.pop(key)
        report = run_preflight(self.root, environ=env, installed_versions=versions, discord_probe={"ok": False})
        self.assertFalse(report["ready"])
        self.assertGreaterEqual(report["summary"]["blockers"], 4)
        rendered = str(report)
        self.assertNotIn(self.env["DISCORD_OAUTH_CLIENT_SECRET"], rendered)
        self.assertNotIn(self.env["SOULSBOT_WEB_SESSION_SECRET"], rendered)

    def test_redirect_uri_mismatch_is_blocked(self):
        env = dict(self.env)
        env["DISCORD_OAUTH_REDIRECT_URI"] = "https://wrong.example.com/auth/discord/callback"
        report = run_preflight(self.root, environ=env, installed_versions=self.versions, discord_probe={"ok": True})
        self.assertFalse(report["ready"])
        self.assertTrue(any(item["name"] == "url:DISCORD_OAUTH_REDIRECT_URI" and item["status"] == "block" for item in report["checks"]))

    def test_session_secret_must_be_independent_and_long_enough(self):
        env = dict(self.env)
        env["SOULSBOT_WEB_SESSION_SECRET"] = env["DISCORD_TOKEN"]
        report = run_preflight(self.root, environ=env, installed_versions=self.versions, discord_probe={"ok": True})
        self.assertFalse(report["ready"])
        self.assertTrue(any(item["name"] == "secret:session_key_separation" and item["status"] == "block" for item in report["checks"]))

    def test_database_is_read_only_and_missing_schema_is_blocked(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DROP TABLE cartas_exemplares")
        conn.commit()
        conn.close()
        report = run_preflight(self.root, environ=self.env, installed_versions=self.versions, discord_probe={"ok": True})
        self.assertFalse(report["ready"])
        self.assertTrue(any(item["name"] == "database:collection_schema" and item["status"] == "block" for item in report["checks"]))

    def test_database_file_is_not_modified_by_preflight(self):
        before = self.db_path.read_bytes()
        run_preflight(self.root, environ=self.env, installed_versions=self.versions, discord_probe={"ok": True})
        after = self.db_path.read_bytes()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
