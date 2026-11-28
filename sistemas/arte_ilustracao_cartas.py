"""Ponto de entrada das ilustrações por código: cada carta vira uma cena própria.

``pintar_ilustracao(card, aw, ah, seed)`` escolhe cenário, figura, armadura, arma e brilhos a
partir do ID (receita exata para as cartas nomeadas) ou, nas demais (patentes, cartas geradas,
transmutações), do nome/lore/facção/fileira. Determinístico: a mesma carta gera a mesma arte.
"""
from __future__ import annotations

import colorsys
import hashlib
import math
import random
import unicodedata
from typing import Any

from PIL import Image

from . import arte_ilustracao_cenarios as cen
from . import arte_ilustracao_figuras as fig
from .arte_ilustracao_base import Tela, brilho, finalizar, neblina, particulas

# --- paletas de armadura/pano por facção -------------------------------------------------------
PALETAS = {
    "Ordem Áurea": dict(arm=((214, 170, 82), (60, 42, 16)), pano=((176, 40, 36), (60, 12, 12)), amb="aurea", cen="planicie"),
    "Véu Carmesim": dict(arm=((120, 52, 60), (26, 8, 12)), pano=((150, 28, 44), (40, 6, 14)), amb="carmesim", cen="mohgwyn"),
    "Lua Negra": dict(arm=((120, 130, 200), (22, 24, 56)), pano=((70, 80, 170), (16, 18, 52)), amb="lua", cen="academia"),
    "Os Esquecidos": dict(arm=((170, 164, 146), (44, 42, 36)), pano=((140, 134, 116), (40, 38, 32)), amb="esquecidos", cen="capela"),
}


def _n(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s).casefold()) if unicodedata.category(c) != "Mn")


