"""Contract tests for the isolated, non-runtime deck-fatigue candidate."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from sistemas.card_engine_v2.deck_fatigue_candidate import (
    resolve_draw_phase_candidate,
    resolve_fatigue_step,
)
from sistemas.card_engine_v2.errors import InvalidOperation


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "data/card_game/card-engine-v2-deck-fatigue-policy-candidate.v0.1.json"


class DeckFatigueCandidateTests(unittest.TestCase):
    def test_reference_formula_increases_per_failed_draw_phase(self) -> None:
        results = [
            resolve_fatigue_step(count, initial_damage=1, damage_increment=2)
            for count in range(4)
        ]
        self.assertEqual([item["fatigue_count"] for item in results], [1, 2, 3, 4])
        self.assertEqual([item["damage"] for item in results], [1, 3, 5, 7])

    def test_each_player_counter_is_independent(self) -> None:
        player_a = resolve_fatigue_step(2, initial_damage=1, damage_increment=1)
        player_b = resolve_fatigue_step(0, initial_damage=1, damage_increment=1)
        self.assertEqual(player_a["damage"], 3)
        self.assertEqual(player_b["damage"], 1)
        self.assertEqual(player_a["fatigue_count"], 3)
        self.assertEqual(player_b["fatigue_count"], 1)

    def test_optional_cap_limits_damage_without_resetting_counter(self) -> None:
        results = [
            resolve_fatigue_step(count, initial_damage=2, damage_increment=2, maximum_damage=5)
            for count in range(5)
        ]
        self.assertEqual([item["damage"] for item in results], [2, 4, 5, 5, 5])
        self.assertEqual([item["fatigue_count"] for item in results], [1, 2, 3, 4, 5])

    def test_no_cap_means_no_implicit_clamp(self) -> None:
        result = resolve_fatigue_step(100, initial_damage=1, damage_increment=1)
        self.assertEqual(result["damage"], 101)
        self.assertIsNone(result["maximum_damage"])

    def test_invalid_counters_and_policy_values_fail_closed(self) -> None:
        invalid_calls = (
            lambda: resolve_fatigue_step(-1, initial_damage=1, damage_increment=1),
            lambda: resolve_fatigue_step(True, initial_damage=1, damage_increment=1),
            lambda: resolve_fatigue_step(0, initial_damage=0, damage_increment=1),
            lambda: resolve_fatigue_step(0, initial_damage=1, damage_increment=0),
            lambda: resolve_fatigue_step(0, initial_damage=1, damage_increment=1, maximum_damage=0),
            lambda: resolve_fatigue_step(0, initial_damage=1, damage_increment=1, maximum_damage=1),
            lambda: resolve_fatigue_step(0, initial_damage=3, damage_increment=1, maximum_damage=2),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(InvalidOperation):
                    call()

    def test_fully_satisfied_draw_phase_does_not_apply_fatigue(self) -> None:
        result = resolve_draw_phase_candidate(
            2, requested_cards=2, available_cards=2, initial_damage=1, damage_increment=1
        )
        self.assertEqual(result["cards_drawn"], 2)
        self.assertEqual(result["cards_missing"], 0)
        self.assertFalse(result["fatigue_applied"])
        self.assertEqual(result["fatigue_count"], 2)
        self.assertEqual(result["fatigue_damage"], 0)

    def test_partial_draw_phase_applies_one_fatigue_step(self) -> None:
        result = resolve_draw_phase_candidate(
            0, requested_cards=2, available_cards=1, initial_damage=1, damage_increment=2
        )
        self.assertEqual(result["cards_drawn"], 1)
        self.assertEqual(result["cards_missing"], 1)
        self.assertTrue(result["fatigue_applied"])
        self.assertEqual(result["fatigue_count"], 1)
        self.assertEqual(result["fatigue_damage"], 1)

    def test_empty_draw_pile_applies_one_step_not_one_per_missing_card(self) -> None:
        result = resolve_draw_phase_candidate(
            1, requested_cards=3, available_cards=0, initial_damage=1, damage_increment=2
        )
        self.assertEqual(result["cards_drawn"], 0)
        self.assertEqual(result["cards_missing"], 3)
        self.assertTrue(result["fatigue_applied"])
        self.assertEqual(result["fatigue_count"], 2)
        self.assertEqual(result["fatigue_damage"], 3)

    def test_invalid_draw_phase_counts_fail_closed(self) -> None:
        invalid_calls = (
            lambda: resolve_draw_phase_candidate(0, requested_cards=0, available_cards=0, initial_damage=1, damage_increment=1),
            lambda: resolve_draw_phase_candidate(0, requested_cards=True, available_cards=0, initial_damage=1, damage_increment=1),
            lambda: resolve_draw_phase_candidate(0, requested_cards=1, available_cards=-1, initial_damage=1, damage_increment=1),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(InvalidOperation):
                    call()

    def test_historical_candidate_policy_is_superseded_and_not_a_runtime_source(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(policy["status"], "superseded_historical_candidate_not_runtime_source")
        self.assertIsNone(policy["candidate_arithmetic"]["initial_damage"])
        self.assertIsNone(policy["candidate_arithmetic"]["damage_increment"])
        self.assertIsNone(policy["candidate_arithmetic"]["maximum_damage"])
        self.assertFalse(policy["runtime_integration"]["enabled"])


if __name__ == "__main__":
    unittest.main()
