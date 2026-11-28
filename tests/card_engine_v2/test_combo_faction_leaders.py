from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path

from sistemas.card_engine_v2.alpha_catalog import AlphaCatalog
from sistemas.card_engine_v2.match import AlphaMatchController
from sistemas.card_engine_v2.power import bonus_total, status_counts
from sistemas.card_engine_v2.repository import HandlerResult, SQLiteMatchRepository
from sistemas.card_engine_v2.zones import transition_instance_zone
from tests.card_engine_v2.support import mechanics_catalog

PLAYER_A = "1001"
PLAYER_B = "2002"
FILLERS = [
    "arma_lanca_fornalha",
    "arma_cajado_marulho",
    "arma_martelo_fornalha",
    "chefe_vigia_cinzento",
    "arma_grande_sino",
    "arma_duas_luas",
]


class ComboFactionLeaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repository = SQLiteMatchRepository(Path(self.temp.name) / "combo-leaders.sqlite3")
        self.catalog = mechanics_catalog(self.temp.name)
        self.controller = AlphaMatchController(self.repository, self.catalog)
        self.next_match_id = 2026112890

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _create_match(
        self,
        *,
        a_cards: list[str] | None = None,
        b_cards: list[str] | None = None,
        leader_id: str | None = None,
        faction_id: str | None = None,
    ) -> int:
        match_id = self.next_match_id
        self.next_match_id += 1
        deck_a = list(a_cards or [])
        deck_b = list(b_cards or [])
        while len(deck_a) < 12:
            deck_a.append(FILLERS[len(deck_a) % len(FILLERS)])
        while len(deck_b) < 12:
            deck_b.append(FILLERS[len(deck_b) % len(FILLERS)])
        self.controller.create_match(
            match_id=match_id,
            player_ids=[PLAYER_A, PLAYER_B],
            decks={PLAYER_A: deck_a, PLAYER_B: deck_b},
            initial_hand_size=12,
            player_factions={PLAYER_A: faction_id} if faction_id else None,
            leaders={PLAYER_A: leader_id} if leader_id else None,
        )
        return match_id

    def _find_hand_instance(self, state: dict, player_id: str, card_id: str, used: set[str]) -> str:
        for instance_id in state["players"][player_id]["zones"]["hand"]:
            if instance_id not in used and state["instances"][instance_id]["card_id"] == card_id:
                used.add(instance_id)
                return instance_id
        raise AssertionError(f"missing fixture card {player_id}/{card_id}")

    def _seed_zones(
        self,
        match_id: int,
        *,
        own_board: list[tuple[str, str]] = (),
        enemy_board: list[tuple[str, str]] = (),
        own_discard: list[str] = (),
        own_statuses: dict[str, list[str]] | None = None,
        enemy_statuses: dict[str, list[str]] | None = None,
    ) -> dict[str, list[str]]:
        state = self.repository.get_match(match_id)
        used = {PLAYER_A: set(), PLAYER_B: set()}
        ids: dict[str, list[str]] = {PLAYER_A: [], PLAYER_B: []}
        for player_id, board in ((PLAYER_A, own_board), (PLAYER_B, enemy_board)):
            for card_id, row in board:
                instance_id = self._find_hand_instance(state, player_id, card_id, used[player_id])
                transition_instance_zone(state, instance_id, "board", target_row=row)
                ids[player_id].append(instance_id)
        for card_id in own_discard:
            instance_id = self._find_hand_instance(state, PLAYER_A, card_id, used[PLAYER_A])
            transition_instance_zone(state, instance_id, "discard")
            ids[PLAYER_A].append(instance_id)
        seed_event_id = str(uuid.uuid4())
        for player_id, mapping in ((PLAYER_A, own_statuses or {}), (PLAYER_B, enemy_statuses or {})):
            for card_id, statuses in mapping.items():
                matches = [
                    item for item in ids[player_id]
                    if state["instances"][item]["card_id"] == card_id
                    and item in state["players"][player_id]["zones"]["board"]
                ]
                if not matches:
                    raise AssertionError(f"status fixture target not on board: {player_id}/{card_id}")
                target_id = matches[0]
                for status_id in statuses:
                    state["instances"][target_id]["state"]["status_applications"].append({
                        "application_id": str(uuid.uuid4()),
                        "status_id": status_id,
                        "source_effect_id": "test.fixture_status",
                        "source_instance_id": None,
                        "applied_event_id": seed_event_id,
                        "expires_on": "round_close",
                    })
        request = {
            "operation_id": str(uuid.uuid4()),
            "actor": {"type": "system", "system_id": "combo-leader-fixture"},
            "expected_revision": state["state_revision"],
            "action_type": "test.install_combo_leader_fixture",
            "payload": {},
        }
        runtime = self.repository.get_match_runtime(match_id)
        self.repository.execute_operation(
            match_id,
            request,
            lambda _working, _body: HandlerResult(
                outcome="applied",
                state=state,
                runtime_state=runtime,
                events=[{
                    "event_id": seed_event_id,
                    "kind": "test_fixture_installed",
                    "effect_scope": "system",
                    "source_effect_id": None,
                    "source_instance_id": None,
                    "target_instance_ids": [*ids[PLAYER_A], *ids[PLAYER_B]],
                    "caused_by_event_ids": [],
                    "payload": {"fixture": "combo-leader"},
                }],
            ),
        )
        return ids

    def _hand_instance(self, match_id: int, player_id: str, card_id: str) -> str:
        state = self.repository.get_match(match_id)
        return next(
            item for item in state["players"][player_id]["zones"]["hand"]
            if state["instances"][item]["card_id"] == card_id
        )

    def test_definition_manifest_hashes_combo_passive_and_leader_artifacts(self):
        import hashlib
        self.assertEqual(len(self.catalog.combo_registry), 27)
        self.assertEqual(len(self.catalog.faction_passives), 4)
        self.assertEqual(len(self.catalog.leader_registry), 10)
        manifest = self.catalog.definition_manifest()
        root = Path(__file__).resolve().parents[2]
        expected = {
            "combos": root / "data/card_game/card-engine-v2-alpha-combos.v0.1.json",
            "faction_passives": root / "data/card_game/card-engine-v2-alpha-faction-passives.v0.1.json",
            "leaders": root / "data/card_game/card-engine-v2-alpha-leaders.v0.1.json",
        }
        for key, path in expected.items():
            self.assertEqual(manifest["artifact_sha256"][key], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_combo_priority_pending_activation_and_distinct_physical_participants(self):
        match_id = self._create_match(
            a_cards=["chefe_dama_vazio", "magia_nevoa_antiga", "arma_duas_luas"],
        )
        ids = self._seed_zones(match_id, own_board=[("chefe_dama_vazio", "siege")])
        first = self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_A,
            instance_id=self._hand_instance(match_id, PLAYER_A, "magia_nevoa_antiga"),
        )
        self.assertEqual(first.result["outcome"], "applied")
        state = self.repository.get_match(match_id)
        astrologer_id = next(
            item for item in state["players"][PLAYER_A]["zones"]["board"]
            if state["instances"][item]["card_id"] == "magia_nevoa_antiga"
        )
        self.assertEqual(bonus_total(state["instances"][astrologer_id]), 2)
        self.assertIn("vazio_astral", state["players"][PLAYER_A]["round_state"]["synergy_used"])
        self.assertEqual(len(set([ids[PLAYER_A][0], astrologer_id])), 2)

        self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_B,
            instance_id=self._hand_instance(match_id, PLAYER_B, FILLERS[0]),
        )
        second = self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_A,
            instance_id=self._hand_instance(match_id, PLAYER_A, "arma_duas_luas"),
        )
        self.assertEqual(second.result["outcome"], "applied")
        state = self.repository.get_match(match_id)
        self.assertTrue(state["players"][PLAYER_A]["round_state"]["synergy_used"].get("convergencia_lunar"))
        activated = [event for event in self.repository.get_events(match_id) if event["kind"] == "card_combo_activated"]
        self.assertEqual([event["payload"]["combo_id"] for event in activated], ["vazio_astral", "convergencia_lunar"])

    def test_only_one_combo_activates_per_play_and_priority_wins(self):
        match_id = self._create_match(a_cards=["arma_duas_luas", "arma_duas_luas", "magia_nevoa_antiga"])
        self._seed_zones(
            match_id,
            own_board=[("arma_duas_luas", "melee"), ("magia_nevoa_antiga", "siege")],
        )
        receipt = self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_A,
            instance_id=self._hand_instance(match_id, PLAYER_A, "arma_duas_luas"),
        )
        self.assertEqual(receipt.result["outcome"], "applied")
        activated = [event for event in self.repository.get_events(match_id) if event["kind"] == "card_combo_activated"]
        self.assertEqual(len(activated), 1)
        self.assertEqual(activated[0]["payload"]["combo_id"], "passos_duas_luas")

    def test_all_four_faction_passives_are_loaded_and_apply_to_their_first_unit(self):
        cases = {
            "golden_order": "arma_lanca_fornalha",
            "crimson_veil": "arma_martelo_fornalha",
            "dark_moon": "arma_cajado_marulho",
            "the_forgotten": "luterano_anjo",
        }
        for faction_id, card_id in cases.items():
            with self.subTest(faction=faction_id):
                match_id = self._create_match(a_cards=[card_id], faction_id=faction_id)
                target_id = self._hand_instance(match_id, PLAYER_A, card_id)
                receipt = self.controller.play_unit(match_id, actor_player_id=PLAYER_A, instance_id=target_id)
                self.assertEqual(receipt.result["outcome"], "applied")
                state = self.repository.get_match(match_id)
                grants = [
                    item for item in state["instances"][target_id]["state"]["bonus_grants"]
                    if item["source_effect_id"] == "faction.first_unit_of_faction_each_round"
                ]
                self.assertEqual(len(grants), 1)
                self.assertEqual(grants[0]["amount"], 1)
                self.assertEqual(state["players"][PLAYER_A]["faction_id"], faction_id)

    def test_combo_is_not_repeated_for_same_player_in_same_round(self):
        match_id = self._create_match(
            a_cards=["gwent_unidade_herdeiro_portao", "gwent_unidade_veterano_cercos", "gwent_unidade_veterano_cercos"]
        )
        self._seed_zones(match_id, own_board=[("gwent_unidade_herdeiro_portao", "melee")])
        self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_A,
            instance_id=self._hand_instance(match_id, PLAYER_A, "gwent_unidade_veterano_cercos"),
        )
        self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_B,
            instance_id=self._hand_instance(match_id, PLAYER_B, FILLERS[0]),
        )
        self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_A,
            instance_id=self._hand_instance(match_id, PLAYER_A, "gwent_unidade_veterano_cercos"),
        )
        activated = [event for event in self.repository.get_events(match_id) if event["kind"] == "card_combo_activated"]
        self.assertEqual([event["payload"]["combo_id"] for event in activated], ["muralha_inabalavel"])

    def test_combo_team_bonus_targets_only_previously_boarded_same_row_allies(self):
        match_id = self._create_match(a_cards=["gwent_unidade_herdeiro_portao", "gwent_unidade_veterano_cercos"])
        seeded = self._seed_zones(
            match_id,
            own_board=[("gwent_unidade_herdeiro_portao", "melee"), ("arma_cajado_marulho", "ranged")],
        )
        activator_id = self._hand_instance(match_id, PLAYER_A, "gwent_unidade_veterano_cercos")
        receipt = self.controller.play_unit(match_id, actor_player_id=PLAYER_A, instance_id=activator_id)
        self.assertEqual(receipt.result["outcome"], "applied")
        state = self.repository.get_match(match_id)
        ally_id = seeded[PLAYER_A][0]
        self.assertEqual(bonus_total(state["instances"][activator_id]), 2)
        self.assertEqual(bonus_total(state["instances"][ally_id]), 1)
        ranged_ally_id = seeded[PLAYER_A][1]
        self.assertEqual(bonus_total(state["instances"][ranged_ally_id]), 0)
        combo_event = next(event for event in self.repository.get_events(match_id) if event["kind"] == "card_combo_activated")
        self.assertEqual(combo_event["payload"]["team_bonus_target_instance_ids"], [ally_id])

    def test_faction_passive_ignores_off_faction_play_and_resets_next_round(self):
        match_id = self._create_match(
            a_cards=["arma_cajado_marulho", "gwent_unidade_herdeiro_portao", "gwent_unidade_veterano_cercos"],
            faction_id="golden_order",
        )
        off_faction_id = self._hand_instance(match_id, PLAYER_A, "arma_cajado_marulho")
        self.controller.play_unit(match_id, actor_player_id=PLAYER_A, instance_id=off_faction_id)
        state = self.repository.get_match(match_id)
        self.assertFalse(state["players"][PLAYER_A]["round_state"]["faction_passive_used"])
        self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_B,
            instance_id=self._hand_instance(match_id, PLAYER_B, FILLERS[0]),
        )
        first_faction_unit = self._hand_instance(match_id, PLAYER_A, "gwent_unidade_herdeiro_portao")
        self.controller.play_unit(match_id, actor_player_id=PLAYER_A, instance_id=first_faction_unit)
        state = self.repository.get_match(match_id)
        self.assertEqual(bonus_total(state["instances"][first_faction_unit]), 1)
        self.assertTrue(state["players"][PLAYER_A]["round_state"]["faction_passive_used"])
        self.controller.play_unit(
            match_id,
            actor_player_id=PLAYER_B,
            instance_id=self._hand_instance(match_id, PLAYER_B, FILLERS[1]),
        )
        second_faction_unit = self._hand_instance(match_id, PLAYER_A, "gwent_unidade_veterano_cercos")
        self.controller.play_unit(match_id, actor_player_id=PLAYER_A, instance_id=second_faction_unit)
        state = self.repository.get_match(match_id)
        passive_grants = [
            grant for grant in state["instances"][second_faction_unit]["state"]["bonus_grants"]
            if grant["source_effect_id"] == "faction.first_unit_of_faction_each_round"
        ]
        self.assertEqual(passive_grants, [])
        # Both players pass; the new round must reset the once-per-round flag.
        self.controller.pass_turn(match_id, actor_player_id=PLAYER_B)
        self.controller.pass_turn(match_id, actor_player_id=PLAYER_A)
        state = self.repository.get_match(match_id)
        self.assertEqual(self.repository.get_match_runtime(match_id)["round_number"], 2)
        self.assertFalse(state["players"][PLAYER_A]["round_state"]["faction_passive_used"])

    def test_all_ten_leader_handlers_resolve_their_declared_alpha_behavior(self):
        scenarios = [
            {
                "leader": "comandante_fornalha",
                "own_board": [("arma_lanca_fornalha", "melee"), ("arma_cajado_marulho", "ranged")],
                "row": None,
                "check": lambda state, ids: self.assertEqual(bonus_total(state["instances"][ids[PLAYER_A][0]]), 2),
            },
            {
                "leader": "bastiao_ancestral",
                "own_board": [("arma_lanca_fornalha", "melee"), ("arma_martelo_fornalha", "melee"), ("arma_cajado_marulho", "ranged")],
                "row": "melee",
                "check": lambda state, ids: self.assertEqual(sum(bool(state["instances"][item]["state"]["protection_grants"]) for item in ids[PLAYER_A]), 2),
            },
            {
                "leader": "juiz_cerco",
                "own_board": [("arma_lanca_fornalha", "melee"), ("arma_cajado_marulho", "ranged")],
                "own_statuses": {"arma_lanca_fornalha": ["status.bleeding"], "arma_cajado_marulho": ["status.madness"]},
                "row": None,
                "check": lambda state, ids: self.assertEqual([len(state["instances"][item]["state"]["status_applications"]) for item in ids[PLAYER_A]], [0, 0]),
            },
            {
                "leader": "arquimaga_eclipse",
                "own_board": [("luterano_papa", "siege"), ("arma_lanca_fornalha", "melee")],
                "own_statuses": {"luterano_papa": ["status.frost", "status.scarlet_rot"], "arma_lanca_fornalha": ["status.bleeding"]},
                "row": None,
                "check": lambda state, ids: self.assertEqual(status_counts(state["instances"][ids[PLAYER_A][0]])["status.frost"], 0),
            },
            {
                "leader": "mestre_veu",
                "enemy_board": [("arma_lanca_fornalha", "melee"), ("arma_martelo_fornalha", "melee")],
                "enemy_statuses": {"arma_lanca_fornalha": ["status.bleeding"], "arma_martelo_fornalha": ["status.bleeding"]},
                "row": "melee",
                "check": lambda state, ids: self.assertEqual([bonus_total(state["instances"][item]) for item in ids[PLAYER_B]], [-2, -2]),
            },
            {
                "leader": "sombra_caminhante",
                "own_board": [("gwent_unidade_herdeiro_portao", "melee"), ("arma_grande_sino", "melee")],
                "row": "melee",
                "check": lambda state, ids: self.assertEqual(
                    sorted(grant["amount"] for grant in state["instances"][ids[PLAYER_A][1]]["state"]["bonus_grants"]), [1, 2]
                ),
            },
            {
                "leader": "voz_caidos",
                "own_discard": ["luterano_anjo", "chefe_vigia_cinzento", "arma_grande_sino"],
                "row": "siege",
                "check": lambda state, ids: self.assertEqual(state["instances"][ids[PLAYER_A][1]]["state"]["current_row"], "siege"),
            },
            {
                "leader": "lider_papa_esquecido",
                "own_board": [("luterano_anjo", "ranged"), ("luterano_papa", "siege")],
                "row": "ranged",
                "check": lambda state, ids: self.assertEqual(bonus_total(state["instances"][ids[PLAYER_A][0]]), 1),
            },
            {
                "leader": "mestre_eclipse",
                "enemy_board": [("arma_lanca_fornalha", "melee"), ("arma_martelo_fornalha", "melee"), ("arma_grande_sino", "melee")],
                "row": "melee",
                "check": lambda state, ids: self.assertTrue(all(status_counts(state["instances"][item])["status.frost"] == 1 for item in ids[PLAYER_B])),
            },
            {
                "leader": "oraculo_tempestade",
                "own_board": [("arma_cajado_marulho", "ranged"), ("luterano_anjo", "ranged"), ("arma_lanca_fornalha", "melee")],
                "row": "ranged",
                "check": lambda state, ids: self.assertTrue(all(bonus_total(state["instances"][item]) >= 2 for item in ids[PLAYER_A][:2])),
            },
        ]
        for index, scenario in enumerate(scenarios):
            with self.subTest(leader=scenario["leader"]):
                match_id = self._create_match(
                    a_cards=[card for card, _row in scenario.get("own_board", [])] + scenario.get("own_discard", []) + FILLERS,
                    b_cards=[card for card, _row in scenario.get("enemy_board", [])] + FILLERS,
                    leader_id=scenario["leader"],
                )
                ids = self._seed_zones(
                    match_id,
                    own_board=scenario.get("own_board", []),
                    enemy_board=scenario.get("enemy_board", []),
                    own_discard=scenario.get("own_discard", []),
                    own_statuses=scenario.get("own_statuses"),
                    enemy_statuses=scenario.get("enemy_statuses"),
                )
                result = self.controller.activate_leader(
                    match_id,
                    actor_player_id=PLAYER_A,
                    selected_row=scenario["row"],
                )
                self.assertEqual(result.result["outcome"], "applied")
                state = self.repository.get_match(match_id)
                self.assertTrue(state["players"][PLAYER_A]["leader_used"])
                scenario["check"](state, ids)
                self.assertTrue(any(event["kind"] == "leader_activated" for event in self.repository.get_events(match_id)))
                # The activation is once per match, even after the opponent takes a turn.
                self.controller.pass_turn(match_id, actor_player_id=PLAYER_B)
                replay = self.controller.activate_leader(match_id, actor_player_id=PLAYER_A, selected_row=scenario["row"])
                self.assertEqual(replay.result["outcome"], "rejected")
                self.assertEqual(replay.result["reason_code"], "leader_already_used")

    def test_leader_setup_rejects_faction_mismatch(self):
        cards = FILLERS * 2
        with self.assertRaises(Exception):
            self.controller.create_match(
                match_id=self.next_match_id,
                player_ids=[PLAYER_A, PLAYER_B],
                decks={PLAYER_A: cards, PLAYER_B: cards},
                initial_hand_size=12,
                player_factions={PLAYER_A: "dark_moon"},
                leaders={PLAYER_A: "comandante_fornalha"},
            )

    def test_leader_rejected_without_eligible_target_does_not_consume_activation(self):
        match_id = self._create_match(leader_id="bastiao_ancestral")
        result = self.controller.activate_leader(match_id, actor_player_id=PLAYER_A, selected_row="melee")
        self.assertEqual(result.result["outcome"], "rejected")
        state = self.repository.get_match(match_id)
        self.assertFalse(state["players"][PLAYER_A]["leader_used"])
        self.assertEqual(state["state_revision"], 0)


if __name__ == "__main__":
    unittest.main()
