from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import RARITY_IDS
from sistemas.card_engine_v2.deck_builder import (
    DECK_SIZE,
    MAX_COPIES_PER_CARD,
    AlphaDeckBuilder,
)
from sistemas.card_engine_v2.errors import InvalidOperation
from tests.card_engine_v2.support import mechanics_catalog


class AlphaDeckBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.catalog = mechanics_catalog(self.temp.name)
        self.builder = AlphaDeckBuilder(self.catalog)
        definitions = {card_id: self.catalog.definition_for(card_id) for card_id in self.catalog.allowed_card_ids()}
        units = sorted(card_id for card_id, item in definitions.items() if item.get("kind") == "unit")
        specials = sorted(card_id for card_id, item in definitions.items() if item.get("kind") == "special")
        self.unique_cards = units[:7] + specials[:3]
        self.card_ids = self.unique_cards * 3
        self.owned = {card_id: 3 for card_id in set(self.card_ids)}
        self.rarity_names = {value: key for key, value in RARITY_IDS.items()}
        self.exemplar_ids = list(range(50001, 50031))
        self.owned_exemplars = {}
        for index, (exemplar_id, card_id) in enumerate(zip(self.exemplar_ids, self.card_ids)):
            definition = definitions[card_id]
            power_base = definition.get("power_base")
            self.owned_exemplars[exemplar_id] = {
                "exemplar_id": exemplar_id,
                "owner_player_id": "1001",
                "card_id": card_id,
                "rarity": self.rarity_names[definition.get("rarity_id") or "common"],
                "power": (power_base + (index % 3)) if definition.get("kind") == "unit" else 1,
            }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_official_30_card_deck_accepts_mixed_units_and_specials(self):
        report = self.builder.validate(
            self.card_ids,
            leader_id="mestre_eclipse",
            faction_id="dark_moon",
            owned_card_counts=self.owned,
        )
        self.assertTrue(report.valid, report.errors)
        self.assertEqual(report.card_count, DECK_SIZE)
        self.assertEqual(report.unique_card_count, 10)
        self.assertEqual(sum(report.counts_by_card_id.values()), 30)
        self.assertEqual(report.unit_count + report.special_count, 30)
        self.assertGreater(report.special_count, 0)

    def test_deck_must_have_exactly_30_cards(self):
        report = self.builder.validate(self.card_ids[:-1], owned_card_counts=self.owned)
        self.assertFalse(report.valid)
        self.assertIn("deck_must_contain_exactly_30_cards", report.errors)

    def test_more_than_three_copies_is_rejected(self):
        deck = [self.card_ids[0]] * 4 + self.card_ids[4:30]
        report = self.builder.validate(deck, owned_card_counts={card_id: 4 for card_id in set(deck)})
        self.assertFalse(report.valid)
        self.assertTrue(any(item.startswith("copy_limit_exceeded:") for item in report.errors))
        self.assertEqual(MAX_COPIES_PER_CARD, 3)

    def test_non_allowlisted_models_are_rejected(self):
        deck = list(self.card_ids)
        deck[0] = "arma_agulha_astro"
        report = self.builder.validate(deck, owned_card_counts=self.owned)
        self.assertFalse(report.valid)
        self.assertIn("card_not_allowlisted:arma_agulha_astro", report.errors)

    def test_invalid_entry_types_are_rejected_without_crashing(self):
        deck = list(self.card_ids)
        deck[0] = {"card_id": "arma_lanca_fornalha"}
        report = self.builder.validate(deck, owned_card_counts=self.owned)
        self.assertFalse(report.valid)
        self.assertIn("deck_contains_invalid_card_id_entries", report.errors)

    def test_collection_inventory_is_enforced(self):
        owned = dict(self.owned)
        first = self.card_ids[0]
        owned[first] = 2
        report = self.builder.validate(self.card_ids, owned_card_counts=owned)
        self.assertFalse(report.valid)
        self.assertIn(f"not_enough_owned_copies:{first}:3:2", report.errors)

    def test_invalid_owned_inventory_values_fail_closed(self):
        owned = dict(self.owned)
        owned[self.card_ids[0]] = True
        report = self.builder.validate(self.card_ids, owned_card_counts=owned)
        self.assertFalse(report.valid)
        self.assertTrue(any(item.startswith("invalid_owned_count:") for item in report.errors))

    def test_leader_and_player_faction_must_match(self):
        report = self.builder.validate(
            self.card_ids,
            faction_id="dark_moon",
            leader_id="comandante_fornalha",
            owned_card_counts=self.owned,
        )
        self.assertFalse(report.valid)
        self.assertIn("leader_faction_mismatch", report.errors)

    def test_shuffle_is_reproducible_when_seeded_and_never_mutates_input(self):
        original = tuple(self.card_ids)
        first = self.builder.prepare(self.card_ids, shuffle_seed="match-1", owned_card_counts=self.owned)
        second = self.builder.prepare(self.card_ids, shuffle_seed="match-1", owned_card_counts=self.owned)
        third = self.builder.prepare(self.card_ids, shuffle_seed="match-2", owned_card_counts=self.owned)
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)
        self.assertEqual(tuple(self.card_ids), original)
        self.assertCountEqual(first, original)

    def test_official_rules_are_not_replaced_by_unapproved_12_card_budget_proposal(self):
        deck = list(self.card_ids)
        report = self.builder.validate(deck, owned_card_counts=self.owned)
        self.assertTrue(report.valid, report.errors)
        # No 32-point/12-card experimental budget is calculated here.
        self.assertNotIn("deck_cost", report.to_dict())


    def test_exact_exemplar_provenance_validates_one_physical_copy_per_slot(self):
        report = self.builder.validate(
            self.card_ids,
            exemplar_ids=self.exemplar_ids,
            owned_exemplars=self.owned_exemplars,
            owner_player_id="1001",
            leader_id="mestre_eclipse",
            faction_id="dark_moon",
        )
        self.assertTrue(report.valid, report.errors)
        self.assertEqual(report.exemplar_count, DECK_SIZE)
        self.assertEqual(report.selected_exemplar_ids, tuple(self.exemplar_ids))

    def test_duplicate_physical_exemplar_cannot_fill_two_slots(self):
        duplicate_ids = list(self.exemplar_ids)
        duplicate_ids[-1] = duplicate_ids[0]
        report = self.builder.validate(
            self.card_ids,
            exemplar_ids=duplicate_ids,
            owned_exemplars=self.owned_exemplars,
            owner_player_id="1001",
        )
        self.assertFalse(report.valid)
        self.assertIn("duplicate_exemplar_id_in_deck", report.errors)

    def test_exemplar_owner_must_match_authenticated_player(self):
        report = self.builder.validate(
            self.card_ids,
            exemplar_ids=self.exemplar_ids,
            owned_exemplars=self.owned_exemplars,
            owner_player_id="2002",
        )
        self.assertFalse(report.valid)
        self.assertTrue(any(item.startswith("exemplar_owner_mismatch:") for item in report.errors))

    def test_exemplar_model_must_match_its_deck_slot(self):
        altered = dict(self.owned_exemplars)
        wrong = dict(altered[self.exemplar_ids[0]])
        wrong["card_id"] = self.card_ids[1]
        altered[self.exemplar_ids[0]] = wrong
        report = self.builder.validate(
            self.card_ids,
            exemplar_ids=self.exemplar_ids,
            owned_exemplars=altered,
            owner_player_id="1001",
        )
        self.assertFalse(report.valid)
        self.assertIn(
            f"exemplar_card_mismatch:{self.exemplar_ids[0]}:{self.card_ids[0]}",
            report.errors,
        )

    def test_missing_or_invalid_unit_power_fails_closed(self):
        altered = dict(self.owned_exemplars)
        first_unit_id = self.exemplar_ids[0]
        first_unit = dict(altered[first_unit_id])
        first_unit["power"] = 0
        altered[first_unit_id] = first_unit
        report = self.builder.validate(
            self.card_ids,
            exemplar_ids=self.exemplar_ids,
            owned_exemplars=altered,
            owner_player_id="1001",
        )
        self.assertFalse(report.valid)
        self.assertIn(f"invalid_exemplar_power:{self.card_ids[0]}", report.errors)

    def test_exemplar_slot_shuffle_keeps_card_and_physical_id_paired(self):
        slots = self.builder.prepare_exemplar_slots(
            self.card_ids,
            self.exemplar_ids,
            owner_player_id="1001",
            owned_exemplars=self.owned_exemplars,
            shuffle_seed="physical-match-1",
        )
        self.assertEqual(len(slots), 30)
        self.assertEqual({item["exemplar_id"] for item in slots}, set(self.exemplar_ids))
        for slot in slots:
            self.assertEqual(
                self.owned_exemplars[slot["exemplar_id"]]["card_id"],
                slot["card_id"],
            )

    def test_exemplar_rarity_is_classification_and_does_not_change_frozen_power(self):
        exemplar_id = self.exemplar_ids[0]
        original = dict(self.owned_exemplars[exemplar_id])
        altered = dict(original)
        altered["rarity"] = "Singular"
        definition = self.catalog.definition_for(self.card_ids[0])
        original_snapshot = self.builder.exemplar_snapshot_for(
            card_id=self.card_ids[0], definition=definition, exemplar=original
        )
        altered_snapshot = self.builder.exemplar_snapshot_for(
            card_id=self.card_ids[0], definition=definition, exemplar=altered
        )
        self.assertEqual(original_snapshot["power_base"], altered_snapshot["power_base"])
        self.assertNotEqual(original_snapshot["rarity_id"], altered_snapshot["rarity_id"])

    def test_malformed_card_id_with_exact_provenance_fails_without_crashing(self):
        malformed = list(self.card_ids)
        malformed[0] = {"card_id": self.card_ids[0]}
        report = self.builder.validate(
            malformed,
            exemplar_ids=self.exemplar_ids,
            owned_exemplars=self.owned_exemplars,
            owner_player_id="1001",
        )
        self.assertFalse(report.valid)
        self.assertIn("deck_contains_invalid_card_id_entries", report.errors)

    def test_boolean_exemplar_power_is_rejected(self):
        exemplar_id = self.exemplar_ids[0]
        exemplar = dict(self.owned_exemplars[exemplar_id])
        exemplar["power"] = True
        definition = self.catalog.definition_for(self.card_ids[0])
        with self.assertRaisesRegex(InvalidOperation, "invalid_exemplar_power"):
            self.builder.exemplar_snapshot_for(
                card_id=self.card_ids[0], definition=definition, exemplar=exemplar
            )

    def test_primordial_rarity_is_preserved_as_display_classification_only(self):
        exemplar_id = self.exemplar_ids[0]
        exemplar = dict(self.owned_exemplars[exemplar_id])
        exemplar["rarity"] = "Primordial"
        definition = self.catalog.definition_for(self.card_ids[0])
        baseline_power = self.builder.exemplar_snapshot_for(
            card_id=self.card_ids[0], definition=definition, exemplar=self.owned_exemplars[exemplar_id]
        )["power_base"]
        primordial_snapshot = self.builder.exemplar_snapshot_for(
            card_id=self.card_ids[0], definition=definition, exemplar=exemplar
        )
        self.assertEqual(primordial_snapshot["rarity_id"], "primordial")
        self.assertEqual(primordial_snapshot["power_base"], baseline_power)

    def test_require_valid_raises_domain_error(self):
        with self.assertRaises(InvalidOperation):
            self.builder.require_valid(self.card_ids[:-5])


if __name__ == "__main__":
    unittest.main()
