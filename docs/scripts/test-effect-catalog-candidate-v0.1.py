#!/usr/bin/env python3
"""Regression tests for the proposed v0.1 effect registry migration artifact.

These tests validate extraction completeness and structural consistency only.
They do not claim that candidate handlers exist or that the candidate balance is
approved. No legacy runtime module is modified by this script.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator  # noqa: E402
import sistemas.cartas as legacy_cards  # noqa: E402
import sistemas.gwent as legacy_engine  # noqa: E402
from sistemas.card_contract import validate_effect_registry, _validate_effect_params  # noqa: E402

DATA = ROOT / "data/card_game"
DOCS = ROOT / "docs"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


REGISTRY = read_json(DATA / "effect-registry-candidate.v1.json")
REGISTRY_SCHEMA = read_json(DATA / "effect-registry.schema.v1.json")
ALIASES = read_json(DATA / "legacy-effect-aliases-v0.1.json")
LEADERS = read_json(DATA / "leader-registry-candidate.v1.json")
FACTIONS = read_json(DATA / "faction-passives-candidate.v1.json")
DECISIONS = read_json(DOCS / "card-game-effect-catalog-decision-v0.1.json")
SOURCE_MAP = read_json(DOCS / "card-game-stale-identity-disposition-v0.1.json")

EFFECT_BY_ID = {item["effect_id"]: item for item in REGISTRY["effects"]}
GENERIC_ALIASES = ALIASES["generic_and_special_aliases"]
IDENTITY_ALIASES = ALIASES["active_identity_card_overrides"]
STALE_ALIASES = ALIASES["inactive_identity_branch_decisions"]


class EffectCatalogCandidateTests(unittest.TestCase):
    def test_registry_matches_draft_2020_12_schema(self):
        errors = list(Draft202012Validator(REGISTRY_SCHEMA).iter_errors(REGISTRY))
        self.assertEqual([], [f"{list(e.absolute_path)}: {e.message}" for e in errors])

    def test_registry_passes_runtime_contract_validator(self):
        result = validate_effect_registry(REGISTRY)
        self.assertTrue(result.valid, "; ".join(result.errors))

    def test_candidate_effect_family_count_is_54(self):
        self.assertEqual(54, len(REGISTRY["effects"]))
        self.assertEqual(54, len(EFFECT_BY_ID))

    def test_candidate_family_types_are_36_units_12_specials_6_relics(self):
        from collections import Counter
        kinds = Counter(item["kind"] for item in REGISTRY["effects"])
        self.assertEqual({"unit": 36, "special": 12, "relic": 6}, dict(kinds))

    def test_effect_ids_are_unique_and_names_are_nonempty(self):
        ids = [item["effect_id"] for item in REGISTRY["effects"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(item["name"].strip() for item in REGISTRY["effects"]))

    def test_every_template_placeholder_is_a_declared_parameter(self):
        for effect in REGISTRY["effects"]:
            placeholders = set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", effect["rules_template"]))
            declared = set(effect.get("parameters", {}))
            self.assertLessEqual(placeholders, declared, effect["effect_id"])

    def test_all_59_habilidades_have_exactly_one_migration_alias(self):
        ids = [item["legacy_id"] for item in GENERIC_ALIASES]
        self.assertEqual(59, len(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(legacy_cards.HABILIDADES), set(ids))

    def test_all_generic_alias_targets_and_default_params_validate(self):
        for item in GENERIC_ALIASES:
            effect_id = item["canonical_effect_id"]
            self.assertIn(effect_id, EFFECT_BY_ID, item["legacy_id"])
            errors = _validate_effect_params(
                item["default_effect_params"], EFFECT_BY_ID[effect_id], prefix=item["legacy_id"]
            )
            self.assertEqual([], errors, item["legacy_id"])

    def test_alias_source_names_descriptions_and_card_assignments_match_legacy(self):
        cards_by_skill: dict[str, list[str]] = {}
        for card_id, card in legacy_cards.CARTAS_POR_ID.items():
            skill_id = getattr(card, "habilidade", None)
            if skill_id:
                cards_by_skill.setdefault(skill_id, []).append(card_id)
        for item in GENERIC_ALIASES:
            legacy_meta = legacy_cards.HABILIDADES[item["legacy_id"]]
            self.assertEqual(legacy_meta["nome"], item["legacy_display_name"])
            self.assertEqual(legacy_meta["texto"], item["legacy_description"])
            self.assertEqual(sorted(cards_by_skill.get(item["legacy_id"], [])), item["assigned_card_ids"])
            self.assertEqual(len(item["assigned_card_ids"]), item["assigned_card_count"])

    def test_22_active_identity_overrides_are_unique_and_complete(self):
        self.assertEqual(22, len(IDENTITY_ALIASES))
        by_card = {item["card_id"]: item for item in IDENTITY_ALIASES}
        self.assertEqual(22, len(by_card))
        self.assertEqual(set(legacy_engine.CARD_IDENTITY_ABILITIES), set(by_card))

    def test_identity_alias_targets_and_params_validate(self):
        for item in IDENTITY_ALIASES:
            effect_id = item["canonical_effect_id"]
            self.assertIn(effect_id, EFFECT_BY_ID, item["card_id"])
            errors = _validate_effect_params(
                item["default_effect_params"], EFFECT_BY_ID[effect_id], prefix=item["card_id"]
            )
            self.assertEqual([], errors, item["card_id"])
            self.assertIn(item["card_id"], legacy_cards.CARTAS_POR_ID)

    def test_16_identity_cards_keep_only_identity_effect_in_new_model(self):
        count = sum(bool(item["legacy_generic_field_suppressed"]) for item in IDENTITY_ALIASES)
        self.assertEqual(16, count)
        self.assertEqual(16, ALIASES["identity_generic_suppression_count"])

    def test_hidden_gloria_and_survivente_are_explicitly_mapped(self):
        hidden = {item["legacy_id"]: item for item in ALIASES["hidden_lifecycle_aliases"]}
        self.assertEqual({"gloria", "sobrevivente"}, set(hidden))
        self.assertEqual("effect.round_victory_survivor", hidden["gloria"]["candidate_effect_id"])
        self.assertEqual("effect.round_victory_survivor", hidden["sobrevivente"]["candidate_effect_id"])
        self.assertEqual(3, hidden["gloria"]["assigned_card_count"])

    def test_stale_branch_counts_are_18_v18_6_v75_and_4_unregistered(self):
        self.assertEqual(18, len(SOURCE_MAP["v18_filtered_identity_candidates"]))
        self.assertEqual(6, len(SOURCE_MAP["stale_v75_effect_candidates"]))
        self.assertEqual(4, len(SOURCE_MAP["unmapped_legacy_field_effect_candidates"]))
        archived_identity_branches = sum(1 for item in STALE_ALIASES if item["disposition"] in {"ARCHIVE_AS_OPTIONAL_ALIAS", "ARCHIVE_DO_NOT_REACTIVATE_AUTOMATICALLY", "ARCHIVE_STALE_BRANCH"})
        archived_unregistered_fields = sum(1 for item in STALE_ALIASES if item["disposition"] == "ARCHIVE_UNREGISTERED_FIELD_EFFECT")
        self.assertEqual(24, archived_identity_branches)
        self.assertEqual(4, archived_unregistered_fields)

    def test_27_combos_have_unique_priorities_and_minimum_two(self):
        combos = REGISTRY["combos"]
        self.assertEqual(27, len(combos))
        priorities = [item["priority"] for item in combos]
        self.assertEqual(len(priorities), len(set(priorities)))
        self.assertTrue(all(item["minimum_participants"] >= 2 for item in combos))

    def test_every_combo_has_distinct_card_pair_covering_all_required_tags(self):
        evidence = {item["combo_id"]: item for item in DECISIONS["combo_pair_evidence"]}
        self.assertEqual(27, len(evidence))
        tag_map = legacy_engine.CARD_SYNERGY_TAGS
        cards = legacy_cards.CARTAS_POR_ID
        for combo in REGISTRY["combos"]:
            old_id = combo["combo_id"].removeprefix("combo.")
            item = evidence[old_id]
            left, right = item["distinct_participant_example"]
            self.assertNotEqual(left, right)
            self.assertIn(left, cards)
            self.assertIn(right, cards)
            participant_tags = set(tag_map[left]) | set(tag_map[right])
            required_tags = set(combo["required_tags"])
            self.assertTrue(required_tags <= participant_tags, old_id)
            self.assertTrue(set(tag_map[left]) & required_tags or set(tag_map[right]) & required_tags, old_id)

    def test_five_orphan_combo_ids_are_explicitly_excluded(self):
        expected = {
            "gwent_unidade_cruzado",
            "gwent_unidade_evangelista",
            "gwent_unidade_missionario",
            "gwent_unidade_protetor",
            "gwent_unidade_sacerdote",
        }
        self.assertEqual(expected, set(ALIASES["orphan_synergy_card_ids"]))
        self.assertTrue(expected.isdisjoint(legacy_cards.CARTAS_POR_ID))

    def test_all_ten_leaders_are_mapped(self):
        entries = LEADERS["leaders"]
        self.assertEqual(10, len(entries))
        self.assertEqual(set(legacy_engine.LEADERS), {item["leader_id"] for item in entries})

    def test_four_faction_passives_are_separate_from_individual_effects(self):
        entries = FACTIONS["passives"]
        self.assertEqual(4, len(entries))
        self.assertEqual(4, len({item["faction_id"] for item in entries}))
        self.assertTrue(all(item["passive_id"] == "faction.first_unit_of_faction_each_round" for item in entries))

    def test_each_legacy_entry_has_keep_merge_redesign_or_remove_disposition(self):
        from collections import Counter
        generic_recommendations = Counter(item["proposed_disposition"] for item in GENERIC_ALIASES)
        identity_recommendations = Counter(item["proposed_disposition"] for item in IDENTITY_ALIASES)
        stale_recommendations = Counter(item["proposed_disposition"] for item in STALE_ALIASES)
        self.assertEqual(29, generic_recommendations["MERGE_AS_PARAMETERIZED_FAMILY"])
        self.assertEqual(29, generic_recommendations["KEEP_AS_CANDIDATE_PENDING_BEHAVIOR_TEST"])
        self.assertEqual(1, generic_recommendations["REDESIGN_AS_EXPLICIT_ROUND_END_EFFECT; NEW_HANDLER_REQUIRED"])
        self.assertEqual(5, identity_recommendations["KEEP_AS_SINGLE_CARD_EFFECT_CANDIDATE"])
        self.assertEqual(8, identity_recommendations["MERGE_AS_PARAMETERIZED_FAMILY"])
        self.assertEqual(9, identity_recommendations["REDESIGN_OR_SPLIT_AFTER_BEHAVIOR_REVIEW"])
        self.assertEqual(9, stale_recommendations["REMOVE_FROM_NEW_RUNTIME; PRESERVE_OPTIONAL_ALIAS_METADATA"])
        self.assertEqual(15, stale_recommendations["REMOVE_FROM_NEW_RUNTIME_UNLESS_EXPLICITLY_REASSIGNED"])
        self.assertEqual(4, stale_recommendations["REMOVE_UNREGISTERED_FIELD_EFFECT_FROM_NEW_RUNTIME"])

    def test_sequence_power_requires_an_explicit_previous_play(self):
        effect = EFFECT_BY_ID["effect.sequence_power"]
        self.assertIn("requires_previous_play", effect["required_parameters"])
        self.assertEqual("boolean", effect["parameters"]["requires_previous_play"]["type"])
        aliases = [item for item in GENERIC_ALIASES if item["canonical_effect_id"] == "effect.sequence_power"]
        aliases += [item for item in IDENTITY_ALIASES if item["canonical_effect_id"] == "effect.sequence_power"]
        self.assertGreaterEqual(len(aliases), 3)
        self.assertTrue(all(item["default_effect_params"].get("requires_previous_play") is True for item in aliases))

    def test_lifecycle_gloria_is_not_treated_as_proven_equivalent_to_unimplemented_survivente(self):
        hidden = {item["legacy_id"]: item for item in ALIASES["hidden_lifecycle_aliases"]}
        self.assertIn("REDESIGN_AS_EXPLICIT_ROUND_END_EFFECT", hidden["gloria"]["proposed_disposition"])
        self.assertIn("UNIMPLEMENTED_LEGACY_TEXT", hidden["sobrevivente"]["proposed_disposition"])
        self.assertEqual("ARCHIVE_UNIMPLEMENTED_TEXT; NO_AUTOMATIC_MIGRATION", hidden["sobrevivente"]["disposition"])
        survivor_alias = next(item for item in GENERIC_ALIASES if item["legacy_id"] == "sobrevivente")
        self.assertIn("NEW_HANDLER_REQUIRED", survivor_alias["proposed_disposition"])

    def test_artifact_remains_candidate_not_approved(self):
        self.assertIn("CANDIDATE", REGISTRY.get("status", "CANDIDATE"))
        self.assertIn("NOT AN APPROVED", DECISIONS["metadata"]["status"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EffectCatalogCandidateTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