# --- receitas exatas por ID (personagens e itens nomeados) ----------------------------------------
# chaves: cen, fig (humanoide|gurranq|dragao|besta|mae|gemeas|gigante|cavalo), amb, e opções da figura
R: dict[str, dict] = {
    "chefe_guardiao_cinzas": dict(cen="planicie", fig="cavalo", helm="grande", crista="pluma", arma="lanca", corpo="placas"),
    "chefe_dama_vazio": dict(cen="academia", amb="lua", helm="bruxa", corpo="robe", arma="cajado", pele=(150, 190, 220), cabelo=(40, 70, 120), cabelo_longo=True, extras=("lua",), orbe=(150, 190, 255), arm=((120, 150, 220), (20, 26, 70)), pano=((60, 90, 190), (12, 18, 60)), chapeu=(40, 60, 140), olhos_luz=(150, 200, 255)),
    "chefe_cervo_sombrio": dict(cen="mohgwyn", helm="grande", crista="chifres", arma="espada_grande", corpo="placas", arm=((96, 48, 52), (20, 8, 10)), brilho=(255, 80, 70)),
    "chefe_rei_afogado": dict(cen="planicie", helm="aberto", corpo="nu", arma="machado", cabelo=(210, 190, 140), cabelo_longo=True, pele=(176, 128, 98), pano=((120, 90, 50), (40, 28, 14)), extras=("runas",), brilho=(255, 214, 125)),
    "chefe_oraculo_ruina": dict(cen="leyndell", fig="gurranq", amb="aurea"),
    "chefe_cacador_sem_rosto": dict(cen="mohgwyn", helm="capuz", corpo="couro", arma="adagas", mascara=True, arm=((70, 50, 56), (14, 8, 12)), pano=((60, 20, 28), (14, 4, 8)), capuz=(36, 20, 26), brilho=(255, 90, 80)),
    "chefe_vigia_cinzento": dict(cen="leyndell", helm="grande", corpo="placas", arma="lanca", escudo="redondo"),
    "chefe_aparicao_veio": dict(cen="mohgwyn", helm="capuz", corpo="couro", arma="katana", arm=((50, 40, 50), (10, 6, 10)), pano=((34, 20, 30), (8, 4, 8)), capuz=(24, 16, 22), brilho=(255, 70, 70), brilho_lamina=(255, 60, 60)),
    "chefe_malenia_lamina_miquella": dict(cen="caelid", amb="podridao", helm="grande", crista="asas_elmo", corpo="placas", arma="katana", cabelo=(190, 50, 30), arm=((200, 170, 120), (70, 48, 24)), pano=((150, 120, 70), (60, 40, 20)), brilho=(255, 140, 70), brilho_lamina=(255, 120, 60), extras=("asas_rubras",)),
    "chefe_radahn_flagelo_estrelas": dict(cen="caelid", fig="cavalo", amb="podridao", helm="grande", crista="pluma", pluma=(220, 40, 30), arma="duas_espadas", corpo="placas", arm=((150, 110, 80), (40, 24, 16)), brilho=(255, 150, 60), brilho_lamina=(255, 180, 80), estrelas=True),
    "chefe_maliketh_morte_destinada": dict(cen="farum", amb="trevas", helm="chifres", corpo="placas", arma="katana", arm=((46, 40, 52), (8, 6, 12)), pano=((30, 20, 34), (6, 4, 10)), brilho=(255, 200, 90), brilho_lamina=(255, 200, 90), extras=("asas_negras",)),
    "chefe_messmer_impalador": dict(cen="volcano", amb="chama", helm="grande", crista="cobra", corpo="placas", arma="lanca", arm=((150, 70, 40), (36, 14, 8)), pano=((180, 60, 20), (50, 14, 6)), brilho=(255, 150, 60), extras=("chamas",)),
    "chefe_placidusax_lorde_dragao": dict(cen="farum", fig="dragao", amb="tempestade"),
    "arma_lamina_peregrino": dict(cen="volcano", helm="aberto", corpo="couro", arma="katana", cabelo=(60, 36, 30), arm=((110, 50, 56), (24, 8, 12))),
    "arma_martelo_fornalha": dict(cen="volcano", helm="aberto", corpo="nu", arma="martelo", careca=True, pele=(150, 104, 80), pano=((90, 60, 40), (26, 16, 10))),
    "arma_cajado_marulho": dict(cen="academia", helm="cone", corpo="robe", arma="cajado", chapeu=(50, 60, 140), orbe=(150, 190, 255)),
    "arma_duas_luas": dict(cen="academia", helm="grande", corpo="placas", arma="espada_escudo", extras=("lua",), brilho_lamina=(160, 190, 255)),
    "arma_grande_sino": dict(cen="leyndell", helm="grande", corpo="placas", arma="alabarda", escala=1.08, crista="chifres"),
    "arma_agulha_astro": dict(cen="nokron", helm="capuz", corpo="robe", arma="cajado", orbe=(190, 210, 255), capuz=(40, 50, 120)),
    "arma_lanca_fornalha": dict(cen="planicie", helm="grande", corpo="placas", arma="lanca"),
    "arma_arco_peregrino": dict(cen="volcano", helm="capuz", corpo="couro", arma="arco", capuz=(70, 26, 30), arm=((100, 50, 50), (22, 8, 10))),
    "magia_brasa_errante": dict(cen="montanha", helm="aberto", corpo="robe", arma="cajado", careca=True, orbe=(255, 150, 60), extras=("chamas",), brilho=(255, 140, 50)),
    "magia_selo_vigilia": dict(cen="leyndell", helm="capuz", corpo="robe", arma="livro", mascara=True, capuz=(180, 150, 90)),
    "magia_trovao_oco": dict(cen="farum", amb="tempestade", helm="grande", crista="chifres", corpo="placas", arma="lanca", brilho=(255, 232, 150), brilho_lamina=(255, 232, 150)),
    "magia_nevoa_antiga": dict(cen="academia", helm="cone", corpo="robe", arma="cajado", orbe=(190, 170, 255), extras=("runas",)),
    "magia_sol_negro": dict(cen="mohgwyn", helm="capuz", corpo="robe", arma="cajado", orbe=(40, 10, 20), capuz=(60, 16, 24), brilho=(255, 80, 70), extras=("runas",)),
    "magia_fagulha": dict(cen="academia", helm="cone", corpo="robe", arma="cajado", orbe=(255, 200, 120), chapeu=(60, 60, 150)),
    "magia_orbe_eco": dict(cen="academia", helm="aberto", corpo="robe", arma="livro", cabelo=(80, 80, 100)),
    "magia_chama_fria": dict(cen="montanha", amb="geada", helm="bruxa", corpo="robe", arma="cajado", orbe=(190, 240, 255), pele=(200, 220, 235), cabelo=(220, 240, 255), cabelo_longo=True),
    "covenant_lobos_cinza": dict(cen="caelid", helm="grande", corpo="placas", arma="estandarte", crista="pluma", pluma=(190, 40, 30)),
    "covenant_lua_velada": dict(cen="academia", helm="aberto", corpo="robe", arma="espada_grande", extras=("lua",), cabelo=(40, 70, 130), cabelo_longo=True, pele=(160, 190, 220)),
    "covenant_sentinelas": dict(cen="nokron", helm="grande", corpo="placas", arma="lanca", escudo="redondo"),
    "covenant_coroa_abismo": dict(cen="mohgwyn", helm="grande", crista="coroa", corpo="placas", arma="lanca", brilho=(255, 90, 80)),
    "covenant_ultimos": dict(cen="mohgwyn", helm="grande", corpo="placas", arma="espada_escudo", brilho=(255, 90, 80)),
    "covenant_filhos_brasa": dict(cen="montanha", helm="aberto", corpo="nu", arma="martelo", careca=True, pele=(170, 120, 90), extras=("chamas",), brilho=(255, 150, 60)),
    "covenant_peregrinos_nevoa": dict(cen="nokron", helm="capuz", corpo="couro", arma="cajado", orbe=(160, 190, 255)),
    "covenant_irmandade_ferro": dict(cen="planicie", helm="grande", corpo="placas", arma="espada_escudo", escudo="redondo"),
    "gwent_unidade_baluarte": dict(cen="leyndell", helm="grande", corpo="placas", arma="espada_escudo", escudo="alto", escala=1.04),
    "gwent_unidade_lamina_sem_juramento": dict(cen="nokron", helm="capuz", corpo="couro", arma="katana", capuz=(50, 34, 40)),
    "gwent_unidade_portaestandarte": dict(cen="leyndell", helm="grande", corpo="placas", arma="estandarte"),
    "gwent_unidade_oraculo_clima": dict(cen="academia", helm="aberto", corpo="robe", arma="cajado", orbe=(190, 210, 255), cabelo=(200, 200, 230), cabelo_longo=True),
    "gwent_unidade_eco": dict(cen="academia", helm="aberto", corpo="robe", arma="livro", cabelo=(70, 70, 110)),
    "gwent_unidade_cavaleira": dict(cen="academia", helm="aberto", corpo="placas", arma="espada_escudo", cabelo=(70, 70, 130), cabelo_longo=True, brilho_lamina=(170, 190, 255)),
    "gwent_unidade_gigante": dict(cen="montanha", fig="gigante", helm="aberto", corpo="nu", arma="martelo", amb="chama", cabelo=(210, 90, 30), pele=(120, 84, 70), extras=("chamas",), brilho=(255, 150, 60)),
    "gwent_unidade_cartografa": dict(cen="nokron", helm="aberto", corpo="couro", arma="livro", cabelo=(60, 60, 110)),
    "gwent_unidade_invocador": dict(cen="mohgwyn", helm="capuz", corpo="robe", arma="cajado", orbe=(255, 70, 60), capuz=(50, 14, 20), extras=("runas",)),
    "gwent_unidade_mestre_forja": dict(cen="volcano", helm="aberto", corpo="nu", arma="martelo", careca=True, escala=1.08, pele=(140, 96, 74)),
    "gwent_unidade_dupla_veu": dict(cen="nokron", fig="gemeas", helm="capuz", corpo="couro", arma="adagas", capuz=(40, 50, 110)),
    "gwent_unidade_circulo": dict(cen="academia", helm="cone", corpo="robe", arma="livro", extras=("runas",)),
    "gwent_unidade_sentinela_rubra": dict(cen="caelid", helm="grande", corpo="placas", arma="espada_escudo", crista="pluma", pluma=(200, 40, 30)),
    "gwent_unidade_veterano_cercos": dict(cen="farum", helm="grande", corpo="placas", arma="espada_grande", crista="chifres", brilho_lamina=(255, 232, 150)),
    "gwent_unidade_herdeiro_portao": dict(cen="leyndell", helm="aberto", corpo="placas", arma="espada_grande", cabelo=(230, 200, 120), cabelo_longo=True, arm=((200, 160, 70), (50, 34, 10)), pano=((120, 24, 24), (40, 8, 8)), extras=("aureola",), brilho_lamina=(255, 214, 125)),
    "gwent_unidade_carniceiro_forja": dict(cen="volcano", helm="grande", corpo="placas", arma="machado", crista="chifres", escala=1.06),
    "gwent_unidade_intendente": dict(cen="planicie", helm="capuz", corpo="couro", arma="cajado", orbe=(255, 214, 125), capuz=(110, 90, 50)),
    "gwent_unidade_cacadora_fantasma": dict(cen="mohgwyn", helm="capuz", corpo="couro", arma="adagas", mascara=True),
    "gwent_unidade_cantora_lamentos": dict(cen="mohgwyn", helm="aberto", corpo="robe", arma="livro", cabelo=(40, 30, 40), cabelo_longo=True, pele=(190, 160, 150), olhos_luz=(255, 90, 90)),
    "gwent_unidade_senhor_cacada": dict(cen="academia", helm="lobo", corpo="placas", arma="espada_grande", escala=1.06, brilho_lamina=(170, 190, 255)),
    "gwent_unidade_saqueadora_veu": dict(cen="nokron", helm="capuz", corpo="couro", arma="arco"),
    "gwent_unidade_contrabandista": dict(cen="catacumba", helm="capuz", corpo="couro", arma="adagas", capuz=(80, 30, 30)),
    "gwent_unidade_guardiao_runas": dict(cen="leyndell", helm="grande", corpo="placas", arma="alabarda", extras=("runas",)),
    "gwent_unidade_necromante": dict(cen="nokron", helm="capuz", corpo="robe", arma="cajado", orbe=(150, 200, 255), capuz=(30, 40, 90), extras=("runas",)),
    "gwent_unidade_detonador": dict(cen="caelid", amb="podridao", helm="grande", corpo="placas", arma="machado", brilho=(255, 220, 80), extras=("chamas",)),
    "gwent_unidade_devorador_mana": dict(cen="mohgwyn", helm="grande", corpo="placas", arma="lanca", crista="chifres", brilho=(255, 80, 70)),
    "gwent_unidade_bibliotecaria": dict(cen="academia", helm="aberto", corpo="robe", arma="livro", cabelo=(90, 70, 60)),
    "gwent_mitica_coroa": dict(cen="leyndell", helm="grande", corpo="placas", arma="espada_escudo", crista="coroa", escala=1.06, extras=("aureola",), arm=((255, 226, 150), (120, 84, 26))),
    "gwent_singular_primeiro": dict(cen="mohgwyn", special="runa", cor=(236, 70, 80)),
    "gwent_singular_intocavel": dict(cen="mohgwyn", special="lamina", cor=(220, 70, 76), lamina=(40, 30, 40), luz=(255, 150, 140)),
    "gwent_singular_nivel1": dict(cen="leyndell", special="lamina", cor=(255, 214, 125), lamina=(210, 170, 80), luz=(255, 240, 190)),
    "gwent_singular_cacador_chefes": dict(cen="academia", special="runa", cor=(190, 200, 255), forma_g="coroa"),
    "luterano_cruzado": dict(cen="capela", helm="grande", corpo="placas", arma="espada_grande", arm=((176, 170, 150), (46, 44, 38))),
    "luterano_missionario": dict(cen="capela", helm="capuz", corpo="robe", arma="cajado", orbe=(235, 228, 196), capuz=(120, 114, 98)),
    "luterano_bispo": dict(cen="capela", helm="mitra", corpo="robe", arma="cajado", orbe=(250, 240, 200), extras=("aureola",)),
    "luterano_anjo": dict(cen="capela", helm="aberto", corpo="robe", arma="espada_grande", extras=("asas", "aureola"), pele=(226, 220, 205), cabelo=(240, 234, 220), cabelo_longo=True),
    "luterano_papa": dict(cen="capela", helm="mitra", corpo="robe", arma="cajado", escala=1.04, extras=("aureola", "asas"), pano=((230, 224, 200), (96, 90, 72))),
    "luterano_sacerdote": dict(cen="capela", helm="capuz", corpo="robe", arma="livro", capuz=(130, 124, 108)),
    "luterano_irmao": dict(cen="capela", helm="aberto", corpo="robe", arma="cajado", careca=True, orbe=(235, 228, 196)),
    "luterano_diacon": dict(cen="capela", helm="aberto", corpo="robe", arma="livro", cabelo=(100, 96, 88)),
    "luterano_apostolo": dict(cen="leyndell", helm="capuz", corpo="robe", arma="cajado", orbe=(255, 224, 150), capuz=(150, 124, 70)),
    "luterano_profeta": dict(cen="leyndell", helm="aberto", corpo="robe", arma="livro", extras=("aureola",), cabelo=(220, 214, 200), cabelo_longo=True),
    "luterano_pastor": dict(cen="mohgwyn", helm="capuz", corpo="robe", arma="cajado", orbe=(255, 90, 80), capuz=(90, 24, 30)),
    "luterano_mistico": dict(cen="nokron", helm="capuz", corpo="robe", arma="livro", capuz=(50, 60, 140)),
    "luterano_vigia": dict(cen="capela", helm="capuz", corpo="couro", arma="lanca", capuz=(70, 24, 30)),
    "luterano_anjo2": dict(cen="nokron", helm="aberto", corpo="robe", arma="espada_grande", extras=("asas", "aureola"), cabelo=(200, 210, 255), cabelo_longo=True, pele=(210, 214, 235)),
    "primordial_origem": dict(cen="leyndell", fig="besta", amb="aurea"),
    "primordial_trono": dict(cen="leyndell", helm="coroa", corpo="robe", arma="cajado", cabelo=(240, 210, 130), cabelo_longo=True, pele=(226, 196, 160), extras=("aureola", "runas"), pano=((70, 20, 40), (20, 6, 14)), orbe=(255, 224, 150), escala=1.06),
    "primordial_tempestade": dict(cen="farum", fig="dragao", amb="tempestade"),
    "primordial_abismo": dict(cen="mohgwyn", fig="mae", amb="carmesim"),
    "primordial_eternidade": dict(cen="farum", amb="trevas", helm="chifres", corpo="placas", arma="katana", escala=1.06, arm=((52, 46, 58), (8, 6, 12)), brilho_lamina=(255, 200, 90), brilho=(255, 200, 90), extras=("asas_negras",)),
    "gwent_v75_ordem_veterano_juramento": dict(cen="leyndell", helm="grande", corpo="placas", arma="espada_escudo", escudo="alto"),
    "gwent_v75_ordem_guardiao_crisol": dict(cen="leyndell", helm="grande", corpo="placas", arma="martelo"),
    "gwent_v75_ordem_confessora_graca": dict(cen="leyndell", helm="capuz", corpo="robe", arma="livro", mascara=True, capuz=(190, 160, 100)),
    "gwent_v75_ordem_arauto_estandarte": dict(cen="leyndell", helm="grande", corpo="placas", arma="estandarte", crista="pluma"),
    "gwent_v75_veu_acolito_sangue": dict(cen="mohgwyn", helm="capuz", corpo="robe", arma="cajado", orbe=(255, 80, 70), capuz=(90, 20, 30)),
    "gwent_v75_veu_devota_hemorragia": dict(cen="mohgwyn", helm="aberto", corpo="robe", arma="livro", cabelo=(60, 20, 26), cabelo_longo=True, olhos_luz=(255, 80, 80)),
    "gwent_v75_veu_carrasco_preco": dict(cen="mohgwyn", helm="grande", corpo="placas", arma="machado", crista="chifres", escala=1.06),
    "gwent_v75_veu_cacador_sangue": dict(cen="catacumba", helm="capuz", corpo="couro", arma="arco", capuz=(80, 20, 28)),
    "gwent_v75_lua_oraculo_geada": dict(cen="montanha", amb="geada", helm="bruxa", corpo="robe", arma="cajado", orbe=(190, 240, 255)),
    "gwent_v75_lua_cartografo_lunar": dict(cen="nokron", helm="capuz", corpo="couro", arma="livro", capuz=(46, 56, 130)),
    "gwent_v75_lua_graviturgista": dict(cen="nokron", helm="cone", corpo="robe", arma="cajado", orbe=(190, 170, 255), extras=("runas",)),
    "gwent_v75_lua_guardia": dict(cen="academia", helm="grande", corpo="placas", arma="espada_escudo", extras=("lua",)),
}

