"""Runtime invariants for CardInstance match envelopes and event records."""

from __future__ import annotations

import re
import uuid
from typing import Any

from .errors import InvalidMatchState, InvalidOperation

UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
ZONES = ("hand", "draw_pile", "board", "discard")
ROWS = ("melee", "ranged", "siege")
REMOVAL_CAUSES = ("normal_removal", "execution", "sacrifice")
BLOCKABLE_CAUSES = ("normal_removal", "execution")
VALID_OUTCOMES = ("applied", "partial", "blocked", "consumed_no_effect", "rejected")


def is_uuid4(value: Any) -> bool:
    if not isinstance(value, str) or not UUID4_RE.fullmatch(value):
        return False
    try:
        return uuid.UUID(value).version == 4
    except ValueError:
        return False


def validate_match_state(state: dict[str, Any]) -> None:
    """Validate invariants that must hold before a snapshot can be persisted.

    The JSON Schema remains the structural contract. This validator enforces
    cross-object invariants that JSON Schema cannot conveniently express.
    """
    if not isinstance(state, dict):
        raise InvalidMatchState("match state must be an object")
    required = {
        "schema_version",
        "match_id",
        "state_revision",
        "event_watermark",
        "status",
        "players",
        "instances",
        "definition_manifest",
    }
    missing = required - state.keys()
    if missing:
        raise InvalidMatchState(f"missing top-level keys: {sorted(missing)}")
    if state["schema_version"] != 7:
        raise InvalidMatchState("schema_version must be 7")
    if not isinstance(state["match_id"], int) or isinstance(state["match_id"], bool) or state["match_id"] <= 0:
        raise InvalidMatchState("match_id must be a positive integer")
    for field in ("state_revision", "event_watermark"):
        if not isinstance(state[field], int) or isinstance(state[field], bool) or state[field] < 0:
            raise InvalidMatchState(f"{field} must be a non-negative integer")
    if state["status"] not in ("active", "finished"):
        raise InvalidMatchState("status must be active or finished")

    players = state["players"]
    instances = state["instances"]
    if not isinstance(players, dict) or len(players) < 2:
        raise InvalidMatchState("players must contain at least two participants")
    if not isinstance(instances, dict):
        raise InvalidMatchState("instances must be an object keyed by instance_id")

    manifest = state["definition_manifest"]
    if not isinstance(manifest, dict):
        raise InvalidMatchState("definition_manifest must be an object")
    for key in (
        "catalog_release_id",
        "effect_registry_release_id",
        "balance_rules_release_id",
        "ruleset_release_id",
    ):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise InvalidMatchState(f"definition_manifest.{key} is required")
    if manifest.get("canonicalization") != "RFC8785":
        raise InvalidMatchState("definition_manifest.canonicalization must be RFC8785")

    seen_zone_ids: dict[str, str] = {}
    seen_exemplars: set[int] = set()
    for player_id, player in players.items():
        if not isinstance(player, dict):
            raise InvalidMatchState(f"player {player_id} must be an object")
        zones = player.get("zones")
        if not isinstance(zones, dict) or set(zones) != set(ZONES):
            raise InvalidMatchState(f"player {player_id} must define exactly the four zones")
        for zone_name in ZONES:
            zone_items = zones[zone_name]
            if not isinstance(zone_items, list):
                raise InvalidMatchState(f"{player_id}.{zone_name} must be a list")
            for instance_id in zone_items:
                if not is_uuid4(instance_id):
                    raise InvalidMatchState(f"invalid instance UUID in {player_id}.{zone_name}")
                if instance_id in seen_zone_ids:
                    raise InvalidMatchState(f"instance {instance_id} appears in multiple zones")
                seen_zone_ids[instance_id] = zone_name

    if set(seen_zone_ids) != set(instances):
        missing_from_zones = set(instances) - set(seen_zone_ids)
        unknown_in_zones = set(seen_zone_ids) - set(instances)
        raise InvalidMatchState(
            f"zone partition mismatch; missing={sorted(missing_from_zones)}, "
            f"unknown={sorted(unknown_in_zones)}"
        )

    for instance_id, instance in instances.items():
        if not is_uuid4(instance_id):
            raise InvalidMatchState(f"invalid instance key: {instance_id}")
        if not isinstance(instance, dict):
            raise InvalidMatchState(f"instance {instance_id} must be an object")
        if instance.get("schema_version") != 7 or instance.get("instance_id") != instance_id:
            raise InvalidMatchState(f"instance {instance_id} has inconsistent schema/identity")
        if not isinstance(instance.get("card_id"), str) or not instance["card_id"]:
            raise InvalidMatchState(f"instance {instance_id} has no card_id")
        raw_owner_id = instance.get("owner_player_id")
        if not isinstance(raw_owner_id, str) or not raw_owner_id:
            raise InvalidMatchState(f"instance {instance_id} has invalid owner_player_id")
        owner_id = raw_owner_id
        if owner_id not in players:
            raise InvalidMatchState(f"instance {instance_id} has unknown owner {owner_id}")
        if seen_zone_ids[instance_id] not in ZONES:
            raise InvalidMatchState(f"instance {instance_id} has invalid zone")
        owner_zones = players[owner_id]["zones"]
        if instance_id not in owner_zones[seen_zone_ids[instance_id]]:
            raise InvalidMatchState(f"instance {instance_id} is not in its owner's zone")
        exemplar_id = instance.get("exemplar_id")
        if exemplar_id is not None:
            if not isinstance(exemplar_id, int) or isinstance(exemplar_id, bool) or exemplar_id <= 0:
                raise InvalidMatchState(f"instance {instance_id} has invalid exemplar_id")
            if exemplar_id in seen_exemplars:
                raise InvalidMatchState(f"exemplar_id {exemplar_id} is used by multiple instances")
            seen_exemplars.add(exemplar_id)
        exemplar_snapshot = instance.get("exemplar_snapshot")
        if exemplar_snapshot is not None:
            if instance.get("origin_type") != "deck_exemplar" or not isinstance(exemplar_snapshot, dict):
                raise InvalidMatchState(f"instance {instance_id} has exemplar_snapshot without deck_exemplar provenance")
            rarity_id = exemplar_snapshot.get("rarity_id")
            if rarity_id not in {"common", "uncommon", "rare", "epic", "legendary", "mythic", "primordial", "singular"}:
                raise InvalidMatchState(f"instance {instance_id} has invalid exemplar rarity classification")
            exemplar_power = exemplar_snapshot.get("power_base")
            if exemplar_power is not None and (
                not isinstance(exemplar_power, int) or isinstance(exemplar_power, bool) or not 1 <= exemplar_power <= 15
            ):
                raise InvalidMatchState(f"instance {instance_id} has invalid exemplar power snapshot")
        if instance.get("origin_type") == "deck_exemplar":
            if exemplar_id is None or not isinstance(exemplar_snapshot, dict):
                raise InvalidMatchState(f"deck_exemplar instance {instance_id} requires exemplar_id and exemplar_snapshot")
            kind = instance.get("definition_snapshot", {}).get("kind")
            if kind == "unit" and not isinstance(exemplar_snapshot.get("power_base"), int):
                raise InvalidMatchState(f"unit exemplar instance {instance_id} requires frozen exemplar power")
            if kind == "special" and exemplar_snapshot.get("power_base") is not None:
                raise InvalidMatchState(f"special exemplar instance {instance_id} cannot carry board power")
        elif exemplar_snapshot is not None:
            raise InvalidMatchState(f"non-exemplar instance {instance_id} cannot carry exemplar_snapshot")
        snapshot = instance.get("definition_snapshot")
        if not isinstance(snapshot, dict) or snapshot.get("card_id") != instance["card_id"]:
            raise InvalidMatchState(f"instance {instance_id} definition_snapshot/card_id mismatch")
        digest = snapshot.get("definition_digest")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise InvalidMatchState(f"instance {instance_id} has invalid definition_digest")
        runtime = instance.get("state")
        if not isinstance(runtime, dict):
            raise InvalidMatchState(f"instance {instance_id} state must be an object")
        current_row = runtime.get("current_row")
        expected_zone = seen_zone_ids[instance_id]
        if expected_zone == "board":
            if current_row not in ROWS:
                raise InvalidMatchState(f"board instance {instance_id} needs a current_row")
        elif current_row is not None:
            raise InvalidMatchState(f"non-board instance {instance_id} must have current_row=null")
        if runtime.get("last_board_row") not in (*ROWS, None):
            raise InvalidMatchState(f"instance {instance_id} has invalid last_board_row")
        for grant_key in (
            "bonus_grants",
            "protection_grants",
            "status_applications",
            "weather_resistance_modifiers",
        ):
            if not isinstance(runtime.get(grant_key), list):
                raise InvalidMatchState(f"instance {instance_id}.{grant_key} must be a list")

    for player_id, player in players.items():
        faction_id = player.get("faction_id")
        if faction_id is not None and faction_id not in {"golden_order", "crimson_veil", "dark_moon", "the_forgotten"}:
            raise InvalidMatchState(f"player {player_id} has invalid faction_id")
        leader_id = player.get("leader_id")
        if leader_id is not None and (not isinstance(leader_id, str) or not leader_id):
            raise InvalidMatchState(f"player {player_id} has invalid leader_id")
        if "leader_used" in player and not isinstance(player["leader_used"], bool):
            raise InvalidMatchState(f"player {player_id} has invalid leader_used")
        round_state = player.get("round_state")
        if not isinstance(round_state, dict) or round_state.get("last_unit_play_row") not in (*ROWS, None):
            raise InvalidMatchState(f"player {player_id} has invalid round_state.last_unit_play_row")
        passive_used = round_state.get("faction_passive_used", False)
        if not isinstance(passive_used, bool):
            raise InvalidMatchState(f"player {player_id} has invalid round_state.faction_passive_used")
        synergy_used = round_state.get("synergy_used", {})
        if not isinstance(synergy_used, dict) or any(
            not isinstance(combo_id, str) or not combo_id or not isinstance(used, bool)
            for combo_id, used in synergy_used.items()
        ):
            raise InvalidMatchState(f"player {player_id} has invalid round_state.synergy_used")
        counters = player.get("counters")
        if not isinstance(counters, dict):
            raise InvalidMatchState(f"player {player_id} counters must be an object")
        for counter in ("board_removal_count", "sacrifice_count"):
            value = player.get("counters", {}).get(counter)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise InvalidMatchState(f"player {player_id} has invalid {counter}")


