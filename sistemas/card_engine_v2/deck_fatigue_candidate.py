"""Isolated reference arithmetic for the proposed deck-fatigue contract.

This module is intentionally NOT imported by AlphaMatchController and is not
part of the active ruleset. It makes the proposed damage progression testable
without choosing balance values or silently defining draw-phase cadence.
"""

from __future__ import annotations

from typing import Any

from .errors import InvalidOperation


def _positive_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InvalidOperation(f"{field_name} must be a positive integer")
    return value


def _non_negative_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise InvalidOperation(f"{field_name} must be a non-negative integer")
    return value


def resolve_fatigue_step(
    previous_fatigue_count: int,
    *,
    initial_damage: int,
    damage_increment: int,
    maximum_damage: int | None = None,
) -> dict[str, int | None]:
    """Calculate one player's next empty-draw fatigue step, without mutation.

    Candidate arithmetic (not yet approved as a game rule):
        raw_damage = initial_damage + previous_fatigue_count * damage_increment
        applied_damage = min(raw_damage, maximum_damage) when a cap is set.

    `previous_fatigue_count` counts this player's earlier failed draw phases.
    The caller is responsible for invoking this exactly once at the approved
    draw-phase boundary, persisting the new count and applying player-life
    damage atomically. Those runtime responsibilities are deliberately absent.
    """
    previous_count = _non_negative_int(previous_fatigue_count, "previous_fatigue_count")
    base = _positive_int(initial_damage, "initial_damage")
    increment = _positive_int(damage_increment, "damage_increment")
    cap = None if maximum_damage is None else _positive_int(maximum_damage, "maximum_damage")
    if cap is not None and cap <= base:
        raise InvalidOperation("maximum_damage must be greater than initial_damage")

    fatigue_count = previous_count + 1
    raw_damage = base + previous_count * increment
    applied_damage = raw_damage if cap is None else min(raw_damage, cap)
    return {
        "previous_fatigue_count": previous_count,
        "fatigue_count": fatigue_count,
        "raw_damage": raw_damage,
        "damage": applied_damage,
        "maximum_damage": cap,
    }


def resolve_draw_phase_candidate(
    previous_fatigue_count: int,
    *,
    requested_cards: int,
    available_cards: int,
    initial_damage: int,
    damage_increment: int,
    maximum_damage: int | None = None,
) -> dict[str, int | bool | None]:
    """Model one incomplete draw phase as one fatigue step (candidate only).

    The candidate treats any short draw as one fatigue event, even if several
    cards could not be drawn. This is explicitly a proposed policy choice, not
    a rule approved by the source document. No physical card zones are mutated.
    """
    requested = _positive_int(requested_cards, "requested_cards")
    available = _non_negative_int(available_cards, "available_cards")
    drawn = min(requested, available)
    missing = requested - drawn
    if missing == 0:
        return {
            "cards_drawn": drawn,
            "cards_missing": 0,
            "fatigue_applied": False,
            "fatigue_count": _non_negative_int(previous_fatigue_count, "previous_fatigue_count"),
            "fatigue_damage": 0,
        }

    step = resolve_fatigue_step(
        previous_fatigue_count,
        initial_damage=initial_damage,
        damage_increment=damage_increment,
        maximum_damage=maximum_damage,
    )
    return {
        "cards_drawn": drawn,
        "cards_missing": missing,
        "fatigue_applied": True,
        "fatigue_count": step["fatigue_count"],
        "fatigue_damage": step["damage"],
    }


__all__ = ["resolve_draw_phase_candidate", "resolve_fatigue_step"]
