"""Identity-safe zone and row transitions for CardInstance v7.

These helpers move only the physical instance and its zone/row metadata. They
do not silently clean bonuses, shields, statuses, or resistance modifiers;
that normalization must be supplied by the effect-specific transition policy.
"""

from __future__ import annotations

from typing import Any

from .errors import InvalidMatchState, InvalidOperation
from .validation import ROWS, ZONES, validate_match_state


def locate_instance(state: dict[str, Any], instance_id: str) -> tuple[str, str]:
    """Return (owner_player_id, zone) for exactly one occurrence."""
    found: list[tuple[str, str]] = []
    for player_id, player in state.get("players", {}).items():
        for zone in ZONES:
            if instance_id in player.get("zones", {}).get(zone, []):
                found.append((player_id, zone))
    if len(found) != 1:
        raise InvalidMatchState(
            f"instance {instance_id} must appear in exactly one player zone; found={len(found)}"
        )
    return found[0]


def move_instance_row(state: dict[str, Any], instance_id: str, target_row: str) -> dict[str, Any]:
    """Move one board instance between rows without changing any grants."""
    if target_row not in ROWS:
        raise InvalidOperation(f"invalid target row: {target_row}")
    owner_id, zone = locate_instance(state, instance_id)
    if zone != "board":
        raise InvalidOperation("only a board instance can move between rows")
    instance = state["instances"][instance_id]
    previous_row = instance["state"].get("current_row")
    instance["state"]["current_row"] = target_row
    instance["state"]["last_board_row"] = target_row
    return {
        "transition": "row_move",
        "instance_id": instance_id,
        "owner_player_id": owner_id,
        "from_row": previous_row,
        "to_row": target_row,
    }


def transition_instance_zone(
    state: dict[str, Any],
    instance_id: str,
    to_zone: str,
    *,
    target_row: str | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    """Move an exact instance to another zone, preserving non-zone state.

    For a transition onto the board, target_row is mandatory. For every other
    zone it must be null. Returning from the board stores last_board_row and
    clears current_row. No bonus/protection/status/weather cleanup is implicit.
    """
    if to_zone not in ZONES:
        raise InvalidOperation(f"invalid destination zone: {to_zone}")
    owner_id, from_zone = locate_instance(state, instance_id)
    if from_zone == to_zone:
        raise InvalidOperation("instance is already in the requested zone")
    if to_zone == "board":
        if target_row not in ROWS:
            raise InvalidOperation("entering the board requires target_row")
    elif target_row is not None:
        raise InvalidOperation("target_row must be null outside the board")

    player = state["players"][owner_id]
    source_list = player["zones"][from_zone]
    destination = player["zones"][to_zone]
    # Validate every caller-controlled argument before mutating either zone.
    # A failed transition must leave the detached candidate state unchanged.
    if position is not None and (
        not isinstance(position, int)
        or isinstance(position, bool)
        or not 0 <= position <= len(destination)
    ):
        raise InvalidOperation("position must be an insertion index within the destination zone")
    source_list.remove(instance_id)
    if position is None:
        destination.append(instance_id)
    else:
        destination.insert(position, instance_id)

    runtime = state["instances"][instance_id]["state"]
    if from_zone == "board":
        runtime["last_board_row"] = runtime.get("current_row")
        runtime["current_row"] = None
    if to_zone == "board":
        runtime["current_row"] = target_row
        runtime["last_board_row"] = target_row

    return {
        "transition": "zone_change",
        "instance_id": instance_id,
        "owner_player_id": owner_id,
        "from_zone": from_zone,
        "to_zone": to_zone,
        "from_row": None,
        "to_row": target_row,
    }


def validate_after_transition(state: dict[str, Any]) -> None:
    """Convenience guard for callers after a sequence of transitions."""
    validate_match_state(state)
