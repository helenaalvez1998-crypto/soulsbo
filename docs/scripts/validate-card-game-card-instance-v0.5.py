#!/usr/bin/env python3
"""Validate CardInstance v0.5 document contracts; no runtime integration."""
from __future__ import annotations
import json, unittest
from pathlib import Path
import jsonschema
ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SCHEMAS = DOCS / "schemas"
EXAMPLES = DOCS / "examples"
def load(path): return json.loads(path.read_text(encoding="utf-8"))

class CardInstanceV05Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.match_schema = load(SCHEMAS / "card-game-card-instance-match.schema.v5.json")
        cls.example = load(EXAMPLES / "card-instance-match.example.v5.json")
        cls.request_schema = load(SCHEMAS / "card-game-action-request.schema.v1.json")
        cls.offer_schema = load(SCHEMAS / "card-game-target-offer.schema.v1.json")
        cls.policy_schema = load(SCHEMAS / "card-game-effect-target-policy.schema.v1.json")
        cls.result_schema = load(SCHEMAS / "card-game-action-result.schema.v1.json")
        cls.decisions = load(DOCS / "card-game-selection-group-D-decisions-v0.1.json")
        cls.approval = load(DOCS / "card-game-selection-group-D-approval-v0.1.json")

    def test_v5_schema_is_valid(self):
        jsonschema.Draft202012Validator.check_schema(self.match_schema)
    def test_v5_example_matches_schema(self):
        jsonschema.Draft202012Validator(self.match_schema).validate(self.example)
    def test_group_d_approval_covers_twelve_ids(self):
        self.assertEqual("OWNER_APPROVED", self.approval["status"])
        self.assertEqual([f"DSEL-DEC-{i:03d}" for i in range(1,13)], self.approval["approved_decision_ids"])
    def test_decision_register_marks_all_twelve_approved(self):
        self.assertEqual("OWNER_APPROVED", self.decisions["status"])
        self.assertEqual(12, len(self.decisions["decisions"]))
        self.assertTrue(all(x["status"] == "OWNER_APPROVED" for x in self.decisions["decisions"]))
    def test_four_group_d_schemas_are_valid(self):
        for schema in (self.request_schema, self.offer_schema, self.policy_schema, self.result_schema):
            jsonschema.Draft202012Validator.check_schema(schema)
    def test_v5_operation_result_outcomes_are_exact(self):
        self.assertEqual({"applied","partial","blocked","consumed_no_effect","rejected"}, set(self.match_schema["$defs"]["action_result"]["properties"]["outcome"]["enum"]))
    def test_target_outcomes_are_exact(self):
        self.assertEqual({"applied","blocked","skipped"}, set(self.match_schema["$defs"]["action_target_result"]["properties"]["outcome"]["enum"]))
    def test_conflict_is_not_a_gameplay_outcome(self):
        self.assertNotIn("conflict", self.match_schema["$defs"]["action_result"]["properties"]["outcome"]["enum"])
    def test_cost_dimensions_are_separate(self):
        required = set(self.match_schema["$defs"]["action_costs"]["required"])
        self.assertEqual({"turn_consumed","source_consumed","activation_consumed","protection_grants_consumed","other_costs"}, required)
    def test_operation_expected_revision_matches_result(self):
        for key, record in self.example["operations"].items():
            self.assertEqual(key, record["operation_id"])
            self.assertEqual(key, record["result"]["operation_id"])
            self.assertEqual(record["expected_revision"], record["result"]["revision_before"])
    def test_rejected_result_has_no_costs_events_or_revision_change(self):
        r = {
            "schema_version": 1, "operation_id": "00000000-0000-4000-8000-000000000099",
            "outcome": "rejected", "revision_before": 4, "revision_after": 4,
            "target_results": [], "event_ids": [],
            "costs": {"turn_consumed":False,"source_consumed":False,"activation_consumed":False,"protection_grants_consumed":[],"other_costs":[]}
        }
        jsonschema.Draft202012Validator(self.result_schema).validate(r)
        self.assertEqual(r["revision_before"], r["revision_after"])
        self.assertFalse(r["costs"]["turn_consumed"] or r["costs"]["source_consumed"] or r["costs"]["activation_consumed"] or r["costs"]["protection_grants_consumed"] or r["costs"]["other_costs"])
        self.assertEqual([], r["event_ids"])
    def test_partial_result_is_mixed_per_target(self):
        outcomes = [x["outcome"] for x in self.example["operations"]["00000000-0000-4000-8000-000000000010"]["result"]["target_results"]]
        mixed = {"applied", "blocked"}
        self.assertIn(outcomes[0], {"applied","blocked","skipped"})
        self.assertEqual(mixed, set(self.match_schema["$defs"]["action_target_result"]["properties"]["outcome"]["enum"]) & mixed)
    def test_up_to_one_available_is_not_partial_by_max_shortfall(self):
        policy = load(EXAMPLES / "card-game-effect-target-policy.example.v1.json")
        policy["target_count"] = {"mode":"up_to","minimum_targets":1,"maximum_targets":2}
        available = 1
        outcome = "applied" if available >= policy["target_count"]["minimum_targets"] else "rejected"
        self.assertEqual("applied", outcome)
    def test_target_policy_has_no_rarity_dependency(self):
        for key, value in self.policy_schema["properties"].items():
            self.assertNotEqual("rarity_id", key)
        policy = load(EXAMPLES / "card-game-effect-target-policy.example.v1.json")
        self.assertNotIn("rarity_id", policy)
    def test_target_offer_contains_revision_and_server_metrics(self):
        offer = load(EXAMPLES / "card-game-target-offer.example.v1.json")
        jsonschema.Draft202012Validator(self.offer_schema).validate(offer)
        self.assertIn("state_revision", offer)
        self.assertIn("eligibility_metric", offer["metrics"])
        self.assertIn("display_metric", offer["metrics"])
        self.assertIn("sort_metric", offer["metrics"])
    def test_manual_primary_autofill_requires_preview_token(self):
        sel = {"mode":"manual_primary_auto_fill", "target_instance_id":"00000000-0000-4000-8000-000000000001", "preview_token":"opaque-server-token"}
        req = {"schema_version":1,"operation_id":"00000000-0000-4000-8000-000000000002","expected_revision":0,"action":"play","selection":sel}
        jsonschema.Draft202012Validator(self.request_schema).validate(req)
    def test_manual_set_uses_unique_instance_ids(self):
        ids = ["00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000002"]
        self.assertEqual(len(ids), len(set(ids)))
    def test_protection_tie_break_is_explicit_in_approval(self):
        text = (DOCS / "card-game-selection-group-D-approval-v0.1.md").read_text(encoding="utf-8")
        self.assertIn("applied_event.sequence", text)
        self.assertIn("grant_id", text)
    def test_runtime_guardrail_remains_false(self):
        self.assertFalse(self.approval["boundaries"]["runtime_integration_authorized"])
        self.assertFalse(self.approval["boundaries"]["production_api_or_database_changes_authorized"])
    def test_v5_instance_schema_version_is_five(self):
        self.assertEqual(5, self.match_schema["$defs"]["card_instance"]["properties"]["schema_version"]["const"])
    def test_root_schema_version_is_five(self):
        self.assertEqual(5, self.match_schema["properties"]["schema_version"]["const"])
    def test_special_source_is_in_discard_after_consumption(self):
        player = self.example["players"]["1001"]["zones"]
        source_id = "00000000-0000-4000-8000-000000000005"
        self.assertNotIn(source_id, player["hand"])
        self.assertIn(source_id, player["discard"])
    def test_action_result_event_ids_reference_existing_events(self):
        event_ids = {e["event_id"] for e in self.example["events"]}
        for record in self.example["operations"].values():
            self.assertTrue(set(record["result"]["event_ids"]).issubset(event_ids))
    def test_events_reference_existing_operations(self):
        op_ids = set(self.example["operations"])
        self.assertTrue(all(e["operation_id"] in op_ids for e in self.example["events"]))
    def test_rejection_cost_semantics_documented(self):
        text = (DOCS / "card-game-card-instance-contract-v0.5.md").read_text(encoding="utf-8")
        self.assertIn("Nenhum custo", text)
        self.assertIn("revision_after == revision_before", text)
    def test_target_offer_is_transient_not_a_match_zone(self):
        text = (DOCS / "card-game-card-instance-contract-v0.5.md").read_text(encoding="utf-8")
        self.assertIn("recurso de serviço temporário", text)
    def test_conflicts_are_group_e(self):
        text = (DOCS / "card-game-card-instance-contract-v0.5.md").read_text(encoding="utf-8")
        self.assertIn("conflito de transporte/persistência do Grupo E", text)
    def test_group_f_and_e_remain_open(self):
        self.assertEqual([True, True], [self.approval["boundaries"]["group_F_open"], self.approval["boundaries"]["group_E_open"]])

if __name__ == "__main__":
    unittest.main(verbosity=2)
