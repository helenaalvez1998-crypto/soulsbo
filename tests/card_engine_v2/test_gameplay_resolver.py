from __future__ import annotations

import copy
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from sistemas.card_engine_v2 import (
    ActionDefinition,
    GameplayResolver,
    ProtectionProfile,
    SQLiteMatchRepository,
    TargetPolicy,
    build_target_offer,
)
from sistemas.card_engine_v2.errors import InvalidOperation
from sistemas.card_engine_v2.models import make_card_instance
from sistemas.card_engine_v2.repository import HandlerResult

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "docs/examples/card-instance-match.example.v7.json"

PLAYER_A = "1001"
PLAYER_B = "2002"
A_SOURCE = "00000000-0000-4000-8000-000000000005"
A_BOARD = "00000000-0000-4000-8000-000000000003"
B_BOARD = "00000000-0000-4000-8000-000000000002"
B_VENGEANCE = "00000000-0000-4000-8000-000000000004"


def uid() -> str:
    return str(uuid.uuid4())


def sample_state(match_id: int = 2026112701) -> dict:
    state = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    state["match_id"] = match_id
    state["state_revision"] = 0
    state["event_watermark"] = 0
    # The test special is an action source in hand, not an already-discarded card.
    if A_SOURCE in state["players"][PLAYER_A]["zones"]["discard"]:
        state["players"][PLAYER_A]["zones"]["discard"].remove(A_SOURCE)
        state["players"][PLAYER_A]["zones"]["hand"].append(A_SOURCE)
    return state


def make_resolver(
    *,
    no_target_outcome: str = "rejected",
    consume_source_on_no_target: bool = False,
    consume_source_on_block: bool = False,
    consume_source_on_success: bool = False,
) -> GameplayResolver:
    enemy_policy = TargetPolicy(
        policy_id="policy.enemy.board.remove",
        selection_mode="manual_set",
        target_side="enemies",
        source_zone="board",
        eligibility_metric="none",
        display_metric="base_power",
        sort_metric="none",
        direction="none",
        tie_breaker="zone_order",
        minimum_targets=1,
        maximum_targets="all",
        on_no_target=("consume_no_effect" if no_target_outcome == "consumed_no_effect" else "reject"),
    )
    ally_policy = TargetPolicy(
        policy_id="policy.ally.board.sacrifice",
        selection_mode="manual_single",
        target_side="allies",
        source_zone="board",
        eligibility_metric="none",
        display_metric="base_power",
        sort_metric="none",
        direction="none",
        tie_breaker="zone_order",
        minimum_targets=1,
        maximum_targets=1,
    )
    ally_set_policy = TargetPolicy(
        policy_id="policy.ally.board.buff",
        selection_mode="manual_set",
        target_side="allies",
        source_zone="board",
        eligibility_metric="none",
        display_metric="base_power",
        sort_metric="none",
        direction="none",
        tie_breaker="zone_order",
        minimum_targets=1,
        maximum_targets="all",
    )
    protect_policy = TargetPolicy(
        policy_id="policy.enemy.board.protect",
        selection_mode="manual_set",
        target_side="enemies",
        source_zone="board",
        eligibility_metric="none",
        display_metric="base_power",
        sort_metric="none",
        direction="none",
        tie_breaker="zone_order",
        minimum_targets=1,
        maximum_targets="all",
    )
    actions = {
        "unit.remove": ActionDefinition(
            action_type="unit.remove",
            source_effect_id="special.remove_units",
            target_policy_id=enemy_policy.policy_id,
            allowed_causes=frozenset({"normal_removal", "execution"}),
            no_target_outcome=no_target_outcome,
            consume_source_on_no_target=consume_source_on_no_target,
            consume_source_on_block=consume_source_on_block,
            consume_source_on_success=consume_source_on_success,
            allowed_source_zones=frozenset({"hand"}),
        ),
        "unit.sacrifice": ActionDefinition(
            action_type="unit.sacrifice",
            source_effect_id="effect.sacrifice_unit",
            target_policy_id=ally_policy.policy_id,
            allowed_causes=frozenset({"sacrifice"}),
        ),
        "unit.move": ActionDefinition(
            action_type="unit.move",
            source_effect_id="effect.test_movement",
            target_policy_id=ally_policy.policy_id,
            allowed_target_rows=frozenset({"melee", "ranged", "siege"}),
        ),
        "unit.grant_bonus": ActionDefinition(
            action_type="unit.grant_bonus",
            source_effect_id="effect.test_bonus",
            target_policy_id=ally_set_policy.policy_id,
            bonus_amount=2,
            bonus_expires_on="round_close",
            bonus_clamp_policy_id="balance.test.buff_clamp",
        ),
        "unit.grant_protection": ActionDefinition(
            action_type="unit.grant_protection",
            source_effect_id="effect.test_shield",
            target_policy_id=protect_policy.policy_id,
            protection_profile_id="example.protection.standard",
            protection_charges=1,
            protection_expires_on="round_close",
        ),
    }
    return GameplayResolver(
        actions=actions,
        target_policies={
            enemy_policy.policy_id: enemy_policy,
            ally_policy.policy_id: ally_policy,
            ally_set_policy.policy_id: ally_set_policy,
            protect_policy.policy_id: protect_policy,
        },
        protection_profiles={
            "example.protection.standard": ProtectionProfile("example.protection.standard")
        },
        vengeance_clamp_policy_id="balance.test.vengeance_clamp",
    )


