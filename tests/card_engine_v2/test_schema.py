from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:  # jsonschema is a development-time validator, not a runtime dependency.
    Draft202012Validator = None

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipIf(Draft202012Validator is None, "jsonschema not installed; schema test skipped")
class CardInstanceV7SchemaTests(unittest.TestCase):
    def test_v7_schema_and_persisted_fixture(self) -> None:
        schema = json.loads(
            (ROOT / "docs/schemas/card-game-card-instance-match.schema.v7.json").read_text(encoding="utf-8")
        )
        fixture = json.loads(
            (ROOT / "docs/examples/card-instance-match.example.v7.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(fixture))
        self.assertEqual(errors, [])
        self.assertEqual(fixture["schema_version"], 7)
        self.assertIn("event_watermark", fixture)
        self.assertNotIn("operations", fixture)
        self.assertNotIn("events", fixture)

    def test_v7_schema_accepts_primordial_exemplar_classification(self) -> None:
        schema = json.loads(
            (ROOT / "docs/schemas/card-game-card-instance-match.schema.v7.json").read_text(encoding="utf-8")
        )
        fixture = json.loads(
            (ROOT / "docs/examples/card-instance-match.example.v7.json").read_text(encoding="utf-8")
        )
        exemplar = next(item for item in fixture["instances"].values() if item.get("exemplar_snapshot"))
        exemplar["exemplar_snapshot"]["rarity_id"] = "primordial"
        errors = list(Draft202012Validator(schema).iter_errors(fixture))
        self.assertEqual(errors, [])

    def test_v7_schema_accepts_alpha_combo_passive_and_leader_state(self) -> None:
        schema = json.loads(
            (ROOT / "docs/schemas/card-game-card-instance-match.schema.v7.json").read_text(encoding="utf-8")
        )
        fixture = json.loads(
            (ROOT / "docs/examples/card-instance-match.example.v7.json").read_text(encoding="utf-8")
        )
        player = next(iter(fixture["players"].values()))
        player["faction_id"] = "golden_order"
        player["leader_id"] = "comandante_fornalha"
        player["leader_used"] = False
        player["round_state"]["faction_passive_used"] = True
        player["round_state"]["synergy_used"] = {"muralha_inabalavel": True}
        errors = list(Draft202012Validator(schema).iter_errors(fixture))
        self.assertEqual(errors, [])

    def test_exported_sql_matches_runtime_migration_checksum(self) -> None:
        from sistemas.card_engine_v2.repository import MIGRATION_CHECKSUM, MIGRATION_ID, MIGRATION_STATEMENTS

        sql = (ROOT / "docs/schemas/card-engine-v2-persistence-schema-v0.1.sql").read_text(encoding="utf-8")
        self.assertIn(f"-- migration_id: {MIGRATION_ID}", sql)
        self.assertIn(f"-- checksum_sha256: {MIGRATION_CHECKSUM}", sql)
        for statement in MIGRATION_STATEMENTS:
            self.assertIn(statement.rstrip().rstrip(";") + ";", sql)

    def test_internal_operation_request_schema_and_example(self) -> None:
        schema = json.loads(
            (ROOT / "docs/schemas/card-engine-v2-operation-request.schema.v1.json").read_text(encoding="utf-8")
        )
        fixture = json.loads(
            (ROOT / "docs/examples/card-engine-v2-operation-request.example.v1.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(fixture))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
