#!/usr/bin/env python3
"""Read-only Group C audit validator for Soulsbo.

Runs static/fixture assertions against the legacy engine and checks the candidate
proposal matrix. It does not edit runtime files or claim production integration.
"""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "sistemas/gwent.py").read_text(encoding="utf-8")
STATUS_MODULE = (ROOT / "sistemas/card_status_candidate.py").read_text(encoding="utf-8")
REMOVAL_MODULE = (ROOT / "sistemas/card_removal_resurrection_candidate.py").read_text(encoding="utf-8")
STATUS_REGISTRY = json.loads((ROOT / "data/card_game/status-registry-candidate.v1.json").read_text(encoding="utf-8"))
DECISIONS = json.loads((ROOT / "docs/card-game-state-lifecycle-group-C-decisions-v0.1.json").read_text(encoding="utf-8"))
EXAMPLE = json.loads((ROOT / "docs/examples/card-game-state-lifecycle-group-C.example.v0.1.json").read_text(encoding="utf-8"))

class GroupCValidation(unittest.TestCase):
    def test_decision_set_has_exact_ten_ids(self):
        self.assertEqual({"CI-008", "CI-009", "BUF-008", "BUF-009", "BUF-010", "BUF-011", "BUF-014", "RSRX-07", "RSRX-08", "RSRX-10"}, {x["id"] for x in DECISIONS["decisions"]})
    def test_decisions_are_owner_approved(self):
        self.assertTrue(all(x["status"] == "OWNER_APPROVED" and x.get("owner_approved") is True for x in DECISIONS["decisions"]))
    def test_every_decision_has_approved_resolution(self):
        self.assertTrue(all(x.get("recommended_resolution") and x.get("approved_resolution") for x in DECISIONS["decisions"]))
        self.assertEqual("OWNER_APPROVED", DECISIONS["recommended_path"]["status"])
        self.assertEqual("docs/card-game-state-lifecycle-group-C-approval-v0.1.json", DECISIONS["metadata"]["approval_record"])
    def test_group_c_guardrail_is_approved(self):
        self.assertTrue(DECISIONS["guardrails"]["group_C_approved"])
    def test_runtime_guardrail_is_false(self):
        self.assertFalse(DECISIONS["guardrails"]["runtime_modified"])
    def test_contract_freeze_guardrail_is_false(self):
        self.assertFalse(DECISIONS["guardrails"]["schema_frozen"])
    def test_transition_matrix_has_seven_policies(self):
        self.assertEqual(7, len(DECISIONS["transition_policies"]))
    def test_transition_ids_are_unique(self):
        ids = [x["transition"] for x in DECISIONS["transition_policies"]]
        self.assertEqual(len(ids), len(set(ids)))
    def test_all_transition_policies_have_proposals(self):
        self.assertTrue(all(x.get("proposed") for x in DECISIONS["transition_policies"]))
    def test_example_is_not_a_schema(self):
        self.assertEqual("ILLUSTRATIVE_POLICY_EXAMPLE_NOT_A_MATCH_SCHEMA", EXAMPLE["status"])
    def test_example_keeps_round_scoped_bonus_until_expiry(self):
        self.assertEqual(2, EXAMPLE["after_proposed_transition"]["bonus"])
    def test_bonus_projection_has_sourced_grant_and_expiry(self):
        grants = EXAMPLE["before"]["bonus_grants"]
        self.assertTrue(grants)
        self.assertTrue(all({"source_effect_id", "applied_event_id", "clamp_policy_id", "expires_on"} <= set(g) for g in grants))
    def test_status_applications_record_source_and_expiry(self):
        applications = EXAMPLE["before"]["status_applications"]
        self.assertTrue(applications)
        self.assertTrue(all({"status_id", "source_effect_id", "applied_event_id", "expires_on"} <= set(a) for a in applications))
    def test_shield_grants_record_profile_source_and_expiry(self):
        grants = EXAMPLE["before"]["shield_grants"]
        self.assertTrue(grants)
        self.assertTrue(all({"profile_id", "source_effect_id", "applied_event_id", "expires_on"} <= set(g) for g in grants))
    def test_round_close_expires_bonus_in_discard_after_result_snapshot(self):
        close = EXAMPLE["round_close_example"]
        self.assertEqual("discard", close["instance_zone"])
        self.assertEqual("after_immutable_round_result_snapshot", close["timing"])
        self.assertEqual(0, close["after"]["bonus"])
        self.assertEqual([], close["after"]["bonus_grants"])
    def test_example_clears_status_and_protection_on_successful_removal(self):
        after = EXAMPLE["after_proposed_transition"]
        self.assertEqual([], after["shield_grants"])
        self.assertTrue(all(v == 0 for v in after["statuses"].values()))
    def test_status_registry_has_four_states(self):
        self.assertEqual({"status.frost", "status.scarlet_rot", "status.bleeding", "status.madness"}, {x["status_id"] for x in STATUS_REGISTRY["statuses"]})
    def test_status_registry_remains_candidate(self):
        self.assertEqual("CANDIDATE_FOR_REVIEW_NOT_APPROVED", STATUS_REGISTRY["status"])
    def test_status_counters_cap_at_two(self):
        self.assertTrue(all(x["max_marks_per_unit"] == 2 for x in STATUS_REGISTRY["statuses"]))
    def test_statuses_expire_at_round_close_in_candidate(self):
        self.assertTrue(all(x["expires_at"] == "round_close" for x in STATUS_REGISTRY["statuses"]))
    def test_statuses_clear_on_removal_in_candidate(self):
        self.assertTrue(all(x["cleared_on_unit_removal"] for x in STATUS_REGISTRY["statuses"]))
    def test_effective_power_uses_current_row_weather_resistance_and_control_states(self):
        fn = SOURCE[SOURCE.index("def _poder_efetivo("):SOURCE.index("def _remover_unidade(")]
        self.assertIn("weather.get(unit.get(\"row\")", fn)
        self.assertIn("unit.get(\"weather_resist\", 0)", fn)
        self.assertIn("min(3", fn)
        self.assertIn("max(1", fn)
    def test_successful_removal_clears_shield_and_four_states(self):
        fn = SOURCE[SOURCE.index("def _remover_unidade("):SOURCE.index("def ", SOURCE.index("def _remover_unidade(") + 5)]
        self.assertIn("unit.pop(\"escudo\", None)", fn)
        self.assertIn('for status_key in ("sangramento", "geada", "podrida", "loucura"):', fn)
        self.assertIn('unit[status_key] = 0', fn)
    def test_removal_preserves_bonus_weather_resistance_and_combo_marker(self):
        fn = SOURCE[SOURCE.index("def _remover_unidade("):SOURCE.index("def ", SOURCE.index("def _remover_unidade(") + 5)]
        self.assertNotIn('unit["bonus"] = 0', fn)
        self.assertNotIn('unit["weather_resist"] = 0', fn)
        self.assertNotIn('unit.pop("combo_ativado"', fn)
    def test_shield_block_returns_before_status_cleanup(self):
        fn = SOURCE[SOURCE.index("def _remover_unidade("):SOURCE.index("def ", SOURCE.index("def _remover_unidade(") + 5)]
        self.assertLess(fn.index("return f\"{unit['nome']} resistiu"), fn.index("unit.pop(\"escudo\", None)"))
    def test_sacrifice_bypasses_legacy_shield_check(self):
        self.assertIn('if causa != "sacrificio" and int(unit.get("escudo", 0)) > 0:', SOURCE)
    def test_normal_round_cleanup_resets_bonus_shield_status_and_combo(self):
        segment = SOURCE[SOURCE.index("def _resolve_round("):SOURCE.index("def _auto_pass_empty_hands(")]
        for fragment in ('archived["bonus"] = 0', 'archived["escudo"] = 0', 'archived.pop("combo_ativado", None)', 'kept["bonus"] = 0', 'kept["escudo"] = 0', 'kept.pop("combo_ativado", None)'):
            self.assertIn(fragment, segment)
        self.assertIn('for status_key in ("sangramento", "geada", "podrida", "loucura"):', segment)
        self.assertIn('archived[status_key] = 0', segment)
        self.assertIn('kept[status_key] = 0', segment)
    def test_round_cleanup_does_not_reset_weather_resistance(self):
        segment = SOURCE[SOURCE.index("def _resolve_round("):SOURCE.index("def _auto_pass_empty_hands(")]
        self.assertNotIn('archived["weather_resist"] = 0', segment)
        self.assertNotIn('kept["weather_resist"] = 0', segment)
    def test_round_cleanup_iterates_board_not_existing_discard(self):
        segment = SOURCE[SOURCE.index("def _resolve_round("):SOURCE.index("def _auto_pass_empty_hands(")]
        self.assertIn('board = player.get("board", [])', segment)
        self.assertIn('for fallen in board:', segment)
        self.assertNotIn('for discarded in player.get("discard", [])', segment)
    def test_terminal_branch_returns_before_nonterminal_cleanup(self):
        segment = SOURCE[SOURCE.index("def _resolve_round("):SOURCE.index("def _auto_pass_empty_hands(")]
        terminal = segment.index('state["status"] = "finished"')
        early_return = segment.index("return", terminal)
        nonterminal_cleanup = segment.index('archived["bonus"] = 0')
        self.assertLess(early_return, nonterminal_cleanup)
    def test_legacy_weather_resistance_is_scalar(self):
        self.assertIn('unit.get("weather_resist", 0)', SOURCE)
        self.assertNotIn('weather_resistance_modifiers', SOURCE)
    def test_vigil_seal_sets_one_point(self):
        self.assertIn('elif effect == "vigil_seal":\n        card["weather_resist"] = 1', SOURCE)
    def test_generic_resistance_branch_is_two_but_must_remain_binding_gated(self):
        self.assertIn('elif skill == "resistencia_climatica":\n                card["weather_resist"] = 2', SOURCE)
        self.assertTrue(DECISIONS["guardrails"]["group_B_approved"])
    def test_status_candidate_still_reads_scalar_weather_resistance(self):
        self.assertIn('unit.get("weather_resist", 0)', STATUS_MODULE)
        self.assertNotIn("weather_resistance_modifiers", STATUS_MODULE)
    def test_status_candidate_tracks_round_close_expiry(self):
        self.assertIn('def close_round_statuses(', STATUS_MODULE)
    def test_protection_checks_are_not_universal_in_legacy(self):
        self.assertIn('if int(alvo.get("escudo",0))>0', SOURCE)
        self.assertIn('if int(alvo.get("escudo",0))>0:', SOURCE)
        self.assertIn('unit["geada"] = min(2', SOURCE)
    def test_noite_flame_consumes_relic_on_block(self):
        segment = SOURCE[SOURCE.index('elif skill == "reliquia_noite_chama"'):SOURCE.index('elif skill == "reliquia_lamina_negra"')]
        self.assertIn('player["relic_used"]=True', segment)
        self.assertIn('alvo["escudo"]-=1', segment)
    def test_black_blade_does_not_consume_relic_on_block(self):
        segment = SOURCE[SOURCE.index('elif skill == "reliquia_lamina_negra"'):SOURCE.index('elif skill == "reliquia_algemas"')]
        blocked = segment[:segment.index("else:")]
        self.assertIn('alvo["escudo"]-=1', blocked)
        self.assertNotIn('player["relic_used"] = True', blocked)
    def test_resurrect_and_requiem_legacy_reset_bonus(self):
        self.assertIn('revivida["bonus"] = 0', SOURCE)
        self.assertIn('revived["bonus"] = 0', REMOVAL_MODULE)
    def test_esgar_legacy_adds_one_to_prior_bonus_and_clears_status(self):
        segment = SOURCE[SOURCE.index('elif effect == "esgar_blood_priest"'):SOURCE.index('elif effect == "rennala_full_moon"')]
        self.assertIn('revived["bonus"] = int(revived.get("bonus", 0)) + 1', segment)
        self.assertIn('for key in ("sangramento", "geada", "podrida", "loucura"):', segment)
        self.assertIn('revived[key] = 0', segment)
    def test_resurrection_policies_are_per_effect_in_candidate(self):
        self.assertIn('entry_bonus_mode: str = "reset_to_zero"', REMOVAL_MODULE)
        self.assertIn('add_one_to_existing_bonus', REMOVAL_MODULE)
    def test_recover_to_hand_does_not_normalize_payload(self):
        fn = REMOVAL_MODULE[REMOVAL_MODULE.index("def recover_unit_to_hand("):]
        self.assertIn('card = discard.pop(index)', fn)
        self.assertIn('hand.append(card)', fn)
        self.assertNotIn('card["bonus"] = 0', fn)
        self.assertNotIn('clear_statuses', fn)
    def test_candidate_example_keeps_instance_identity_concept(self):
        self.assertEqual("successful_removal_or_sacrifice", EXAMPLE["transition"])
        self.assertIn("intrinsic_weather_resistance", EXAMPLE["before"])
        self.assertIn("weather_resistance_modifiers", EXAMPLE["before"])

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GroupCValidation)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "metadata": {
            "document":"Group C state lifecycle candidate validation v0.1",
            "status":"OWNER_APPROVED",
            "approval_record":"docs/card-game-state-lifecycle-group-C-approval-v0.1.json",
            "runtime_integration":False,
            "scope":"Static source checks and candidate proposal consistency; no production DB/API/Discord run."
        },
        "counts":{"tests":result.testsRun,"passed":result.testsRun-len(result.failures)-len(result.errors),"failed":len(result.failures)+len(result.errors)},
        "test_names":sorted(name for name in dir(GroupCValidation) if name.startswith("test_")),
        "failures":[str(x[1]) for x in result.failures+result.errors],
        "limitations":[
            "Static assertions prove presence/order of inspected legacy branches, not live match behavior in production.",
            "Group C design is owner-approved; the validator still does not prove runtime integration or production behavior.",
            "No runtime, DB, API, Discord, frontend or migration file was changed."
        ]
    }
    out = ROOT / "docs/card-game-state-lifecycle-group-C-validation-v0.1.json"
    out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Group C: {summary['counts']['passed']}/{summary['counts']['tests']} passed; {summary['counts']['failed']} failed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