def validate_operation_request(match_id: int, request: dict[str, Any]) -> None:
    if not isinstance(request, dict):
        raise InvalidOperation("request must be an object")
    required = {"operation_id", "actor", "expected_revision", "action_type", "payload"}
    missing = required - request.keys()
    extra = request.keys() - required
    if missing:
        raise InvalidOperation(f"missing request keys: {sorted(missing)}")
    if extra:
        raise InvalidOperation(f"unexpected request keys: {sorted(extra)}")
    if not isinstance(match_id, int) or match_id <= 0:
        raise InvalidOperation("match_id must be a positive integer")
    if not is_uuid4(request["operation_id"]):
        raise InvalidOperation("operation_id must be UUIDv4")
    if not isinstance(request["expected_revision"], int) or isinstance(request["expected_revision"], bool):
        raise InvalidOperation("expected_revision must be an integer")
    if request["expected_revision"] < 0:
        raise InvalidOperation("expected_revision must be non-negative")
    if not isinstance(request["action_type"], str) or not request["action_type"]:
        raise InvalidOperation("action_type is required")
    if not isinstance(request["payload"], dict):
        raise InvalidOperation("payload must be an object")
    actor = request["actor"]
    if not isinstance(actor, dict) or actor.get("type") not in ("player", "system"):
        raise InvalidOperation("actor must be player or system")
    if actor["type"] == "player":
        if set(actor) != {"type", "player_id"} or not isinstance(actor.get("player_id"), str):
            raise InvalidOperation("player actor requires only a string player_id")
        if not re.fullmatch(r"-?(?:0|[1-9][0-9]*)", actor["player_id"]):
            raise InvalidOperation("player_id must be a numeric identifier string")
    if actor["type"] == "system":
        if set(actor) != {"type", "system_id"} or not isinstance(actor.get("system_id"), str):
            raise InvalidOperation("system actor requires only a string system_id")
        if not actor["system_id"] or len(actor["system_id"]) > 80:
            raise InvalidOperation("system_id must contain 1..80 characters")