# --- cenas completas das cartas especiais ----------------------------------------------------------
E: dict[str, tuple[str, dict]] = {
    "gwent_especial_tempestade": ("tempestade", dict(amb="tempestade")),
    "gwent_especial_nevoa": ("miasma", {}),
    "gwent_especial_geada": ("geada", dict(amb="geada")),
    "gwent_especial_chuva": ("sangue", dict(amb="carmesim")),
    "gwent_especial_chifre": ("rugido", dict(amb="aurea")),
    "gwent_especial_medico": ("lagrima", dict(amb="aurea")),
    "gwent_especial_queima": ("chama", dict(variante="negra", amb="trevas")),
    "gwent_especial_purificar": ("sigilo", dict(cor=(176, 200, 255), n=34, pontas=8, achatar=.8)),
    "gwent_especial_execucao": ("lamina", dict(cor=(255, 200, 90), lamina=(26, 22, 30), luz=(255, 214, 125))),
    "gwent_especial_vinculo": ("vinculo", dict(amb="aurea")),
    "gwent_especial_batedor": ("passo", dict(amb="carmesim")),
    "gwent_especial_muralha": ("muralha", dict(amb="aurea")),
    "elden_especial_sangramento": ("ritual", dict(amb="carmesim")),
    "elden_especial_geada": ("lua", dict(amb="lua")),
    "elden_especial_podrida": ("flor", dict(amb="podridao")),
    "elden_especial_loucura": ("chama", dict(variante="frenetica", amb="chama")),
    "elden_especial_chama": ("chama", dict(variante="gigante", amb="chama")),
    "elden_especial_invocacao": ("lobo", dict(amb="lua", cor=(200, 206, 230))),
    "reliquia_grande_runa_godrick": ("runa", dict(cor=(240, 190, 90), amb="aurea")),
    "reliquia_runa_nao_nascidos": ("runa", dict(cor=(120, 190, 255), amb="lua")),
    "reliquia_runa_morte": ("runa", dict(cor=(255, 214, 125), amb="trevas", forma_g="losango")),
    "reliquia_noite_chama": ("lamina", dict(cor=(120, 150, 255), lamina=(70, 80, 130), luz=(190, 210, 255), dupla=(255, 130, 40))),
    "reliquia_lamina_negra": ("lamina", dict(cor=(255, 120, 60), lamina=(14, 10, 18), luz=(255, 170, 90), curva=34)),
    "reliquia_algemas_margit": ("correntes", dict(amb="aurea")),
    "gwent_especial_egide": ("arvore", dict(amb="aurea")),
    "gwent_especial_requiem": ("espiritos", dict(amb="lua")),
    "gwent_especial_passo": ("lobo", dict(amb="carmesim", cor=(255, 150, 140))),
}

