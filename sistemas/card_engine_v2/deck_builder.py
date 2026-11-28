"""Authoritative deck validation and preparation for the Card Engine v2 alpha.

Rules are transcribed from docs/CARD_GAME_REDESIGN.md (Setup): 30 cards,
maximum three copies per model. Every competitive slot must now reference a
unique, server-verified physical collection exemplar. The experimental
12-card/32-point proposal is not approved and is deliberately not applied.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .alpha_catalog import AlphaCatalog, RARITY_IDS, VALID_FACTIONS
from .errors import InvalidOperation

DECK_RULES_VERSION = "soulsbo-alpha-deck-rules-v0.2-exemplar-provenance"
DECK_SIZE = 30
MAX_COPIES_PER_CARD = 3
INITIAL_HAND_SIZE = 4


@dataclass(frozen=True, slots=True)
class DeckValidation:
    valid: bool
    card_count: int
    unique_card_count: int
    unit_count: int
    special_count: int
    counts_by_card_id: dict[str, int]
    faction_counts: dict[str, int]
    exemplar_count: int
    selected_exemplar_ids: tuple[int, ...]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "rules_version": DECK_RULES_VERSION,
            "card_count": self.card_count,
            "required_card_count": DECK_SIZE,
            "unique_card_count": self.unique_card_count,
            "unit_count": self.unit_count,
            "special_count": self.special_count,
            "counts_by_card_id": dict(self.counts_by_card_id),
            "faction_counts": dict(self.faction_counts),
            "exemplar_count": self.exemplar_count,
            "selected_exemplar_ids": list(self.selected_exemplar_ids),
            "errors": list(self.errors),
        }


class AlphaDeckBuilder:
    """Validates alpha decks against server-owned models and exact exemplars."""

    def __init__(self, catalog: AlphaCatalog | None = None) -> None:
        self.catalog = catalog or AlphaCatalog()

    @staticmethod
    def _owned_exemplar_lookup(
        owned_exemplars: Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]],
    ) -> dict[int, Mapping[str, Any]]:
        if isinstance(owned_exemplars, Mapping):
            items = owned_exemplars.items()
        elif isinstance(owned_exemplars, Sequence) and not isinstance(owned_exemplars, (str, bytes)):
            items = []
            for row in owned_exemplars:
                if not isinstance(row, Mapping):
                    continue
                key = row.get("exemplar_id", row.get("id"))
                items.append((key, row))
        else:
            raise InvalidOperation("owned_exemplars must be a mapping or a sequence of records")

        normalized: dict[int, Mapping[str, Any]] = {}
        for raw_id, row in items:
            if not isinstance(row, Mapping):
                continue
            try:
                exemplar_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if exemplar_id <= 0 or isinstance(raw_id, bool):
                continue
            if exemplar_id in normalized:
                raise InvalidOperation(f"duplicate_owned_exemplar_id:{exemplar_id}")
            normalized[exemplar_id] = row
        return normalized

    @staticmethod
    def exemplar_snapshot_for(
        *, card_id: str, definition: Mapping[str, Any], exemplar: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Freeze only individual mechanics and display classification for this exemplar.

        Rarity is carried for presentation/forensics only. Effective power reads
        `power_base`; no resolver is allowed to read `rarity_id`.
        """
        kind = definition.get("kind")
        if kind == "unit":
            power = exemplar.get("power")
            if not isinstance(power, int) or isinstance(power, bool) or not 1 <= power <= 15:
                raise InvalidOperation(f"invalid_exemplar_power:{card_id}")
            power_base: int | None = power
        elif kind == "special":
            # Legacy exemplar rows may contain a placeholder power for specials;
            # specials have no board power in the v2 catalog.
            power_base = None
        else:
            raise InvalidOperation(f"unsupported_exemplar_card_kind:{card_id}")

        rarity = exemplar.get("rarity")
        rarity_id = RARITY_IDS.get(str(rarity)) if rarity is not None else None
        if rarity_id is None:
            raise InvalidOperation(f"invalid_exemplar_rarity:{card_id}")
        return {"power_base": power_base, "rarity_id": rarity_id}

    def validate(
        self,
        card_ids: Sequence[str],
        *,
        leader_id: str | None = None,
        faction_id: str | None = None,
        owned_card_counts: Mapping[str, int] | None = None,
        exemplar_ids: Sequence[int] | None = None,
        owned_exemplars: Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]] | None = None,
        owner_player_id: str | int | None = None,
    ) -> DeckValidation:
        errors: list[str] = []
        if isinstance(card_ids, (str, bytes)) or not isinstance(card_ids, Sequence):
            card_ids = ()
            errors.append("deck_must_be_a_sequence_of_card_ids")
        else:
            card_ids = tuple(card_ids)

        if len(card_ids) != DECK_SIZE:
            errors.append(f"deck_must_contain_exactly_{DECK_SIZE}_cards")

        invalid_entries = [
            index for index, card_id in enumerate(card_ids)
            if not isinstance(card_id, str) or not card_id.strip()
        ]
        if invalid_entries:
            errors.append("deck_contains_invalid_card_id_entries")

        normalized = [card_id for card_id in card_ids if isinstance(card_id, str) and card_id.strip()]
        counts = Counter(normalized)
        for card_id, count in sorted(counts.items()):
            if card_id not in self.catalog.allowed_card_ids():
                errors.append(f"card_not_allowlisted:{card_id}")
            if count > MAX_COPIES_PER_CARD:
                errors.append(f"copy_limit_exceeded:{card_id}:{count}")

        unit_count = 0
        special_count = 0
        faction_counts: Counter[str] = Counter()
        definitions_by_card: dict[str, Mapping[str, Any]] = {}
        for card_id in normalized:
            try:
                definition = self.catalog.definition_for(card_id)
            except InvalidOperation:
                continue
            definitions_by_card[card_id] = definition
            kind = definition.get("kind")
            if kind == "unit":
                unit_count += 1
            elif kind == "special":
                special_count += 1
            else:
                errors.append(f"unsupported_card_kind:{card_id}")
            faction = definition.get("faction_id")
            if isinstance(faction, str) and faction:
                faction_counts[faction] += 1

        if faction_id is not None and faction_id not in VALID_FACTIONS:
            errors.append("unknown_player_faction")

        if leader_id is not None:
            if not isinstance(leader_id, str) or not leader_id:
                errors.append("invalid_leader_id")
            else:
                leader_definition = self.catalog.leader_registry.get(leader_id)
                if leader_definition is None:
                    errors.append("unknown_alpha_leader")
                elif faction_id is not None and leader_definition.get("faction_id") != faction_id:
                    errors.append("leader_faction_mismatch")

        if owned_card_counts is not None:
            for card_id, required in sorted(counts.items()):
                available = owned_card_counts.get(card_id, 0)
                if not isinstance(available, int) or isinstance(available, bool) or available < 0:
                    errors.append(f"invalid_owned_count:{card_id}")
                elif required > available:
                    errors.append(f"not_enough_owned_copies:{card_id}:{required}:{available}")

        selected_exemplars: tuple[int, ...] = ()
        exact_provenance_requested = exemplar_ids is not None or owned_exemplars is not None or owner_player_id is not None
        if exact_provenance_requested:
            if exemplar_ids is None or owned_exemplars is None or owner_player_id is None:
                errors.append("exact_exemplar_provenance_requires_ids_inventory_and_owner")
            elif isinstance(exemplar_ids, (str, bytes)) or not isinstance(exemplar_ids, Sequence):
                errors.append("exemplar_ids_must_be_a_sequence")
            else:
                raw_exemplar_ids = tuple(exemplar_ids)
                if len(raw_exemplar_ids) != len(card_ids):
                    errors.append("exemplar_ids_must_align_one_to_one_with_card_ids")
                normalized_ids: list[int] = []
                for raw_id in raw_exemplar_ids:
                    if not isinstance(raw_id, int) or isinstance(raw_id, bool) or raw_id <= 0:
                        errors.append("invalid_exemplar_id")
                    else:
                        normalized_ids.append(raw_id)
                if len(normalized_ids) == len(raw_exemplar_ids):
                    selected_exemplars = tuple(normalized_ids)
                    if len(set(selected_exemplars)) != len(selected_exemplars):
                        errors.append("duplicate_exemplar_id_in_deck")
                try:
                    exemplar_lookup = self._owned_exemplar_lookup(owned_exemplars)
                except InvalidOperation:
                    exemplar_lookup = {}
                    errors.append("invalid_owned_exemplars_inventory")
                owner = str(owner_player_id)
                if not owner.isdigit():
                    errors.append("invalid_exemplar_owner_player_id")
                for index, (card_id, exemplar_id) in enumerate(zip(card_ids, raw_exemplar_ids)):
                    if not isinstance(exemplar_id, int) or isinstance(exemplar_id, bool) or exemplar_id <= 0:
                        continue
                    exemplar = exemplar_lookup.get(exemplar_id)
                    if exemplar is None:
                        errors.append(f"exemplar_not_owned_or_missing:{exemplar_id}")
                        continue
                    record_id = exemplar.get("exemplar_id", exemplar.get("id", exemplar_id))
                    record_owner = exemplar.get("owner_player_id", exemplar.get("user_id"))
                    record_card_id = exemplar.get("card_id")
                    if str(record_id) != str(exemplar_id):
                        errors.append(f"exemplar_identity_mismatch:{exemplar_id}")
                    if str(record_owner) != owner:
                        errors.append(f"exemplar_owner_mismatch:{exemplar_id}")
                    if record_card_id != card_id:
                        errors.append(f"exemplar_card_mismatch:{exemplar_id}:{card_id}")
                    definition = definitions_by_card.get(card_id) if isinstance(card_id, str) else None
                    if definition is not None:
                        try:
                            self.exemplar_snapshot_for(
                                card_id=card_id,
                                definition=definition,
                                exemplar=exemplar,
                            )
                        except InvalidOperation as exc:
                            errors.append(str(exc))

        # Keep error order stable for deterministic reports.
        stable_errors = tuple(dict.fromkeys(errors))
        return DeckValidation(
            valid=not stable_errors,
            card_count=len(card_ids),
            unique_card_count=len(counts),
            unit_count=unit_count,
            special_count=special_count,
            counts_by_card_id=dict(sorted(counts.items())),
            faction_counts=dict(sorted(faction_counts.items())),
            exemplar_count=len(selected_exemplars),
            selected_exemplar_ids=selected_exemplars,
            errors=stable_errors,
        )

    def require_valid(self, card_ids: Sequence[str], **kwargs: Any) -> DeckValidation:
        report = self.validate(card_ids, **kwargs)
        if not report.valid:
            raise InvalidOperation("invalid_alpha_deck:" + ";".join(report.errors))
        return report

    def prepare(
        self,
        card_ids: Sequence[str],
        *,
        shuffle_seed: int | str | bytes | None = None,
        **validation_kwargs: Any,
    ) -> tuple[str, ...]:
        """Legacy/model-only shuffle for deterministic harnesses, not matchmaking."""
        self.require_valid(card_ids, **validation_kwargs)
        prepared = list(card_ids)
        if shuffle_seed is None:
            random.SystemRandom().shuffle(prepared)
        else:
            random.Random(shuffle_seed).shuffle(prepared)
        return tuple(prepared)

    def prepare_exemplar_slots(
        self,
        card_ids: Sequence[str],
        exemplar_ids: Sequence[int],
        *,
        owner_player_id: str | int,
        owned_exemplars: Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]],
        shuffle_seed: int | str | bytes | None = None,
        leader_id: str | None = None,
        faction_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Validate and shuffle aligned card/exemplar slots without losing identity."""
        report = self.require_valid(
            card_ids,
            exemplar_ids=exemplar_ids,
            owned_exemplars=owned_exemplars,
            owner_player_id=owner_player_id,
            leader_id=leader_id,
            faction_id=faction_id,
        )
        lookup = self._owned_exemplar_lookup(owned_exemplars)
        slots: list[dict[str, Any]] = []
        for card_id, exemplar_id in zip(card_ids, report.selected_exemplar_ids):
            definition = self.catalog.definition_for(card_id)
            record = lookup[exemplar_id]
            slots.append(
                {
                    "card_id": card_id,
                    "exemplar_id": exemplar_id,
                    "exemplar_snapshot": self.exemplar_snapshot_for(
                        card_id=card_id,
                        definition=definition,
                        exemplar=record,
                    ),
                }
            )
        if shuffle_seed is None:
            random.SystemRandom().shuffle(slots)
        else:
            random.Random(shuffle_seed).shuffle(slots)
        return tuple(slots)
