"""Painel de entrada do Coliseu no Discord.

O Discord apresenta um resumo leve e encaminha as operações do jogo para o site.
Não replica coleção, drops, forja, rituais web ou estatísticas que já existem no portal.
Mantém somente a Convergência, uma operação exclusiva da interface Discord.
"""
from __future__ import annotations

import os
from collections import Counter

import discord
from discord import app_commands
from discord.ext import commands


COR_COLISEU = 0x8E6A3A
COR_ALERTA = 0xA33B32


def _nome_carta(card_id: str) -> str:
    from sistemas.cartas import CARTAS_POR_ID
    carta = CARTAS_POR_ID.get(str(card_id))
    return carta.nome if carta else str(card_id).replace("_", " ").strip().title()


class ConfirmarConvergenciaView(discord.ui.View):
    """Confirmação explícita para o consumo irreversível de três exemplares."""

    def __init__(self, bot, user_id: int, exemplar_ids: list[int], resumo: str):
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = int(user_id)
        self.exemplar_ids = list(exemplar_ids)
        self.resumo = resumo

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Este ritual pertence a outro jogador.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Confirmar sacrifício", emoji="🔥",
        style=discord.ButtonStyle.danger, row=0,
    )
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        resultado = await self.bot.db.coliseu_convergir_exemplares(
            self.user_id, self.exemplar_ids
        )
        status = resultado.get("status")
        if status == "ok":
            embed = discord.Embed(
                title="Convergência concluída",
                description=(
                    f"{self.resumo}\n\n"
                    f"**Novo exemplar:** #{resultado['exemplar_id']}\n"
                    f"**Raridade:** {resultado['rarity']} · **Poder:** {resultado['power']}\n\n"
                    "Os três sacrifícios foram registrados. O poder anterior não foi transferido."
                ),
                color=COR_COLISEU,
            )
            return await interaction.response.edit_message(embed=embed, content=None, view=None)

        mensagens = {
            "exemplar_equipado": "Um dos exemplares está equipado no deck. Retire-o antes do ritual.",
            "carta_pessoal_protegida": "Cartas pessoais ou protegidas não podem ser sacrificadas.",
            "ritual_especial_necessario": "Esta evolução exige um Ritual Ancestral.",
            "receita_incompativel": "Use três exemplares do mesmo modelo e raridade.",
            "exemplar_nao_encontrado": "Um dos exemplares não está mais disponível.",
            "carta_especial_nao_funde": "Cartas especiais não podem passar por convergência.",
            "deck_indisponivel": "Não foi possível validar o deck. Nenhum exemplar foi consumido.",
        }
        await interaction.response.edit_message(
            content="⛔ " + mensagens.get(status, "Ritual não concluído."),
            embed=None,
            view=None,
        )

    @discord.ui.button(
        label="Cancelar", emoji="↩️", style=discord.ButtonStyle.secondary, row=0,
    )
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Ritual cancelado. Nenhum exemplar foi consumido.",
            embed=None,
            view=None,
        )


class SelecaoConvergencia(discord.ui.Select):
    def __init__(self, bot, user_id: int, rows: list[dict]):
        self.bot = bot
        self.user_id = int(user_id)
        self.rows_by_id = {int(row["id"]): dict(row) for row in rows}
        options = [
            discord.SelectOption(
                label=f"{_nome_carta(row['card_id'])} · {row['rarity']}"[:100],
                value=str(row["id"]),
                description=f"Exemplar #{row['id']} · Poder {row['power']}"[:100],
            )
            for row in rows[:25]
        ]
        super().__init__(
            placeholder="Selecione 3 exemplares do mesmo modelo e raridade",
            min_values=3,
            max_values=3,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        escolhidos = [self.rows_by_id[int(value)] for value in self.values]
        if (
            len({str(row["card_id"]) for row in escolhidos}) != 1
            or len({str(row["rarity"]) for row in escolhidos}) != 1
        ):
            return await interaction.response.send_message(
                "Selecione três exemplares do mesmo modelo e raridade.",
                ephemeral=True,
            )

        from sistemas.cartas import RARIDADES
        raridade = str(escolhidos[0]["rarity"])
        if raridade not in RARIDADES or RARIDADES.index(raridade) + 1 >= len(RARIDADES):
            return await interaction.response.send_message(
                "Esta raridade exige um Ritual Ancestral.", ephemeral=True
            )
        proxima = RARIDADES[RARIDADES.index(raridade) + 1]
        if proxima in ("Primordial", "Singular"):
            return await interaction.response.send_message(
                "A próxima raridade exige um Ritual Ancestral.", ephemeral=True
            )

        nome = _nome_carta(escolhidos[0]["card_id"])
        resumo = (
            f"**{nome}** · {raridade} → {proxima}\n"
            "Sacrificar: "
            + ", ".join(
                f"#{row['id']} (Poder {row['power']})" for row in escolhidos
            )
        )
        embed = discord.Embed(
            title="Prévia · Ritual de Convergência",
            description=(
                f"{resumo}\n\n"
                "**Resultado:** 1 exemplar na raridade seguinte, com poder inicial mínimo.\n"
                "**Custo:** 3 exemplares. Operação irreversível.\n"
                "O poder e a lapidação dos exemplares sacrificados não são transferidos."
            ),
            color=COR_ALERTA,
        )
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmarConvergenciaView(
                self.bot, self.user_id, [int(value) for value in self.values], resumo
            ),
            ephemeral=True,
        )


