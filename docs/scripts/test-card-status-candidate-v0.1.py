from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from sistemas import card_status_candidate as candidate
from sistemas import gwent as legacy_gwent
from sistemas.cartas import CARTAS_POR_ID, HABILIDADES

REGISTRY_PATH = ROOT / "data/card_game/status-registry-candidate.v1.json"
SCHEMA_PATH = ROOT / "data/card_game/status-registry.schema.v1.json"
ASSIGNMENT_IDS = {
    "special.gwent_nevoa", "special.gwent_geada", "special.gwent_chuva",
    "special.gwent_sangramento", "special.gwent_geada_cariana",
    "special.gwent_podrida", "special.gwent_loucura",
    "unit.malenia_scarlet_bloom", "unit.messmer_impaling_spear",
    "unit.placidusax_time_storm", "unit.v75_frost_oracle", "unit.v75_blood_mark",
    "leader.mohg_blood_rite", "leader.astel_gravity", "relic.night_flame_night_mode",
}


class StatusRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        candidate.validate_registry(cls.registry)

    def test_schema_is_valid_draft_2020_12(self):
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(self.schema)

    def test_registry_matches_schema(self):
        import jsonschema
        jsonschema.Draft202012Validator(self.schema).validate(self.registry)

    def test_candidate_status_and_version_are_explicit(self):
        self.assertEqual("CANDIDATE_FOR_REVIEW_NOT_APPROVED", self.registry["status"])
        self.assertEqual("0.1", self.registry["status_registry_version"])

    def test_exactly_four_statuses_are_defined(self):
        self.assertEqual({"status.frost", "status.scarlet_rot", "status.bleeding", "status.madness"},
                         {item["status_id"] for item in self.registry["statuses"]})

    def test_all_status_counters_have_cap_two(self):
        for item in self.registry["statuses"]:
            self.assertEqual(2, item["max_marks_per_unit"])

    def test_only_frost_rot_and_madness_reduce_effective_power(self):
        defs = {item["status_id"]: item for item in self.registry["statuses"]}
        self.assertEqual(1, defs["status.frost"]["effective_power"]["per_mark_reduction"])
        self.assertEqual(1, defs["status.scarlet_rot"]["effective_power"]["per_mark_reduction"])
        self.assertEqual(1, defs["status.madness"]["effective_power"]["per_mark_reduction"])
        self.assertEqual(0, defs["status.bleeding"]["effective_power"]["per_mark_reduction"])

    def test_all_control_statuses_share_cap_three(self):
        for item in self.registry["statuses"]:
            if item["status_id"] != "status.bleeding":
                self.assertEqual("control_debuffs", item["effective_power"]["reduction_group"])
                self.assertEqual(3, item["effective_power"]["group_cap"])

    def test_thresholds_are_transition_based(self):
        for item in self.registry["statuses"]:
            threshold = item["threshold"]
            if threshold:
                self.assertEqual(2, threshold["marks"])
                self.assertEqual("on_transition_to_threshold", threshold["trigger"])

    def test_bleeding_threshold_resets_marks(self):
        item = next(x for x in self.registry["statuses"] if x["status_id"] == "status.bleeding")
        self.assertTrue(item["threshold"]["reset_marks"])
        self.assertEqual("reduce_bonus", item["threshold"]["action"])

    def test_rot_and_madness_remain_at_two_marks_after_threshold(self):
        defs = {x["status_id"]: x for x in self.registry["statuses"]}
        self.assertFalse(defs["status.scarlet_rot"]["threshold"]["reset_marks"])
        self.assertFalse(defs["status.madness"]["threshold"]["reset_marks"])

    def test_rarity_does_not_scale_candidate_statuses(self):
        self.assertFalse(self.registry["global_rules"]["rarity_scaling"])
        self.assertTrue(all(not item["candidate_rarity_scaling"] for item in self.registry["applications"]))

    def test_all_seven_special_status_cards_are_mapped(self):
        ids = {item["legacy_effect_id"] for item in self.registry["applications"] if item["source_kind"] == "special"}
        self.assertEqual({"gwent_nevoa", "gwent_geada", "gwent_chuva", "gwent_sangramento",
                          "gwent_geada_cariana", "gwent_podrida", "gwent_loucura"}, ids)

    def test_all_current_identity_status_applications_are_mapped(self):
        ids = {item["legacy_effect_id"] for item in self.registry["applications"] if item["source_kind"] == "unit_identity"}
        self.assertEqual({"scarlet_bloom", "impaling_spear", "time_storm", "v75_frost_oracle", "v75_blood_mark"}, ids)

    def test_all_application_assignments_have_unique_ids(self):
        assignments = self.registry["applications"]
        self.assertEqual(len(assignments), len({x["assignment_id"] for x in assignments}))
        self.assertEqual(ASSIGNMENT_IDS, {x["assignment_id"] for x in assignments})

    def test_all_special_aliases_exist_in_catalogue_and_skill_registry(self):
        for item in self.registry["applications"]:
            if item["source_kind"] != "special":
                continue
            self.assertIn(item["legacy_effect_id"], HABILIDADES)
            for card_id in item["card_ids"]:
                self.assertIn(card_id, CARTAS_POR_ID)
                self.assertEqual(item["legacy_effect_id"], CARTAS_POR_ID[card_id].habilidade)

    def test_all_identity_aliases_are_active_for_the_declared_card(self):
        for item in self.registry["applications"]:
            if item["source_kind"] != "unit_identity":
                continue
            for card_id in item["card_ids"]:
                self.assertIn(card_id, legacy_gwent.CARD_IDENTITY_ABILITIES)
                self.assertEqual(item["legacy_effect_id"], legacy_gwent.CARD_IDENTITY_ABILITIES[card_id]["effect"])

    def test_leader_assignments_match_actual_leader_registry(self):
        for item in self.registry["applications"]:
            if item["source_kind"] != "leader":
                continue
            self.assertEqual(item["legacy_effect_id"], legacy_gwent.LEADERS[item["leader_id"]]["effect"])

    def test_relic_assignment_matches_actual_card(self):
        item = next(x for x in self.registry["applications"] if x["source_kind"] == "relic")
        self.assertEqual(item["legacy_effect_id"], CARTAS_POR_ID[item["card_ids"][0]].habilidade)

    def test_purifier_map_covers_all_five_current_paths(self):
        self.assertEqual({"radagon_purification", "rennala_full_moon", "v75_grace_mender", "gwent_chama", "reliquia_renala"},
                         {x["legacy_effect_id"] for x in self.registry["cleansers"]})

    def test_cleanser_assignments_match_the_current_runtime_sources(self):
        for item in self.registry["cleansers"]:
            kind = item["source_kind"]
            if kind == "leader":
                self.assertEqual(item["legacy_effect_id"], legacy_gwent.LEADERS[item["leader_id"]]["effect"])
            elif kind == "unit_identity":
                for card_id in item["card_ids"]:
                    self.assertEqual(item["legacy_effect_id"], legacy_gwent.CARD_IDENTITY_ABILITIES[card_id]["effect"])
            elif kind == "special":
                self.assertIn(item["legacy_effect_id"], HABILIDADES)
                for card_id in item["card_ids"]:
                    self.assertEqual(item["legacy_effect_id"], CARTAS_POR_ID[card_id].habilidade)
            elif kind == "relic":
                for card_id in item["card_ids"]:
                    self.assertEqual(item["legacy_effect_id"], CARTAS_POR_ID[card_id].habilidade)
            else:
                self.fail(f"source_kind não suportado: {kind}")

    def test_status_application_source_cards_are_unique(self):
        card_ids = [card_id for item in self.registry["applications"] for card_id in item.get("card_ids", [])]
        self.assertEqual(len(card_ids), len(set(card_ids)))

    def test_frost_is_reduced_one_point_per_mark(self):
        unit = {"poder": 8, "bonus": 0, "geada": 0}
        result = candidate.apply_status_marks(unit, self.registry, "status.frost", 1)
        self.assertEqual(1, result.marks_after)
        self.assertEqual(7, candidate.effective_power(unit, self.registry))

    def test_frost_stops_at_two_marks_and_does_not_repeat_threshold(self):
        unit = {"poder": 8, "bonus": 0, "geada": 2}
        result = candidate.apply_status_marks(unit, self.registry, "status.frost", 1)
        self.assertEqual(0, result.marks_applied)
        self.assertEqual(1, result.marks_wasted)
        self.assertEqual(2, unit["geada"])

    def test_rot_crossing_two_marks_corrodes_one_positive_bonus(self):
        unit = {"poder": 8, "bonus": 3, "podrida": 1}
        result = candidate.apply_status_marks(unit, self.registry, "status.scarlet_rot", 1)
        self.assertEqual(2, result.marks_after)
        self.assertEqual(1, result.threshold_triggers)
        self.assertEqual(2, unit["bonus"])

    def test_rot_threshold_does_not_repeat_at_cap(self):
        unit = {"poder": 8, "bonus": 3, "podrida": 2}
        result = candidate.apply_status_marks(unit, self.registry, "status.scarlet_rot", 1)
        self.assertEqual(0, result.threshold_triggers)
        self.assertEqual(3, unit["bonus"])

    def test_rot_does_not_make_nonpositive_bonus_more_negative(self):
        unit = {"poder": 8, "bonus": -1, "podrida": 1}
        candidate.apply_status_marks(unit, self.registry, "status.scarlet_rot", 1)
        self.assertEqual(-1, unit["bonus"])

    def test_bleeding_second_mark_reduces_bonus_and_consumes_marks(self):
        unit = {"poder": 8, "bonus": 2, "sangramento": 1}
        result = candidate.apply_status_marks(unit, self.registry, "status.bleeding", 1)
        self.assertEqual(1, result.threshold_triggers)
        self.assertEqual(0, unit["sangramento"])
        self.assertEqual(0, unit["bonus"])
        self.assertEqual(8, candidate.effective_power(unit, self.registry))

    def test_bleeding_bonus_floor_is_minus_two(self):
        unit = {"poder": 8, "bonus": -1, "sangramento": 1}
        candidate.apply_status_marks(unit, self.registry, "status.bleeding", 1)
        self.assertEqual(-2, unit["bonus"])

    def test_bleeding_can_trigger_again_after_consumed_marks(self):
        unit = {"poder": 8, "bonus": 4, "sangramento": 0}
        first = candidate.apply_status_marks(unit, self.registry, "status.bleeding", 2)
        self.assertEqual(1, first.threshold_triggers)
        self.assertEqual(0, unit["sangramento"])
        second = candidate.apply_status_marks(unit, self.registry, "status.bleeding", 2)
        self.assertEqual(1, second.threshold_triggers)
        self.assertEqual(0, unit["sangramento"])
        self.assertEqual(0, unit["bonus"])

    def test_madness_second_mark_clears_positive_bonus(self):
        unit = {"poder": 8, "bonus": 4, "loucura": 1}
        result = candidate.apply_status_marks(unit, self.registry, "status.madness", 1)
        self.assertEqual(1, result.threshold_triggers)
        self.assertEqual(2, unit["loucura"])
        self.assertEqual(0, unit["bonus"])

    def test_madness_does_not_change_negative_bonus(self):
        unit = {"poder": 8, "bonus": -2, "loucura": 1}
        candidate.apply_status_marks(unit, self.registry, "status.madness", 1)
        self.assertEqual(-2, unit["bonus"])

    def test_control_statuses_share_combined_cap_three(self):
        unit = {"poder": 10, "bonus": 0, "geada": 2, "podrida": 2, "loucura": 2}
        self.assertEqual(3, candidate.combined_control_penalty(unit, self.registry))
        self.assertEqual(7, candidate.effective_power(unit, self.registry))

    def test_weather_and_statuses_combine_before_power_floor(self):
        unit = {"poder": 4, "bonus": 0, "geada": 2, "weather_resist": 1}
        self.assertEqual(1, candidate.effective_power(unit, self.registry, weather_level=3))

    def test_round_close_clears_all_four_statuses(self):
        units = [{"sangramento": 1, "geada": 2, "podrida": 1, "loucura": 2}, {"geada": 1}]
        count = candidate.close_round_statuses(units, self.registry)
        self.assertEqual(5, count)
        self.assertTrue(all(not any(unit.get(k, 0) for k in ("sangramento", "geada", "podrida", "loucura")) for unit in units))

    def test_selective_purification_only_clears_named_statuses(self):
        unit = {"sangramento": 1, "geada": 2, "podrida": 1, "loucura": 2}
        removed = candidate.clear_statuses(unit, self.registry, ["status.frost", "status.scarlet_rot"])
        self.assertEqual(["status.frost", "status.scarlet_rot"], removed)
        self.assertEqual(1, unit["sangramento"])
        self.assertEqual(2, unit["loucura"])

    def test_legacy_power_formula_has_combined_cap_three(self):
        unit = {"poder": 10, "bonus": 0, "geada": 2, "podrida": 2, "loucura": 2}
        self.assertEqual(7, legacy_gwent._poder_efetivo(unit, {}))

    def test_runtime_malenia_does_not_repeat_corrosion_at_mark_cap(self):
        player = {"board": []}
        target = {"id": "enemy", "nome": "Alvo", "row": "melee", "poder": 8, "bonus": 3, "podrida": 2}
        other = {"board": [target]}
        card = {"id": "chefe_malenia_lamina_miquella", "nome": "Malenia", "poder": 8, "bonus": 0}
        legacy_gwent._aplicar_habilidade_identidade(player, other, card, {"weather": {}}, "melee")
        self.assertEqual(2, target["podrida"])
        self.assertEqual(3, target["bonus"], "Malenia não volta a corroer um alvo que já está no limite de duas marcas")

    def test_legacy_frost_oracle_rewards_again_even_when_target_is_at_cap(self):
        player = {"board": []}
        target = {"id": "enemy", "nome": "Alvo", "row": "melee", "poder": 8, "bonus": 0, "geada": 2}
        other = {"board": [target]}
        card = {"id": "gwent_v75_lua_oraculo_geada", "nome": "Oráculo", "poder": 6, "bonus": 0}
        legacy_gwent._aplicar_habilidade_identidade(player, other, card, {"weather": {}}, "melee")
        self.assertEqual(2, target["geada"])
        self.assertEqual(1, card["bonus"])

    def test_legacy_rarity_amplifier_adds_extra_rot_bonus_loss(self):
        target = {"id": "enemy", "nome": "Alvo", "row": "melee", "bonus": 2}
        card = {"id": "test", "nome": "Malenia", "raridade": "Lendária", "bonus": 0}
        applied = legacy_gwent._aplicar_potencia_raridade(
            card, {"board": []}, {"board": [target]}, {id(target): 3}, 0
        )
        self.assertEqual(1, applied)
        self.assertEqual(1, target["bonus"], "a queda de 1 configurada pelo estado recebe outra queda de 1 via raridade")

    def test_status_candidate_does_not_apply_legacy_rarity_amplification(self):
        unit = {"poder": 8, "bonus": 3, "podrida": 1}
        candidate.apply_status_marks(unit, self.registry, "status.scarlet_rot", 1)
        self.assertEqual(2, unit["bonus"], "o registry candidato aplica somente o efeito de Podridão definido")

    def test_source_line_references_are_within_current_motor(self):
        line_count = len((ROOT / "sistemas/gwent.py").read_text(encoding="utf-8").splitlines())
        for item in self.registry["applications"] + self.registry["cleansers"]:
            for start, end in item["source_lines"]:
                self.assertGreaterEqual(start, 1)
                self.assertGreaterEqual(end, start)
                self.assertLessEqual(end, line_count)


if __name__ == "__main__":
    unittest.main(verbosity=2)
