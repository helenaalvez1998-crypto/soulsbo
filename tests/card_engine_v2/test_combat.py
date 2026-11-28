from __future__ import annotations

import unittest

from sistemas.card_engine_v2.combat import apply_life_damage, resolve_row_combat
from sistemas.card_engine_v2.errors import InvalidOperation
from sistemas.card_engine_v2.power import effective_power


class RowCombatTests(unittest.TestCase):
    def _unit(self, instance_id: str, power: int, row: str) -> dict:
        return {
            "instance_id": instance_id,
            "card_id": f"test.{instance_id}",
            "schema_version": 7,
            "owner_player_id": "A",
            "definition_snapshot": {
                "card_id": f"test.{instance_id}",
                "power_base": power,
                "intrinsic_weather_resistance": 0,
            },
            "state": {
                "current_row": row,
                "bonus_grants": [],
                "status_applications": [],
                "weather_resistance_modifiers": [],
            },
        }

    def test_row_differential_deals_damage_only_to_the_lower_power_side(self):
        state = {
            "players": {
                "A": {"zones": {"board": ["a1"]}},
                "B": {"zones": {"board": ["b1"]}},
            },
            "instances": {
                "a1": self._unit("a1", 7, "melee"),
                "b1": self._unit("b1", 4, "melee"),
            },
        }
        result = resolve_row_combat(
            state,
            ["A", "B"],
            {"melee": 0, "ranged": 0, "siege": 0},
        )
        self.assertEqual(result["damage_by_player"], {"A": 0, "B": 3})
        self.assertEqual(result["rows"][0]["winner_player_id"], "A")
        self.assertEqual(result["rows"][1]["damage_by_player"], {"A": 0, "B": 0})

    def test_weather_resistance_is_applied_through_effective_power(self):
        state = {
            "players": {
                "A": {"zones": {"board": ["a1"]}},
                "B": {"zones": {"board": []}},
            },
            "instances": {"a1": self._unit("a1", 7, "melee")},
        }
        state["instances"]["a1"]["definition_snapshot"]["intrinsic_weather_resistance"] = 2
        result = resolve_row_combat(
            state,
            ["A", "B"],
            {"melee": 3, "ranged": 0, "siege": 0},
        )
        self.assertEqual(result["row_power_by_player"]["A"]["melee"], 6)
        self.assertEqual(result["damage_by_player"], {"A": 0, "B": 6})

    def test_life_damage_clamps_at_zero_and_reports_lethal_players(self):
        result = apply_life_damage(
            {"A": 4, "B": 20},
            {"A": 9, "B": 3},
        )
        self.assertEqual(result["life_by_player"], {"A": 0, "B": 17})
        self.assertEqual(result["defeated_player_ids"], ["A"])
        self.assertEqual(result["life_changes"]["A"]["damage_taken"], 9)

    def test_simultaneous_lethal_is_reported_for_both_players(self):
        result = apply_life_damage({"A": 5, "B": 8}, {"A": 5, "B": 12})
        self.assertEqual(result["defeated_player_ids"], ["A", "B"])


    def test_physical_exemplar_power_overrides_catalog_power_but_rarity_does_not(self):
        unit = self._unit("physical-1", 4, "melee")
        unit["definition_snapshot"]["kind"] = "unit"
        unit["exemplar_snapshot"] = {"power_base": 8, "rarity_id": "rare"}
        state = {"instances": {"physical-1": unit}}
        first = effective_power(state, unit, {"melee": 0, "ranged": 0, "siege": 0})
        unit["exemplar_snapshot"]["rarity_id"] = "singular"
        second = effective_power(state, unit, {"melee": 0, "ranged": 0, "siege": 0})
        self.assertEqual(first, 8)
        self.assertEqual(second, 8)
        unit["exemplar_snapshot"]["power_base"] = 9
        third = effective_power(state, unit, {"melee": 0, "ranged": 0, "siege": 0})
        self.assertEqual(third, 9)

    def test_invalid_damage_values_fail_closed(self):
        with self.assertRaises(InvalidOperation):
            apply_life_damage({"A": 5}, {"A": -1})
        with self.assertRaises(InvalidOperation):
            apply_life_damage({"A": 5}, {"B": 1})


if __name__ == "__main__":
    unittest.main()