class ConvergenciaView(discord.ui.View):
    def __init__(self, bot, user_id: int, rows: list[dict]):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = int(user_id)
        self.page = 0
        self.page_size = 25
        self.selector = None

        # Mantém cada grupo (mesma carta + mesma raridade) inteiro na página.
        grouped: dict[tuple[str, str], list[dict]] = {}
        for raw_row in rows:
            row = dict(raw_row)
            grouped.setdefault((str(row["card_id"]), str(row["rarity"])), []).append(row)
        groups = []
        for key in sorted(grouped):
            # Prioriza as cópias de menor poder como candidatas a sacrifício,
            # sem esconder exemplares quando o jogador possui mais de 25 iguais.
            group = sorted(
                grouped[key],
                key=lambda item: (int(item.get("power") or 0), int(item["id"])),
            )
            if len(group) < 3:
                continue
            if len(group) <= self.page_size:
                groups.append(group)
                continue
            # Select do Discord aceita 25 opções; janelas sobrepostas preservam
            # acesso aos exemplares finais e mantêm pelo menos três por página.
            for start in range(0, len(group), self.page_size - 2):
                chunk = group[start:start + self.page_size]
                if len(chunk) < 3:
                    chunk = group[-self.page_size:]
                groups.append(chunk)

        self.pages: list[list[dict]] = []
        current: list[dict] = []
        for group in groups:
            if current and len(current) + len(group) > self.page_size:
                self.pages.append(current)
                current = []
            current.extend(group)
        if current:
            self.pages.append(current)

        self._rebuild_selector()
        self.anterior.disabled = True
        self.proxima.disabled = len(self.pages) <= 1

    def _rebuild_selector(self):
        if self.selector is not None:
            self.remove_item(self.selector)
        self.selector = SelecaoConvergencia(
            self.bot, self.user_id, self.pages[self.page]
        )
        self.add_item(self.selector)

    async def _change_page(self, interaction: discord.Interaction, delta: int):
        total_pages = max(1, len(self.pages))
        self.page = max(0, min(total_pages - 1, self.page + delta))
        self._rebuild_selector()
        self.anterior.disabled = self.page == 0
        self.proxima.disabled = self.page >= total_pages - 1
        await interaction.response.edit_message(
            content=f"Página **{self.page + 1}/{total_pages}** · grupos de exemplares elegíveis",
            view=self,
        )

    @discord.ui.button(
        label="Anterior", emoji="◀️", style=discord.ButtonStyle.secondary, row=1
    )
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._change_page(interaction, -1)

    @discord.ui.button(
        label="Próxima", emoji="▶️", style=discord.ButtonStyle.secondary, row=1
    )
    async def proxima(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._change_page(interaction, 1)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Esta seleção pertence a outro jogador.", ephemeral=True
            )
            return False
        return True


def _base_url() -> str:
    return str(
        os.getenv("SOULSBOT_PUBLIC_URL", "https://narabot.sbs")
        or "https://narabot.sbs"
    ).strip().rstrip("/")


async def _criar_embed_resumo(bot: commands.Bot, user_id: int) -> discord.Embed:
    """Monta o resumo exibido no /jogo e reutilizado pelo botão de atualização."""
    estado = await bot.db.coliseu_estado_usuario(int(user_id))
    ranking_row = await bot.db._one(
        "SELECT mmr,wins,losses,draws FROM cartas_gwent_rankings WHERE user_id=?",
        (int(user_id),),
    )
    partidas_row = await bot.db._one(
        "SELECT COUNT(*) AS total FROM cartas_gwent_matches WHERE creator_id=? OR opponent_id=?",
        (int(user_id), int(user_id)),
    )

    ranking = dict(ranking_row) if ranking_row else {
        "mmr": 1000, "wins": 0, "losses": 0, "draws": 0,
    }
    partidas = dict(partidas_row) if partidas_row else {"total": 0}

    embed = discord.Embed(
        title="Cartas do Coliseu",
        description=(
            "Seu resumo do Coliseu em um só lugar. "
            "Arena, Deck, Mercado e Ofícios ficam organizados no portal; "
            "aqui você também pode executar a Convergência."
        ),
        color=COR_COLISEU,
    )
    embed.add_field(
        name="COLEÇÃO",
        value=f"**{int(estado['cartas']):,}** cartas",
        inline=True,
    )
    embed.add_field(
        name="RECURSOS",
        value=(
            f"**{int(estado['almas']):,}** Almas\n"
            f"**{int(estado['fragmentos']):,}** Fragmentos"
        ),
        inline=True,
    )
    embed.add_field(
        name="GWENT",
        value=(
            f"**{int(partidas['total'] or 0):,}** partidas\n"
            f"{int(ranking['wins'] or 0)}V · {int(ranking['losses'] or 0)}D · "
            f"{int(ranking['draws'] or 0)}E\n"
            f"**MMR {int(ranking['mmr'] or 1000):,}**"
        ),
        inline=True,
    )
    embed.set_footer(text="Coliseu · Portal do jogador")
    return embed


