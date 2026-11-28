#!/usr/bin/env python3
"""Testes locais do snapshot SQLite, export DB sanitizado, listagem R2 e reconciliação.

Usa SQLite temporário e cliente S3 falso; não acessa produção ou rede.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Não foi possível carregar {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


snapshot = load_script("snapshot_sqlite_readonly", "snapshot-sqlite-readonly-v0.1.py")
db_audit = load_script("audit_production_card_db", "audit-production-card-db-v0.1.py")
r2_inventory = load_script("inventory_r2_readonly", "inventory-r2-readonly-v0.1.py")
reconcile = load_script("reconcile_production_card_assets", "reconcile-production-card-assets-v0.1.py")


class FakePaginator:
    def __init__(self, records):
        self.records = records
        self.calls = []

    def paginate(self, **kwargs):
        self.calls.append(kwargs)
        prefix = kwargs.get("Prefix")
        contents = self.records
        if prefix:
            contents = [item for item in contents if item["Key"].startswith(prefix)]
        yield {"Contents": contents}


class FakeS3Client:
    def __init__(self, records):
        self.paginator = FakePaginator(records)
        self.requested_operation = None

    def get_paginator(self, operation):
        self.requested_operation = operation
        return self.paginator


class ProductionAuditToolingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="soulsbo-production-audit-")
        self.work = Path(self.temp_dir.name)
        self.source = self.work / "production.sqlite3"
        self.snapshot = self.work / "snapshot.sqlite3"
        self.db_report_path = self.work / "db-audit.json"
        self.r2_report_path = self.work / "r2-inventory.json"
        self.output_reconciliation = self.work / "reconciliation.json"
        self._make_fixture_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_fixture_db(self):
        conn = sqlite3.connect(self.source)
        conn.executescript("""
            CREATE TABLE cartas_colecao(user_id INTEGER, card_id TEXT, quantidade INTEGER);
            INSERT INTO cartas_colecao VALUES (101,'card_alpha',2),(202,'card_beta',1);
            CREATE TABLE cartas_exemplares(id INTEGER,user_id INTEGER,card_id TEXT,rarity TEXT,power INTEGER,source TEXT);
            INSERT INTO cartas_exemplares VALUES (1,101,'card_alpha','Rara',5,'pack');
            CREATE TABLE cartas_gwent_decks(user_id INTEGER,card_ids_json TEXT,exemplar_ids_json TEXT,faction TEXT,leader_id TEXT,relic_id TEXT);
            INSERT INTO cartas_gwent_decks VALUES (101,'["card_alpha","card_beta"]','[1,2]','Ordem Áurea','godfrey','relic_x');
            CREATE TABLE cartas_gwent_matches(id INTEGER,status TEXT,state_json TEXT);
            INSERT INTO cartas_gwent_matches VALUES (1,'active','{"version":2,"players":{}}');
            CREATE TABLE cartas_atelie_submissoes(
                id INTEGER,card_id TEXT,exemplar_id INTEGER,full_card INTEGER,status TEXT,mime_type TEXT,
                created_at TEXT,reviewed_at TEXT,image_key TEXT,image_data BLOB,user_id INTEGER,prompt_text TEXT
            );
            INSERT INTO cartas_atelie_submissoes VALUES
                (7,'card_alpha',1,1,'approved','image/jpeg','2026-01-01',NULL,
                 'atelier/submissions/101/hash/exemplar-1/approved.jpg',X'',101,'PRIVATE PROMPT A');
            INSERT INTO cartas_atelie_submissoes VALUES
                (8,'card_beta',2,1,'pending','image/jpeg','2026-01-02',NULL,
                 'atelier/submissions/202/hash/exemplar-2/pending.jpg',X'',202,'PRIVATE PROMPT B');
            INSERT INTO cartas_atelie_submissoes VALUES
                (9,'card_beta',NULL,1,'rejected','image/jpeg','2026-01-03',NULL,'',X'0102',202,'PRIVATE PROMPT C');
            CREATE TABLE cartas_atelie_artes(id INTEGER,card_id TEXT,status TEXT,channel_id INTEGER,message_id INTEGER,attachment_id INTEGER,created_at TEXT,reviewed_at TEXT,user_id INTEGER);
            INSERT INTO cartas_atelie_artes VALUES (3,'card_alpha','approved',11,22,33,'2026-01-01',NULL,101);
            CREATE TABLE cartas_atelie_sessoes(user_id INTEGER,status TEXT);
            INSERT INTO cartas_atelie_sessoes VALUES (101,'awaiting_upload');
            CREATE TABLE cartas_gwent_lideres_artes(leader_id TEXT,mime_type TEXT,revision TEXT,created_at TEXT,updated_at TEXT,image_data BLOB);
            INSERT INTO cartas_gwent_lideres_artes VALUES ('godfrey','image/jpeg','rev1','2026-01-01','2026-01-02',X'010203');
            CREATE TABLE cartas_geradas(card_id TEXT,rarity TEXT,faction TEXT,power INTEGER,art_path TEXT,art_status TEXT,status TEXT,generator_version TEXT,created_at TEXT);
            INSERT INTO cartas_geradas VALUES ('generated_card_01','Épica','Lua Negra',6,'relative/generated.png','validated','published','v1','2026-01-01');
            CREATE TABLE cartas_geradas_artes(generated_card_id TEXT,storage_path TEXT,content_hash TEXT,width INTEGER,height INTEGER,status TEXT,created_at TEXT);
            INSERT INTO cartas_geradas_artes VALUES ('generated_card_01','relative/generated.png','expected_hash',512,768,'validated','2026-01-01');
            CREATE TABLE cartas_geradas_habilidades(id INTEGER);
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def _sha(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def test_snapshot_uses_readonly_backup_and_preserves_source(self):
        before_hash = self._sha(self.source)
        report = snapshot.create_snapshot(self.source, self.snapshot)
        self.assertEqual(before_hash, self._sha(self.source))
        self.assertTrue(report["source_query_only"])
        self.assertEqual(report["source_open_mode"], "read-only (mode=ro)")
        self.assertEqual(report["source_quick_check"], "ok")
        self.assertEqual(report["snapshot_quick_check"], "ok")
        self.assertEqual(self.snapshot.stat().st_mode & 0o777, 0o600)

    def test_snapshot_includes_wal_rows_without_modifying_source_wal(self):
        wal_db = self.work / "wal-production.sqlite3"
        wal_snapshot = self.work / "wal-snapshot.sqlite3"
        writer = sqlite3.connect(wal_db)
        try:
            mode = writer.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            self.assertEqual(str(mode).lower(), "wal")
            writer.execute("CREATE TABLE wal_fixture(value INTEGER)")
            writer.commit()
            writer.execute("INSERT INTO wal_fixture(value) VALUES (42)")
            writer.commit()
            wal_path = Path(str(wal_db) + "-wal")
            self.assertTrue(wal_path.exists())
            wal_before = wal_path.read_bytes()
            report = snapshot.create_snapshot(wal_db, wal_snapshot)
            self.assertEqual(wal_path.read_bytes(), wal_before)
            self.assertEqual(report["snapshot_quick_check"], "ok")
            with sqlite3.connect(wal_snapshot) as reader:
                self.assertEqual(reader.execute("SELECT value FROM wal_fixture").fetchall(), [(42,)])
        finally:
            writer.close()

    def test_db_audit_is_sanitized_and_counts_art_pipelines(self):
        report = db_audit.build_report(self.source)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["atelier"]["submissions"]["rows"], 3)
        self.assertEqual(report["atelier"]["submissions"]["by_status"]["approved"], 1)
        self.assertEqual(report["atelier"]["submissions"]["approved_without_any_image_source"], 0)
        self.assertEqual(report["atelier"]["discord_attachment_requests"]["rows"], 1)
        self.assertEqual(report["art_storage"]["leader_art_blobs"]["rows"], 1)
        self.assertNotIn("PRIVATE PROMPT", serialized)
        self.assertNotIn("101", [row.get("user_id") for row in report["atelier"]["submissions"]["records"]])
        self.assertNotIn("atelier/submissions/101/", serialized)
        self.assertNotIn("image_data\": \"", serialized)

    def test_optional_local_art_check_does_not_export_paths(self):
        local_root = self.work / "data"
        local_file = local_root / "relative" / "generated.png"
        local_file.parent.mkdir(parents=True)
        local_file.write_bytes(b"generated-art-fixture")
        report = db_audit.build_report(self.source, verify_local_generated_art=True, data_dir=local_root)
        row = report["art_storage"]["generated_art_records"]["records"][0]
        self.assertTrue(row["local_file_check"]["exists"])
        self.assertNotIn(str(local_file), json.dumps(report))

    def test_r2_inventory_uses_only_list_objects_and_redacts_keys(self):
        from datetime import datetime, timezone
        records = [
            {"Key": "atelier/submissions/101/hash/exemplar-1/approved.jpg", "Size": 50,
             "LastModified": datetime(2026, 1, 1, tzinfo=timezone.utc), "ETag": '"e1"'},
            {"Key": "cards/abc/etag.webp", "Size": 100,
             "LastModified": datetime(2026, 1, 2, tzinfo=timezone.utc), "ETag": '"e2"'},
            {"Key": "atelier/submissions/999/hash/exemplar-2/orphan.jpg", "Size": 75,
             "LastModified": datetime(2026, 1, 3, tzinfo=timezone.utc), "ETag": '"e3"'},
        ]
        fake_client = FakeS3Client(records)
        original_configs = r2_inventory._bucket_configs
        original_client = r2_inventory._client
        try:
            r2_inventory._bucket_configs = lambda: [{
                "alias": "primary", "bucket": "fixture-bucket", "account_id": "not-used",
                "access_key_id": "not-used", "secret_access_key": "not-used",
            }]
            r2_inventory._client = lambda config: fake_client
            r2_inventory.write_inventory(self.r2_report_path)
        finally:
            r2_inventory._bucket_configs = original_configs
            r2_inventory._client = original_client
        report = json.loads(self.r2_report_path.read_text(encoding="utf-8"))
        serialized = json.dumps(report)
        self.assertEqual(fake_client.requested_operation, "list_objects_v2")
        self.assertTrue(report["complete"])
        self.assertEqual(report["total_objects"], 3)
        self.assertNotIn("atelier/submissions/101/", serialized)
        self.assertIn("key_sha256", serialized)

    def test_reconciliation_detects_missing_and_unlinked_without_deleting(self):
        db = db_audit.build_report(self.source)
        # Simula o segundo objeto de submissão sem presença no inventário R2.
        keys = []
        for row in db["atelier"]["submissions"]["records"]:
            if row["image_key_sha256"]:
                keys.append(row["image_key_sha256"])
        matched_hash = keys[0]
        orphan_hash = hashlib.sha256(b"atelier/submissions/999/orphan").hexdigest()
        r2 = {
            "schema": "cloudflare-r2-object-inventory/v0.1",
            "complete": True,
            "scope": {"all_objects": True, "prefixes": []},
            "total_objects": 2,
            "buckets": [{"alias": "primary", "bucket": "fixture", "objects": [
                {"key_sha256": matched_hash, "namespace": "atelier/submissions", "size": 50},
                {"key_sha256": orphan_hash, "namespace": "atelier/submissions", "size": 70},
            ]}],
        }
        result = reconcile.reconcile(db, r2)
        summary = result["reconciliation"]
        self.assertEqual(summary["db_key_hashes_missing_from_r2_by_status"], {"pending": 1})
        self.assertEqual(summary["approved_r2_refs_missing_and_without_legacy_blob"], 0)
        self.assertEqual(summary["unlinked_atelier_r2_objects_candidate_count"], 1)
        self.assertFalse(result["safety"]["objects_modified_or_deleted"])

    def test_reconciliation_rejects_truncated_inventory(self):
        db = db_audit.build_report(self.source)
        with self.assertRaises(ValueError):
            reconcile.reconcile(db, {"schema": "cloudflare-r2-object-inventory/v0.1", "complete": False, "scope": {"all_objects": True}, "buckets": []})
        with self.assertRaises(ValueError):
            reconcile.reconcile(db, {"schema": "cloudflare-r2-object-inventory/v0.1", "complete": True, "scope": {"all_objects": False}, "buckets": []})


if __name__ == "__main__":
    unittest.main(verbosity=2)