def operation(action_type: str, payload: dict, *, revision: int = 0, operation_id: str | None = None) -> dict:
    return {
        "operation_id": operation_id or uid(),
        "actor": {"type": "player", "player_id": PLAYER_A},
        "expected_revision": revision,
        "action_type": action_type,
        "payload": payload,
    }


def move_vengeance_victim_to_board(state: dict, *, owner_id: str = PLAYER_B, row: str = "ranged") -> str:
    state["players"][PLAYER_B]["zones"]["discard"].remove(B_VENGEANCE)
    state["players"][owner_id]["zones"]["board"].append(B_VENGEANCE)
    state["instances"][B_VENGEANCE]["owner_player_id"] = owner_id
    state["instances"][B_VENGEANCE]["state"]["current_row"] = row
    state["instances"][B_VENGEANCE]["state"]["last_board_row"] = row
    return B_VENGEANCE


def add_ally_vengeance(state: dict, *, row: str = "ranged") -> str:
    source = state["instances"][B_VENGEANCE]
    instance_id = uid()
    instance = make_card_instance(
        card_id=source["card_id"],
        owner_player_id=PLAYER_A,
        origin_type="test_fixture",
        definition_snapshot=copy.deepcopy(source["definition_snapshot"]),
        instance_id=instance_id,
        initial_row=row,
    )
    state["instances"][instance_id] = instance
    state["players"][PLAYER_A]["zones"]["board"].append(instance_id)
    return instance_id


def add_standard_shield(instance: dict, *, grant_id: str | None = None, applied_event_id: str | None = None) -> str:
    identity = grant_id or uid()
    instance["state"]["protection_grants"].append(
        {
            "grant_id": identity,
            "profile_id": "example.protection.standard",
            "charges": 1,
            "source_effect_id": "effect.test_shield",
            "source_instance_id": None,
            "applied_event_id": applied_event_id or uid(),
            "expires_on": "round_close",
        }
    )
    return identity


class GameplayResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "gameplay.sqlite3"
        self.repo = SQLiteMatchRepository(self.db_path)
        self.state = sample_state()
        self.repo.create_match(self.state)
        self.resolver = make_resolver()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_action_bound_target_offer_rejects_wrong_source_owner_or_effect(self) -> None:
        with self.assertRaises(InvalidOperation):
            self.resolver.target_offer_for_action(
                self.repo,
                2026112701,
                actor_player_id=PLAYER_A,
                action_type="unit.remove",
                cause_id="normal_removal",
                source_instance_id=B_BOARD,
            )
        with self.assertRaises(InvalidOperation):
            self.resolver.target_offer_for_action(
                self.repo,
                2026112701,
                actor_player_id=PLAYER_A,
                action_type="unit.remove",
                cause_id="normal_removal",
                source_instance_id=A_BOARD,
            )

    def test_offer_is_server_generated_revision_bound_and_stably_ordered(self) -> None:
        policy = self.resolver.target_policies["policy.enemy.board.remove"]
        state = self.repo.get_match(2026112701)
        offer = build_target_offer(state, actor_player_id=PLAYER_A, policy=policy, source_instance_id=A_SOURCE)
        self.assertEqual(offer["state_revision"], 0)
        self.assertEqual(offer["selection_mode"], "manual_set")
        self.assertEqual([x["target_instance_id"] for x in offer["candidates"]], [B_BOARD])
        self.assertEqual(offer["candidates"][0]["base_power"], 5)
        self.assertEqual(offer["candidates"][0]["bonus"], 1)
        self.assertEqual(offer["requires_confirmation"], True)

    def test_primary_auto_fill_exposes_and_resolves_secondary_targets(self) -> None:
        state = sample_state(2026112702)
        extra_id = uid()
        extra = copy.deepcopy(state["instances"][B_BOARD])
        extra["instance_id"] = extra_id
        extra["exemplar_id"] = None
        extra["card_id"] = "second_enemy"
        extra["definition_snapshot"] = copy.deepcopy(extra["definition_snapshot"])
        extra["definition_snapshot"]["card_id"] = "second_enemy"
        extra["definition_snapshot"]["power_base"] = 3
        extra["definition_snapshot"]["definition_digest"] = "c" * 64
        extra["state"]["protection_grants"] = []
        extra["state"]["bonus_grants"] = []
        state["instances"][extra_id] = extra
        state["players"][PLAYER_B]["zones"]["board"].append(extra_id)
        self.repo.create_match(state)

        auto_fill_policy = TargetPolicy(
            policy_id="policy.enemy.primary-autofill",
            selection_mode="manual_primary_auto_fill",
            target_side="enemies",
            source_zone="board",
            eligibility_metric="none",
            display_metric="base_power",
            sort_metric="base_power",
            direction="descending",
            tie_breaker="zone_order",
            minimum_targets=2,
            maximum_targets=2,
            secondary_selection="auto_ranked",
        )
        auto_fill_action = ActionDefinition(
            action_type="unit.remove",
            source_effect_id="special.remove_units",
            target_policy_id=auto_fill_policy.policy_id,
            allowed_causes=frozenset({"normal_removal"}),
        )
        resolver = GameplayResolver(
            actions={"unit.remove": auto_fill_action},
            target_policies={auto_fill_policy.policy_id: auto_fill_policy},
            protection_profiles=self.resolver.protection_profiles,
            vengeance_clamp_policy_id=self.resolver.vengeance_clamp_policy_id,
        )
        offer = resolver.target_offer_for_action(
            self.repo,
            2026112702,
            actor_player_id=PLAYER_A,
            action_type="unit.remove",
            cause_id="normal_removal",
            source_instance_id=A_SOURCE,
            secondary_primary_id=B_BOARD,
        )
        self.assertEqual(offer["secondary_primary_instance_id"], B_BOARD)
        self.assertEqual(offer["secondary_targets_preview"], [extra_id])
        selection = {"mode": "manual_primary_auto_fill", "target_instance_id": B_BOARD}
        from sistemas.card_engine_v2.targeting import resolve_target_selection
        self.assertEqual(resolve_target_selection(offer, auto_fill_policy, selection), [B_BOARD, extra_id])

        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": selection,
            },
        )
        receipt = resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertIn(B_BOARD, saved["players"][PLAYER_B]["zones"]["discard"])
        self.assertIn(extra_id, saved["players"][PLAYER_B]["zones"]["discard"])

    def test_execution_uses_its_own_cause_bound_target_policy(self) -> None:
        generic_policy = self.resolver.target_policies["policy.enemy.board.remove"]
        execution_policy = TargetPolicy(
            policy_id="policy.enemy.execution.threshold",
            selection_mode="manual_set",
            target_side="enemies",
            source_zone="board",
            eligibility_metric="effective_power",
            display_metric="effective_power",
            sort_metric="effective_power",
            direction="ascending",
            tie_breaker="zone_order",
            minimum_targets=1,
            maximum_targets="all",
            predicates=({"predicate_id": "metric.at_most", "params": {"metric": "effective_power", "amount": 5}},),
        )
        removal_action = ActionDefinition(
            action_type="unit.remove",
            source_effect_id="special.remove_units",
            cause_target_policy_ids=(
                ("normal_removal", generic_policy.policy_id),
                ("execution", execution_policy.policy_id),
            ),
            allowed_causes=frozenset({"normal_removal", "execution"}),
        )
        resolver = GameplayResolver(
            actions={
                **self.resolver.actions,
                "unit.remove": removal_action,
            },
            target_policies={
                **self.resolver.target_policies,
                execution_policy.policy_id: execution_policy,
            },
            protection_profiles=self.resolver.protection_profiles,
            vengeance_clamp_policy_id=self.resolver.vengeance_clamp_policy_id,
            metric_resolver=lambda _state, instance, _metric: (
                instance["definition_snapshot"]["power_base"]
                + sum(grant["amount"] for grant in instance["state"]["bonus_grants"])
            ),
        )
        normal_offer = resolver.target_offer_for_action(
            self.repo,
            2026112701,
            actor_player_id=PLAYER_A,
            action_type="unit.remove",
            source_instance_id=A_SOURCE,
            cause_id="normal_removal",
        )
        execution_offer = resolver.target_offer_for_action(
            self.repo,
            2026112701,
            actor_player_id=PLAYER_A,
            action_type="unit.remove",
            source_instance_id=A_SOURCE,
            cause_id="execution",
        )
        self.assertEqual([item["target_instance_id"] for item in normal_offer["candidates"]], [B_BOARD])
        self.assertEqual(execution_offer["candidates"], [])  # effective power is 6, above the release-bound threshold 5

    def test_effective_power_requires_a_release_bound_resolver(self) -> None:
        policy = TargetPolicy(
            policy_id="policy.effective.power",
            selection_mode="manual_single",
            target_side="enemies",
            source_zone="board",
            eligibility_metric="effective_power",
            display_metric="effective_power",
            sort_metric="effective_power",
            direction="descending",
            minimum_targets=1,
            maximum_targets=1,
        )
        state = self.repo.get_match(2026112701)
        with self.assertRaises(InvalidOperation):
            build_target_offer(state, actor_player_id=PLAYER_A, policy=policy)
        offer = build_target_offer(
            state,
            actor_player_id=PLAYER_A,
            policy=policy,
            metric_resolver=lambda _state, instance, _metric: instance["definition_snapshot"]["power_base"]
            + sum(grant["amount"] for grant in instance["state"]["bonus_grants"]),
        )
        self.assertEqual(offer["candidates"][0]["effective_power"], 6)
        self.assertEqual(offer["candidates"][0]["eligibility_value"], 6)

    def test_manual_selection_rejects_instance_not_in_offer(self) -> None:
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [A_BOARD]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "invalid_target_selection")
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)

    def test_successful_removal_updates_zone_counter_and_event(self) -> None:
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        state = self.repo.get_match(2026112701)
        events = self.repo.get_events(2026112701)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertIn(B_BOARD, state["players"][PLAYER_B]["zones"]["discard"])
        self.assertNotIn(B_BOARD, state["players"][PLAYER_B]["zones"]["board"])
        self.assertEqual(state["players"][PLAYER_B]["counters"]["board_removal_count"], 2)
        self.assertEqual([event["kind"] for event in events], ["unit_removed"])
        self.assertEqual(events[0]["payload"]["cause_id"], "normal_removal")

    def test_shield_blocks_and_consumes_exactly_one_charge_without_vengeance(self) -> None:
        state = sample_state(2026112702)
        grant_id = add_standard_shield(state["instances"][B_BOARD])
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "execution",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        state = self.repo.get_match(2026112702)
        events = self.repo.get_events(2026112702)
        self.assertEqual(receipt.result["outcome"], "blocked")
        self.assertEqual(receipt.result["target_results"][0]["outcome"], "blocked")
        self.assertEqual(state["players"][PLAYER_B]["counters"]["board_removal_count"], 1)
        self.assertEqual(state["instances"][B_BOARD]["state"]["protection_grants"], [])
        self.assertEqual([event["kind"] for event in events], ["unit_removal_blocked"])
        self.assertEqual(receipt.result["costs"]["protection_grants_consumed"], [grant_id])

    def test_block_cost_policy_can_consume_source_independently_of_shield_charge(self) -> None:
        state = sample_state(2026112702)
        grant_id = add_standard_shield(state["instances"][B_BOARD])
        self.repo.create_match(state)
        resolver = make_resolver(consume_source_on_block=True)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
        )
        receipt = resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        events = self.repo.get_events(2026112702)
        self.assertEqual(receipt.result["outcome"], "blocked")
        self.assertEqual(receipt.result["costs"]["protection_grants_consumed"], [grant_id])
        self.assertTrue(receipt.result["costs"]["source_consumed"])
        self.assertIn(A_SOURCE, saved["players"][PLAYER_A]["zones"]["discard"])
        self.assertEqual([event["kind"] for event in events], ["unit_removal_blocked", "action_source_consumed"])
        self.assertEqual(events[1]["caused_by_event_ids"], [events[0]["event_id"]])

    def test_sacrifice_bypasses_shield_and_vengeance_is_reactive(self) -> None:
        state = sample_state(2026112702)
        victim_id = add_ally_vengeance(state, row="ranged")
        add_standard_shield(state["instances"][victim_id])
        self.repo.create_match(state)
        request = operation(
            "unit.sacrifice",
            {
                "cause_id": "sacrifice",
                "selection": {"mode": "manual_single", "target_instance_id": victim_id},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        events = self.repo.get_events(2026112702)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertIn(victim_id, saved["players"][PLAYER_A]["zones"]["discard"])
        self.assertEqual(saved["players"][PLAYER_A]["counters"]["sacrifice_count"], 1)
        # A round_close protection grant remains represented until its declared expiry.
        self.assertEqual(len(saved["instances"][victim_id]["state"]["protection_grants"]), 1)
        self.assertEqual([event["kind"] for event in events], ["unit_removed", "vengeance_bonus_applied"])
        self.assertEqual(events[1]["effect_scope"], "reactive")
        self.assertEqual(events[1]["source_effect_id"], "effect.vengeance_on_removal")
        self.assertEqual(events[1]["caused_by_event_ids"], [events[0]["event_id"]])
        self.assertEqual(saved["instances"][A_BOARD]["state"]["bonus_grants"][-1]["amount"], 1)

    def test_successful_removal_of_vengeance_unit_triggers_only_same_row_survivors(self) -> None:
        state = sample_state(2026112702)
        state["players"][PLAYER_B]["zones"]["discard"].remove(B_VENGEANCE)
        state["players"][PLAYER_B]["zones"]["board"].append(B_VENGEANCE)
        state["instances"][B_VENGEANCE]["state"]["current_row"] = "ranged"
        state["instances"][B_VENGEANCE]["state"]["last_board_row"] = "ranged"
        state["instances"][B_BOARD]["state"]["current_row"] = "ranged"
        state["instances"][B_BOARD]["state"]["last_board_row"] = "ranged"
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_VENGEANCE]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        events = self.repo.get_events(2026112702)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual([event["kind"] for event in events], ["unit_removed", "vengeance_bonus_applied"])
        self.assertEqual(events[1]["target_instance_ids"], [B_BOARD])
        self.assertEqual(saved["instances"][B_BOARD]["state"]["bonus_grants"][-1]["amount"], 1)
        self.assertEqual(saved["instances"][A_BOARD]["state"]["bonus_grants"], [])

    def test_successful_execution_triggers_vengeance_as_a_reactive_event(self) -> None:
        state = sample_state(2026112702)
        state["players"][PLAYER_B]["zones"]["discard"].remove(B_VENGEANCE)
        state["players"][PLAYER_B]["zones"]["board"].append(B_VENGEANCE)
        state["instances"][B_VENGEANCE]["state"]["current_row"] = "ranged"
        state["instances"][B_VENGEANCE]["state"]["last_board_row"] = "ranged"
        state["instances"][B_BOARD]["state"]["current_row"] = "ranged"
        state["instances"][B_BOARD]["state"]["last_board_row"] = "ranged"
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "execution",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_VENGEANCE]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        events = self.repo.get_events(2026112702)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual([event["kind"] for event in events], ["unit_removed", "vengeance_bonus_applied"])
        self.assertEqual(events[0]["payload"]["cause_id"], "execution")
        self.assertEqual(events[1]["caused_by_event_ids"], [events[0]["event_id"]])

    def test_multi_target_removal_resolves_vengeance_after_all_direct_removals(self) -> None:
        state = sample_state(2026112702)
        state["players"][PLAYER_B]["zones"]["discard"].remove(B_VENGEANCE)
        state["players"][PLAYER_B]["zones"]["board"].append(B_VENGEANCE)
        original_b_board_vengeance_grants = sum(
            1 for grant in state["instances"][B_BOARD]["state"]["bonus_grants"]
            if grant["source_effect_id"] == "effect.vengeance_on_removal"
        )
        for instance_id in (B_VENGEANCE, B_BOARD):
            state["instances"][instance_id]["state"]["current_row"] = "ranged"
            state["instances"][instance_id]["state"]["last_board_row"] = "ranged"
        survivor_id = uid()
        survivor = copy.deepcopy(state["instances"][B_BOARD])
        survivor["instance_id"] = survivor_id
        survivor["exemplar_id"] = None
        survivor["card_id"] = "surviving_ally"
        survivor["definition_snapshot"] = copy.deepcopy(survivor["definition_snapshot"])
        survivor["definition_snapshot"]["card_id"] = "surviving_ally"
        survivor["definition_snapshot"]["definition_digest"] = "b" * 64
        survivor["state"]["protection_grants"] = []
        survivor["state"]["bonus_grants"] = []
        state["instances"][survivor_id] = survivor
        state["players"][PLAYER_B]["zones"]["board"].append(survivor_id)
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_VENGEANCE, B_BOARD]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        events = self.repo.get_events(2026112702)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual([event["kind"] for event in events], ["unit_removed", "unit_removed", "vengeance_bonus_applied"])
        self.assertEqual(events[-1]["target_instance_ids"], [survivor_id])
        self.assertEqual(saved["instances"][survivor_id]["state"]["bonus_grants"][-1]["source_effect_id"], "effect.vengeance_on_removal")
        self.assertEqual(
            sum(1 for grant in saved["instances"][B_BOARD]["state"]["bonus_grants"] if grant["source_effect_id"] == "effect.vengeance_on_removal"),
            original_b_board_vengeance_grants,
        )

    def test_blocked_vengeance_unit_does_not_trigger_reactive_event(self) -> None:
        state = sample_state(2026112702)
        state["players"][PLAYER_B]["zones"]["discard"].remove(B_VENGEANCE)
        state["players"][PLAYER_B]["zones"]["board"].append(B_VENGEANCE)
        state["instances"][B_VENGEANCE]["state"]["current_row"] = "ranged"
        state["instances"][B_VENGEANCE]["state"]["last_board_row"] = "ranged"
        add_standard_shield(state["instances"][B_VENGEANCE])
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_VENGEANCE]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        events = self.repo.get_events(2026112702)
        self.assertEqual(receipt.result["outcome"], "blocked")
        self.assertEqual([event["kind"] for event in events], ["unit_removal_blocked"])

    def test_partial_removal_reports_applied_and_blocked_targets(self) -> None:
        state = sample_state(2026112702)
        add_standard_shield(state["instances"][B_BOARD])
        extra_id = uid()
        extra = copy.deepcopy(state["instances"][B_BOARD])
        extra["instance_id"] = extra_id
        extra["exemplar_id"] = None
        extra["card_id"] = "unshielded_enemy"
        extra["definition_snapshot"] = copy.deepcopy(extra["definition_snapshot"])
        extra["definition_snapshot"]["card_id"] = "unshielded_enemy"
        extra["definition_snapshot"]["definition_digest"] = "a" * 64
        extra["state"]["protection_grants"] = []
        state["instances"][extra_id] = extra
        state["players"][PLAYER_B]["zones"]["board"].append(extra_id)
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD, extra_id]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        self.assertEqual(receipt.result["outcome"], "partial")
        self.assertEqual([x["outcome"] for x in receipt.result["target_results"]], ["blocked", "applied"])
        self.assertEqual(self.repo.get_match(2026112702)["state_revision"], 1)

    def test_no_target_can_be_recorded_as_consumed_no_effect(self) -> None:
        state = sample_state(2026112702)
        state["players"][PLAYER_B]["zones"]["board"].clear()
        state["players"][PLAYER_B]["zones"]["discard"].append(B_BOARD)
        state["instances"][B_BOARD]["state"]["current_row"] = None
        self.repo.create_match(state)
        resolver = make_resolver(
            no_target_outcome="consumed_no_effect",
            consume_source_on_no_target=True,
        )
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": []},
            },
        )
        receipt = resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        self.assertEqual(receipt.result["outcome"], "consumed_no_effect")
        self.assertTrue(receipt.result["costs"]["source_consumed"])
        self.assertIn(A_SOURCE, saved["players"][PLAYER_A]["zones"]["discard"])
        self.assertEqual([event["kind"] for event in self.repo.get_events(2026112702)], ["action_source_consumed"])
        self.assertEqual(receipt.result["revision_after"], receipt.result["revision_before"] + 1)
        self.assertIsNotNone(self.repo.get_operation(2026112702, request["operation_id"]))

    def test_unknown_cause_is_rejected_before_any_mutation(self) -> None:
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "round_archive",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "invalid_removal_cause")
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)
        self.assertEqual(self.repo.get_events(2026112701), [])

    def test_movement_updates_row_projection_and_does_not_trigger_vengeance(self) -> None:
        request = operation(
            "unit.move",
            {"selection": {"mode": "manual_single", "target_instance_id": A_BOARD}, "target_row": "siege"},
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        state = self.repo.get_match(2026112701)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual(state["instances"][A_BOARD]["state"]["current_row"], "siege")
        self.assertEqual(state["instances"][A_BOARD]["state"]["last_board_row"], "siege")
        self.assertEqual([event["kind"] for event in self.repo.get_events(2026112701)], ["unit_moved"])

    def test_move_to_same_row_is_noop_without_fake_event(self) -> None:
        request = operation(
            "unit.move",
            {"selection": {"mode": "manual_single", "target_instance_id": A_BOARD}, "target_row": "ranged"},
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(self.repo.get_events(2026112701), [])
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)

    def test_bonus_grant_is_traced_and_persisted(self) -> None:
        request = operation(
            "unit.grant_bonus",
            {"selection": {"mode": "manual_set", "target_instance_ids": [A_BOARD]}},
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        state = self.repo.get_match(2026112701)
        grants = state["instances"][A_BOARD]["state"]["bonus_grants"]
        events = self.repo.get_events(2026112701)
        self.assertEqual(receipt.result["outcome"], "applied")
        self.assertEqual(grants[-1]["amount"], 2)
        self.assertEqual(grants[-1]["source_effect_id"], "effect.test_bonus")
        self.assertEqual(grants[-1]["applied_event_id"], events[0]["event_id"])
        self.assertEqual(events[0]["kind"], "bonus_grant_applied")

    def test_reactive_bonus_deduplicates_on_operation_replay(self) -> None:
        state = sample_state(2026112702)
        state["players"][PLAYER_B]["zones"]["discard"].remove(B_VENGEANCE)
        state["players"][PLAYER_B]["zones"]["board"].append(B_VENGEANCE)
        state["instances"][B_VENGEANCE]["state"]["current_row"] = "ranged"
        state["instances"][B_VENGEANCE]["state"]["last_board_row"] = "ranged"
        state["instances"][B_BOARD]["state"]["current_row"] = "ranged"
        state["instances"][B_BOARD]["state"]["last_board_row"] = "ranged"
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_VENGEANCE]},
            },
        )
        first = self.resolver.execute(self.repo, 2026112702, request)
        second = self.resolver.execute(self.repo, 2026112702, request)
        state_after = self.repo.get_match(2026112702)
        grants = state_after["instances"][B_BOARD]["state"]["bonus_grants"]
        vengeance_grants = [grant for grant in grants if grant["source_effect_id"] == "effect.vengeance_on_removal"]
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(len(vengeance_grants), 2)  # one pre-existing fixture grant + one newly applied
        self.assertEqual(len(self.repo.get_events(2026112702)), 2)

    def test_protection_grant_is_server_bound_persisted_and_consumed_by_removal(self) -> None:
        grant_request = operation(
            "unit.grant_protection",
            {"selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]}},
        )
        grant_receipt = self.resolver.execute(self.repo, 2026112701, grant_request)
        after_grant = self.repo.get_match(2026112701)
        grant = after_grant["instances"][B_BOARD]["state"]["protection_grants"][-1]
        event = self.repo.get_events(2026112701)[0]
        self.assertEqual(grant_receipt.result["outcome"], "applied")
        self.assertEqual(grant["profile_id"], "example.protection.standard")
        self.assertEqual(grant["charges"], 1)
        self.assertEqual(grant["applied_event_id"], event["event_id"])
        self.assertEqual(event["kind"], "protection_grant_applied")
        self.assertEqual(event["payload"]["grant_ids_by_target"][B_BOARD], grant["grant_id"])

        removal_request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
            revision=1,
        )
        removal_receipt = self.resolver.execute(self.repo, 2026112701, removal_request)
        saved = self.repo.get_match(2026112701)
        self.assertEqual(removal_receipt.result["outcome"], "blocked")
        self.assertEqual(saved["instances"][B_BOARD]["state"]["protection_grants"], [])
        self.assertIn(B_BOARD, saved["players"][PLAYER_B]["zones"]["board"])

    def test_protection_parameters_cannot_be_overridden_by_client(self) -> None:
        request = operation(
            "unit.grant_protection",
            {
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
                "profile_id": "client.untrusted",
                "charges": 100,
                "expires_on": "permanent_instance",
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "client_supplied_protection_parameters")
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)
        self.assertEqual(self.repo.get_events(2026112701), [])

    def test_bonus_parameters_are_server_bound_and_client_override_is_rejected(self) -> None:
        before = self.repo.get_match(2026112701)
        request = operation(
            "unit.grant_bonus",
            {
                "selection": {"mode": "manual_set", "target_instance_ids": [A_BOARD]},
                "amount": 999,
                "expires_on": "permanent_instance",
                "clamp_policy_id": "client.untrusted",
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        after = self.repo.get_match(2026112701)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "client_supplied_effect_parameters")
        self.assertEqual(after["state_revision"], before["state_revision"])
        self.assertEqual(after["instances"][A_BOARD]["state"]["bonus_grants"], before["instances"][A_BOARD]["state"]["bonus_grants"])
        self.assertEqual(self.repo.get_events(2026112701), [])

    def test_move_rejects_row_not_allowed_by_release_config(self) -> None:
        request = operation(
            "unit.move",
            {"selection": {"mode": "manual_single", "target_instance_id": A_BOARD}, "target_row": "void"},
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "target_row_not_allowed_by_action")
        self.assertEqual(self.repo.get_match(2026112701)["state_revision"], 0)
        self.assertEqual(self.repo.get_events(2026112701), [])

    def test_source_in_disallowed_zone_is_rejected_before_removal_mutates_any_target(self) -> None:
        state = sample_state(2026112702)
        state["players"][PLAYER_A]["zones"]["hand"].remove(A_SOURCE)
        state["players"][PLAYER_A]["zones"]["discard"].append(A_SOURCE)
        self.repo.create_match(state)
        resolver = make_resolver(consume_source_on_success=True)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
        )
        receipt = resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "source_zone_not_allowed")
        self.assertIn(B_BOARD, saved["players"][PLAYER_B]["zones"]["board"])
        self.assertEqual(saved["players"][PLAYER_B]["counters"]["board_removal_count"], 1)
        self.assertEqual(self.repo.get_events(2026112702), [])

    def test_unknown_shield_profile_rejects_entire_action_before_consumption(self) -> None:
        state = sample_state(2026112702)
        add_standard_shield(state["instances"][B_BOARD])
        state["instances"][B_BOARD]["state"]["protection_grants"][0]["profile_id"] = "unknown.protection.profile"
        self.repo.create_match(state)
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112702, request)
        saved = self.repo.get_match(2026112702)
        self.assertEqual(receipt.result["outcome"], "rejected")
        self.assertEqual(receipt.result["reason_code"], "invalid_protection_state")
        self.assertIn(B_BOARD, saved["players"][PLAYER_B]["zones"]["board"])
        self.assertEqual(saved["instances"][B_BOARD]["state"]["protection_grants"][0]["charges"], 1)
        self.assertEqual(self.repo.get_events(2026112702), [])

    def test_action_result_and_target_offer_match_group_d_schemas(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("jsonschema not installed")
        schemas_dir = ROOT / "docs" / "schemas"
        offer_schema = json.loads((schemas_dir / "card-game-target-offer.schema.v1.json").read_text(encoding="utf-8"))
        result_schema = json.loads((schemas_dir / "card-game-action-result.schema.v1.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(offer_schema)
        Draft202012Validator.check_schema(result_schema)
        policy = self.resolver.target_policies["policy.enemy.board.remove"]
        offer = self.resolver.target_offer(
            self.repo,
            2026112701,
            actor_player_id=PLAYER_A,
            policy_id=policy.policy_id,
            source_instance_id=A_SOURCE,
        )
        offer_errors = list(Draft202012Validator(offer_schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(offer))
        self.assertEqual(offer_errors, [])
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        result_errors = list(Draft202012Validator(result_schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(receipt.result))
        self.assertEqual(result_errors, [])
        rejected_request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [A_BOARD]},
            },
            revision=1,
        )
        rejected_receipt = self.resolver.execute(self.repo, 2026112701, rejected_request)
        rejected_errors = list(Draft202012Validator(result_schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(rejected_receipt.result))
        self.assertEqual(rejected_receipt.result["outcome"], "rejected")
        self.assertEqual(rejected_errors, [])

    def test_protection_priority_uses_event_sequence_then_grant_id(self) -> None:
        grant_early = "00000000-0000-4000-8000-000000000041"
        grant_late = "00000000-0000-4000-8000-000000000042"
        event_early = uid()
        event_late = uid()

        def add_shields(state: dict, _request: dict) -> HandlerResult:
            state["instances"][B_BOARD]["state"]["protection_grants"] = [
                {
                    "grant_id": grant_late,
                    "profile_id": "example.protection.standard",
                    "charges": 1,
                    "source_effect_id": "effect.test_shield",
                    "source_instance_id": None,
                    "applied_event_id": event_late,
                    "expires_on": "round_close",
                },
                {
                    "grant_id": grant_early,
                    "profile_id": "example.protection.standard",
                    "charges": 1,
                    "source_effect_id": "effect.test_shield",
                    "source_instance_id": None,
                    "applied_event_id": event_early,
                    "expires_on": "round_close",
                },
            ]
            return HandlerResult(
                outcome="applied",
                state=state,
                events=[
                    {
                        "event_id": event_early,
                        "kind": "protection_grant_applied",
                        "effect_scope": "direct",
                        "source_effect_id": "effect.test_shield",
                        "source_instance_id": None,
                        "target_instance_ids": [B_BOARD],
                        "caused_by_event_ids": [],
                        "payload": {
                            "profile_id": "example.protection.standard",
                            "charges": 1,
                            "expires_on": "round_close",
                            "grant_ids_by_target": {B_BOARD: grant_early},
                        },
                    },
                    {
                        "event_id": event_late,
                        "kind": "protection_grant_applied",
                        "effect_scope": "direct",
                        "source_effect_id": "effect.test_shield",
                        "source_instance_id": None,
                        "target_instance_ids": [B_BOARD],
                        "caused_by_event_ids": [],
                        "payload": {
                            "profile_id": "example.protection.standard",
                            "charges": 1,
                            "expires_on": "round_close",
                            "grant_ids_by_target": {B_BOARD: grant_late},
                        },
                    },
                ],
            )

        self.repo.execute_operation(
            2026112701,
            {
                "operation_id": uid(),
                "actor": {"type": "system", "system_id": "test_setup"},
                "expected_revision": 0,
                "action_type": "test.add_shields",
                "payload": {},
            },
            add_shields,
        )
        request = operation(
            "unit.remove",
            {
                "source_instance_id": A_SOURCE,
                "cause_id": "normal_removal",
                "selection": {"mode": "manual_set", "target_instance_ids": [B_BOARD]},
            },
            revision=1,
        )
        receipt = self.resolver.execute(self.repo, 2026112701, request)
        self.assertEqual(receipt.result["target_results"][0]["protection_grant_id"], grant_early)
        remaining = self.repo.get_match(2026112701)["instances"][B_BOARD]["state"]["protection_grants"]
        self.assertEqual([grant["grant_id"] for grant in remaining], [grant_late])


if __name__ == "__main__":
    unittest.main(verbosity=2)