class PainelJogoView(discord.ui.View):
    """Atalhos essenciais do site e controles contextuais do painel Discord."""

    def __init__(self, bot: commands.Bot, user_id: int, callback_voltar=None):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = int(user_id)
        self.callback_voltar = callback_voltar
        base_url = _base_url()

        # Três destinos principais. As demais operações já estão organizadas no site.
        self.add_item(discord.ui.Button(
            label="Arena Gwent", emoji="⚔️", style=discord.ButtonStyle.link,
            url=f"{base_url}/#arena", row=0,
        ))
        self.add_item(discord.ui.Button(
            label="Deck e coleção", emoji="🃏", style=discord.ButtonStyle.link,
            url=f"{base_url}/#deck", row=0,
        ))
        self.add_item(discord.ui.Button(
            label="Mercado e drops", emoji="🎁", style=discord.ButtonStyle.link,
            url=f"{base_url}/#market", row=0,
        ))
        self.add_item(discord.ui.Button(
            label="Ofícios", emoji="⚒️", style=discord.ButtonStyle.link,
            url=f"{base_url}/#oficios", row=0,
        ))
        self.add_item(discord.ui.Button(
            label="Card Engine v2 · Alpha", emoji="🧪", style=discord.ButtonStyle.link,
            url=f"{base_url}/card-engine-v2", row=0,
        ))

        if callback_voltar is not None:
            voltar = discord.ui.Button(
                label="Voltar à NARA", emoji="↩️",
                style=discord.ButtonStyle.secondary, row=1,
            )
            voltar.callback = self._voltar
            self.add_item(voltar)

    async def _voltar(self, interaction: discord.Interaction):
        if self.callback_voltar is None:
            return await interaction.response.send_message(
                "Abra `/nara` para voltar à central.", ephemeral=True
            )
        await self.callback_voltar(interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Este painel pertence a outro jogador. Use `/jogo` para abrir o seu.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Ritual de Convergência", emoji="♻️",
        style=discord.ButtonStyle.primary, row=1,
    )
    async def convergencia(self, interaction: discord.Interaction, button: discord.ui.Button):
        raw_rows = await self.bot.db.coliseu_listar_exemplares(self.user_id)
        from sistemas.cartas import get_carta

        sacrificaveis = []
        for raw_row in raw_rows:
            row = dict(raw_row)
            modelo = get_carta(str(row["card_id"]))
            if (
                modelo is not None
                and str(modelo.categoria).casefold() != "especial"
                and int(row.get("is_sacrificable", 1) or 0) == 1
                and str(row.get("origin_type") or "").casefold() != "transmutacao"
            ):
                sacrificaveis.append(row)

        grupos = Counter(
            (str(row["card_id"]), str(row["rarity"])) for row in sacrificaveis
        )
        elegiveis = [
            row for row in sacrificaveis
            if grupos[(str(row["card_id"]), str(row["rarity"]))] >= 3
        ]

        if not elegiveis:
            return await interaction.response.send_message(
                "Você ainda não possui três exemplares sacrificáveis do mesmo modelo e raridade.",
                ephemeral=True,
            )

        embed = discord.Embed(
            title="Ritual de Convergência",
            description=(
                "Selecione três exemplares do mesmo modelo e raridade. "
                "A próxima tela mostrará o resultado antes de qualquer consumo.\n\n"
                "**Atenção:** cartas equipadas, pessoais ou protegidas não podem ser sacrificadas."
            ),
            color=COR_COLISEU,
        )
        if len(elegiveis) > 25:
            embed.set_footer(text=f"Mostrando os primeiros 25 de {len(elegiveis)} exemplares elegíveis.")
        view = ConvergenciaView(self.bot, self.user_id, elegiveis)
        await interaction.response.send_message(
            content=f"Página **1/{len(view.pages)}** · grupos de exemplares elegíveis",
            embed=embed,
            view=view,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Atualizar resumo", emoji="🔄",
        style=discord.ButtonStyle.secondary, row=1,
    )
    async def atualizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await _criar_embed_resumo(self.bot, self.user_id)
        await interaction.response.edit_message(embed=embed, view=self)


class PainelJogo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def abrir_painel(self, interaction: discord.Interaction, callback_voltar=None):
        embed = await _criar_embed_resumo(self.bot, interaction.user.id)
        view = PainelJogoView(
            self.bot,
            interaction.user.id,
            callback_voltar=callback_voltar,
        )
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=view, content=None)
        else:
            await interaction.response.edit_message(embed=embed, view=view, content=None)

    @app_commands.command(
        name="jogo",
        description="Abra os atalhos do Coliseu: Arena, Deck e Card Engine v2.",
    )
    @app_commands.guild_only()
    async def jogo(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.abrir_painel(interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(PainelJogo(bot))
