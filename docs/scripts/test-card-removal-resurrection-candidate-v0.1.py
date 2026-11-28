#!/usr/bin/env python3
"""Tests and source cross-checks for candidate removal/sacrifice/resurrection rules.

Synthetic candidate resolver tests are kept separate from behavior assertions
against the legacy Gwent runtime. This script does not alter the live engine.
"""
from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sistemas import card_removal_resurrection_candidate as candidate  # noqa: E402
from sistemas import gwent  # noqa: E402
from sistemas.cartas import CARTAS_POR_ID  # noqa: E402

REGISTRY_PATH = ROOT / "data/card_game/removal-resurrection-registry-candidate.v1.json"
SCHEMA_PATH = ROOT / "data/card_game/removal-resurrection-registry.schema.v1.json"
SOURCE_PATH = ROOT / "sistemas/gwent.py"
REPORT_PATH = ROOT / "docs/card-game-removal-resurrection-validation-v0.1.json"
SMOKE_HELPER_PATH = ROOT / "docs/scripts/validate-card-effect-smoke-v0.1.py"

_spec = importlib.util.spec_from_file_location("removal_resurrection_smoke_helpers", SMOKE_HELPER_PATH)
smoke = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(smoke)

REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def unit(instance_id: str, *, row: str = "melee", power: int = 3, bonus: int = 0,
         kind: str = "unit", **extra: Any) -> dict[str, Any]:
    item = {
        "instance_id": instance_id,
        "card_id": extra.pop("card_id", instance_id.split("#")[0]),
        "kind": kind,
        "power_base": power,
        "row": row,
        "bonus": bonus,
        "effect_ids": [],
        "shield": 0,
        "sangramento": 0,
        "geada": 0,
        "podrida": 0,
        "loucura": 0,
    }
    item.update(extra)
    return item


class CandidateResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidate.validate_registry(REGISTRY)

    def test_schema_is_valid_draft_2020_12(self):
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(SCHEMA)

    def test_registry_matches_schema(self):
        import jsonschema
        jsonschema.Draft202012Validator(SCHEMA).validate(REGISTRY)

    def test_registry_is_not_approved(self):
        self.assertEqual("CANDIDATE_FOR_REVIEW_NOT_APPROVED", REGISTRY["status"])

    def test_nine_assignments_have_unique_ids(self):
        assignments = REGISTRY["assignments"]
        ids = [item["assignment_id"] for item in assignments]
        self.assertEqual(9, len(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_seven_card_assignments_exist_in_legacy_catalog(self):
        mapped = {card_id for item in REGISTRY["assignments"] for card_id in item.get("card_ids", [])}
        expected = {
            "gwent_especial_queima", "gwent_especial_execucao",
            "gwent_unidade_carniceiro_forja", "gwent_v75_veu_carrasco_preco",
            "gwent_unidade_necromante", "gwent_especial_requiem", "gwent_especial_medico",
        }
        self.assertEqual(expected, mapped)
        self.assertTrue(mapped.issubset(CARTAS_POR_ID))

    def test_three_removal_causes_are_explicit(self):
        self.assertEqual(
            {"normal_removal", "execution", "sacrifice"},
            {item["cause_id"] for item in REGISTRY["removal_policy"]["causes"]},
        )

    def test_unknown_removal_cause_is_rejected(self):
        side = {"board": [], "discard": []}
        with self.assertRaises(candidate.RemovalResurrectionError):
            candidate.attempt_removal(side, unit("missing"), "delete")

    def test_non_board_unit_is_not_removed(self):
        victim = unit("outside")
        side = {"board": [], "discard": [], "baixas": 0}
        result = candidate.attempt_removal(side, victim, "normal_removal")
        self.assertFalse(result.removed)
        self.assertEqual([], side["discard"])
        self.assertEqual(0, side["baixas"])

    def test_normal_removal_is_blocked_by_shield_and_consumes_one_charge(self):
        for cause in ("normal_removal", "execution"):
            with self.subTest(cause=cause):
                victim = unit("shielded", shield=2)
                side = {"board": [victim], "discard": [], "baixas": 0}
                result = candidate.attempt_removal(side, victim, cause)
                self.assertTrue(result.blocked_by_shield)
                self.assertEqual(1, victim["shield"])
                self.assertIs(victim, side["board"][0])
                self.assertEqual([], side["discard"])
                self.assertEqual(0, side["baixas"])

    def test_sacrifice_bypasses_shield(self):
        victim = unit("sacrifice-shield", shield=1)
        side = {"board": [victim], "discard": [], "baixas": 0}
        result = candidate.attempt_removal(side, victim, "sacrifice")
        self.assertTrue(result.removed)
        self.assertFalse(result.blocked_by_shield)
        self.assertNotIn(victim, side["board"])
        self.assertIs(victim, side["discard"][0])

    def test_successful_removal_clears_shield_and_all_four_states(self):
        victim = unit("marked", shield=1, sangramento=1, geada=2, podrida=1, loucura=2)
        side = {"board": [victim], "discard": [], "baixas": 0}
        result = candidate.attempt_removal(side, victim, "sacrifice")
        self.assertTrue(result.removed)
        self.assertNotIn("shield", victim)
        self.assertEqual({key: 0 for key in ("sangramento", "geada", "podrida", "loucura")},
                         {key: victim[key] for key in ("sangramento", "geada", "podrida", "loucura")})
        self.assertEqual(1, side["baixas"])

    def test_successful_removal_increments_counter_including_sacrifice(self):
        for cause in ("normal_removal", "execution", "sacrifice"):
            victim = unit(f"victim-{cause}")
            side = {"board": [victim], "discard": [], "baixas": 4}
            result = candidate.attempt_removal(side, victim, cause)
            self.assertTrue(result.removed)
            self.assertEqual(5, side["baixas"])

    def test_blocked_removal_does_not_trigger_vengeance(self):
        victim = unit("vengeance-blocked", shield=1, habilidade="vinganca", row="ranged")
        ally = unit("ally", row="ranged", bonus=2)
        side = {"board": [victim, ally], "discard": [], "baixas": 0}
        result = candidate.attempt_removal(side, victim, "execution")
        self.assertFalse(result.removed)
        self.assertEqual(2, ally["bonus"])
        self.assertEqual(0, result.vengeance_targets)

    def test_vengeance_affects_only_remaining_allies_in_same_row(self):
        victim = unit("vengeance", row="ranged", effect_ids=["effect.vengeance_on_removal"])
        same_a = unit("same-a", row="ranged", bonus=1)
        same_b = unit("same-b", row="ranged", bonus=-1)
        other = unit("other", row="siege", bonus=3)
        side = {"board": [victim, same_a, same_b, other], "discard": [], "baixas": 0}
        result = candidate.attempt_removal(side, victim, "sacrifice")
        self.assertEqual(2, result.vengeance_targets)
        self.assertEqual((2, 0, 3), (same_a["bonus"], same_b["bonus"], other["bonus"]))

    def test_candidate_removal_uses_exact_object_identity_for_equal_dict_copies(self):
        decoy = unit("same-card#1", card_id="same-card")
        intended = unit("same-card#2", card_id="same-card")
        # Both objects are equal except for per-copy id. Simulate a corrupt or
        # legacy payload in which the physical instance identifiers are absent.
        decoy.pop("instance_id")
        intended.pop("instance_id")
        decoy.pop("card_id")
        intended.pop("card_id")
        self.assertEqual(decoy, intended)
        side = {"board": [decoy, intended], "discard": [], "baixas": 0}
        result = candidate.attempt_removal(side, intended, "sacrifice")
        self.assertTrue(result.removed)
        self.assertIs(intended, side["discard"][0])
        self.assertIs(decoy, side["board"][0])

    def test_vengeance_legacy_alias_is_accepted_by_candidate_adapter(self):
        victim = unit("vengeance-old", habilidade="vinganca")
        ally = unit("old-ally", bonus=0)
        side = {"board": [victim, ally], "discard": [], "baixas": 0}
        candidate.attempt_removal(side, victim, "normal_removal")
        self.assertEqual(1, ally["bonus"])

    def test_canonical_singular_effect_id_activates_vengeance(self):
        victim = unit("vengeance-canonical", effect_id="effect.vengeance_on_removal")
        ally = unit("canonical-ally", bonus=2)
        side = {"board": [victim, ally], "discard": [], "baixas": 0}
        result = candidate.attempt_removal(side, victim, "sacrifice")
        self.assertEqual(1, result.vengeance_targets)
        self.assertEqual(3, ally["bonus"])

    def test_removal_then_resurrection_returns_a_clean_unit(self):
        victim = unit("roundtrip", shield=1, sangramento=2, geada=1, podrida=1, loucura=1)
        side = {"board": [victim], "discard": [], "baixas": 0}
        removed = candidate.attempt_removal(side, victim, "sacrifice")
        self.assertTrue(removed.removed)
        revived = candidate.resurrect_from_discard(
            side, max_power=5, row="ranged", target_instance_id="roundtrip"
        ).resurrected
        self.assertEqual([0, 0, 0, 0], [revived[k] for k in ("sangramento", "geada", "podrida", "loucura")])
        self.assertNotIn("shield", revived)
        self.assertEqual(1, side["baixas"])

    def test_resurrected_combo_tag_can_contribute_to_a_later_play(self):
        returned_source = unit("eco-copy#1", card_id="gwent_unidade_eco", power=4)
        returned_source["id"] = "gwent_unidade_eco"
        side = {"board": [], "discard": [returned_source]}
        revived = candidate.resurrect_from_discard(
            side, max_power=5, row="melee", target_instance_id="eco-copy#1"
        ).resurrected
        player = {"board": [revived], "synergy_used": {}}
        later_card = smoke.unit("magia_orbe_eco", row="melee", power=0, special=True)
        activated = gwent._aplicar_combo_de_cartas(player, later_card)
        self.assertEqual("Eco das Pedras Cintilantes", activated)
        self.assertEqual("eco_convergente", later_card["combo_ativado"])

    def test_resurrection_selects_strongest_eligible_unit(self):
        side = {"discard": [unit("weak", power=2), unit("strong", power=5), unit("too-strong", power=6)], "board": []}
        result = candidate.resurrect_from_discard(side, max_power=5, row="melee")
        self.assertEqual("strong", result.resurrected["instance_id"])
        self.assertEqual(["weak", "too-strong"], [item["instance_id"] for item in side["discard"]])

    def test_resurrection_removes_exactly_one_physical_copy(self):
        copy_a = unit("same-card#1", card_id="same-card", power=4)
        copy_b = unit("same-card#2", card_id="same-card", power=4)
        side = {"discard": [copy_a, copy_b], "board": []}
        result = candidate.resurrect_from_discard(side, max_power=5, row="melee", target_instance_id="same-card#2")
        self.assertEqual("same-card#2", result.resurrected["instance_id"])
        self.assertEqual([copy_a], side["discard"])

    def test_card_id_selector_is_rejected_when_duplicate_copies_exist(self):
        side = {"discard": [unit("copy#1", card_id="copy"), unit("copy#2", card_id="copy")], "board": []}
        with self.assertRaisesRegex(candidate.RemovalResurrectionError, "ambíguo"):
            candidate.resurrect_from_discard(side, max_power=5, row="melee", target_card_id="copy")

    def test_card_id_selector_is_allowed_if_unique(self):
        side = {"discard": [unit("copy#1", card_id="copy")], "board": []}
        result = candidate.resurrect_from_discard(side, max_power=5, row="melee", target_card_id="copy")
        self.assertEqual("copy#1", result.resurrected["instance_id"])
        self.assertEqual("unique_legacy_card_id", result.selected_by)

    def test_special_cards_are_never_eligible(self):
        side = {"discard": [unit("special", kind="special", power=1), unit("unit", kind="unit", power=1)], "board": []}
        result = candidate.resurrect_from_discard(side, max_power=5, row="melee")
        self.assertEqual("unit", result.resurrected["instance_id"])

    def test_resurrection_clears_statuses_and_shield(self):
        stale = unit("stale", shield=1, sangramento=2, geada=2, podrida=1, loucura=2)
        side = {"discard": [stale], "board": []}
        revived = candidate.resurrect_from_discard(side, max_power=5, row="ranged").resurrected
        self.assertFalse("shield" in revived)
        self.assertEqual([0, 0, 0, 0], [revived[key] for key in ("sangramento", "geada", "podrida", "loucura")])

    def test_resurrection_bonus_modes_are_explicit(self):
        for mode, expected in (("reset_to_zero", 0), ("add_one_to_existing_bonus", 4), ("preserve", 3)):
            side = {"discard": [unit(f"bonus-{mode}", bonus=3)], "board": []}
            result = candidate.resurrect_from_discard(side, max_power=5, row="melee", entry_bonus_mode=mode)
            self.assertEqual(expected, result.resurrected["bonus"])

    def test_resurrection_preserves_valid_row_or_uses_fallback(self):
        side = {"discard": [unit("valid-row", row="siege"), unit("bad-row", row="invalid")], "board": []}
        candidate.resurrect_from_discard(side, max_power=5, row="ranged", target_instance_id="valid-row")
        revived = candidate.resurrect_from_discard(side, max_power=5, row="ranged", target_instance_id="bad-row")
        self.assertEqual("siege", side["board"][0]["row"])
        self.assertEqual("ranged", revived.resurrected["row"])

    def test_resurrection_can_force_selected_row(self):
        side = {"discard": [unit("force", row="siege")], "board": []}
        result = candidate.resurrect_from_discard(side, max_power=5, row="ranged", row_mode="force_selected_row")
        self.assertEqual("ranged", result.resurrected["row"])

    def test_resurrection_tie_break_is_first_discard_order(self):
        side = {"discard": [unit("first", power=4), unit("second", power=4)], "board": []}
        result = candidate.resurrect_from_discard(side, max_power=5, row="melee")
        self.assertEqual("first", result.resurrected["instance_id"])

    def test_resurrection_does_not_decrement_removal_counter(self):
        side = {"discard": [unit("return")], "board": [], "baixas": 3}
        candidate.resurrect_from_discard(side, max_power=5, row="melee")
        self.assertEqual(3, side["baixas"])

    def test_return_to_hand_preserves_legacy_payload_fields(self):
        stale = unit("to-hand", bonus=4, sangramento=1, shield=1)
        side = {"discard": [stale], "hand": []}
        returned = candidate.recover_unit_to_hand(side, max_power=5)
        self.assertIs(stale, returned)
        self.assertEqual(4, returned["bonus"])
        self.assertEqual(1, returned["sangramento"])
        self.assertEqual(1, returned["shield"])
        self.assertEqual([stale], side["hand"])

    def test_recovery_selects_last_eligible_by_default(self):
        first, last = unit("first"), unit("last")
        side = {"discard": [first, last], "hand": []}
        returned = candidate.recover_unit_to_hand(side, max_power=5)
        self.assertIs(last, returned)

    def test_invalid_canonical_power_is_rejected(self):
        side = {"discard": [unit("bad", power="four")], "board": []}
        with self.assertRaises(candidate.RemovalResurrectionError):
            candidate.resurrect_from_discard(side, max_power=5, row="melee")


class LegacyRuntimeEvidenceTests(unittest.TestCase):
    def test_legacy_removal_shield_blocks_and_consumes_charge(self):
        victim = smoke.unit("legacy-shield", escudo=1)
        side = {"board": [victim], "discard": [], "baixas": 0}
        text = gwent._remover_unidade(side, victim, "execucao")
        self.assertIn("resistiu", text)
        self.assertEqual(0, victim["escudo"])
        self.assertEqual([victim], side["board"])
        self.assertEqual([], side["discard"])
        self.assertEqual(0, side["baixas"])

    def test_legacy_removal_by_equal_dict_can_remove_wrong_physical_object(self):
        first = smoke.unit("duplicate", row="melee", power=3)
        second = smoke.unit("duplicate", row="melee", power=3)
        self.assertEqual(first, second)
        side = {"board": [first, second], "discard": [], "baixas": 0}
        gwent._remover_unidade(side, second, "sacrificio")
        # list.remove uses dict equality, so the first equal dictionary is
        # discarded even though the caller passed the second object.
        self.assertIs(second, side["board"][0])
        self.assertIs(second, side["discard"][0])
        self.assertIsNot(first, side["board"][0])
        self.assertIsNot(first, side["discard"][0])

    def test_legacy_sacrifice_bypasses_shield_and_clears_statuses(self):
        victim = smoke.unit("legacy-sacrifice", escudo=1, sangramento=1, geada=1, podrida=1, loucura=1)
        side = {"board": [victim], "discard": [], "baixas": 0}
        gwent._remover_unidade(side, victim, "sacrificio")
        self.assertEqual([], side["board"])
        self.assertEqual([victim], side["discard"])
        self.assertEqual(1, side["baixas"])
        self.assertFalse("escudo" in victim)
        self.assertEqual([0, 0, 0, 0], [victim[k] for k in ("sangramento", "geada", "podrida", "loucura")])

    def test_legacy_vengeance_triggers_on_successful_sacrifice(self):
        victim = smoke.unit("legacy-vengeance", skill="vinganca", row="ranged")
        ally = smoke.unit("legacy-ally", row="ranged", bonus=2)
        other_row = smoke.unit("legacy-other-row", row="siege", bonus=2)
        side = {"board": [victim, ally, other_row], "discard": [], "baixas": 0}
        gwent._remover_unidade(side, victim, "sacrificio")
        self.assertEqual(3, ally["bonus"])
        self.assertEqual(2, other_row["bonus"])

    def test_execution_rarity_formula_is_constant_six(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("min(6, 6 + potencia_raridade)", source)
        for budget in (0, 1, 2, 3):
            self.assertEqual(6, min(6, 6 + budget))

    def test_legacy_esgar_removes_all_copies_with_same_card_id(self):
        base = smoke.unit("leader_fixture")
        state = smoke.fixture(base, "melee")
        player = state["players"]["1"]
        player["faction"] = "Véu Carmesim"
        player["leader_id"] = "voz_caidos"
        player["leader_used"] = False
        player["discard"] = [
            smoke.unit("same_card_id", power=4, nome="Copy A"),
            smoke.unit("same_card_id", power=5, nome="Copy B"),
            smoke.unit("unrelated", power=3),
        ]
        player["hand"] = [smoke.unit("leader_reserve")]
        state["turn"] = "1"
        result = gwent.aplicar_jogada(state, 1, action="leader", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        self.assertEqual(["unrelated"], [item["id"] for item in after["discard"]])
        self.assertEqual(1, sum(item.get("id") == "same_card_id" for item in after["board"]))

    def test_legacy_execution_threshold_stays_six_even_at_singular_rarity(self):
        card = smoke.unit("execution", skill="gwent_execucao", special=True, power=0, rarity="Singular")
        state = smoke.fixture(card, "melee")
        player, enemy = state["players"]["1"], state["players"]["2"]
        player["hand"] = [card, smoke.unit("reserve")]
        enemy["board"] = [smoke.unit("too-strong", row="melee", power=7)]
        rejected = gwent.aplicar_jogada(state, 1, card_id="execution", action="play", row="melee")
        self.assertIn("error", rejected)
        self.assertIn("6 ou menos", rejected["error"])

        card2 = smoke.unit("execution-shield", skill="gwent_execucao", special=True, power=0, rarity="Singular")
        state2 = smoke.fixture(card2, "melee")
        player2, enemy2 = state2["players"]["1"], state2["players"]["2"]
        player2["hand"] = [card2, smoke.unit("reserve2")]
        enemy2["board"] = [smoke.unit("six-with-shield", row="melee", power=6, escudo=1)]
        accepted = gwent.aplicar_jogada(state2, 1, card_id="execution-shield", action="play", row="melee")
        self.assertNotIn("error", accepted)
        after = accepted["state"]["players"]["2"]
        self.assertEqual(0, after["board"][0]["escudo"])
        self.assertEqual([], after["discard"])

    def test_legacy_blood_price_identity_sacrifices_even_shielded_ally(self):
        from sistemas.cartas import CARTAS_POR_ID
        card = CARTAS_POR_ID["gwent_v75_veu_carrasco_preco"].para_dict()
        card.update({"bonus": 0, "row": "melee", "escudo": 0, "sangramento": 0,
                     "geada": 0, "podrida": 0, "loucura": 0})
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        player["faction"] = "Véu Carmesim"
        player["hand"] = [card, smoke.unit("blood-price-reserve")]
        player["board"] = [smoke.unit("blood-price-victim", row="melee", power=3, escudo=1),
                            smoke.unit("blood-price-ally", row="melee", power=5)]
        result = gwent.aplicar_jogada(state, 1, card_id=card["id"], action="play", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        played = next(item for item in after["board"] if item["id"] == card["id"])
        self.assertEqual(4, played["bonus"])
        self.assertTrue(any(item["id"] == "blood-price-victim" for item in after["discard"]))
        self.assertEqual(0, next(item for item in after["discard"] if item["id"] == "blood-price-victim")["escudo"]
                         if "escudo" in next(item for item in after["discard"] if item["id"] == "blood-price-victim") else 0)

    def test_legacy_requiem_power_limit_uses_rarity_budget(self):
        card = smoke.unit("requiem-limit", skill="gwent_requiem", special=True, power=0, rarity="Épica")
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        player["hand"] = [card, smoke.unit("requiem-reserve")]
        player["discard"] = [smoke.unit("power-seven", power=7), smoke.unit("power-eight", power=8)]
        result = gwent.aplicar_jogada(state, 1, card_id="requiem-limit", action="play", row="ranged")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        self.assertTrue(any(item["id"] == "power-seven" for item in after["board"]))
        self.assertTrue(any(item["id"] == "power-eight" for item in after["discard"]))

    def test_legacy_devour_without_ally_is_silent_noop(self):
        card = smoke.unit("devourer", skill="devorar", power=4)
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        player["board"] = []
        player["hand"] = [card, smoke.unit("reserve")]
        player["discard"] = []
        result = gwent.aplicar_jogada(state, 1, card_id="devourer", action="play", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        played = next(item for item in after["board"] if item["id"] == "devourer")
        self.assertEqual(0, played["bonus"])
        self.assertEqual([], after["discard"])

    def test_legacy_ressurgir_does_not_clear_stale_status_fields(self):
        card = smoke.unit("resurrection_card", skill="ressurgir", power=4)
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        player["hand"] = [card, smoke.unit("reserve")]
        player["discard"] = [smoke.unit("stale_return", power=5, geada=1, podrida=1, sangramento=1, loucura=1, escudo=1)]
        result = gwent.aplicar_jogada(state, 1, card_id="resurrection_card", action="play", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        revived = next(item for item in after["board"] if item["id"] == "stale_return")
        self.assertEqual([1, 1, 1, 1], [revived[k] for k in ("sangramento", "geada", "podrida", "loucura")])

    def test_legacy_requiem_does_not_clear_stale_status_fields(self):
        card = smoke.unit("requiem", skill="gwent_requiem", special=True, power=0)
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        player["hand"] = [card, smoke.unit("reserve")]
        player["discard"] = [smoke.unit("stale_requiem", power=5, geada=1, podrida=1, sangramento=1, loucura=1, escudo=1)]
        result = gwent.aplicar_jogada(state, 1, card_id="requiem", action="play", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        revived = next(item for item in after["board"] if item["id"] == "stale_requiem")
        self.assertEqual([1, 1, 1, 1], [revived[k] for k in ("sangramento", "geada", "podrida", "loucura")])

    def test_legacy_esgar_clears_statuses_but_adds_to_existing_bonus(self):
        base = smoke.unit("leader_fixture")
        state = smoke.fixture(base, "melee")
        player = state["players"]["1"]
        player["faction"] = "Véu Carmesim"
        player["leader_id"] = "voz_caidos"
        player["leader_used"] = False
        stale = smoke.unit("esgar_stale", power=5, bonus=3, geada=1, podrida=1, sangramento=1, loucura=1, escudo=1)
        player["discard"] = [stale]
        player["hand"] = [smoke.unit("leader_reserve")]
        result = gwent.aplicar_jogada(state, 1, action="leader", row="siege")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        revived = next(item for item in after["board"] if item["id"] == "esgar_stale")
        self.assertEqual(4, revived["bonus"])
        self.assertEqual([0, 0, 0, 0], [revived[k] for k in ("sangramento", "geada", "podrida", "loucura")])

    def test_legacy_devour_vengeance_buffs_remaining_ally_before_devour_gain(self):
        card = smoke.unit("devourer-veng", skill="devorar", power=4)
        state = smoke.fixture(card, "melee")
        player = state["players"]["1"]
        victim = smoke.unit("vengeance-victim", skill="vinganca", row="melee", power=2)
        survivor = smoke.unit("survivor", row="melee", power=5, bonus=0)
        player["board"] = [victim, survivor]
        player["hand"] = [card, smoke.unit("devourer-reserve")]
        result = gwent.aplicar_jogada(state, 1, card_id="devourer-veng", action="play", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        played = next(item for item in after["board"] if item["id"] == "devourer-veng")
        remaining = next(item for item in after["board"] if item["id"] == "survivor")
        self.assertEqual(2, played["bonus"])  # ganho pelo poder efetivo da vítima, sem receber Vingança
        self.assertEqual(1, remaining["bonus"])  # Vingança atinge apenas aliados já presentes
        self.assertTrue(any(item["id"] == "vengeance-victim" for item in after["discard"]))

    def test_legacy_rykard_stacks_vengeance_then_row_bonus(self):
        base = smoke.unit("rykard_fixture")
        state = smoke.fixture(base, "melee")
        player = state["players"]["1"]
        player["faction"] = "Véu Carmesim"
        player["leader_id"] = "sombra_caminhante"
        player["leader_used"] = False
        victim = smoke.unit("rykard_victim", skill="vinganca", row="melee", power=1)
        ally_a = smoke.unit("rykard_ally_a", row="melee", power=3, bonus=0)
        ally_b = smoke.unit("rykard_ally_b", row="melee", power=4, bonus=0)
        player["board"] = [victim, ally_a, ally_b]
        player["hand"] = [smoke.unit("rykard_reserve")]
        result = gwent.aplicar_jogada(state, 1, action="leader", row="melee")
        self.assertNotIn("error", result)
        after = result["state"]["players"]["1"]
        self.assertEqual(3, next(item for item in after["board"] if item["id"] == "rykard_ally_a")["bonus"])
        self.assertEqual(3, next(item for item in after["board"] if item["id"] == "rykard_ally_b")["bonus"])
        self.assertTrue(any(item["id"] == "rykard_victim" for item in after["discard"]))

    def test_legacy_resurrection_is_appended_after_combo_resolution(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        segment_start = source.index("# Habilidade exclusiva da carta, depois das habilidades gerais e antes dos combos.")
        segment_end = source.index('player["last_row"] = row', segment_start)
        play_segment = source[segment_start:segment_end]
        combo_pos = play_segment.index("_aplicar_combo_de_cartas(player, card)")
        played_append_pos = play_segment.index('player["board"].append(card)')
        revived_append_pos = play_segment.index('player["board"].append(unidade_revivida)')
        self.assertLess(combo_pos, played_append_pos)
        self.assertLess(played_append_pos, revived_append_pos)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "metadata": {
            "document": "Removal, sacrifice and resurrection candidate validation v0.1",
            "status": "CANDIDATE_FOR_REVIEW_NOT_APPROVED",
            "runtime_integration": False,
            "scope": "Independent candidate resolver tests plus controlled evidence against current legacy engine; not a production match/API test.",
        },
        "counts": {
            "tests": result.testsRun,
            "passed": result.testsRun - len(result.failures) - len(result.errors),
            "failed": len(result.failures) + len(result.errors),
        },
        "source_references": {
            "central_removal": "sistemas/gwent.py:995-1021",
            "target_options": "sistemas/gwent.py:1041-1078",
            "rykard_and_esgar": "sistemas/gwent.py:1427-1448",
            "sacred_teardrop_and_black_flame": "sistemas/gwent.py:1604-1620",
            "destined_death_execution": "sistemas/gwent.py:1623-1638",
            "requiem": "sistemas/gwent.py:1762-1779",
            "devour_and_ressurgir": "sistemas/gwent.py:1871-1889",
            "blood_price_identity": "sistemas/gwent.py:594-601",
        },
        "artifact_sha256": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [
                REGISTRY_PATH,
                SCHEMA_PATH,
                ROOT / "sistemas/card_removal_resurrection_candidate.py",
                Path(__file__).resolve(),
                SOURCE_PATH,
                ROOT / "sistemas/cartas.py",
                ROOT / "bot.py",
                ROOT / "database.py",
                ROOT / "site/app.js",
            ]
        },
        "limitations": [
            "The candidate resolver is not imported by sistemas.gwent.",
            "Legacy assertions use synthetic in-memory match states and do not verify database, HTTP, Discord, R2 or production behavior.",
            "The new card contract and instance_id migration are not yet integrated into the collection/deck persistence layer.",
            "Power limits and no-target policies remain design decisions for approval.",
        ],
        "failures": [str(item[1]) for item in result.failures + result.errors],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