# --- inferência por palavras-chave (patentes, cartas geradas, transmutações) ----------------------
_ARMAS = (("arco", "arco"), ("batedor", "arco"), ("cajado", "cajado"), ("feiticeiro", "cajado"), ("mago", "cajado"), ("erudito", "livro"),
          ("aprendiz", "livro"), ("novato", "livro"), ("confessor", "livro"), ("bibliotec", "livro"), ("sacerdote", "livro"), ("profeta", "cajado"),
          ("estandarte", "estandarte"), ("arauto", "estandarte"), ("assassin", "adagas"), ("cacador", "adagas"), ("ladin", "adagas"),
          ("duelista", "katana"), ("martelo", "martelo"), ("ferreiro", "martelo"), ("machado", "machado"), ("carrasco", "machado"),
          ("lanceiro", "lanca"), ("guarda", "lanca"), ("sentinela", "lanca"), ("escudeiro", "espada_escudo"), ("cavaleiro", "espada_escudo"),
          ("lorde", "espada_grande"), ("executor", "espada_grande"), ("guerreiro", "espada_grande"), ("veterano", "espada_escudo"))
_CORPOS = (("feiticeir", "robe"), ("mago", "robe"), ("mestre", "robe"), ("sacerdote", "robe"), ("profeta", "robe"), ("aprendiz", "robe"),
           ("novato", "robe"), ("erudit", "robe"), ("astrolog", "robe"), ("assassin", "couro"), ("cacador", "couro"), ("ladin", "couro"),
           ("batedor", "couro"), ("acolit", "robe"), ("sacerdot", "robe"), ("monge", "robe"))


