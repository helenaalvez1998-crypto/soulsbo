"""Two-player best-of-three playable match harness for the isolated v2 alpha.

This harness uses only the explicit alpha allowlist and dedicated SQLite
repository. It is not an HTTP/Discord adapter and is not wired to production.
"""

from __future__ import annotations

import copy
import random
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

from .alpha_catalog import AlphaCatalog
from .combat import DEFAULT_STARTING_LIFE, apply_life_damage, resolve_row_combat
from .errors import InvalidOperation
from .entry_effects import resolve_unit_entry_effect
from .gameplay import ActionDefinition, GameplayResolver, ProtectionProfile
from .models import make_card_instance
from .leaders import resolve_leader_effect
from .power import (
    ALPHA_RAW_GRANT_POLICY,
    bonus_total,
    effective_power,
    base_power,
    metric_resolver_for_weather,
    status_counts,
)
from .repository import HandlerResult, OperationReceipt, SQLiteMatchRepository
from .targeting import TargetPolicy, build_target_offer
from .synergies import resolve_combo_for_play, resolve_faction_passive_for_play
from .validation import ROWS, is_uuid4, validate_match_state
from .zones import locate_instance, transition_instance_zone


PLAYER_ACTIONS = {
    "match.play_unit",
    "match.play_special",
    "match.sacrifice_unit",
    "match.activate_leader",
    "match.activate_card_ability",
    "match.pass",
}


def _event(
    kind: str,
    *,
    effect_scope: str = "direct",
    source_effect_id: str | None = None,
    source_instance_id: str | None = None,
    target_instance_ids: list[str] | None = None,
    caused_by_event_ids: list[str] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "kind": kind,
        "effect_scope": effect_scope,
        "source_effect_id": source_effect_id,
        "source_instance_id": source_instance_id,
        "target_instance_ids": target_instance_ids or [],
        "caused_by_event_ids": caused_by_event_ids or [],
        "payload": payload or {},
    }


