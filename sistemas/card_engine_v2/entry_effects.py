"""Server-side alpha resolver for the supported unit on-play effect families.

This module deliberately implements a closed set of release-pinned effects.
Unknown IDs are not guessed or mapped by display text.
"""
from __future__ import annotations

import copy
import uuid
from typing import Any

from .errors import InvalidOperation
from .power import ALPHA_RAW_GRANT_POLICY, bonus_total, effective_power

SUPPORTED_ENTRY_EFFECTS = frozenset(
    {
        "effect.discard_advantage_power",
        "effect.ruin_omen",
        "effect.enemy_bonus_reduction",
        "effect.cross_row_presence_power",
        "effect.weather_ward_support",
        "effect.weather_affinity_power",
        "effect.enemy_positive_bonus_power",
        "effect.comeback_power",
        "effect.solitary_row_power",
        "effect.ahead_power",
        "effect.sequence_power",
        "effect.arcane_hunter_power",
    }
)


def _event(
    kind: str,
    *,
    effect_id: str,
    source_instance_id: str,
    target_instance_ids: list[str],
    caused_by_event_ids: list[str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "kind": kind,
        "effect_scope": "direct",
        "source_effect_id": effect_id,
        "source_instance_id": source_instance_id,
        "target_instance_ids": target_instance_ids,
        "caused_by_event_ids": caused_by_event_ids,
        "payload": payload,
    }


def _player_and_opponent(state: dict[str, Any], player_id: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    player = state["players"][player_id]
    opponents = [(pid, data) for pid, data in state["players"].items() if pid != player_id]
    if len(opponents) != 1:
        raise InvalidOperation("alpha entry effects require exactly one opponent")
    opponent_id, opponent = opponents[0]
    return player, opponent_id, opponent


def _side_score(state: dict[str, Any], player: dict[str, Any], weather: dict[str, int]) -> int:
    return sum(
        effective_power(state, state["instances"][instance_id], weather)
        for instance_id in player["zones"]["board"]
    )


def _ordered_by_power(
    state: dict[str, Any], player: dict[str, Any], weather: dict[str, int], *, descending: bool
) -> list[str]:
    ids = list(player["zones"]["board"])
    order = {instance_id: index for index, instance_id in enumerate(ids)}
    return sorted(
        ids,
        key=lambda instance_id: (
            -effective_power(state, state["instances"][instance_id], weather)
            if descending
            else effective_power(state, state["instances"][instance_id], weather),
            order[instance_id],
        ),
    )


def _add_bonus_grant(
    state: dict[str, Any],
    *,
    target_id: str,
    amount: int,
    effect_id: str,
    source_id: str,
    event_id: str,
    expires_on: str = "permanent_instance",
) -> dict[str, Any]:
    grant = {
        "grant_id": str(uuid.uuid4()),
        "amount": amount,
        "source_effect_id": effect_id,
        "source_instance_id": source_id,
        "applied_event_id": event_id,
        "expires_on": expires_on,
        "clamp_policy_id": ALPHA_RAW_GRANT_POLICY,
    }
    state["instances"][target_id]["state"]["bonus_grants"].append(grant)
    return grant


def _add_weather_resistance_modifier(
    state: dict[str, Any],
    *,
    target_id: str,
    amount: int,
    effect_id: str,
    source_id: str,
    event_id: str,
) -> dict[str, Any]:
    modifier = {
        "modifier_id": str(uuid.uuid4()),
        "amount": amount,
        "source_effect_id": effect_id,
        "source_instance_id": source_id,
        "applied_event_id": event_id,
        "expires_on": "board_exit",
    }
    state["instances"][target_id]["state"]["weather_resistance_modifiers"].append(modifier)
    return modifier


def resolve_unit_entry_effect(
    state: dict[str, Any],
    runtime: dict[str, Any],
    *,
    instance_id: str,
    player_id: str,
    previous_own_last_row: str | None,
    previous_opponent_last_row: str | None,
    played_event_id: str,
) -> dict[str, Any] | None:
    """Resolve one explicitly supported entry effect after the unit enters board.

    The caller invokes this inside the repository's operation handler, after
    `unit_played` is created and before the transaction is committed.
    """
    instance = state["instances"][instance_id]
    snapshot = instance["definition_snapshot"]
    effect_id = snapshot.get("effect_id")
    if effect_id not in SUPPORTED_ENTRY_EFFECTS:
        return None

    params = copy.deepcopy(snapshot.get("effect_params") or {})
    row = instance["state"].get("current_row")
    if row not in ("melee", "ranged", "siege"):
        raise InvalidOperation("on-play unit effect requires a valid current_row")
    player, opponent_id, opponent = _player_and_opponent(state, player_id)
    allies = list(player["zones"]["board"])
    enemies = list(opponent["zones"]["board"])
    weather = runtime["weather_by_row"]
    own_score = _side_score(state, player, weather)
    opponent_score = _side_score(state, opponent, weather)
    target_ids: list[str] = []
    grant_specs: list[tuple[str, int, str]] = []
    resistance_specs: list[tuple[str, int]] = []
    details: dict[str, Any] = {"condition_met": False}

    def self_bonus(amount: int) -> None:
        if amount:
            grant_specs.append((instance_id, amount, "permanent_instance"))

    if effect_id == "effect.discard_advantage_power":
        own_discard = len(player["zones"]["discard"])
        if own_discard > 0:
            amount = int(params.get("discard_bonus", 2))
            self_bonus(amount)
            details = {"condition_met": True, "condition": "own_discard_nonempty", "discard_count": own_discard}
        elif len(enemies) > len(allies):
            amount = int(params.get("fallback_bonus", 1))
            self_bonus(amount)
            details = {"condition_met": True, "condition": "opponent_has_more_units", "own_units": len(allies), "enemy_units": len(enemies)}
        else:
            details = {"condition_met": False, "condition": "no_discard_and_no_enemy_unit_advantage"}

    elif effect_id == "effect.ruin_omen":
        ordered_enemies = _ordered_by_power(state, opponent, weather, descending=True)
        if ordered_enemies:
            target_id = ordered_enemies[0]
            current = bonus_total(state["instances"][target_id])
            floor = int(params.get("enemy_bonus_floor", -2))
            amount = int(params.get("enemy_bonus_reduction", 1))
            delta = max(floor, current - amount) - current
            if delta:
                grant_specs.append((target_id, delta, "permanent_instance"))
                target_ids.append(target_id)
        behind = own_score < opponent_score
        if behind:
            self_bonus(int(params.get("self_bonus_if_behind", 1)))
        details = {"condition_met": bool(grant_specs), "own_score_before_effect": own_score, "opponent_score_before_effect": opponent_score, "enemy_target": target_id if ordered_enemies else None, "behind": behind}

    elif effect_id == "effect.enemy_bonus_reduction":
        scope = params.get("target_scope")
        if scope == "strongest_enemy":
            candidates = _ordered_by_power(state, opponent, weather, descending=True)[:1]
        elif scope == "chosen_enemy_row":
            candidates = [enemy_id for enemy_id in enemies if state["instances"][enemy_id]["state"].get("current_row") == row]
        else:
            raise InvalidOperation(f"unsupported enemy_bonus_reduction target_scope: {scope!r}")
        amount = int(params.get("amount", 1))
        floor = int(params.get("floor", -2))
        changed: list[str] = []
        for target_id in candidates:
            current = bonus_total(state["instances"][target_id])
            delta = max(floor, current - amount) - current
            if delta:
                grant_specs.append((target_id, delta, "permanent_instance"))
                target_ids.append(target_id)
                changed.append(target_id)
        details = {"condition_met": bool(changed), "target_scope": scope, "affected_targets": changed, "amount": amount, "floor": floor}

    elif effect_id == "effect.cross_row_presence_power":
        other_rows = sorted(
            {state["instances"][ally_id]["state"].get("current_row") for ally_id in allies if ally_id != instance_id and state["instances"][ally_id]["state"].get("current_row") != row}
        )
        max_bonus = int(params.get("max_bonus", 1))
        per_row = int(params.get("bonus_per_row", 1))
        amount = min(max_bonus, len(other_rows) * per_row)
        self_bonus(amount)
        details = {"condition_met": amount > 0, "distinct_other_rows": other_rows, "bonus": amount}

    elif effect_id == "effect.weather_ward_support":
        resistance = int(params.get("weather_resistance", 1))
        if resistance:
            resistance_specs.append((instance_id, resistance))
            target_ids.append(instance_id)
        same_row_allies = [
            ally_id for ally_id in allies
            if ally_id != instance_id and state["instances"][ally_id]["state"].get("current_row") == row
        ]
        selected_ally = None
        if same_row_allies:
            order = {ally_id: index for index, ally_id in enumerate(allies)}
            selected_ally = min(
                same_row_allies,
                key=lambda ally_id: (effective_power(state, state["instances"][ally_id], weather), order[ally_id]),
            )
            ally_bonus = int(params.get("ally_bonus", 1))
            if ally_bonus:
                grant_specs.append((selected_ally, ally_bonus, "permanent_instance"))
                target_ids.append(selected_ally)
        details = {"condition_met": bool(resistance or selected_ally), "weather_resistance": resistance, "ally_target": selected_ally}

    elif effect_id == "effect.weather_affinity_power":
        scope = params.get("weather_scope", "own_row_active")
        weather_active = any(int(value or 0) > 0 for value in weather.values()) if scope == "any_row_active" else int(weather.get(row, 0)) > 0
        amount = int(params.get("bonus", 2)) if weather_active else 0
        self_bonus(amount)
        details = {"condition_met": weather_active, "weather_scope": scope, "bonus": amount}

    elif effect_id == "effect.enemy_positive_bonus_power":
        positive_targets = [enemy_id for enemy_id in enemies if bonus_total(state["instances"][enemy_id]) > 0]
        amount = int(params.get("bonus", 2)) if positive_targets else 0
        self_bonus(amount)
        target_ids.extend(positive_targets)
        details = {"condition_met": bool(positive_targets), "positive_bonus_enemy_ids": positive_targets, "bonus": amount}

    elif effect_id == "effect.comeback_power":
        condition = own_score < opponent_score
        amount = int(params.get("bonus", 2)) if condition else 0
        self_bonus(amount)
        details = {"condition_met": condition, "own_score_before_effect": own_score, "opponent_score_before_effect": opponent_score, "bonus": amount}

    elif effect_id == "effect.solitary_row_power":
        same_row_allies = [ally_id for ally_id in allies if ally_id != instance_id and state["instances"][ally_id]["state"].get("current_row") == row]
        condition = not same_row_allies
        amount = int(params.get("bonus", 2)) if condition else 0
        self_bonus(amount)
        details = {"condition_met": condition, "same_row_allies": same_row_allies, "bonus": amount}

    elif effect_id == "effect.ahead_power":
        condition = own_score > opponent_score
        amount = int(params.get("bonus", 1)) if condition else 0
        self_bonus(amount)
        details = {"condition_met": condition, "own_score_before_effect": own_score, "opponent_score_before_effect": opponent_score, "bonus": amount}

    elif effect_id == "effect.sequence_power":
        reference = params.get("reference_side")
        relation = params.get("row_relation")
        reference_row = previous_opponent_last_row if reference == "opponent" else previous_own_last_row if reference == "own" else None
        condition = bool(params.get("requires_previous_play", True)) and reference_row is not None and (
            (relation == "same" and reference_row == row) or (relation == "different" and reference_row != row)
        )
        amount = int(params.get("bonus", 1)) if condition else 0
        self_bonus(amount)
        details = {"condition_met": condition, "reference_side": reference, "reference_row": reference_row, "played_row": row, "row_relation": relation, "bonus": amount}

    elif effect_id == "effect.arcane_hunter_power":
        dark_moon_present = any(state["instances"][enemy_id]["definition_snapshot"].get("faction_id") == "dark_moon" for enemy_id in enemies)
        positive_bonus_present = any(bonus_total(state["instances"][enemy_id]) > 0 for enemy_id in enemies)
        condition = dark_moon_present or positive_bonus_present
        amount = int(params.get("bonus", 1)) if condition else 0
        self_bonus(amount)
        details = {"condition_met": condition, "dark_moon_enemy_present": dark_moon_present, "positive_enemy_bonus_present": positive_bonus_present, "bonus": amount}

    elif effect_id == "effect.ranged_row_power":
        condition = row == "ranged"
        amount = int(params.get("bonus", 1)) if condition else 0
        self_bonus(amount)
        details = {"condition_met": condition, "played_row": row, "bonus": amount}

    else:  # Defensive: a supported set mismatch must never silently no-op.
        raise InvalidOperation(f"entry effect handler missing for {effect_id}")

    if not grant_specs and not resistance_specs:
        return _event(
            "unit_entry_effect_no_effect",
            effect_id=effect_id,
            source_instance_id=instance_id,
            target_instance_ids=target_ids,
            caused_by_event_ids=[played_event_id],
            payload={"card_id": snapshot["card_id"], "details": details},
        )

    all_targets = list(dict.fromkeys([target for target, _amount, _expiry in grant_specs] + [target for target, _amount in resistance_specs] + target_ids))
    event = _event(
        "unit_entry_effect_applied",
        effect_id=effect_id,
        source_instance_id=instance_id,
        target_instance_ids=all_targets,
        caused_by_event_ids=[played_event_id],
        payload={
            "card_id": snapshot["card_id"],
            "details": details,
            "grants": [{"target_instance_id": target, "amount": amount, "expires_on": expiry} for target, amount, expiry in grant_specs],
            "weather_resistance_modifiers": [{"target_instance_id": target, "amount": amount, "expires_on": "board_exit"} for target, amount in resistance_specs],
            "rarity_mechanical": False,
        },
    )
    event_id = event["event_id"]
    for target, amount, expiry in grant_specs:
        _add_bonus_grant(state, target_id=target, amount=amount, effect_id=effect_id, source_id=instance_id, event_id=event_id, expires_on=expiry)
    for target, amount in resistance_specs:
        _add_weather_resistance_modifier(state, target_id=target, amount=amount, effect_id=effect_id, source_id=instance_id, event_id=event_id)
    return event
