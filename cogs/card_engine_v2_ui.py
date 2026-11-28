"""Discord UI for the isolated Card Engine v2 alpha.

The current /jogo command remains the public entry point. This module adds a
private Deck Builder / challenge / match-play surface to that panel. All
player IDs originate from Discord's authenticated Interaction.user; the UI
never accepts an owner ID from user-entered text or a select payload.

Pending challenge buttons are process-local and expire after ten minutes.
Decks and matches themselves are persisted by the v2 SQLite repositories.
"""
from __future__ import annotations

import asyncio
import secrets
import time
import uuid
from pathlib import Path
from typing import Any

import discord

from sistemas.card_engine_v2.application import (
    AlphaGameApplication,
    AsyncAlphaGameApplication,
)
from sistemas.card_engine_v2.discord_gateway import CardEngineV2DiscordGateway
from sistemas.card_engine_v2.errors import InvalidOperation, MatchNotFound


COLOUR = 0x8E6A3A
ROW_LABELS = {
    "melee": "Corpo a Corpo",
    "ranged": "Longa Distância",
    "siege": "Cerco",
}


def get_card_engine_service(bot: Any) -> "CardEngineV2DiscordService":
    """Create one lazy service instance per running bot process."""
    service = getattr(bot, "card_engine_v2_discord_service", None)
    if service is not None:
        return service

    gateway = getattr(bot, "card_engine_v2_shared_gateway", None)
    if gateway is None:
        import config
        root = Path(config.get_data_dir()).expanduser().resolve() / "card_engine_v2"
        root.mkdir(parents=True, exist_ok=True)
        application = AlphaGameApplication(
            match_database_path=root / "matches.sqlite3",
            deck_database_path=root / "decks.sqlite3",
        )
        async_application = AsyncAlphaGameApplication(application)
        gateway = CardEngineV2DiscordGateway(database=bot.db, application=async_application)
        setattr(bot, "card_engine_v2_shared_gateway", gateway)
    service = CardEngineV2DiscordService(bot=bot, gateway=gateway)
    setattr(bot, "card_engine_v2_discord_service", service)
    return service


