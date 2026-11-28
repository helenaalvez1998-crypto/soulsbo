"""Closed alpha leader handlers for the isolated Card Engine v2 match."""
from __future__ import annotations

import uuid
from typing import Any, Callable

from .errors import InvalidOperation
from .power import ALPHA_RAW_GRANT_POLICY, base_power, bonus_total, effective_power, status_counts
from .validation import ROWS
from .zones import transition_instance_zone

STATUS_KEYS = ("status.bleeding", "status.frost", "status.scarlet_rot", "status.madness")


def _event(
    kind: str,
    *,
    effect_id: str,
    targets: list[str],
    payload: dict[str, Any],
    caused_by: list[str] | None = None,
    scope: str = "direct",
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "kind": kind,
        "effect_scope": scope,
        "source_effect_id": effect_id,
        "source_instance_id": None,
        "target_instance_ids": targets,
        "caused_by_event_ids": caused_by or [],
        "payload": payload,
    }


def _ordered(
    state: dict[str, Any],
    player_id: str,
    runtime: dict[str, Any],
    *,
    row: str | None = None,
    descending: bool,
) -> list[str]:
    ids = list(state["players"][player_id]["zones"]["board"])
    if row is not None:
        ids = [item for item in ids if state["instances"][item]["state"].get("current_row") == row]
    order = {item: index for index, item in enumerate(state["players"][player_id]["zones"]["board"])}
    return sorted(
        ids,
        key=lambda item: (
            -effective_power(state, state["instances"][item], runtime["weather_by_row"])
            if descending
            else effective_power(state, state["instances"][item], runtime["weather_by_row"]),
            order[item],
        ),
    )


def _bonus_grant(
    state: dict[str, Any],
    *,
    target_id: str,
    amount: int,
    effect_id: str,
    event_id: str,
    source_instance_id: str | None = None,
) -> str:
    if not isinstance(amount, int) or isinstance(amount, bool) or amount == 0:
        raise InvalidOperation("leader bonus must be a non-zero integer")
    grant_id = str(uuid.uuid4())
    state["instances"][target_id]["state"]["bonus_grants"].append(
        {
            "grant_id": grant_id,
            "amount": amount,
            "source_effect_id": effect_id,
            "source_instance_id": source_instance_id,
            "applied_event_id": event_id,
            "expires_on": "round_close",
            "clamp_policy_id": ALPHA_RAW_GRANT_POLICY,
        }
    )
    return grant_id


def _add_status_mark(
    state: dict[str, Any],
    *,
    target_id: str,
    status_id: str,
    effect_id: str,
    event_id: str,
) -> tuple[int, int | None]:
    instance = state["instances"][target_id]
    before = status_counts(instance)[status_id]
    if before >= 2:
        return 0, None
    instance["state"]["status_applications"].append(
        {
            "application_id": str(uuid.uuid4()),
            "status_id": status_id,
            "source_effect_id": effect_id,
            "source_instance_id": None,
            "applied_event_id": event_id,
            "expires_on": "round_close",
        }
    )
    after = before + 1
    bonus_delta = None
    if status_id == "status.bleeding" and before < 2 <= after:
        current_bonus = bonus_total(instance)
        new_bonus = max(-2, current_bonus - 2)
        bonus_delta = new_bonus - current_bonus
        if bonus_delta:
            _bonus_grant(
                state,
                target_id=target_id,
                amount=bonus_delta,
                effect_id="status.bleeding.threshold",
                event_id=event_id,
            )
        instance["state"]["status_applications"] = [
            app for app in instance["state"]["status_applications"]
            if app.get("status_id") != "status.bleeding"
        ]
    return 1, bonus_delta


def _protection_charges(instance: dict[str, Any]) -> int:
    return sum(
        int(grant.get("charges", 0))
        for grant in instance["state"].get("protection_grants", [])
        if isinstance(grant.get("charges", 0), int) and not isinstance(grant.get("charges", 0), bool)
    )


