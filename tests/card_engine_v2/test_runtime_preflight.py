from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.runtime_preflight import EXACT_DISTRIBUTIONS, RANGED_DISTRIBUTIONS, validate_runtime


class RuntimePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in ("bot.py", "requirements.txt", "site_hub.py", "site_card_engine_v2.py", "cogs/card_engine_v2_ui.py"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# fixture\n", encoding="utf-8")
        faq_fixture = self.root / "dados" / "nara_faq.json"
        faq_fixture.parent.mkdir(parents=True, exist_ok=True)
        faq_fixture.write_text('{"intents": [{"intent": "fixture"}]}', encoding="utf-8")
        self.data_dir = self.root / "persistent"
        self.database = self.data_dir / "colizeu.db"
        self.data_dir.mkdir()
        conn = sqlite3.connect(self.database)
        conn.executescript(
            "CREATE TABLE users(user_id INTEGER PRIMARY KEY);"
            "CREATE TABLE cartas_exemplares(id INTEGER PRIMARY KEY,user_id INTEGER,card_id TEXT,rarity TEXT,power INTEGER);"
            "CREATE TABLE cartas_colecao(user_id INTEGER,card_id TEXT,quantidade INTEGER);"
        )
        conn.commit()
        conn.close()
        self.environment = {
            "DISCORD_TOKEN": "test-discord-token-value",
            "DISCORD_OAUTH_CLIENT_ID": "123456789",
            "DISCORD_OAUTH_CLIENT_SECRET": "test-oauth-secret",
            "DISCORD_OAUTH_REDIRECT_URI": "https://soulsbo.test/auth/discord/callback",
            "SOULSBOT_WEB_SESSION_SECRET": "independent-session-secret-material-0001",
            "SOULSBOT_PUBLIC_URL": "https://soulsbo.test",
            "DATA_DIR": str(self.data_dir),
            "DB_PATH": str(self.database),
            "PORT": "8080",
        }
        self.versions = {**EXACT_DISTRIBUTIONS, **{name: "1.40.0" if name == "boto3" else "4.3.0" for name in RANGED_DISTRIBUTIONS}}

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_runtime_has_no_blockers(self):
        checks = validate_runtime(self.root, self.environment, distribution_versions=self.versions)
        self.assertFalse([item for item in checks if item["status"] == "block"])
        self.assertTrue(any(item["name"] == "legacy_database" and item["status"] == "pass" for item in checks))

    def test_wrong_callback_and_shared_session_secret_block_runtime(self):
        env = dict(self.environment)
        env["DISCORD_OAUTH_REDIRECT_URI"] = "https://other.test/auth/discord/callback"
        env["SOULSBOT_WEB_SESSION_SECRET"] = env["DISCORD_TOKEN"]
        checks = validate_runtime(self.root, env, distribution_versions=self.versions)
        blocked = {item["name"] for item in checks if item["status"] == "block"}
        self.assertIn("oauth_redirect", blocked)
        self.assertIn("session_secret", blocked)

    def test_example_domain_placeholders_are_rejected_even_when_urls_match(self):
        env = dict(self.environment)
        env["SOULSBOT_PUBLIC_URL"] = "https://SEU-DOMINIO"
        env["DISCORD_OAUTH_REDIRECT_URI"] = "https://SEU-DOMINIO/auth/discord/callback"
        checks = validate_runtime(self.root, env, distribution_versions=self.versions)
        blocked = {item["name"] for item in checks if item["status"] == "block"}
        self.assertIn("env:SOULSBOT_PUBLIC_URL", blocked)
        self.assertIn("env:DISCORD_OAUTH_REDIRECT_URI", blocked)
        self.assertIn("public_url", blocked)
        self.assertIn("oauth_redirect", blocked)

    def test_public_url_rejects_path_prefix_and_query(self):
        env = dict(self.environment)
        env["SOULSBOT_PUBLIC_URL"] = "https://soulsbo.test/app?mode=preview"
        env["DISCORD_OAUTH_REDIRECT_URI"] = "https://soulsbo.test/app?mode=preview/auth/discord/callback"
        checks = validate_runtime(self.root, env, distribution_versions=self.versions)
        blocked = {item["name"] for item in checks if item["status"] == "block"}
        self.assertIn("public_url", blocked)
        self.assertIn("oauth_redirect", blocked)

    def test_missing_pinned_distribution_blocks_runtime(self):
        versions = dict(self.versions)
        versions["discord.py"] = ""
        checks = validate_runtime(self.root, self.environment, distribution_versions=versions)
        self.assertTrue(any(item["name"] == "dependency:discord.py" and item["status"] == "block" for item in checks))

    def test_absent_database_requires_explicit_empty_install_flag(self):
        env = dict(self.environment)
        self.database.unlink()
        blocked = validate_runtime(self.root, env, distribution_versions=self.versions)
        self.assertTrue(any(item["name"] == "legacy_database" and item["status"] == "block" for item in blocked))
        env["SOULSBOT_ALLOW_EMPTY_DATABASE"] = "true"
        warned = validate_runtime(self.root, env, distribution_versions=self.versions)
        item = next(item for item in warned if item["name"] == "legacy_database")
        self.assertEqual(item["status"], "warn")

    def test_database_outside_persistent_data_directory_is_blocked(self):
        env = dict(self.environment)
        env["DB_PATH"] = str(self.root / "ephemeral" / "colizeu.db")
        checks = validate_runtime(self.root, env, distribution_versions=self.versions)
        item = next(item for item in checks if item["name"] == "database_persistence")
        self.assertEqual(item["status"], "block")

    def test_incompatible_or_corrupt_database_blocks_runtime(self):
        conn = sqlite3.connect(self.database)
        conn.execute("DROP TABLE cartas_exemplares")
        conn.commit()
        conn.close()
        checks = validate_runtime(self.root, self.environment, distribution_versions=self.versions)
        self.assertTrue(any(item["name"] == "legacy_database" and item["status"] == "block" for item in checks))


if __name__ == "__main__":
    unittest.main()
