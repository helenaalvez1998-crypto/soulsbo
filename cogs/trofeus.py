"""Caçador de Troféus — painéis do jogador, pesquisa com IA e administração de catálogos.

Regras que este módulo preserva:
* Nenhum catálogo gerado por IA é publicado automaticamente (revisão humana obrigatória).
* Cada jogador tem progresso próprio; painéis só aceitam cliques de quem os abriu.
* Um pedido de pesquisa nunca se perde nem se duplica (ver `cacador_fila`).
* Erros técnicos vão para a fila administrativa; o jogador vê apenas mensagens seguras.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import discord
from discord import app_commands
from discord.ext import commands

import cacador_fila as fila
import catalogo_ia
import config
import trofeus_service as svc
from admin_config import GuildConfig
from utils import get_text_channel
from ia_provedores import diagnostico_configuracao

log = logging.getLogger("nara.trofeus")

VIEW_TIMEOUT = 600
POR_PAGINA = 25          # limite de opções de um Select do Discord
TROFEUS_POR_PAGINA = 10


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def _corta(texto, limite: int) -> str:
    texto = str(texto or "")
    return texto if len(texto) <= limite else texto[: max(0, limite - 1)] + "…"


def _barra(atual: int, total: int, tamanho: int = 12) -> str:
    if total <= 0:
        return "▱" * tamanho
    cheios = round(max(0, min(1, atual / total)) * tamanho)
    return "▰" * cheios + "▱" * (tamanho - cheios)


def _pct(atual: int, total: int) -> int:
    return round(atual / total * 100) if total else 0


def _linha_progresso(rotulo: str, par: tuple[int, int]) -> str:
    feitos, total = par
    if not total:
        return f"{rotulo}: —"
    return f"{rotulo}: **{feitos}/{total}** · `{_barra(feitos, total)}` {_pct(feitos, total)}%"


def _nome(item) -> str:
    return svc.nome_exibicao(item["name_pt"], item["name_original"])


def _md(texto, limite: int | None = None) -> str:
    texto = str(texto or "")
    if limite is not None:
        texto = _corta(texto, limite)
    return discord.utils.escape_markdown(texto)


def _eh_admin(interaction: discord.Interaction) -> bool:
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms and perms.manage_guild)


def _tags_trofeu(t) -> list[str]:
    tags = []
    if t["is_platinum"]:
        tags.append("💎 Platina")
    if t["missable"]:
        tags.append("⚠️ Perdível")
    if t["hidden"]:
        tags.append("👁️ Oculto")
    if t["story_related"]:
        tags.append("📖 História")
    if t["dlc"]:
        tags.append(f"➕ {_corta(t['dlc'], 40)}")
    return tags


@dataclass
class ResultadoPesquisa:
    ok: bool
    mensagem: str
    game: object | None = None   # catálogo já publicado a ser aberto no lugar de pesquisar


# ----------------------------------------------------------------------------
# Base das views: dono, timeout limpo e erros sem "interação falhou"
# ----------------------------------------------------------------------------
class ViewDono(discord.ui.View):
    def __init__(self, user_id: int, *, timeout: float = VIEW_TIMEOUT):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self._interaction: discord.Interaction | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este painel pertence a outro jogador.", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self._interaction is not None:
            try:
                await self._interaction.edit_original_response(view=self)
            except discord.HTTPException:
                pass  # mensagem apagada ou token expirado: nada a fazer

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        log.error("Erro em componente do Caçador (%s)", type(item).__name__, exc_info=error)
        aviso = "Algo deu errado ao processar sua ação. Reabra o painel pelo botão **Caçador de Troféus** em `/nara` e tente novamente."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(aviso, ephemeral=True)
            else:
                await interaction.response.send_message(aviso, ephemeral=True)
        except discord.HTTPException:
            pass


async def mostrar(interaction: discord.Interaction, view: ViewDono, embed: discord.Embed | None = None, *,
                  content: str | None = None, antiga: discord.ui.View | None = None) -> None:
    """Troca a mensagem do componente pela nova view e encerra a anterior (sem timeout fantasma)."""
    await interaction.response.edit_message(content=content, embed=embed, view=view)
    view._interaction = interaction
    if antiga is not None and antiga is not view:
        antiga.stop()


class BotaoPagina(discord.ui.Button):
    def __init__(self, owner_view, delta: int, row: int = 2):
        super().__init__(label="Anterior" if delta < 0 else "Próxima", emoji="◀️" if delta < 0 else "▶️",
                         style=discord.ButtonStyle.secondary, row=row)
        self.owner_view, self.delta = owner_view, delta

    async def callback(self, interaction: discord.Interaction):
        await self.owner_view.mudar_pagina(interaction, self.delta)


class BotaoFechar(discord.ui.Button):
    def __init__(self, row: int = 1):
        super().__init__(label="Fechar", emoji="✖️", style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Painel fechado.", embed=None, view=None)
        if self.view is not None:
            self.view.stop()


# ----------------------------------------------------------------------------
# Painel inicial
# ----------------------------------------------------------------------------
class SeletorJogo(discord.ui.Select):
    def __init__(self, cog, jogos):
        self.cog = cog
        options = [
            discord.SelectOption(label=_corta(g["name"], 100) or "Jogo", value=str(g["id"]))
            for g in jogos[:POR_PAGINA]
        ]
        super().__init__(placeholder="Escolha um jogo...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        owner = self.view
        game = await svc.buscar_jogo(self.cog.bot.db, int(self.values[0]))
        if not game or game["status"] != "ready":
            return await interaction.response.send_message("Esse catálogo não está disponível no momento.", ephemeral=True)
        await svc.registrar_acesso(self.cog.bot.db, owner.user_id, int(game["id"]))
        nova = PainelJogoView(self.cog, owner.user_id, game)
        await mostrar(interaction, nova, await nova.embed(), antiga=owner)


class BotaoRetomar(discord.ui.Button):
    def __init__(self, cog, game_id: int):
        super().__init__(label="Continuar última jornada", emoji="▶️", style=discord.ButtonStyle.success, row=1)
        self.cog, self.game_id = cog, game_id

    async def callback(self, interaction: discord.Interaction):
        owner = self.view
        game = await svc.buscar_jogo(self.cog.bot.db, self.game_id)
        if not game or game["status"] != "ready":
            return await interaction.response.send_message("Esse catálogo não está mais disponível.", ephemeral=True)
        nova = PainelJogoView(self.cog, owner.user_id, game)
        await mostrar(interaction, nova, await nova.embed(), antiga=owner)


class BotaoSolicitarJogo(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="Não encontrou seu jogo? Solicitar cadastro", emoji="🔎",
                         style=discord.ButtonStyle.secondary, row=1)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SolicitarJogoModal(self.cog))


class PainelCacadorView(ViewDono):
    def __init__(self, cog, user, page: int = 0):
        super().__init__(user.id)
        self.cog, self.page = cog, page
        self._paginas = 1

    async def embed(self) -> discord.Embed:
        db = self.cog.bot.db
        jogos = await svc.listar_jogos(db)
        self._paginas = max(1, -(-len(jogos) // POR_PAGINA))
        self.page = max(0, min(self.page, self._paginas - 1))
        ultimo = await svc.ultimo_jogo(db, self.user_id)
        e = discord.Embed(
            title="📜 NARA — CAÇADOR DE TROFÉUS",
            description="Acompanhe troféus e colecionáveis em um único progresso.\n"
                        "Escolha um jogo para começar ou retome sua última jornada.",
            color=config.COR_OURO,
        )
        if ultimo:
            feitos, total = await svc.progresso_jogo(db, ultimo["id"], self.user_id)
            e.add_field(name="▶️ Continuar jornada",
                        value=_corta(f"**{ultimo['name']}**\n{feitos}/{total} itens · {_barra(feitos, total)}", 1024),
                        inline=False)
        if jogos:
            inicio = self.page * POR_PAGINA
            fatia = jogos[inicio:inicio + POR_PAGINA]
            rotulo = "🎮 Jogos disponíveis" + (f" (página {self.page + 1}/{self._paginas})" if self._paginas > 1 else "")
            e.add_field(name=rotulo, value=_corta("\n".join(f"• {_corta(g['name'], 60)}" for g in fatia), 1024),
                        inline=False)
        else:
            e.add_field(
                name="Catálogo em preparação",
                value="Ainda não há jogos publicados. Os catálogos precisam ser importados e validados antes de aparecerem para os jogadores.",
                inline=False,
            )
        e.set_footer(text="Seu progresso é individual e fica salvo no banco da Nara.")
        return e

    async def montar(self) -> None:
        self.clear_items()
        db = self.cog.bot.db
        jogos = await svc.listar_jogos(db)
        self._paginas = max(1, -(-len(jogos) // POR_PAGINA))
        self.page = max(0, min(self.page, self._paginas - 1))
        inicio = self.page * POR_PAGINA
        if jogos:
            self.add_item(SeletorJogo(self.cog, jogos[inicio:inicio + POR_PAGINA]))
        ultimo = await svc.ultimo_jogo(db, self.user_id)
        if ultimo:
            self.add_item(BotaoRetomar(self.cog, int(ultimo["id"])))
        self.add_item(BotaoSolicitarJogo(self.cog))
        self.add_item(BotaoFechar())
        if self._paginas > 1:
            if self.page > 0:
                self.add_item(BotaoPagina(self, -1))
            if self.page < self._paginas - 1:
                self.add_item(BotaoPagina(self, 1))

    async def mudar_pagina(self, interaction: discord.Interaction, delta: int) -> None:
        self.page += delta
        await self.montar()
        await mostrar(interaction, self, await self.embed())


class SolicitarJogoModal(discord.ui.Modal, title="Solicitar cadastro de jogo"):
    nome = discord.ui.TextInput(label="Nome do jogo", placeholder="Ex.: Lies of P", max_length=100, required=True)
    plataforma = discord.ui.TextInput(label="Plataforma (opcional)", placeholder="PC, PlayStation, Xbox...",
                                      max_length=80, required=False)

    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        nome = " ".join(str(self.nome.value).split()).strip()
        plataforma = " ".join(str(self.plataforma.value or "").split()).strip()
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.cog.identificar_e_confirmar(interaction, nome, plataforma)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        log.error("Erro no formulário de solicitação de jogo", exc_info=error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Não consegui processar o formulário. Tente de novo.", ephemeral=True)
            else:
                await interaction.response.send_message("Não consegui processar o formulário. Tente de novo.", ephemeral=True)
        except discord.HTTPException:
            pass


# ----------------------------------------------------------------------------
# Painel do jogo
# ----------------------------------------------------------------------------
class BotaoVoltarJogo(discord.ui.Button):
    def __init__(self, cog, game, row: int = 1):
        super().__init__(label="Voltar ao jogo", emoji="↩️", style=discord.ButtonStyle.secondary, row=row)
        self.cog, self.game = cog, game

    async def callback(self, interaction: discord.Interaction):
        owner = self.view
        nova = PainelJogoView(self.cog, owner.user_id, self.game)
        await mostrar(interaction, nova, await nova.embed(), antiga=owner)


class PainelJogoView(ViewDono):
    def __init__(self, cog, user_id: int, game):
        super().__init__(user_id)
        self.cog, self.game = cog, game

    async def embed(self) -> discord.Embed:
        db, gid = self.cog.bot.db, int(self.game["id"])
        itens = await svc.progresso_itens_por_conteudo(db, gid, self.user_id)
        trof = await svc.progresso_trofeus_jogo(db, gid, self.user_id)
        cats = await svc.categorias_do_jogo(db, gid)
        trofeus = await svc.listar_trofeus(db, gid, self.user_id)
        platina = next((t for t in trofeus if t["is_platinum"]), None)

        linhas = [_linha_progresso("🏆 Troféus", trof["total"]), _linha_progresso("📦 Colecionáveis", itens["total"])]
        if platina is not None:
            linhas.append("💎 **Platina conquistada!**" if platina["completed"] else "💎 Platina ainda não conquistada")
        e = discord.Embed(title=_corta(f"🎮 {self.game['name']}", 256), description="\n".join(linhas), color=config.COR_OURO)

        nomes_dlc = sorted(set(trof["dlc"]) | set(itens["dlc"]), key=str.casefold)
        if nomes_dlc:
            bt, bi = trof["base"], itens["base"]
            e.add_field(name="🎮 Jogo base", value=f"🏆 {bt[0]}/{bt[1]} · 📦 {bi[0]}/{bi[1]}", inline=False)
            for nome in nomes_dlc[:8]:
                t, i = trof["dlc"].get(nome, (0, 0)), itens["dlc"].get(nome, (0, 0))
                e.add_field(name=_corta(f"➕ {nome}", 256), value=f"🏆 {t[0]}/{t[1]} · 📦 {i[0]}/{i[1]}", inline=True)
            if len(nomes_dlc) > 8:
                e.add_field(name="Outras DLCs", value=f"+ {len(nomes_dlc) - 8} conteúdo(s) adicional(is).", inline=False)
        if cats:
            e.add_field(
                name="📦 Coleções",
                value=_corta("\n".join(f"• **{_corta(c['category'], 50)}** — {c['total']} itens" for c in cats[:12]), 1024),
                inline=False,
            )
        e.set_footer(text="Marque cada item uma vez; o progresso é compartilhado com os troféus relacionados.")
        return e

    @discord.ui.button(label="Coleções", emoji="📦", style=discord.ButtonStyle.primary, row=0)
    async def colecoes(self, interaction: discord.Interaction, button: discord.ui.Button):
        cats = await svc.categorias_do_jogo(self.cog.bot.db, self.game["id"])
        if not cats:
            return await interaction.response.send_message("Ainda não existem coleções cadastradas para este jogo.", ephemeral=True)
        nova = CategoriasView(self.cog, self.user_id, self.game, cats)
        nova.montar()
        await mostrar(interaction, nova, await nova.embed(), antiga=self)

    @discord.ui.button(label="Troféus", emoji="🏆", style=discord.ButtonStyle.success, row=0)
    async def trofeus(self, interaction: discord.Interaction, button: discord.ui.Button):
        nova = TrofeusView(self.cog, self.user_id, self.game)
        await nova.rebuild()
        await mostrar(interaction, nova, await nova.embed(), antiga=self)

    @discord.ui.button(label="Voltar", emoji="↩️", style=discord.ButtonStyle.secondary, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        nova = PainelCacadorView(self.cog, interaction.user)
        await nova.montar()
        await mostrar(interaction, nova, await nova.embed(), antiga=self)


# ----------------------------------------------------------------------------
# Coleções
# ----------------------------------------------------------------------------
class SeletorCategoria(discord.ui.Select):
    def __init__(self, owner_view, categorias):
        self.owner_view = owner_view
        options = [
            discord.SelectOption(label=_corta(f"{c['category']} ({c['total']})", 100), value=c["category"][:100])
            for c in categorias
        ]
        super().__init__(placeholder="Escolha uma coleção...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        o = self.owner_view
        categoria = next((c["category"] for c in o.categories if c["category"][:100] == self.values[0]), self.values[0])
        nova = ListaItensView(o.cog, o.user_id, o.game, categoria)
        await nova.rebuild()
        await mostrar(interaction, nova, await nova.embed(), antiga=o)


class CategoriasView(ViewDono):
    def __init__(self, cog, user_id, game, categories, page: int = 0):
        super().__init__(user_id)
        self.cog, self.game, self.categories, self.page = cog, game, list(categories), page

    def _fatia(self):
        paginas = max(1, -(-len(self.categories) // POR_PAGINA))
        self.page = max(0, min(self.page, paginas - 1))
        inicio = self.page * POR_PAGINA
        return self.categories[inicio:inicio + POR_PAGINA], paginas

    def montar(self) -> None:
        self.clear_items()
        fatia, paginas = self._fatia()
        if fatia:
            self.add_item(SeletorCategoria(self, fatia))
        self.add_item(BotaoVoltarJogo(self.cog, self.game))
        if paginas > 1:
            if self.page > 0:
                self.add_item(BotaoPagina(self, -1, row=1))
            if self.page < paginas - 1:
                self.add_item(BotaoPagina(self, 1, row=1))

    async def mudar_pagina(self, interaction: discord.Interaction, delta: int) -> None:
        self.page += delta
        self.montar()
        await mostrar(interaction, self, await self.embed())

    async def embed(self) -> discord.Embed:
        fatia, paginas = self._fatia()
        e = discord.Embed(
            title=_corta(f"📦 Coleções — {self.game['name']}", 256),
            description="Escolha uma categoria para ver os itens, buscar por nome e marcar o que já conseguiu."
                        + (f"\nPágina {self.page + 1}/{paginas}" if paginas > 1 else ""),
            color=config.COR_OURO,
        )
        for c in fatia:
            got, total = await svc.progresso_categoria(self.cog.bot.db, self.game["id"], c["category"], self.user_id)
            e.add_field(name=_corta(c["category"], 256), value=f"{got}/{total} · {_barra(got, total)}", inline=True)
        return e


class SeletorItem(discord.ui.Select):
    def __init__(self, owner_view, items):
        self.owner_view = owner_view
        options = []
        for item in items:
            status = "✅ Obtido" if item["obtained"] else "⬜ Faltando"
            extra = " · ⚠️ Perdível" if item["missable"] else ""
            options.append(discord.SelectOption(
                label=_corta(_nome(item), 100), value=str(item["id"]),
                description=_corta(f"{status}{extra}", 100),
                default=(owner_view.selected_item_id == item["id"]),
            ))
        super().__init__(placeholder="Selecione um item para ver detalhes...", min_values=1, max_values=1,
                         options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.owner_view.selected_item_id = int(self.values[0])
        await self.owner_view.rebuild()
        await mostrar(interaction, self.owner_view, await self.owner_view.embed())


class BuscaItemModal(discord.ui.Modal, title="Buscar item"):
    termo = discord.ui.TextInput(label="Nome (ou parte do nome)", max_length=60, required=False,
                                 placeholder="Deixe vazio para limpar a busca")

    def __init__(self, owner_view):
        super().__init__(timeout=180)
        self.owner_view = owner_view

    async def on_submit(self, interaction: discord.Interaction):
        o = self.owner_view
        o.busca = " ".join(str(self.termo.value or "").split())
        o.page, o.selected_item_id = 0, None
        await o.rebuild()
        await mostrar(interaction, o, await o.embed())


class BotaoMarcarItem(discord.ui.Button):
    def __init__(self, owner_view, obtido: bool):
        super().__init__(label="Marcar obtido" if obtido else "Desmarcar", emoji="✅" if obtido else "↩️",
                         style=discord.ButtonStyle.success if obtido else discord.ButtonStyle.secondary, row=1)
        self.owner_view, self.obtido = owner_view, obtido

    async def callback(self, interaction: discord.Interaction):
        await self.owner_view.marcar(interaction, self.obtido)


class BotaoBuscarItem(discord.ui.Button):
    def __init__(self, owner_view):
        super().__init__(label="Buscar", emoji="🔎", style=discord.ButtonStyle.primary, row=1)
        self.owner_view = owner_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BuscaItemModal(self.owner_view))


class BotaoLimparBusca(discord.ui.Button):
    def __init__(self, owner_view):
        super().__init__(label="Limpar busca", emoji="🧹", style=discord.ButtonStyle.secondary, row=2)
        self.owner_view = owner_view

    async def callback(self, interaction: discord.Interaction):
        o = self.owner_view
        o.busca, o.page, o.selected_item_id = "", 0, None
        await o.rebuild()
        await mostrar(interaction, o, await o.embed())


class BotaoVoltarCategorias(discord.ui.Button):
    def __init__(self, owner_view):
        super().__init__(label="Categorias", emoji="↩️", style=discord.ButtonStyle.secondary, row=2)
        self.owner_view = owner_view

    async def callback(self, interaction: discord.Interaction):
        o = self.owner_view
        cats = await svc.categorias_do_jogo(o.cog.bot.db, o.game["id"])
        nova = CategoriasView(o.cog, o.user_id, o.game, cats)
        nova.montar()
        await mostrar(interaction, nova, await nova.embed(), antiga=o)


class ListaItensView(ViewDono):
    PAGE_SIZE = 20

    def __init__(self, cog, user_id, game, category, page: int = 0, selected_item_id=None, busca: str = ""):
        super().__init__(user_id)
        self.cog, self.game, self.category = cog, game, category
        self.page, self.selected_item_id, self.busca = page, selected_item_id, busca

    async def _items(self):
        return await svc.listar_itens(self.cog.bot.db, self.game["id"], self.category, self.user_id,
                                      self.PAGE_SIZE, self.page * self.PAGE_SIZE, self.busca)

    async def embed(self) -> discord.Embed:
        db = self.cog.bot.db
        items = await self._items()
        got, total = await svc.progresso_categoria(db, self.game["id"], self.category, self.user_id)
        encontrados = await svc.contar_itens(db, self.game["id"], self.category, self.busca)
        paginas = max(1, -(-encontrados // self.PAGE_SIZE))
        cabecalho = f"**{got}/{total} obtidos** · {_barra(got, total)}\nPágina {self.page + 1}/{paginas}"
        if self.busca:
            cabecalho += f" · 🔎 “{_md(self.busca, 40)}” ({encontrados} resultado(s))"
        linhas = []
        for it in items:
            marca = "▶ " if self.selected_item_id == it["id"] else ""
            estado = "✅" if it["obtained"] else "⬜"
            aviso = " ⚠️" if it["missable"] else ""
            linhas.append(f"{marca}{estado} {_md(_nome(it), 70)}{aviso}")
        corpo = "\n".join(linhas) if linhas else "Nenhum item encontrado."
        e = discord.Embed(title=_corta(f"📦 {self.category} — {self.game['name']}", 256),
                          description=_corta(f"{cabecalho}\n\n{corpo}", 4000), color=config.COR_OURO)
        selecionado = next((x for x in items if x["id"] == self.selected_item_id), None)
        if selecionado is not None:
            detalhes = []
            if selecionado["location_pt"]:
                detalhes.append(f"**Localização:** {selecionado['location_pt']}")
            if selecionado["acquisition_pt"]:
                detalhes.append(f"**Como obter:** {selecionado['acquisition_pt']}")
            if selecionado["dlc"]:
                detalhes.append(f"**Conteúdo:** {selecionado['dlc']}")
            if selecionado["ng_cycle"]:
                detalhes.append(f"**Ciclo:** {selecionado['ng_cycle']}")
            if selecionado["missable"]:
                detalhes.append("⚠️ **Perdível:** pode exigir atenção a uma condição ou progresso específico.")
            if selecionado["description_pt"]:
                detalhes.append(selecionado["description_pt"])
            if selecionado["source_url"]:
                detalhes.append(f"[Fonte consultada]({selecionado['source_url']})")
            e.add_field(name=_corta(f"Detalhes — {_nome(selecionado)}", 256),
                        value=_corta("\n".join(detalhes) or "Sem detalhes cadastrados.", 1024), inline=False)
        return e

    async def rebuild(self) -> None:
        self.clear_items()
        items = await self._items()
        if items:
            self.add_item(SeletorItem(self, items))
        self.add_item(BotaoMarcarItem(self, True))
        self.add_item(BotaoMarcarItem(self, False))
        self.add_item(BotaoBuscarItem(self))
        total = await svc.contar_itens(self.cog.bot.db, self.game["id"], self.category, self.busca)
        if self.busca:
            self.add_item(BotaoLimparBusca(self))
        if self.page > 0:
            self.add_item(BotaoPagina(self, -1))
        if (self.page + 1) * self.PAGE_SIZE < total:
            self.add_item(BotaoPagina(self, 1))
        self.add_item(BotaoVoltarCategorias(self))

    async def mudar_pagina(self, interaction: discord.Interaction, delta: int) -> None:
        self.page = max(0, self.page + delta)
        self.selected_item_id = None
        await self.rebuild()
        await mostrar(interaction, self, await self.embed())

    async def marcar(self, interaction: discord.Interaction, obtido: bool) -> None:
        if not self.selected_item_id:
            return await interaction.response.send_message("Selecione um item primeiro.", ephemeral=True)
        try:
            await svc.definir_item_obtido(self.cog.bot.db, self.user_id, self.selected_item_id, obtido)
        except ValueError as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)
        await self.rebuild()
        await mostrar(interaction, self, await self.embed())


# ----------------------------------------------------------------------------
# Troféus
# ----------------------------------------------------------------------------
class SeletorTrofeu(discord.ui.Select):
    def __init__(self, owner_view, trofeus):
        self.owner_view = owner_view
        options = []
        for t in trofeus:
            estado = "✅ " if t["completed"] else ""
            resumo = t["description_pt"] or t["grade"] or "Ver requisitos"
            options.append(discord.SelectOption(
                label=_corta(svc.nome_exibicao(t["name_pt"], t["name_original"]), 100), value=str(t["id"]),
                description=_corta(f"{estado}{resumo}", 100),
                default=(owner_view.selected_trophy_id == t["id"]),
            ))
        super().__init__(placeholder="Escolha um troféu...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.owner_view.selected_trophy_id = int(self.values[0])
        await self.owner_view.rebuild()
        await mostrar(interaction, self.owner_view, await self.owner_view.embed())


class SeletorFiltroTrofeus(discord.ui.Select):
    def __init__(self, owner_view):
        self.owner_view = owner_view
        options = [
            discord.SelectOption(label="Todos os troféus", value="todos", default=owner_view.filtro is None),
            discord.SelectOption(label="Somente jogo base", value="base", default=owner_view.filtro == ""),
        ]
        for i, nome in enumerate(owner_view.dlcs[:23]):
            options.append(discord.SelectOption(label=_corta(f"DLC: {nome}", 100), value=f"d{i}",
                                                default=owner_view.filtro == nome))
        super().__init__(placeholder="Filtrar: jogo base / DLC", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        o, valor = self.owner_view, self.values[0]
        o.filtro = None if valor == "todos" else "" if valor == "base" else o.dlcs[int(valor[1:])]
        o.page, o.selected_trophy_id = 0, None
        await o.rebuild()
        await mostrar(interaction, o, await o.embed())


class BotaoAlternarTrofeu(discord.ui.Button):
    def __init__(self, owner_view, concluido: bool):
        super().__init__(label="Desmarcar conquista" if concluido else "Marcar como conquistado",
                         emoji="↩️" if concluido else "☑️",
                         style=discord.ButtonStyle.secondary if concluido else discord.ButtonStyle.success, row=2)
        self.owner_view = owner_view

    async def callback(self, interaction: discord.Interaction):
        o = self.owner_view
        try:
            await svc.alternar_trofeu(o.cog.bot.db, o.user_id, o.selected_trophy_id)
        except ValueError as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)
        await o.rebuild()
        await mostrar(interaction, o, await o.embed())


class TrofeusView(ViewDono):
    def __init__(self, cog, user_id, game):
        super().__init__(user_id)
        self.cog, self.game = cog, game
        self.page = 0
        self.filtro: str | None = None     # None = todos · "" = jogo base · "<nome>" = uma DLC
        self.selected_trophy_id: int | None = None
        self.dlcs: list[str] = []
        self._todos: list = []

    async def _carregar(self) -> None:
        self._todos = list(await svc.listar_trofeus(self.cog.bot.db, self.game["id"], self.user_id))
        self.dlcs = sorted({t["dlc"] for t in self._todos if t["dlc"]}, key=str.casefold)

    def _filtrados(self) -> list:
        if self.filtro is None:
            return self._todos
        return [t for t in self._todos if (t["dlc"] or "") == self.filtro]

    def _pagina(self) -> tuple[list, int]:
        lista = self._filtrados()
        paginas = max(1, -(-len(lista) // TROFEUS_POR_PAGINA))
        self.page = max(0, min(self.page, paginas - 1))
        inicio = self.page * TROFEUS_POR_PAGINA
        return lista[inicio:inicio + TROFEUS_POR_PAGINA], paginas

    async def embed(self) -> discord.Embed:
        await self._carregar()
        db = self.cog.bot.db
        prog = await svc.progresso_trofeus_jogo(db, self.game["id"], self.user_id)
        pagina, paginas = self._pagina()
        topo = [_linha_progresso("🏆 Conquistados", prog["total"])]
        if prog["dlc"]:
            topo.append(_linha_progresso("🎮 Jogo base", prog["base"]))
            for nome, par in list(prog["dlc"].items())[:6]:
                topo.append(_linha_progresso(f"➕ {_corta(nome, 40)}", par))
        escopo = "todos" if self.filtro is None else "jogo base" if self.filtro == "" else f"DLC {self.filtro}"
        topo.append(f"\nExibindo **{escopo}** · página {self.page + 1}/{paginas}")
        linhas = []
        for t in pagina:
            marca = "▶ " if self.selected_trophy_id == t["id"] else ""
            estado = "✅" if t["completed"] else "⬜"
            tags = _tags_trofeu(t)
            linhas.append(f"{marca}{estado} {_md(svc.nome_exibicao(t['name_pt'], t['name_original']), 60)}"
                          + (f" — {' · '.join(tags)}" if tags else ""))
        corpo = "\n".join(linhas) if linhas else "Nenhum troféu neste filtro."
        e = discord.Embed(title=_corta(f"🏆 Troféus — {self.game['name']}", 256),
                          description=_corta("\n".join(topo) + "\n\n" + corpo, 4000), color=config.COR_OURO)
        selecionado = next((t for t in self._todos if t["id"] == self.selected_trophy_id), None)
        if selecionado is not None:
            feitos, total, reqs = await svc.progresso_trofeu(db, selecionado["id"], self.user_id)
            detalhes = []
            tags = _tags_trofeu(selecionado)
            if selecionado["grade"] and not selecionado["is_platinum"]:
                tags.insert(0, f"🏅 {selecionado['grade']}")
            if tags:
                detalhes.append(" · ".join(tags))
            if selecionado["description_pt"]:
                detalhes.append(selecionado["description_pt"])
            vinculados = [r for r in reqs if r["item_id"] is not None]
            if selecionado["completed"]:
                detalhes.append("**Status:** ✅ conquistado")
            elif vinculados:
                detalhes.append(f"**Progresso dos itens:** {feitos}/{total} · {_barra(feitos, total)}")
            for r in reqs[:12]:
                if r["item_id"] is not None:
                    rotulo = svc.nome_exibicao(r["name_pt"] or r["description_pt"], r["name_original"] or "")
                    detalhes.append(f"{'✅' if r['obtained'] else '⬜'} {_md(rotulo, 80)}")
                elif r["description_pt"]:
                    detalhes.append(f"• Requisito: {_corta(r['description_pt'], 160)}")
            if not vinculados:
                detalhes.append("_Acompanhado por confirmação manual._")
            if selecionado["source_url"]:
                detalhes.append(f"[Fonte]({selecionado['source_url']})")
            e.add_field(name=_corta(f"Detalhes — {svc.nome_exibicao(selecionado['name_pt'], selecionado['name_original'])}", 256),
                        value=_corta("\n".join(detalhes), 1024), inline=False)
        return e

    async def rebuild(self) -> None:
        await self._carregar()
        self.clear_items()
        pagina, paginas = self._pagina()
        if pagina:
            self.add_item(SeletorTrofeu(self, pagina))
        if self.dlcs:
            self.add_item(SeletorFiltroTrofeus(self))
        if self.selected_trophy_id is not None:
            atual = next((t for t in self._todos if t["id"] == self.selected_trophy_id), None)
            if atual is not None:
                self.add_item(BotaoAlternarTrofeu(self, bool(atual["completed"])))
        if paginas > 1:
            if self.page > 0:
                self.add_item(BotaoPagina(self, -1))
            if self.page < paginas - 1:
                self.add_item(BotaoPagina(self, 1))
        self.add_item(BotaoVoltarJogo(self.cog, self.game, row=2))

    async def mudar_pagina(self, interaction: discord.Interaction, delta: int) -> None:
        self.page += delta
        self.selected_trophy_id = None
        await self.rebuild()
        await mostrar(interaction, self, await self.embed())


# ----------------------------------------------------------------------------
# Identificação e confirmação do jogo
# ----------------------------------------------------------------------------
class SeletorCandidato(discord.ui.Select):
    def __init__(self, owner_view):
        self.owner_view = owner_view
        opts = []
        for i, c in enumerate(owner_view.candidates[:5]):
            year = f" · {c['release_year']}" if c.get("release_year") else ""
            conf = f"Confiança {round(c['confidence'] * 100)}%"
            opts.append(discord.SelectOption(
                label=_corta(c["canonical_title"] + year, 100), value=str(i),
                description=_corta(f"{c.get('developer') or 'Estúdio não confirmado'} · {conf}", 100),
            ))
        super().__init__(placeholder="Selecione o jogo correto...", min_values=1, max_values=1, options=opts, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.owner_view.selected = int(self.values[0])
        await interaction.response.edit_message(embed=self.owner_view.embed(), view=self.owner_view)


class ConfirmarPesquisaJogo(discord.ui.Button):
    def __init__(self, owner_view):
        super().__init__(label="Confirmar jogo e pesquisar catálogo", emoji="🔎",
                         style=discord.ButtonStyle.success, row=1)
        self.owner_view = owner_view
        self.claimed = False

    async def callback(self, interaction: discord.Interaction):
        p = self.owner_view
        if p.selected is None:
            return await interaction.response.send_message("Selecione primeiro o jogo correto.", ephemeral=True)
        if self.claimed:
            return await interaction.response.send_message("Esta pesquisa já foi iniciada.", ephemeral=True)

        # Claim antes do primeiro await: dois cliques quase simultâneos não iniciam duas pesquisas.
        self.claimed = True
        candidate = p.candidates[p.selected]
        for child in p.children:
            child.disabled = True
        # edit_message confirma a interação E desabilita os botões na própria mensagem efêmera
        # (interaction.message.edit não funciona em mensagens efêmeras).
        await interaction.response.edit_message(view=p)

        resultado = await p.cog.pesquisar_e_importar(
            candidate, query=p.query, identity_sources=p.sources, solicitante_id=p.user_id,
            job_id=p.job_id, admin=_eh_admin(interaction), actor_id=interaction.user.id,
            guild_id=interaction.guild_id,
        )
        if resultado.game is not None:
            painel = PainelJogoView(p.cog, p.user_id, resultado.game)
            await svc.registrar_acesso(p.cog.bot.db, p.user_id, int(resultado.game["id"]))
            await interaction.followup.send(resultado.mensagem, embed=await painel.embed(), view=painel, ephemeral=True)
            painel._interaction = interaction
            p.stop()
            return
        if not resultado.ok:
            # O pedido ficou preservado na fila: libera o botão para uma nova tentativa sem duplicar nada.
            self.claimed = False
            for child in p.children:
                child.disabled = False
            await self._atualizar_mensagem(interaction, p)
        else:
            p.stop()
        try:
            await interaction.followup.send(resultado.mensagem, ephemeral=True)
        except discord.HTTPException:
            log.exception("Não foi possível enviar o resultado da pesquisa ao usuário")

    @staticmethod
    async def _atualizar_mensagem(interaction: discord.Interaction, view) -> None:
        try:
            await interaction.edit_original_response(view=view)
        except discord.HTTPException:
            log.warning("Não foi possível atualizar os botões da confirmação de pesquisa")


class ConfirmacaoJogoView(ViewDono):
    def __init__(self, cog, user_id, query, candidates, sources, notes, job_id: int | None = None):
        super().__init__(user_id, timeout=300)
        self.cog, self.query = cog, query
        self.candidates, self.sources, self.notes, self.job_id = candidates, sources, notes, job_id
        self.selected = 0 if len(candidates) == 1 else None
        if len(candidates) > 1:
            self.add_item(SeletorCandidato(self))
        self.add_item(ConfirmarPesquisaJogo(self))
        self.add_item(BotaoFechar())

    def embed(self) -> discord.Embed:
        e = discord.Embed(
            title="Identificação do jogo",
            description=f"Entrada pesquisada: **{_md(self.query, 120)}**\n"
                        "A entrada não será usada como nome oficial. Confirme a correspondência antes da pesquisa do catálogo.",
            color=config.COR_OURO,
        )
        for i, c in enumerate(self.candidates[:5]):
            marca = " ▶" if self.selected == i else ""
            e.add_field(
                name=_corta(f"{i + 1}. {c['canonical_title']}{marca}", 256),
                value=_corta(f"Original: {c.get('original_title') or '—'} · Ano: {c.get('release_year') or '—'}\n"
                             f"Estúdio: {c.get('developer') or '—'} · Confiança estimada: {round(c['confidence'] * 100)}%\n"
                             f"Escopo: {c.get('edition_scope') or 'Não determinado'}\n"
                             f"{c.get('identity_evidence') or ''}", 900),
                inline=False,
            )
        if self.notes:
            e.add_field(name="Observações", value=_corta(self.notes, 900), inline=False)
        fontes = []
        for source in self.sources[:8]:
            if not isinstance(source, dict):
                continue
            url = str(source.get("url", "")).strip()
            if not url.startswith("https://"):
                continue
            fontes.append(f"• [{_md(source.get('title') or url, 100)}]({url})")
        if fontes:
            e.add_field(name="Fontes para conferência", value=_corta("\n".join(fontes), 1024), inline=False)
        elif not self.sources:
            e.add_field(name="Base da identificação",
                        value="Base local curada. A pesquisa do catálogo fará sua própria busca, com fontes.",
                        inline=False)
        e.set_footer(text="A confiança é estimativa, não garantia factual. Confira antes de confirmar.")
        return e


# ----------------------------------------------------------------------------
# Administração
# ----------------------------------------------------------------------------
class ConfirmarValidacaoCatalogo(ViewDono):
    def __init__(self, cog, game_id, game_name, user_id):
        super().__init__(user_id, timeout=120)
        self.cog, self.game_id, self.game_name = cog, game_id, game_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id or not _eh_admin(interaction):
            await interaction.response.send_message(
                "Somente o administrador que abriu esta confirmação pode validar.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirmo que revisei", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            result = await svc.validar_catalogo(self.cog.bot.db, self.game_id, interaction.user.id)
        except Exception as exc:
            log.exception("Falha ao validar catálogo %s", self.game_id)
            return await interaction.response.send_message(
                f"Não foi possível validar o catálogo: {_md(str(exc), 400)}", ephemeral=True)
        self.stop()
        await interaction.response.edit_message(
            content=(f"Registros de **{_md(self.game_name)}** marcados como revisados "
                     f"({result['items']} itens e {result['trophies']} troféus). "
                     "Agora use `/adm` → Caçador para auditar e publicar, se aprovado."),
            view=None,
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Validação cancelada.", view=None)


class ModalAcaoCatalogo(discord.ui.Modal):
    def __init__(self, cog, acao: str):
        nomes = {"catalogo_auditar": "Auditar catálogo", "catalogo_validar": "Validar revisão humana",
                 "catalogo_publicar": "Publicar catálogo", "catalogo_rejeitar": "Rejeitar catálogo",
                 "catalogo_despublicar": "Despublicar catálogo", "catalogo_retentar": "Retentar pedido"}
        super().__init__(title=nomes[acao], timeout=180)
        self.cog, self.acao = cog, acao
        self.identificador = discord.ui.TextInput(label="Número do pedido" if acao == "catalogo_retentar" else "Slug do catálogo",
            placeholder="Ex.: 12" if acao == "catalogo_retentar" else "Ex.: lies-of-p", max_length=120)
        self.add_item(self.identificador)
        if acao in {"catalogo_rejeitar", "catalogo_despublicar"}:
            self.motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph,
                required=acao == "catalogo_rejeitar", max_length=500)
            self.add_item(self.motivo)

    async def on_submit(self, interaction: discord.Interaction):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Permissão Gerenciar Servidor necessária.", ephemeral=True)
        valor = str(self.identificador.value).strip()
        if self.acao == "catalogo_retentar":
            try:
                pedido = int(valor)
                if pedido < 1: raise ValueError()
            except ValueError:
                return await interaction.response.send_message("Informe um número de pedido válido.", ephemeral=True)
            return await type(self.cog).catalogo_retentar.callback(self.cog, interaction, pedido)
        if not valor:
            return await interaction.response.send_message("Informe o slug do catálogo.", ephemeral=True)
        if self.acao in {"catalogo_rejeitar", "catalogo_despublicar"}:
            return await getattr(type(self.cog), self.acao).callback(
                self.cog, interaction, valor, str(self.motivo.value).strip())
        return await getattr(type(self.cog), self.acao).callback(self.cog, interaction, valor)


class SelecionarAcaoCatalogo(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="Auditar, validar, publicar, rejeitar ou retentar…", min_values=1, max_values=1,
            options=[discord.SelectOption(label=nome, value=acao) for nome, acao in [
                ("Auditar fontes e cobertura", "catalogo_auditar"),
                ("Confirmar revisão humana", "catalogo_validar"),
                ("Publicar catálogo", "catalogo_publicar"),
                ("Rejeitar catálogo", "catalogo_rejeitar"),
                ("Despublicar catálogo", "catalogo_despublicar"),
                ("Retentar pesquisa da fila", "catalogo_retentar"),
                ("Ver histórico", "catalogo_historico")]])

    async def callback(self, interaction: discord.Interaction):
        cog = self.view.cog
        if self.values[0] == "catalogo_historico":
            return await type(cog).catalogo_historico.callback(cog, interaction, "")
        await interaction.response.send_modal(ModalAcaoCatalogo(cog, self.values[0]))


class PainelAdminCacador(ViewDono):
    def __init__(self, cog, user_id):
        super().__init__(user_id, timeout=300)
        self.cog = cog
        self.add_item(SelecionarAcaoCatalogo())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id or not _eh_admin(interaction):
            await interaction.response.send_message("Apenas o administrador que abriu o painel pode usá-lo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Ver fila de jogos", emoji="📥", style=discord.ButtonStyle.primary)
    async def ver_fila(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self.cog.embed_fila()
        if embed is None:
            return await interaction.response.send_message("A fila está vazia.", ephemeral=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Diagnóstico da pesquisa", emoji="🩺", style=discord.ButtonStyle.secondary)
    async def diagnostico(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.cog.texto_diagnostico(), ephemeral=True)

    @discord.ui.button(label="Fechar", emoji="✖️", style=discord.ButtonStyle.secondary)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Painel administrativo fechado.", embed=None, view=None)


# ----------------------------------------------------------------------------
# Cog
# ----------------------------------------------------------------------------
class CacadorTrofeus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- utilidades ----------
    async def _catalogo_por_slug(self, texto: str):
        texto = " ".join(str(texto or "").split())
        if not texto:
            return None
        db = self.bot.db
        row = await db._one("SELECT * FROM games_catalog WHERE slug=? COLLATE NOCASE", (texto,))
        if row:
            return row
        return await db._one("SELECT * FROM games_catalog WHERE name=? COLLATE NOCASE", (texto,))

    async def _autocomplete_slug(self, interaction: discord.Interaction, current: str):
        termo = (current or "").strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        rows = await self.bot.db._all(
            """SELECT slug,name,status FROM games_catalog
               WHERE slug LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\'
               ORDER BY updated_at DESC LIMIT 25""",
            (f"%{termo}%", f"%{termo}%"),
        )
        return [app_commands.Choice(name=_corta(f"{r['name']} [{r['status']}]", 100), value=str(r["slug"])[:100])
                for r in rows]

    def texto_diagnostico(self) -> str:
        from gemini_resilience import all_gemini_status
        from ia_provedores import pesquisa_status
        linhas = ["**🩺 Diagnóstico da pesquisa do Caçador**"]
        problemas = diagnostico_configuracao()
        linhas += [f"⚠️ {p}" for p in problemas] or ["✅ Chaves de pesquisa e de IA configuradas."]
        for nome, estado in all_gemini_status().items():
            rotulo = "Gemini principal" if nome == "primary" else "Gemini reserva"
            if estado["blocked"]:
                linhas.append(f"• {rotulo}: **pausado** ({estado['kind']}, ~{max(1, (estado['remaining_seconds'] + 59) // 60)} min)")
            else:
                linhas.append(f"• {rotulo}: circuito liberado")
        busca = pesquisa_status()
        if busca["blocked"]:
            linhas.append(f"• Tavily Free: **pausada** ({busca['kind']}, ~{max(1, (busca['remaining_seconds'] + 59) // 60)} min)")
        else:
            linhas.append("• Tavily Free: circuito liberado" if busca["configured"] else "• Tavily Free: **não configurada**")
        linhas.append(f"• Teto: {config.CACADOR_PESQUISAS_DIA} pesquisas completas/dia no servidor; "
                      f"{config.CACADOR_LIMITE_USUARIO} identificações/{config.CACADOR_JANELA_MINUTOS} min por jogador.")
        return _corta("\n".join(linhas), 1900)

    async def embed_fila(self, limite: int = 15):
        await fila.reconciliar_orfaos(self.bot.db, 5)
        rows = await fila.listar_fila(self.bot.db, limite)
        if not rows:
            return None
        linhas = []
        for r in rows:
            rotulo = fila.ROTULOS.get(r["status"], r["status"])
            tentativas = f" · {r['attempts']} tentativa(s)" if r["attempts"] else ""
            resumo = _md(fila.resumo_job(r), 220) or "Sem detalhes."
            linhas.append(f"`#{r['id']}` **{_md(r['game_name'], 80)}** · <@{r['requested_by']}> · `{rotulo}`{tentativas}\n↳ {resumo}")
        e = discord.Embed(title="📥 Solicitações de novos jogos", description=_corta("\n\n".join(linhas), 4000),
                          color=config.COR_OURO)
        e.set_footer(text="Use /catalogo_retentar <id> para retomar um pedido sem duplicá-lo.")
        return e

    async def _avisar_moderacao(self, guild_id: int, texto: str) -> None:
        """Envia avisos de catálogo para a mesma Central de Aprovação do servidor."""
        if not guild_id:
            return
        try:
            canal_id = await GuildConfig.get(self.bot.db, guild_id, "mod_channel")
            if not canal_id:
                return
            canal = await get_text_channel(self.bot, canal_id)
            if canal is not None:
                await canal.send(texto[:1900], allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            log.warning("Não foi possível avisar a Central de Aprovação sobre o novo catálogo", exc_info=True)

    # ---------- fluxo de identificação ----------
    async def identificar_e_confirmar(self, interaction: discord.Interaction, nome: str, plataforma: str = "") -> None:
        """Resolve o nome digitado e mostra a confirmação. Usa `followup` (interação já adiada)."""
        db = self.bot.db
        nome = " ".join(str(nome or "").split())[:120]
        if len(nome) < 2:
            return await interaction.followup.send("Digite pelo menos dois caracteres.", ephemeral=True)
        try:
            existente = await svc.buscar_jogo_por_nome_ou_alias(db, nome)
            if existente:
                await svc.registrar_acesso(db, interaction.user.id, int(existente["id"]))
                painel = PainelJogoView(self, interaction.user.id, existente)
                await interaction.followup.send(
                    f"Correspondência encontrada no catálogo: **{_md(existente['name'])}**.",
                    embed=await painel.embed(), view=painel, ephemeral=True)
                painel._interaction = interaction
                return

            # Base local não gasta API nem a cota do jogador.
            result = catalogo_ia.identificar_local(nome)
            if result is None:
                permitido, _, _ = await db.reservar_pesquisa_catalogo(
                    interaction.user.id, limite=config.CACADOR_LIMITE_USUARIO,
                    janela_minutos=config.CACADOR_JANELA_MINUTOS)
                if not permitido:
                    return await interaction.followup.send(
                        f"Limite de pesquisa atingido: são permitidas até {config.CACADOR_LIMITE_USUARIO} "
                        f"identificações por {config.CACADOR_JANELA_MINUTOS} minutos para evitar abuso da API. "
                        "Tente novamente mais tarde.", ephemeral=True)
                result = await catalogo_ia.identificar_jogo(nome)
        except Exception as exc:
            return await self._falha_identificacao(interaction, nome, plataforma, exc)

        candidatos = result.get("candidates", [])
        if not candidatos:
            return await interaction.followup.send(
                "Não encontrei uma correspondência confiável. Tente incluir o ano, o estúdio ou a plataforma. "
                "Nenhum nome foi cadastrado.", ephemeral=True)
        view = ConfirmacaoJogoView(self, interaction.user.id, nome, candidatos,
                                   result.get("sources", []), result.get("notes", ""))
        prefixo = f"Plataforma informada: **{_md(plataforma)}**. " if plataforma else ""
        await interaction.followup.send(
            f"{prefixo}Confirme o título oficial abaixo para iniciar a pesquisa do catálogo.",
            embed=view.embed(), view=view, ephemeral=True)
        view._interaction = interaction

    async def _falha_identificacao(self, interaction: discord.Interaction, nome: str, plataforma: str,
                                   exc: BaseException) -> None:
        db = self.bot.db
        transitoria, admin_msg, user_msg = fila.classificar_erro(exc)
        if transitoria:
            log.warning("Identificação de %r indisponível: %s", nome, admin_msg[:300])
        else:
            log.error("Falha ao identificar %r", nome, exc_info=exc)
        job_id, criado = None, False
        try:
            if transitoria:
                await db.devolver_pesquisa_catalogo(interaction.user.id)  # a falha não foi do jogador
            job_id, criado, _ = await fila.abrir_job(
                db, interaction.user.id, nome, chave=fila.chave_consulta(nome),
                details=f"Plataforma: {plataforma or 'não informada'}")
            await fila.registrar_falha(db, job_id, exc)
        except Exception:
            log.exception("Não foi possível guardar o pedido de %r na fila", nome)
        if job_id is None:
            destino = "Não consegui registrar o pedido na fila; tente de novo em instantes."
        elif criado:
            destino = f"Seu pedido foi guardado na fila (#{job_id}) e a administração pode retomá-lo."
        else:
            destino = f"Já existe um pedido para este jogo (#{job_id}); não criei outro."
        try:
            await interaction.followup.send(
                f"**A identificação automática não pôde ser concluída.**\n"
                f"Jogo: **{_md(nome, 120)}**\nMotivo: {_md(user_msg, 400)}\n{destino}",
                ephemeral=True)
        except discord.HTTPException:
            log.exception("Não foi possível notificar a falha de identificação")

    # ---------- pesquisa e importação ----------
    async def pesquisar_e_importar(self, candidate: dict, *, query: str, identity_sources: list,
                                   solicitante_id: int, job_id: int | None = None, admin: bool = False,
                                   actor_id: int | None = None, guild_id: int | None = None) -> ResultadoPesquisa:
        """Pesquisa o catálogo de um título confirmado, sem duplicar pedidos e sem perder falhas."""
        db = self.bot.db
        actor_id = actor_id or solicitante_id
        titulo = str(candidate.get("canonical_title", "")).strip()
        ano = candidate.get("release_year")
        ano = ano if isinstance(ano, int) else None
        nome_exibicao = f"{titulo} ({ano})" if ano else titulo
        try:
            slug = svc.slug_jogo(titulo, ano)
            atual = await db._one("SELECT * FROM games_catalog WHERE slug=?", (slug,))
            if atual is not None and atual["status"] == "ready":
                if job_id:
                    await fila.encerrar_jobs_do_jogo(db, int(atual["id"]), "published")
                return ResultadoPesquisa(True, f"**{_md(atual['name'])}** já está publicado. Abri o catálogo sem gastar pesquisa.", atual)
            if atual is not None and atual["status"] == "rejected" and not admin:
                return ResultadoPesquisa(False, "Este catálogo já foi analisado e rejeitado pela administração. "
                                                "Fale com um administrador para reavaliá-lo.")
            if atual is not None and atual["status"] == "review":
                if job_id:  # queda entre importar e concluir: apenas reconcilia o pedido
                    await fila.concluir_job(db, job_id, int(atual["id"]), {"game_id": int(atual["id"]), "slug": slug})
                return ResultadoPesquisa(True, f"**{_md(atual['name'])}** já foi pesquisado e aguarda a revisão da administração.")

            if job_id is None:
                job_id, criado, status = await fila.abrir_job(
                    db, solicitante_id, nome_exibicao, chave=fila.chave_jogo(slug), candidate=candidate,
                    details=json.dumps({"input": query, "candidate": candidate}, ensure_ascii=False)[:1500])
                if not criado and status == "researching":
                    return ResultadoPesquisa(False, f"Já existe uma pesquisa em andamento para este jogo (#{job_id}). Aguarde a conclusão.")
                await fila.encerrar_consulta(db, fila.chave_consulta(query), job_id)
            else:
                job_id = await fila.promover_para_jogo(db, job_id, slug, nome_exibicao, candidate)

            if not await fila.marcar_pesquisando(db, job_id):
                return ResultadoPesquisa(False, f"Este pedido (#{job_id}) já está sendo pesquisado ou já foi concluído.")

            if not await db.reservar_orcamento_global("research", config.CACADOR_PESQUISAS_DIA):
                await fila.adiar_job(db, job_id, f"Limite diário de {config.CACADOR_PESQUISAS_DIA} pesquisas do servidor atingido.")
                return ResultadoPesquisa(False, f"O limite diário de pesquisas do servidor foi atingido. "
                                                f"Seu pedido ficou salvo na fila (#{job_id}) para ser retomado depois.")
        except Exception as exc:
            log.exception("Falha ao preparar a pesquisa de %r", titulo)
            return ResultadoPesquisa(False, f"Não consegui preparar a pesquisa ({_md(fila.classificar_erro(exc)[2], 300)}). Nada foi publicado.")

        try:
            payload = await catalogo_ia.pesquisar_catalogo(candidate, incluir_dlc=True)
            payload["name"] = nome_exibicao
            payload["name_original"] = candidate.get("original_title", "")
            payload["platforms"] = candidate.get("platforms", [])
            result = await svc.importar_catalogo(db, payload, publicar=False, actor_id=actor_id)
            # Não converta um nome genérico (ex.: "God of War") em alias de uma edição específica.
            base_titles = {titulo.casefold(), str(candidate.get("original_title") or "").casefold()}
            aliases = [a for a in (query, *candidate.get("aliases", [])) if str(a).strip().casefold() not in base_titles]
            await svc.salvar_aliases(db, result["game_id"], aliases)
            detalhes = {
                "game_id": result["game_id"], "slug": result["slug"],
                "coverage_notes": payload.get("coverage_notes", ""), "sources": payload.get("sources", []),
                "identity_sources": identity_sources, "research_sources": payload.get("research_sources", 0),
                "items": result["items_received"], "trophies": result["trophies_received"],
            }
            await fila.concluir_job(db, job_id, result["game_id"], detalhes)
        except Exception as exc:
            transitoria, user_msg = await self._registrar_falha_pesquisa(job_id, exc)
            if transitoria:
                try:
                    await db.devolver_orcamento_global("research")
                except Exception:
                    log.warning("Não foi possível devolver o orçamento de pesquisa", exc_info=True)
            log.log(logging.WARNING if transitoria else logging.ERROR,
                    "Pesquisa de %r falhou (pedido #%s)", titulo, job_id, exc_info=None if transitoria else exc)
            return ResultadoPesquisa(
                False,
                f"**A pesquisa não pôde ser concluída.**\nMotivo: {_md(user_msg, 400)}\n"
                f"O pedido **#{job_id}** foi preservado na fila. Você pode tentar de novo pelo mesmo botão, "
                "sem criar um registro duplicado. Nenhum catálogo foi publicado.")

        if guild_id is not None:
            await self._avisar_moderacao(
                guild_id,
                f"📥 Novo catálogo aguardando revisão: **{result['name']}** (`{result['slug']}`) — "
                f"{result['items_received']} itens, {result['trophies_received']} troféus. "
                f"Revise em `/adm` → Caçador: Auditar e Validar.")
        return ResultadoPesquisa(True, (
            "**Pesquisa concluída — catálogo em revisão**\n"
            f"Jogo identificado: **{_md(titulo)}**\n"
            f"Slug: `{result['slug']}`\n"
            f"Itens coletados: **{result['items_received']}** · Troféus: **{result['trophies_received']}**\n"
            f"Fontes encontradas: **{detalhes['research_sources']}**\n"
            f"Escopo: {_md(detalhes['coverage_notes'] or 'Cobertura ainda não determinada.', 600)}\n\n"
            "O catálogo NÃO foi publicado. Os dados começam como não verificados e precisam de revisão administrativa."))

    async def _registrar_falha_pesquisa(self, job_id: int, exc: BaseException) -> tuple[bool, str]:
        try:
            return await fila.registrar_falha(self.bot.db, job_id, exc)
        except Exception:
            log.exception("Não foi possível registrar a falha do pedido %s", job_id)
            transitoria, _, user_msg = fila.classificar_erro(exc)
            return transitoria, user_msg

    # ---------- comandos do jogador ----------
    async def abrir(self, interaction: discord.Interaction, editar: bool = False):
        view = PainelCacadorView(self, interaction.user)
        await view.montar()
        embed = await view.embed()
        if editar:
            await interaction.response.edit_message(content=None, embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        view._interaction = interaction

    @app_commands.command(name="cacador", description="Abre seu painel de troféus e colecionáveis.")
    @app_commands.guild_only()
    async def cacador(self, interaction: discord.Interaction):
        await self.abrir(interaction)

    @app_commands.command(name="jogo_buscar", description="Identifica o título oficial do jogo e pesquisa fontes para o catálogo.")
    @app_commands.guild_only()
    @app_commands.describe(nome="Pode ser abreviação, nome traduzido ou conter erros de digitação.")
    async def jogo_buscar(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.identificar_e_confirmar(interaction, nome)

    # ---------- comandos administrativos ----------
    @app_commands.command(name="catalogo_admin", description="[ADMIN] Abre a administração do Caçador de Troféus.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def catalogo_admin(self, interaction: discord.Interaction):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Você precisa da permissão Gerenciar servidor.", ephemeral=True)
        e = discord.Embed(
            title="⚙️ Administração — Caçador de Troféus",
            description=(
                "**Fluxo de trabalho**\n"
                "1. **Ver fila de jogos**: consulte solicitações e erros.\n"
                "2. Use **Pesquisar jogo** em `/nara` para identificar o título oficial e gerar o catálogo.\n"
                "3. **Auditar**: confira fontes e cobertura pelo seletor abaixo.\n"
                "4. **Validar**: confirme a revisão humana pelo seletor.\n"
                "5. **Publicar** ou **Rejeitar**: decida o destino.\n"
                "6. **Despublicar**, **Retentar** e **Histórico** também estão no seletor.\n\n"
                "Apenas membros com **Gerenciar servidor** podem administrar. A publicação nunca é automática."
            ),
            color=config.COR_OURO,
        )
        view = PainelAdminCacador(self, interaction.user.id)
        await interaction.response.send_message(embed=e, view=view, ephemeral=True)
        view._interaction = interaction

    @app_commands.command(name="catalogo_importar", description="[MOD] Importa um catálogo de jogo em JSON para revisão.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def catalogo_importar(self, interaction: discord.Interaction, arquivo: discord.Attachment):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores podem importar catálogos.", ephemeral=True)
        if not arquivo.filename.lower().endswith(".json") or arquivo.size > 8 * 1024 * 1024:
            return await interaction.response.send_message("Envie um arquivo .json de até 8 MB.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            raw = await arquivo.read()
            payload = json.loads(raw.decode("utf-8-sig"))
            slug = None
            if isinstance(payload, dict):
                try:
                    slug = svc._slug(str(payload.get("slug") or payload.get("name") or ""))
                except ValueError:
                    slug = None
            antes = await self.bot.db._one("SELECT status FROM games_catalog WHERE slug=?", (slug,)) if slug else None
            # Importação manual por um administrador é uma decisão explícita de atualizar o catálogo.
            result = await svc.importar_catalogo(self.bot.db, payload, publicar=False, actor_id=interaction.user.id,
                                                 permitir_sobrescrever_publicado=True)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            return await interaction.followup.send(f"Não foi possível importar: {_md(str(exc), 500)}", ephemeral=True)
        except Exception:
            log.exception("Falha ao importar catálogo JSON")
            return await interaction.followup.send("Falha interna ao importar o catálogo. Consulte os logs.", ephemeral=True)
        aviso = ("\n⚠️ Este catálogo estava publicado e voltou para **revisão**: valide e publique novamente."
                 if antes is not None and antes["status"] == "ready" else "")
        await interaction.followup.send(
            f"📥 **{_md(result['name'])}** importado para revisão.\n"
            f"• Itens recebidos: {result['items_received']}\n"
            f"• Troféus recebidos: {result['trophies_received']}\n"
            f"O jogo ainda não aparece para os jogadores até a publicação.{aviso}",
            ephemeral=True)

    @app_commands.command(name="catalogo_auditar", description="[MOD] Mostra cobertura, fontes e estado de validação de um catálogo.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def catalogo_auditar(self, interaction: discord.Interaction, slug: str):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores.", ephemeral=True)
        row = await self._catalogo_por_slug(slug)
        if not row:
            return await interaction.response.send_message("Slug não encontrado.", ephemeral=True)
        a = await svc.auditar_catalogo(self.bot.db, int(row["id"]))
        fontes = "\n".join(f"• [{_md(x.get('title') or x.get('url'), 80)}]({x.get('url')})" for x in a["sources"][:8]
                           if isinstance(x, dict)) or "Nenhuma fonte."
        e = discord.Embed(title=_corta(f"Auditoria — {row['name']}", 256), description=(
            f"Status: `{row['status']}`\nItens: **{a['items']}** · Troféus: **{a['trophies']}**\n"
            f"Registros com fonte: **{a['sourced']}/{a['total']}**\n"
            f"Verificados manualmente: **{a['verified']}/{a['total']}**\n"
            f"Domínios independentes: **{len(a['domains'])}** ({', '.join(a['domains'][:8]) or 'nenhum'})\n"
            f"Pronto para publicar: **{'SIM' if a['ready'] else 'NÃO'}**"
        ), color=config.COR_OURO)
        e.add_field(name="Fontes de pesquisa", value=_corta(fontes, 1024), inline=False)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="catalogo_validar", description="[MOD] Confirma revisão humana de todos os registros de um catálogo.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def catalogo_validar(self, interaction: discord.Interaction, slug: str):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores.", ephemeral=True)
        row = await self._catalogo_por_slug(slug)
        if not row:
            return await interaction.response.send_message("Slug não encontrado.", ephemeral=True)
        view = ConfirmarValidacaoCatalogo(self, int(row["id"]), row["name"], interaction.user.id)
        await interaction.response.send_message(
            f"Você confirma que revisou manualmente **todos** os itens, troféus, requisitos, localizações e fontes de **{_md(row['name'])}**?\n"
            "Use o botão para marcar os registros como verificados. Isso não publica o catálogo.",
            view=view, ephemeral=True)
        view._interaction = interaction

    @app_commands.command(name="catalogo_publicar", description="[MOD] Publica um catálogo já importado e validado.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def catalogo_publicar(self, interaction: discord.Interaction, slug: str):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores podem publicar catálogos.", ephemeral=True)
        row = await self._catalogo_por_slug(slug)
        if not row:
            return await interaction.response.send_message("Não encontrei esse catálogo. Confira o slug.", ephemeral=True)
        try:
            audit = await svc.publicar_catalogo(self.bot.db, int(row["id"]), interaction.user.id)
        except ValueError as exc:
            return await interaction.response.send_message(
                f"Publicação bloqueada. {_md(str(exc), 900)}\n"
                "Revise as fontes e os registros, use `/catalogo_validar` após a revisão humana e tente novamente.",
                ephemeral=True)
        except Exception:
            log.exception("Falha ao publicar catálogo %s", slug)
            return await interaction.response.send_message(
                "Falha interna ao publicar. O status do catálogo não foi alterado; consulte os logs.", ephemeral=True)
        await interaction.response.send_message(f"✅ **{_md(audit['name'])}** está publicado no Caçador de Troféus.", ephemeral=True)

    @app_commands.command(name="catalogo_rejeitar", description="[MOD] Rejeita um catálogo em revisão (não publica e registra o motivo).")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.describe(slug="Catálogo em revisão", motivo="Por que está sendo rejeitado (fica no histórico).")
    async def catalogo_rejeitar(self, interaction: discord.Interaction, slug: str, motivo: str = ""):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores.", ephemeral=True)
        row = await self._catalogo_por_slug(slug)
        if not row:
            return await interaction.response.send_message("Slug não encontrado.", ephemeral=True)
        try:
            r = await svc.rejeitar_catalogo(self.bot.db, int(row["id"]), interaction.user.id, motivo)
        except ValueError as exc:
            return await interaction.response.send_message(_md(str(exc), 500), ephemeral=True)
        await interaction.response.send_message(
            f"🗑️ **{_md(r['name'])}** foi rejeitado e não aparecerá para os jogadores. O motivo ficou no histórico.", ephemeral=True)

    @app_commands.command(name="catalogo_despublicar", description="[MOD] Tira um catálogo publicado do ar (volta para revisão).")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def catalogo_despublicar(self, interaction: discord.Interaction, slug: str, motivo: str = ""):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores.", ephemeral=True)
        row = await self._catalogo_por_slug(slug)
        if not row:
            return await interaction.response.send_message("Slug não encontrado.", ephemeral=True)
        try:
            r = await svc.despublicar_catalogo(self.bot.db, int(row["id"]), interaction.user.id, motivo)
        except ValueError as exc:
            return await interaction.response.send_message(_md(str(exc), 500), ephemeral=True)
        await interaction.response.send_message(
            f"⏸️ **{_md(r['name'])}** saiu do ar e voltou para revisão. O progresso dos jogadores foi preservado.", ephemeral=True)

    @app_commands.command(name="catalogo_historico", description="[MOD] Mostra o histórico de alterações dos catálogos.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.describe(slug="Opcional: limita o histórico a um catálogo.")
    async def catalogo_historico(self, interaction: discord.Interaction, slug: str = ""):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores.", ephemeral=True)
        game_id = None
        if slug.strip():
            row = await self._catalogo_por_slug(slug)
            if not row:
                return await interaction.response.send_message("Slug não encontrado.", ephemeral=True)
            game_id = int(row["id"])
        rows = await svc.listar_historico(self.bot.db, game_id, 15)
        if not rows:
            return await interaction.response.send_message("Ainda não há histórico registrado.", ephemeral=True)
        linhas = []
        for r in rows:
            detalhe = f"\n↳ {_md(r['details'], 160)}" if r["details"] else ""
            linhas.append(f"`{r['created_at']}` **{_md(r['action'])}** — {_md(r['game_name'], 60)} · <@{r['actor_id']}>{detalhe}")
        e = discord.Embed(title="🕘 Histórico do Caçador", description=_corta("\n".join(linhas), 4000), color=config.COR_OURO)
        await interaction.response.send_message(embed=e, ephemeral=True)

    @app_commands.command(name="catalogo_fila", description="[MOD] Consulta solicitações de novos jogos.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def catalogo_fila(self, interaction: discord.Interaction):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores podem consultar a fila.", ephemeral=True)
        embed = await self.embed_fila()
        if embed is None:
            return await interaction.response.send_message("A fila de solicitações está vazia.", ephemeral=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="catalogo_retentar", description="[MOD] Retoma um pedido da fila (sem duplicar registros).")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.describe(pedido="Número do pedido mostrado em /catalogo_fila.")
    async def catalogo_retentar(self, interaction: discord.Interaction, pedido: int):
        if not _eh_admin(interaction):
            return await interaction.response.send_message("Apenas administradores.", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        db = self.bot.db
        job = await fila.obter_job(db, pedido)
        if job is None:
            return await interaction.followup.send("Pedido não encontrado.", ephemeral=True)
        if job["status"] not in fila.REINICIAVEIS:
            rotulo = fila.ROTULOS.get(job["status"], job["status"])
            return await interaction.followup.send(f"O pedido #{pedido} está **{rotulo}** e não pode ser retomado.", ephemeral=True)
        candidato = None
        if job["candidate_json"]:
            try:
                candidato = json.loads(job["candidate_json"])
            except ValueError:
                candidato = None
        if isinstance(candidato, dict) and candidato.get("canonical_title"):
            r = await self.pesquisar_e_importar(
                candidato, query=job["game_name"], identity_sources=[], solicitante_id=int(job["requested_by"]),
                job_id=int(job["id"]), admin=True, actor_id=interaction.user.id,
                guild_id=interaction.guild_id)
            return await interaction.followup.send(r.mensagem, ephemeral=True)
        # Pedido ainda sem título confirmado: o administrador confirma a identidade.
        try:
            result = catalogo_ia.identificar_local(job["game_name"]) or await catalogo_ia.identificar_jogo(job["game_name"])
        except Exception as exc:
            _, user_msg = await self._registrar_falha_pesquisa(int(job["id"]), exc)
            return await interaction.followup.send(
                f"A identificação ainda não pôde ser concluída: {_md(user_msg, 400)}\nO pedido #{pedido} continua na fila.", ephemeral=True)
        candidatos = result.get("candidates", [])
        if not candidatos:
            return await interaction.followup.send("Nenhuma correspondência confiável. O pedido continua na fila.", ephemeral=True)
        view = ConfirmacaoJogoView(self, interaction.user.id, job["game_name"], candidatos,
                                   result.get("sources", []), result.get("notes", ""), job_id=int(job["id"]))
        await interaction.followup.send(f"Retomando o pedido **#{pedido}**. Confirme o título:", embed=view.embed(),
                                        view=view, ephemeral=True)
        view._interaction = interaction

    # Autocomplete de slugs nos comandos administrativos.
    @catalogo_auditar.autocomplete("slug")
    async def _ac_auditar(self, interaction: discord.Interaction, current: str):
        return await self._autocomplete_slug(interaction, current)

    @catalogo_validar.autocomplete("slug")
    async def _ac_validar(self, interaction: discord.Interaction, current: str):
        return await self._autocomplete_slug(interaction, current)

    @catalogo_publicar.autocomplete("slug")
    async def _ac_publicar(self, interaction: discord.Interaction, current: str):
        return await self._autocomplete_slug(interaction, current)

    @catalogo_rejeitar.autocomplete("slug")
    async def _ac_rejeitar(self, interaction: discord.Interaction, current: str):
        return await self._autocomplete_slug(interaction, current)

    @catalogo_despublicar.autocomplete("slug")
    async def _ac_despublicar(self, interaction: discord.Interaction, current: str):
        return await self._autocomplete_slug(interaction, current)

    @catalogo_historico.autocomplete("slug")
    async def _ac_historico(self, interaction: discord.Interaction, current: str):
        return await self._autocomplete_slug(interaction, current)

    async def cog_load(self):
        # Ao iniciar, nenhuma pesquisa do processo anterior continua rodando: todas as
        # 'researching' são órfãs. Ficam como 'interrupted' e podem ser retomadas sem duplicar.
        orfas = await fila.reconciliar_orfaos(self.bot.db, 0)
        if orfas:
            log.warning("%d pesquisa(s) do Caçador estavam interrompidas e foram marcadas para retomada.", orfas)
        for problema in diagnostico_configuracao():
            log.warning("Caçador de Troféus — configuração: %s", problema)
        log.info("Caçador de Troféus carregado.")


async def setup(bot):
    await bot.add_cog(CacadorTrofeus(bot))
