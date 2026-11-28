#!/usr/bin/env python3
"""Unit tests for the new canonical card data contract (no external deps)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas.card_contract import (  # noqa: E402
    CARD_SCHEMA_VERSION,
    is_pure_unit,
    minimum_pure_cards,
    validate_card_definition,
    validate_catalog,
    validate_effect_registry,
)

KNOWN_EFFECTS = {"effect.guard", "effect.hex", "effect.summon"}
KNOWN_TAGS = {"golden_order", "formation", "scarlet_veil"}


def make_unit(card_id: str, *, pure: bool = False, power: int = 7, tags=None, effect_id=None):
    tags = [] if tags is None else tags
    if not pure and effect_id is None and not tags:
        effect_id = "effect.guard"
    return {
        "schema_version": CARD_SCHEMA_VERSION,
        "card_id": card_id,
        "name": f"Carta {card_id}",
        "title": None,
        "kind": "unit",
        "faction_id": "golden_order",
        "row": "melee",
        "power_base": power,
        "effect_id": effect_id,
        "effect_params": {} if pure or effect_id is None else {"bonus": 1},
        "combo_tags": tags,
        "lore": "Uma sentinela protege as ruínas da capital caída.",
        "art_version": 1,
    }


def make_special(card_id: str):
    return {
        "schema_version": CARD_SCHEMA_VERSION,
        "card_id": card_id,
        "name": f"Especial {card_id}",
        "title": None,
        "kind": "special",
        "faction_id": "dark_moon",
        "row": None,
        "power_base": None,
        "effect_id": "effect.hex",
        "effect_params": {},
        "combo_tags": [],
        "lore": "Um rito lunar altera o curso da batalha.",
        "art_version": 1,
    }


class CardContractTests(unittest.TestCase):
    def test_minimum_pure_count_for_137_models_is_42(self):
        self.assertEqual(minimum_pure_cards(137), 42)

    def test_minimum_pure_count_rounds_up(self):
        self.assertEqual(minimum_pure_cards(1), 1)
        self.assertEqual(minimum_pure_cards(10), 3)

    def test_boolean_is_not_an_integer_power(self):
        card = make_unit("unit_boolean_power", power=True)
        result = validate_card_definition(card, known_effect_ids=KNOWN_EFFECTS, known_combo_tags=KNOWN_TAGS)
        self.assertTrue(any("power_base inteiro" in error for error in result.errors))

    def test_unit_power_minimum_is_one(self):
        card = make_unit("unit_power_zero", power=0)
        result = validate_card_definition(card, known_effect_ids=KNOWN_EFFECTS, known_combo_tags=KNOWN_TAGS)
        self.assertFalse(result.valid)

    def test_unit_power_maximum_is_fifteen(self):
        card = make_unit("unit_power_sixteen", power=16)
        result = validate_card_definition(card, known_effect_ids=KNOWN_EFFECTS, known_combo_tags=KNOWN_TAGS)
        self.assertFalse(result.valid)

    def test_power_boundary_one_is_valid(self):
        result = validate_card_definition(make_unit("unit_power_one", pure=True, power=1))
        self.assertTrue(result.valid, result.errors)

    def test_power_boundary_fifteen_is_valid(self):
        result = validate_card_definition(make_unit("unit_power_fifteen", pure=True, power=15))
        self.assertTrue(result.valid, result.errors)

    def test_special_has_no_combat_power(self):
        result = validate_card_definition(make_special("special_hex"), known_effect_ids=KNOWN_EFFECTS)
        self.assertTrue(result.valid, result.errors)

    def test_special_with_zero_power_is_rejected(self):
        card = make_special("special_bad_power")
        card["power_base"] = 0
        result = validate_card_definition(card, known_effect_ids=KNOWN_EFFECTS)
        self.assertTrue(any("power_base=null" in error for error in result.errors))

    def test_relic_is_not_a_deck_unit(self):
        card = make_special("relic_test")
        card.update({"kind": "relic"})
        result = validate_card_definition(card, known_effect_ids=KNOWN_EFFECTS)
        self.assertTrue(result.valid, result.errors)

    def test_pure_unit_has_no_effect_or_combo_tag(self):
        self.assertTrue(is_pure_unit(make_unit("unit_pure", pure=True)))
        tagged = make_unit("unit_tagged", pure=True, tags=["golden_order"])
        self.assertFalse(is_pure_unit(tagged))

    def test_effect_params_without_effect_are_rejected(self):
        card = make_unit("unit_orphan_params", pure=True)
        card["effect_params"] = {"bonus": 1}
        result = validate_card_definition(card)
        self.assertFalse(result.valid)

    def test_unknown_effect_is_rejected(self):
        card = make_unit("unit_unknown_effect", effect_id="effect.missing")
        result = validate_card_definition(card, known_effect_ids=KNOWN_EFFECTS)
        self.assertTrue(any("sem definição" in error for error in result.errors))

    def test_unknown_combo_tag_is_rejected(self):
        card = make_unit("unit_unknown_tag", pure=True, tags=["tag_missing"])
        result = validate_card_definition(card, known_combo_tags=KNOWN_TAGS)
        self.assertFalse(result.valid)

    def test_duplicate_combo_tags_are_rejected(self):
        card = make_unit("unit_duplicate_tag", pure=True, tags=["golden_order", "golden_order"])
        result = validate_card_definition(card, known_combo_tags=KNOWN_TAGS)
        self.assertFalse(result.valid)

    def test_catalog_requires_thirty_percent_pure(self):
        cards = [make_unit(f"unit_{i}", pure=False) for i in range(10)]
        cards.extend([make_special("special_a"), make_special("special_b")])
        result = validate_catalog(
            {"schema_version": 1, "cards": cards},
            known_effect_ids=KNOWN_EFFECTS,
            known_combo_tags=KNOWN_TAGS,
        )
        self.assertTrue(any("quota de cartas puras" in error for error in result.errors))

    def test_catalog_accepts_at_least_thirty_percent_pure(self):
        cards = [make_unit(f"unit_{i}", pure=i < 3) for i in range(10)]
        result = validate_catalog(
            {"schema_version": 1, "cards": cards},
            known_effect_ids=KNOWN_EFFECTS,
            known_combo_tags=KNOWN_TAGS,
        )
        self.assertTrue(result.valid, result.errors)

    def test_catalog_rejects_duplicate_ids(self):
        unit = make_unit("unit_duplicate_id", pure=True)
        result = validate_catalog(
            {"schema_version": 1, "cards": [unit, dict(unit)]},
            known_effect_ids=KNOWN_EFFECTS,
            known_combo_tags=KNOWN_TAGS,
        )
        self.assertTrue(any("card_id duplicado" in error for error in result.errors))

    def test_lore_is_required(self):
        card = make_unit("unit_no_lore", pure=True)
        card["lore"] = "  "
        result = validate_card_definition(card)
        self.assertFalse(result.valid)

    def test_unknown_fields_are_rejected(self):
        card = make_unit("unit_unknown_field", pure=True)
        card["hidden_ability"] = "ghost"
        result = validate_card_definition(card)
        self.assertFalse(result.valid)

    def test_non_ascii_card_ids_are_rejected(self):
        card = make_unit("unit_cárd", pure=True)
        result = validate_card_definition(card)
        self.assertFalse(result.valid)

    def test_malformed_kind_and_faction_do_not_crash_validator(self):
        card = make_unit("unit_malformed_types", pure=True)
        card["kind"] = ["unit"]
        card["faction_id"] = ["golden_order"]
        result = validate_card_definition(card)
        self.assertFalse(result.valid)

    def test_boolean_schema_version_is_rejected(self):
        card = make_unit("unit_boolean_schema", pure=True)
        card["schema_version"] = True
        result = validate_card_definition(card)
        self.assertFalse(result.valid)

    def test_example_files_are_valid_json(self):
        for relative in (
            "data/card_game/card-definition.schema.v1.json",
            "data/card_game/effect-registry.schema.v1.json",
            "data/card_game/card-definition.example.v1.json",
            "data/card_game/effect-registry.example.v1.json",
            "data/card_game/catalog-legacy-baseline-v0.1.json",
        ):
            with self.subTest(path=relative):
                json.loads((ROOT / relative).read_text(encoding="utf-8"))


    def _example_registry(self):
        return json.loads((ROOT / "data/card_game/effect-registry.example.v1.json").read_text(encoding="utf-8"))

    def test_example_effect_registry_is_valid(self):
        result = validate_effect_registry(self._example_registry())
        self.assertTrue(result.valid, result.errors)

    def test_effect_registry_rejects_combo_with_one_participant(self):
        registry = self._example_registry()
        registry["combos"][0]["minimum_participants"] = 1
        result = validate_effect_registry(registry)
        self.assertTrue(any("minimum_participants" in error for error in result.errors))

    def test_effect_registry_rejects_duplicate_priority(self):
        registry = self._example_registry()
        registry["combos"].append({
            "combo_id": "combo.second_formation", "name": "Segunda Formação",
            "required_tags": ["golden_order"], "minimum_participants": 2, "priority": 10,
        })
        result = validate_effect_registry(registry)
        self.assertTrue(any("priority duplicada" in error for error in result.errors))

    def test_effect_registry_rejects_duplicate_effect_id(self):
        registry = self._example_registry()
        registry["effects"].append(dict(registry["effects"][0]))
        result = validate_effect_registry(registry)
        self.assertTrue(any("effect_id duplicado" in error for error in result.errors))

    def test_catalog_rejects_missing_required_effect_parameter(self):
        registry = self._example_registry()
        card = json.loads((ROOT / "data/card_game/card-definition.example.v1.json").read_text(encoding="utf-8"))
        card["effect_params"] = {"ally_bonus": 1}
        result = validate_card_definition(
            card,
            known_effect_ids={"effect.golden_guard"},
            known_combo_tags={"golden_order", "formation"},
            effect_registry={"effect.golden_guard": registry["effects"][0]},
        )
        self.assertTrue(any("max_targets" in error for error in result.errors))

    def test_catalog_rejects_effect_parameter_out_of_range(self):
        registry = self._example_registry()
        card = json.loads((ROOT / "data/card_game/card-definition.example.v1.json").read_text(encoding="utf-8"))
        card["effect_params"]["ally_bonus"] = 4
        result = validate_card_definition(
            card,
            known_effect_ids={"effect.golden_guard"},
            known_combo_tags={"golden_order", "formation"},
            effect_registry={"effect.golden_guard": registry["effects"][0]},
        )
        self.assertTrue(any("acima do máximo" in error for error in result.errors))

    def test_catalog_rejects_undeclared_effect_parameter(self):
        registry = self._example_registry()
        card = json.loads((ROOT / "data/card_game/card-definition.example.v1.json").read_text(encoding="utf-8"))
        card["effect_params"]["hidden_multiplier"] = 3
        result = validate_card_definition(
            card,
            known_effect_ids={"effect.golden_guard"},
            known_combo_tags={"golden_order", "formation"},
            effect_registry={"effect.golden_guard": registry["effects"][0]},
        )
        self.assertTrue(any("não declarados" in error for error in result.errors))

    def test_catalog_rejects_wrong_effect_parameter_type(self):
        registry = self._example_registry()
        card = json.loads((ROOT / "data/card_game/card-definition.example.v1.json").read_text(encoding="utf-8"))
        card["effect_params"]["ally_bonus"] = True
        result = validate_card_definition(
            card,
            known_effect_ids={"effect.golden_guard"},
            known_combo_tags={"golden_order", "formation"},
            effect_registry={"effect.golden_guard": registry["effects"][0]},
        )
        self.assertTrue(any("tipo inválido" in error for error in result.errors))


    def _run_catalog_cli(self, *, invalid_parameter=False):
        example = json.loads((ROOT / "data/card_game/card-definition.example.v1.json").read_text(encoding="utf-8"))
        registry = self._example_registry()
        if invalid_parameter:
            example["effect_params"]["ally_bonus"] = 99
        cards = [example]
        for index in range(3):
            cards.append({
                "schema_version": 1,
                "card_id": f"pure_fixture_{index + 1}",
                "name": f"Unidade Pura {index + 1}",
                "title": None,
                "kind": "unit",
                "faction_id": "golden_order",
                "row": "melee",
                "power_base": 3 + index,
                "effect_id": None,
                "effect_params": {},
                "combo_tags": [],
                "lore": "Uma unidade de teste sem habilidade individual nem tags de combo.",
                "art_version": 1,
                "origin_id": "synthetic_test",
                "source_game": "Original",
            })
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            catalog_path = temp / "catalog.json"
            registry_path = temp / "registry.json"
            catalog_path.write_text(json.dumps({"schema_version": 1, "cards": cards}), encoding="utf-8")
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(ROOT / "docs/scripts/validate-card-catalog-v1.py"),
                 "--catalog", str(catalog_path), "--registry", str(registry_path)],
                capture_output=True, text=True, check=False,
            )

    def test_catalog_cli_accepts_valid_synthetic_catalog(self):
        result = self._run_catalog_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["card_count"], 4)
        self.assertTrue(payload["effect_parameter_validation"])

    def test_catalog_cli_rejects_out_of_range_effect_parameter(self):
        result = self._run_catalog_cli(invalid_parameter=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        self.assertTrue(any("acima do máximo" in error for error in payload["errors"]))

    def test_legacy_snapshot_is_137_records_and_not_the_new_catalog(self):
        data = json.loads((ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "historical_snapshot_not_runtime_source_of_truth")
        self.assertEqual(data["counts"]["catalogue_models"], 137)
        self.assertEqual(data["counts"]["units"], 110)
        self.assertEqual(data["counts"]["specials"], 21)
        self.assertEqual(data["counts"]["relics"], 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
