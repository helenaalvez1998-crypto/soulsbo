"""Explicitly allowlisted catalog adapter for the isolated Card Engine v2 alpha.

The source is a historical audit snapshot, not a published runtime catalog. This
adapter intentionally exposes a tiny allowlist and refuses every other card.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .canonical import sha256_json
from .errors import InvalidOperation

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = ROOT / "data/card_game/catalog-legacy-baseline-v0.1.json"
DEFAULT_EFFECTS_PATH = ROOT / "data/card_game/card-engine-v2-alpha-effects.v0.2.json"
DEFAULT_ALIASES_PATH = ROOT / "data/card_game/legacy-effect-aliases-v0.1.json"
DEFAULT_ALLOWLIST_PATH = ROOT / "data/card_game/card-engine-v2-alpha-catalog.v0.3.json"
DEFAULT_COMBOS_PATH = ROOT / "data/card_game/card-engine-v2-alpha-combos.v0.1.json"
DEFAULT_FACTION_PASSIVES_PATH = ROOT / "data/card_game/card-engine-v2-alpha-faction-passives.v0.1.json"
DEFAULT_LEADERS_PATH = ROOT / "data/card_game/card-engine-v2-alpha-leaders.v0.1.json"
DEFAULT_BALANCE_PATH = ROOT / "data/card_game/card-engine-v2-alpha-balance.v0.1.json"
DEFAULT_RULESET_PATH = ROOT / "data/card_game/card-engine-v2-alpha-ruleset.v0.5.json"
DEFAULT_COST_SCHEDULE_PATH = ROOT / "data/card_game/card-engine-v2-alpha-energy-cost-schedule.v0.1.json"
DEFAULT_ACTIVATED_ABILITIES_PATH = ROOT / "data/card_game/card-engine-v2-alpha-activated-abilities.v0.1.json"
ALPHA_RULESET_RELEASE_ID = "alpha-test-only.ruleset.v0.5"

ALPHA_CARD_ALLOWLIST = frozenset(
    {
        # Existing playable-match alpha cards.
        "arma_lanca_fornalha",
        "arma_cajado_marulho",
        "arma_martelo_fornalha",
        "chefe_vigia_cinzento",
        "gwent_v75_ordem_veterano_juramento",
        "gwent_unidade_herdeiro_portao",
        "gwent_especial_egide",
        "gwent_especial_execucao",
        "gwent_especial_tempestade",
        "elden_especial_geada",
        # Expanded on-play effect families (v0.2 alpha only).
        "chefe_rei_afogado",
        "chefe_oraculo_ruina",
        "chefe_maliketh_morte_destinada",
        "chefe_dama_vazio",
        "arma_duas_luas",
        "magia_selo_vigilia",
        "magia_nevoa_antiga",
        "magia_sol_negro",
        "magia_trovao_oco",
        "arma_grande_sino",
        "gwent_singular_primeiro",
        "patente_1",
        "patente_9",
        "patente_10",
        "gwent_unidade_veterano_cercos",
        "luterano_anjo",
        "luterano_papa",
    }
)

RARITY_IDS = {
    "Comum": "common",
    "Incomum": "uncommon",
    "Rara": "rare",
    "Épica": "epic",
    "Lendária": "legendary",
    "Mítica": "mythic",
    "Primordial": "primordial",
    "Singular": "singular",
}
VALID_FACTIONS = {"golden_order", "crimson_veil", "dark_moon", "the_forgotten"}
VALID_ROWS = {"melee", "ranged", "siege"}


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_without_digest(
    *,
    catalog_path: Path,
    effects_path: Path,
    balance_path: Path,
    ruleset_path: Path,
    allowlist_path: Path,
    combos_path: Path,
    faction_passives_path: Path,
    leaders_path: Path,
    cost_schedule_path: Path,
    activated_abilities_path: Path,
) -> dict[str, Any]:
    return {
        "manifest_version": 1,
        "canonicalization": "RFC8785",
        "catalog_release_id": "alpha-test-only.catalog.v0.3",
        "effect_registry_release_id": "alpha-test-only.effects.v0.2",
        "balance_rules_release_id": "alpha-test-only.balance.v0.1",
        "ruleset_release_id": ALPHA_RULESET_RELEASE_ID,
        "artifact_sha256": {
            "catalog": _file_sha256(catalog_path),
            "alpha_allowlist": _file_sha256(allowlist_path),
            "effect_registry": _file_sha256(effects_path),
            "balance_rules": _file_sha256(balance_path),
            "ruleset": _file_sha256(ruleset_path),
            "combos": _file_sha256(combos_path),
            "faction_passives": _file_sha256(faction_passives_path),
            "leaders": _file_sha256(leaders_path),
            "energy_cost_schedule": _file_sha256(cost_schedule_path),
            "activated_abilities": _file_sha256(activated_abilities_path),
        },
    }


class AlphaCatalog:
    """Load the alpha-only allowlist and build immutable CardInstance definitions."""

    def __init__(
        self,
        *,
        catalog_path: Path = DEFAULT_CATALOG_PATH,
        effects_path: Path = DEFAULT_EFFECTS_PATH,
        balance_path: Path = DEFAULT_BALANCE_PATH,
        ruleset_path: Path = DEFAULT_RULESET_PATH,
        aliases_path: Path = DEFAULT_ALIASES_PATH,
        allowlist_path: Path = DEFAULT_ALLOWLIST_PATH,
        combos_path: Path = DEFAULT_COMBOS_PATH,
        faction_passives_path: Path = DEFAULT_FACTION_PASSIVES_PATH,
        leaders_path: Path = DEFAULT_LEADERS_PATH,
        cost_schedule_path: Path = DEFAULT_COST_SCHEDULE_PATH,
        activated_abilities_path: Path = DEFAULT_ACTIVATED_ABILITIES_PATH,
    ) -> None:
        self.catalog_path = Path(catalog_path)
        self.effects_path = Path(effects_path)
        self.balance_path = Path(balance_path)
        self.ruleset_path = Path(ruleset_path)
        self.aliases_path = Path(aliases_path)
        self.allowlist_path = Path(allowlist_path)
        self.combos_path = Path(combos_path)
        self.faction_passives_path = Path(faction_passives_path)
        self.leaders_path = Path(leaders_path)
        self.cost_schedule_path = Path(cost_schedule_path)
        self.activated_abilities_path = Path(activated_abilities_path)
        for path in (
            self.catalog_path, self.effects_path, self.balance_path, self.ruleset_path,
            self.aliases_path, self.allowlist_path, self.combos_path,
            self.faction_passives_path, self.leaders_path, self.cost_schedule_path,
            self.activated_abilities_path,
        ):
            if not path.is_file():
                raise InvalidOperation(f"missing alpha content artifact: {path}")

        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        effects = json.loads(self.effects_path.read_text(encoding="utf-8"))
        balance = json.loads(self.balance_path.read_text(encoding="utf-8"))
        ruleset = json.loads(self.ruleset_path.read_text(encoding="utf-8"))
        aliases = json.loads(self.aliases_path.read_text(encoding="utf-8"))
        allowlist = json.loads(self.allowlist_path.read_text(encoding="utf-8"))
        combos = json.loads(self.combos_path.read_text(encoding="utf-8"))
        faction_passives = json.loads(self.faction_passives_path.read_text(encoding="utf-8"))
        leaders = json.loads(self.leaders_path.read_text(encoding="utf-8"))
        cost_schedule = json.loads(self.cost_schedule_path.read_text(encoding="utf-8"))
        activated_abilities = json.loads(self.activated_abilities_path.read_text(encoding="utf-8"))
        if catalog.get("status") != "historical_snapshot_not_runtime_source_of_truth":
            raise InvalidOperation("catalog source is not the expected historical snapshot")
        if allowlist.get("artifact_type") != "soulsbo_card_engine_v2_alpha_catalog_allowlist":
            raise InvalidOperation("card allowlist artifact type is invalid")
        if allowlist.get("status") != "alpha_test_only_not_a_published_catalog":
            raise InvalidOperation("card allowlist is not marked alpha-only")
        if (
            allowlist.get("version") != "0.3"
            or allowlist.get("catalog_release_id") != "alpha-test-only.catalog.v0.3"
            or allowlist.get("rarity_is_mechanical") is not False
        ):
            raise InvalidOperation("unsupported alpha card allowlist release")
        allowlist_ids = allowlist.get("card_ids")
        if not isinstance(allowlist_ids, list) or not all(isinstance(item, str) and item for item in allowlist_ids):
            raise InvalidOperation("alpha card allowlist card_ids must be a non-empty string list")
        if len(allowlist_ids) != len(set(allowlist_ids)) or allowlist.get("card_count") != len(allowlist_ids):
            raise InvalidOperation("alpha card allowlist contains duplicate IDs or an invalid card_count")
        self.allowlist = frozenset(allowlist_ids)
        if self.allowlist != ALPHA_CARD_ALLOWLIST:
            raise InvalidOperation("alpha card allowlist artifact differs from the reviewed code-level allowlist")
        if combos.get("artifact_type") != "soulsbo_card_engine_v2_alpha_combo_registry" or combos.get("status") != "alpha_test_only_not_a_published_registry":
            raise InvalidOperation("combo registry is not the expected alpha-only artifact")
        if faction_passives.get("artifact_type") != "soulsbo_card_engine_v2_alpha_faction_passives" or faction_passives.get("status") != "alpha_test_only_not_a_published_registry":
            raise InvalidOperation("faction passive registry is not the expected alpha-only artifact")
        if leaders.get("artifact_type") != "soulsbo_card_engine_v2_alpha_leader_registry" or leaders.get("status") != "alpha_test_only_not_a_published_registry":
            raise InvalidOperation("leader registry is not the expected alpha-only artifact")
        if effects.get("status") != "alpha_test_only_not_a_published_registry":
            raise InvalidOperation("effect allowlist is not marked alpha-only")
        if balance.get("status") != "alpha_test_only_not_approved_for_release":
            raise InvalidOperation("balance artifact is not marked alpha-only")
        if ruleset.get("status") != "alpha_test_only_not_approved_for_release":
            raise InvalidOperation("ruleset artifact is not marked alpha-only")
        fatigue = ruleset.get("deck_fatigue")
        energy = ruleset.get("energy_economy")
        if (
            ruleset.get("version") != "0.5"
            or ruleset.get("initial_hand_size") != 4
            or ruleset.get("starting_player_life") != 20
            or ruleset.get("combat_resolution") != "row_power_differential_at_round_close_v1"
            or ruleset.get("lethal_damage_ends_match") is not True
            or ruleset.get("simultaneous_lethal_outcome") != "draw"
            or not isinstance(fatigue, dict)
            or fatigue.get("enabled") is not True
            or fatigue.get("trigger") != "start_of_individual_player_turn_when_draw_pile_empty"
            or fatigue.get("initial_damage") != 1
            or fatigue.get("damage_increment") != 1
            or fatigue.get("maximum_damage") is not None
            or fatigue.get("counter_scope") != "per_player_per_match"
            or fatigue.get("counter_reset") != "never_during_match"
            or fatigue.get("initial_deal_exemptions") != "one_initial_turn_per_player"
            or fatigue.get("terminal_timing") != "immediate_before_player_action"
            or fatigue.get("discard_reshuffle") is not False
            or not isinstance(energy, dict)
            or energy.get("enabled") is not True
            or not isinstance(energy.get("starting_energy"), int)
            or isinstance(energy.get("starting_energy"), bool)
            or energy.get("starting_energy") != 0
            or not isinstance(energy.get("energy_gain_per_turn"), int)
            or isinstance(energy.get("energy_gain_per_turn"), bool)
            or energy.get("energy_gain_per_turn") != 1
            or not isinstance(energy.get("maximum_energy"), int)
            or isinstance(energy.get("maximum_energy"), bool)
            or energy.get("maximum_energy") != 5
            or energy.get("energy_persistence") != "carries_across_rounds_until_spent"
            or energy.get("card_cost_source") != "explicit_card_id_schedule_v1"
            or energy.get("unconfigured_card_cost_policy") != "reject_unpriced_alpha_action"
            or energy.get("unconfigured_leader_cost_policy") != "reject_unpriced_leader_activation"
            or energy.get("unconfigured_ability_cost_policy") != "reject_unpriced_manual_ability_activation"
            or energy.get("costed_actions") != ["play_unit", "play_special", "activate_leader", "activate_card_ability"]
            or energy.get("energy_is_not_refunded_after_successful_card_play") is not True
            or energy.get("energy_is_not_refunded_after_successful_costed_action") is not True
            or energy.get("rarity_is_not_a_cost_input") is not True
        ):
            raise InvalidOperation("unsupported alpha ruleset, deck-fatigue or energy-economy release")
        card_energy_costs = energy.get("card_energy_cost_by_card_id")
        leader_energy_costs = energy.get("leader_activation_energy_cost_by_leader_id")
        ability_energy_costs = energy.get("ability_activation_energy_cost_by_ability_id")
        if not isinstance(card_energy_costs, dict) or not isinstance(leader_energy_costs, dict) or not isinstance(ability_energy_costs, dict):
            raise InvalidOperation("alpha energy costs must be explicit card/leader/ability ID maps")
        for card_id, energy_cost in card_energy_costs.items():
            if (
                not isinstance(card_id, str) or not card_id
                or not isinstance(energy_cost, int) or isinstance(energy_cost, bool)
                or energy_cost < 1
                or energy_cost > energy.get("maximum_energy", 0)
            ):
                raise InvalidOperation("explicit card energy-cost map contains an invalid entry")
        for leader_id, energy_cost in leader_energy_costs.items():
            if (
                not isinstance(leader_id, str) or not leader_id
                or not isinstance(energy_cost, int) or isinstance(energy_cost, bool)
                or energy_cost < 1
                or energy_cost > energy.get("maximum_energy", 0)
            ):
                raise InvalidOperation("explicit leader energy-cost map contains an invalid entry")
        if effects.get("rarity_is_mechanical") is not False or balance.get("rarity_scaling") is not False:
            raise InvalidOperation("alpha catalog cannot enable rarity-based mechanics")

        alias_metadata = aliases.get("metadata", {})
        if (
            alias_metadata.get("status") != "PROPOSTA DE MIGRAÇÃO; NÃO ALTERA O RUNTIME"
            or "aliases" not in str(alias_metadata.get("document", "")).lower()
        ):
            raise InvalidOperation("legacy alias artifact is not the expected historical v0.1 source")
        combo_rows = combos.get("combos", [])
        priorities = [row.get("priority") for row in combo_rows]
        combo_ids = [row.get("combo_id") for row in combo_rows]
        if len(combo_rows) != 27 or len(combo_ids) != len(set(combo_ids)) or len(priorities) != len(set(priorities)):
            raise InvalidOperation("alpha combo registry must have 27 unique IDs and priorities")
        for row in combo_rows:
            priority = row.get("priority")
            individual_bonus = row.get("individual_bonus")
            team_bonus = row.get("team_bonus")
            required_tags = row.get("required_tags")
            if (
                not isinstance(row.get("combo_id"), str) or not row["combo_id"]
                or not isinstance(priority, int) or isinstance(priority, bool)
                or not isinstance(required_tags, list) or not required_tags
                or any(not isinstance(tag, str) or not tag for tag in required_tags)
                or len(required_tags) != len(set(required_tags))
                or row.get("minimum_distinct_participants") != 2
                or not isinstance(individual_bonus, int) or isinstance(individual_bonus, bool) or individual_bonus <= 0
                or not isinstance(team_bonus, int) or isinstance(team_bonus, bool) or team_bonus < 0
            ):
                raise InvalidOperation("alpha combo definition violates approved combo policy")
        passive_rows = faction_passives.get("passives", [])
        if len(passive_rows) != 4 or len({row.get("faction_id") for row in passive_rows}) != 4:
            raise InvalidOperation("alpha faction passive registry must define four unique factions")
        for row in passive_rows:
            bonus = row.get("bonus")
            if (
                row.get("faction_id") not in VALID_FACTIONS
                or not isinstance(row.get("passive_id"), str) or not row["passive_id"]
                or row.get("trigger") != "first_unit_of_this_faction_played_each_round"
                or not isinstance(bonus, int) or isinstance(bonus, bool) or bonus != 1
            ):
                raise InvalidOperation("unsupported alpha faction passive rule")
        leader_rows = leaders.get("leaders", [])
        leader_ids = [row.get("leader_id") for row in leader_rows]
        leader_effect_ids = [row.get("effect_id") for row in leader_rows]
        if (
            len(leader_rows) != 10 or len(leader_ids) != len(set(leader_ids))
            or len(leader_effect_ids) != len(set(leader_effect_ids))
        ):
            raise InvalidOperation("alpha leader registry must define ten unique leaders/effects")
        for row in leader_rows:
            if (
                row.get("uses_per_match") != 1
                or row.get("faction_id") not in VALID_FACTIONS
                or not isinstance(row.get("params"), dict)
                or row["params"].get("effect_id") != row.get("effect_id")
            ):
                raise InvalidOperation("alpha leader definition has invalid faction, use limit or parameters")

        if (
            cost_schedule.get("artifact_type") != "soulsbo_card_engine_v2_alpha_energy_cost_schedule"
            or cost_schedule.get("version") != "0.1"
            or cost_schedule.get("status") != "alpha_only_provisional_playtest_schedule_not_approved_for_release"
            or cost_schedule.get("ruleset_release_id") != ALPHA_RULESET_RELEASE_ID
        ):
            raise InvalidOperation("energy cost schedule is not the expected provisional alpha v0.1 artifact")
        schedule_cards = cost_schedule.get("card_energy_cost_by_card_id")
        schedule_leaders = cost_schedule.get("leader_activation_energy_cost_by_leader_id")
        schedule_abilities = cost_schedule.get("ability_activation_energy_cost_by_ability_id")
        if not all(isinstance(item, dict) for item in (schedule_cards, schedule_leaders, schedule_abilities)):
            raise InvalidOperation("energy cost schedule must contain three ID maps")
        if any(not isinstance(value, dict) for value in schedule_cards.values()) or any(
            not isinstance(value, dict) for value in schedule_leaders.values()
        ):
            raise InvalidOperation("card and leader cost schedule rows must be objects")
        schedule_card_map = {key: value.get("energy_cost") for key, value in schedule_cards.items()}
        schedule_leader_map = {key: value.get("energy_cost") for key, value in schedule_leaders.items()}
        if (
            set(schedule_cards) != self.allowlist
            or set(schedule_leaders) != set(leader_ids)
            or schedule_card_map != card_energy_costs
            or schedule_leader_map != leader_energy_costs
        ):
            raise InvalidOperation("ruleset energy maps differ from the reviewed cost schedule artifact")
        if schedule_abilities != ability_energy_costs:
            raise InvalidOperation("ruleset ability costs differ from the reviewed cost schedule artifact")
        if set(card_energy_costs) != self.allowlist:
            raise InvalidOperation("provisional alpha schedule must price every allowlisted card exactly once")
        if set(leader_energy_costs) != set(leader_ids):
            raise InvalidOperation("provisional alpha schedule must price all ten alpha leaders exactly once")
        if any(not isinstance(item, int) or isinstance(item, bool) or item < 1 or item > energy["maximum_energy"] for item in card_energy_costs.values()):
            raise InvalidOperation("card energy costs must be positive integers within the energy cap")
        if any(not isinstance(item, int) or isinstance(item, bool) or item < 1 or item > energy["maximum_energy"] for item in leader_energy_costs.values()):
            raise InvalidOperation("leader energy costs must be positive integers within the energy cap")

        if (
            activated_abilities.get("artifact_type") != "soulsbo_card_engine_v2_alpha_activated_ability_registry"
            or activated_abilities.get("version") != "0.1"
            or activated_abilities.get("status") != "alpha_test_only_not_a_published_registry"
        ):
            raise InvalidOperation("activated ability registry is not the expected alpha-only registry")
        allowed_ability_actions = {"unit.grant_bonus", "unit.grant_protection", "unit.remove", "unit.move"}
        declared_ability_actions = activated_abilities.get("supported_action_types")
        ability_rows = activated_abilities.get("abilities")
        if (
            not isinstance(declared_ability_actions, list)
            or set(declared_ability_actions) != allowed_ability_actions
            or not isinstance(ability_rows, list)
        ):
            raise InvalidOperation("activated ability registry has invalid action allowlist or abilities")
        ability_ids = [row.get("ability_id") for row in ability_rows]
        if (
            any(not isinstance(item, str) or not item for item in ability_ids)
            or len(ability_ids) != len(set(ability_ids))
        ):
            raise InvalidOperation("activated ability registry contains invalid or duplicate ability IDs")
        from .gameplay import ActionDefinition, GameplayResolver, ProtectionProfile
        from .targeting import TargetPolicy
        for ability in ability_rows:
            source_ids = ability.get("source_card_ids")
            policy_data = ability.get("target_policy")
            params = ability.get("params")
            if (
                not isinstance(ability.get("ability_id"), str) or not ability["ability_id"]
                or not isinstance(source_ids, list) or not source_ids
                or any(not isinstance(item, str) or not item for item in source_ids)
                or len(source_ids) != len(set(source_ids)) or not set(source_ids).issubset(self.allowlist)
                or ability.get("action_type") not in allowed_ability_actions
                or not isinstance(policy_data, dict)
                or not isinstance(params, dict)
                or not isinstance(ability.get("uses_per_match"), int)
                or isinstance(ability.get("uses_per_match"), bool)
                or ability.get("uses_per_match") != 1
            ):
                raise InvalidOperation("manual ability definition is invalid or references a blocked card")
            try:
                policy = TargetPolicy(**policy_data)
                action_type = ability["action_type"]
                common = {
                    "action_type": action_type,
                    "source_effect_id": ability["ability_id"],
                    "target_policy_id": policy.policy_id,
                    "allowed_source_zones": frozenset({"board"}),
                    "source_card_ids": frozenset(source_ids),
                    "no_target_outcome": "consumed_no_effect" if policy.on_no_target == "consume_no_effect" else "rejected",
                }
                if action_type == "unit.grant_bonus":
                    action = ActionDefinition(
                        **common,
                        bonus_amount=params.get("bonus_amount"),
                        bonus_expires_on=params.get("bonus_expires_on"),
                        bonus_clamp_policy_id=params.get("bonus_clamp_policy_id", "balance.alpha.raw_grants.v1"),
                    )
                elif action_type == "unit.grant_protection":
                    action = ActionDefinition(
                        **common,
                        protection_profile_id=params.get("protection_profile_id"),
                        protection_charges=params.get("protection_charges"),
                        protection_expires_on=params.get("protection_expires_on"),
                    )
                    profile = action.protection_profile_id
                    if profile != "alpha.protection.standard":
                        raise InvalidOperation("manual ability references an unavailable protection profile")
                elif action_type == "unit.move":
                    action = ActionDefinition(
                        **common,
                        allowed_target_rows=frozenset(params.get("allowed_target_rows", [])),
                    )
                else:  # unit.remove
                    allowed_causes = frozenset(params.get("allowed_causes", []))
                    cause_map = tuple(tuple(item) for item in params.get("cause_target_policy_ids", []))
                    action = ActionDefinition(
                        **common,
                        allowed_causes=allowed_causes,
                        cause_target_policy_ids=cause_map,
                    )
                GameplayResolver(
                    actions={action.action_type: action},
                    target_policies={policy.policy_id: policy},
                    protection_profiles={
                        "alpha.protection.standard": ProtectionProfile("alpha.protection.standard")
                    },
                )
            except (TypeError, InvalidOperation, ValueError) as exc:
                raise InvalidOperation("manual ability action or target configuration is invalid") from exc
        if set(ability_energy_costs) != set(ability_ids):
            raise InvalidOperation("each registered manual ability must have exactly one explicit energy cost")
        if any(not isinstance(item, int) or isinstance(item, bool) or item < 1 or item > energy["maximum_energy"] for item in ability_energy_costs.values()):
            raise InvalidOperation("manual ability energy costs must be positive integers within the energy cap")

        self.combo_registry = {row["combo_id"]: copy.deepcopy(row) for row in combo_rows}
        self.faction_passives = {row["faction_id"]: copy.deepcopy(row) for row in passive_rows}
        self.leader_registry = {row["leader_id"]: copy.deepcopy(row) for row in leader_rows}
        self.leaders_by_effect = {row["effect_id"]: copy.deepcopy(row) for row in leader_rows}
        self.card_energy_cost_by_id = copy.deepcopy(card_energy_costs)
        self.leader_energy_cost_by_id = copy.deepcopy(leader_energy_costs)
        self.ability_energy_cost_by_id = copy.deepcopy(ability_energy_costs)
        self.activated_abilities = {row["ability_id"]: copy.deepcopy(row) for row in ability_rows}
        self.activated_abilities_by_card_id: dict[str, list[dict[str, Any]]] = {card_id: [] for card_id in self.allowlist}
        for ability in ability_rows:
            for source_card_id in ability["source_card_ids"]:
                self.activated_abilities_by_card_id[source_card_id].append(copy.deepcopy(ability))
        self.balance = balance
        self.ruleset = ruleset
        self.energy_economy = copy.deepcopy(energy)
        self.effect_allowlist = {
            row["effect_id"]: copy.deepcopy(row) for row in effects.get("supported_effects", [])
        }
        self.generic_aliases = {
            row["legacy_id"]: copy.deepcopy(row)
            for row in aliases.get("generic_and_special_aliases", [])
        }
        self.identity_aliases = {
            row["card_id"]: copy.deepcopy(row)
            for row in aliases.get("active_identity_card_overrides", [])
        }
        self._raw_cards = {row["card_id"]: row for row in catalog.get("cards", [])}
        self._definitions: dict[str, dict[str, Any]] = {}
        self._names: dict[str, str] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

        if not self.allowlist.issubset(self._raw_cards):
            missing = sorted(self.allowlist - set(self._raw_cards))
            raise InvalidOperation(f"alpha card allowlist references missing historical cards: {missing}")

        for card_id in self.allowlist:
            raw = self._raw_cards.get(card_id)
            if raw is None:
                raise InvalidOperation(f"allowlisted card is absent from historical snapshot: {card_id}")
            self._names[card_id] = str(raw.get("name_legacy") or card_id)
            self._metadata[card_id] = {
                "display_name": self._names[card_id],
                "legacy_deck_cost": raw.get("deck_cost_legacy"),
                "legacy_rarity": raw.get("rarity_legacy"),
                "energy_cost": self.card_energy_cost_by_id.get(card_id),
                "energy_cost_configured": card_id in self.card_energy_cost_by_id,
                "source_status": "historical_fixture_only",
                "faction_review_status": raw.get("faction_review_status"),
                "migration_status": raw.get("migration_status"),
                "runtime_scope": "alpha_v0.5_explicit_allowlist_only",
            }
            self._definitions[card_id] = self._build_definition(raw)

        self.manifest = _manifest_without_digest(
            catalog_path=self.catalog_path,
            effects_path=self.effects_path,
            balance_path=self.balance_path,
            ruleset_path=self.ruleset_path,
            allowlist_path=self.allowlist_path,
            combos_path=self.combos_path,
            faction_passives_path=self.faction_passives_path,
            leaders_path=self.leaders_path,
            cost_schedule_path=self.cost_schedule_path,
            activated_abilities_path=self.activated_abilities_path,
        )
        self.manifest["catalog_release_id"] = allowlist.get(
            "catalog_release_id", "alpha-test-only.catalog.v0.3"
        )
        self.manifest["artifact_sha256"]["legacy_aliases"] = _file_sha256(self.aliases_path)
        self.manifest["definition_digest"] = sha256_json(self.manifest)
        self._validate_allowlist_links()

    def _build_definition(self, raw: dict[str, Any]) -> dict[str, Any]:
        card_id = raw["card_id"]
        kind = raw.get("legacy_kind")
        if kind not in ("unit", "special"):
            raise InvalidOperation(f"unsupported alpha card kind: {card_id}")
        faction = raw.get("faction_id_candidate")
        if faction not in VALID_FACTIONS:
            raise InvalidOperation(f"alpha fixture has unreviewed/invalid faction for {card_id}")
        row = raw.get("row_legacy")
        power = raw.get("power_base_legacy")
        if kind == "unit":
            if row not in VALID_ROWS or not isinstance(power, int) or isinstance(power, bool) or power < 1:
                raise InvalidOperation(f"unit fixture has invalid row/power: {card_id}")
        elif row is not None or power is not None:
            raise InvalidOperation(f"special fixture cannot have printed row/power: {card_id}")

        legacy_effect_id = raw.get("effective_legacy_effect_id")
        generic_skill = raw.get("declared_generic_skill_id")
        active_identity = raw.get("active_identity")
        effect_params: dict[str, Any] = {}
        if kind == "special":
            # Special action handlers keep their explicit server-side action IDs.
            effect_id = legacy_effect_id
        elif generic_skill == "vinganca":
            effect_id = "effect.vengeance_on_removal"
        elif card_id in self.identity_aliases and self.identity_aliases[card_id].get("canonical_effect_id") in self.effect_allowlist:
            identity = self.identity_aliases[card_id]
            effect_id = identity.get("canonical_effect_id")
            effect_params = copy.deepcopy(identity.get("default_effect_params", {}))
        elif generic_skill in self.generic_aliases:
            alias = self.generic_aliases[generic_skill]
            effect_id = alias.get("canonical_effect_id")
            effect_params = copy.deepcopy(alias.get("default_effect_params", {}))
        elif active_identity:
            # Explicit alpha-only effects such as the already tested V75 oath.
            effect_id = active_identity.get("effect_id")
        else:
            effect_id = legacy_effect_id

        if effect_id:
            entry = self.effect_allowlist.get(effect_id)
            if entry is None or card_id not in entry.get("source_card_ids", []):
                raise InvalidOperation(f"card effect is not included in the alpha allowlist: {card_id}/{effect_id}")
            by_card = entry.get("params_by_card_id", {})
            if card_id in by_card:
                effect_params = copy.deepcopy(by_card[card_id])
            elif not effect_params:
                effect_params = copy.deepcopy(entry.get("params", {}))

        rarity = raw.get("rarity_legacy")
        if rarity not in RARITY_IDS:
            raise InvalidOperation(f"unknown legacy rarity label in alpha fixture: {rarity!r}")
        rarity_id = RARITY_IDS[rarity]

        definition = {
            "card_id": card_id,
            "kind": kind,
            "faction_id": faction,
            "printed_row": row,
            "power_base": power,
            "rarity_id": rarity_id,
            "effect_id": effect_id,
            "effect_params": effect_params,
            "combo_tags": list(raw.get("legacy_combo_tags") or []),
            "catalog_release_id": "alpha-test-only.catalog.v0.3",
            "effect_registry_release_id": "alpha-test-only.effects.v0.2",
            "balance_rules_release_id": "alpha-test-only.balance.v0.1",
            "ruleset_release_id": ALPHA_RULESET_RELEASE_ID,
            "intrinsic_weather_resistance": 0,
        }
        definition["definition_digest"] = sha256_json(definition)
        return definition

    def _validate_allowlist_links(self) -> None:
        linked_cards = set()
        for entry in self.effect_allowlist.values():
            linked_cards.update(entry.get("source_card_ids", []))
        if not linked_cards.issubset(self.allowlist):
            raise InvalidOperation("effect allowlist refers to a card outside the explicit alpha allowlist")
        for card_id, definition in self._definitions.items():
            if definition["effect_id"] and card_id not in linked_cards:
                raise InvalidOperation(f"card effect has no allowlist link: {card_id}")

    def definition_for(self, card_id: str) -> dict[str, Any]:
        try:
            return copy.deepcopy(self._definitions[card_id])
        except KeyError as exc:
            raise InvalidOperation(f"card is not available in the alpha test allowlist: {card_id}") from exc

    def display_name(self, card_id: str) -> str:
        try:
            return self._names[card_id]
        except KeyError as exc:
            raise InvalidOperation(f"card is not available in the alpha test allowlist: {card_id}") from exc

    def metadata_for(self, card_id: str) -> dict[str, Any]:
        try:
            return copy.deepcopy(self._metadata[card_id])
        except KeyError as exc:
            raise InvalidOperation(f"card is not available in the alpha test allowlist: {card_id}") from exc

    def energy_cost_for_card(self, card_id: str) -> int | None:
        """Return the explicitly configured per-card energy cost, if any."""
        return self.card_energy_cost_by_id.get(card_id)

    def energy_cost_for_leader(self, leader_id: str) -> int | None:
        """Return the reviewed alpha leader activation cost."""
        return self.leader_energy_cost_by_id.get(leader_id)

    def energy_cost_for_ability(self, ability_id: str) -> int | None:
        """Return the explicit energy cost for a registered manual card ability."""
        return self.ability_energy_cost_by_id.get(ability_id)

    def manual_abilities_for_card(self, card_id: str) -> list[dict[str, Any]]:
        """Return server-registered manual abilities; on-play effects are excluded."""
        return copy.deepcopy(self.activated_abilities_by_card_id.get(card_id, []))

    def definition_manifest(self) -> dict[str, Any]:
        return copy.deepcopy(self.manifest)

    def allowed_card_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))
