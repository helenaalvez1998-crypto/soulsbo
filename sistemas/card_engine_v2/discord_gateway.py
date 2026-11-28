"""Authenticated transport boundary for the Discord Card Engine v2 alpha.

This module contains no discord.py dependency. Discord handlers pass the
platform-authenticated user ID as ``authenticated_player_id``; IDs from
interaction payloads are never treated as an authority for ownership.

The legacy collection is read-only. Match/deck SQLite files stay separate
from the NARA database and all SQLite calls are offloaded by the async app.
"""
from __future__ import annotations

import asyncio
import secrets
from typing import Any

from .application import AsyncAlphaGameApplication, legacy_collection_exemplars
from .errors import InvalidOperation, MatchNotFound


_ALLOWED_ACTIONS = frozenset(
    {
        "play_unit",
        "play_special",
        "sacrifice_unit",
        "activate_leader",
        "activate_card_ability",
        "pass_turn",
    }
)


class CardEngineV2DiscordGateway:
    """Use-case facade for Discord interactions with authenticated identities."""

    def __init__(self, *, database: Any, application: AsyncAlphaGameApplication) -> None:
        self.database = database
        self.application = application
        self.catalog = application.application.catalog

    @staticmethod
    def _player_id(authenticated_player_id: int | str) -> str:
        raw = str(authenticated_player_id)
        if not raw.isascii() or not raw.isdigit() or int(raw) <= 0:
            raise InvalidOperation("invalid_authenticated_discord_player_id")
        return raw

    async def collection_for_player(self, authenticated_player_id: int | str) -> dict[int, dict[str, Any]]:
        player_id = self._player_id(authenticated_player_id)
        inventory = await legacy_collection_exemplars(self.database, player_id)
        allowed = self.catalog.allowed_card_ids()
        return {
            exemplar_id: record
            for exemplar_id, record in inventory.items()
            if record.get("card_id") in allowed
        }

    async def list_decks(self, authenticated_player_id: int | str) -> list[dict[str, Any]]:
        player_id = self._player_id(authenticated_player_id)
        return await self.application.list_decks(player_id)

    async def list_matches(
        self, authenticated_player_id: int | str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        player_id = self._player_id(authenticated_player_id)
        return await self.application.list_player_matches(player_id, limit=limit)

    async def match_history(
        self,
        *,
        match_id: int,
        authenticated_player_id: int | str,
        after_sequence: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        player_id = self._player_id(authenticated_player_id)
        return await self.application.get_match_history_for_player(
            match_id, player_id, after_sequence=after_sequence, limit=limit
        )

    async def save_deck(
        self,
        *,
        authenticated_player_id: int | str,
        deck_id: str,
        name: str,
        card_ids: list[str],
        exemplar_ids: list[int],
        faction_id: str,
        leader_id: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        player_id = self._player_id(authenticated_player_id)
        # Fetch live ownership immediately before saving. The application runs
        # the same authoritative AlphaDeckBuilder validation before persistence.
        inventory = await self.collection_for_player(player_id)
        return await self.application.save_deck(
            owner_player_id=player_id,
            deck_id=deck_id,
            name=name,
            card_ids=card_ids,
            exemplar_ids=exemplar_ids,
            faction_id=faction_id,
            leader_id=leader_id,
            owned_exemplars=inventory,
            expected_version=expected_version,
        )

    async def get_deck(
        self, *, authenticated_player_id: int | str, deck_id: str
    ) -> dict[str, Any] | None:
        player_id = self._player_id(authenticated_player_id)
        return await self.application.get_deck(player_id, deck_id)

    async def delete_deck(
        self,
        *,
        authenticated_player_id: int | str,
        deck_id: str,
        expected_version: int,
    ) -> bool:
        player_id = self._player_id(authenticated_player_id)
        return await self.application.delete_deck(
            player_id, deck_id, expected_version=expected_version
        )

    async def create_match_from_decks(
        self,
        *,
        authenticated_challenger_id: int | str,
        authenticated_opponent_id: int | str,
        challenger_deck_id: str,
        opponent_deck_id: str,
    ) -> dict[str, Any]:
        challenger = self._player_id(authenticated_challenger_id)
        opponent = self._player_id(authenticated_opponent_id)
        if challenger == opponent:
            raise InvalidOperation("a_player_cannot_challenge_themselves")
        if not challenger_deck_id or not opponent_deck_id:
            raise InvalidOperation("both_players_must_select_a_saved_deck")

        # Ownership and model identity are read again for both players at the
        # point of match creation; stale saved-deck provenance fails closed.
        challenger_inventory, opponent_inventory = await asyncio.gather(
            legacy_collection_exemplars(self.database, challenger),
            legacy_collection_exemplars(self.database, opponent),
        )
        match_id = await self._new_match_id()
        result = await self.application.create_match_from_saved_decks(
            match_id=match_id,
            player_ids=[challenger, opponent],
            deck_ids_by_player={
                challenger: challenger_deck_id,
                opponent: opponent_deck_id,
            },
            owned_exemplars_by_player={
                challenger: challenger_inventory,
                opponent: opponent_inventory,
            },
        )
        return {"match_id": match_id, **result}

    async def _new_match_id(self) -> int:
        # Positive interoperable JSON integer ID (below 2**53). A preflight lookup
        # rejects the vanishingly unlikely collision before the INSERT.
        for _ in range(12):
            candidate = secrets.randbelow((1 << 53) - 1) + 1
            try:
                await self.application.view_match(candidate)
            except MatchNotFound:
                return candidate
        raise InvalidOperation("could_not_allocate_unique_match_id")

    async def player_view(
        self, *, match_id: int, authenticated_player_id: int | str
    ) -> dict[str, Any]:
        player_id = self._player_id(authenticated_player_id)
        return await self.application.view_match_for_player(match_id, player_id)

    async def execute_action(
        self,
        *,
        match_id: int,
        authenticated_player_id: int | str,
        action: str,
        **payload: Any,
    ) -> Any:
        player_id = self._player_id(authenticated_player_id)
        if action not in _ALLOWED_ACTIONS:
            raise InvalidOperation("unsupported_discord_match_action")
        # This player-safe projection is also the participant authorization
        # check. No handler receives a player ID supplied by the client.
        await self.application.view_match_for_player(match_id, player_id)
        return await self.application.execute_match_action(
            action,
            match_id,
            actor_player_id=player_id,
            **payload,
        )

    async def target_offer(
        self,
        *,
        match_id: int,
        authenticated_player_id: int | str,
        source_instance_id: str,
        selected_row: str | None = None,
    ) -> dict[str, Any]:
        player_id = self._player_id(authenticated_player_id)
        await self.application.view_match_for_player(match_id, player_id)
        return await self.application.target_offer(
            match_id,
            actor_player_id=player_id,
            source_instance_id=source_instance_id,
            selected_row=selected_row,
        )

    async def sacrifice_offer(
        self, *, match_id: int, authenticated_player_id: int | str
    ) -> dict[str, Any]:
        player_id = self._player_id(authenticated_player_id)
        await self.application.view_match_for_player(match_id, player_id)
        return await self.application.sacrifice_target_offer(
            match_id, actor_player_id=player_id
        )

    async def verify_integrity(self) -> dict[str, Any]:
        return await self.application.verify_integrity()


__all__ = ["CardEngineV2DiscordGateway"]