def _inferir(card: dict[str, Any], palet: dict, row: str, rarity: str) -> dict:
    nome = _n(f"{card.get('nome', '')} {card.get('descricao', '')}")
    nome_curto = _n(card.get("nome", ""))
    o: dict[str, Any] = {}
    for k, v in _CORPOS:
        if k in nome_curto:
            o["corpo"] = v
            break
    for k, v in _ARMAS:
        if k in nome_curto:
            o["arma"] = v
            break
    o.setdefault("corpo", "robe" if row == "ranged" and "arma" not in o else "placas")
    if "arma" not in o:
        o["arma"] = {"melee": "espada_escudo", "ranged": "arco", "siege": "cajado"}.get(row, "espada_escudo")
    if o["corpo"] == "robe" and o["arma"] in ("espada_escudo", "espada_grande", "lanca", "arco"):
        o["arma"] = "cajado" if row != "ranged" else "livro"
    o["helm"] = {"robe": "cone" if "lua" in _n(card.get("faccao", "")) else "capuz", "couro": "capuz", "placas": "grande"}[o["corpo"]]
    if any(k in nome_curto for k in ("sacerdote", "profeta", "confessor", "bibliotec")):
        o["helm"] = "aberto"
    if "mascar" in nome or "assassin" in nome_curto:
        o["mascara"] = True
    cenarios = (("leyndell", "leyndell"), ("mohgwyn", "mohgwyn"), ("volcano", "volcano"), ("raya", "academia"), ("liurnia", "academia"), ("academia", "academia"),
                ("nokron", "nokron"), ("cidade eterna", "nokron"), ("sellia", "nokron"), ("caelid", "caelid"), ("radahn", "caelid"), ("farum", "farum"),
                ("gigante", "montanha"), ("pico", "montanha"), ("catacumba", "catacumba"), ("capela", "capela"), ("arvore aurea", "planicie"))
    for k, v in cenarios:
        if k in nome:
            o["cen"] = v
            break
    if rarity in ("Lendária", "Mítica", "Primordial", "Singular"):
        o["extras"] = ("aureola",) if "ordem" in _n(card.get("faccao", "")) else ("runas",)
        o["escala"] = 1.05
    return o


