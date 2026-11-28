from __future__ import annotations

import unittest

from sistemas.card_game_achievements import evaluate_achievement_cards


class CardAchievementProjectionTests(unittest.TestCase):
    def test_known_progress_unlocks_only_at_server_derived_threshold(self):
        cards = evaluate_achievement_cards({
            "wins": 1,
            "exemplars": 49,
            "forged_exemplars": 10,
            "singular_exemplars": 1,
            "common_models_owned": 7,
            "common_models_total": 7,
            "matches_played": 99,
        })
        by_key = {item["key"]: item for item in cards}
        self.assertTrue(by_key["first_blood"]["unlocked"])
        self.assertEqual(by_key["collector"]["progress"], 49)
        self.assertFalse(by_key["collector"]["unlocked"])
        self.assertTrue(by_key["forger"]["unlocked"])
        self.assertTrue(by_key["legend"]["unlocked"])
        self.assertTrue(by_key["perfectionist"]["unlocked"])
        self.assertFalse(by_key["dedicado"]["unlocked"])

    def test_unsupported_achievements_are_explicitly_untrackable_not_fake_zero(self):
        cards = evaluate_achievement_cards({})
        by_key = {item["key"]: item for item in cards}
        self.assertEqual(by_key["apostador"]["status"], "tracking_pending")
        self.assertIsNone(by_key["apostador"]["progress"])
        self.assertEqual(by_key["survivor"]["status"], "tracking_pending")
        self.assertIsNone(by_key["survivor"]["total"])

    def test_zero_common_models_does_not_unlock_perfectionist(self):
        cards = evaluate_achievement_cards({"common_models_owned": 0, "common_models_total": 0})
        perfectionist = next(item for item in cards if item["key"] == "perfectionist")
        self.assertFalse(perfectionist["unlocked"])
        self.assertEqual(perfectionist["status"], "tracking_pending")


if __name__ == "__main__":
    unittest.main()
