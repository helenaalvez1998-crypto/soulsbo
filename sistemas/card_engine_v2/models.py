"""Small constructors for identity-safe CardInstance v7 values."""

from __future__ import annotations

import copy
import uuid
from typing import Any

from .validation import ROWS


def new_instance_id() -> str:
    """Generate the server-side UUIDv4 identity for one physical match occurrence."""
    return str(uuid.uuid4())


def make_card_instance(
    *,
    card_id: str,
    owner_player_id: str | int,
    origin_type: str,
    definition_snapshot: dict[str, Any],
    exemplar_id: int | None = None,
    exemplar_snapshot: dict[str, Any] | None = None,
    instance_id: str | None = None,
    initial_row: str | None = None,
) -> dict[str, Any]:
    """Build one CardInstance v7, preserving exemplar provenance when supplied."""
    if not card_id:
        raise ValueError("card_id is required")
    if not origin_type:
        raise ValueError("origin_type is required")
    if definition_snapshot.get("card_id") != card_id:
        raise ValueError("definition_snapshot.card_id must match card_id")
    if initial_row not in (*ROWS, None):
        raise ValueError("initial_row must be melee, ranged, siege or None")
    if origin_type == "deck_exemplar" and (exemplar_id is None or not isinstance(exemplar_snapshot, dict)):
        raise ValueError("deck_exemplar instances require a verified exemplar_id and exemplar_snapshot")
    if origin_type != "deck_exemplar" and exemplar_snapshot is not None:
        raise ValueError("exemplar_snapshot is only allowed for deck_exemplar instances")
    identity = instance_id or new_instance_id()
    return {
        "schema_version": 7,
        "instance_id": identity,
        "card_id": card_id,
        "exemplar_id": exemplar_id,
        "exemplar_snapshot": copy.deepcopy(exemplar_snapshot) if exemplar_snapshot is not None else None,
        "owner_player_id": str(owner_player_id),
        "origin_type": origin_type,
        "definition_snapshot": copy.deepcopy(definition_snapshot),
        "state": {
            "current_row": initial_row,
            "last_board_row": initial_row,
            "bonus_grants": [],
            "protection_grants": [],
            "status_applications": [],
            "weather_resistance_modifiers": [],
            "activated_combo_ids": [],
            "effect_state": {},
        },
    }