# --- entrada ----------------------------------------------------------------------------------
def _spec(card: dict[str, Any], faccao: str, row: str, rarity: str) -> dict:
    cid = str(card.get("id", ""))
    p = PALETAS.get(faccao, PALETAS["Ordem Áurea"])
    base = dict(arm=p["arm"], pano=p["pano"], amb=p["amb"], cen=p["cen"], helm="grande", corpo="placas", arma="espada_grande", escala=1.1)
    if cid in R:
        spec = {**base, **R[cid]}
    else:
        spec = {**base, **_inferir(card, p, row, rarity)}
    # armadura derivada se a receita trouxe só a cor do capuz/etc. continua com a paleta da facção
    return spec


def _hsv(c, dh=0.0, ds=1.0, dv=1.0):
    h, sa, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
    r, g, b = colorsys.hsv_to_rgb((h + dh) % 1.0, min(1, sa * ds), min(1, v * dv))
    return (int(r * 255), int(g * 255), int(b * 255))


def _hash_carta(card: dict[str, Any]) -> int:
    base = f"{card.get('id', '')}|{card.get('nome', '')}"
    return int.from_bytes(hashlib.sha256(base.encode("utf-8")).digest()[:8], "big")


_PELES = ((226, 188, 160), (196, 150, 120), (160, 112, 84), (120, 82, 62), (232, 214, 196), (150, 170, 190))
_CABELOS = ((40, 30, 26), (96, 64, 36), (200, 170, 110), (180, 60, 40), (210, 210, 220), (60, 70, 120), (30, 24, 34))


