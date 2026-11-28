"""Authoritative target-offer construction for the isolated Card Engine v2.

Policies are supplied by trusted server-side release configuration. Requests may
select only identities already offered by the server; they cannot submit or
override eligibility, metrics, sort order, or fallback rules.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import InvalidOperation
from .power import base_power
from .validation import ROWS, ZONES


MetricResolver = Callable[[dict[str, Any], dict[str, Any], str], int | None]


@dataclass(frozen=True, slots=True)
class TargetPolicy:
    policy_id: str
    selection_mode: str = "manual_single"
    target_side: str = "enemies"
    source_zone: str = "board"
    row_scope: str = "global"
    row_basis: str = "current_row"
    fixed_row: str | None = None
    eligibility_metric: str = "none"
    display_metric: str = "none"
    sort_metric: str = "none"
    direction: str = "none"
    tie_breaker: str = "zone_order"
    minimum_targets: int = 1
    maximum_targets: int | str = 1
    on_no_target: str = "reject"
    predicates: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    secondary_selection: str = "none"

    def __post_init__(self) -> None:
        if not self.policy_id or len(self.policy_id) > 96:
            raise InvalidOperation("target policy requires a valid policy_id")
        if self.selection_mode not in ("none", "manual_single", "manual_set", "automatic", "manual_primary_auto_fill"):
            raise InvalidOperation("unsupported target selection mode")
        if self.target_side not in ("self", "allies", "enemies", "any", "none"):
            raise InvalidOperation("unsupported target_side")
        if self.source_zone not in (*ZONES, "any", "none"):
            raise InvalidOperation("unsupported source_zone")
        if self.row_scope not in ("global", "selected_row", "fixed_row", "different_from_selected_row"):
            raise InvalidOperation("unsupported row_scope")
        if self.row_basis != "current_row":
            raise InvalidOperation("this alpha supports current_row only for row-scoped offers")
        if self.row_scope == "fixed_row" and self.fixed_row not in ROWS:
            raise InvalidOperation("fixed_row policies require a valid fixed_row")
        if self.eligibility_metric not in ("none", "base_power", "effective_power", "bonus"):
            raise InvalidOperation("unsupported eligibility metric")
        if self.display_metric not in ("none", "base_power", "effective_power", "bonus"):
            raise InvalidOperation("unsupported display metric")
        if self.sort_metric not in ("none", "base_power", "effective_power", "bonus", "zone_order"):
            raise InvalidOperation("unsupported sort metric in this alpha")
        if self.direction not in ("none", "ascending", "descending"):
            raise InvalidOperation("unsupported sort direction")
        if self.tie_breaker not in ("none", "zone_order"):
            raise InvalidOperation("unsupported tie breaker in this alpha")
        if not isinstance(self.minimum_targets, int) or isinstance(self.minimum_targets, bool) or self.minimum_targets < 0:
            raise InvalidOperation("minimum_targets must be a non-negative integer")
        if self.maximum_targets != "all" and (
            not isinstance(self.maximum_targets, int)
            or isinstance(self.maximum_targets, bool)
            or self.maximum_targets < 0
        ):
            raise InvalidOperation("maximum_targets must be a non-negative integer or 'all'")
        if self.maximum_targets != "all" and self.maximum_targets < self.minimum_targets:
            raise InvalidOperation("maximum_targets cannot be less than minimum_targets")
        if self.on_no_target not in ("reject", "consume_no_effect"):
            raise InvalidOperation("unsupported on_no_target policy")
        if self.secondary_selection not in ("none", "manual_set", "auto_ranked"):
            raise InvalidOperation("unsupported secondary_selection")
        if self.selection_mode == "manual_primary_auto_fill":
            if self.secondary_selection != "auto_ranked":
                raise InvalidOperation("manual_primary_auto_fill requires secondary_selection=auto_ranked")
            if self.maximum_targets != "all" and self.maximum_targets < 2:
                raise InvalidOperation("manual_primary_auto_fill requires maximum_targets >= 2 or 'all'")
        elif self.secondary_selection != "none":
            raise InvalidOperation("secondary selection is supported only by manual_primary_auto_fill")


def _bonus_total(instance: dict[str, Any]) -> int:
    total = 0
    for grant in instance["state"].get("bonus_grants", []):
        amount = grant.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise InvalidOperation("bonus grant amount must be an integer")
        total += amount
    return total


def _default_metric(state: dict[str, Any], instance: dict[str, Any], metric: str) -> int | None:
    snapshot = instance["definition_snapshot"]
    if metric == "none":
        return None
    if metric == "base_power":
        return base_power(instance)
    if metric == "bonus":
        return _bonus_total(instance)
    if metric == "effective_power":
        raise InvalidOperation(
            "effective_power requires a release-bound metric resolver; weather/status rules are not implemented in this alpha"
        )
    raise InvalidOperation(f"unsupported metric: {metric}")


def _predicate_matches(
    predicate: dict[str, Any],
    *,
    state: dict[str, Any],
    instance: dict[str, Any],
    source_instance_id: str | None,
    metric_resolver: MetricResolver | None,
) -> bool:
    predicate_id = predicate.get("predicate_id")
    params = predicate.get("params", {})
    if not isinstance(params, dict):
        raise InvalidOperation("predicate params must be an object")
    snapshot = instance["definition_snapshot"]
    if predicate_id == "instance.not_source":
        return instance["instance_id"] != source_instance_id
    if predicate_id == "definition.kind_is":
        return snapshot.get("kind") == params.get("kind")
    if predicate_id == "definition.effect_id_is":
        return snapshot.get("effect_id") == params.get("effect_id")
    if predicate_id == "runtime.bonus_at_least":
        threshold = params.get("amount")
        if not isinstance(threshold, int) or isinstance(threshold, bool):
            raise InvalidOperation("runtime.bonus_at_least requires integer params.amount")
        return _bonus_total(instance) >= threshold
    if predicate_id == "runtime.has_status":
        status_id = params.get("status_id")
        if not isinstance(status_id, str) or not status_id:
            raise InvalidOperation("runtime.has_status requires params.status_id")
        return any(item.get("status_id") == status_id for item in instance["state"].get("status_applications", []))
    if predicate_id == "runtime.has_protection_profile":
        profile_id = params.get("profile_id")
        if not isinstance(profile_id, str) or not profile_id:
            raise InvalidOperation("runtime.has_protection_profile requires params.profile_id")
        return any(
            item.get("profile_id") == profile_id and item.get("charges", 0) > 0
            for item in instance["state"].get("protection_grants", [])
        )
    if predicate_id in ("metric.at_most", "metric.at_least"):
        metric = params.get("metric")
        threshold = params.get("amount")
        if metric not in ("base_power", "effective_power", "bonus"):
            raise InvalidOperation("metric predicates require base_power, effective_power or bonus")
        if not isinstance(threshold, int) or isinstance(threshold, bool):
            raise InvalidOperation("metric predicates require an integer params.amount")
        if metric == "effective_power":
            if metric_resolver is None:
                raise InvalidOperation("effective_power predicate requires a release-bound metric resolver")
            value = metric_resolver(state, instance, metric)
        else:
            value = _default_metric(state, instance, metric)
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidOperation(f"metric {metric} is unavailable for target eligibility")
        return value <= threshold if predicate_id == "metric.at_most" else value >= threshold
    raise InvalidOperation(f"unknown target eligibility predicate: {predicate_id}")


def _side_matches(owner_id: str, actor_id: str, source_id: str | None, side: str) -> bool:
    if side == "none":
        return False
    if side == "any":
        return True
    if side in ("self",):
        return owner_id == actor_id and source_id is not None
    if side == "allies":
        return owner_id == actor_id
    if side == "enemies":
        return owner_id != actor_id
    return False


def build_target_offer(
    state: dict[str, Any],
    *,
    actor_player_id: str,
    policy: TargetPolicy,
    source_instance_id: str | None = None,
    selected_row: str | None = None,
    metric_resolver: MetricResolver | None = None,
    secondary_primary_id: str | None = None,
) -> dict[str, Any]:
    """Build a revision-bound offer; all eligibility/order decisions are server-side."""
    if actor_player_id not in state.get("players", {}):
        raise InvalidOperation("actor is not a participant in this match")
    if selected_row is not None and selected_row not in ROWS:
        raise InvalidOperation("selected_row must be a valid row")
    if policy.row_scope in ("selected_row", "different_from_selected_row") and selected_row is None:
        raise InvalidOperation("row-scoped policy requires selected_row")
    if source_instance_id is not None and source_instance_id not in state.get("instances", {}):
        raise InvalidOperation("source_instance_id does not exist")
    if secondary_primary_id is not None and policy.selection_mode != "manual_primary_auto_fill":
        raise InvalidOperation("secondary_primary_id is only valid for manual_primary_auto_fill policies")

    def metric_value(instance: dict[str, Any], metric_name: str) -> int | None:
        if metric_name == "effective_power" and metric_resolver is not None:
            value = metric_resolver(state, instance, metric_name)
        else:
            value = _default_metric(state, instance, metric_name)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            raise InvalidOperation(f"metric resolver returned a non-integer value for {metric_name}")
        return value

    candidates: list[dict[str, Any]] = []
    global_order = 0
    for owner_id, player in state["players"].items():
        if not _side_matches(owner_id, actor_player_id, source_instance_id, policy.target_side):
            continue
        for zone in ZONES:
            if policy.source_zone not in ("any", zone):
                continue
            for zone_order, instance_id in enumerate(player["zones"][zone]):
                global_order += 1
                if policy.target_side == "self" and instance_id != source_instance_id:
                    continue
                instance = state["instances"][instance_id]
                runtime = instance["state"]
                row = runtime.get("current_row")
                if policy.row_scope == "fixed_row" and row != policy.fixed_row:
                    continue
                if policy.row_scope == "selected_row" and row != selected_row:
                    continue
                if policy.row_scope == "different_from_selected_row" and row == selected_row:
                    continue
                if any(
                    not _predicate_matches(
                        predicate,
                        state=state,
                        instance=instance,
                        source_instance_id=source_instance_id,
                        metric_resolver=metric_resolver,
                    )
                    for predicate in policy.predicates
                ):
                    continue
                eligibility_value = metric_value(instance, policy.eligibility_metric)
                display_value = metric_value(instance, policy.display_metric)
                base_power = metric_value(instance, "base_power")
                bonus = metric_value(instance, "bonus")
                effective_power = None
                if metric_resolver is not None:
                    effective_power = metric_value(instance, "effective_power")
                candidate = {
                    "target_instance_id": instance_id,
                    "display_name": str(instance.get("definition_snapshot", {}).get("display_name") or instance["card_id"]),
                    "current_row": row,
                    "base_power": base_power,
                    "effective_power": effective_power,
                    "bonus": bonus,
                    "eligibility_value": eligibility_value,
                    "display_value": display_value,
                    "selection_order": global_order - 1,
                    "_zone_order": zone_order,
                }
                candidates.append(candidate)

    def metric_key(candidate: dict[str, Any]) -> int:
        key_name = {
            "base_power": "base_power",
            "bonus": "bonus",
            "effective_power": "effective_power",
            "zone_order": "_zone_order",
            "none": "_zone_order",
        }[policy.sort_metric]
        value = candidate.get(key_name)
        if value is None:
            raise InvalidOperation(f"sort metric {policy.sort_metric} is unavailable for a candidate")
        return int(value)

    if policy.sort_metric != "none":
        reverse = policy.direction == "descending"
        if policy.direction == "none":
            raise InvalidOperation("sorted target policies require ascending or descending direction")
        candidates.sort(
            key=lambda item: (
                -metric_key(item) if reverse else metric_key(item),
                item["selection_order"] if policy.tie_breaker == "zone_order" else item["target_instance_id"],
            )
        )
    elif policy.tie_breaker == "zone_order":
        # The insertion order above is deterministic by player order then zone order.
        candidates.sort(key=lambda item: item["selection_order"])

    if policy.secondary_selection == "auto_ranked" and secondary_primary_id is not None:
        if secondary_primary_id not in {item["target_instance_id"] for item in candidates}:
            raise InvalidOperation("secondary preview primary is not an eligible candidate")
        limit = policy.maximum_targets
        count = len(candidates) if limit == "all" else int(limit)
        secondary_ids = [item["target_instance_id"] for item in candidates if item["target_instance_id"] != secondary_primary_id][: max(0, count - 1)]
    else:
        secondary_ids = []

    public_candidates = []
    for item in candidates:
        public_candidates.append({key: value for key, value in item.items() if not key.startswith("_")})

    return {
        "schema_version": 1,
        "offer_id": str(uuid.uuid4()),
        "state_revision": state["state_revision"],
        "target_policy_id": policy.policy_id,
        "selection_mode": policy.selection_mode,
        "secondary_primary_instance_id": secondary_primary_id,
        "metrics": {
            "eligibility_metric": policy.eligibility_metric,
            "display_metric": policy.display_metric,
            "sort_metric": policy.sort_metric,
            "direction": policy.direction,
        },
        "target_count": {
            "minimum_targets": policy.minimum_targets,
            "maximum_targets": policy.maximum_targets,
        },
        "candidates": public_candidates,
        "secondary_targets_preview": secondary_ids,
        "requires_confirmation": policy.selection_mode in ("manual_single", "manual_set", "manual_primary_auto_fill"),
    }


def resolve_target_selection(
    offer: dict[str, Any],
    policy: TargetPolicy,
    selection: dict[str, Any],
) -> list[str]:
    """Validate a client selection against the server-generated current offer."""
    if offer.get("target_policy_id") != policy.policy_id:
        raise InvalidOperation("target offer does not match the server policy")
    if not isinstance(selection, dict):
        raise InvalidOperation("selection must be an object")
    mode = selection.get("mode")
    if mode != policy.selection_mode or offer.get("selection_mode") != mode:
        raise InvalidOperation("selection mode does not match target policy")
    expected_fields = {
        "none": {"mode"},
        "manual_single": {"mode", "target_instance_id"},
        "manual_set": {"mode", "target_instance_ids"},
        "automatic": {"mode"},
        "manual_primary_auto_fill": {"mode", "target_instance_id"},
    }.get(mode)
    if expected_fields is None or set(selection) != expected_fields:
        raise InvalidOperation("selection fields do not match the declared selection mode")

    candidates = [item["target_instance_id"] for item in offer["candidates"]]
    allowed = set(candidates)
    if mode == "none":
        selected: list[str] = []
    elif mode in ("manual_single", "manual_primary_auto_fill"):
        selected = [selection.get("target_instance_id")]
    elif mode == "manual_set":
        selected = selection.get("target_instance_ids")
        if not isinstance(selected, list):
            raise InvalidOperation("manual_set requires target_instance_ids")
    elif mode == "automatic":
        count = len(candidates) if policy.maximum_targets == "all" else int(policy.maximum_targets)
        selected = candidates[:count]
    else:  # pragma: no cover - exhaustive guard
        raise InvalidOperation("unsupported selection mode")

    if any(not isinstance(item, str) for item in selected):
        raise InvalidOperation("selected target identities must be strings")
    if len(selected) != len(set(selected)):
        raise InvalidOperation("duplicate target_instance_id in selection")
    if any(target_id not in allowed for target_id in selected):
        raise InvalidOperation("selection contains an instance not present in the current target offer")

    if mode == "manual_primary_auto_fill":
        primary_id = selected[0]
        if offer.get("secondary_primary_instance_id") != primary_id:
            raise InvalidOperation("target offer secondary preview was not generated for this primary target")
        secondary_ids = offer.get("secondary_targets_preview")
        if not isinstance(secondary_ids, list):
            raise InvalidOperation("target offer has an invalid secondary target preview")
        if any(not isinstance(item, str) or item not in allowed or item == primary_id for item in secondary_ids):
            raise InvalidOperation("target offer contains invalid secondary target identities")
        selected.extend(secondary_ids)

    if len(selected) < policy.minimum_targets:
        raise InvalidOperation("selection has fewer targets than the policy minimum")
    if policy.maximum_targets != "all" and len(selected) > policy.maximum_targets:
        raise InvalidOperation("selection has more targets than the policy maximum")
    if mode == "manual_single" and len(selected) != 1:
        raise InvalidOperation("manual_single must select exactly one target")
    return list(selected)
