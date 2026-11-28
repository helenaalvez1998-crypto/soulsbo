"""Alpha effective-power projection for the approved CardInstance v0.7 rules.

This is bound only to the explicitly marked alpha balance release. It does not
read rarity and refuses unsupported clamp policies or malformed status grants.
"""

from __future__ import annotations

from typing import Any

from .errors import InvalidOperation

CONTROL_STATUS_IDS = {"status.frost", "status.scarlet_rot", "status.madness"}
VALID_STATUS_IDS = CONTROL_STATUS_IDS | {"status.bleeding"}
ALPHA_RAW_GRANT_POLICY = "balance.alpha.raw_grants.v1"


def bonus_total(instance: dict[str, Any]) -> int:
    grants = instance.get("state", {}).get("bonus_grants", [])
    total = 0
    for grant in grants:
        amount = grant.get("amount")
        policy_id = grant.get("clamp_policy_id")
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise InvalidOperation("bonus grant amount must be an integer")
        if policy_id != ALPHA_RAW_GRANT_POLICY:
            raise InvalidOperation(f"unsupported alpha bonus clamp policy: {policy_id}")
        total += amount
    return total


def status_counts(instance: dict[str, Any]) -> dict[str, int]:
    counts = {status_id: 0 for status_id in VALID_STATUS_IDS}
    for application in instance.get("state", {}).get("status_applications", []):
        status_id = application.get("status_id")
        if status_id not in counts:
            raise InvalidOperation(f"unsupported alpha status application: {status_id}")
        counts[status_id] += 1
    for status_id, amount in counts.items():
        if amount > 2:
            raise InvalidOperation(f"status {status_id} exceeds the approved two-mark maximum")
    return counts


def effective_weather_resistance(instance: dict[str, Any]) -> int:
    base = instance.get("definition_snapshot", {}).get("intrinsic_weather_resistance", 0)
    if not isinstance(base, int) or isinstance(base, bool) or base < 0:
        raise InvalidOperation("intrinsic weather resistance must be a non-negative integer")
    modifiers = instance.get("state", {}).get("weather_resistance_modifiers", [])
    total = base
    for modifier in modifiers:
        amount = modifier.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise InvalidOperation("weather resistance modifier must be an integer")
        total += amount
    return max(0, total)



def base_power(instance: dict[str, Any]) -> int | None:
    """Return frozen per-exemplar power when present, otherwise catalog power.

    The exemplar's rarity classification is deliberately never consulted.
    """
    exemplar_snapshot = instance.get("exemplar_snapshot")
    if isinstance(exemplar_snapshot, dict) and exemplar_snapshot.get("power_base") is not None:
        value = exemplar_snapshot.get("power_base")
    else:
        value = instance.get("definition_snapshot", {}).get("power_base")
    if not isinstance(value, int) or isinstance(value, bool):
        return None
    return value

def effective_power(
    state: dict[str, Any],
    instance: dict[str, Any],
    weather_by_row: dict[str, int],
) -> int:
    snapshot = instance.get("definition_snapshot", {})
    base = base_power(instance)
    row = instance.get("state", {}).get("current_row")
    if not isinstance(base, int) or isinstance(base, bool):
        raise InvalidOperation("effective power requires a unit with integer power_base")
    if row not in ("melee", "ranged", "siege"):
        raise InvalidOperation("effective power requires a unit on a valid board row")
    weather = weather_by_row.get(row, 0)
    if not isinstance(weather, int) or isinstance(weather, bool) or weather < 0:
        raise InvalidOperation("weather penalty must be a non-negative integer")
    resistance = effective_weather_resistance(instance)
    weather_penalty = max(0, weather - resistance)
    counts = status_counts(instance)
    control_penalty = min(3, sum(counts[status_id] for status_id in CONTROL_STATUS_IDS))
    # Bleeding has no direct power penalty; its two-mark transition is applied
    # by the status resolver, not by this read-only projection.
    return max(1, base + bonus_total(instance) - weather_penalty - control_penalty)


def metric_resolver_for_weather(weather_by_row: dict[str, int]):
    """Return a targeting callback bound to a detached weather projection."""

    def resolve(state: dict[str, Any], instance: dict[str, Any], metric: str) -> int | None:
        if metric == "effective_power":
            return effective_power(state, instance, weather_by_row)
        if metric == "base_power":
            return base_power(instance)
        if metric == "bonus":
            return bonus_total(instance)
        return None

    return resolve
