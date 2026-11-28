"""Entrada compacta do Coliseu no Discord, integrada à experiência de jogo no site."""
from __future__ import annotations

import os

import discord
from discord import app_commands
from discord.ext import commands


COR_COLISEU = 0x8E6A3A
class PainelJogoView(discord.ui.View):
    """Entrada enxuta para o Coliseu web, sem duplicar as operações do site."""

    def __init__(self, bot: commands.Bot, user_id: int, callback_voltar=None):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = int(user_id)
        self.callback_voltar = callback_voltar
        base_url = str(os.getenv("SOULSBOT_PUBLIC_URL", "https://narabot.sbs") or "https://narabot.sbs").strip().rstrip("/")
        self.add_item(discord.ui.Button(
            label="Entrar na Arena", emoji="⚔️", style=discord.ButtonStyle.link,
            url=f"{base_url}/#arena", row=0,
        ))
        self.add_item(discord.ui.Button(
            label="Montar deck", emoji="🃏", style=discord.ButtonStyle.link,
            url=f"{base_url}/#deck", row=0,
        ))
        if callback_voltar is not None:
            voltar = discord.ui.Button(label="Voltar à NARA", emoji="↩️", style=discord.ButtonStyle.secondary, row=1)
            voltar.callback = self._voltar
            self.add_item(voltar)

    async def _voltar(self, interaction: discord.Interaction):
        if self.callback_voltar is None:
            return await interaction.response.send_message("Abra `/nara` para voltar à central.", ephemeral=True)
        await self.callback_voltar(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Este painel pertence a outro jogador. Use `/jogo` para abrir o seu.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Atualizar resumo", emoji="🔄", style=discord.ButtonStyle.secondary, row=1)
    async def atualizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        estado = await self.bot.db.coliseu_estado_usuario(self.user_id)
        ranking = await self.bot.db._one(
            "SELECT mmr,wins,losses,draws FROM cartas_gwent_rankings WHERE user_id=?",
            (self.user_id,),
        )
        partidas = await self.bot.db._one(
            "SELECT COUNT(*) AS total FROM cartas_gwent_matches WHERE creator_id=? OR opponent_id=?",
            (self.user_id, self.user_id),
        )
        ranking = dict(ranking) if ranking else {"mmr": 1000, "wins": 0, "losses": 0, "draws": 0}
        embed = discord.Embed(
            title="🏛️ Cartas do Coliseu",
            description=(
                "Use os atalhos para abrir a experiência completa do Coliseu no site.\n\n"
                f"**Coleção:** {estado['cartas']} cartas\n"
                f"**Almas:** {estado['almas']:,} · **Fragmentos:** {estado['fragmentos']:,}\n"
                f"**Partidas:** {int(partidas['total'] or 0)} · {ranking['wins']} vitórias · {ranking['losses']} derrotas · {ranking['draws']} empates\n"
                f"**MMR:** {ranking['mmr']}"
            ),
            color=COR_COLISEU,
        )
        embed.set_footer(text="Cartas do Coliseu · Arena e decks no site")
        await interaction.response.edit_message(embed=embed, view=self)


class PainelJogo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def abrir_painel(self, interaction: discord.Interaction, callback_voltar=None):
        user_id = int(interaction.user.id)
        estado = await self.bot.db.coliseu_estado_usuario(user_id)
        ranking_row = await self.bot.db._one(
            "SELECT mmr,wins,losses,draws FROM cartas_gwent_rankings WHERE user_id=?",
            (user_id,),
        )
        partidas_row = await self.bot.db._one(
            "SELECT COUNT(*) AS total FROM cartas_gwent_matches WHERE creator_id=? OR opponent_id=?",
            (user_id, user_id),
        )
        ranking = dict(ranking_row) if ranking_row else {
            "mmr": 1000, "wins": 0, "losses": 0, "draws": 0,
        }
        total_partidas = int(partidas_row["total"] or 0) if partidas_row else 0
        embed = discord.Embed(
            title="🏛️ Cartas do Coliseu",
            description=(
                "Acesse a experiência completa do Coliseu no site para coleção, mercado, decks, forja e partidas.\n\n"
                f"**Coleção:** {estado['cartas']} cartas\n"
                f"**Almas:** {estado['almas']:,} · **Fragmentos:** {estado['fragmentos']:,}\n"
                f"**Partidas:** {total_partidas} · {int(ranking['wins'])} vitórias · {int(ranking['losses'])} derrotas\n"
                f"**MMR:** {int(ranking['mmr'])}"
            ),
            color=COR_COLISEU,
        )
        embed.set_footer(text="Cartas do Coliseu · Arena e decks no site")
        view = PainelJogoView(self.bot, interaction.user.id, callback_voltar=callback_voltar)
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=view, content=None)
        else:
            await interaction.response.edit_message(embed=embed, view=view, content=None)

    @app_commands.command(name="jogo", description="Acesse a Arena e o construtor de decks do Coliseu no site.")
    @app_commands.guild_only()
    async def jogo(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.abrir_painel(interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(PainelJogo(bot))
