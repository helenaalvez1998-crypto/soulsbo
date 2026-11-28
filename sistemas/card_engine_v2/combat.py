"""Round-combat resolution for the isolated Card Engine v2 alpha.

The current Soulsbo rules define combat as a per-row difference between the
opponents' effective total power. Damage is applied to player life; this module
does not invent per-unit attack, armor, or hit-point attributes.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .errors import InvalidOperation
from .power import effective_power
from .validation import ROWS


DEFAULT_STARTING_LIFE = 20


def _non_negative_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvalidOperation(f"{field_name} must be a non-negative integer")
    return value


def resolve_row_combat(
    state: dict[str, Any],
    player_ids: Sequence[str],
    weather_by_row: Mapping[str, int],
) -> dict[str, Any]:
    """Resolve simultaneous row power comparisons for exactly two players.

    For each row, the player with more effective power deals the positive
    difference as damage to the opponent. Equal rows deal no damage. Effective
    power already includes bonuses, weather, weather resistance, and control
    statuses according to the pinned alpha balance rules.
    """
    if len(player_ids) != 2 or len(set(player_ids)) != 2:
        raise InvalidOperation("row combat requires exactly two distinct players")
    if any(player_id not in state.get("players", {}) for player_id in player_ids):
        raise InvalidOperation("row combat players must belong to the match")
    if set(weather_by_row) != set(ROWS):
        raise InvalidOperation("weather_by_row must define exactly the three rows")
    for row, penalty in weather_by_row.items():
        _non_negative_int(penalty, f"weather_by_row[{row}]")

    row_power_by_player: dict[str, dict[str, int]] = {
        player_id: {row: 0 for row in ROWS} for player_id in player_ids
    }
    for player_id in player_ids:
        for instance_id in state["players"][player_id]["zones"]["board"]:
            instance = state["instances"][instance_id]
            row = instance["state"].get("current_row")
            if row not in ROWS:
                raise InvalidOperation(f"board instance {instance_id} has an invalid current_row")
            row_power_by_player[player_id][row] += effective_power(
                state, instance, dict(weather_by_row)
            )

    damage_by_player = {player_id: 0 for player_id in player_ids}
    row_results: list[dict[str, Any]] = []
    first_player_id, second_player_id = player_ids
    for row in ROWS:
        first_power = row_power_by_player[first_player_id][row]
        second_power = row_power_by_player[second_player_id][row]
        row_damage = {first_player_id: 0, second_player_id: 0}
        winner_player_id: str | None = None
        if first_power > second_power:
            winner_player_id = first_player_id
            row_damage[second_player_id] = first_power - second_power
        elif second_power > first_power:
            winner_player_id = second_player_id
            row_damage[first_player_id] = second_power - first_power

        for player_id, amount in row_damage.items():
            damage_by_player[player_id] += amount
        row_results.append(
            {
                "row": row,
                "power_by_player": {
                    first_player_id: first_power,
                    second_player_id: second_power,
                },
                "damage_by_player": row_damage,
                "winner_player_id": winner_player_id,
            }
        )

    return {
        "row_power_by_player": row_power_by_player,
        "damage_by_player": damage_by_player,
        "rows": row_results,
    }


def apply_life_damage(
    life_by_player: Mapping[str, int],
    damage_by_player: Mapping[str, int],
) -> dict[str, Any]:
    """Return a detached, clamped life update and its auditable breakdown."""
    if (
        not isinstance(life_by_player, Mapping)
        or not isinstance(damage_by_player, Mapping)
        or not life_by_player
        or set(life_by_player) != set(damage_by_player)
    ):
        raise InvalidOperation("life and damage maps must cover the same players")

    updated_life: dict[str, int] = {}
    life_changes: dict[str, dict[str, int]] = {}
    defeated: list[str] = []
    for player_id, current_life in life_by_player.items():
        current = _non_negative_int(current_life, f"life_by_player[{player_id}]")
        damage = _non_negative_int(damage_by_player[player_id], f"damage_by_player[{player_id}]")
        remaining = max(0, current - damage)
        updated_life[player_id] = remaining
        life_changes[player_id] = {
            "life_before": current,
            "damage_taken": damage,
            "life_after": remaining,
        }
        if remaining == 0:
            defeated.append(player_id)

    return {
        "life_by_player": updated_life,
        "life_changes": life_changes,
        "defeated_player_ids": defeated,
    }


__all__ = [
    "DEFAULT_STARTING_LIFE",
    "apply_life_damage",
    "resolve_row_combat",
]