def _expire_grants(instance: dict[str, Any], expirations: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for field_name in (
        "bonus_grants",
        "protection_grants",
        "status_applications",
        "weather_resistance_modifiers",
    ):
        current = instance["state"].get(field_name, [])
        retained = [item for item in current if item.get("expires_on") not in expirations]
        counts[field_name] = len(current) - len(retained)
        instance["state"][field_name] = retained
    return counts


class AlphaMatchController:
    """Server-authoritative controller for a small playable two-player match."""

    def __init__(self, repository: SQLiteMatchRepository, catalog: AlphaCatalog | None = None) -> None:
        self.repository = repository
        self.catalog = catalog or AlphaCatalog()
        self._build_resolver()

    def _build_resolver(self) -> None:
        ally_policy = TargetPolicy(
            policy_id="alpha.ally.board.single",
            selection_mode="manual_single",
            target_side="allies",
            source_zone="board",
            row_scope="global",
            eligibility_metric="none",
            display_metric="effective_power",
            sort_metric="none",
            direction="none",
            tie_breaker="zone_order",
            minimum_targets=1,
            maximum_targets=1,
            on_no_target="reject",
        )
        execution_policy = TargetPolicy(
            policy_id="alpha.enemy.selected_row.execution",
            selection_mode="manual_single",
            target_side="enemies",
            source_zone="board",
            row_scope="selected_row",
            eligibility_metric="effective_power",
            display_metric="effective_power",
            sort_metric="none",
            direction="none",
            tie_breaker="zone_order",
            minimum_targets=1,
            maximum_targets=1,
            on_no_target="reject",
            predicates=(
                {"predicate_id": "metric.at_most", "params": {"metric": "effective_power", "amount": 6}},
            ),
        )
        actions = {
            "unit.grant_protection": ActionDefinition(
                action_type="unit.grant_protection",
                source_effect_id="gwent_egide",
                target_policy_id=ally_policy.policy_id,
                allowed_source_zones=frozenset({"hand"}),
                protection_profile_id="alpha.protection.standard",
                protection_charges=1,
                protection_expires_on="round_close",
            ),
            "unit.remove": ActionDefinition(
                action_type="unit.remove",
                source_effect_id="gwent_execucao",
                cause_target_policy_ids=(("execution", execution_policy.policy_id),),
                allowed_causes=frozenset({"execution"}),
                no_target_outcome="rejected",
                consume_source_on_success=True,
                consume_source_on_block=True,
                allowed_source_zones=frozenset({"hand"}),
            ),
            "unit.sacrifice": ActionDefinition(
                action_type="unit.sacrifice",
                source_effect_id="effect.sacrifice_unit",
                target_policy_id=ally_policy.policy_id,
                allowed_causes=frozenset({"sacrifice"}),
            ),
        }
        self.resolver = GameplayResolver(
            actions=actions,
            target_policies={ally_policy.policy_id: ally_policy, execution_policy.policy_id: execution_policy},
            protection_profiles={
                "alpha.protection.standard": ProtectionProfile("alpha.protection.standard")
            },
            vengeance_clamp_policy_id=ALPHA_RAW_GRANT_POLICY,
        )
        self.ally_policy = ally_policy
        self.execution_policy = execution_policy

    def _resolver_for_runtime(self, runtime: dict[str, Any]) -> GameplayResolver:
        """Return the server resolver bound to the match's current weather."""
        return GameplayResolver(
            actions=self.resolver.actions,
            target_policies=self.resolver.target_policies,
            protection_profiles=self.resolver.protection_profiles,
            vengeance_clamp_policy_id=self.resolver.vengeance_clamp_policy_id,
            metric_resolver=metric_resolver_for_weather(runtime["weather_by_row"]),
        )

    def create_match(
        self,
        *,
        match_id: int,
        player_ids: Sequence[str | int],
        decks: Mapping[str | int, Sequence[str]],
        initial_hand_size: int | None = None,
        player_factions: Mapping[str | int, str] | None = None,
        leaders: Mapping[str | int, str] | None = None,
        match_setup_metadata: Mapping[str, Any] | None = None,
        starting_player_id: str | int | None = None,
        exemplar_slots_by_player: Mapping[str | int, Sequence[Mapping[str, Any]]] | None = None,
    ) -> None:
        """Create a deterministic match from card IDs; duplicate models are allowed."""
        normalized_players = [str(item) for item in player_ids]
        if len(normalized_players) != 2 or len(set(normalized_players)) != 2:
            raise InvalidOperation("alpha playable match requires exactly two distinct players")
        if any(not item.isdigit() for item in normalized_players):
            raise InvalidOperation("alpha player IDs must be numeric strings")
        starter = normalized_players[0] if starting_player_id is None else str(starting_player_id)
        if starter not in normalized_players:
            raise InvalidOperation("starting_player_id must identify one of the match players")
        hand_size = self.catalog.ruleset.get("initial_hand_size", 4) if initial_hand_size is None else initial_hand_size
        if not isinstance(hand_size, int) or isinstance(hand_size, bool) or hand_size < 1:
            raise InvalidOperation("initial_hand_size must be a positive integer")

        state: dict[str, Any] = {
            "schema_version": 7,
            "match_id": match_id,
            "state_revision": 0,
            "event_watermark": 0,
            "status": "active",
            "definition_manifest": self.catalog.definition_manifest(),
            "players": {},
            "instances": {},
        }
        for player_id in normalized_players:
            deck_ids = decks.get(player_id, decks.get(int(player_id)))
            if not isinstance(deck_ids, Sequence) or isinstance(deck_ids, (str, bytes)):
                raise InvalidOperation(f"deck list is missing or invalid for player {player_id}")
            if len(deck_ids) < hand_size:
                raise InvalidOperation(f"player {player_id} deck must contain at least {hand_size} cards")
            leader_id = None
            if leaders is not None:
                leader_id = leaders.get(player_id, leaders.get(int(player_id)))
            leader_definition = self.catalog.leader_registry.get(leader_id) if leader_id else None
            if leader_id and leader_definition is None:
                raise InvalidOperation(f"unknown alpha leader for player {player_id}: {leader_id}")
            faction_id = None
            if player_factions is not None:
                faction_id = player_factions.get(player_id, player_factions.get(int(player_id)))
            if leader_definition is not None:
                leader_faction = leader_definition["faction_id"]
                if faction_id is not None and faction_id != leader_faction:
                    raise InvalidOperation(f"leader {leader_id} does not belong to player faction {faction_id}")
                faction_id = leader_faction if faction_id is None else faction_id
            if faction_id is not None and faction_id not in self.catalog.faction_passives:
                raise InvalidOperation(f"unknown alpha player faction for {player_id}: {faction_id}")
            player_zones = {"hand": [], "draw_pile": [], "board": [], "discard": []}
            state["players"][player_id] = {
                "zones": player_zones,
                "faction_id": faction_id,
                "leader_id": leader_id,
                "leader_used": False,
                "round_state": {
                    "last_unit_play_row": None,
                    "faction_passive_used": False,
                    "synergy_used": {},
                },
                "counters": {"board_removal_count": 0, "sacrifice_count": 0},
            }
            player_exemplar_slots = None
            if exemplar_slots_by_player is not None:
                player_exemplar_slots = exemplar_slots_by_player.get(
                    player_id, exemplar_slots_by_player.get(int(player_id))
                )
                if not isinstance(player_exemplar_slots, Sequence) or isinstance(player_exemplar_slots, (str, bytes)):
                    raise InvalidOperation(f"exemplar slots missing for player {player_id}")
                if len(player_exemplar_slots) != len(deck_ids):
                    raise InvalidOperation(f"exemplar slots do not align with deck for player {player_id}")
            for index, card_id in enumerate(deck_ids):
                definition = self.catalog.definition_for(card_id)
                exemplar_slot = player_exemplar_slots[index] if player_exemplar_slots is not None else None
                if exemplar_slot is not None:
                    if not isinstance(exemplar_slot, Mapping) or exemplar_slot.get("card_id") != card_id:
                        raise InvalidOperation("shuffled exemplar slot does not match its card model")
                    origin_type = "deck_exemplar"
                    exemplar_id = exemplar_slot.get("exemplar_id")
                    exemplar_snapshot = exemplar_slot.get("exemplar_snapshot")
                else:
                    origin_type = "catalog_deck"
                    exemplar_id = None
                    exemplar_snapshot = None
                instance = make_card_instance(
                    card_id=card_id,
                    owner_player_id=player_id,
                    origin_type=origin_type,
                    definition_snapshot=definition,
                    exemplar_id=exemplar_id,
                    exemplar_snapshot=exemplar_snapshot,
                    initial_row=None,
                )
                instance_id = instance["instance_id"]
                state["instances"][instance_id] = instance
                zone = "hand" if index < hand_size else "draw_pile"
                player_zones[zone].append(instance_id)
        validate_match_state(state)
        runtime = {
            "runtime_version": 1,
            "phase": "round",
            "round_number": 1,
            "round_starter_player_id": starter,
            "current_player_id": starter,
            "passed_player_ids": [],
            "round_wins": {player_id: 0 for player_id in normalized_players},
            "life_by_player": {
                player_id: int(self.catalog.ruleset.get("starting_player_life", DEFAULT_STARTING_LIFE))
                for player_id in normalized_players
            },
            "match_winner_player_id": None,
            "best_of": int(self.catalog.ruleset.get("best_of", 3)),
            "max_rounds": int(self.catalog.ruleset.get("maximum_rounds", 3)),
            "draw_per_round": int(self.catalog.ruleset.get("draw_per_new_round", 2)),
            "turn_number": 0,
            "maximum_energy": int(self.catalog.energy_economy["maximum_energy"]),
            "energy_by_player": {
                player_id: (
                    min(
                        int(self.catalog.energy_economy["maximum_energy"]),
                        int(self.catalog.energy_economy["starting_energy"])
                        + int(self.catalog.energy_economy["energy_gain_per_turn"]),
                    )
                    if player_id == starter
                    else int(self.catalog.energy_economy["starting_energy"])
                )
                for player_id in normalized_players
            },
            "energy_turns_started_by_player": {
                player_id: (1 if player_id == starter else 0)
                for player_id in normalized_players
            },
            "card_ability_uses_by_instance": {},
            "deck_fatigue_count_by_player": {player_id: 0 for player_id in normalized_players},
            # The opening player's first turn begins with match setup. The
            # second player's first turn begins on the first turn transition.
            # Both initial turns are exempt from fatigue accounting.
            "initial_turn_exemption_pending_by_player": {
                player_id: player_id != starter for player_id in normalized_players
            },
            "weather_by_row": {row: 0 for row in ROWS},
            "round_history": [],
            "match_setup": dict(match_setup_metadata) if match_setup_metadata is not None else {
                "mode": "internal_test_harness",
                "deck_validation": "bypassed_for_deterministic_fixture",
            },
        }
        self.repository.create_match(state, runtime_state=runtime)

    def create_competitive_match(
        self,
        *,
        match_id: int,
        player_ids: Sequence[str | int],
        decks: Mapping[str | int, Sequence[str]],
        exemplar_ids_by_player: Mapping[str | int, Sequence[int]],
        owned_exemplars_by_player: Mapping[
            str | int, Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]]
        ],
        player_factions: Mapping[str | int, str] | None = None,
        leaders: Mapping[str | int, str] | None = None,
        shuffle_seeds_by_player: Mapping[str | int, int | str | bytes] | None = None,
        starting_player_seed: int | str | bytes | None = None,
    ) -> dict[str, Any]:
        """Create a strict 30-card match from exact, server-verified exemplars.

        The deck list and exemplar IDs are shuffled as paired slots. Per-copy
        power and rarity classification are frozen from the current collection
        record; only power is mechanical, while rarity remains display metadata.
        """
        from .deck_builder import AlphaDeckBuilder, INITIAL_HAND_SIZE

        normalized_players = [str(item) for item in player_ids]
        if len(normalized_players) != 2 or len(set(normalized_players)) != 2:
            raise InvalidOperation("competitive alpha match requires exactly two distinct players")
        builder = AlphaDeckBuilder(self.catalog)
        # Real matchmaking omits the seed and uses OS-backed randomness. Seeds
        # are available only to the low-level simulation/test interface.
        starter_rng = random.SystemRandom() if starting_player_seed is None else random.Random(starting_player_seed)
        starting_player_id = starter_rng.choice(normalized_players)
        prepared_decks: dict[str, tuple[str, ...]] = {}
        prepared_exemplar_slots: dict[str, tuple[dict[str, Any], ...]] = {}
        reports: dict[str, dict[str, Any]] = {}
        selected_exemplar_ids: set[int] = set()

        def _lookup(mapping: Mapping[str | int, Any] | None, player_id: str) -> Any:
            if mapping is None:
                return None
            return mapping.get(player_id, mapping.get(int(player_id)))

        for player_id in normalized_players:
            deck_ids = _lookup(decks, player_id)
            exemplar_ids = _lookup(exemplar_ids_by_player, player_id)
            owned_exemplars = _lookup(owned_exemplars_by_player, player_id)
            if not isinstance(deck_ids, Sequence) or isinstance(deck_ids, (str, bytes)):
                raise InvalidOperation(f"deck list is missing or invalid for player {player_id}")
            if not isinstance(exemplar_ids, Sequence) or isinstance(exemplar_ids, (str, bytes)):
                raise InvalidOperation(f"exact exemplar IDs are required for player {player_id}")
            if not isinstance(owned_exemplars, (Mapping, Sequence)) or isinstance(owned_exemplars, (str, bytes)):
                raise InvalidOperation(f"owned exemplar inventory is required for player {player_id}")
            leader_id = _lookup(leaders, player_id)
            faction_id = _lookup(player_factions, player_id)
            seed = _lookup(shuffle_seeds_by_player, player_id)
            prepared_slots = builder.prepare_exemplar_slots(
                deck_ids,
                exemplar_ids,
                owner_player_id=player_id,
                owned_exemplars=owned_exemplars,
                shuffle_seed=seed,
                leader_id=leader_id,
                faction_id=faction_id,
            )
            for slot in prepared_slots:
                exemplar_id = int(slot["exemplar_id"])
                if exemplar_id in selected_exemplar_ids:
                    raise InvalidOperation(f"exemplar_id_used_by_multiple_players:{exemplar_id}")
                selected_exemplar_ids.add(exemplar_id)
            prepared_exemplar_slots[player_id] = prepared_slots
            prepared_decks[player_id] = tuple(slot["card_id"] for slot in prepared_slots)
            reports[player_id] = builder.require_valid(
                deck_ids,
                exemplar_ids=exemplar_ids,
                owned_exemplars=owned_exemplars,
                owner_player_id=player_id,
                leader_id=leader_id,
                faction_id=faction_id,
            ).to_dict()

        self.create_match(
            match_id=match_id,
            player_ids=normalized_players,
            decks=prepared_decks,
            initial_hand_size=INITIAL_HAND_SIZE,
            player_factions=player_factions,
            leaders=leaders,
            exemplar_slots_by_player=prepared_exemplar_slots,
            match_setup_metadata={
                "mode": "competitive_alpha",
                "deck_rules_version": "soulsbo-alpha-deck-rules-v0.2-exemplar-provenance",
                "deck_size": 30,
                "maximum_copies_per_card": 3,
                "initial_hand_size": INITIAL_HAND_SIZE,
                "server_shuffled": True,
                "owned_inventory_checked": True,
                "exact_exemplar_provenance_checked": True,
                "exemplar_snapshot_policy": "current_power_and_display_rarity_at_match_creation_v1",
                "first_player_selection": "server_random",
                "starting_player_id": starting_player_id,
            },
            starting_player_id=starting_player_id,
        )
        return {
            "match_id": match_id,
            "rules_version": "soulsbo-alpha-deck-rules-v0.2-exemplar-provenance",
            "initial_hand_size": INITIAL_HAND_SIZE,
            "deck_reports": reports,
            "shuffled_by_server": True,
            "starting_player_id": starting_player_id,
            "first_player_selection": "server_random",
            "exact_exemplar_provenance": True,
            "selected_exemplar_count": len(selected_exemplar_ids),
        }

    def _current(self, runtime: dict[str, Any], actor_id: str) -> bool:
        return (
            runtime.get("phase") == "round"
            and runtime.get("current_player_id") == actor_id
            and actor_id not in runtime.get("passed_player_ids", [])
        )

    @staticmethod
    def _next_actor(runtime: dict[str, Any], actor_id: str, player_ids: list[str]) -> None:
        candidates = [player_id for player_id in player_ids if player_id != actor_id and player_id not in runtime["passed_player_ids"]]
        runtime["current_player_id"] = candidates[0] if candidates else actor_id
        runtime["turn_number"] += 1

    def _apply_turn_start_energy(
        self,
        runtime: dict[str, Any],
        player_id: str | None,
    ) -> list[dict[str, Any]]:
        """Grant the normal +1 energy at the beginning of an individual turn."""
        if (
            runtime.get("phase") != "round"
            or not isinstance(player_id, str)
            or runtime.get("current_player_id") != player_id
        ):
            return []
        rules = self.catalog.energy_economy
        energy_by_player = runtime.setdefault(
            "energy_by_player",
            {candidate_id: int(rules["starting_energy"]) for candidate_id in runtime.get("round_wins", {})},
        )
        before = int(energy_by_player[player_id])
        maximum = int(rules["maximum_energy"])
        requested_gain = int(rules["energy_gain_per_turn"])
        after = min(maximum, before + requested_gain)
        actual_gain = after - before
        energy_by_player[player_id] = after
        turns_started = runtime.setdefault(
            "energy_turns_started_by_player",
            {candidate_id: 0 for candidate_id in runtime.get("round_wins", {})},
        )
        turns_started[player_id] += 1
        return [
            _event(
                "player_energy_gained",
                effect_scope="system",
                payload={
                    "player_id": player_id,
                    "round_number": runtime["round_number"],
                    "turn_number": runtime["turn_number"],
                    "energy_before": before,
                    "requested_gain": requested_gain,
                    "energy_gained": actual_gain,
                    "energy_after": after,
                    "maximum_energy": maximum,
                    "gain_capped": actual_gain < requested_gain,
                    "turns_started": turns_started[player_id],
                },
            )
        ]

    def _apply_turn_start_rules(
        self,
        state: dict[str, Any],
        runtime: dict[str, Any],
        player_id: str | None,
    ) -> list[dict[str, Any]]:
        """Resolve all server-owned effects that happen before a player's action."""
        events = self._apply_turn_start_energy(runtime, player_id)
        events.extend(self._apply_turn_start_fatigue(state, runtime, player_id))
        return events

    def _card_energy_check(
        self,
        runtime: dict[str, Any],
        player_id: str,
        card_id: str,
    ) -> tuple[bool, int | None, int, str | None]:
        """Check an explicit per-card cost; an absent price is rejected by the alpha ruleset."""
        energy = int(runtime.get("energy_by_player", {}).get(player_id, 0))
        cost = self.catalog.energy_cost_for_card(card_id)
        if cost is None:
            return False, None, energy, "card_energy_cost_not_configured"
        if energy < cost:
            return False, cost, energy, "insufficient_energy"
        return True, cost, energy, None

    def _leader_energy_check(
        self,
        runtime: dict[str, Any],
        player_id: str,
        leader_id: str,
    ) -> tuple[bool, int | None, int, str | None]:
        energy = int(runtime.get("energy_by_player", {}).get(player_id, 0))
        cost = self.catalog.energy_cost_for_leader(leader_id)
        if cost is None:
            return False, None, energy, "leader_energy_cost_not_configured"
        if energy < cost:
            return False, cost, energy, "insufficient_energy"
        return True, cost, energy, None

    def _ability_energy_check(
        self, runtime: dict[str, Any], player_id: str, ability_id: str
    ) -> tuple[bool, int | None, int, str | None]:
        energy = int(runtime.get("energy_by_player", {}).get(player_id, 0))
        cost = self.catalog.energy_cost_for_ability(ability_id)
        if cost is None:
            return False, None, energy, "ability_energy_cost_not_configured"
        if energy < cost:
            return False, cost, energy, "insufficient_energy"
        return True, cost, energy, None

    def _spend_energy(
        self,
        runtime: dict[str, Any],
        player_id: str,
        *,
        amount: int | None,
        source_kind: str,
        source_id: str,
        action: str,
        caused_by_event_ids: list[str] | None = None,
        source_instance_id: str | None = None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """Spend only an explicit configured cost and return event/result metadata."""
        energy_by_player = runtime["energy_by_player"]
        before = int(energy_by_player[player_id])
        if amount is None:
            return None, {
                "energy_spent": 0,
                "energy_cost_configured": False,
                "energy_remaining": before,
            }
        if amount < 0 or before < amount:
            raise InvalidOperation("energy payment is invalid after action validation")
        after = before - amount
        energy_by_player[player_id] = after
        event = _event(
            "player_energy_spent",
            effect_scope="system",
            source_instance_id=(source_id if source_kind == "card" else source_instance_id),
            caused_by_event_ids=caused_by_event_ids or [],
            payload={
                "player_id": player_id,
                "source_kind": source_kind,
                "source_id": source_id,
                "action": action,
                "energy_before": before,
                "energy_spent": amount,
                "energy_after": after,
            },
        )
        return event, {
            "energy_spent": amount,
            "energy_cost_configured": True,
            "energy_remaining": after,
        }

    def _apply_turn_start_fatigue(
        self,
        state: dict[str, Any],
        runtime: dict[str, Any],
        player_id: str | None,
    ) -> list[dict[str, Any]]:
        """Apply the pinned alpha fatigue policy before the active player acts.

        Fatigue is checked once whenever an individual player's turn starts.
        The initial deal gives each player one exempt opening turn. Once that
        exemption is consumed, an empty draw pile causes 1, 2, 3... life damage
        on successive fatigue triggers. The per-player counter never resets.
        """
        if (
            runtime.get("phase") != "round"
            or not isinstance(player_id, str)
            or runtime.get("current_player_id") != player_id
        ):
            return []

        initial_exemptions = runtime.setdefault(
            "initial_turn_exemption_pending_by_player",
            {candidate_id: False for candidate_id in state["players"]},
        )
        if initial_exemptions.get(player_id, False):
            initial_exemptions[player_id] = False
            return []

        if state["players"][player_id]["zones"]["draw_pile"]:
            return []

        rules = self.catalog.ruleset["deck_fatigue"]
        counts = runtime.setdefault(
            "deck_fatigue_count_by_player",
            {candidate_id: 0 for candidate_id in state["players"]},
        )
        previous_count = counts[player_id]
        fatigue_count = previous_count + 1
        damage = rules["initial_damage"] + previous_count * rules["damage_increment"]
        if rules["maximum_damage"] is not None:
            damage = min(damage, rules["maximum_damage"])
        counts[player_id] = fatigue_count

        life_before = runtime["life_by_player"][player_id]
        life_result = apply_life_damage({player_id: life_before}, {player_id: damage})
        change = life_result["life_changes"][player_id]
        runtime["life_by_player"][player_id] = change["life_after"]

        fatigue_event = _event(
            "deck_fatigue_applied",
            effect_scope="system",
            payload={
                "player_id": player_id,
                "round_number": runtime["round_number"],
                "turn_number": runtime["turn_number"],
                "fatigue_count": fatigue_count,
                "damage": damage,
                "life_before": life_before,
                "life_after": change["life_after"],
                "draw_pile_count": 0,
                "initial_damage": rules["initial_damage"],
                "damage_increment": rules["damage_increment"],
                "maximum_damage": rules["maximum_damage"],
            },
        )
        damage_event = _event(
            "player_damage_applied",
            effect_scope="system",
            caused_by_event_ids=[fatigue_event["event_id"]],
            payload={
                "round_number": runtime["round_number"],
                "turn_number": runtime["turn_number"],
                "player_id": player_id,
                **change,
                "damage_source": "deck_fatigue",
                "fatigue_count": fatigue_count,
            },
        )
        events = [fatigue_event, damage_event]

        if life_result["defeated_player_ids"]:
            opponent_id = next(candidate_id for candidate_id in state["players"] if candidate_id != player_id)
            defeated_event = _event(
                "player_defeated",
                effect_scope="system",
                caused_by_event_ids=[damage_event["event_id"]],
                payload={
                    "round_number": runtime["round_number"],
                    "turn_number": runtime["turn_number"],
                    "player_id": player_id,
                    "reason": "deck_fatigue",
                },
            )
            state["status"] = "finished"
            runtime["phase"] = "finished"
            runtime["current_player_id"] = None
            runtime["match_winner_player_id"] = opponent_id
            runtime["match_finish_reason"] = "deck_fatigue"
            finished_event = _event(
                "match_finished",
                effect_scope="system",
                caused_by_event_ids=[defeated_event["event_id"]],
                payload={
                    "round_wins": copy.deepcopy(runtime["round_wins"]),
                    "winner_player_id": opponent_id,
                    "finish_reason": "deck_fatigue",
                    "life_by_player": copy.deepcopy(runtime["life_by_player"]),
                    "deck_fatigue_count_by_player": copy.deepcopy(counts),
                },
            )
            events.extend([defeated_event, finished_event])

        return events

    def _make_request(
        self,
        *,
        actor_id: str,
        expected_revision: int,
        action_type: str,
        payload: dict[str, Any],
        operation_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "operation_id": operation_id or str(uuid.uuid4()),
            "actor": {"type": "player", "player_id": actor_id},
            "expected_revision": expected_revision,
            "action_type": action_type,
            "payload": copy.deepcopy(payload),
        }

    def target_offer(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        source_instance_id: str,
        selected_row: str | None = None,
    ) -> dict[str, Any]:
        actor_id = str(actor_player_id)
        state = self.repository.get_match(match_id)
        runtime = self.repository.get_match_runtime(match_id)
        if not self._current(runtime, actor_id):
            raise InvalidOperation("target offer is available only to the current active player")
        if source_instance_id not in state["instances"]:
            raise InvalidOperation("source instance does not exist")
        source_owner, source_zone = locate_instance(state, source_instance_id)
        if source_owner != actor_id or source_zone != "hand":
            raise InvalidOperation("source card must be in the actor's hand")
        source_effect_id = state["instances"][source_instance_id]["definition_snapshot"].get("effect_id")
        if source_effect_id == "gwent_egide":
            policy = self.ally_policy
        elif source_effect_id == "gwent_execucao":
            policy = self.execution_policy
            if selected_row not in ROWS:
                raise InvalidOperation("execution offer requires selected_row")
        else:
            raise InvalidOperation("this alpha special does not require a target identity offer")
        offer = build_target_offer(
            state,
            actor_player_id=actor_id,
            policy=policy,
            source_instance_id=source_instance_id,
            selected_row=selected_row,
            metric_resolver=metric_resolver_for_weather(runtime["weather_by_row"]),
        )
        for candidate in offer["candidates"]:
            target_instance = state["instances"][candidate["target_instance_id"]]
            candidate["display_name"] = self.catalog.display_name(target_instance["card_id"])
        offer["weather_by_row"] = copy.deepcopy(runtime["weather_by_row"])
        return offer

    def sacrifice_target_offer(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
    ) -> dict[str, Any]:
        """Return a revision-bound, server-authoritative offer for allied sacrifice."""
        actor_id = str(actor_player_id)
        runtime = self.repository.get_match_runtime(match_id)
        if not self._current(runtime, actor_id):
            raise InvalidOperation("sacrifice offer is available only to the current active player")
        resolver = self._resolver_for_runtime(runtime)
        offer = resolver.target_offer_for_action(
            self.repository,
            match_id,
            actor_player_id=actor_id,
            action_type="unit.sacrifice",
        )
        state = self.repository.get_match(match_id)
        for candidate in offer["candidates"]:
            target = state["instances"][candidate["target_instance_id"]]
            candidate["display_name"] = self.catalog.display_name(target["card_id"])
        offer["weather_by_row"] = copy.deepcopy(runtime["weather_by_row"])
        return offer

    def sacrifice_unit(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        target_instance_id: str,
        expected_revision: int,
        operation_id: str | None = None,
    ) -> OperationReceipt:
        """Sacrifice one allied board unit as a normal, turn-consuming action.

        The target must come from the latest `sacrifice_target_offer`; the
        repository enforces that offer's revision with CAS. Sacrifice is
        resolved by GameplayResolver so protection bypass, counters and
        Vingança retain their canonical semantics.
        """
        actor_id = str(actor_player_id)
        if not isinstance(target_instance_id, str) or not is_uuid4(target_instance_id):
            raise InvalidOperation("target_instance_id must be UUIDv4")
        if not isinstance(expected_revision, int) or isinstance(expected_revision, bool) or expected_revision < 0:
            raise InvalidOperation("expected_revision must be a non-negative integer from the latest target offer")

        request = self._make_request(
            actor_id=actor_id,
            expected_revision=expected_revision,
            action_type="match.sacrifice_unit",
            payload={
                "cause_id": "sacrifice",
                "selection": {"mode": "manual_single", "target_instance_id": target_instance_id},
            },
            operation_id=operation_id,
        )
        event_sequence_by_id = {
            event["event_id"]: event["sequence"]
            for event in self.repository.get_events(match_id)
        }

        def handler(working: dict[str, Any], body: dict[str, Any]) -> HandlerResult:
            runtime = copy.deepcopy(body["_runtime_context"])
            if not self._current(runtime, actor_id):
                return HandlerResult(outcome="rejected", state=working, reason_code="not_current_player")

            internal_request = copy.deepcopy(body)
            internal_request["action_type"] = "unit.sacrifice"
            resolver = self._resolver_for_runtime(runtime)
            result = resolver.handle(
                working,
                internal_request,
                event_sequence_by_id=event_sequence_by_id,
            )
            if result.outcome == "rejected":
                return result

            resolved_state = result.state or working
            events = list(result.events)
            self._next_actor(runtime, actor_id, list(resolved_state["players"].keys()))
            events.append(
                _event(
                    "turn_action_completed",
                    effect_scope="system",
                    source_effect_id="effect.sacrifice_unit",
                    target_instance_ids=[target_instance_id],
                    caused_by_event_ids=[events[-1]["event_id"]] if events else [],
                    payload={
                        "player_id": actor_id,
                        "action": "sacrifice_unit",
                        "cause_id": "sacrifice",
                        "turn_number": runtime["turn_number"],
                    },
                )
            )
            events.extend(
                self._apply_turn_start_rules(
                    resolved_state, runtime, runtime.get("current_player_id")
                )
            )
            costs = copy.deepcopy(result.costs)
            costs["turn_consumed"] = True
            costs["energy_spent"] = 0
            costs["energy_cost_configured"] = False
            costs["energy_remaining"] = int(runtime.get("energy_by_player", {}).get(actor_id, 0))
            return HandlerResult(
                outcome=result.outcome,
                state=resolved_state,
                target_results=result.target_results,
                costs=costs,
                reason_code=result.reason_code,
                events=events,
                rewards=result.rewards,
                outbox=result.outbox,
                runtime_state=runtime,
            )

        return self.repository.execute_operation(match_id, request, handler)

    def play_unit(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        instance_id: str,
        expected_revision: int | None = None,
        operation_id: str | None = None,
    ) -> OperationReceipt:
        actor_id = str(actor_player_id)
        state = self.repository.get_match(match_id)
        revision = state["state_revision"] if expected_revision is None else expected_revision
        request = self._make_request(
            actor_id=actor_id,
            expected_revision=revision,
            action_type="match.play_unit",
            payload={"instance_id": instance_id},
            operation_id=operation_id,
        )
        event_sequence_by_id = {event["event_id"]: event["sequence"] for event in self.repository.get_events(match_id)}

        def handler(working: dict[str, Any], body: dict[str, Any]) -> HandlerResult:
            return self._handle_play_unit(working, body, event_sequence_by_id)

        return self.repository.execute_operation(match_id, request, handler)

    def _handle_play_unit(
        self, state: dict[str, Any], request: dict[str, Any], event_sequence_by_id: dict[str, int]
    ) -> HandlerResult:
        actor_id = request["actor"]["player_id"]
        runtime = copy.deepcopy(request["_runtime_context"])
        if not self._current(runtime, actor_id):
            return HandlerResult(outcome="rejected", state=state, reason_code="not_current_player")
        instance_id = request["payload"].get("instance_id")
        if not is_uuid4(instance_id) or instance_id not in state["instances"]:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_card_instance")
        try:
            owner_id, zone = locate_instance(state, instance_id)
        except Exception:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_card_zone")
        if owner_id != actor_id or zone != "hand":
            return HandlerResult(outcome="rejected", state=state, reason_code="unit_not_in_actor_hand")
        instance = state["instances"][instance_id]
        snapshot = instance["definition_snapshot"]
        if snapshot["kind"] != "unit":
            return HandlerResult(outcome="rejected", state=state, reason_code="card_is_not_a_unit")
        energy_ok, energy_cost, available_energy, energy_error = self._card_energy_check(
            runtime, actor_id, instance["card_id"]
        )
        if not energy_ok:
            return HandlerResult(outcome="rejected", state=state, reason_code=energy_error)
        row = snapshot["printed_row"]
        if row not in ROWS:
            return HandlerResult(outcome="rejected", state=state, reason_code="unit_has_no_printed_row")
        other_player_ids = [player_id for player_id in state["players"] if player_id != actor_id]
        if len(other_player_ids) != 1:
            return HandlerResult(outcome="rejected", state=state, reason_code="alpha_requires_two_players")
        previous_own_last_row = state["players"][actor_id]["round_state"].get("last_unit_play_row")
        previous_opponent_last_row = state["players"][other_player_ids[0]]["round_state"].get("last_unit_play_row")
        golden_vow_params = None
        if snapshot.get("effect_id") == "v75_golden_vow":
            golden_vow_params = snapshot.get("effect_params", {})
            if (
                not isinstance(golden_vow_params.get("self_bonus"), int)
                or isinstance(golden_vow_params.get("self_bonus"), bool)
                or not isinstance(golden_vow_params.get("weakest_same_row_ally_bonus"), int)
                or isinstance(golden_vow_params.get("weakest_same_row_ally_bonus"), bool)
            ):
                return HandlerResult(outcome="rejected", state=state, reason_code="invalid_v75_golden_vow_params")

        transition = transition_instance_zone(state, instance_id, "board", target_row=row)
        state["players"][actor_id]["round_state"]["last_unit_play_row"] = row
        played_event = _event(
            "unit_played",
            effect_scope="system",
            source_effect_id=snapshot.get("effect_id"),
            source_instance_id=instance_id,
            target_instance_ids=[instance_id],
            payload={"owner_player_id": actor_id, "row": row, "transition": transition},
        )
        events = [played_event]

        if golden_vow_params is not None:
            self_amount = golden_vow_params["self_bonus"]
            ally_amount = golden_vow_params["weakest_same_row_ally_bonus"]
            same_row_allies = [
                candidate_id
                for candidate_id in state["players"][actor_id]["zones"]["board"]
                if candidate_id != instance_id
                and state["instances"][candidate_id]["state"].get("current_row") == row
            ]
            weather = runtime["weather_by_row"]
            same_row_allies.sort(
                key=lambda candidate_id: (
                    effective_power(state, state["instances"][candidate_id], weather),
                    state["players"][actor_id]["zones"]["board"].index(candidate_id),
                )
            )
            bonus_targets = [(instance_id, self_amount)]
            if same_row_allies:
                bonus_targets.append((same_row_allies[0], ally_amount))
            bonus_event = _event(
                "golden_vow_resolved",
                effect_scope="direct",
                source_effect_id="v75_golden_vow",
                source_instance_id=instance_id,
                target_instance_ids=[target_id for target_id, _amount in bonus_targets],
                caused_by_event_ids=[played_event["event_id"]],
                payload={
                    "grants": [
                        {"target_instance_id": target_id, "amount": amount, "expires_on": "round_close"}
                        for target_id, amount in bonus_targets
                    ],
                    "clamp_policy_id": ALPHA_RAW_GRANT_POLICY,
                },
            )
            for target_id, amount in bonus_targets:
                state["instances"][target_id]["state"]["bonus_grants"].append(
                    {
                        "grant_id": str(uuid.uuid4()),
                        "amount": amount,
                        "source_effect_id": "v75_golden_vow",
                        "source_instance_id": instance_id,
                        "applied_event_id": bonus_event["event_id"],
                        "expires_on": "round_close",
                        "clamp_policy_id": ALPHA_RAW_GRANT_POLICY,
                    }
                )
            events.append(bonus_event)

        entry_effect_event = resolve_unit_entry_effect(
            state,
            runtime,
            instance_id=instance_id,
            player_id=actor_id,
            previous_own_last_row=previous_own_last_row,
            previous_opponent_last_row=previous_opponent_last_row,
            played_event_id=played_event["event_id"],
        )
        if entry_effect_event is not None:
            events.append(entry_effect_event)

        combo_event = resolve_combo_for_play(
            state,
            player_id=actor_id,
            current_instance_id=instance_id,
            played_event_id=played_event["event_id"],
            combo_registry=self.catalog.combo_registry,
        )
        if combo_event is not None:
            events.append(combo_event)

        passive_event = resolve_faction_passive_for_play(
            state,
            player_id=actor_id,
            current_instance_id=instance_id,
            played_event_id=played_event["event_id"],
            passive_registry=self.catalog.faction_passives,
        )
        if passive_event is not None:
            events.append(passive_event)

        energy_event, energy_costs = self._spend_energy(
            runtime,
            actor_id,
            amount=energy_cost,
            source_kind="card",
            source_id=instance_id,
            action="play_unit",
            caused_by_event_ids=[played_event["event_id"]],
        )
        if energy_event is not None:
            events.append(energy_event)
        self._next_actor(runtime, actor_id, list(state["players"].keys()))
        events.append(
            _event(
                "turn_action_completed",
                effect_scope="system",
                source_instance_id=instance_id,
                target_instance_ids=[instance_id],
                caused_by_event_ids=[events[-1]["event_id"]],
                payload={"player_id": actor_id, "action": "play_unit", "turn_number": runtime["turn_number"]},
            )
        )
        events.extend(
            self._apply_turn_start_rules(state, runtime, runtime.get("current_player_id"))
        )
        return HandlerResult(
            outcome="applied",
            state=state,
            target_results=[{"target_instance_id": instance_id, "outcome": "applied"}],
            costs={"turn_consumed": True, **energy_costs},
            events=events,
            runtime_state=runtime,
        )

    def play_special(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        source_instance_id: str,
        selected_row: str | None = None,
        selection: dict[str, Any] | None = None,
        expected_revision: int | None = None,
        operation_id: str | None = None,
    ) -> OperationReceipt:
        actor_id = str(actor_player_id)
        state = self.repository.get_match(match_id)
        source_effect_id = (
            state.get("instances", {}).get(source_instance_id, {}).get("definition_snapshot", {}).get("effect_id")
            if isinstance(source_instance_id, str)
            else None
        )
        if source_effect_id in ("gwent_egide", "gwent_execucao") and expected_revision is None:
            raise InvalidOperation("targeted specials require expected_revision from the latest server target offer")
        revision = state["state_revision"] if expected_revision is None else expected_revision
        request = self._make_request(
            actor_id=actor_id,
            expected_revision=revision,
            action_type="match.play_special",
            payload={
                "source_instance_id": source_instance_id,
                "selected_row": selected_row,
                "selection": copy.deepcopy(selection or {}),
            },
            operation_id=operation_id,
        )
        event_sequence_by_id = {event["event_id"]: event["sequence"] for event in self.repository.get_events(match_id)}

        def handler(working: dict[str, Any], body: dict[str, Any]) -> HandlerResult:
            return self._handle_play_special(working, body, event_sequence_by_id)

        return self.repository.execute_operation(match_id, request, handler)

    def _handle_play_special(
        self, state: dict[str, Any], request: dict[str, Any], event_sequence_by_id: dict[str, int]
    ) -> HandlerResult:
        actor_id = request["actor"]["player_id"]
        runtime = copy.deepcopy(request["_runtime_context"])
        if not self._current(runtime, actor_id):
            return HandlerResult(outcome="rejected", state=state, reason_code="not_current_player")
        payload = request["payload"]
        source_id = payload.get("source_instance_id")
        if not is_uuid4(source_id) or source_id not in state["instances"]:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_source_instance")
        try:
            owner_id, zone = locate_instance(state, source_id)
        except Exception:
            return HandlerResult(outcome="rejected", state=state, reason_code="invalid_source_zone")
        if owner_id != actor_id or zone != "hand":
            return HandlerResult(outcome="rejected", state=state, reason_code="special_not_in_actor_hand")
        source = state["instances"][source_id]
        snapshot = source["definition_snapshot"]
        if snapshot["kind"] != "special":
            return HandlerResult(outcome="rejected", state=state, reason_code="card_is_not_special")
        energy_ok, energy_cost, available_energy, energy_error = self._card_energy_check(
            runtime, actor_id, source["card_id"]
        )
        if not energy_ok:
            return HandlerResult(outcome="rejected", state=state, reason_code=energy_error)
        effect_id = snapshot.get("effect_id")
        weather = runtime["weather_by_row"]
        resolver = self._resolver_for_runtime(runtime)

        if effect_id == "gwent_egide":
            internal_request = copy.deepcopy(request)
            internal_request["action_type"] = "unit.grant_protection"
            result = resolver.handle(state, internal_request, event_sequence_by_id=event_sequence_by_id)
            if result.outcome == "rejected":
                return result
            consumed = self._consume_special_source(
                result.state or state, source_id, actor_id, "gwent_egide", caused_by_event_ids=[event["event_id"] for event in result.events]
            )
            if consumed is None:
                return HandlerResult(outcome="rejected", state=state, reason_code="special_source_not_consumable")
            events = [*result.events, consumed]
            return self._finish_special_result(result, state, runtime, actor_id, source_id, events)

        if effect_id == "gwent_execucao":
            internal_request = copy.deepcopy(request)
            internal_request["action_type"] = "unit.remove"
            internal_request["payload"]["cause_id"] = "execution"
            result = resolver.handle(state, internal_request, event_sequence_by_id=event_sequence_by_id)
            if result.outcome == "rejected":
                return result
            return self._finish_special_result(result, state, runtime, actor_id, source_id, result.events)

        if effect_id == "gwent_clima":
            row = payload.get("selected_row")
            if row not in ROWS:
                return HandlerResult(outcome="rejected", state=state, reason_code="weather_requires_valid_row")
            penalty = int(self.catalog.effect_allowlist[effect_id]["params"]["penalty"])
            if weather[row] == penalty:
                outcome = "consumed_no_effect"
                applied_events = [
                    _event(
                        "weather_reapplied_no_change",
                        source_effect_id=effect_id,
                        source_instance_id=source_id,
                        payload={"row": row, "penalty": penalty},
                    )
                ]
            else:
                runtime["weather_by_row"][row] = penalty
                outcome = "applied"
                applied_events = [
                    _event(
                        "weather_applied",
                        source_effect_id=effect_id,
                        source_instance_id=source_id,
                        payload={"row": row, "penalty": penalty, "expires_on": "round_close"},
                    )
                ]
            consumed = self._consume_special_source(state, source_id, actor_id, effect_id, caused_by_event_ids=[applied_events[0]["event_id"]])
            if consumed is None:
                return HandlerResult(outcome="rejected", state=state, reason_code="special_source_not_consumable")
            return self._finish_special_result(
                HandlerResult(outcome=outcome, state=state, events=[*applied_events, consumed], costs={"source_consumed": True}),
                state,
                runtime,
                actor_id,
                source_id,
                [*applied_events, consumed],
            )

        if effect_id == "gwent_geada_cariana":
            row = payload.get("selected_row")
            if row not in ROWS:
                return HandlerResult(outcome="rejected", state=state, reason_code="frost_requires_valid_row")
            status_id = "status.frost"
            applied: list[str] = []
            target_results: list[dict[str, Any]] = []
            enemy_ids = [
                instance_id
                for player_id, player in state["players"].items()
                if player_id != actor_id
                for instance_id in player["zones"]["board"]
                if state["instances"][instance_id]["state"].get("current_row") == row
            ]
            max_marks = int(self.catalog.effect_allowlist[effect_id]["params"]["maximum_marks"])
            marks_per_target = int(self.catalog.effect_allowlist[effect_id]["params"]["marks_per_target"])
            for target_id in enemy_ids:
                instance = state["instances"][target_id]
                existing = status_counts(instance)[status_id]
                add_count = min(marks_per_target, max(0, max_marks - existing))
                if add_count:
                    applied.append(target_id)
                    target_results.append({"target_instance_id": target_id, "outcome": "applied", "marks_added": add_count})
                else:
                    target_results.append({"target_instance_id": target_id, "outcome": "skipped", "reason_code": "status_at_maximum"})
            status_event = _event(
                "status_applied" if applied else "status_application_no_effect",
                source_effect_id=effect_id,
                source_instance_id=source_id,
                target_instance_ids=applied,
                payload={"status_id": status_id, "marks_per_target": marks_per_target, "maximum_marks": max_marks, "expires_on": "round_close"},
            )
            for target_id in applied:
                instance = state["instances"][target_id]
                existing = status_counts(instance)[status_id]
                add_count = min(marks_per_target, max(0, max_marks - existing))
                for _ in range(add_count):
                    instance["state"]["status_applications"].append(
                        {
                            "application_id": str(uuid.uuid4()),
                            "status_id": status_id,
                            "source_effect_id": effect_id,
                            "source_instance_id": source_id,
                            "applied_event_id": status_event["event_id"],
                            "expires_on": "round_close",
                        }
                    )
            consumed = self._consume_special_source(state, source_id, actor_id, effect_id, caused_by_event_ids=[status_event["event_id"]])
            if consumed is None:
                return HandlerResult(outcome="rejected", state=state, reason_code="special_source_not_consumable")
            outcome = "applied" if applied and len(applied) == len(enemy_ids) else "partial" if applied else "consumed_no_effect"
            result = HandlerResult(
                outcome=outcome,
                state=state,
                target_results=target_results,
                costs={"source_consumed": True},
                events=[status_event, consumed],
            )
            return self._finish_special_result(result, state, runtime, actor_id, source_id, result.events)

        return HandlerResult(outcome="rejected", state=state, reason_code="special_effect_not_in_alpha_allowlist")

    def _consume_special_source(
        self,
        state: dict[str, Any],
        source_id: str,
        actor_id: str,
        effect_id: str,
        *,
        caused_by_event_ids: list[str],
    ) -> dict[str, Any] | None:
        try:
            owner_id, zone = locate_instance(state, source_id)
            if owner_id != actor_id or zone != "hand":
                return None
            transition = transition_instance_zone(state, source_id, "discard")
        except Exception:
            return None
        return _event(
            "action_source_consumed",
            source_effect_id=effect_id,
            source_instance_id=source_id,
            target_instance_ids=[source_id],
            caused_by_event_ids=caused_by_event_ids,
            payload={"reason": "special_resolved", "transition": transition},
        )

    def _finish_special_result(
        self,
        result: HandlerResult,
        state: dict[str, Any],
        runtime: dict[str, Any],
        actor_id: str,
        source_id: str,
        events: list[dict[str, Any]],
    ) -> HandlerResult:
        if result.outcome == "rejected":
            return result
        resolved_state = result.state or state
        source_card_id = resolved_state["instances"][source_id]["card_id"]
        card_energy_cost = self.catalog.energy_cost_for_card(source_card_id)
        energy_event, energy_costs = self._spend_energy(
            runtime,
            actor_id,
            amount=card_energy_cost,
            source_kind="card",
            source_id=source_id,
            action="play_special",
            caused_by_event_ids=[events[-1]["event_id"]] if events else [],
        )
        events = list(events)
        if energy_event is not None:
            events.append(energy_event)
        self._next_actor(runtime, actor_id, list(state["players"].keys()))
        costs = copy.deepcopy(result.costs)
        costs["turn_consumed"] = True
        costs.update(energy_costs)
        costs.setdefault("source_consumed", True)
        turn_event = _event(
            "turn_action_completed",
            effect_scope="system",
            source_instance_id=source_id,
            target_instance_ids=[source_id],
            caused_by_event_ids=[events[-1]["event_id"]] if events else [],
            payload={"player_id": actor_id, "action": "play_special", "turn_number": runtime["turn_number"]},
        )
        turn_events = self._apply_turn_start_rules(
            resolved_state, runtime, runtime.get("current_player_id")
        )
        return HandlerResult(
            outcome=result.outcome,
            state=resolved_state,
            target_results=result.target_results,
            costs=costs,
            reason_code=result.reason_code,
            events=[*events, turn_event, *turn_events],
            rewards=result.rewards,
            outbox=result.outbox,
            runtime_state=runtime,
        )

    def _manual_ability_resolver(
        self, ability: dict[str, Any], runtime: dict[str, Any]
    ) -> GameplayResolver:
        """Build a resolver from a hash-pinned manual ability definition."""
        policy_data = copy.deepcopy(ability["target_policy"])
        policy = TargetPolicy(**policy_data)
        params = copy.deepcopy(ability["params"])
        action_type = ability["action_type"]
        common = {
            "action_type": action_type,
            "source_effect_id": ability["ability_id"],
            "target_policy_id": policy.policy_id,
            "allowed_source_zones": frozenset({"board"}),
            "source_card_ids": frozenset(ability["source_card_ids"]),
            "no_target_outcome": "consumed_no_effect" if policy.on_no_target == "consume_no_effect" else "rejected",
        }
        if action_type == "unit.grant_bonus":
            action = ActionDefinition(
                **common,
                bonus_amount=params.get("bonus_amount"),
                bonus_expires_on=params.get("bonus_expires_on"),
                bonus_clamp_policy_id=params.get("bonus_clamp_policy_id", ALPHA_RAW_GRANT_POLICY),
            )
        elif action_type == "unit.grant_protection":
            action = ActionDefinition(
                **common,
                protection_profile_id=params.get("protection_profile_id"),
                protection_charges=params.get("protection_charges"),
                protection_expires_on=params.get("protection_expires_on"),
            )
        elif action_type == "unit.move":
            action = ActionDefinition(
                **common,
                allowed_target_rows=frozenset(params.get("allowed_target_rows", [])),
            )
        elif action_type == "unit.remove":
            allowed_causes = frozenset(params.get("allowed_causes", []))
            cause_map = tuple(tuple(item) for item in params.get("cause_target_policy_ids", []))
            action = ActionDefinition(
                **common,
                allowed_causes=allowed_causes,
                cause_target_policy_ids=cause_map,
            )
        else:  # Catalog validation should make this unreachable.
            raise InvalidOperation("unsupported_manual_ability_action")
        return GameplayResolver(
            actions={action.action_type: action},
            target_policies={policy.policy_id: policy},
            protection_profiles=self.resolver.protection_profiles,
            vengeance_clamp_policy_id=self.resolver.vengeance_clamp_policy_id,
            metric_resolver=metric_resolver_for_weather(runtime["weather_by_row"]),
        )

    def card_ability_target_offer(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        source_instance_id: str,
        ability_id: str,
        selected_row: str | None = None,
    ) -> dict[str, Any]:
        """Return a server-built target offer for a registered manual card ability."""
        actor_id = str(actor_player_id)
        state = self.repository.get_match(match_id)
        runtime = self.repository.get_match_runtime(match_id)
        if not self._current(runtime, actor_id):
            raise InvalidOperation("not_current_player")
        ability = self.catalog.activated_abilities.get(ability_id)
        if ability is None:
            raise InvalidOperation("manual_ability_not_registered")
        if not is_uuid4(source_instance_id) or source_instance_id not in state["instances"]:
            raise InvalidOperation("invalid_source_instance")
        owner_id, zone = locate_instance(state, source_instance_id)
        if owner_id != actor_id or zone != "board":
            raise InvalidOperation("ability_source_not_owned_on_board")
        if state["instances"][source_instance_id]["card_id"] not in ability["source_card_ids"]:
            raise InvalidOperation("source_card_not_allowed_for_ability")
        usage_key = f"{source_instance_id}:{ability['ability_id']}"
        uses = runtime.get("card_ability_uses_by_instance", {})
        if int(uses.get(usage_key, 0)) >= int(ability["uses_per_match"]):
            raise InvalidOperation("manual_ability_already_used")
        energy_ok, _ability_cost, _available_energy, energy_error = self._ability_energy_check(
            runtime, actor_id, ability["ability_id"]
        )
        if not energy_ok:
            raise InvalidOperation(energy_error or "ability_energy_unavailable")
        resolver = self._manual_ability_resolver(ability, runtime)
        return resolver.target_offer_for_action(
            self.repository,
            match_id,
            actor_player_id=actor_id,
            action_type=ability["action_type"],
            source_instance_id=source_instance_id,
            selected_row=selected_row,
        )

    def activate_card_ability(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        source_instance_id: str,
        ability_id: str,
        selection: dict[str, Any] | None = None,
        selected_row: str | None = None,
        target_row: str | None = None,
        expected_revision: int | None = None,
        operation_id: str | None = None,
    ) -> OperationReceipt:
        """Activate one explicitly registered manual ability on an owned board unit."""
        actor_id = str(actor_player_id)
        state = self.repository.get_match(match_id)
        revision = state["state_revision"] if expected_revision is None else expected_revision
        request = self._make_request(
            actor_id=actor_id,
            expected_revision=revision,
            action_type="match.activate_card_ability",
            payload={
                "source_instance_id": source_instance_id,
                "ability_id": ability_id,
                "selection": copy.deepcopy(selection or {}),
                "selected_row": selected_row,
                "target_row": target_row,
            },
            operation_id=operation_id,
        )
        event_sequence_by_id = {event["event_id"]: event["sequence"] for event in self.repository.get_events(match_id)}

        def handler(working: dict[str, Any], body: dict[str, Any]) -> HandlerResult:
            runtime = copy.deepcopy(body["_runtime_context"])
            if not self._current(runtime, actor_id):
                return HandlerResult(outcome="rejected", state=working, reason_code="not_current_player")
            ability = self.catalog.activated_abilities.get(body["payload"].get("ability_id"))
            if ability is None:
                return HandlerResult(outcome="rejected", state=working, reason_code="manual_ability_not_registered")
            source_id = body["payload"].get("source_instance_id")
            if not is_uuid4(source_id) or source_id not in working["instances"]:
                return HandlerResult(outcome="rejected", state=working, reason_code="invalid_source_instance")
            try:
                owner_id, zone = locate_instance(working, source_id)
            except InvalidOperation:
                return HandlerResult(outcome="rejected", state=working, reason_code="invalid_source_zone")
            source_card_id = working["instances"][source_id].get("card_id")
            if owner_id != actor_id or zone != "board":
                return HandlerResult(outcome="rejected", state=working, reason_code="ability_source_not_owned_on_board")
            if source_card_id not in ability["source_card_ids"]:
                return HandlerResult(outcome="rejected", state=working, reason_code="source_card_not_allowed_for_ability")

            usage_key = f"{source_id}:{ability['ability_id']}"
            uses = runtime.setdefault("card_ability_uses_by_instance", {})
            used_count = uses.get(usage_key, 0)
            if used_count >= int(ability["uses_per_match"]):
                return HandlerResult(outcome="rejected", state=working, reason_code="manual_ability_already_used")
            energy_ok, ability_cost, _available_energy, energy_error = self._ability_energy_check(
                runtime, actor_id, ability["ability_id"]
            )
            if not energy_ok:
                return HandlerResult(outcome="rejected", state=working, reason_code=energy_error)

            candidate = copy.deepcopy(working)
            try:
                resolver = self._manual_ability_resolver(ability, runtime)
                action_payload = {
                    "source_instance_id": source_id,
                    "selection": copy.deepcopy(body["payload"].get("selection") or {}),
                    "selected_row": body["payload"].get("selected_row"),
                    "target_row": body["payload"].get("target_row"),
                }
                configured_cause = ability["params"].get("cause_id")
                if configured_cause is not None:
                    action_payload["cause_id"] = configured_cause
                internal_request = {
                    "action_type": ability["action_type"],
                    "actor": {"type": "player", "player_id": actor_id},
                    "payload": action_payload,
                }
                result = resolver.handle(candidate, internal_request, event_sequence_by_id=event_sequence_by_id)
            except (InvalidOperation, KeyError, TypeError, ValueError):
                return HandlerResult(outcome="rejected", state=working, reason_code="manual_ability_resolution_failed")
            if result.outcome == "rejected":
                return HandlerResult(outcome="rejected", state=working, reason_code=result.reason_code or "manual_ability_rejected")

            resolved_state = result.state or candidate
            uses[usage_key] = used_count + 1
            resolver_event_ids = [item["event_id"] for item in result.events]
            target_ids = list(dict.fromkeys(
                target_id for item in result.events for target_id in item.get("target_instance_ids", [])
            ))
            activation_event = _event(
                "card_ability_activated",
                effect_scope="system",
                source_effect_id=ability["ability_id"],
                source_instance_id=source_id,
                target_instance_ids=target_ids,
                caused_by_event_ids=resolver_event_ids,
                payload={
                    "player_id": actor_id,
                    "card_id": source_card_id,
                    "ability_id": ability["ability_id"],
                    "uses_per_match": ability["uses_per_match"],
                    "uses_after_activation": uses[usage_key],
                    "turn_number": runtime["turn_number"],
                },
            )
            energy_event, energy_costs = self._spend_energy(
                runtime,
                actor_id,
                amount=ability_cost,
                source_kind="ability",
                source_id=ability["ability_id"],
                action="activate_card_ability",
                caused_by_event_ids=[activation_event["event_id"]],
                source_instance_id=source_id,
            )
            self._next_actor(runtime, actor_id, list(resolved_state["players"].keys()))
            turn_event = _event(
                "turn_action_completed",
                effect_scope="system",
                source_effect_id=ability["ability_id"],
                source_instance_id=source_id,
                target_instance_ids=target_ids,
                caused_by_event_ids=[energy_event["event_id"] if energy_event else activation_event["event_id"]],
                payload={"player_id": actor_id, "action": "activate_card_ability", "turn_number": runtime["turn_number"]},
            )
            turn_events = self._apply_turn_start_rules(
                resolved_state, runtime, runtime.get("current_player_id")
            )
            events = [*result.events, activation_event]
            if energy_event is not None:
                events.append(energy_event)
            events.extend([turn_event, *turn_events])
            return HandlerResult(
                outcome=result.outcome,
                state=resolved_state,
                target_results=result.target_results,
                costs={"turn_consumed": True, "ability_activation_consumed": True, **energy_costs},
                reason_code=result.reason_code,
                events=events,
                runtime_state=runtime,
            )

        return self.repository.execute_operation(match_id, request, handler)

    def activate_leader(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        selected_row: str | None = None,
        expected_revision: int | None = None,
        operation_id: str | None = None,
    ) -> OperationReceipt:
        """Activate the player's selected leader once per match."""
        actor_id = str(actor_player_id)
        state = self.repository.get_match(match_id)
        revision = state["state_revision"] if expected_revision is None else expected_revision
        request = self._make_request(
            actor_id=actor_id,
            expected_revision=revision,
            action_type="match.activate_leader",
            payload={"selected_row": selected_row},
            operation_id=operation_id,
        )

        def handler(working: dict[str, Any], body: dict[str, Any]) -> HandlerResult:
            runtime = copy.deepcopy(body["_runtime_context"])
            if not self._current(runtime, actor_id):
                return HandlerResult(outcome="rejected", state=working, reason_code="not_current_player")
            player = working["players"][actor_id]
            leader_id = player.get("leader_id")
            if not leader_id:
                return HandlerResult(outcome="rejected", state=working, reason_code="no_leader_selected")
            if player.get("leader_used"):
                return HandlerResult(outcome="rejected", state=working, reason_code="leader_already_used")
            leader = self.catalog.leader_registry.get(leader_id)
            if leader is None:
                return HandlerResult(outcome="rejected", state=working, reason_code="leader_not_in_alpha_registry")
            if player.get("faction_id") != leader.get("faction_id"):
                return HandlerResult(outcome="rejected", state=working, reason_code="leader_faction_mismatch")
            energy_ok, leader_energy_cost, available_energy, energy_error = self._leader_energy_check(
                runtime, actor_id, leader_id
            )
            if not energy_ok:
                return HandlerResult(outcome="rejected", state=working, reason_code=energy_error)
            candidate = copy.deepcopy(working)
            try:
                events, target_results = resolve_leader_effect(
                    candidate,
                    runtime,
                    player_id=actor_id,
                    leader=leader,
                    selected_row=body["payload"].get("selected_row"),
                    apply_vengeance=self.resolver._apply_vengeance,
                )
            except InvalidOperation as exc:
                return HandlerResult(outcome="rejected", state=working, reason_code=str(exc).replace(" ", "_").lower()[:120])
            candidate["players"][actor_id]["leader_used"] = True
            leader_event = _event(
                    "leader_activated",
                    effect_scope="system",
                    source_effect_id=leader["effect_id"],
                    target_instance_ids=list(dict.fromkeys(
                        item for event in events for item in event.get("target_instance_ids", [])
                    )),
                    caused_by_event_ids=[events[-1]["event_id"]] if events else [],
                    payload={"leader_id": leader_id, "leader_name": leader["name"], "faction_id": leader["faction_id"], "uses_per_match": 1, "turn_number": runtime["turn_number"]},
                )
            events.append(leader_event)
            energy_event, leader_energy_costs = self._spend_energy(
                runtime,
                actor_id,
                amount=leader_energy_cost,
                source_kind="leader",
                source_id=leader_id,
                action="activate_leader",
                caused_by_event_ids=[leader_event["event_id"]],
            )
            if energy_event is not None:
                events.append(energy_event)
            self._next_actor(runtime, actor_id, list(candidate["players"].keys()))
            events.extend(
                self._apply_turn_start_rules(
                    candidate, runtime, runtime.get("current_player_id")
                )
            )
            return HandlerResult(
                outcome="applied",
                state=candidate,
                target_results=target_results,
                costs={"turn_consumed": True, "leader_activation_consumed": True, **leader_energy_costs},
                events=events,
                runtime_state=runtime,
            )

        return self.repository.execute_operation(match_id, request, handler)

    def pass_turn(
        self,
        match_id: int,
        *,
        actor_player_id: str | int,
        expected_revision: int | None = None,
        operation_id: str | None = None,
    ) -> OperationReceipt:
        actor_id = str(actor_player_id)
        state = self.repository.get_match(match_id)
        revision = state["state_revision"] if expected_revision is None else expected_revision
        request = self._make_request(
            actor_id=actor_id,
            expected_revision=revision,
            action_type="match.pass",
            payload={},
            operation_id=operation_id,
        )

        def handler(working: dict[str, Any], body: dict[str, Any]) -> HandlerResult:
            runtime = copy.deepcopy(body["_runtime_context"])
            if not self._current(runtime, actor_id):
                return HandlerResult(outcome="rejected", state=working, reason_code="not_current_player")
            runtime["passed_player_ids"].append(actor_id)
            pass_event = _event(
                "player_passed",
                effect_scope="system",
                payload={"player_id": actor_id, "round_number": runtime["round_number"]},
            )
            if len(runtime["passed_player_ids"]) < len(working["players"]):
                remaining = [pid for pid in working["players"] if pid not in runtime["passed_player_ids"]]
                runtime["current_player_id"] = remaining[0]
                runtime["turn_number"] += 1
                fatigue_events = self._apply_turn_start_rules(
                    working, runtime, runtime.get("current_player_id")
                )
                return HandlerResult(
                    outcome="applied",
                    state=working,
                    costs={
                        "turn_consumed": True,
                        "energy_spent": 0,
                        "energy_cost_configured": False,
                        "energy_remaining": int(runtime.get("energy_by_player", {}).get(actor_id, 0)),
                    },
                    events=[pass_event, *fatigue_events],
                    runtime_state=runtime,
                )
            close_events = [pass_event]
            close_events.extend(self._close_round(working, runtime))
            return HandlerResult(
                outcome="applied",
                state=working,
                costs={
                    "turn_consumed": True,
                    "energy_spent": 0,
                    "energy_cost_configured": False,
                    "energy_remaining": int(runtime.get("energy_by_player", {}).get(actor_id, 0)),
                },
                events=close_events,
                runtime_state=runtime,
            )

        return self.repository.execute_operation(match_id, request, handler)

    def _close_round(self, state: dict[str, Any], runtime: dict[str, Any]) -> list[dict[str, Any]]:
        weather = runtime["weather_by_row"]
        player_ids = list(state["players"].keys())
        combat_result = resolve_row_combat(state, player_ids, weather)
        scores = {
            player_id: sum(combat_result["row_power_by_player"][player_id].values())
            for player_id in player_ids
        }
        if "life_by_player" not in runtime:
            runtime["life_by_player"] = {
                player_id: int(self.catalog.ruleset.get("starting_player_life", DEFAULT_STARTING_LIFE))
                for player_id in player_ids
            }
        life_result = apply_life_damage(runtime["life_by_player"], combat_result["damage_by_player"])
        runtime["life_by_player"] = life_result["life_by_player"]
        winner = None
        if len(scores) == 2:
            first, second = list(scores.items())
            if first[1] > second[1]:
                winner = first[0]
            elif second[1] > first[1]:
                winner = second[0]
        round_number = runtime["round_number"]
        events = [
            _event(
                "combat_row_resolved",
                effect_scope="system",
                payload={
                    "round_number": round_number,
                    **row_result,
                    "resolution": "row_power_differential_at_round_close_v1",
                },
            )
            for row_result in combat_result["rows"]
        ]
        damage_event_ids: list[str] = []
        for player_id, change in life_result["life_changes"].items():
            if change["damage_taken"] <= 0:
                continue
            damage_event = _event(
                "player_damage_applied",
                effect_scope="system",
                caused_by_event_ids=[
                    event["event_id"]
                    for event in events
                    if event["kind"] == "combat_row_resolved"
                    and event["payload"]["damage_by_player"].get(player_id, 0) > 0
                ],
                payload={
                    "round_number": round_number,
                    "player_id": player_id,
                    **change,
                },
            )
            events.append(damage_event)
            damage_event_ids.append(damage_event["event_id"])
        for player_id in life_result["defeated_player_ids"]:
            events.append(
                _event(
                    "player_defeated",
                    effect_scope="system",
                    caused_by_event_ids=[
                        event["event_id"]
                        for event in events
                        if event["kind"] == "player_damage_applied"
                        and event["payload"]["player_id"] == player_id
                    ],
                    payload={
                        "round_number": round_number,
                        "player_id": player_id,
                        "reason": "life_depleted",
                    },
                )
            )
        events.append(
            _event(
                "round_score_frozen",
                effect_scope="system",
                caused_by_event_ids=[
                    event["event_id"] for event in events if event["kind"] == "combat_row_resolved"
                ],
                payload={
                    "round_number": round_number,
                    "scores": scores,
                    "winner_player_id": winner,
                    "row_power_by_player": combat_result["row_power_by_player"],
                    "damage_by_player": combat_result["damage_by_player"],
                    "life_by_player": copy.deepcopy(runtime["life_by_player"]),
                },
            )
        )
        if winner is not None:
            runtime["round_wins"][winner] += 1
        runtime["round_history"].append(
            {
                "round_number": round_number,
                "scores": scores,
                "winner_player_id": winner,
                "row_power_by_player": copy.deepcopy(combat_result["row_power_by_player"]),
                "damage_by_player": copy.deepcopy(combat_result["damage_by_player"]),
                "life_by_player": copy.deepcopy(runtime["life_by_player"]),
            }
        )

        archived = []
        for player_id, player in state["players"].items():
            for instance_id in list(player["zones"]["board"]):
                instance = state["instances"][instance_id]
                row = instance["state"].get("current_row")
                transition = transition_instance_zone(state, instance_id, "discard")
                _expire_grants(instance, {"board_exit", "round_close"})
                archived.append(instance_id)
                events.append(
                    _event(
                        "unit_archived",
                        effect_scope="system",
                        target_instance_ids=[instance_id],
                        payload={
                            "transition_id": "round_archive",
                            "owner_player_id": player_id,
                            "row_at_archive": row,
                            "zone_transition": transition,
                            "triggers_vengeance": False,
                        },
                    )
                )
        expired_counts = {key: 0 for key in ("bonus_grants", "protection_grants", "status_applications", "weather_resistance_modifiers")}
        for instance in state["instances"].values():
            counts = _expire_grants(instance, {"round_close"})
            for key, count in counts.items():
                expired_counts[key] += count
        for player in state["players"].values():
            player["round_state"]["last_unit_play_row"] = None
            player["round_state"]["faction_passive_used"] = False
            player["round_state"]["synergy_used"] = {}
        runtime["weather_by_row"] = {row: 0 for row in ROWS}
        events.append(
            _event(
                "round_closed",
                effect_scope="system",
                payload={
                    "round_number": round_number,
                    "archived_instance_ids": archived,
                    "expired_grants": expired_counts,
                    "life_by_player": copy.deepcopy(runtime["life_by_player"]),
                    "weather_cleared": True,
                },
            )
        )

        # Reaching zero life ends the match. The isolated alpha harness keeps
        # best-of-three as a fallback only when neither player is defeated by
        # the configured round limit.
        defeated_players = life_result["defeated_player_ids"]
        if defeated_players:
            if len(defeated_players) == len(player_ids):
                match_winner = None
                finish_reason = "simultaneous_lethal"
            else:
                match_winner = next(pid for pid in player_ids if pid not in defeated_players)
                finish_reason = "life_depleted"
            state["status"] = "finished"
            runtime["phase"] = "finished"
            runtime["current_player_id"] = None
            runtime["match_winner_player_id"] = match_winner
            runtime["match_finish_reason"] = finish_reason
            events.append(
                _event(
                    "match_finished",
                    effect_scope="system",
                    caused_by_event_ids=[
                        event["event_id"] for event in events if event["kind"] == "player_defeated"
                    ],
                    payload={
                        "round_wins": copy.deepcopy(runtime["round_wins"]),
                        "winner_player_id": match_winner,
                        "finish_reason": finish_reason,
                        "life_by_player": copy.deepcopy(runtime["life_by_player"]),
                    },
                )
            )
            return events

        wins_needed = (runtime["best_of"] // 2) + 1
        finished_by_wins = any(wins >= wins_needed for wins in runtime["round_wins"].values())
        finished_by_limit = round_number >= runtime["max_rounds"]
        if finished_by_wins or finished_by_limit:
            state["status"] = "finished"
            runtime["phase"] = "finished"
            runtime["current_player_id"] = None
            match_winner = None
            max_wins = max(runtime["round_wins"].values())
            leaders = [pid for pid, wins in runtime["round_wins"].items() if wins == max_wins]
            if len(leaders) == 1:
                match_winner = leaders[0]
            runtime["match_winner_player_id"] = match_winner
            runtime["match_finish_reason"] = "round_limit"
            events.append(
                _event(
                    "match_finished",
                    effect_scope="system",
                    payload={
                        "round_wins": copy.deepcopy(runtime["round_wins"]),
                        "winner_player_id": match_winner,
                        "finish_reason": runtime["match_finish_reason"],
                        "life_by_player": copy.deepcopy(runtime["life_by_player"]),
                    },
                )
            )
            return events

        # Next round: alternate starter and draw the configured number of cards.
        player_ids = list(state["players"].keys())
        current_starter = runtime["round_starter_player_id"]
        next_starter = next(player_id for player_id in player_ids if player_id != current_starter)
        runtime["round_number"] += 1
        runtime["round_starter_player_id"] = next_starter
        runtime["current_player_id"] = next_starter
        runtime["passed_player_ids"] = []
        for player_id, player in state["players"].items():
            drawn: list[str] = []
            for _ in range(runtime["draw_per_round"]):
                if not player["zones"]["draw_pile"]:
                    break
                instance_id = player["zones"]["draw_pile"][0]
                transition_instance_zone(state, instance_id, "hand")
                drawn.append(instance_id)
            if drawn:
                events.append(
                    _event(
                        "cards_drawn",
                        effect_scope="system",
                        target_instance_ids=drawn,
                        payload={"player_id": player_id, "round_number": runtime["round_number"]},
                    )
                )
        runtime["turn_number"] += 1
        events.append(
            _event(
                "round_started",
                effect_scope="system",
                payload={"round_number": runtime["round_number"], "starter_player_id": next_starter},
            )
        )
        events.extend(self._apply_turn_start_rules(state, runtime, next_starter))
        return events

    def view(self, match_id: int, *, viewer_player_id: str | int | None = None) -> dict[str, Any]:
        """Return a match projection.

        Omitting ``viewer_player_id`` produces a privileged internal/debug view.
        Player-facing adapters must pass the authenticated participant ID; that
        projection hides the opponent's hand and physical collection identifiers.
        """
        state = self.repository.get_match(match_id)
        runtime = self.repository.get_match_runtime(match_id)
        viewer = str(viewer_player_id) if viewer_player_id is not None else None
        if viewer is not None and viewer not in state["players"]:
            raise InvalidOperation("viewer_not_a_match_participant")
        players: dict[str, Any] = {}
        for player_id, player in state["players"].items():
            is_viewer = viewer is None or viewer == player_id
            board = []
            for instance_id in player["zones"]["board"]:
                instance = state["instances"][instance_id]
                card_id = instance["card_id"]
                exemplar_snapshot = instance.get("exemplar_snapshot") or {}
                board_item = {
                    "instance_id": instance_id,
                    "card_id": card_id,
                    "name": self.catalog.display_name(card_id),
                    "row": instance["state"]["current_row"],
                    "base_power": base_power(instance),
                    "bonus": bonus_total(instance),
                    "effective_power": effective_power(state, instance, runtime["weather_by_row"]),
                    "statuses": status_counts(instance),
                    "protection_charges": sum(item.get("charges", 0) for item in instance["state"]["protection_grants"]),
                    "exemplar_rarity_id": exemplar_snapshot.get("rarity_id"),
                    "manual_abilities": [
                        {
                            "ability_id": ability["ability_id"],
                            "energy_cost": self.catalog.energy_cost_for_ability(ability["ability_id"]),
                            "uses_per_match": ability["uses_per_match"],
                            "uses_used": runtime.get("card_ability_uses_by_instance", {}).get(
                                f"{instance_id}:{ability['ability_id']}", 0
                            ),
                        }
                        for ability in self.catalog.manual_abilities_for_card(card_id)
                    ],
                }
                if is_viewer:
                    board_item["exemplar_id"] = instance.get("exemplar_id")
                board.append(board_item)
            hand = []
            for instance_id in player["zones"]["hand"]:
                if not is_viewer:
                    continue
                instance = state["instances"][instance_id]
                exemplar_snapshot = instance.get("exemplar_snapshot") or {}
                card_id = instance["card_id"]
                hand.append(
                    {
                        "instance_id": instance_id,
                        "card_id": card_id,
                        "name": self.catalog.display_name(card_id),
                        "energy_cost": self.catalog.energy_cost_for_card(card_id),
                        "energy_cost_configured": self.catalog.energy_cost_for_card(card_id) is not None,
                        "exemplar_id": instance.get("exemplar_id"),
                        "exemplar_power_base": exemplar_snapshot.get("power_base"),
                        "exemplar_rarity_id": exemplar_snapshot.get("rarity_id"),
                    }
                )
            players[player_id] = {
                "faction_id": player.get("faction_id"),
                "leader_id": player.get("leader_id"),
                "leader_used": bool(player.get("leader_used", False)),
                "leader_energy_cost": (
                    self.catalog.energy_cost_for_leader(player.get("leader_id"))
                    if player.get("leader_id") else None
                ),
                "faction_passive_used": bool(player.get("round_state", {}).get("faction_passive_used", False)),
                "activated_combos_this_round": sorted(
                    combo_id for combo_id, used in player.get("round_state", {}).get("synergy_used", {}).items() if used
                ),
                "hand": hand,
                "hand_count": len(player["zones"]["hand"]),
                "hand_hidden": viewer is not None and viewer != player_id,
                "energy": runtime.get("energy_by_player", {}).get(player_id, 0),
                "maximum_energy": runtime.get("maximum_energy", self.catalog.energy_economy["maximum_energy"]),
                "energy_turns_started": runtime.get("energy_turns_started_by_player", {}).get(player_id, 0),
                "draw_pile_count": len(player["zones"]["draw_pile"]),
                "deck_fatigue_count": runtime.get("deck_fatigue_count_by_player", {}).get(player_id, 0),
                "deck_fatigue_next_damage": (
                    None
                    if player["zones"]["draw_pile"]
                    or runtime.get("initial_turn_exemption_pending_by_player", {}).get(player_id, False)
                    else self.catalog.ruleset["deck_fatigue"]["initial_damage"]
                    + runtime.get("deck_fatigue_count_by_player", {}).get(player_id, 0)
                    * self.catalog.ruleset["deck_fatigue"]["damage_increment"]
                ),
                "discard_count": len(player["zones"]["discard"]),
                "board": board,
                "score": sum(unit["effective_power"] for unit in board),
                "round_wins": runtime["round_wins"][player_id],
                "life": runtime.get("life_by_player", {}).get(
                    player_id, int(self.catalog.ruleset.get("starting_player_life", DEFAULT_STARTING_LIFE))
                ),
            }
        return {
            "match_id": match_id,
            "status": state["status"],
            "round_number": runtime["round_number"],
            "phase": runtime["phase"],
            "current_player_id": runtime["current_player_id"],
            "passed_player_ids": list(runtime["passed_player_ids"]),
            "weather_by_row": copy.deepcopy(runtime["weather_by_row"]),
            "round_wins": copy.deepcopy(runtime["round_wins"]),
            "life_by_player": copy.deepcopy(runtime.get("life_by_player", {})),
            "deck_fatigue_count_by_player": copy.deepcopy(runtime.get("deck_fatigue_count_by_player", {})),
            "energy_by_player": copy.deepcopy(runtime.get("energy_by_player", {})),
            "energy_turns_started_by_player": copy.deepcopy(runtime.get("energy_turns_started_by_player", {})),
            "card_ability_uses_by_instance": copy.deepcopy(runtime.get("card_ability_uses_by_instance", {})),
            "maximum_energy": runtime.get("maximum_energy", self.catalog.energy_economy["maximum_energy"]),
            "match_winner_player_id": runtime.get("match_winner_player_id"),
            "match_finish_reason": runtime.get("match_finish_reason"),
            "match_setup": copy.deepcopy(runtime.get("match_setup", {})),
            "round_history": copy.deepcopy(runtime["round_history"]),
            "state_revision": state["state_revision"],
            "players": players,
        }


__all__ = ["AlphaMatchController"]
