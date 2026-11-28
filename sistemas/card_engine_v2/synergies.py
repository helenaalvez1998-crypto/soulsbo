"""Server-authoritative combo and faction-passive resolution for the alpha match.

The registry is release-bound by AlphaCatalog. Unknown tags or effects are never
inferred from display text. Combo precedence and once-per-round rules mirror the
approved legacy combo policy.
"""
from __future__ import annotations

import uuid
from typing import Any

from .errors import InvalidOperation
from .power import ALPHA_RAW_GRANT_POLICY


def _event(
    kind: str,
    *,
    source_effect_id: str,
    source_instance_id: str,
    target_instance_ids: list[str],
    caused_by_event_ids: list[str],
    payload: dict[str, Any],
    effect_scope: str = "direct",
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "kind": kind,
        "effect_scope": effect_scope,
        "source_effect_id": source_effect_id,
        "source_instance_id": source_instance_id,
        "target_instance_ids": target_instance_ids,
        "caused_by_event_ids": caused_by_event_ids,
        "payload": payload,
    }


def _append_bonus_grant(
    state: dict[str, Any],
    *,
    target_instance_id: str,
    amount: int,
    source_effect_id: str,
    source_instance_id: str | None,
    applied_event_id: str,
) -> str:
    if not isinstance(amount, int) or isinstance(amount, bool) or amount == 0:
        raise InvalidOperation("combo/passive bonus must be a non-zero integer")
    grant_id = str(uuid.uuid4())
    state["instances"][target_instance_id]["state"]["bonus_grants"].append(
        {
            "grant_id": grant_id,
            "amount": amount,
            "source_effect_id": source_effect_id,
            "source_instance_id": source_instance_id,
            "applied_event_id": applied_event_id,
            "expires_on": "round_close",
            "clamp_policy_id": ALPHA_RAW_GRANT_POLICY,
        }
    )
    return grant_id


