"""Minimal pure gameplay resolver for Card Engine v2 alpha.

This is an intentionally small vertical, not a complete card catalog or the
legacy engine replacement. All effect identities, target policies, protection
profiles and clamp policies are supplied by trusted release-bound config.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from typing import Any

from .errors import InvalidOperation
from .repository import HandlerResult, OperationReceipt, SQLiteMatchRepository
from .targeting import MetricResolver, TargetPolicy, build_target_offer, resolve_target_selection
from .validation import BLOCKABLE_CAUSES, REMOVAL_CAUSES, ROWS, ZONES, is_uuid4
from .zones import locate_instance, move_instance_row, transition_instance_zone


@dataclass(frozen=True, slots=True)
class ProtectionProfile:
    profile_id: str
    blocked_causes: frozenset[str] = frozenset(BLOCKABLE_CAUSES)

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise InvalidOperation("protection profile_id is required")
        if not self.blocked_causes.issubset(set(BLOCKABLE_CAUSES)):
            raise InvalidOperation("protection profiles may block normal_removal/execution only; sacrifice bypasses")


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    action_type: str
    source_effect_id: str
    target_policy_id: str | None = None
    cause_target_policy_ids: tuple[tuple[str, str], ...] = ()
    allowed_causes: frozenset[str] = frozenset()
    no_target_outcome: str = "rejected"
    consume_source_on_success: bool = False
    consume_source_on_block: bool = False
    consume_source_on_no_target: bool = False
    allowed_target_rows: frozenset[str] = frozenset()
    allowed_source_zones: frozenset[str] = frozenset({"hand", "board"})
    bonus_amount: int | None = None
    bonus_expires_on: str | None = None
    bonus_clamp_policy_id: str | None = None
    protection_profile_id: str | None = None
    protection_charges: int | None = None
    protection_expires_on: str | None = None
    source_card_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.action_type or not self.source_effect_id:
            raise InvalidOperation("action definition requires action_type and source_effect_id")
        if not isinstance(self.source_card_ids, frozenset) or any(not isinstance(item, str) or not item for item in self.source_card_ids):
            raise InvalidOperation("source_card_ids must be a frozenset of non-empty card IDs")
        if self.no_target_outcome not in ("rejected", "consumed_no_effect"):
            raise InvalidOperation("invalid no_target_outcome")
        for flag_name in ("consume_source_on_success", "consume_source_on_block", "consume_source_on_no_target"):
            if not isinstance(getattr(self, flag_name), bool):
                raise InvalidOperation(f"{flag_name} must be boolean")
        if self.consume_source_on_no_target and self.no_target_outcome != "consumed_no_effect":
            raise InvalidOperation("consume_source_on_no_target requires no_target_outcome=consumed_no_effect")
        if any((self.consume_source_on_success, self.consume_source_on_block, self.consume_source_on_no_target)) and self.action_type not in ("unit.remove", "unit.sacrifice"):
            raise InvalidOperation("source consumption is currently implemented only for removal/sacrifice actions")
        if not isinstance(self.allowed_causes, frozenset) or not self.allowed_causes.issubset(set(REMOVAL_CAUSES)):
            raise InvalidOperation("allowed_causes must be a frozenset of canonical removal causes")
        if not isinstance(self.allowed_target_rows, frozenset) or not self.allowed_target_rows.issubset(set(ROWS)):
            raise InvalidOperation("allowed_target_rows must be a frozenset of canonical rows")
        if not isinstance(self.allowed_source_zones, frozenset) or not self.allowed_source_zones.issubset(set(ZONES)):
            raise InvalidOperation("allowed_source_zones must be a frozenset of canonical zones")
        if not isinstance(self.cause_target_policy_ids, tuple):
            raise InvalidOperation("cause_target_policy_ids must be a tuple of (cause_id, policy_id) pairs")
        mapped_causes: set[str] = set()
        for item in self.cause_target_policy_ids:
            if not isinstance(item, tuple) or len(item) != 2:
                raise InvalidOperation("cause_target_policy_ids entries must be 2-item tuples")
            cause_id, policy_id = item
            if cause_id not in self.allowed_causes or not isinstance(policy_id, str) or not policy_id:
                raise InvalidOperation("cause target policy map contains an unsupported cause or policy")
            if cause_id in mapped_causes:
                raise InvalidOperation("cause target policy map contains duplicate causes")
            mapped_causes.add(cause_id)
        if self.cause_target_policy_ids and mapped_causes != set(self.allowed_causes):
            raise InvalidOperation("cause target policy map must define every allowed cause")
        if self.action_type == "unit.move" and not self.allowed_target_rows:
            raise InvalidOperation("unit.move requires server-configured allowed_target_rows")
        if self.action_type == "unit.grant_bonus":
            if not isinstance(self.bonus_amount, int) or isinstance(self.bonus_amount, bool) or self.bonus_amount == 0:
                raise InvalidOperation("unit.grant_bonus requires a non-zero server-configured bonus_amount")
            if self.bonus_expires_on not in ("round_close", "board_exit", "permanent_instance"):
                raise InvalidOperation("unit.grant_bonus requires a valid server-configured bonus_expires_on")
            if not isinstance(self.bonus_clamp_policy_id, str) or not self.bonus_clamp_policy_id:
                raise InvalidOperation("unit.grant_bonus requires a server-configured bonus_clamp_policy_id")
        if self.action_type == "unit.grant_protection":
            if not isinstance(self.protection_profile_id, str) or not self.protection_profile_id:
                raise InvalidOperation("unit.grant_protection requires a server-configured protection_profile_id")
            if not isinstance(self.protection_charges, int) or isinstance(self.protection_charges, bool) or self.protection_charges < 1:
                raise InvalidOperation("unit.grant_protection requires positive server-configured protection_charges")
            if self.protection_expires_on not in ("round_close", "board_exit", "permanent_instance"):
                raise InvalidOperation("unit.grant_protection requires a valid server-configured protection_expires_on")


    def policy_for_cause(self, cause_id: str) -> str | None:
        if self.cause_target_policy_ids:
            return dict(self.cause_target_policy_ids).get(cause_id)
        return self.target_policy_id


@dataclass(slots=True)
class GameplayResolver:
    """Server-side action registry plus deterministic pure gameplay handlers."""

    actions: dict[str, ActionDefinition]
    target_policies: dict[str, TargetPolicy]
    protection_profiles: dict[str, ProtectionProfile]
    vengeance_clamp_policy_id: str | None = None
    metric_resolver: MetricResolver | None = None

    def __post_init__(self) -> None:
        for key, action in self.actions.items():
            if key != action.action_type:
                raise InvalidOperation("action registry key must equal ActionDefinition.action_type")
        for key, policy in self.target_policies.items():
            if key != policy.policy_id:
                raise InvalidOperation("target policy registry key must equal TargetPolicy.policy_id")
        for key, profile in self.protection_profiles.items():
            if key != profile.profile_id:
                raise InvalidOperation("protection profile registry key must equal ProtectionProfile.profile_id")
        for action in self.actions.values():
            if action.action_type == "unit.grant_protection" and action.protection_profile_id not in self.protection_profiles:
                raise InvalidOperation(f"action references unknown protection profile: {action.protection_profile_id}")
            policy_ids = set()
            if action.target_policy_id is not None:
                policy_ids.add(action.target_policy_id)
            policy_ids.update(policy_id for _cause, policy_id in action.cause_target_policy_ids)
            for policy_id in policy_ids:
                policy = self.target_policies.get(policy_id)
                if policy is None:
                    raise InvalidOperation(f"action references unknown target policy: {policy_id}")
                policy_no_target = "consumed_no_effect" if policy.on_no_target == "consume_no_effect" else "rejected"
                if policy_no_target != action.no_target_outcome:
                    raise InvalidOperation("ActionDefinition and TargetPolicy no-target policies must match")
            if action.consume_source_on_no_target and action.action_type != "unit.remove":
                raise InvalidOperation("source consumption on no-target is currently implemented only for unit.remove")

    def target_offer(
        self,
        repository: SQLiteMatchRepository,
        match_id: int,
        *,
        actor_player_id: str,
        policy_id: str,
        source_instance_id: str | None = None,
        selected_row: str | None = None,
        secondary_primary_id: str | None = None,
    ) -> dict[str, Any]:
        state = repository.get_match(match_id)
        try:
            policy = self.target_policies[policy_id]
        except KeyError as exc:
            raise InvalidOperation(f"unknown server target policy: {policy_id}") from exc
        return build_target_offer(
            state,
            actor_player_id=actor_player_id,
            policy=policy,
            source_instance_id=source_instance_id,
            selected_row=selected_row,
            metric_resolver=self.metric_resolver,
            secondary_primary_id=secondary_primary_id,
        )

    def target_offer_for_action(
        self,
        repository: SQLiteMatchRepository,
        match_id: int,
        *,
        actor_player_id: str,
        action_type: str,
        source_instance_id: str | None = None,
        cause_id: str | None = None,
        selected_row: str | None = None,
        secondary_primary_id: str | None = None,
    ) -> dict[str, Any]:
        """Build an offer using the policy bound to the registered action/cause."""
        action = self.actions.get(action_type)
        if action is None:
            raise InvalidOperation(f"unknown action type: {action_type}")
        if cause_id is not None:
            if cause_id not in action.allowed_causes:
                raise InvalidOperation(f"cause {cause_id!r} is not allowed for {action_type}")
            policy_id = action.policy_for_cause(cause_id)
        else:
            policy_id = action.target_policy_id
        if policy_id is None:
            raise InvalidOperation("action has no target policy for this request")
        policy = self.target_policies[policy_id]
        state = repository.get_match(match_id)
        if actor_player_id not in state["players"]:
            raise InvalidOperation("actor is not a participant in this match")
        if source_instance_id is not None:
            if not is_uuid4(source_instance_id) or source_instance_id not in state["instances"]:
                raise InvalidOperation("source_instance_id is invalid")
            source_owner, source_zone = locate_instance(state, source_instance_id)
            if source_owner != actor_player_id:
                raise InvalidOperation("source instance is not owned by the actor")
            if source_zone not in action.allowed_source_zones:
                raise InvalidOperation("source instance is not in a zone allowed by the action")
            if action.source_card_ids:
                if state["instances"][source_instance_id].get("card_id") not in action.source_card_ids:
                    raise InvalidOperation("source instance card is not registered for the action")
            elif state["instances"][source_instance_id]["definition_snapshot"].get("effect_id") != action.source_effect_id:
                raise InvalidOperation("source instance does not match the registered action effect")
        return build_target_offer(
            state,
            actor_player_id=actor_player_id,
            policy=policy,
            source_instance_id=source_instance_id,
            selected_row=selected_row,
            metric_resolver=self.metric_resolver,
            secondary_primary_id=secondary_primary_id,
        )

    def execute(
        self,
        repository: SQLiteMatchRepository,
        match_id: int,
        request: dict[str, Any],
    ) -> OperationReceipt:
        # Event sequence data is read before the transaction. expected_revision
        # ensures any intervening committed gameplay mutation causes a stale
        # rejection before this callback runs, so this deterministic projection
        # cannot silently drift for an accepted request.
        event_sequence_by_id = {
            event["event_id"]: event["sequence"]
            for event in repository.get_events(match_id)
        }

        def contextual_handler(state: dict[str, Any], body: dict[str, Any]) -> HandlerResult:
            return self.handle(state, body, event_sequence_by_id=event_sequence_by_id)

        return repository.execute_operation(match_id, request, contextual_handler)

    def handle(
        self,
        state: dict[str, Any],
        request: dict[str, Any],
        *,
        event_sequence_by_id: dict[str, int] | None = None,
    ) -> HandlerResult:
        """Dispatcher suitable for SQLiteMatchRepository.execute_operation."""
        action = self.actions.get(request["action_type"])
        if action is None:
            return HandlerResult(outcome="rejected", state=state, reason_code="unknown_action")
        actor = request["actor"]
        if actor["type"] != "player":
            return HandlerResult(outcome="rejected", state=state, reason_code="player_actor_required")
        actor_id = actor["player_id"]
        if actor_id not in state["players"]:
            return HandlerResult(outcome="rejected", state=state, reason_code="actor_not_participant")

        payload = request["payload"]
        source_id = payload.get("source_instance_id")
        if source_id is not None:
            if not is_uuid4(source_id) or source_id not in state["instances"]:
                return HandlerResult(outcome="rejected", state=state, reason_code="invalid_source_instance")
            source_owner, source_zone = locate_instance(state, source_id)
            if source_owner != actor_id:
                return HandlerResult(outcome="rejected", state=state, reason_code="source_not_owned")
            if source_zone not in action.allowed_source_zones:
                return HandlerResult(outcome="rejected", state=state, reason_code="source_zone_not_allowed")
            if action.source_card_ids:
                source_card_id = state["instances"][source_id].get("card_id")
                if source_card_id not in action.source_card_ids:
                    return HandlerResult(outcome="rejected", state=state, reason_code="source_card_mismatch")
            else:
                source_effect_id = state["instances"][source_id]["definition_snapshot"].get("effect_id")
                if source_effect_id != action.source_effect_id:
                    return HandlerResult(outcome="rejected", state=state, reason_code="source_effect_mismatch")

        if request["action_type"] in ("unit.remove", "unit.sacrifice"):
            return self._resolve_removal(
                state, request, action, actor_id, event_sequence_by_id or {}
            )
        if request["action_type"] == "unit.move":
            return self._resolve_move(state, request, action, actor_id)
        if request["action_type"] == "unit.grant_bonus":
            return self._resolve_bonus(state, request, action, actor_id)
        if request["action_type"] == "unit.grant_protection":
            return self._resolve_protection_grant(state, request, action, actor_id)
        return HandlerResult(outcome="rejected", state=state, reason_code="action_not_implemented")

    def _resolve_removal(
        self,
        state: dict[str, Any],
        request: dict[str, Any],
        action: ActionDefinition,
        actor_id: str,
        event_sequence_by_id: dict[str, int],
    ) -> HandlerResult:
        payload = request["payload"]
        cause_id = payload.get("cause_id")
        if not isinstance(cause_id, str) or cause_id not in action.allowed_causes or cause_id not in REMOVAL_CAUSES:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_removal_cause")
        if request["action_type"] == "unit.sacrifice" and cause_id != "sacrifice":
            return HandlerResult(outcome="rejected", state=state, reason_code="sacrifice_action_requires_sacrifice_cause")
        if request["action_type"] == "unit.remove" and cause_id == "sacrifice":
            return HandlerResult(outcome="rejected", state=state, reason_code="use_sacrifice_action")

        policy_id = action.policy_for_cause(cause_id)
        if not policy_id or policy_id not in self.target_policies:
            return HandlerResult(outcome="rejected", state=state, reason_code="missing_target_policy")
        policy = self.target_policies[policy_id]
        source_id = payload.get("source_instance_id")
        selection = payload.get("selection", {})
        secondary_primary_id = (
            selection.get("target_instance_id")
            if isinstance(selection, dict) and selection.get("mode") == "manual_primary_auto_fill"
            else None
        )
        try:
            offer = build_target_offer(
                state,
                actor_player_id=actor_id,
                policy=policy,
                source_instance_id=source_id,
                selected_row=payload.get("selected_row"),
                metric_resolver=self.metric_resolver,
                secondary_primary_id=secondary_primary_id,
            )
        except InvalidOperation:
            return HandlerResult(outcome="rejected", state=state, reason_code="target_offer_failed")

        if not offer["candidates"]:
            if action.no_target_outcome == "consumed_no_effect":
                return self._consume_source_no_effect(state, payload, action, actor_id, "no_eligible_targets")
            return HandlerResult(outcome="rejected", state=state, reason_code="no_eligible_targets")

        try:
            selected_ids = resolve_target_selection(offer, policy, selection)
        except InvalidOperation:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_target_selection")

        if not selected_ids:
            if action.no_target_outcome == "consumed_no_effect":
                return self._consume_source_no_effect(state, payload, action, actor_id, "no_eligible_targets")
            return HandlerResult(outcome="rejected", state=state, reason_code="no_eligible_targets")

        # Complete validation before mutating anything: exact board location,
        # target side, and no duplicates are checked against current state.
        victims: list[tuple[str, str, str]] = []
        try:
            for instance_id in selected_ids:
                owner_id, zone = locate_instance(state, instance_id)
                if zone != "board":
                    raise InvalidOperation("removal target is not on board")
                if cause_id == "sacrifice" and owner_id != actor_id:
                    raise InvalidOperation("sacrifice target must be an ally")
                if cause_id != "sacrifice" and owner_id == actor_id:
                    raise InvalidOperation("removal target must be an enemy")
                row = state["instances"][instance_id]["state"]["current_row"]
                victims.append((instance_id, owner_id, row))
        except (InvalidOperation, KeyError):
            return HandlerResult(outcome="rejected", state=state, reason_code="target_no_longer_eligible")

        # Plan protection for every target before mutating the working copy.
        # Unknown profiles or ambiguous legacy provenance fail the whole action.
        try:
            protection_plan = {
                instance_id: self._find_blocking_protection(
                    state["instances"][instance_id], cause_id, event_sequence_by_id
                )
                for instance_id, _owner_id, _row in victims
            }
        except InvalidOperation:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_protection_state")

        planned_blocked = sum(1 for grant in protection_plan.values() if grant is not None)
        planned_applied = len(victims) - planned_blocked
        planned_outcome = (
            "blocked" if planned_applied == 0 and planned_blocked > 0
            else "partial" if planned_applied > 0 and planned_blocked > 0
            else "applied" if planned_applied > 0
            else "consumed_no_effect"
        )
        planned_source_consumption = (
            (planned_outcome in ("applied", "partial") and action.consume_source_on_success)
            or (planned_outcome == "blocked" and action.consume_source_on_block)
        )
        if planned_source_consumption and not self._source_is_consumable(state, payload.get("source_instance_id"), actor_id):
            return HandlerResult(outcome="rejected", state=state, reason_code="source_not_consumable")

        events: list[dict[str, Any]] = []
        target_results: list[dict[str, Any]] = []
        consumed_grant_ids: list[str] = []
        removed_for_vengeance: list[tuple[str, str, str, str]] = []
        applied = 0
        blocked = 0
        for instance_id, owner_id, original_row in victims:
            instance = state["instances"][instance_id]
            protection = protection_plan[instance_id]
            if protection is not None:
                protection["charges"] -= 1
                grant_id = protection["grant_id"]
                consumed_grant_ids.append(grant_id)
                if protection["charges"] == 0:
                    instance["state"]["protection_grants"].remove(protection)
                event = self._event(
                    kind="unit_removal_blocked",
                    effect_scope="direct",
                    source_effect_id=action.source_effect_id,
                    source_instance_id=payload.get("source_instance_id"),
                    target_instance_ids=[instance_id],
                    caused_by_event_ids=[],
                    payload={"cause_id": cause_id, "protection_grant_id": grant_id},
                )
                events.append(event)
                target_results.append(
                    {
                        "target_instance_id": instance_id,
                        "outcome": "blocked",
                        "protection_grant_id": grant_id,
                        "reason_code": "protection_blocked_removal",
                    }
                )
                blocked += 1
                continue

            transition_instance_zone(state, instance_id, "discard")
            self._expire_board_exit_grants(instance["state"])
            counters = state["players"][owner_id]["counters"]
            if cause_id == "sacrifice":
                counters["sacrifice_count"] += 1
            else:
                counters["board_removal_count"] += 1
            removed_event = self._event(
                kind="unit_removed",
                effect_scope="direct",
                source_effect_id=action.source_effect_id,
                source_instance_id=payload.get("source_instance_id"),
                target_instance_ids=[instance_id],
                caused_by_event_ids=[],
                payload={
                    "cause_id": cause_id,
                    "from_zone": "board",
                    "to_zone": "discard",
                    "affected_player_id": owner_id,
                    "row_at_removal": original_row,
                },
            )
            events.append(removed_event)
            target_results.append({"target_instance_id": instance_id, "outcome": "applied"})
            removed_for_vengeance.append((instance_id, owner_id, original_row, removed_event["event_id"]))
            applied += 1

        # Resolve reactive effects only after all direct target outcomes are
        # finalized. A unit selected for removal by the same multi-target
        # action must not receive Vingança as if it were a survivor.
        for removed_id, owner_id, original_row, removed_event_id in removed_for_vengeance:
            self._apply_vengeance(state, removed_id, owner_id, original_row, removed_event_id, events)

        if applied == 0 and blocked > 0:
            outcome = "blocked"
        elif applied > 0 and blocked > 0:
            outcome = "partial"
        elif applied > 0:
            outcome = "applied"
        else:
            outcome = "consumed_no_effect"
        costs: dict[str, Any] = {}
        if consumed_grant_ids:
            costs["protection_grants_consumed"] = consumed_grant_ids

        should_consume_source = (
            (outcome in ("applied", "partial") and action.consume_source_on_success)
            or (outcome == "blocked" and action.consume_source_on_block)
        )
        if should_consume_source:
            source_event = self._consume_source(
                state,
                payload.get("source_instance_id"),
                actor_id,
                action,
                reason=f"action_{outcome}",
                caused_by_event_ids=[event["event_id"] for event in events if event["kind"] in ("unit_removed", "unit_removal_blocked")],
            )
            if source_event is None:
                return HandlerResult(outcome="rejected", state=state, reason_code="source_not_consumable")
            events.append(source_event)
            costs["source_consumed"] = True

        return HandlerResult(
            outcome=outcome,
            state=state,
            target_results=target_results,
            costs=costs,
            events=events,
        )

    def _consume_source_no_effect(
        self,
        state: dict[str, Any],
        payload: dict[str, Any],
        action: ActionDefinition,
        actor_id: str,
        reason_code: str,
    ) -> HandlerResult:
        if not action.consume_source_on_no_target:
            return HandlerResult(outcome="rejected", state=state, reason_code="no_target_policy_requires_consumable_source")
        source_id = payload.get("source_instance_id")
        if source_id is None:
            return HandlerResult(outcome="rejected", state=state, reason_code="no_source_to_consume")
        event = self._consume_source(
            state,
            source_id,
            actor_id,
            action,
            reason=reason_code,
            caused_by_event_ids=[],
        )
        if event is None:
            return HandlerResult(outcome="rejected", state=state, reason_code="source_not_consumable")
        return HandlerResult(
            outcome="consumed_no_effect",
            state=state,
            costs={"source_consumed": True},
            events=[event],
            reason_code=reason_code,
        )

    @staticmethod
    def _source_is_consumable(state: dict[str, Any], source_id: str | None, actor_id: str) -> bool:
        if source_id is None or source_id not in state.get("instances", {}):
            return False
        try:
            owner_id, zone = locate_instance(state, source_id)
        except (InvalidOperation, KeyError):
            return False
        return owner_id == actor_id and zone == "hand"

    def _consume_source(
        self,
        state: dict[str, Any],
        source_id: str | None,
        actor_id: str,
        action: ActionDefinition,
        *,
        reason: str,
        caused_by_event_ids: list[str],
    ) -> dict[str, Any] | None:
        if source_id is None or source_id not in state["instances"]:
            return None
        try:
            owner_id, zone = locate_instance(state, source_id)
            if owner_id != actor_id or zone != "hand":
                return None
            transition_instance_zone(state, source_id, "discard")
        except (InvalidOperation, KeyError):
            return None
        return self._event(
            kind="action_source_consumed",
            effect_scope="direct",
            source_effect_id=action.source_effect_id,
            source_instance_id=source_id,
            target_instance_ids=[source_id],
            caused_by_event_ids=caused_by_event_ids,
            payload={"reason": reason, "from_zone": "hand", "to_zone": "discard"},
        )

    def _resolve_move(
        self,
        state: dict[str, Any],
        request: dict[str, Any],
        action: ActionDefinition,
        actor_id: str,
    ) -> HandlerResult:
        payload = request["payload"]
        if not action.target_policy_id or action.target_policy_id not in self.target_policies:
            return HandlerResult(outcome="rejected", state=state, reason_code="missing_target_policy")
        policy = self.target_policies[action.target_policy_id]
        try:
            offer = build_target_offer(
                state,
                actor_player_id=actor_id,
                policy=policy,
                source_instance_id=payload.get("source_instance_id"),
                selected_row=payload.get("selected_row"),
                metric_resolver=self.metric_resolver,
            )
            selected = resolve_target_selection(offer, policy, payload.get("selection", {}))
        except InvalidOperation:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_target_selection")
        if len(selected) != 1:
            return HandlerResult(outcome="rejected", state=state, reason_code="move_requires_one_target")
        instance_id = selected[0]
        target_row = payload.get("target_row")
        if not isinstance(target_row, str) or target_row not in action.allowed_target_rows:
            return HandlerResult(outcome="rejected", state=state, reason_code="target_row_not_allowed_by_action")
        owner_id, zone = locate_instance(state, instance_id)
        if owner_id != actor_id or zone != "board":
            return HandlerResult(outcome="rejected", state=state, reason_code="move_target_not_owned_on_board")
        current_row = state["instances"][instance_id]["state"].get("current_row")
        if target_row == current_row:
            return HandlerResult(
                outcome="rejected",
                state=state,
                target_results=[{"target_instance_id": instance_id, "outcome": "skipped", "reason_code": "already_in_target_row"}],
                reason_code="already_in_target_row",
            )
        try:
            movement = move_instance_row(state, instance_id, target_row)
        except InvalidOperation:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_target_row")
        event = self._event(
            kind="unit_moved",
            effect_scope="direct",
            source_effect_id=action.source_effect_id,
            source_instance_id=payload.get("source_instance_id"),
            target_instance_ids=[instance_id],
            caused_by_event_ids=[],
            payload=movement,
        )
        return HandlerResult(
            outcome="applied",
            state=state,
            target_results=[{"target_instance_id": instance_id, "outcome": "applied"}],
            events=[event],
        )

    def _resolve_bonus(
        self,
        state: dict[str, Any],
        request: dict[str, Any],
        action: ActionDefinition,
        actor_id: str,
    ) -> HandlerResult:
        payload = request["payload"]
        # Effect magnitude, duration and clamp policy are release-bound server
        # configuration. A client request may choose targets, never effect params.
        if any(key in payload for key in ("amount", "expires_on", "clamp_policy_id")):
            return HandlerResult(outcome="rejected", state=state, reason_code="client_supplied_effect_parameters")
        amount = action.bonus_amount
        expires_on = action.bonus_expires_on
        clamp_policy_id = action.bonus_clamp_policy_id
        if not action.target_policy_id or action.target_policy_id not in self.target_policies:
            return HandlerResult(outcome="rejected", state=state, reason_code="missing_target_policy")
        policy = self.target_policies[action.target_policy_id]
        try:
            offer = build_target_offer(
                state,
                actor_player_id=actor_id,
                policy=policy,
                source_instance_id=payload.get("source_instance_id"),
                selected_row=payload.get("selected_row"),
                metric_resolver=self.metric_resolver,
            )
            target_ids = resolve_target_selection(offer, policy, payload.get("selection", {}))
        except InvalidOperation:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_target_selection")
        if not target_ids:
            return HandlerResult(outcome="rejected", state=state, reason_code="no_eligible_targets")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount == 0:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_bonus_amount")
        if expires_on not in ("round_close", "board_exit", "permanent_instance"):
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_bonus_expiration")
        if not isinstance(clamp_policy_id, str) or not clamp_policy_id:
            return HandlerResult(outcome="rejected", state=state, reason_code="missing_clamp_policy")
        try:
            targets = []
            for instance_id in target_ids:
                owner_id, zone = locate_instance(state, instance_id)
                if owner_id != actor_id or zone != "board":
                    raise InvalidOperation("bonus target must be an owned board instance")
                targets.append(instance_id)
        except (InvalidOperation, KeyError):
            return HandlerResult(outcome="rejected", state=state, reason_code="target_no_longer_eligible")

        event_id = str(uuid.uuid4())
        source_id = payload.get("source_instance_id")
        for instance_id in targets:
            state["instances"][instance_id]["state"]["bonus_grants"].append(
                {
                    "grant_id": str(uuid.uuid4()),
                    "amount": amount,
                    "source_effect_id": action.source_effect_id,
                    "source_instance_id": source_id,
                    "applied_event_id": event_id,
                    "expires_on": expires_on,
                    "clamp_policy_id": clamp_policy_id,
                }
            )
        event = self._event(
            kind="bonus_grant_applied",
            effect_scope="direct",
            source_effect_id=action.source_effect_id,
            source_instance_id=source_id,
            target_instance_ids=targets,
            caused_by_event_ids=[],
            payload={
                "amount": amount,
                "expires_on": expires_on,
                "clamp_policy_id": clamp_policy_id,
            },
            event_id=event_id,
        )
        return HandlerResult(
            outcome="applied",
            state=state,
            target_results=[{"target_instance_id": item, "outcome": "applied"} for item in targets],
            events=[event],
        )

    def _resolve_protection_grant(
        self,
        state: dict[str, Any],
        request: dict[str, Any],
        action: ActionDefinition,
        actor_id: str,
    ) -> HandlerResult:
        payload = request["payload"]
        if any(key in payload for key in ("profile_id", "charges", "expires_on")):
            return HandlerResult(outcome="rejected", state=state, reason_code="client_supplied_protection_parameters")
        if not action.target_policy_id or action.target_policy_id not in self.target_policies:
            return HandlerResult(outcome="rejected", state=state, reason_code="missing_target_policy")
        policy = self.target_policies[action.target_policy_id]
        try:
            offer = build_target_offer(
                state,
                actor_player_id=actor_id,
                policy=policy,
                source_instance_id=payload.get("source_instance_id"),
                selected_row=payload.get("selected_row"),
                metric_resolver=self.metric_resolver,
            )
            target_ids = resolve_target_selection(offer, policy, payload.get("selection", {}))
        except InvalidOperation:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_target_selection")
        if not target_ids:
            return HandlerResult(outcome="rejected", state=state, reason_code="no_eligible_targets")
        profile_id = action.protection_profile_id
        if profile_id not in self.protection_profiles:
            return HandlerResult(outcome="rejected", state=state, reason_code="unknown_protection_profile")
        targets: list[str] = []
        try:
            for instance_id in target_ids:
                _owner_id, zone = locate_instance(state, instance_id)
                if zone != "board":
                    raise InvalidOperation("protection target must be on board")
                targets.append(instance_id)
        except (InvalidOperation, KeyError):
            return HandlerResult(outcome="rejected", state=state, reason_code="target_no_longer_eligible")

        event_id = str(uuid.uuid4())
        source_id = payload.get("source_instance_id")
        grant_ids: dict[str, str] = {}
        for instance_id in targets:
            grant_id = str(uuid.uuid4())
            grant_ids[instance_id] = grant_id
            state["instances"][instance_id]["state"]["protection_grants"].append(
                {
                    "grant_id": grant_id,
                    "profile_id": profile_id,
                    "charges": action.protection_charges,
                    "source_effect_id": action.source_effect_id,
                    "source_instance_id": source_id,
                    "applied_event_id": event_id,
                    "expires_on": action.protection_expires_on,
                }
            )
        event = self._event(
            kind="protection_grant_applied",
            effect_scope="direct",
            source_effect_id=action.source_effect_id,
            source_instance_id=source_id,
            target_instance_ids=targets,
            caused_by_event_ids=[],
            payload={
                "profile_id": profile_id,
                "charges": action.protection_charges,
                "expires_on": action.protection_expires_on,
                "grant_ids_by_target": grant_ids,
            },
            event_id=event_id,
        )
        return HandlerResult(
            outcome="applied",
            state=state,
            target_results=[{"target_instance_id": item, "outcome": "applied"} for item in targets],
            events=[event],
        )

    def _find_blocking_protection(
        self,
        instance: dict[str, Any],
        cause_id: str,
        event_sequence_by_id: dict[str, int],
    ) -> dict[str, Any] | None:
        if cause_id == "sacrifice":
            return None
        candidates = []
        for grant in instance["state"].get("protection_grants", []):
            charges = grant.get("charges")
            if not isinstance(charges, int) or isinstance(charges, bool) or charges <= 0:
                continue
            profile_id = grant.get("profile_id")
            profile = self.protection_profiles.get(profile_id)
            if profile is None:
                raise InvalidOperation(f"unknown protection profile: {profile_id}")
            if cause_id in profile.blocked_causes:
                grant_id = grant.get("grant_id")
                applied_event_id = grant.get("applied_event_id")
                if not is_uuid4(grant_id) or not is_uuid4(applied_event_id):
                    raise InvalidOperation("protection grant requires UUIDv4 grant_id and applied_event_id")
                candidates.append(grant)
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        # DSEL-DEC-009: earliest applied event wins; grant UUID is the tie-break.
        missing = [
            grant["applied_event_id"]
            for grant in candidates
            if grant["applied_event_id"] not in event_sequence_by_id
        ]
        if missing:
            raise InvalidOperation(
                "cannot resolve protection priority: applied_event_id is missing from the event journal"
            )
        return sorted(
            candidates,
            key=lambda item: (event_sequence_by_id[item["applied_event_id"]], item["grant_id"]),
        )[0]

    def _apply_vengeance(
        self,
        state: dict[str, Any],
        removed_instance_id: str,
        owner_id: str,
        row_at_removal: str,
        caused_by_event_id: str,
        events: list[dict[str, Any]],
    ) -> None:
        removed = state["instances"][removed_instance_id]
        snapshot = removed["definition_snapshot"]
        if snapshot.get("effect_id") != "effect.vengeance_on_removal":
            return
        params = snapshot.get("effect_params", {})
        amount = params.get("bonus_delta") if isinstance(params, dict) else None
        if not isinstance(amount, int) or isinstance(amount, bool) or amount == 0:
            raise InvalidOperation("Vingança requires an explicit non-zero integer effect_params.bonus_delta")
        if not self.vengeance_clamp_policy_id:
            raise InvalidOperation("Vingança requires a release-bound clamp_policy_id")
        survivors = [
            instance_id
            for instance_id in state["players"][owner_id]["zones"]["board"]
            if state["instances"][instance_id]["state"].get("current_row") == row_at_removal
        ]
        event_id = str(uuid.uuid4())
        for survivor_id in survivors:
            state["instances"][survivor_id]["state"]["bonus_grants"].append(
                {
                    "grant_id": str(uuid.uuid4()),
                    "amount": amount,
                    "source_effect_id": "effect.vengeance_on_removal",
                    "source_instance_id": removed_instance_id,
                    "applied_event_id": event_id,
                    "expires_on": "round_close",
                    "clamp_policy_id": self.vengeance_clamp_policy_id,
                }
            )
        if survivors:
            events.append(
                self._event(
                    kind="vengeance_bonus_applied",
                    effect_scope="reactive",
                    source_effect_id="effect.vengeance_on_removal",
                    source_instance_id=removed_instance_id,
                    target_instance_ids=survivors,
                    caused_by_event_ids=[caused_by_event_id],
                    payload={
                        "amount": amount,
                        "expires_on": "round_close",
                        "clamp_policy_id": self.vengeance_clamp_policy_id,
                        "trigger_cause": "successful_removal",
                    },
                    event_id=event_id,
                )
            )
        else:
            events.append(
                self._event(
                    kind="vengeance_triggered_no_targets",
                    effect_scope="reactive",
                    source_effect_id="effect.vengeance_on_removal",
                    source_instance_id=removed_instance_id,
                    target_instance_ids=[],
                    caused_by_event_ids=[caused_by_event_id],
                    payload={"reason_code": "no_surviving_allies_in_original_row", "trigger_cause": "successful_removal"},
                    event_id=event_id,
                )
            )

    @staticmethod
    def _expire_board_exit_grants(runtime: dict[str, Any]) -> None:
        for key in ("bonus_grants", "protection_grants", "status_applications", "weather_resistance_modifiers"):
            runtime[key] = [grant for grant in runtime.get(key, []) if grant.get("expires_on") != "board_exit"]

    @staticmethod
    def _event(
        *,
        kind: str,
        effect_scope: str,
        source_effect_id: str | None,
        source_instance_id: str | None,
        target_instance_ids: list[str],
        caused_by_event_ids: list[str],
        payload: dict[str, Any],
        event_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "event_id": event_id or str(uuid.uuid4()),
            "kind": kind,
            "effect_scope": effect_scope,
            "source_effect_id": source_effect_id,
            "source_instance_id": source_instance_id,
            "target_instance_ids": target_instance_ids,
            "caused_by_event_ids": caused_by_event_ids,
            "payload": payload,
        }

