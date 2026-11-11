"""Pesquisa com dois projetos Gemini e geração de rascunhos em revisão.

O projeto Gemini principal é tentado primeiro; outro projeto Gemini assume
quando a quota/serviço principal falha. Fontes são validadas e nada é publicado
automaticamente.
"""
from __future__ import annotations

import difflib
import json
import logging
import re

from ia_provedores import TodosProvedoresPesquisaIndisponiveis, gerar_pesquisa_com_failover
from trofeus_service import normalizar_texto, slug_jogo

log = logging.getLogger("nara.trofeus.ai")


def _json_from_text(text: str) -> dict:
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("A IA não retornou JSON válido.")
    data = json.loads(raw[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("A resposta da IA não é um objeto JSON.")
    return data



async def _generate(prompt: str, search_queries: list[str] | None = None) -> tuple[str, list[dict]]:
    """Pesquisa com Gemini principal e alternância para o projeto Gemini reserva."""
    queries = search_queries or [
        "video game official title developer publisher release date platforms " + prompt[:60]
    ]
    text, sources, provider = await gerar_pesquisa_com_failover(prompt, queries)
    log.info("Pesquisa de catálogo concluída pelo provedor %s; fontes HTTPS=%d", provider, len(sources))
    # Fonte é sempre URL HTTPS devolvida pelo mecanismo de pesquisa, nunca URL inventada pelo modelo.
    return text, sources


# ---------------------------------------------------------------------------
# Base local curada: identidade (título, ano, estúdio) de jogos muito conhecidos.
# Serve para (1) responder sem gastar API quando a entrada é inequívoca e (2) continuar
# oferecendo sugestões quando todos os provedores de pesquisa estão fora do ar.
# Só entram dados de identidade; troféus e colecionáveis SEMPRE vêm de pesquisa com fontes.
# Entrada: (título, ano, estúdio, [apelidos])
# ---------------------------------------------------------------------------
_ESCOPO_PADRAO = "Jogo base; DLC e edições alternativas devem ser confirmadas na pesquisa."
_JOGOS_LOCAIS: tuple[tuple[str, int, str, tuple[str, ...]], ...] = (
    ("Dark Souls", 2011, "FromSoftware", ("dark souls", "dark souls 1", "dark souls i", "ds1", "dks1",
                                           "dark souls prepare to die edition", "dark souls ptde")),
    ("Dark Souls: Remastered", 2018, "FromSoftware", ("dark souls remastered", "dsr", "dark souls 1 remastered",
                                                       "dark souls", "dark souls 1", "ds1")),
    ("Dark Souls II", 2014, "FromSoftware", ("dark souls 2", "dark souls ii", "ds2", "dks2",
                                              "scholar of the first sin", "dark souls 2 sotfs", "ds2 sotfs")),
    ("Dark Souls III", 2016, "FromSoftware", ("dark souls 3", "dark souls iii", "ds3", "dks3")),
    ("Demon's Souls", 2009, "FromSoftware", ("demons souls", "demon souls", "des", "demons souls ps3")),
    ("Demon's Souls", 2020, "Bluepoint Games", ("demons souls", "demon souls", "des", "demons souls remake",
                                                 "demons souls ps5", "demons souls 2020")),
    ("Bloodborne", 2015, "FromSoftware", ("bloodborne", "blood borne", "bb")),
    ("Sekiro: Shadows Die Twice", 2019, "FromSoftware", ("sekiro", "sekiro shadows die twice", "sdt")),
    ("Elden Ring", 2022, "FromSoftware", ("elden ring", "eldenring", "er", "shadow of the erdtree", "sote")),
    ("Armored Core VI: Fires of Rubicon", 2023, "FromSoftware", ("armored core 6", "armored core vi", "ac6",
                                                                  "armored core vi fires of rubicon")),
    ("Lies of P", 2023, "Round8 Studio", ("lies of p", "liesofp", "lop")),
    ("Nioh", 2017, "Team Ninja", ("nioh", "nioh 1")),
    ("Nioh 2", 2020, "Team Ninja", ("nioh 2", "nioh2")),
    ("Wo Long: Fallen Dynasty", 2023, "Team Ninja", ("wo long", "wo long fallen dynasty")),
    ("Hollow Knight", 2017, "Team Cherry", ("hollow knight",)),
    ("Black Myth: Wukong", 2024, "Game Science", ("black myth wukong", "black myth", "wukong")),
    ("Stellar Blade", 2024, "Shift Up", ("stellar blade",)),
    ("God of War", 2005, "Santa Monica Studio", ("god of war", "gow", "god of war 1", "god of war 2005", "gow 1")),
    ("God of War", 2018, "Santa Monica Studio", ("god of war", "gow", "god of war 2018", "god of war 18",
                                                  "god of war ps4", "god of war 4", "god of war iv",
                                                  "gow 2018", "gow4", "gow 4")),
    ("God of War Ragnarök", 2022, "Santa Monica Studio", ("god of war ragnarok", "gow ragnarok", "gowr",
                                                          "ragnarok", "god of war", "gow")),
)
_SUFIXOS_PLATAFORMA = {"ps3", "ps4", "ps5", "pc", "xbox", "steam", "switch", "playstation"}
_LIMIAR_FUZZY = 0.84


def _candidato_local(titulo: str, ano: int, estudio: str, apelidos, confianca: float, evidencia: str) -> dict:
    extra = {}
    if titulo == "God of War" and ano == 2018:
        extra = {"publisher": "Sony Interactive Entertainment", "platforms": ["PlayStation 4", "PC"],
                 "edition_scope": "Jogo base de 2018; DLC e conteúdo adicional devem ser confirmados separadamente."}
    return {
        "canonical_title": titulo, "original_title": titulo, "release_year": ano,
        "developer": estudio, "publisher": extra.get("publisher", ""),
        "platforms": extra.get("platforms", []),
        "edition_scope": extra.get("edition_scope", _ESCOPO_PADRAO),
        "aliases": sorted(set(apelidos)), "confidence": round(confianca, 2),
        "identity_evidence": evidencia,
    }


def _sem_plataforma(norm: str) -> str:
    tokens = norm.split()
    while len(tokens) > 1 and tokens[-1] in _SUFIXOS_PLATAFORMA:
        tokens.pop()
    return " ".join(tokens)


def buscar_localmente(consulta: str, *, aproximado: bool = False) -> list[dict]:
    """Procura na base local. Exato: apelido idêntico (após normalizar). Aproximado: erro de digitação."""
    norm = normalizar_texto(consulta)
    if not norm:
        return []
    for tentativa in dict.fromkeys((norm, _sem_plataforma(norm))):
        exatos = [e for e in _JOGOS_LOCAIS if tentativa in {normalizar_texto(a) for a in e[3]}
                  or tentativa == normalizar_texto(e[0])]
        if exatos:
            return [
                _candidato_local(t, y, d, a, 1.0,
                                 f"Correspondência canônica local para {t} ({y}); a pesquisa de catálogo "
                                 "ainda precisa de fontes e revisão.")
                for t, y, d, a in exatos
            ]
    if not aproximado or len(norm) < 5:
        return []
    pontuados = []
    for t, y, d, a in _JOGOS_LOCAIS:
        melhor = max(difflib.SequenceMatcher(None, norm, normalizar_texto(x)).ratio()
                     for x in (t, *a) if len(normalizar_texto(x)) >= 5)
        if melhor >= _LIMIAR_FUZZY:
            pontuados.append((melhor, t, y, d, a))
    if not pontuados:
        return []
    pontuados.sort(key=lambda x: -x[0])
    topo = pontuados[0][0]
    return [
        _candidato_local(t, y, d, a, min(0.9, m),
                         f"Semelhança de nome com {t} ({y}) na base local; confirme antes de pesquisar.")
        for m, t, y, d, a in pontuados[:3] if topo - m <= 0.05
    ]


def _resultado_local(consulta: str, candidatos: list[dict], notes: str) -> dict:
    return {"input": consulta, "candidates": candidatos, "needs_clarification": len(candidatos) != 1,
            "notes": notes, "sources": []}


def identificar_local(consulta: str) -> dict | None:
    """Resolve pela base local, sem API. None se a entrada não for inequívoca."""
    consulta = " ".join((consulta or "").split())[:120]
    locais = buscar_localmente(consulta)
    if not locais:
        return None
    return _resultado_local(
        consulta, locais,
        "Título reconhecido pela base local curada. A pesquisa de catálogo e suas fontes ainda "
        "precisam ser executadas e revisadas." if len(locais) == 1 else
        "O nome digitado corresponde a mais de um jogo conhecido. Escolha a edição correta.",
    )


async def identificar_jogo(consulta: str) -> dict:
    """Resolve abreviações/erros para títulos oficiais, sem assumir edição."""
    consulta = " ".join((consulta or "").split())[:120]
    if len(consulta) < 2:
        raise ValueError("Digite pelo menos dois caracteres.")
    local = identificar_local(consulta)
    if local:
        return local
    prompt = f"""
Você é um catalogador de videogames. Identifique o jogo que o usuário quis dizer.
Entrada literal (pode conter erro, abreviação, tradução ou edição): {consulta!r}

Use as fontes web anexadas a esta solicitação. Priorize fontes oficiais (site do estúdio/editora, Steam, PlayStation,
Xbox, Nintendo) para identidade, e bases reconhecidas para desambiguação.
NÃO transforme o texto digitado em nome oficial sem verificar. NÃO invente jogos.
Diferencie jogo-base, remake/remaster, edição/versão, DLC e sequência.
Se a entrada for ambígua, retorne vários candidatos em ordem de confiança.
Retorne SOMENTE JSON neste formato:
{{
 "input": "...",
 "candidates": [
  {{"canonical_title":"título oficial","original_title":"título no idioma original",
   "release_year":2022,"developer":"estúdio","publisher":"editora",
   "platforms":["PC","PS5"],"edition_scope":"jogo base; DLC X opcional",
   "aliases":["abreviações e erros comuns"],"confidence":0.0,
   "identity_evidence":"por que é este jogo"}}
 ],
 "needs_clarification": true,
 "notes":"limitações e diferenças relevantes"
}}
No máximo 5 candidatos. Confidence entre 0 e 1. Se não houver correspondência confiável, candidates deve ser [].
"""
    try:
        text, sources = await _generate(
            prompt, [f'"{consulta}" video game official title release year developer publisher platforms']
        )
    except TodosProvedoresPesquisaIndisponiveis:
        # Pesquisa fora do ar: oferece sugestões por semelhança da base local, claramente marcadas.
        aproximados = buscar_localmente(consulta, aproximado=True)
        if not aproximados:
            raise
        log.warning("Pesquisa indisponível; usando sugestões locais por semelhança para %r.", consulta)
        return _resultado_local(
            consulta, aproximados,
            "A pesquisa online está indisponível agora. Estas sugestões vêm da base local, por semelhança "
            "de nome, e NÃO foram confirmadas em fontes. Confira o título antes de continuar.",
        )
    if not sources:
        return {
            "input": consulta, "candidates": [], "needs_clarification": True,
            "notes": "A pesquisa não retornou referências verificáveis em fontes HTTPS de nenhum provedor. Nenhuma identificação foi aceita.",
            "sources": [],
        }
    data = _json_from_text(text)
    candidates = data.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
    clean = []
    for c in candidates[:5]:
        if not isinstance(c, dict) or not str(c.get("canonical_title", "")).strip():
            continue
        try:
            confidence = max(0.0, min(1.0, float(c.get("confidence", 0))))
        except (TypeError, ValueError):
            confidence = 0.0
        clean.append({
            "canonical_title": str(c["canonical_title"]).strip()[:120],
            "original_title": str(c.get("original_title") or c["canonical_title"]).strip()[:120],
            "release_year": int(c["release_year"]) if str(c.get("release_year", "")).isdigit() and 1970 <= int(c["release_year"]) <= 2100 else None,
            "developer": str(c.get("developer", ""))[:120],
            "publisher": str(c.get("publisher", ""))[:120],
            "platforms": [str(x)[:40] for x in c.get("platforms", [])[:12]] if isinstance(c.get("platforms"), list) else [],
            "edition_scope": str(c.get("edition_scope", ""))[:500],
            "aliases": [str(x)[:100] for x in c.get("aliases", [])[:30]] if isinstance(c.get("aliases"), list) else [],
            "confidence": confidence,
            "identity_evidence": str(c.get("identity_evidence", ""))[:700],
        })
    return {
        "input": consulta, "candidates": clean,
        "needs_clarification": bool(data.get("needs_clarification", len(clean) != 1)),
        "notes": str(data.get("notes", ""))[:1000],
        "sources": sources,
    }


async def pesquisar_catalogo(candidato: dict, incluir_dlc: bool = True) -> dict:
    """Cria rascunho estruturado com fontes. O resultado sempre entra em revisão."""
    title = str(candidato.get("canonical_title", "")).strip()
    scope = str(candidato.get("edition_scope", "jogo base"))
    prompt = f"""
Você é um pesquisador de guias de videogame. Monte um RASCUNHO verificável de catálogo
para o jogo oficialmente identificado abaixo usando as fontes atuais anexadas à solicitação.
Jogo: {title}
Título original: {candidato.get('original_title', title)}
Escopo informado: {scope}
Incluir DLC: {"sim" if incluir_dlc else "não"}
Plataformas: {", ".join(candidato.get("platforms", []))}

OBJETIVO: checklist que conecte colecionáveis a troféus/conquistas sem duplicar itens.
Priorize wiki especializada do jogo, guias reconhecidos e fontes oficiais para troféus.
Não copie conteúdo extenso. Parafraseie em português. Não invente localização, requisitos,
nomes oficiais ou troféus. Se não tiver evidência suficiente, omita o registro.
Inclua armas, armaduras, anéis/acessórios, magias/habilidades, gestos e outros tipos
relevantes ao jogo, mas só os que conseguir fundamentar.
Para troféus, use a lista completa APENAS se encontrar uma fonte confiável de cobertura completa.
Se não puder assegurar completude, declare isso em coverage_notes e retorne apenas os registros
que conseguiu verificar. Não invente que o catálogo é completo.

Retorne SOMENTE JSON neste formato:
{{
 "name":"título oficial","name_original":"título original","slug":"slug-kebab-case",
 "platforms":["..."],"coverage_notes":"o que está coberto e o que falta",
 "sources":[{{"title":"...","url":"https://...","kind":"wiki|official|guide|database"}}],
 "items":[
  {{"category":"Armas","name_pt":"...","name_original":"...","description_pt":"...",
   "location_pt":"...","acquisition_pt":"...","dlc":"...","ng_cycle":"...",
   "missable":false,"source_url":"https://fonte-exata"}}
 ],
 "trophies":[
  {{"name_pt":"...","name_original":"...","description_pt":"...","grade":"Bronze|Prata|Ouro|Platina",
   "is_platinum":false,"source_url":"https://fonte-exata",
   "requirements":[{{"item_name_original":"nome exato de um item do array items",
    "description_pt":"...","quantity":1}}]}}
 ]
}}
REGRAS:
- Cada item e troféu precisa de source_url válido que apareça em sources ou seja fonte direta encontrada.
- Só conecte requirement a item que exista no array items. Não invente relações.
- Para requisitos que não sejam colecionáveis, descreva-os como texto em requirements, sem item_name_original.
- Não inclua campos verified; o sistema inicia tudo como não verificado.
- Não invente URL. Se não encontrar fonte específica, não inclua o registro.
- Respeite o escopo do jogo base/DLC informado.
"""
    search_queries = [
        f'"{title}" official trophy achievement list base game DLC',
        f'"{title}" complete collectibles weapons armor accessories spells locations guide',
        f'"{title}" missable trophies collectibles requirements guide',
        f'"{title}" all trophies achievements platinum requirements walkthrough',
    ]
    text, sources = await _generate(prompt, search_queries)
    if not sources:
        raise RuntimeError("Nenhum dos provedores de pesquisa retornou fontes HTTPS verificáveis para o catálogo.")
    data = _json_from_text(text)
    # O título foi confirmado pelo usuário; o modelo não pode renomear o jogo.
    data["name"] = title
    year = candidato.get("release_year")
    # Ano na chave evita colidir remakes/sequências com nomes canônicos iguais.
    data["slug"] = slug_jogo(title, year if isinstance(year, int) else None)
    # A lista do modelo não é prova. Só URLs retornadas pela Tavily nesta execução
    # são aceitas como evidência de pesquisa.
    merged = {}
    for src in sources:
        if not isinstance(src, dict):
            continue
        url = str(src.get("url", "")).strip()
        if url.startswith("https://"):
            merged[url] = {"title": str(src.get("title", ""))[:180], "url": url,
                           "kind": str(src.get("kind") or "web_search")[:40]}
    data["sources"] = list(merged.values())[:30]
    valid_urls = set(merged)
    # Fail closed: reject malformed records and URLs that were not surfaced as sources.
    items = []
    for item in data.get("items", []) if isinstance(data.get("items"), list) else []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("source_url", "")).strip()
        if not item.get("name_pt") or not item.get("category") or url not in valid_urls:
            continue
        item["verified"] = False
        items.append(item)
    trophies = []
    for trophy in data.get("trophies", []) if isinstance(data.get("trophies"), list) else []:
        if not isinstance(trophy, dict):
            continue
        url = str(trophy.get("source_url", "")).strip()
        if not trophy.get("name_pt") or url not in valid_urls:
            continue
        trophy["verified"] = False
        reqs = []
        for req in trophy.get("requirements", []) if isinstance(trophy.get("requirements"), list) else []:
            if isinstance(req, dict):
                reqs.append(req)
        trophy["requirements"] = reqs
        trophies.append(trophy)
    data["items"], data["trophies"] = items[:10000], trophies[:2000]
    if not data["items"] or not data["trophies"]:
        raise RuntimeError(
            "As fontes encontradas não sustentaram pelo menos um item e um troféu. "
            "O catálogo não será salvo como se estivesse completo."
        )
    data["status"] = "review"
    data["research_sources"] = len(valid_urls)
    data["coverage_notes"] = str(data.get("coverage_notes", ""))[:1500]
    return data