def resolve_combo_for_play(
    state: dict[str, Any],
    *,
    player_id: str,
    current_instance_id: str,
    played_event_id: str,
    combo_registry: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Resolve at most one eligible combo after a unit enters the board.

    The newly played unit must contribute a required tag. Participants are
    distinct physical instances; pending combos remain available but can only
    be activated by a later contributing unit. Team bonus targets only allies
    that were already on the board in the activator's row.
    """
    player = state["players"][player_id]
    current = state["instances"][current_instance_id]
    new_tags = set(current["definition_snapshot"].get("combo_tags") or [])
    if not new_tags:
        return None

    board_ids = list(player["zones"]["board"])
    if current_instance_id not in board_ids:
        raise InvalidOperation("combo activation requires the current unit to be on the board")
    previous_board_ids = [item for item in board_ids if item != current_instance_id]
    prior_tags: set[str] = set()
    for instance_id in previous_board_ids:
        prior_tags.update(state["instances"][instance_id]["definition_snapshot"].get("combo_tags") or [])
    all_tags = prior_tags | new_tags

    round_state = player["round_state"]
    used = round_state.setdefault("synergy_used", {})
    candidates = sorted(
        combo_registry.items(),
        key=lambda item: (int(item[1]["priority"]), str(item[0])),
    )
    current_row = current["state"].get("current_row")
    if current_row not in ("melee", "ranged", "siege"):
        raise InvalidOperation("combo activator must occupy a valid row")

    for combo_id, combo in candidates:
        if used.get(combo_id):
            continue
        required = set(combo["required_tags"])
        if not (new_tags & required):
            continue
        if not required.issubset(all_tags):
            continue

        participant_ids = []
        for candidate_id in [*previous_board_ids, current_instance_id]:
            tags = set(state["instances"][candidate_id]["definition_snapshot"].get("combo_tags") or [])
            if tags & required:
                participant_ids.append(candidate_id)
        minimum = int(combo["minimum_distinct_participants"])
        if len(set(participant_ids)) < minimum:
            continue

        individual_bonus = int(combo["individual_bonus"])
        team_bonus = int(combo.get("team_bonus", 0))
        team_targets = [
            candidate_id
            for candidate_id in previous_board_ids
            if state["instances"][candidate_id]["state"].get("current_row") == current_row
        ] if team_bonus else []
        targets = [current_instance_id, *team_targets]
        event_id = str(uuid.uuid4())
        source_effect_id = f"combo.{combo_id}"
        grants = []
        grants.append(
            {
                "target_instance_id": current_instance_id,
                "amount": individual_bonus,
                "grant_id": _append_bonus_grant(
                    state,
                    target_instance_id=current_instance_id,
                    amount=individual_bonus,
                    source_effect_id=source_effect_id,
                    source_instance_id=current_instance_id,
                    applied_event_id=event_id,
                ),
            }
        )
        for target_id in team_targets:
            grants.append(
                {
                    "target_instance_id": target_id,
                    "amount": team_bonus,
                    "grant_id": _append_bonus_grant(
                        state,
                        target_instance_id=target_id,
                        amount=team_bonus,
                        source_effect_id=source_effect_id,
                        source_instance_id=current_instance_id,
                        applied_event_id=event_id,
                    ),
                }
            )
        current["state"].setdefault("activated_combo_ids", []).append(combo_id)
        used[combo_id] = True
        return {
            "event_id": event_id,
            "kind": "card_combo_activated",
            "effect_scope": "direct",
            "source_effect_id": source_effect_id,
            "source_instance_id": current_instance_id,
            "target_instance_ids": targets,
            "caused_by_event_ids": [played_event_id],
            "payload": {
                "combo_id": combo_id,
                "combo_name": combo["name"],
                "priority": combo["priority"],
                "required_tags": sorted(required),
                "participant_instance_ids": participant_ids,
                "individual_bonus": individual_bonus,
                "team_bonus": team_bonus,
                "team_bonus_target_instance_ids": team_targets,
                "grants": grants,
                "expires_on": "round_close",
                "once_per_player_per_round": True,
            },
        }
    return None


def resolve_faction_passive_for_play(
    state: dict[str, Any],
    *,
    player_id: str,
    current_instance_id: str,
    played_event_id: str,
    passive_registry: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Apply the player's first same-faction unit passive once per round.

    A faction must be selected explicitly at match creation (or inferred from
    the selected leader). Mixed-faction units do not change the player's deck
    faction and do not consume the passive when played.
    """
    player = state["players"][player_id]
    faction_id = player.get("faction_id")
    if not faction_id:
        return None
    passive = passive_registry.get(faction_id)
    if passive is None:
        raise InvalidOperation(f"no alpha faction passive registered for {faction_id}")
    instance = state["instances"][current_instance_id]
    card_faction = instance["definition_snapshot"].get("faction_id")
    round_state = player["round_state"]
    if card_faction != faction_id or round_state.get("faction_passive_used", False):
        return None
    amount = int(passive["bonus"])
    event_id = str(uuid.uuid4())
    effect_id = passive["passive_id"]
    grant_id = _append_bonus_grant(
        state,
        target_instance_id=current_instance_id,
        amount=amount,
        source_effect_id=effect_id,
        source_instance_id=current_instance_id,
        applied_event_id=event_id,
    )
    round_state["faction_passive_used"] = True
    return {
        "event_id": event_id,
        "kind": "faction_passive_applied",
        "effect_scope": "direct",
        "source_effect_id": effect_id,
        "source_instance_id": current_instance_id,
        "target_instance_ids": [current_instance_id],
        "caused_by_event_ids": [played_event_id],
        "payload": {
            "faction_id": faction_id,
            "passive_id": effect_id,
            "amount": amount,
            "grant_id": grant_id,
            "expires_on": "round_close",
            "once_per_player_per_round": True,
        },
    }