def _selo_unico(t: Tela, h: int, cor) -> None:
    """Selo heráldico exclusivo da carta (formato, anéis e posição vêm do hash do ID)."""
    r = random.Random(h ^ 0x5E10)
    cx, cy = 192 + r.uniform(-40, 40), r.uniform(46, 96)
    lados, raio = r.randint(3, 9), r.uniform(14, 24)
    rot = r.uniform(0, math.tau)
    c = t.camada(1)
    pts = [(cx + math.cos(rot + i * math.tau / lados) * raio, cy + math.sin(rot + i * math.tau / lados) * raio) for i in range(lados)]
    c.d.polygon(pts, outline=(*cor, 150), width=1.1)
    for k in range(r.randint(1, 3)):
        rr = raio * (.35 + k * .25)
        c.d.circulo(cx, cy, rr, outline=(*cor, 110), width=.8)
    for i in range(lados):
        a = rot + i * math.tau / lados
        c.d.line([(cx, cy), (cx + math.cos(a) * raio * r.uniform(.5, 1.0), cy + math.sin(a) * raio * r.uniform(.5, 1.0))], fill=(*cor, 120), width=.8)
    c.aplicar(aditivo=True)


def pintar_ilustracao(card: dict[str, Any], aw: int, ah: int, seed: int, faccao: str, row: str,
                      rarity: str, categoria: str) -> Image.Image:
    """Pinta a ilustração completa da carta (aw x ah)."""
    cid = str(card.get("id", ""))
    h = _hash_carta(card)
    seed = h  # a arte depende só do ID/nome: cada carta tem a sua, sempre a mesma
    rng = random.Random(seed)
    S = 2
    t = Tela(384, 430, S=S, seed=seed)
    p = PALETAS.get(faccao, PALETAS["Ordem Áurea"])

    if categoria == "Especial" or (cid in R and R[cid].get("special")):
        if cid in E:
            nome, ops = E[cid]
        elif cid in R and R[cid].get("special"):
            nome, ops = R[cid]["special"], {k: v for k, v in R[cid].items() if k not in ("special", "cen")}
        else:
            nome, ops = {"Ordem Áurea": ("muralha", {}), "Véu Carmesim": ("ritual", {}), "Lua Negra": ("sigilo", dict(cor=(176, 190, 255))),
                         "Os Esquecidos": ("espiritos", {})}.get(faccao, ("sigilo", {}))
        amb = cen_amb(ops.pop("amb", p["amb"]))
        cen.ESPECIAIS[nome](t, amb, rng, **ops)
        _selo_unico(t, h, amb["luz"])
    else:
        spec = _spec(card, faccao, row, rarity)
        A = cen.AMBIENTES[spec["amb"]]
        cen.CENARIOS[spec["cen"]](t, A, rng)
        _selo_unico(t, h, A["luz"])
        tipo = spec.get("fig", "humanoide")
        o = dict(spec)
        vr = random.Random(h ^ 0xA11CE)
        o["lado"] = vr.choice((-1, 1))
        o["vento"] = vr.uniform(-22, 22)
        o["passo"] = vr.uniform(7, 17)
        o["x"] = 192 + vr.uniform(-22, 22)
        o["escala"] = o.get("escala", 1.1) * vr.uniform(.94, 1.06)
        dh = vr.uniform(-.035, .035)
        o["arm"] = (_hsv(o["arm"][0], dh, vr.uniform(.85, 1.15), vr.uniform(.9, 1.08)), _hsv(o["arm"][1], dh, 1, vr.uniform(.9, 1.15)))
        o["pano"] = (_hsv(o["pano"][0], dh * 2, vr.uniform(.85, 1.15), vr.uniform(.9, 1.1)), _hsv(o["pano"][1], dh * 2, 1, vr.uniform(.9, 1.15)))
        if "pele" not in R.get(cid, {}):
            o["pele"] = vr.choice(_PELES)
        if "cabelo" not in R.get(cid, {}):
            o["cabelo"] = vr.choice(_CABELOS)
            o["cabelo_longo"] = o.get("cabelo_longo", vr.random() < .4)
        if tipo == "humanoide":
            fig.humanoide(t, A, o, rng)
        elif tipo == "cavalo":
            hf = fig.cavalo(t, A, {"pelo": ((74, 72, 82), (14, 14, 20)), "escala": .98, "chao": 344, "x": 205, "brilho": spec.get("brilho", A["acento"])}, rng)
            fig.humanoide(t, A, {**o, "montado": True, "x": 196, "chao": 309, "escala": .8, "corpo": o.get("corpo", "placas"), "manto": True}, rng)
        elif tipo == "gurranq":
            fig.gurranq(t, A, {"escala": .9, "chao": 350}, rng)
        elif tipo == "dragao":
            fig.dragao(t, A, {"escala": .95, "chao": 350, "brilho": A["luz"]}, rng)
        elif tipo == "besta":
            fig.besta_pristina(t, A, {"escala": 1.0, "chao": 350}, rng)
        elif tipo == "mae":
            fig.mae_sem_forma(t, A, {"escala": 1.0, "chao": 356}, rng)
        elif tipo == "gemeas":
            fig.gemeas(t, A, o, rng)
        elif tipo == "gigante":
            fig.gigante(t, A, o, rng)
        # neblina frontal e brasas por cima da figura para integrá-la ao cenário
        neblina(t, .74, .9, A["nevoa"], .42, n=14, sal=77)
        brilho(t, 192, 330, 130, A["luz"], k=.22, ry=34)
        particulas(t, 40, A["luz"], (20, 80, 364, 380), (.5, 1.6), .9, sal=99, deriva=.3)
    img = finalizar(t)
    # deslocamento sutil de matiz/saturação exclusivo da carta
    vr2 = random.Random(h ^ 0xC0105)
    hsv = img.convert("RGB").convert("HSV")
    dh = int(vr2.uniform(-9, 9))
    hh, ss, vv = hsv.split()
    hh = hh.point(lambda x: (x + dh) % 256)
    ss = ss.point(lambda x: min(255, int(x * vr2.uniform(.92, 1.12))))
    img = Image.merge("HSV", (hh, ss, vv)).convert("RGBA")
    if (aw, ah) != img.size:
        img = img.resize((aw, ah), Image.Resampling.LANCZOS)
    return img


def cen_amb(nome: str) -> dict:
    return cen.AMBIENTES[nome]
