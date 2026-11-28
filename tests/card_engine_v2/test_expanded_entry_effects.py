from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog
from sistemas.card_engine_v2.entry_effects import SUPPORTED_ENTRY_EFFECTS
from sistemas.card_engine_v2.match import AlphaMatchController
from sistemas.card_engine_v2.power import ALPHA_RAW_GRANT_POLICY, bonus_total, effective_weather_resistance
from sistemas.card_engine_v2.errors import InvalidOperation
from sistemas.card_engine_v2.repository import HandlerResult, SQLiteMatchRepository
from sistemas.card_engine_v2.zones import transition_instance_zone
from tests.card_engine_v2.support import mechanics_catalog

PLAYER_A = "1001"
PLAYER_B = "2002"


class ExpandedEntryEffectTests(unittest.TestCase):
    """Integration coverage for the newly connected, release-pinned unit effects."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repository = SQLiteMatchRepository(Path(self.temp.name) / "expanded-effects.sqlite3")
        self.catalog = mechanics_catalog(self.temp.name)
        self.controller = AlphaMatchController(self.repository, self.catalog)
        self.match_id = 2026112801

    def tearDown(self) -> None:
        self.temp.cleanup()

    def create_match(self, target_card: str, *, own_board: list[tuple[str, str, int]] = (), enemy_board: list[tuple[str, str, int]] = (), own_discard: list[str] = (), own_last_row: str | None = None, enemy_last_row: str | None = None, weather: dict[str, int] | None = None) -> str:
        filler = ["arma_lanca_fornalha", "arma_cajado_marulho", "arma_martelo_fornalha", "chefe_vigia_cinzento", "arma_lanca_fornalha", "arma_cajado_marulho"]
        deck_a = [target_card, *[card_id for card_id, _row, _bonus in own_board], *own_discard, *filler]
        deck_b = [*[card_id for card_id, _row, _bonus in enemy_board], *filler]
        deck_a = (deck_a + filler * 3)[:16]
        deck_b = (deck_b + filler * 3)[:16]
        self.controller.create_match(
            match_id=self.match_id,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck_a, PLAYER_B: deck_b},
            initial_hand_size=16,
        )
        state = self.repository.get_match(self.match_id)
        runtime = self.repository.get_match_runtime(self.match_id)

        def nth_instance(player_id: str, card_id: str, used: set[str]) -> str:
            for instance_id in state["players"][player_id]["zones"]["hand"]:
                if instance_id not in used and state["instances"][instance_id]["card_id"] == card_id:
                    used.add(instance_id)
                    return instance_id
            raise AssertionError(f"no fixture instance {player_id}/{card_id}")

        used_a: set[str] = set()
        used_b: set[str] = set()
        target_id = nth_instance(PLAYER_A, target_card, used_a)
        for card_id, row, bonus in own_board:
            instance_id = nth_instance(PLAYER_A, card_id, used_a)
            transition_instance_zone(state, instance_id, "board", target_row=row)
            if bonus:
                state["instances"][instance_id]["state"]["bonus_grants"].append({
                    "grant_id": str(uuid.uuid4()),
                    "amount": bonus,
                    "source_effect_id": "test.fixture_bonus",
                    "source_instance_id": None,
                    "applied_event_id": str(uuid.uuid4()),
                    "expires_on": "permanent_instance",
                    "clamp_policy_id": ALPHA_RAW_GRANT_POLICY,
                })
        for card_id, row, bonus in enemy_board:
            instance_id = nth_instance(PLAYER_B, card_id, used_b)
            transition_instance_zone(state, instance_id, "board", target_row=row)
            if bonus:
                state["instances"][instance_id]["state"]["bonus_grants"].append({
                    "grant_id": str(uuid.uuid4()),
                    "amount": bonus,
                    "source_effect_id": "test.fixture_bonus",
                    "source_instance_id": None,
                    "applied_event_id": str(uuid.uuid4()),
                    "expires_on": "permanent_instance",
                    "clamp_policy_id": ALPHA_RAW_GRANT_POLICY,
                })
        for card_id in own_discard:
            instance_id = nth_instance(PLAYER_A, card_id, used_a)
            transition_instance_zone(state, instance_id, "discard")
        state["players"][PLAYER_A]["round_state"]["last_unit_play_row"] = own_last_row
        state["players"][PLAYER_B]["round_state"]["last_unit_play_row"] = enemy_last_row
        if weather:
            runtime["weather_by_row"].update(weather)
        fixture_event_id = str(uuid.uuid4())
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "expanded-effect-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_expanded_effect_fixture",
            "payload": {},
        }
        self.repository.execute_operation(
            self.match_id,
            request,
            lambda _working, _body: HandlerResult(
                outcome="applied",
                state=state,
                runtime_state=runtime,
                events=[{
                    "event_id": fixture_event_id,
                    "kind": "test_fixture_installed",
                    "effect_scope": "system",
                    "source_effect_id": None,
                    "source_instance_id": None,
                    "target_instance_ids": [],
                    "caused_by_event_ids": [],
                    "payload": {"fixture": "expanded-entry-effect"},
                }],
            ),
        )
        return target_id

    def play_target(self, target_id: str):
        return self.controller.play_unit(self.match_id, actor_player_id=PLAYER_A, instance_id=target_id)

    def target_instance(self, target_id: str) -> dict:
        state = self.repository.get_match(self.match_id)
        return state["instances"][target_id]

    def test_catalog_expands_to_27_explicit_alpha_cards_and_12_effect_families(self):
        self.assertEqual(len(self.catalog.allowed_card_ids()), 27)
        self.assertEqual(len(SUPPORTED_ENTRY_EFFECTS), 12)
        self.assertEqual(self.catalog.definition_manifest()["catalog_release_id"], "alpha-test-only.catalog.v0.3")
        self.assertEqual(self.catalog.definition_manifest()["effect_registry_release_id"], "alpha-test-only.effects.v0.2")
        self.assertEqual(self.catalog.definition_for("chefe_rei_afogado")["effect_id"], "effect.discard_advantage_power")
        self.assertEqual(self.catalog.definition_for("patente_10")["effect_id"], "effect.sequence_power")
        manifest = self.catalog.definition_manifest()
        allowlist_path = Path(__file__).resolve().parents[2] / "data/card_game/card-engine-v2-alpha-catalog.v0.3.json"
        import hashlib
        expected_hash = hashlib.sha256(allowlist_path.read_bytes()).hexdigest()
        self.assertEqual(manifest["artifact_sha256"]["alpha_allowlist"], expected_hash)
        self.assertEqual(manifest["catalog_release_id"], "alpha-test-only.catalog.v0.3")

    def test_every_enabled_on_play_family_has_an_allowlisted_source_card(self):
        source_effects = {
            self.catalog.definition_for(card_id)["effect_id"]
            for card_id in self.catalog.allowed_card_ids()
        }
        self.assertTrue(SUPPORTED_ENTRY_EFFECTS.issubset(source_effects))

    def test_allowlist_artifact_rejects_duplicates_or_code_drift(self):
        allowlist_path = Path(self.temp.name) / "allowlist.json"
        artifact = json.loads((Path(__file__).resolve().parents[2] / "data/card_game/card-engine-v2-alpha-catalog.v0.3.json").read_text(encoding="utf-8"))
        artifact["card_ids"].append(artifact["card_ids"][0])
        artifact["card_count"] += 1
        allowlist_path.write_text(json.dumps(artifact), encoding="utf-8")
        with self.assertRaises(InvalidOperation):
            AlphaCatalog(allowlist_path=allowlist_path)

        artifact = json.loads((Path(__file__).resolve().parents[2] / "data/card_game/card-engine-v2-alpha-catalog.v0.3.json").read_text(encoding="utf-8"))
        artifact["card_ids"].pop()
        artifact["card_count"] -= 1
        allowlist_path.write_text(json.dumps(artifact), encoding="utf-8")
        with self.assertRaises(InvalidOperation):
            AlphaCatalog(allowlist_path=allowlist_path)

    def test_historical_catalog_staging_contains_all_137_but_blocks_113(self):
        staging_path = Path(__file__).resolve().parents[2] / "data/card_game/card-engine-v2-legacy-catalog-staging.v0.1.json"
        staging = json.loads(staging_path.read_text(encoding="utf-8"))
        self.assertEqual(staging["status"], "review_only_not_a_runtime_catalog")
        self.assertEqual(staging["summary"]["historical_model_count"], 137)
        self.assertEqual(staging["summary"]["alpha_test_only_count"], 24)
        self.assertEqual(staging["summary"]["blocked_staging_only_count"], 113)
        self.assertEqual(sum(card["runtime_status"] == "blocked_staging_only" for card in staging["cards"]), 113)

    def test_current_catalog_staging_v0_2_tracks_27_allowed_and_110_blocked(self):
        staging_path = Path(__file__).resolve().parents[2] / "data/card_game/card-engine-v2-legacy-catalog-staging.v0.2.json"
        staging = json.loads(staging_path.read_text(encoding="utf-8"))
        self.assertEqual(staging["summary"]["historical_model_count"], 137)
        self.assertEqual(staging["summary"]["alpha_test_only_count"], 27)
        self.assertEqual(staging["summary"]["blocked_staging_only_count"], 110)
        self.assertEqual(sum(card["runtime_status"] == "blocked_staging_only" for card in staging["cards"]), 110)
        self.assertEqual(staging["source"]["allowlist_file"], "card-engine-v2-alpha-catalog.v0.3.json")

    def test_weather_affinity_triggers_from_any_active_row(self):
        target_id = self.create_match("magia_nevoa_antiga", weather={"ranged": 1})
        receipt = self.play_target(target_id)
        self.assertEqual(receipt.result["outcome"], "applied")
        unit = self.target_instance(target_id)
        self.assertEqual(bonus_total(unit), 2)
        event = next(item for item in self.repository.get_events(self.match_id) if item["kind"] == "unit_entry_effect_applied")
        self.assertEqual(event["source_effect_id"], "effect.weather_affinity_power")
        self.assertEqual(event["caused_by_event_ids"], [next(item["event_id"] for item in self.repository.get_events(self.match_id) if item["kind"] == "unit_played")])

    def test_weather_ward_adds_board_exit_resistance_and_buffs_weakest_same_row_ally(self):
        target_id = self.create_match("magia_selo_vigilia", own_board=[("arma_lanca_fornalha", "melee", 0), ("chefe_vigia_cinzento", "melee", 0)])
        receipt = self.play_target(target_id)
        self.assertEqual(receipt.result["outcome"], "applied")
        state = self.repository.get_match(self.match_id)
        self.assertEqual(effective_weather_resistance(state["instances"][target_id]), 1)
        ally_ids = [item for item in state["players"][PLAYER_A]["zones"]["board"] if item != target_id]
        grants = {item: bonus_total(state["instances"][item]) for item in ally_ids}
        self.assertEqual(sum(value == 1 for value in grants.values()), 1)
        event = next(item for item in self.repository.get_events(self.match_id) if item["kind"] == "unit_entry_effect_applied")
        modifier = state["instances"][target_id]["state"]["weather_resistance_modifiers"][0]
        self.assertEqual(modifier["expires_on"], "board_exit")
        self.assertEqual(modifier["applied_event_id"], event["event_id"])

    def test_cross_row_presence_grants_self_bonus_once(self):
        target_id = self.create_match("arma_duas_luas", own_board=[("arma_cajado_marulho", "ranged", 0)])
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 1)

    def test_discard_advantage_uses_own_discard_before_fallback(self):
        target_id = self.create_match("chefe_rei_afogado", own_discard=["arma_lanca_fornalha"])
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 2)

    def test_ruin_omen_reduces_strongest_enemy_and_adds_behind_bonus(self):
        target_id = self.create_match("chefe_oraculo_ruina", enemy_board=[("arma_grande_sino", "melee", 2)])
        self.play_target(target_id)
        state = self.repository.get_match(self.match_id)
        enemy_id = state["players"][PLAYER_B]["zones"]["board"][0]
        self.assertEqual(bonus_total(state["instances"][enemy_id]), 1)
        self.assertEqual(bonus_total(state["instances"][target_id]), 1)

    def test_enemy_bonus_reduction_respects_floor_and_target_scope(self):
        target_id = self.create_match("magia_trovao_oco", enemy_board=[("arma_cajado_marulho", "ranged", 3), ("chefe_vigia_cinzento", "melee", 2)])
        self.play_target(target_id)
        state = self.repository.get_match(self.match_id)
        enemy_ranged = next(i for i in state["players"][PLAYER_B]["zones"]["board"] if state["instances"][i]["state"]["current_row"] == "ranged")
        enemy_melee = next(i for i in state["players"][PLAYER_B]["zones"]["board"] if state["instances"][i]["state"]["current_row"] == "melee")
        self.assertEqual(bonus_total(state["instances"][enemy_ranged]), 2)
        self.assertEqual(bonus_total(state["instances"][enemy_melee]), 2)

    def test_comeback_condition(self):
        target_id = self.create_match("arma_grande_sino", enemy_board=[("gwent_singular_primeiro", "melee", 0)])
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 2)

    def test_ahead_condition(self):
        target_id = self.create_match("patente_9", enemy_board=[("arma_lanca_fornalha", "melee", 0)])
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 1)

    def test_solitary_row_condition(self):
        target_id = self.create_match("gwent_singular_primeiro")
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 2)

    def test_sequence_power_uses_opponents_previous_unit_row_before_current_play(self):
        target_id = self.create_match("patente_10", enemy_last_row="siege")
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 1)

    def test_arcane_hunter_triggers_on_enemy_dark_moon_faction(self):
        target_id = self.create_match("patente_1", enemy_board=[("arma_cajado_marulho", "ranged", 0)])
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 1)

    def test_black_sun_triggers_on_positive_enemy_bonus(self):
        target_id = self.create_match("magia_sol_negro", enemy_board=[("arma_lanca_fornalha", "melee", 1)])
        self.play_target(target_id)
        self.assertEqual(bonus_total(self.target_instance(target_id)), 2)

    def test_maliketh_reduces_strongest_enemy_bonus_by_two(self):
        target_id = self.create_match("chefe_maliketh_morte_destinada", enemy_board=[("arma_lanca_fornalha", "melee", 3), ("chefe_vigia_cinzento", "ranged", 1)])
        self.play_target(target_id)
        state = self.repository.get_match(self.match_id)
        enemy_units = [state["instances"][item] for item in state["players"][PLAYER_B]["zones"]["board"]]
        by_row = {unit["state"]["current_row"]: bonus_total(unit) for unit in enemy_units}
        self.assertEqual(by_row["melee"], 1)
        self.assertEqual(by_row["ranged"], 1)

    def test_dama_vazio_uses_the_same_server_bound_reduction_contract(self):
        target_id = self.create_match("chefe_dama_vazio", enemy_board=[("arma_lanca_fornalha", "melee", 3)])
        self.play_target(target_id)
        state = self.repository.get_match(self.match_id)
        enemy_id = state["players"][PLAYER_B]["zones"]["board"][0]
        self.assertEqual(bonus_total(state["instances"][enemy_id]), 1)

    def test_unknown_entry_effect_is_not_inferred_from_legacy_text(self):
        # The full 137-card staging snapshot remains blocked; unlisted identities
        # are not silently interpreted just because their text resembles a handler.
        with self.assertRaises(InvalidOperation):
            self.catalog.definition_for("chefe_cervo_sombrio")


if __name__ == "__main__":
    unittest.main()