def _expire_board_exit(instance: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in ("bonus_grants", "protection_grants", "status_applications", "weather_resistance_modifiers"):
        current = instance["state"].get(key, [])
        retained = [item for item in current if item.get("expires_on") != "board_exit"]
        counts[key] = len(current) - len(retained)
        instance["state"][key] = retained
    instance["state"]["protection_grants"] = []
    instance["state"]["status_applications"] = []
    return counts


def resolve_leader_effect(
    state: dict[str, Any],
    runtime: dict[str, Any],
    *,
    player_id: str,
    leader: dict[str, Any],
    selected_row: str | None,
    apply_vengeance: Callable[[dict[str, Any], str, str, str, str, list[dict[str, Any]]], None],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve one leader on a detached state; raises before commit on invalid use."""
    effect_id = leader["effect_id"]
    params = leader["params"]
    player = state["players"][player_id]
    player_board = list(player["zones"]["board"])
    opponents = [pid for pid in state["players"] if pid != player_id]
    if len(opponents) != 1:
        raise InvalidOperation("alpha leaders require exactly one opponent")
    enemy_id = opponents[0]
    enemy_board = list(state["players"][enemy_id]["zones"]["board"])
    weather = runtime["weather_by_row"]
    row_required = effect_id in {
        "leader.morgott_omen", "leader.mohg_blood_rite", "leader.rykard_devour",
        "leader.esgar_blood_priest", "leader.forgotten_blessing", "leader.astel_gravity",
        "leader.loretta_knight",
    }
    if row_required and selected_row not in ROWS:
        raise InvalidOperation("leader action requires a valid selected row")
    if effect_id == "leader.loretta_knight" and selected_row != params["required_row"]:
        raise InvalidOperation("Loretta can only be activated for the ranged row")

    events: list[dict[str, Any]] = []
    target_results: list[dict[str, Any]] = []

    if effect_id == "leader.godfrey_warlord":
        targets = _ordered(state, player_id, runtime, row=params["row"], descending=False)
        if not targets:
            raise InvalidOperation("Godfrey requires at least one melee ally")
        event = _event("leader_bonus_applied", effect_id=effect_id, targets=targets, payload={"bonus": params["bonus"], "row": params["row"], "expires_on": "round_close"})
        for target_id in targets:
            _bonus_grant(state, target_id=target_id, amount=params["bonus"], effect_id=effect_id, event_id=event["event_id"])
        events.append(event)

    elif effect_id == "leader.morgott_omen":
        targets = [item for item in _ordered(state, player_id, runtime, row=selected_row, descending=True) if _protection_charges(state["instances"][item]) == 0]
        targets = targets[: int(params["maximum_targets"])]
        if not targets:
            raise InvalidOperation("Morgott has no unshielded ally in the selected row")
        event = _event("leader_protection_and_bonus_applied", effect_id=effect_id, targets=targets, payload={"profile_id": params["protection_profile_id"], "charges": params["protection_charges"], "bonus": params["bonus"], "row": selected_row, "expires_on": "round_close"})
        for target_id in targets:
            grant_id = str(uuid.uuid4())
            state["instances"][target_id]["state"]["protection_grants"].append({
                "grant_id": grant_id,
                "profile_id": params["protection_profile_id"],
                "charges": params["protection_charges"],
                "source_effect_id": effect_id,
                "source_instance_id": None,
                "applied_event_id": event["event_id"],
                "expires_on": "round_close",
            })
            _bonus_grant(state, target_id=target_id, amount=params["bonus"], effect_id=effect_id, event_id=event["event_id"])
            target_results.append({"target_instance_id": target_id, "outcome": "applied", "protection_grant_id": grant_id})
        events.append(event)

    elif effect_id in ("leader.radagon_purification", "leader.rennala_full_moon"):
        statuses = set(params["statuses"] if effect_id == "leader.radagon_purification" else params["purify_statuses"])
        affected = []
        bonus_targets = []
        for target_id in player_board:
            instance = state["instances"][target_id]
            present = {item.get("status_id") for item in instance["state"]["status_applications"]}
            removed = present & statuses
            if not removed:
                continue
            instance["state"]["status_applications"] = [
                item for item in instance["state"]["status_applications"] if item.get("status_id") not in statuses
            ]
            affected.append(target_id)
            if effect_id == "leader.radagon_purification" or instance["state"].get("current_row") == params.get("bonus_in_row"):
                bonus_targets.append(target_id)
        if not affected:
            raise InvalidOperation("leader has no ally with a status it can purify")
        event = _event("leader_statuses_purified", effect_id=effect_id, targets=affected, payload={"purified_status_ids": sorted(statuses), "bonus_targets": bonus_targets, "bonus_per_target": params.get("bonus_per_purified_unit", params.get("bonus", 0)), "expires_on": "round_close"})
        amount = int(params.get("bonus_per_purified_unit", params.get("bonus", 0)))
        for target_id in bonus_targets:
            _bonus_grant(state, target_id=target_id, amount=amount, effect_id=effect_id, event_id=event["event_id"])
        events.append(event)

    elif effect_id == "leader.mohg_blood_rite":
        targets = _ordered(state, enemy_id, runtime, row=selected_row, descending=True)[: int(params["maximum_targets"])]
        if not targets:
            raise InvalidOperation("Mohg requires at least one enemy in the selected row")
        event_id = str(uuid.uuid4())
        applications = []
        for target_id in targets:
            marks_added, bonus_delta = _add_status_mark(state, target_id=target_id, status_id=params["status_id"], effect_id=effect_id, event_id=event_id)
            applications.append({"target_instance_id": target_id, "marks_added": marks_added, "bonus_delta": bonus_delta})
        events.append({
            "event_id": event_id,
            "kind": "leader_bleeding_applied",
            "effect_scope": "direct",
            "source_effect_id": effect_id,
            "source_instance_id": None,
            "target_instance_ids": targets,
            "caused_by_event_ids": [],
            "payload": {"status_id": params["status_id"], "applications": applications, "threshold": params["threshold"], "threshold_bonus_delta": params["threshold_bonus_delta"], "bonus_floor": params["bonus_floor"], "expires_on": "round_close"},
        })

    elif effect_id == "leader.rykard_devour":
        allies = _ordered(state, player_id, runtime, row=selected_row, descending=False)
        if len(allies) < int(params["minimum_allies_in_row"]):
            raise InvalidOperation("Rykard requires at least two allies in the selected row")
        victim_id = allies[0]
        victim = state["instances"][victim_id]
        transition = transition_instance_zone(state, victim_id, "discard")
        cleanup = _expire_board_exit(victim)
        player["counters"]["sacrifice_count"] += 1
        removal_event = _event("unit_removed", effect_id=effect_id, targets=[victim_id], payload={"cause_id": "sacrifice", "from_zone": "board", "to_zone": "discard", "affected_player_id": player_id, "row_at_removal": selected_row, "zone_transition": transition, "expired_board_exit_state": cleanup})
        events.append(removal_event)
        apply_vengeance(state, victim_id, player_id, selected_row, removal_event["event_id"], events)
        survivors = [item for item in player["zones"]["board"] if state["instances"][item]["state"].get("current_row") == selected_row]
        if survivors:
            bonus_event = _event("leader_survivor_bonus_applied", effect_id=effect_id, targets=survivors, caused_by=[removal_event["event_id"]], payload={"bonus": params["survivor_bonus"], "row": selected_row, "expires_on": "round_close", "independent_from_vengeance": True})
            for target_id in survivors:
                _bonus_grant(state, target_id=target_id, amount=int(params["survivor_bonus"]), effect_id=effect_id, event_id=bonus_event["event_id"])
            events.append(bonus_event)
        target_results.append({"target_instance_id": victim_id, "outcome": "sacrificed"})

    elif effect_id == "leader.esgar_blood_priest":
        candidates = [
            item for item in player["zones"]["discard"]
            if state["instances"][item]["definition_snapshot"].get("kind") == "unit"
            and (base_power(state["instances"][item]) or 999) <= int(params["maximum_base_power"])
        ]
        if not candidates:
            raise InvalidOperation("Esgar has no eligible unit in the discard pile")
        # Stable max preserves discard-zone order for equal base power.
        target_id = max(candidates, key=lambda item: int(base_power(state["instances"][item]) or 0))
        instance = state["instances"][target_id]
        transition = transition_instance_zone(state, target_id, "board", target_row=selected_row)
        cleanup = _expire_board_exit(instance)
        # RSRX-07/08/10: clear statuses/protection, keep round_close/permanent grants,
        # add Esgar's +1 as a separately sourced grant, and use requested row.
        instance["state"]["protection_grants"] = []
        instance["state"]["status_applications"] = []
        bonus_event = _event("leader_return_bonus_applied", effect_id=effect_id, targets=[target_id], payload={"bonus": params["bonus_on_return"], "expires_on": "round_close"})
        _bonus_grant(state, target_id=target_id, amount=int(params["bonus_on_return"]), effect_id=effect_id, event_id=bonus_event["event_id"])
        return_event = _event("unit_returned_from_discard", effect_id=effect_id, targets=[target_id], payload={"destination_row": selected_row, "zone_transition": transition, "expired_board_exit_state": cleanup, "on_play_hooks_retriggered": False, "combo_retriggered": False, "faction_passive_retriggered": False})
        events.extend([return_event, bonus_event])
        target_results.append({"target_instance_id": target_id, "outcome": "returned", "row": selected_row})

    elif effect_id == "leader.forgotten_blessing":
        targets = [
            item for item in player_board
            if state["instances"][item]["state"].get("current_row") == selected_row
            and state["instances"][item]["definition_snapshot"].get("faction_id") == params["target_faction_id"]
        ]
        if not targets:
            raise InvalidOperation("Papa Esquecido requires a Forgotten ally in the selected row")
        event = _event("leader_bonus_applied", effect_id=effect_id, targets=targets, payload={"bonus": params["bonus"], "row": selected_row, "faction_id": params["target_faction_id"], "expires_on": "round_close"})
        for target_id in targets:
            _bonus_grant(state, target_id=target_id, amount=int(params["bonus"]), effect_id=effect_id, event_id=event["event_id"])
        events.append(event)

    elif effect_id == "leader.astel_gravity":
        targets = _ordered(state, enemy_id, runtime, row=selected_row, descending=True)[: int(params["maximum_targets"])]
        if not targets:
            raise InvalidOperation("Astel requires at least one enemy in the selected row")
        event_id = str(uuid.uuid4())
        applications = []
        for target_id in targets:
            marks_added, _bonus_delta = _add_status_mark(state, target_id=target_id, status_id=params["status_id"], effect_id=effect_id, event_id=event_id)
            applications.append({"target_instance_id": target_id, "marks_added": marks_added})
        events.append({
            "event_id": event_id,
            "kind": "leader_frost_applied",
            "effect_scope": "direct",
            "source_effect_id": effect_id,
            "source_instance_id": None,
            "target_instance_ids": targets,
            "caused_by_event_ids": [],
            "payload": {"status_id": params["status_id"], "applications": applications, "maximum_marks": params["maximum_marks"], "expires_on": "round_close"},
        })

    elif effect_id == "leader.loretta_knight":
        targets = _ordered(state, player_id, runtime, row=params["required_row"], descending=True)[: int(params["maximum_targets"])]
        if not targets:
            raise InvalidOperation("Loretta requires at least one allied ranged unit")
        event = _event("leader_bonus_applied", effect_id=effect_id, targets=targets, payload={"bonus": params["bonus"], "row": params["required_row"], "expires_on": "round_close"})
        for target_id in targets:
            _bonus_grant(state, target_id=target_id, amount=int(params["bonus"]), effect_id=effect_id, event_id=event["event_id"])
        events.append(event)

    else:
        raise InvalidOperation(f"unsupported alpha leader effect: {effect_id}")

    if not events:
        raise InvalidOperation("leader effect produced no event")
    target_ids = []
    for event in events:
        for target_id in event.get("target_instance_ids", []):
            if target_id not in target_ids:
                target_ids.append(target_id)
    if not target_results:
        target_results = [{"target_instance_id": target_id, "outcome": "applied"} for target_id in target_ids]
    return events, target_results