class CardEngineV2DiscordService:
    def __init__(self, *, bot: Any, gateway: CardEngineV2DiscordGateway) -> None:
        self.bot = bot
        self.gateway = gateway
        self.catalog = gateway.catalog
        self.pending_invites: dict[str, dict[str, Any]] = {}
        self._invite_lock = asyncio.Lock()

    async def register_invite(
        self,
        *,
        challenger_id: int,
        opponent_id: int,
        challenger_deck_id: str,
        guild_id: int,
        channel_id: int,
    ) -> str:
        if challenger_id == opponent_id:
            raise InvalidOperation("a_player_cannot_challenge_themselves")
        invite_id = secrets.token_urlsafe(9)
        async with self._invite_lock:
            self._purge_expired_invites()
            if any(
                int(item["challenger_id"]) == int(challenger_id)
                and item["status"] in {"pending", "processing"}
                for item in self.pending_invites.values()
            ):
                raise InvalidOperation("challenger_already_has_pending_invitation")
            now = time.monotonic()
            self.pending_invites[invite_id] = {
                "invite_id": invite_id,
                "challenger_id": int(challenger_id),
                "opponent_id": int(opponent_id),
                "challenger_deck_id": str(challenger_deck_id),
                "guild_id": int(guild_id),
                "channel_id": int(channel_id),
                "created_at": now,
                "expires_at": now + 600,
                "status": "pending",
                "message": None,
            }
        return invite_id

    def _purge_expired_invites(self) -> None:
        now = time.monotonic()
        for key, invite in list(self.pending_invites.items()):
            if invite["expires_at"] <= now or invite["status"] in {"accepted", "declined", "failed"}:
                self.pending_invites.pop(key, None)

    async def get_invite(self, invite_id: str, *, opponent_id: int) -> dict[str, Any]:
        async with self._invite_lock:
            invite = self.pending_invites.get(str(invite_id))
            if invite is not None and invite["expires_at"] <= time.monotonic():
                self.pending_invites.pop(str(invite_id), None)
                invite = None
            if invite is None or invite["status"] != "pending":
                raise InvalidOperation("challenge_invitation_expired_or_unavailable")
            if int(invite["opponent_id"]) != int(opponent_id):
                raise InvalidOperation("only_the_invited_player_can_respond")
            return dict(invite)

    async def cancel_invite(self, invite_id: str) -> None:
        async with self._invite_lock:
            self.pending_invites.pop(str(invite_id), None)

    async def set_invite_message(self, invite_id: str, message: discord.Message) -> None:
        async with self._invite_lock:
            invite = self.pending_invites.get(invite_id)
            if invite is not None:
                invite["message"] = message

    async def claim_invite(self, invite_id: str, *, opponent_id: int) -> dict[str, Any]:
        async with self._invite_lock:
            invite = self.pending_invites.get(str(invite_id))
            if invite is None or invite["expires_at"] <= time.monotonic() or invite["status"] != "pending":
                raise InvalidOperation("challenge_invitation_expired_or_unavailable")
            if int(invite["opponent_id"]) != int(opponent_id):
                raise InvalidOperation("only_the_invited_player_can_respond")
            invite["status"] = "processing"
            return dict(invite)

    async def complete_invite(self, invite_id: str, status: str) -> dict[str, Any]:
        async with self._invite_lock:
            invite = self.pending_invites.get(invite_id)
            if invite is None:
                raise InvalidOperation("challenge_invitation_already_processed")
            expected_status = "pending" if status == "declined" else "processing" if status == "accepted" else None
            if expected_status is None or invite["status"] != expected_status:
                raise InvalidOperation("challenge_invitation_already_processed")
            invite["status"] = status
            return dict(invite)

    async def release_invite(self, invite_id: str) -> None:
        async with self._invite_lock:
            invite = self.pending_invites.get(invite_id)
            if invite is not None and invite["status"] == "processing" and invite["expires_at"] > time.monotonic():
                invite["status"] = "pending"

    async def list_matches(self, player_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
        return await self.gateway.list_matches(player_id, limit=limit)

    def card_name(self, card_id: str) -> str:
        return self.catalog.display_name(card_id)

    def leader_options(self) -> list[dict[str, Any]]:
        rows = []
        for leader_id, definition in sorted(self.catalog.leader_registry.items()):
            rows.append({
                "leader_id": leader_id,
                "name": str(definition.get("name") or leader_id),
                "faction_id": str(definition.get("faction_id") or ""),
                "description": str(definition.get("description_current") or "Líder alpha"),
            })
        return rows

    async def render_match(self, match_id: int, player_id: int, guild: discord.Guild | None, *, hand_page: int = 0) -> tuple[discord.Embed, "MatchPlayView", dict[str, Any]]:
        state = await self.gateway.player_view(
            match_id=int(match_id), authenticated_player_id=int(player_id)
        )
        players = state["players"]
        own_id = str(player_id)
        opponent_id = next(pid for pid in players if pid != own_id)
        own = players[own_id]
        opponent = players[opponent_id]

        def player_label(pid: str) -> str:
            member = guild.get_member(int(pid)) if guild and pid.isdigit() else None
            if member is not None:
                return member.display_name
            cached = self.bot.get_user(int(pid)) if pid.isdigit() else None
            return cached.display_name if cached else f"Jogador {pid[-4:]}"

        current = state.get("current_player_id")
        is_own_turn = state.get("status") == "active" and current == own_id
        status_text = "Partida encerrada" if state.get("status") == "finished" else (
            f"Vez de **{player_label(str(current))}**" if current else "Aguardando próximo turno"
        )
        embed = discord.Embed(
            title=f"⚔️ Card Engine v2 · Partida #{match_id}",
            description=(
                f"**Rodada:** {state.get('round_number', '?')} · **Estado:** {status_text}\n"
                f"**Sua energia:** {own.get('energy', 0)}/{own.get('maximum_energy', 5)} · "
                f"**Sua mão:** {own.get('hand_count', 0)} cartas · "
                f"**Seu deck:** {own.get('draw_pile_count', 0)} cartas\n"
                f"**Fatigue:** {own.get('deck_fatigue_count', 0)} · **Vida:** {own.get('life', 0)}"
            ),
            color=COLOUR,
        )
        own_board = self._format_board(own.get("board", []))
        opponent_board = self._format_board(opponent.get("board", []))
        embed.add_field(
            name=f"Você · {player_label(own_id)} · {own.get('life', 0)} vida · {own.get('score', 0)} poder",
            value=own_board,
            inline=False,
        )
        embed.add_field(
            name=f"Adversário · {player_label(opponent_id)} · {opponent.get('life', 0)} vida · {opponent.get('score', 0)} poder",
            value=opponent_board,
            inline=False,
        )
        hand = own.get("hand", [])
        if hand:
            hand_lines = []
            for item in hand[:20]:
                cost = item.get("energy_cost")
                cost_text = f"{cost} energia" if cost is not None else "custo não configurado"
                power = item.get("exemplar_power_base")
                power_text = f" · poder {power}" if power is not None else ""
                hand_lines.append(f"• **{item['name']}** · {cost_text}{power_text}")
            if len(hand) > 20:
                hand_lines.append(f"… e mais {len(hand) - 20} carta(s) na mão")
            hand_text = "\n".join(hand_lines)
        else:
            hand_text = "Sua mão está vazia."
        embed.add_field(name="Sua mão (visível apenas para você)", value=hand_text[:1024], inline=False)
        if state.get("status") == "finished":
            winner = state.get("match_winner_player_id")
            if winner:
                embed.add_field(name="Resultado", value=f"Vitória de **{player_label(str(winner))}**", inline=False)
            else:
                embed.add_field(name="Resultado", value="Empate", inline=False)
        embed.set_footer(text=f"Card Engine v2 alpha · revisão de estado {state.get('state_revision', 0)}")
        view = MatchPlayView(
            service=self,
            player_id=player_id,
            match_id=match_id,
            state=state,
            is_own_turn=is_own_turn,
            hand_page=hand_page,
            guild=guild,
        )
        return embed, view, state

    @staticmethod
    def _format_board(board: list[dict[str, Any]]) -> str:
        if not board:
            return "*Nenhuma unidade no campo.*"
        by_row: dict[str, list[str]] = {"melee": [], "ranged": [], "siege": []}
        for unit in board:
            row = str(unit.get("row") or "melee")
            by_row.setdefault(row, []).append(
                f"{unit.get('name', 'Unidade')} **{unit.get('effective_power', 0)}**"
            )
        lines = []
        for row in ("melee", "ranged", "siege"):
            if by_row.get(row):
                lines.append(f"**{ROW_LABELS.get(row, row)}:** " + " · ".join(by_row[row]))
        return "\n".join(lines)[:1024]


class AlphaHomeView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, user_id: int) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.user_id = int(user_id)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este painel pertence a outro jogador.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Montar deck", emoji="🧩", style=discord.ButtonStyle.primary, row=0)
    async def create_deck(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(DeckNameModal(self.service, self.user_id))

    @discord.ui.button(label="Meus decks", emoji="📚", style=discord.ButtonStyle.secondary, row=0)
    async def my_decks(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            decks = await self.service.gateway.list_decks(self.user_id)
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível consultar seus decks: `{_safe_error(exc)}`", ephemeral=True
            )
        if not decks:
            return await interaction.followup.send("Você ainda não tem decks salvos no Card Engine v2.", ephemeral=True)
        embed = discord.Embed(title="📚 Seus decks · Card Engine v2", color=COLOUR)
        for deck in decks[:20]:
            embed.add_field(
                name=f"{deck['name']} · versão {deck['version']}",
                value=(f"ID: `{deck['deck_id']}` · {len(deck['card_ids'])} cartas\n"
                       f"Líder: `{deck.get('leader_id') or 'não definido'}` · Facção: `{deck.get('faction_id') or 'não definida'}`"),
                inline=False,
            )
        if len(decks) > 20:
            embed.set_footer(text=f"Exibindo 20 de {len(decks)} decks")
        await interaction.followup.send(
            embed=embed,
            view=DeckManagementView(self.service, self.user_id, decks),
            ephemeral=True,
        )

    @discord.ui.button(label="Desafiar jogador", emoji="⚔️", style=discord.ButtonStyle.success, row=0)
    async def challenge(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            decks = await self.service.gateway.list_decks(self.user_id)
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível consultar seus decks: `{_safe_error(exc)}`", ephemeral=True
            )
        if not decks:
            return await interaction.followup.send(
                "Você precisa salvar um deck competitivo de 30 cartas antes de desafiar alguém.", ephemeral=True
            )
        await interaction.followup.send(
            "Escolha um dos seus decks e o adversário. O convite será publicado neste canal por dez minutos.",
            view=ChallengeSetupView(self.service, self.user_id, decks, interaction.channel),
            ephemeral=True,
        )

    @discord.ui.button(label="Avisos da alpha", emoji="ℹ️", style=discord.ButtonStyle.secondary, row=1)
    async def alpha_info(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        embed = discord.Embed(
            title="Card Engine v2 · Alpha privada",
            description=(
                "Esta é uma integração experimental. O catálogo competitivo aceita somente 27 modelos allowlisted. "
                "Cada slot exige um exemplar físico real da sua coleção; o deck possui 30 cartas e até três cópias "
                "por modelo. Os preços de energia ainda são experimentais. As partidas são persistidas em bancos "
                "SQLite separados do banco legado. Convites expiram após dez minutos e deixam de funcionar se o bot reiniciar."
            ),
            color=COLOUR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Minhas partidas", emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def my_matches(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            matches = await self.service.list_matches(self.user_id, limit=25)
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível consultar suas partidas: `{_safe_error(exc)}`", ephemeral=True
            )
        if not matches:
            return await interaction.followup.send(
                "Você ainda não possui partidas no Card Engine v2 alpha.", ephemeral=True
            )
        await interaction.followup.send(
            "Selecione uma partida para reabrir sua visão privada. A mão do adversário continua oculta.",
            view=MyMatchesView(self.service, self.user_id, matches),
            ephemeral=True,
        )


class MyMatchSelect(discord.ui.Select):
    def __init__(self, parent: "MyMatchesView") -> None:
        self.parent = parent
        options = []
        for item in parent.matches[:25]:
            status = "Em andamento" if item["status"] == "active" else "Encerrada"
            opponent_id = item.get("opponent_player_id")
            opponent = f"Jogador ...{str(opponent_id)[-4:]}" if opponent_id else "Adversário"
            options.append(discord.SelectOption(
                label=f"Partida #{item['match_id']} · {status}"[:100],
                value=str(item["match_id"]),
                description=opponent[:100],
            ))
        super().__init__(placeholder="Escolha uma partida", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent.open_match(interaction, int(self.values[0]))


class MyMatchesView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, player_id: int, matches: list[dict[str, Any]]) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.player_id = int(player_id)
        self.matches = list(matches)
        self.add_item(MyMatchSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Esta lista pertence a outro jogador.", ephemeral=True)
            return False
        return True

    async def open_match(self, interaction: discord.Interaction, match_id: int) -> None:
        if match_id not in {int(item["match_id"]) for item in self.matches}:
            return await interaction.response.send_message("Partida indisponível nesta lista.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            embed, view, _state = await self.service.render_match(
                match_id, self.player_id, interaction.guild
            )
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível reabrir a partida: `{_safe_error(exc)}`", ephemeral=True
            )
        message = await interaction.followup.send(embed=embed, view=view, ephemeral=True, wait=True)
        await view.bind_message(message)
        self.stop()


class DeckManagementSelect(discord.ui.Select):
    def __init__(self, parent: "DeckManagementView") -> None:
        self.parent = parent
        options = [
            discord.SelectOption(
                label=f"{deck['name']} · v{deck['version']}"[:100],
                value=deck["deck_id"],
                description=f"30 cartas · líder {deck.get('leader_id') or 'não definido'}"[:100],
                default=deck["deck_id"] == parent.selected_deck_id,
            )
            for deck in parent.decks[:25]
        ]
        super().__init__(placeholder="Selecione o deck para gerenciar", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent.selected_deck_id = self.values[0]
        self.parent._rebuild()
        await interaction.response.edit_message(content=self.parent.summary(), embed=None, view=self.parent)


class DeckManagementView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, user_id: int, decks: list[dict[str, Any]]) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.user_id = int(user_id)
        self.decks = list(decks)
        self.selected_deck_id = self.decks[0]["deck_id"] if self.decks else None
        self._rebuild()

    def _selected(self) -> dict[str, Any] | None:
        return next((item for item in self.decks if item["deck_id"] == self.selected_deck_id), None)

    def summary(self) -> str:
        deck = self._selected()
        if deck is None:
            return "Nenhum deck selecionado. Atualize a lista ou crie um deck novo."
        return (
            f"**{deck['name']}** · versão {deck['version']} · {len(deck['card_ids'])}/30 cartas\n"
            f"Líder: `{deck.get('leader_id') or 'não definido'}` · Facção: `{deck.get('faction_id') or 'não definida'}`\n"
            "Você pode editar a composição preservando os exemplares ou excluir o deck."
        )

    def _rebuild(self) -> None:
        self.clear_items()
        if len(self.decks) > 1:
            self.add_item(DeckManagementSelect(self))
        edit = discord.ui.Button(label="Editar deck", emoji="✏️", style=discord.ButtonStyle.primary, row=1, disabled=self._selected() is None)
        delete = discord.ui.Button(label="Excluir deck", emoji="🗑️", style=discord.ButtonStyle.danger, row=1, disabled=self._selected() is None)
        refresh = discord.ui.Button(label="Atualizar lista", emoji="🔄", style=discord.ButtonStyle.secondary, row=1)
        edit.callback = self._edit
        delete.callback = self._delete
        refresh.callback = self._refresh
        self.add_item(edit)
        self.add_item(delete)
        self.add_item(refresh)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Esta lista de decks pertence a outro jogador.", ephemeral=True)
            return False
        return True

    async def _refresh(self, interaction: discord.Interaction) -> None:
        try:
            self.decks = await self.service.gateway.list_decks(self.user_id)
        except Exception as exc:
            return await interaction.response.send_message(
                f"Não foi possível atualizar seus decks: `{_safe_error(exc)}`", ephemeral=True
            )
        if not self.decks:
            self.stop()
            return await interaction.response.edit_message(content="Você não possui decks salvos.", embed=None, view=None)
        if not any(item["deck_id"] == self.selected_deck_id for item in self.decks):
            self.selected_deck_id = self.decks[0]["deck_id"]
        self._rebuild()
        await interaction.response.edit_message(content=self.summary(), embed=None, view=self)

    async def _edit(self, interaction: discord.Interaction) -> None:
        deck_meta = self._selected()
        if deck_meta is None:
            return await interaction.response.send_message("Selecione um deck válido.", ephemeral=True)
        await interaction.response.defer()
        try:
            deck = await self.service.gateway.get_deck(
                authenticated_player_id=self.user_id, deck_id=deck_meta["deck_id"]
            )
            inventory = await self.service.gateway.collection_for_player(self.user_id)
            if deck is None:
                raise InvalidOperation("saved_deck_not_found")
            exemplar_ids = list(deck.get("exemplar_ids", []))
            card_ids = list(deck.get("card_ids", []))
            if len(exemplar_ids) != 30 or len(card_ids) != 30:
                raise InvalidOperation("deck_requires_rebuild_with_30_physical_exemplars")
            for exemplar_id, card_id in zip(exemplar_ids, card_ids):
                record = inventory.get(int(exemplar_id))
                if record is None or record.get("card_id") != card_id:
                    raise InvalidOperation("one_or_more_saved_exemplars_are_no_longer_owned")
            wizard = DeckBuilderWizardView(
                self.service,
                user_id=self.user_id,
                deck_name=deck["name"],
                exemplars=list(inventory.items()),
                existing_deck=deck,
            )
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível abrir a edição. Atualize o deck ou reconstrua a seleção de exemplares. Motivo: `{_safe_error(exc)}`",
                ephemeral=True,
            )
        await interaction.edit_original_response(
            content=wizard._initial_message(), embed=None, view=wizard
        )
        self.stop()

    async def _delete(self, interaction: discord.Interaction) -> None:
        deck = self._selected()
        if deck is None:
            return await interaction.response.send_message("Selecione um deck para excluir.", ephemeral=True)
        await interaction.response.send_message(
            f"Confirma excluir o deck **{deck['name']}**? Esta ação não remove cartas da coleção e não pode ser desfeita.",
            view=DeckDeleteConfirmView(self.service, self.user_id, deck),
            ephemeral=True,
        )


class DeckDeleteConfirmView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, user_id: int, deck: dict[str, Any]) -> None:
        super().__init__(timeout=120)
        self.service = service
        self.user_id = int(user_id)
        self.deck = dict(deck)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Somente o proprietário pode excluir este deck.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirmar exclusão", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        try:
            await self.service.gateway.delete_deck(
                authenticated_player_id=self.user_id,
                deck_id=self.deck["deck_id"],
                expected_version=int(self.deck["version"]),
            )
        except Exception as exc:
            return await interaction.edit_original_response(
                content=f"O deck não foi excluído. A versão pode ter mudado; atualize a lista. Motivo: `{_safe_error(exc)}`",
                view=None,
            )
        self.stop()
        await interaction.edit_original_response(
            content=f"Deck **{self.deck['name']}** excluído. Nenhum exemplar foi removido da coleção.",
            view=None,
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.edit_message(content="Exclusão cancelada.", view=None)


class DeckNameModal(discord.ui.Modal, title="Criar deck competitivo alpha"):
    deck_name = discord.ui.TextInput(
        label="Nome do deck",
        placeholder="Ex.: Ordem da Fornalha",
        min_length=1,
        max_length=40,
        required=True,
    )

    def __init__(self, service: CardEngineV2DiscordService, user_id: int) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.user_id = int(user_id)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Este formulário pertence a outro jogador.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            inventory = await self.service.gateway.collection_for_player(self.user_id)
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível consultar sua coleção: `{_safe_error(exc)}`", ephemeral=True
            )
        usable = [
            (exemplar_id, row)
            for exemplar_id, row in inventory.items()
            if row.get("card_id") in self.service.catalog.allowed_card_ids()
        ]
        if len(usable) < 30:
            return await interaction.followup.send(
                f"Você possui **{len(usable)}** exemplares compatíveis com a alpha. São necessários 30 exemplares físicos permitidos para montar um deck. Os modelos fora da allowlist não podem ser usados nesta versão.",
                ephemeral=True,
            )
        await interaction.followup.send(
            content=f"Deck **{self.deck_name.value.strip()}** · selecione 30 exemplares diferentes. O mesmo modelo pode aparecer até três vezes, desde que sejam cópias físicas distintas.",
            view=DeckBuilderWizardView(
                self.service,
                user_id=self.user_id,
                deck_name=self.deck_name.value.strip(),
                exemplars=usable,
            ),
            ephemeral=True,
        )


