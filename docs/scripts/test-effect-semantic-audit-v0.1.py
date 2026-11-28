#!/usr/bin/env python3
"""Regression tests for the read-only effect semantic audit report."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = json.loads((ROOT / "docs/card-game-effect-semantic-audit-v0.1.json").read_text(encoding="utf-8"))
ALIASES = json.loads((ROOT / "data/card_game/legacy-effect-aliases-v0.1.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "data/card_game/effect-registry-candidate.v1.json").read_text(encoding="utf-8"))


class EffectSemanticAuditTests(unittest.TestCase):
    def test_all_54_candidate_families_are_in_semantic_report(self):
        self.assertEqual(54, REPORT["counts"]["candidate_families"])
        self.assertEqual({x["effect_id"] for x in REGISTRY["effects"]}, {x["effect_id"] for x in REPORT["families"]})

    def test_generic_dispatch_coverage_is_56_direct_2_lifecycle_1_missing(self):
        counts = REPORT["counts"]
        self.assertEqual(59, counts["generic_aliases"])
        self.assertEqual(56, counts["direct_play_branch_aliases"])
        self.assertEqual(2, counts["lifecycle_hook_aliases"])
        self.assertEqual(1, counts["generic_aliases_without_handler"])
        missing = [x["legacy_id"] for x in REPORT["generic_execution_coverage"] if x["classification"] == "NO_CURRENT_HANDLER_FOUND"]
        self.assertEqual(["sobrevivente"], missing)

    def test_all_22_active_identity_cards_have_resolver_branch_evidence(self):
        self.assertEqual(22, REPORT["counts"]["active_identity_overrides"])
        self.assertEqual(22, REPORT["counts"]["active_identity_branches_found"])
        self.assertTrue(all(x["evidence"] and x["classification"] == "ACTIVE_IDENTITY_BRANCH_FOUND" for x in REPORT["identity_execution_coverage"]))

    def test_archived_candidate_aliases_are_included_in_family_review(self):
        all_aliases = {a["legacy_id"] for family in REPORT["families"] for a in family["aliases"]}
        self.assertTrue({"shadow_paths", "grey_watch", "veil_shift", "covering_shot", "echo_orb", "counterflame", "gloria"} <= all_aliases)

    def test_unmapped_fields_have_code_branches_but_no_active_binding(self):
        self.assertEqual(4, len(REPORT["unmapped_fields"]))
        for item in REPORT["unmapped_fields"]:
            self.assertTrue(item["identity_resolver_branch_lines"], item["legacy_field_id"])
            self.assertFalse(item["current_card_identity_binding"])
            self.assertEqual("BRANCH_EXISTS_BUT_NO_ACTIVE_CARD_IDENTITY_BINDING", item["classification"])

    def test_gloria_is_implemented_and_sobrevivente_has_no_hook(self):
        hidden = {x["legacy_id"]: x for x in REPORT["hidden_lifecycle_aliases"]}
        self.assertEqual("HOOK_IMPLEMENTED", hidden["gloria"]["implementation_status"])
        self.assertTrue(hidden["gloria"]["source_evidence"])
        self.assertEqual("DECLARED_WITHOUT_HOOK", hidden["sobrevivente"]["implementation_status"])
        self.assertEqual([], hidden["sobrevivente"]["source_evidence"])

    def test_sequence_family_requires_previous_play_explicitly(self):
        effect = next(x for x in REGISTRY["effects"] if x["effect_id"] == "effect.sequence_power")
        self.assertIn("requires_previous_play", effect["required_parameters"])
        self.assertEqual("boolean", effect["parameters"]["requires_previous_play"]["type"])
        entries = [x for x in ALIASES["generic_and_special_aliases"] if x["canonical_effect_id"] == "effect.sequence_power"]
        entries.extend(x for x in ALIASES["inactive_identity_branch_decisions"] if x.get("candidate_effect_id") == "effect.sequence_power")
        self.assertEqual(6, len(entries))
        self.assertTrue(all(x.get("default_effect_params", x.get("candidate_params", {})).get("requires_previous_play") is True for x in entries))

    def test_priority_counts_are_complete(self):
        counts = REPORT["counts"]
        self.assertEqual(counts["candidate_families"], counts["high_risk_families"] + counts["medium_risk_families"] + counts["low_risk_families"])

    def test_semantic_risk_labels_are_review_priority_not_approval(self):
        self.assertIn("not connected", REPORT["metadata"]["status"].lower())
        self.assertTrue(all(x["candidate_warning"] for x in REPORT["families"]))
        round_end = next(x for x in REPORT["families"] if x["effect_id"] == "effect.round_victory_survivor")
        self.assertEqual("MEDIUM", round_end["review_priority"])

    def test_manual_finding_priority_matches_family_review_priority(self):
        family_priority = {x["effect_id"]: x["review_priority"] for x in REPORT["families"]}
        for finding in REPORT["manual_findings"]:
            subjects = [x.strip() for x in finding["subject"].split("/")]
            for subject in subjects:
                self.assertEqual(finding["priority"], family_priority[subject], finding["finding_id"])

    def test_source_hashes_are_recorded(self):
        sources = REPORT["metadata"]["sources"]
        self.assertTrue(sources["sistemas/cartas.py"])
        self.assertTrue(sources["sistemas/gwent.py"])
        self.assertTrue(sources["data/card_game/effect-registry-candidate.v1.json"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EffectSemanticAuditTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
