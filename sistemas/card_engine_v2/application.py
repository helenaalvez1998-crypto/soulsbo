"""Application boundary for the isolated Card Engine v2 alpha.

The synchronous SQLite repositories are always called off the Discord/HTTP
async event loop through AsyncAlphaGameApplication. No legacy database is
opened or migrated here.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Mapping, Sequence

from .alpha_catalog import AlphaCatalog
from .deck_builder import AlphaDeckBuilder
from .deck_repository import SQLiteDeckRepository
from .errors import InvalidOperation
from .match import AlphaMatchController
from .repository import SQLiteMatchRepository


MATCH_ACTIONS = frozenset(
    {
        "play_unit",
        "play_special",
        "sacrifice_unit",
        "activate_leader",
        "activate_card_ability",
        "pass_turn",
    }
)


class AlphaGameApplication:
    """Own the v2 alpha repositories and expose use-case-oriented operations."""

    def __init__(
        self,
        *,
        match_database_path: str | Path,
        deck_database_path: str | Path,
        catalog: AlphaCatalog | None = None,
    ) -> None:
        match_path = Path(match_database_path).expanduser().resolve()
        deck_path = Path(deck_database_path).expanduser().resolve()
        if match_path == deck_path:
            raise ValueError("match and deck repositories require separate dedicated SQLite files")
        self.catalog = catalog or AlphaCatalog()
        self.deck_builder = AlphaDeckBuilder(self.catalog)
        self.deck_repository = SQLiteDeckRepository(deck_path)
        self.match_repository = SQLiteMatchRepository(match_path)
        self.match_controller = AlphaMatchController(self.match_repository, self.catalog)

    def validate_deck(
        self,
        *,
        owner_player_id: str | int,
        card_ids: Sequence[str],
        exemplar_ids: Sequence[int],
        faction_id: str | None = None,
        leader_id: str | None = None,
        owned_exemplars: Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        return self.deck_builder.require_valid(
            card_ids,
            exemplar_ids=exemplar_ids,
            owned_exemplars=owned_exemplars,
            owner_player_id=owner_player_id,
            faction_id=faction_id,
            leader_id=leader_id,
        ).to_dict()

    def save_deck(
        self,
        *,
        owner_player_id: str | int,
        deck_id: str,
        name: str,
        card_ids: Sequence[str],
        exemplar_ids: Sequence[int],
        faction_id: str | None,
        leader_id: str | None,
        owned_exemplars: Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]],
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        validation = self.deck_builder.require_valid(
            card_ids,
            exemplar_ids=exemplar_ids,
            owned_exemplars=owned_exemplars,
            owner_player_id=owner_player_id,
            faction_id=faction_id,
            leader_id=leader_id,
        )
        saved = self.deck_repository.save_deck(
            owner_player_id=owner_player_id,
            deck_id=deck_id,
            name=name,
            card_ids=card_ids,
            exemplar_ids=validation.selected_exemplar_ids,
            faction_id=faction_id,
            leader_id=leader_id,
            expected_version=expected_version,
        )
        saved["validation"] = validation.to_dict()
        return saved

    def list_player_matches(self, player_id: str | int, *, limit: int = 20) -> list[dict[str, Any]]:
        return self.match_repository.list_matches_for_player(player_id, limit=limit)

    def get_competitive_stats_for_player(self, player_id: str | int) -> dict[str, int]:
        return self.match_repository.get_competitive_stats_for_player(player_id)

    def get_match_history_for_player(
        self, match_id: int, player_id: str | int, *, after_sequence: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        return self.match_repository.get_event_history_for_player(
            match_id, player_id, after_sequence=after_sequence, limit=limit
        )

    def get_deck(self, owner_player_id: str | int, deck_id: str) -> dict[str, Any] | None:
        return self.deck_repository.get_deck(owner_player_id, deck_id)

    def list_decks(self, owner_player_id: str | int) -> list[dict[str, Any]]:
        return self.deck_repository.list_decks(owner_player_id)

    def delete_deck(
        self, owner_player_id: str | int, deck_id: str, *, expected_version: int
    ) -> bool:
        return self.deck_repository.delete_deck(
            owner_player_id, deck_id, expected_version=expected_version
        )

    def create_match_from_saved_decks(
        self,
        *,
        match_id: int,
        player_ids: Sequence[str | int],
        deck_ids_by_player: Mapping[str | int, str],
        owned_exemplars_by_player: Mapping[
            str | int, Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]]
        ],
    ) -> dict[str, Any]:
        normalized_players = [str(item) for item in player_ids]
        if len(normalized_players) != 2 or len(set(normalized_players)) != 2:
            raise InvalidOperation("a v2 match requires exactly two different players")

        decks: dict[str, Sequence[str]] = {}
        exemplar_ids: dict[str, Sequence[int]] = {}
        inventories: dict[str, Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]]] = {}
        factions: dict[str, str] = {}
        leaders: dict[str, str] = {}
        all_selected_exemplars: set[int] = set()

        for player_id in normalized_players:
            deck_id = deck_ids_by_player.get(player_id, deck_ids_by_player.get(int(player_id)))
            if not isinstance(deck_id, str) or not deck_id:
                raise InvalidOperation(f"saved deck ID missing for player {player_id}")
            saved = self.deck_repository.get_deck(player_id, deck_id)
            if saved is None:
                raise InvalidOperation(f"saved deck not found for player {player_id}")
            if len(saved.get("exemplar_ids", [])) != len(saved.get("card_ids", [])):
                raise InvalidOperation("saved_deck_requires_exact_exemplar_provenance")

            owned = owned_exemplars_by_player.get(
                player_id, owned_exemplars_by_player.get(int(player_id))
            )
            if not isinstance(owned, (Mapping, Sequence)) or isinstance(owned, (str, bytes)):
                raise InvalidOperation(f"live exemplar inventory missing for player {player_id}")

            report = self.deck_builder.require_valid(
                saved["card_ids"],
                exemplar_ids=saved["exemplar_ids"],
                owned_exemplars=owned,
                owner_player_id=player_id,
                faction_id=saved["faction_id"],
                leader_id=saved["leader_id"],
            )
            for exemplar_id in report.selected_exemplar_ids:
                if exemplar_id in all_selected_exemplars:
                    raise InvalidOperation(f"exemplar_id_used_by_multiple_players:{exemplar_id}")
                all_selected_exemplars.add(exemplar_id)

            decks[player_id] = saved["card_ids"]
            exemplar_ids[player_id] = saved["exemplar_ids"]
            inventories[player_id] = owned
            if saved["faction_id"] is not None:
                factions[player_id] = saved["faction_id"]
            if saved["leader_id"] is not None:
                leaders[player_id] = saved["leader_id"]

        return self.match_controller.create_competitive_match(
            match_id=match_id,
            player_ids=normalized_players,
            decks=decks,
            exemplar_ids_by_player=exemplar_ids,
            owned_exemplars_by_player=inventories,
            player_factions=factions,
            leaders=leaders,
        )

    def view_match(
        self, match_id: int, *, viewer_player_id: str | int | None = None
    ) -> dict[str, Any]:
        return self.match_controller.view(match_id, viewer_player_id=viewer_player_id)

    def view_match_for_player(self, match_id: int, authenticated_player_id: str | int) -> dict[str, Any]:
        """Player-safe projection; caller must derive the ID from authentication."""
        return self.match_controller.view(match_id, viewer_player_id=authenticated_player_id)

    def execute_match_action(
        self,
        action: str,
        match_id: int,
        **kwargs: Any,
    ) -> Any:
        if action not in MATCH_ACTIONS:
            raise InvalidOperation("unsupported_match_action")
        handler = getattr(self.match_controller, action)
        return handler(match_id, **kwargs)

    def target_offer(self, match_id: int, **kwargs: Any) -> dict[str, Any]:
        return self.match_controller.target_offer(match_id, **kwargs)

    def sacrifice_target_offer(self, match_id: int, **kwargs: Any) -> dict[str, Any]:
        return self.match_controller.sacrifice_target_offer(match_id, **kwargs)

    def card_ability_target_offer(self, match_id: int, **kwargs: Any) -> dict[str, Any]:
        return self.match_controller.card_ability_target_offer(match_id, **kwargs)

    def verify_integrity(self) -> dict[str, Any]:
        return {
            "match_repository": self.match_repository.verify_integrity(),
            "deck_repository": self.deck_repository.verify_integrity(),
        }


class AsyncAlphaGameApplication:
    """Async transport facade; sqlite3 never blocks the Discord/HTTP event loop."""

    def __init__(self, application: AlphaGameApplication) -> None:
        self.application = application

    async def _offload(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        allowed = {
            "validate_deck",
            "save_deck",
            "get_deck",
            "list_decks",
            "list_player_matches",
            "get_match_history_for_player",
            "get_competitive_stats_for_player",
            "delete_deck",
            "create_match_from_saved_decks",
            "view_match",
            "view_match_for_player",
            "execute_match_action",
            "target_offer",
            "sacrifice_target_offer",
            "card_ability_target_offer",
            "verify_integrity",
        }
        if method_name not in allowed:
            raise InvalidOperation("unsupported_application_operation")
        method = getattr(self.application, method_name)
        return await asyncio.to_thread(method, *args, **kwargs)

    async def validate_deck(self, **kwargs: Any) -> dict[str, Any]:
        return await self._offload("validate_deck", **kwargs)

    async def save_deck(self, **kwargs: Any) -> dict[str, Any]:
        return await self._offload("save_deck", **kwargs)

    async def get_deck(self, owner_player_id: str | int, deck_id: str) -> dict[str, Any] | None:
        return await self._offload("get_deck", owner_player_id, deck_id)

    async def list_decks(self, owner_player_id: str | int) -> list[dict[str, Any]]:
        return await self._offload("list_decks", owner_player_id)

    async def list_player_matches(self, player_id: str | int, *, limit: int = 20) -> list[dict[str, Any]]:
        return await self._offload("list_player_matches", player_id, limit=limit)

    async def get_competitive_stats_for_player(self, player_id: str | int) -> dict[str, int]:
        return await self._offload("get_competitive_stats_for_player", player_id)

    async def get_match_history_for_player(
        self, match_id: int, player_id: str | int, *, after_sequence: int = 0, limit: int = 50
    ) -> dict[str, Any]:
        return await self._offload(
            "get_match_history_for_player", match_id, player_id,
            after_sequence=after_sequence, limit=limit,
        )

    async def delete_deck(
        self, owner_player_id: str | int, deck_id: str, *, expected_version: int
    ) -> bool:
        return await self._offload(
            "delete_deck", owner_player_id, deck_id, expected_version=expected_version
        )

    async def create_match_from_saved_decks(
        self,
        *,
        match_id: int,
        player_ids: Sequence[str | int],
        deck_ids_by_player: Mapping[str | int, str],
        owned_exemplars_by_player: Mapping[
            str | int, Mapping[int | str, Mapping[str, Any]] | Sequence[Mapping[str, Any]]
        ],
    ) -> dict[str, Any]:
        return await self._offload(
            "create_match_from_saved_decks",
            match_id=match_id,
            player_ids=player_ids,
            deck_ids_by_player=deck_ids_by_player,
            owned_exemplars_by_player=owned_exemplars_by_player,
        )

    async def view_match(
        self, match_id: int, *, viewer_player_id: str | int | None = None
    ) -> dict[str, Any]:
        return await self._offload("view_match", match_id, viewer_player_id=viewer_player_id)

    async def view_match_for_player(
        self, match_id: int, authenticated_player_id: str | int
    ) -> dict[str, Any]:
        return await self._offload("view_match_for_player", match_id, authenticated_player_id)

    async def execute_match_action(self, action: str, match_id: int, **kwargs: Any) -> Any:
        return await self._offload("execute_match_action", action, match_id, **kwargs)

    async def target_offer(self, match_id: int, **kwargs: Any) -> dict[str, Any]:
        return await self._offload("target_offer", match_id, **kwargs)

    async def sacrifice_target_offer(self, match_id: int, **kwargs: Any) -> dict[str, Any]:
        return await self._offload("sacrifice_target_offer", match_id, **kwargs)

    async def card_ability_target_offer(self, match_id: int, **kwargs: Any) -> dict[str, Any]:
        return await self._offload("card_ability_target_offer", match_id, **kwargs)

    async def verify_integrity(self) -> dict[str, Any]:
        return await self._offload("verify_integrity")


async def legacy_collection_exemplars(database: Any, user_id: int | str) -> dict[int, dict[str, Any]]:
    """Read exact physical exemplars from the legacy DB, without writing to it.

    `cartas_exemplares.id` is a global primary key. Each returned record keeps
    owner, card model, current per-copy power, and display rarity. Matchmaking
    rechecks these records and snapshots power; rarity is never used by rules.
    """
    owner = str(int(user_id))
    rows = await database.coliseu_listar_exemplares(int(user_id))
    exemplars: dict[int, dict[str, Any]] = {}

    def _value(row: Any, key: str, default: Any = None) -> Any:
        if isinstance(row, Mapping):
            return row.get(key, default)
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default

    for row in rows:
        try:
            exemplar_id = int(_value(row, "id"))
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidOperation("legacy exemplar row is missing a valid global id") from exc
        if exemplar_id <= 0 or exemplar_id in exemplars:
            raise InvalidOperation("legacy exemplar inventory contains duplicate/invalid IDs")
        card_id = str(_value(row, "card_id") or "")
        if not card_id:
            raise InvalidOperation(f"legacy exemplar {exemplar_id} has no card_id")
        exemplars[exemplar_id] = {
            "exemplar_id": exemplar_id,
            "owner_player_id": str(_value(row, "user_id", owner)),
            "card_id": card_id,
            "rarity": str(_value(row, "rarity") or ""),
            "power": _value(row, "power"),
            "source": str(_value(row, "source") or ""),
            "origin_type": str(_value(row, "origin_type") or ""),
            "origin_card_id": str(_value(row, "origin_card_id") or ""),
            "is_sacrificable": bool(_value(row, "is_sacrificable", True)),
        }
    return exemplars


async def legacy_collection_counts(database: Any, user_id: int | str) -> dict[str, int]:
    """Compatibility-only model-count projection; not valid for competitive decks."""
    rows = await database.coliseu_listar_colecao(int(user_id))
    counts: dict[str, int] = {}
    for row in rows:
        card_id = str(row["card_id"])
        quantity = int(row["quantidade"] or 0)
        if card_id and quantity > 0:
            counts[card_id] = quantity
    return counts