class ExemplarSelect(discord.ui.Select):
    def __init__(self, parent: "DeckBuilderWizardView") -> None:
        self.parent = parent
        options = []
        for exemplar_id, row in parent.current_page_rows():
            card_id = str(row["card_id"])
            power = row.get("power")
            desc = f"Exemplar #{exemplar_id} · {row.get('rarity') or 'sem raridade'}"
            if power is not None:
                desc += f" · Poder {power}"
            options.append(discord.SelectOption(
                label=parent.service.card_name(card_id)[:100],
                value=str(exemplar_id),
                description=desc[:100],
            ))
        if not options:
            options = [discord.SelectOption(label="Nenhum exemplar disponível", value="none", description="Desfaça uma seleção ou encerre o deck")]
        super().__init__(
            placeholder="Escolha uma cópia física para adicionar",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
            disabled=not parent.current_page_rows(),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent.add_exemplar(interaction, int(self.values[0]))


class SelectedExemplarRemoveSelect(discord.ui.Select):
    def __init__(self, parent: "DeckBuilderWizardView", indexed_ids: list[tuple[int, int]]) -> None:
        self.parent = parent
        options = []
        card_lookup = {eid: row for eid, row in parent.exemplars}
        for index, exemplar_id in indexed_ids:
            row = card_lookup.get(exemplar_id, {})
            card_id = str(row.get("card_id") or "")
            label = parent.service.card_name(card_id) if card_id else "Exemplar"
            options.append(discord.SelectOption(
                label=label[:100],
                value=str(index),
                description=f"Remover exemplar físico #{exemplar_id}"[:100],
            ))
        super().__init__(
            placeholder=f"Remover uma carta selecionada · página {parent.selected_page + 1}",
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent.remove_selected(interaction, int(self.values[0]))


class DeckBuilderWizardView(discord.ui.View):
    PAGE_SIZE = 25

    def __init__(
        self,
        service: CardEngineV2DiscordService,
        *,
        user_id: int,
        deck_name: str,
        exemplars: list[tuple[int, dict[str, Any]]],
        existing_deck: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(timeout=900)
        self.service = service
        self.user_id = int(user_id)
        self.deck_name = str(deck_name)
        self.exemplars = list(exemplars)
        self.existing_deck = dict(existing_deck) if existing_deck else None
        self.selected_ids = list(self.existing_deck.get("exemplar_ids", [])) if self.existing_deck else []
        self.selected_cards = list(self.existing_deck.get("card_ids", [])) if self.existing_deck else []
        self.page = 0
        self.selected_page = 0
        self._rebuild()

    def _initial_message(self) -> str:
        label = "Editando" if self.existing_deck else "Montando"
        return (
            f"**{label} deck:** {self.deck_name} · **{len(self.selected_ids)}/30** exemplares escolhidos\n"
            "Selecione cópias físicas. Use o menu de remoção para substituir exemplares; o limite é três cópias por modelo."
        )

    def current_page_rows(self) -> list[tuple[int, dict[str, Any]]]:
        counts: dict[str, int] = {}
        for card_id in self.selected_cards:
            counts[card_id] = counts.get(card_id, 0) + 1
        selected = set(self.selected_ids)
        candidates = [
            (eid, row)
            for eid, row in self.exemplars
            if eid not in selected and counts.get(str(row.get("card_id")), 0) < 3
        ]
        total_pages = max(1, (len(candidates) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page = min(self.page, total_pages - 1)
        start = self.page * self.PAGE_SIZE
        return candidates[start:start + self.PAGE_SIZE]

    def _rebuild(self) -> None:
        self.clear_items()
        total_pages = max(1, (len(self.exemplars) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        previous = discord.ui.Button(label="Página anterior", emoji="◀️", style=discord.ButtonStyle.secondary, row=0, disabled=self.page <= 0)
        next_page = discord.ui.Button(label="Próxima página", emoji="▶️", style=discord.ButtonStyle.secondary, row=0)
        previous.callback = self._previous
        next_page.callback = self._next
        self.add_item(previous)
        self.add_item(next_page)
        self.add_item(ExemplarSelect(self))
        selected_pages = max(1, (len(self.selected_ids) + 24) // 25)
        self.selected_page = min(self.selected_page, selected_pages - 1)
        selected_slice = list(enumerate(self.selected_ids))[self.selected_page * 25:(self.selected_page + 1) * 25]
        if selected_slice:
            self.add_item(SelectedExemplarRemoveSelect(self, selected_slice))
        undo = discord.ui.Button(label="Desfazer última", emoji="↩️", style=discord.ButtonStyle.secondary, row=3, disabled=not self.selected_ids)
        finish = discord.ui.Button(label=f"Continuar ({len(self.selected_ids)}/30)", emoji="➡️", style=discord.ButtonStyle.success, row=3, disabled=len(self.selected_ids) != 30)
        cancel = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.danger, row=3)
        undo.callback = self._undo
        finish.callback = self._finish
        cancel.callback = self._cancel
        self.add_item(undo)
        self.add_item(finish)
        self.add_item(cancel)
        if selected_pages > 1:
            selected_prev = discord.ui.Button(label="Seleção anterior", style=discord.ButtonStyle.secondary, row=4, disabled=self.selected_page <= 0)
            selected_next = discord.ui.Button(label="Próximos selecionados", style=discord.ButtonStyle.secondary, row=4, disabled=self.selected_page + 1 >= selected_pages)
            selected_prev.callback = self._previous_selected
            selected_next.callback = self._next_selected
            self.add_item(selected_prev)
            self.add_item(selected_next)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este Deck Builder pertence a outro jogador.", ephemeral=True)
            return False
        return True

    async def _redraw(self, interaction: discord.Interaction, note: str = "") -> None:
        self._rebuild()
        counts: dict[str, int] = {}
        for card_id in self.selected_cards:
            counts[card_id] = counts.get(card_id, 0) + 1
        distribution = ", ".join(
            f"{self.service.card_name(card_id)} ×{count}"
            for card_id, count in sorted(counts.items())
        ) or "Nenhuma carta selecionada"
        available = len(self.current_page_rows())
        content = (
            f"**{self.deck_name}** · **{len(self.selected_ids)}/30** exemplares escolhidos\n"
            f"Máximo de três cópias por modelo; cada cópia precisa ter ID físico diferente.\n"
            f"Página {self.page + 1} · {available} opções disponíveis nesta página.\n"
            f"**Composição:** {distribution}"
            + (f"\n**Edição:** `{self.existing_deck['deck_id']}` · versão {self.existing_deck['version']}" if self.existing_deck else "")
        )
        if note:
            content = f"{note}\n\n{content}"
        await interaction.response.edit_message(content=content[:1900], view=self)

    async def add_exemplar(self, interaction: discord.Interaction, exemplar_id: int) -> None:
        record = next((row for eid, row in self.exemplars if eid == exemplar_id), None)
        if record is None or exemplar_id in self.selected_ids:
            return await interaction.response.send_message("Este exemplar não está disponível para seleção.", ephemeral=True)
        card_id = str(record["card_id"])
        if self.selected_cards.count(card_id) >= 3:
            return await interaction.response.send_message("O limite de três cópias deste modelo já foi atingido.", ephemeral=True)
        if len(self.selected_ids) >= 30:
            return await interaction.response.send_message("O deck já possui 30 cartas.", ephemeral=True)
        self.selected_ids.append(exemplar_id)
        self.selected_cards.append(card_id)
        await self._redraw(interaction, f"Adicionado: **{self.service.card_name(card_id)}** · exemplar #{exemplar_id}.")

    async def _previous(self, interaction: discord.Interaction) -> None:
        self.page = max(0, self.page - 1)
        await self._redraw(interaction)

    async def _next(self, interaction: discord.Interaction) -> None:
        self.page += 1
        self.current_page_rows()
        await self._redraw(interaction)

    async def remove_selected(self, interaction: discord.Interaction, index: int) -> None:
        if not 0 <= index < len(self.selected_ids):
            return await interaction.response.send_message("Esta seleção não está mais disponível.", ephemeral=True)
        exemplar_id = self.selected_ids.pop(index)
        card_id = self.selected_cards.pop(index)
        self.selected_page = min(self.selected_page, max(0, (len(self.selected_ids) - 1) // 25))
        await self._redraw(interaction, f"Removido: **{self.service.card_name(card_id)}** · exemplar #{exemplar_id}.")

    async def _previous_selected(self, interaction: discord.Interaction) -> None:
        self.selected_page = max(0, self.selected_page - 1)
        await self._redraw(interaction)

    async def _next_selected(self, interaction: discord.Interaction) -> None:
        self.selected_page += 1
        await self._redraw(interaction)

    async def _undo(self, interaction: discord.Interaction) -> None:
        if not self.selected_ids:
            return await interaction.response.send_message("Não há seleção para desfazer.", ephemeral=True)
        exemplar_id = self.selected_ids.pop()
        card_id = self.selected_cards.pop()
        await self._redraw(interaction, f"Removido: **{self.service.card_name(card_id)}** · exemplar #{exemplar_id}.")

    async def _finish(self, interaction: discord.Interaction) -> None:
        if len(self.selected_ids) != 30:
            return await interaction.response.send_message("Selecione exatamente 30 exemplares.", ephemeral=True)
        await interaction.response.edit_message(
            content=f"Deck **{self.deck_name}** possui 30 exemplares. Agora escolha o líder; a facção será vinculada ao líder selecionado.",
            view=DeckLeaderSelectionView(
                self.service,
                user_id=self.user_id,
                deck_name=self.deck_name,
                exemplar_ids=list(self.selected_ids),
                card_ids=list(self.selected_cards),
                existing_deck=self.existing_deck,
            ),
        )

    async def _cancel(self, interaction: discord.Interaction) -> None:
        self.stop()
        await interaction.response.edit_message(content="Montagem cancelada. Nenhum deck foi salvo.", view=None)


class LeaderSelect(discord.ui.Select):
    def __init__(self, parent: "DeckLeaderSelectionView") -> None:
        self.parent = parent
        options = [
            discord.SelectOption(
                label=f"{leader['name']} · {leader['faction_id']}"[:100],
                value=leader["leader_id"],
                description=leader["description"][:100],
                default=leader["leader_id"] == parent.leader_id,
            )
            for leader in parent.service.leader_options()
        ]
        super().__init__(placeholder="Escolha o líder do deck", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent.leader_id = self.values[0]
        await interaction.response.edit_message(
            content=self.parent.summary(),
            view=self.parent,
        )


class DeckLeaderSelectionView(discord.ui.View):
    def __init__(
        self,
        service: CardEngineV2DiscordService,
        *,
        user_id: int,
        deck_name: str,
        exemplar_ids: list[int],
        card_ids: list[str],
        existing_deck: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(timeout=600)
        self.service = service
        self.user_id = int(user_id)
        self.deck_name = deck_name
        self.exemplar_ids = exemplar_ids
        self.card_ids = card_ids
        self.existing_deck = dict(existing_deck) if existing_deck else None
        self.leader_id: str | None = self.existing_deck.get("leader_id") if self.existing_deck else None
        self.add_item(LeaderSelect(self))
        save = discord.ui.Button(label="Validar e salvar deck", emoji="💾", style=discord.ButtonStyle.success, row=1, disabled=True)
        save.callback = self._save
        cancel = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.danger, row=1)
        cancel.callback = self._cancel
        self.save_button = save
        self.add_item(save)
        self.add_item(cancel)

    def summary(self) -> str:
        self.save_button.disabled = not bool(self.leader_id)
        leader = next((x for x in self.service.leader_options() if x["leader_id"] == self.leader_id), None)
        if not leader:
            return f"Deck **{self.deck_name}** · 30 cartas. Escolha um líder para definir a facção."
        mode = (f"Atualizar deck `{self.existing_deck['deck_id']}` da versão {self.existing_deck['version']}"
                if self.existing_deck else "Criar novo deck")
        return (f"{mode} · **{self.deck_name}** · 30 cartas\n"
                f"**Líder:** {leader['name']}\n**Facção:** `{leader['faction_id']}`\n"
                "Confirme para revalidar a posse dos 30 exemplares e salvar o deck.")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este deck pertence a outro jogador.", ephemeral=True)
            return False
        return True

    async def _save(self, interaction: discord.Interaction) -> None:
        if not self.leader_id:
            return await interaction.response.send_message("Escolha um líder primeiro.", ephemeral=True)
        # This is a component interaction on an already-ephemeral message;
        # defer the message update, then replace that same message below.
        await interaction.response.defer()
        leader = next(x for x in self.service.leader_options() if x["leader_id"] == self.leader_id)
        deck_id = self.existing_deck["deck_id"] if self.existing_deck else f"alpha-{uuid.uuid4().hex[:16]}"
        expected_version = self.existing_deck["version"] if self.existing_deck else None
        try:
            saved = await self.service.gateway.save_deck(
                authenticated_player_id=self.user_id,
                deck_id=deck_id,
                name=self.deck_name,
                card_ids=self.card_ids,
                exemplar_ids=self.exemplar_ids,
                faction_id=leader["faction_id"],
                leader_id=self.leader_id,
                expected_version=expected_version,
            )
        except Exception as exc:
            await interaction.edit_original_response(
                content=(f"Não foi possível salvar o deck. A coleção foi revalidada e nada foi salvo. "
                         f"Motivo: `{_safe_error(exc)}`"),
                embed=None,
                view=None,
            )
            return
        await interaction.edit_original_response(
            content=(f"Deck **{saved['name']}** {'atualizado' if self.existing_deck else 'salvo'}. "
                     f"ID `{saved['deck_id']}` · versão {saved['version']} · "
                     "30 exemplares físicos validados. Já pode desafiar outro jogador pela alpha."),
            view=None,
        )
        self.stop()

    async def _cancel(self, interaction: discord.Interaction) -> None:
        self.stop()
        await interaction.response.edit_message(content="Salvamento cancelado. Nenhum deck foi criado.", view=None)


class ChallengeDeckSelect(discord.ui.Select):
    def __init__(self, parent: "ChallengeSetupView") -> None:
        self.parent = parent
        options = [
            discord.SelectOption(
                label=f"{deck['name']} · v{deck['version']}"[:100],
                value=deck["deck_id"],
                description=f"{len(deck['card_ids'])} cartas · líder {deck.get('leader_id') or 'não definido'}"[:100],
            )
            for deck in parent.decks[:25]
        ]
        super().__init__(placeholder="Escolha seu deck", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent.deck_id = self.values[0]
        await interaction.response.edit_message(content=self.parent.summary(), view=self.parent)


class ChallengeSetupView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, user_id: int, decks: list[dict[str, Any]], channel: Any) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.user_id = int(user_id)
        self.decks = decks
        self.channel = channel
        self.deck_id: str | None = None
        self.opponent_id: int | None = None
        self.add_item(ChallengeDeckSelect(self))
        self.user_select = discord.ui.UserSelect(
            placeholder="Escolha o adversário no servidor",
            min_values=1,
            max_values=1,
            row=1,
        )
        self.user_select.callback = self._select_opponent
        self.add_item(self.user_select)
        send = discord.ui.Button(label="Enviar convite", emoji="⚔️", style=discord.ButtonStyle.success, row=2, disabled=True)
        send.callback = self._send_invite
        self.send_button = send
        self.add_item(send)

    def summary(self) -> str:
        self.send_button.disabled = not (self.deck_id and self.opponent_id and self.opponent_id != self.user_id)
        opponent = f"<@{self.opponent_id}>" if self.opponent_id else "não selecionado"
        deck = next((x["name"] for x in self.decks if x["deck_id"] == self.deck_id), "não selecionado")
        return f"**Deck:** {deck}\n**Adversário:** {opponent}\nConvite válido por dez minutos."

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Somente quem abriu o desafio pode configurá-lo.", ephemeral=True)
            return False
        return True

    async def _select_opponent(self, interaction: discord.Interaction) -> None:
        chosen = self.user_select.values[0]
        if bool(getattr(chosen, "bot", False)):
            return await interaction.response.send_message("Bots não podem ser adversários nesta alpha.", ephemeral=True)
        self.opponent_id = int(chosen.id)
        await interaction.response.edit_message(content=self.summary(), view=self)

    async def _send_invite(self, interaction: discord.Interaction) -> None:
        if not self.deck_id or not self.opponent_id or self.opponent_id == self.user_id:
            return await interaction.response.send_message("Escolha um deck e outro jogador.", ephemeral=True)
        if interaction.guild_id is None or self.channel is None or not hasattr(self.channel, "send"):
            return await interaction.response.send_message("Os desafios alpha precisam ser enviados em um canal de servidor.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        invite_id = None
        try:
            invite_id = await self.service.register_invite(
                challenger_id=self.user_id,
                opponent_id=self.opponent_id,
                challenger_deck_id=self.deck_id,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
            )
            view = ChallengeInviteView(self.service, invite_id)
            embed = discord.Embed(
                title="⚔️ Desafio · Card Engine v2 alpha",
                description=(f"<@{self.user_id}> desafiou <@{self.opponent_id}>.\n"
                             "O adversário precisa aceitar e selecionar um deck próprio de 30 cartas.\n"
                             "O convite expira em dez minutos."),
                color=COLOUR,
            )
            message = await self.channel.send(
                content=f"<@{self.opponent_id}>",
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
            await self.service.set_invite_message(invite_id, message)
        except Exception as exc:
            if invite_id is not None:
                await self.service.cancel_invite(invite_id)
            await interaction.followup.send(
                f"Não foi possível publicar o desafio: `{_safe_error(exc)}`", ephemeral=True
            )
            return
        await interaction.followup.send("Convite publicado neste canal.", ephemeral=True)
        self.stop()


class ChallengeInviteView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, invite_id: str) -> None:
        super().__init__(timeout=600)
        self.service = service
        self.invite_id = invite_id

    @discord.ui.button(label="Aceitar e escolher deck", emoji="✅", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        try:
            invite = await self.service.get_invite(self.invite_id, opponent_id=interaction.user.id)
        except InvalidOperation as exc:
            return await interaction.response.send_message(f"Convite indisponível: `{_safe_error(exc)}`", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            decks = await self.service.gateway.list_decks(interaction.user.id)
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível consultar seus decks: `{_safe_error(exc)}`", ephemeral=True
            )
        if not decks:
            return await interaction.followup.send("Você precisa salvar seu próprio deck de 30 cartas antes de aceitar.", ephemeral=True)
        await interaction.followup.send(
            "Escolha qual dos seus decks será usado nesta partida. A posse dos exemplares será revalidada.",
            view=OpponentDeckChoiceView(self.service, self.invite_id, interaction.user.id, decks),
            ephemeral=True,
        )

    @discord.ui.button(label="Recusar", emoji="✖️", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        try:
            invite = await self.service.get_invite(self.invite_id, opponent_id=interaction.user.id)
            invite = await self.service.complete_invite(self.invite_id, "declined")
        except InvalidOperation as exc:
            return await interaction.response.send_message(f"Convite indisponível: `{_safe_error(exc)}`", ephemeral=True)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Desafio recusado.", embed=None, view=self)


class OpponentDeckSelect(discord.ui.Select):
    def __init__(self, parent: "OpponentDeckChoiceView") -> None:
        self.parent = parent
        options = [
            discord.SelectOption(
                label=f"{deck['name']} · v{deck['version']}"[:100],
                value=deck["deck_id"],
                description=f"30 cartas · líder {deck.get('leader_id') or 'não definido'}"[:100],
            )
            for deck in parent.decks[:25]
        ]
        super().__init__(placeholder="Selecione seu deck", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent.create_match(interaction, self.values[0])


class OpponentDeckChoiceView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, invite_id: str, opponent_id: int, decks: list[dict[str, Any]]) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.invite_id = invite_id
        self.opponent_id = int(opponent_id)
        self.decks = decks
        self.add_item(OpponentDeckSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("Esta escolha pertence ao jogador convidado.", ephemeral=True)
            return False
        return True

    async def create_match(self, interaction: discord.Interaction, opponent_deck_id: str) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        invite = None
        claimed = False
        try:
            invite = await self.service.claim_invite(self.invite_id, opponent_id=self.opponent_id)
            claimed = True
            result = await self.service.gateway.create_match_from_decks(
                authenticated_challenger_id=invite["challenger_id"],
                authenticated_opponent_id=self.opponent_id,
                challenger_deck_id=invite["challenger_deck_id"],
                opponent_deck_id=opponent_deck_id,
            )
            await self.service.complete_invite(self.invite_id, "accepted")
        except Exception as exc:
            if claimed:
                await self.service.release_invite(self.invite_id)
            await interaction.followup.send(
                f"Não foi possível iniciar a partida. Os decks e a posse dos exemplares são revalidados antes do início. Motivo: `{_safe_error(exc)}`",
                ephemeral=True,
            )
            return
        invite_message = invite.get("message")
        if invite_message is not None:
            try:
                await invite_message.edit(
                    content=f"Desafio aceito por <@{self.opponent_id}>. Partida **#{result['match_id']}** criada.",
                    embed=None,
                    view=OpenMatchView(self.service, result["match_id"], [invite["challenger_id"], self.opponent_id]),
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except discord.HTTPException:
                pass
        embed, view, _state = await self.service.render_match(
            result["match_id"], self.opponent_id, interaction.guild
        )
        message = await interaction.followup.send(embed=embed, view=view, ephemeral=True, wait=True)
        await view.bind_message(message)
        self.stop()


class OpenMatchView(discord.ui.View):
    def __init__(self, service: CardEngineV2DiscordService, match_id: int, participants: list[int]) -> None:
        super().__init__(timeout=24 * 60 * 60)
        self.service = service
        self.match_id = int(match_id)
        self.participants = {int(item) for item in participants}

    @discord.ui.button(label="Abrir minha partida", emoji="⚔️", style=discord.ButtonStyle.primary)
    async def open_match(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id not in self.participants:
            return await interaction.response.send_message("Esta partida pertence aos dois jogadores do desafio.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            embed, view, _state = await self.service.render_match(
                self.match_id, interaction.user.id, interaction.guild
            )
        except Exception as exc:
            return await interaction.followup.send(f"Não foi possível abrir a partida: `{_safe_error(exc)}`", ephemeral=True)
        message = await interaction.followup.send(embed=embed, view=view, ephemeral=True, wait=True)
        await view.bind_message(message)


class HandCardSelect(discord.ui.Select):
    def __init__(self, parent: "MatchPlayView") -> None:
        self.parent = parent
        start = parent.hand_page * 25
        items = parent.own_player.get("hand", [])[start:start + 25]
        options = []
        for item in items:
            cost = item.get("energy_cost")
            label = f"{item['name']} · {cost if cost is not None else '?'} energia"
            detail = f"Exemplar #{item.get('exemplar_id')}" if item.get("exemplar_id") else item["card_id"]
            options.append(discord.SelectOption(label=label[:100], value=item["instance_id"], description=detail[:100]))
        if not options:
            options = [discord.SelectOption(label="Nenhuma carta na mão", value="none", description="Aguardando compra ou fim de partida")]
        super().__init__(
            placeholder=f"Jogar carta da mão · página {parent.hand_page + 1}",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
            disabled=not parent.is_own_turn or not parent.own_player.get("hand") or parent.finished,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.values[0] == "none":
            return await interaction.response.send_message("Não há cartas selecionáveis nesta página.", ephemeral=True)
        await self.parent.play_selected_card(interaction, self.values[0])


class MatchHistoryView(discord.ui.View):
    """Paginated, participant-only event timeline with sanitized repository data."""

    def __init__(self, *, service: CardEngineV2DiscordService, player_id: int, match_id: int, first_page: dict[str, Any]) -> None:
        super().__init__(timeout=300)
        self.service = service
        self.player_id = int(player_id)
        self.match_id = int(match_id)
        self.pages = [first_page]
        self.index = 0
        self._rebuild()

    def _rebuild(self) -> None:
        self.clear_items()
        page = self.pages[self.index]
        previous = discord.ui.Button(label="Eventos anteriores", emoji="◀️", style=discord.ButtonStyle.secondary, row=0, disabled=self.index == 0)
        following = discord.ui.Button(label="Próximos eventos", emoji="▶️", style=discord.ButtonStyle.secondary, row=0, disabled=not page.get("has_more"))
        previous.callback = self._previous
        following.callback = self._next
        self.add_item(previous)
        self.add_item(following)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Este histórico pertence a outro jogador.", ephemeral=True)
            return False
        return True

    def make_embed(self) -> discord.Embed:
        page = self.pages[self.index]
        labels = {
            "player_passed": "Passou o turno",
            "turn_action_completed": "Ação concluída",
            "player_damaged": "Jogador sofreu dano",
            "row_combat_resolved": "Combate de fileira",
            "unit_entered_board": "Unidade entrou no campo",
            "unit_removed": "Unidade removida",
            "unit_removal_blocked": "Remoção bloqueada",
            "leader_activated": "Líder ativado",
            "energy_gained": "Energia recebida",
            "energy_spent": "Energia consumida",
        }
        lines = []
        for event in page.get("events", []):
            actor = {"you": "Você", "opponent": "Adversário"}.get(event.get("subject"), "Sistema")
            kind = labels.get(event.get("kind"), str(event.get("kind", "Evento")).replace("_", " ").capitalize())
            payload = event.get("payload") or {}
            details = []
            for key, label in (("row", "fileira"), ("damage", "dano"), ("energy_spent", "energia"), ("amount", "quantidade"), ("reason", "motivo")):
                if key in payload and payload[key] is not None:
                    details.append(f"{label}: {payload[key]}")
            if event.get("target_count"):
                details.append(f"alvos: {event['target_count']}")
            suffix = f" — {' · '.join(details)}" if details else ""
            lines.append(f"`#{event['sequence']}` **{actor}:** {kind}{suffix}")
        body = "\n".join(lines) if lines else "Nenhum evento registrado nesta página."
        embed = discord.Embed(
            title=f"📜 Histórico · partida #{self.match_id}",
            description=body[:4000],
            color=COLOUR,
        )
        embed.set_footer(text=f"Página {self.index + 1} · eventos sanitizados · IDs privados omitidos")
        return embed

    async def _load(self, interaction: discord.Interaction, direction: int) -> None:
        await interaction.response.defer()
        if direction < 0 and self.index > 0:
            self.index -= 1
        elif direction > 0:
            current = self.pages[self.index]
            if current.get("has_more"):
                data = await self.service.gateway.match_history(
                    match_id=self.match_id, authenticated_player_id=self.player_id,
                    after_sequence=int(current.get("next_cursor", 0)), limit=20,
                )
                self.pages.append(data)
                self.index += 1
        self._rebuild()
        await interaction.edit_original_response(embed=self.make_embed(), view=self)

    async def _previous(self, interaction: discord.Interaction) -> None:
        await self._load(interaction, -1)

    async def _next(self, interaction: discord.Interaction) -> None:
        await self._load(interaction, 1)


class MatchPlayView(discord.ui.View):
    def __init__(
        self,
        *,
        service: CardEngineV2DiscordService,
        player_id: int,
        match_id: int,
        state: dict[str, Any],
        is_own_turn: bool,
        hand_page: int = 0,
        guild: discord.Guild | None = None,
    ) -> None:
        super().__init__(timeout=900)
        self.service = service
        self.player_id = int(player_id)
        self.match_id = int(match_id)
        self.state = state
        self.is_own_turn = bool(is_own_turn)
        self.hand_page = max(0, int(hand_page))
        self.own_player = state["players"][str(player_id)]
        self.finished = state.get("status") == "finished"
        self.guild = guild
        self._bound_message: discord.Message | None = None
        self._refresh_task: asyncio.Task | None = None
        self._refresh_lock = asyncio.Lock()
        self._replaced = False
        self.add_item(HandCardSelect(self))
        hand_count = int(self.own_player.get("hand_count", 0))
        previous = discord.ui.Button(label="Mão anterior", emoji="◀️", style=discord.ButtonStyle.secondary, row=1, disabled=self.hand_page <= 0)
        next_button = discord.ui.Button(label="Próxima página da mão", emoji="▶️", style=discord.ButtonStyle.secondary, row=1, disabled=(self.hand_page + 1) * 25 >= hand_count)
        previous.callback = self._previous_hand
        next_button.callback = self._next_hand
        self.add_item(previous)
        self.add_item(next_button)
        pass_button = discord.ui.Button(label="Passar turno", emoji="⏭️", style=discord.ButtonStyle.secondary, row=2, disabled=not self.is_own_turn or self.finished)
        leader_button = discord.ui.Button(label="Ativar líder", emoji="👑", style=discord.ButtonStyle.primary, row=2, disabled=not self.is_own_turn or self.finished or self.own_player.get("leader_used") or not self.own_player.get("leader_id"))
        sacrifice_button = discord.ui.Button(label="Sacrificar unidade", emoji="🔥", style=discord.ButtonStyle.danger, row=2, disabled=not self.is_own_turn or self.finished or not self.own_player.get("board"))
        refresh_button = discord.ui.Button(label="Atualizar", emoji="🔄", style=discord.ButtonStyle.secondary, row=2)
        pass_button.callback = self._pass_turn
        leader_button.callback = self._activate_leader
        sacrifice_button.callback = self._sacrifice
        refresh_button.callback = self._refresh
        self.add_item(pass_button)
        self.add_item(leader_button)
        self.add_item(sacrifice_button)
        self.add_item(refresh_button)
        history_button = discord.ui.Button(label="Histórico", emoji="📜", style=discord.ButtonStyle.secondary, row=3)
        history_button.callback = self._show_history
        self.add_item(history_button)

    async def bind_message(self, message: discord.Message) -> None:
        """Attach this private match view to its message and enable server refresh."""
        self._bound_message = message
        if not self.finished and not self.is_finished() and self._refresh_task is None:
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    async def _auto_refresh_loop(self) -> None:
        failures = 0
        try:
            while not self.finished and not self._replaced and self._bound_message is not None:
                await asyncio.sleep(12)
                if self._replaced or self._bound_message is None:
                    return
                async with self._refresh_lock:
                    try:
                        latest = await self.service.gateway.player_view(
                            match_id=self.match_id, authenticated_player_id=self.player_id
                        )
                        failures = 0
                    except Exception:
                        failures += 1
                        if failures >= 5:
                            return
                        continue
                    if int(latest.get("state_revision", 0)) == int(self.state.get("state_revision", 0)):
                        if latest.get("status") == "finished":
                            return
                        continue
                    embed, replacement, state = await self.service.render_match(
                        self.match_id, self.player_id, self.guild
                    )
                    self._replaced = True
                    self.stop()
                    await self._bound_message.edit(embed=embed, view=replacement)
                    await replacement.bind_message(self._bound_message)
                    self.state = state
                    return
        except asyncio.CancelledError:
            raise
        except Exception:
            # An expired ephemeral token or deleted message ends polling quietly.
            return
        finally:
            self._refresh_task = None

    def _stop_refresh(self) -> None:
        self._replaced = True
        task = self._refresh_task
        if task is not None and task is not asyncio.current_task():
            task.cancel()
        self._refresh_task = None

    async def on_timeout(self) -> None:
        self._stop_refresh()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Este painel de partida pertence a outro jogador. Abra a partida pelo convite do Discord.", ephemeral=True)
            return False
        return True

    async def _replace(self, interaction: discord.Interaction, note: str = "", *, response_deferred: bool = False) -> None:
        async with self._refresh_lock:
            self._stop_refresh()
            embed, view, _state = await self.service.render_match(self.match_id, self.player_id, interaction.guild)
            if note:
                embed.description = (embed.description or "") + f"\n\n{note}"
            if response_deferred:
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                await interaction.response.edit_message(embed=embed, view=view)
            try:
                message = await interaction.original_response()
                await view.bind_message(message)
            except Exception:
                pass

    async def _operation(self, interaction: discord.Interaction, action: str, **payload: Any) -> None:
        await interaction.response.defer()
        try:
            receipt = await self.service.gateway.execute_action(
                match_id=self.match_id,
                authenticated_player_id=self.player_id,
                action=action,
                **payload,
            )
            result = getattr(receipt, "result", receipt)
            outcome = str(result.get("outcome", "unknown")) if isinstance(result, dict) else "unknown"
            reason = result.get("reason_code") if isinstance(result, dict) else None
            note = "Ação concluída." if outcome in {"applied", "partial", "consumed_no_effect"} else f"Ação não aplicada: `{reason or outcome}`. Atualizei o estado da partida."
        except Exception as exc:
            note = f"Ação não concluída: `{_safe_error(exc)}`. Atualizei o estado da partida."
        await self._replace(interaction, note, response_deferred=True)

    async def _refresh(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await self._replace(interaction, response_deferred=True)

    async def _show_history(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            data = await self.service.gateway.match_history(
                match_id=self.match_id, authenticated_player_id=self.player_id, limit=20
            )
        except Exception as exc:
            return await interaction.followup.send(
                f"Não foi possível carregar o histórico: `{_safe_error(exc)}`", ephemeral=True
            )
        view = MatchHistoryView(
            service=self.service, player_id=self.player_id, match_id=self.match_id, first_page=data
        )
        await interaction.followup.send(embed=view.make_embed(), view=view, ephemeral=True)

    async def _pass_turn(self, interaction: discord.Interaction) -> None:
        await self._operation(
            interaction,
            "pass_turn",
            expected_revision=int(self.state["state_revision"]),
        )

    async def _activate_leader(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            content="Escolha uma fileira para a habilidade do líder. Para líderes que não usam fileira, a escolha não altera o efeito.",
            embed=None,
            view=RowChoiceView(
                service=self.service,
                player_id=self.player_id,
                match_id=self.match_id,
                state_revision=int(self.state["state_revision"]),
                action_kind="leader",
                guild=interaction.guild,
            ),
        )

    async def _sacrifice(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            offer = await self.service.gateway.sacrifice_offer(
                match_id=self.match_id,
                authenticated_player_id=self.player_id,
            )
        except Exception as exc:
            return await interaction.followup.send(f"Não foi possível obter alvos válidos: `{_safe_error(exc)}`", ephemeral=True)
        candidates = offer.get("candidates", [])
        if not candidates:
            return await interaction.followup.send("Não há unidades aliadas elegíveis para sacrifício.", ephemeral=True)
        await interaction.followup.send(
            "Selecione a unidade que será sacrificada. A oferta está vinculada à revisão atual da partida.",
            view=CandidateActionView(
                service=self.service,
                player_id=self.player_id,
                match_id=self.match_id,
                state_revision=int(offer["state_revision"]),
                candidates=candidates,
                action_kind="sacrifice",
                guild=interaction.guild,
            ),
            ephemeral=True,
        )

    async def _previous_hand(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        embed, view, _state = await self.service.render_match(
            self.match_id, self.player_id, interaction.guild,
            hand_page=max(0, self.hand_page - 1),
        )
        await interaction.edit_original_response(embed=embed, view=view)
        try:
            await view.bind_message(await interaction.original_response())
        except Exception:
            pass

    async def _next_hand(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        embed, view, _state = await self.service.render_match(
            self.match_id, self.player_id, interaction.guild,
            hand_page=self.hand_page + 1,
        )
        await interaction.edit_original_response(embed=embed, view=view)
        try:
            await view.bind_message(await interaction.original_response())
        except Exception:
            pass

    async def play_selected_card(self, interaction: discord.Interaction, instance_id: str) -> None:
        item = next((card for card in self.own_player.get("hand", []) if card["instance_id"] == instance_id), None)
        if item is None:
            return await interaction.response.send_message("A carta não está mais na sua mão. Atualize a partida.", ephemeral=True)
        definition = self.service.catalog.definition_for(str(item["card_id"]))
        if definition.get("kind") == "unit":
            return await self._operation(
                interaction,
                "play_unit",
                instance_id=instance_id,
                expected_revision=int(self.state["state_revision"]),
            )
        if definition.get("kind") != "special":
            return await interaction.response.send_message("Tipo de carta não suportado nesta alpha.", ephemeral=True)
        effect_id = definition.get("effect_id")
        if effect_id in {"gwent_clima", "gwent_geada_cariana", "gwent_execucao"}:
            return await interaction.response.edit_message(
                content=f"Escolha a fileira para **{item['name']}**.",
                embed=None,
                view=RowChoiceView(
                    service=self.service,
                    player_id=self.player_id,
                    match_id=self.match_id,
                    state_revision=int(self.state["state_revision"]),
                    action_kind="special",
                    source_instance_id=instance_id,
                    effect_id=str(effect_id),
                    guild=interaction.guild,
                ),
            )
        if effect_id == "gwent_egide":
            return await self._open_special_targets(interaction, instance_id, selected_row=None)
        return await interaction.response.send_message("Este efeito especial ainda não está disponível na interface Discord alpha.", ephemeral=True)

    async def _open_special_targets(self, interaction: discord.Interaction, source_instance_id: str, selected_row: str | None) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            offer = await self.service.gateway.target_offer(
                match_id=self.match_id,
                authenticated_player_id=self.player_id,
                source_instance_id=source_instance_id,
                selected_row=selected_row,
            )
        except Exception as exc:
            return await interaction.followup.send(f"Não foi possível calcular os alvos: `{_safe_error(exc)}`", ephemeral=True)
        candidates = offer.get("candidates", [])
        if not candidates:
            return await interaction.followup.send("Não existem alvos elegíveis para este efeito.", ephemeral=True)
        await interaction.followup.send(
            "Selecione um alvo oferecido pelo servidor. A seleção será validada pela revisão da partida.",
            view=CandidateActionView(
                service=self.service,
                player_id=self.player_id,
                match_id=self.match_id,
                state_revision=int(offer["state_revision"]),
                candidates=candidates,
                action_kind="special",
                source_instance_id=source_instance_id,
                selected_row=selected_row,
                guild=interaction.guild,
            ),
            ephemeral=True,
        )


class RowChoiceView(discord.ui.View):
    def __init__(
        self,
        *,
        service: CardEngineV2DiscordService,
        player_id: int,
        match_id: int,
        state_revision: int,
        action_kind: str,
        guild: discord.Guild | None,
        source_instance_id: str | None = None,
        effect_id: str | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.service = service
        self.player_id = int(player_id)
        self.match_id = int(match_id)
        self.state_revision = int(state_revision)
        self.action_kind = action_kind
        self.guild = guild
        self.source_instance_id = source_instance_id
        self.effect_id = effect_id
        for row_id, label in ROW_LABELS.items():
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            button.callback = self._make_callback(row_id)
            self.add_item(button)

    def _make_callback(self, row_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.player_id:
                return await interaction.response.send_message("Esta seleção pertence a outro jogador.", ephemeral=True)
            if self.action_kind == "leader":
                await interaction.response.defer()
                try:
                    receipt = await self.service.gateway.execute_action(
                        match_id=self.match_id,
                        authenticated_player_id=self.player_id,
                        action="activate_leader",
                        selected_row=row_id,
                        expected_revision=self.state_revision,
                    )
                    result = getattr(receipt, "result", receipt)
                    note = "Líder ativado." if result.get("outcome") == "applied" else f"Ativação não aplicada: `{result.get('reason_code') or result.get('outcome')}`."
                except Exception as exc:
                    note = f"Ativação não concluída: `{_safe_error(exc)}`."
                embed, view, _state = await self.service.render_match(self.match_id, self.player_id, self.guild)
                embed.description = (embed.description or "") + f"\n\n{note}"
                await interaction.edit_original_response(embed=embed, view=view, content=None)
                try:
                    await view.bind_message(await interaction.original_response())
                except Exception:
                    pass
                self.stop()
                return
            if self.action_kind == "special" and self.effect_id in {"gwent_clima", "gwent_geada_cariana"}:
                await interaction.response.defer()
                try:
                    receipt = await self.service.gateway.execute_action(
                        match_id=self.match_id,
                        authenticated_player_id=self.player_id,
                        action="play_special",
                        source_instance_id=self.source_instance_id,
                        selected_row=row_id,
                        expected_revision=self.state_revision,
                    )
                    result = getattr(receipt, "result", receipt)
                    note = "Especial resolvida." if result.get("outcome") in {"applied", "partial", "consumed_no_effect"} else f"Especial não aplicada: `{result.get('reason_code') or result.get('outcome')}`."
                except Exception as exc:
                    note = f"Especial não resolvida: `{_safe_error(exc)}`."
                embed, view, _state = await self.service.render_match(self.match_id, self.player_id, self.guild)
                embed.description = (embed.description or "") + f"\n\n{note}"
                await interaction.edit_original_response(embed=embed, view=view, content=None)
                self.stop()
                return
            if self.action_kind == "special" and self.effect_id == "gwent_execucao":
                await interaction.response.defer()
                try:
                    offer = await self.service.gateway.target_offer(
                        match_id=self.match_id,
                        authenticated_player_id=self.player_id,
                        source_instance_id=str(self.source_instance_id),
                        selected_row=row_id,
                    )
                except Exception as exc:
                    await interaction.edit_original_response(
                        content=f"Não foi possível calcular os alvos: `{_safe_error(exc)}`",
                        embed=None,
                        view=None,
                    )
                    return
                candidates = offer.get("candidates", [])
                if not candidates:
                    await interaction.edit_original_response(
                        content="Não existem alvos elegíveis nesta fileira.", embed=None, view=None
                    )
                    return
                await interaction.edit_original_response(
                    content="Escolha o alvo da Execução.",
                    embed=None,
                    view=CandidateActionView(
                        service=self.service,
                        player_id=self.player_id,
                        match_id=self.match_id,
                        state_revision=int(offer["state_revision"]),
                        candidates=candidates,
                        action_kind="special",
                        source_instance_id=self.source_instance_id,
                        selected_row=row_id,
                        guild=self.guild,
                    ),
                )
                self.stop()
                return
            await interaction.response.send_message("Seleção de fileira inválida.", ephemeral=True)
        return callback


class CandidateSelect(discord.ui.Select):
    def __init__(self, parent: "CandidateActionView") -> None:
        self.parent = parent
        start = parent.page * parent.PAGE_SIZE
        candidates = parent.candidates[start:start + parent.PAGE_SIZE]
        options = []
        for candidate in candidates:
            label = str(candidate.get("display_name") or candidate.get("target_instance_id"))
            metric = candidate.get("display_metric_value")
            target_suffix = str(candidate["target_instance_id"])[-6:]
            detail = f"Poder: {metric} · alvo {target_suffix}" if metric is not None else f"Alvo {target_suffix}"
            options.append(discord.SelectOption(label=label[:100], value=str(candidate["target_instance_id"]), description=detail[:100]))
        super().__init__(placeholder="Selecione um alvo válido", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent.apply(interaction, self.values[0])


class CandidateActionView(discord.ui.View):
    def __init__(
        self,
        *,
        service: CardEngineV2DiscordService,
        player_id: int,
        match_id: int,
        state_revision: int,
        candidates: list[dict[str, Any]],
        action_kind: str,
        guild: discord.Guild | None,
        source_instance_id: str | None = None,
        selected_row: str | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.service = service
        self.player_id = int(player_id)
        self.match_id = int(match_id)
        self.state_revision = int(state_revision)
        self.candidates = list(candidates)
        self.action_kind = action_kind
        self.source_instance_id = source_instance_id
        self.selected_row = selected_row
        self.guild = guild
        self.page = 0
        self._rebuild()

    PAGE_SIZE = 25

    def _rebuild(self) -> None:
        self.clear_items()
        self.add_item(CandidateSelect(self))
        total_pages = max(1, (len(self.candidates) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if total_pages > 1:
            previous = discord.ui.Button(
                label="Alvos anteriores", emoji="◀️", style=discord.ButtonStyle.secondary,
                row=1, disabled=self.page <= 0,
            )
            following = discord.ui.Button(
                label="Próximos alvos", emoji="▶️", style=discord.ButtonStyle.secondary,
                row=1, disabled=self.page >= total_pages - 1,
            )
            previous.callback = self._previous
            following.callback = self._next
            self.add_item(previous)
            self.add_item(following)

    async def _change_page(self, interaction: discord.Interaction, delta: int) -> None:
        total_pages = max(1, (len(self.candidates) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page = max(0, min(total_pages - 1, self.page + delta))
        self._rebuild()
        await interaction.response.edit_message(
            content=f"Selecione um alvo · página {self.page + 1}/{total_pages}.",
            view=self,
        )

    async def _previous(self, interaction: discord.Interaction) -> None:
        await self._change_page(interaction, -1)

    async def _next(self, interaction: discord.Interaction) -> None:
        await self._change_page(interaction, 1)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Esta seleção pertence a outro jogador.", ephemeral=True)
            return False
        return True

    async def apply(self, interaction: discord.Interaction, target_id: str) -> None:
        await interaction.response.defer()
        try:
            if self.action_kind == "sacrifice":
                action = "sacrifice_unit"
                payload = {
                    "target_instance_id": target_id,
                    "expected_revision": self.state_revision,
                }
            else:
                action = "play_special"
                payload = {
                    "source_instance_id": self.source_instance_id,
                    "selected_row": self.selected_row,
                    "selection": {"mode": "manual_single", "target_instance_id": target_id},
                    "expected_revision": self.state_revision,
                }
            receipt = await self.service.gateway.execute_action(
                match_id=self.match_id,
                authenticated_player_id=self.player_id,
                action=action,
                **payload,
            )
            result = getattr(receipt, "result", receipt)
            note = "Ação concluída." if result.get("outcome") in {"applied", "partial", "consumed_no_effect"} else f"Ação não aplicada: `{result.get('reason_code') or result.get('outcome')}`."
        except Exception as exc:
            note = f"Ação não concluída: `{_safe_error(exc)}`."
        embed, view, _state = await self.service.render_match(self.match_id, self.player_id, self.guild)
        embed.description = (embed.description or "") + f"\n\n{note}"
        await interaction.edit_original_response(embed=embed, view=view, content=None)
        try:
            await view.bind_message(await interaction.original_response())
        except Exception:
            pass
        self.stop()


def _safe_error(exc: BaseException) -> str:
    """Return a user-safe message; never expose SQL paths or internal values."""
    if isinstance(exc, InvalidOperation):
        return "a regra atual da partida não permite esta operação"
    if isinstance(exc, MatchNotFound):
        return "partida não encontrada ou indisponível para sua conta"
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return "a operação excedeu o tempo limite; atualize e tente novamente"
    return "erro interno ao processar a solicitação; tente novamente"


__all__ = [
    "AlphaHomeView",
    "CardEngineV2DiscordService",
    "get_card_engine_service",
    "MyMatchesView",
]
