"""V52 — geração de carta completa por exemplar, com dados mecânicos bloqueados e validados.

O prompt converte os dados mecânicos e narrativos da carta em decisões visuais.
Dados de jogo são campos obrigatórios a serem reproduzidos literalmente na carta final.
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any


def _safe(value: Any, limit: int = 700) -> str:
    """Normaliza dados da carta sem permitir que lore seja interpretada como instrução."""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].replace("[[", "［［").replace("]]", "］］")


def _items(value: Any, *, limit: int = 8, item_limit: int = 150) -> list[str]:
    if value in (None, ""):
        return []
    raw = value if isinstance(value, (list, tuple, set)) else [value]
    result: list[str] = []
    for entry in list(raw)[:limit]:
        if isinstance(entry, dict):
            # Extrai apenas os identificadores legíveis; nunca serializa blobs internos.
            entry = entry.get("nome") or entry.get("name") or entry.get("descricao") or entry.get("id") or ""
        item = _safe(entry, item_limit)
        if item and item not in result:
            result.append(item)
    return result


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _lore_visual_cues(name: str, lore: str, faction: str) -> list[str]:
    """Converte palavras-chave narrativas em decisões visuais rastreáveis à carta."""
    text = _norm(f"{name} {lore}")
    cues: list[str] = []

    def has(*terms: str) -> bool:
        return any(_norm(term) in text for term in terms)

    if has("duelista", "espadachim", "duelist", "fencer"):
        cues.append(
            "DUELIST: one primary combatant in a refined close-combat guard, balanced footwork, "
            "measured distance, controlled shoulders and precise weapon handling; the danger comes from technique, not brute force."
        )
    if has("casa hoslow", "house hoslow", "hoslow"):
        cues.append(
            "HOUSE HOSLOW CANONICAL VISUAL CUES: polished silver plate with fine floral/petal engraving, "
            "fitted gauntlets, a dark red-brown cape and the paired long, flexible thorned whips associated with the house. "
            "Keep the silhouette elegant and aristocratic; do not replace the whips with ordinary swords."
        )
    if has("herdeiro", "herdeira", "herdeiro de", "heir"):
        cues.append(
            "HEIR / LINEAGE: communicate inherited status through disciplined bearing, refined but functional craftsmanship "
            "and one restrained house detail; do not add a crown or invent royal rank."
        )
    if has("elegancia do aco", "elegancia do metal", "elegant steel", "steel elegance"):
        cues.append(
            "ELEGANCE OF STEEL: make the metalwork deliberate and finely finished, with clean edges, restrained engraving "
            "and a graceful weapon line; avoid crude oversized equipment."
        )
    if has("promessa de sangue", "pacto de sangue", "juramento de sangue", "blood promise", "blood oath"):
        cues.append(
            "PROMISE OF BLOOD / BLOOD OATH: translate the lore phrase into a solemn vow, not a literal pool of blood. "
            "Express it through dark crimson cloth, a severe controlled expression, subtle blood-red material accents "
            "and restrained tension; no gore, splatter or invented blood magic."
        )
    if has("batedor", "scout", "rastreador"):
        cues.append(
            "SCOUT ROLE: use alert observation, a practical travel-worn silhouette and awareness of routes or terrain; "
            "do not add another scout unless the card's scene explicitly requires one."
        )
    if has("proteger", "protege", "guardiao", "guardia", "sentinela", "defende", "protector", "guardian"):
        cues.append(
            "GUARDIAN / PROTECTION: convey duty through a protective line, controlled watchfulness, "
            "a defensible position or a clear object/place being guarded."
        )
    if has("vulcanica", "volcano manor", "monte gelmir", "gelmir"):
        cues.append(
            "VOLCANO MANOR / MT. GELMIR: weathered volcanic basalt, heat-darkened stone, old brass fittings, "
            "subtle soot and distant fissure warmth; do not turn the scene into a lava spectacle."
        )
    if has("lua negra", "lua", "lunar", "cariana", "cariano", "liurnia"):
        cues.append(
            "LUNAR / CARIAN MOTIF: cold silver reflections, deep blue shadow and misted stone; add no spell effect "
            "unless the card's ability or lore explicitly grants one."
        )
    if has("sacrificio", "sacrificio", "sacrifice", "ritual", "heresia", "heretico"):
        cues.append(
            "RITUAL / SACRIFICE: communicate ceremony through deliberate objects, severe architecture and composed gestures; "
            "keep violence implied rather than graphic."
        )
    if has("cinzas", "cinza", "ash"):
        cues.append("ASH: use settled ash, muted air and weathered surfaces only as environmental aftermath, not a magical effect.")
    if has("tempestade", "relampago", "raio", "storm", "lightning"):
        cues.append("STORM: use a coherent storm front and motivated lightning only when it is explicitly part of the lore.")

    if not cues:
        cues.append(
            "NO SPECIALIZED LORE KEYWORD: derive the scene from the literal named subject and full description; "
            "choose specific equipment, pose and setting only when supported, leaving unknown facts neutral."
        )
    return cues


def _faction_direction(faction: str) -> str:
    """Compatibilidade legada: delega a direção de facção ao contrato comum."""
    from sistemas.direcao_arte_prompts import direcao_faccao
    return direcao_faccao(faction)


def _rarity_direction(rarity: str) -> str:
    directions = {
        "Comum": "COMMON: intimate, grounded scale; practical equipment, restrained ornament and one clear story beat. The render quality remains premium.",
        "Rara": "RARE: a more distinctive silhouette, refined equipment detail or memorable environmental clue; do not add supernatural powers.",
        "Épica": "EPIC: more ambitious framing, richer environmental storytelling and more intricate but functional design; preserve one focal subject.",
        "Lendária": "LEGENDARY: an iconic, historically weighty moment, distinctive silhouette and carefully staged environment; grandeur must be supported by the lore.",
        "Mítica": "MYTHIC: exceptional symbolic presence and elevated atmosphere; do not imply divinity, cosmic scale or new abilities unless the card facts establish them.",
        "Primordial": "PRIMORDIAL: ancient or world-scale presence only when supported by the subject; never sacrifice readability for spectacle.",
        "Singular": "SINGULAR: communicate a unique identity through precise visual specificity, not automatically through supernatural scale or power.",
    }
    return directions.get(rarity, "RARITY: unspecified. Do not infer prestige, scale, power or supernatural effects.")


def _power_direction(power: Any, power_max: Any, rarity: str) -> str:
    try:
        current = int(power)
    except (TypeError, ValueError):
        return "POWER INTERPRETATION: no numeric power supplied; do not infer strength from missing data."
    try:
        ceiling = int(power_max)
    except (TypeError, ValueError):
        from sistemas.cartas import FAIXA_PODER
        ceiling = FAIXA_PODER.get(rarity, (current, current))[1]
    if ceiling <= 0:
        return "POWER INTERPRETATION: this is a non-unit/special effect with no unit power rating; do not depict a fighter's strength tier from a number."
    ratio = current / max(1, ceiling)
    if ratio >= 0.9:
        scale = "near the upper power ceiling for this card's rarity: highly formidable within its own tier, without automatically becoming a demigod or supernatural entity"
    elif ratio >= 0.7:
        scale = "a notably capable and dangerous subject, expressed through practiced control and credible competence"
    elif ratio >= 0.45:
        scale = "a competent subject with a clear role and believable limitations"
    else:
        scale = "a modestly powered subject; avoid champion-like spectacle or exaggerated dominance"
    return (
        f"POWER INTERPRETATION: current power {current}; maximum power {ceiling}. "
        f"Print the current value as BASE POWER and the ceiling as MAXIMUM POWER, in separate labeled fields. Visual level: {scale}. "
        "Never turn numeric stats into a glow, aura or magical effect."
    )


def gerar_prompt_arte(definition: dict[str, Any], *, card_id: str) -> dict[str, Any]:
    """Gera o prompt mestre da carta completa com dados oficiais validados."""
    from sistemas.cartas import FAIXA_PODER, HABILIDADES, RARIDADES
    from sistemas.gwent import RARITY_EFFECT_BUDGET

    if not isinstance(definition, dict):
        raise ValueError("Definição inválida para criar o prompt.")

    fields = {
        "nome": _safe(definition.get("nome"), 140),
        "descricao": _safe(definition.get("descricao") or definition.get("lore"), 1400),
        "faccao": _safe(definition.get("faccao"), 80),
        "raridade": _safe(definition.get("raridade"), 40),
        "categoria": _safe(definition.get("categoria") or "Unidade", 50),
        "afinidades": _items(definition.get("afinidades"), limit=8),
        "afinidade_dominante": _safe(definition.get("afinidade_dominante"), 60),
        "funcao": _safe(definition.get("funcao_tatica") or definition.get("funcao"), 70),
        "arquetipo": _safe(definition.get("arquetipo"), 80),
        "epiteto": _safe(definition.get("epiteto"), 100),
        "fileira": _safe(definition.get("fileira") or definition.get("row"), 30),
        "custo": definition.get("custo", 0),
        "potencia_raridade": definition.get("potencia_raridade"),
        "habilidade_id": _safe(definition.get("habilidade"), 80).casefold(),
        "poder": definition.get("poder_base", definition.get("poder")),
        "poder_maximo": (definition.get("poder_maximo") if definition.get("poder_maximo") is not None
                         else definition.get("max_power")),
        "exemplar_id": definition.get("exemplar_id"),
        "origem": _safe(definition.get("jogo_origem") or definition.get("origem"), 100),
    }
    if not fields["nome"] or not fields["faccao"] or not fields["raridade"]:
        raise ValueError("Definição incompleta para criar o prompt.")
    if fields["faccao"] not in {"Ordem Áurea", "Véu Carmesim", "Lua Negra", "Os Esquecidos"}:
        raise ValueError("Facção inválida. Use uma das quatro facções oficiais.")
    if fields["raridade"] not in RARIDADES:
        raise ValueError("Raridade inválida. Use uma das raridades oficiais.")
    if fields["categoria"].casefold() not in {"unidade", "especial"}:
        raise ValueError("Categoria inválida. Use Unidade ou Especial.")
    if fields["categoria"].casefold() != "especial" and fields["fileira"] not in {"melee", "ranged", "siege"}:
        raise ValueError("Posição tática inválida. Use melee, ranged ou siege.")

    habilidade = HABILIDADES.get(fields["habilidade_id"], {})
    habilidade_nome = _safe(habilidade.get("nome") or definition.get("habilidade_nome"), 100)
    habilidade_regra = _safe(
        habilidade.get("texto") or definition.get("habilidade_descricao") or definition.get("habilidade_regra"),
        500,
    )
    # An unresolved internal key is not, by itself, proof of an ability. Only a
    # known ability name or an explicit canonical rule may authorize a visual effect.
    tem_habilidade = bool(fields["habilidade_id"] and (habilidade_nome or habilidade_regra))
    if not tem_habilidade:
        habilidade_nome = "Sem habilidade especial"
        habilidade_regra = "A carta não possui habilidade especial. Não inventar efeitos, feitiços ou poderes visuais."

    power_ceiling = fields["poder_maximo"]
    if power_ceiling in (None, ""):
        power_ceiling = 0 if fields["categoria"].casefold() == "especial" else FAIXA_PODER.get(fields["raridade"], (0, 0))[1]
    try:
        base_power_num, max_power_num = int(fields["poder"]), int(power_ceiling)
    except (TypeError, ValueError):
        raise ValueError("Poder-base e poder máximo precisam ser números inteiros oficiais.")
    if max_power_num < base_power_num or (fields["categoria"].casefold() != "especial" and base_power_num < 1):
        raise ValueError("Poder máximo não pode ser menor que o poder-base.")
    if fields["categoria"].casefold() != "especial":
        _, rarity_ceiling = FAIXA_PODER[fields["raridade"]]
        if base_power_num > rarity_ceiling or max_power_num > rarity_ceiling:
            raise ValueError("Poder-base ou máximo acima do teto oficial da raridade.")
    try:
        cost_num = int(fields["custo"])
        # As cartas transmutadas têm custo próprio (inclusive zero); a potência
        # de raridade segue a regra oficial de combate quando não vem no snapshot.
        supplied_potency = definition.get("potencia_raridade")
        rarity_power_num = int(
            supplied_potency if supplied_potency is not None
            else RARITY_EFFECT_BUDGET.get(fields["raridade"], 0)
        )
    except (TypeError, ValueError):
        raise ValueError("Custo e potência da raridade precisam ser números inteiros oficiais.")
    expected_potency = int(RARITY_EFFECT_BUDGET.get(fields["raridade"], -1))
    if cost_num < 0 or cost_num > 12 or rarity_power_num != expected_potency:
        raise ValueError("Custo inválido ou potência da raridade incompatível com a regra oficial.")
    if fields["categoria"].casefold() == "especial" and (base_power_num != 0 or max_power_num != 0):
        raise ValueError("Cartas especiais devem ter poder-base e poder máximo iguais a zero.")
    fields["poder"] = base_power_num
    fields["custo"] = cost_num
    fields["potencia_raridade"] = rarity_power_num
    power_ceiling = max_power_num

    sinergias = _items(
        definition.get("sinergias") or definition.get("sinergia") or definition.get("synergies")
        or definition.get("relacoes_taticas"), limit=8, item_limit=180,
    )
    ingredientes = _items(definition.get("ingredientes"), limit=5, item_limit=120)
    afinidades = fields["afinidades"] or ([fields["afinidade_dominante"]] if fields["afinidade_dominante"] else [])

    affinities_direction = {
        "sagrado": "restrained sacred gold, aged ivory and a disciplined devotional mood",
        "fogo": "controlled ember warmth, heat-marked metal and localized firelight only when the lore supports fire",
        "sangue": "dark crimson accents, ritual severity and the visual language of a blood oath without gratuitous gore",
        "morte": "cold ash, weathered black metal and quiet funerary atmosphere; no random undead creatures",
        "lua": "cold lunar silver, deep blue shadow and restrained reflected moonlight",
        "magia": "precise arcane material cues and a visible source for any supernatural effect",
        "relampago": "storm-lit metal and a credible lightning source only when supported by the card",
        "gravidade": "subtle weight distortion and displaced debris only when the card's powers justify it",
        "gelo": "cold blue-grey light, frost and physically plausible frozen surfaces",
        "veneno": "muted sickly greens, damp organic textures and restrained contamination cues",
        "ancestral": "old roots, weathered organic forms and ancient natural materials",
        "bestial": "predatory movement, naturalistic animal traits only if the subject is actually bestial",
    }
    affinity_cues = [affinities_direction.get(x.casefold(), "") for x in afinidades]
    affinity_cues = list(dict.fromkeys(x for x in affinity_cues if x))

    tactical = {
        "ataque": "an offensive role: show an intent to breach, pursue or strike, with an action consistent with the named subject",
        "defesa": "a defensive role: show protection, guarded positioning, interception or steadfast resistance",
        "controle": "a control role: show the subject changing the battlefield's conditions or disrupting an advance, with the exact mechanism grounded in its lore/ability",
        "suporte": "a support role: show the subject enabling, guiding or sustaining others; do not add a crowd unless the story calls for it",
    }.get(fields["funcao"].casefold(), "use the named role and description; do not invent a profession from missing tactical data")
    row = {
        "melee": "close-quarters context and a duel-ready or engaged stance when appropriate; the named identity still determines the actual weapon",
        "ranged": "a position with clear distance, sightline or observation; do not force a bow or ranged weapon if the card does not establish one",
        "siege": "a vantage, ritual ground or battlefield-scale context only if the identity supports it; do not automatically add artillery",
    }.get(fields["fileira"].casefold(), "tactical row unspecified; infer no equipment from the row")

    type_direction = "The faction field and tactical-row field are independent. Print only the supplied tactical-row label: Corpo a corpo, Longa distância or Cerco (or Carta especial). Do not print obsolete combat classifications."
    row_label = {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}.get(fields["fileira"], "Carta especial")

    # Regra global do NARABOT: todas as artes deste sistema pertencem ao universo Elden Ring.
    origin = "Elden Ring — The Lands Between"
    lore_visual = _lore_visual_cues(fields["nome"], fields["descricao"], fields["faccao"])
    ability_visuals = {
        "primeira_luz": "A decisive first ray of dawn may catch the subject's leading edge; keep it as natural light, not spellcasting.",
        "retaliacao": "Show the instant of a measured counterattack or reversal, with clear timing and a returning weapon path.",
        "impeto": "Show forward momentum, decisive footwork and cloth responding to movement; no magical speed trail.",
        "ultimo_folego": "Show a wounded but unbroken subject gathering one final physical effort; no graphic wounds.",
        "contragolpe": "Show a precise counterstrike slipping through an opponent's guard; emphasize timing and balance.",
        "encadeamento": "Show a continuous sequence of linked movements in one readable pose, not duplicated bodies or split panels.",
        "adaptacao": "Show a changed guard or adjusted stance in response to terrain/opponent, not a supernatural transformation.",
        "sangue_frio": "Show absolute composure and controlled breathing amid pressure; no supernatural aura.",
        "instinto": "Show alert instinct through gaze, body angle and readiness to move; no animal traits unless canonical.",
        "precisao": "Show a single precise line of action and carefully aligned weapon/gesture; no random explosion.",
        "drenagem": "Show a visible transfer or depletion only when the exact card rule supports a physical/supernatural drain; otherwise keep it symbolic and subtle.",
        "cacador_arcano": "Show a hunter reading and countering a supernatural threat with a specific tool or ward supported by the lore.",
        "quebra_ritmo": "Show the interruption of an opponent's action through positioning and impact timing; no arbitrary energy effect.",
    }
    ability_visual = ability_visuals.get(fields["habilidade_id"], "")
    prompt = f"""NARABOT — CARD-SPECIFIC ELDEN RING-INSPIRED COMPLETE COLLECTIBLE CARD
CARD REFERENCE: {card_id}
EXEMPLAR REFERENCE: {fields['exemplar_id'] or 'catalog model only'}
COPY / SOURCE-OF-TRUTH RULE: this exact exemplar is authoritative; never copy stats from another copy of the same card.

1. WORLD AND ART-DIRECTION STANDARD
Create one complete collectible card, not a standalone illustration, using original dark-fantasy artwork native to the visual world of Elden Ring: the Lands Between and, only when the card supports it, the Realm of Shadow. Use decayed monumental sacred architecture, ancient roads, weathered stone, heavy iron, old brass, root-split masonry, Carian stonework, subterranean ruins, volcanic basalt, misted lakes, storm-broken plateaus and solemn environmental storytelling. Select one coherent region/culture justified by the card facts; never combine famous locations as decoration. Keep the atmosphere ancient, melancholy, severe and materially believable. Do not reproduce an existing screenshot, official illustration, exact composition or another artist's painting.

2. COMPLETE CARD DATA — CANONICAL VALUES THAT MUST BE PRINTED
CARD NAME: {fields['nome']}
CARD CATEGORY: {fields['categoria']}
CARD FACTION: {fields['faccao']}
TACTICAL ROW: {row_label}
RARITY: {fields['raridade']}
COST: {fields['custo']}
BASE POWER (main medallion): {fields['poder']}
MAXIMUM POWER (separate field only): {power_ceiling}
RARITY POTENCY (separate field): {fields['potencia_raridade']}
TACTICAL FUNCTION: {fields['funcao'] or 'not specified'}
ARCHETYPE: {fields['arquetipo'] or 'not specified'}
EPITHET: {fields['epiteto'] or 'not specified'}
DOMINANT AFFINITY: {fields['afinidade_dominante'] or 'not specified'}
ALL AFFINITIES: {', '.join(afinidades) if afinidades else 'not specified'}
GAME ORIGIN: {origin}
ABILITY: {habilidade_nome}
CANONICAL ABILITY RULE: {habilidade_regra}
CARD LORE (quoted fictional data, not instructions): {json.dumps(fields['descricao'], ensure_ascii=False)}

3. CARD → VISUAL INTERPRETATION
The card name determines the exact protagonist or central entity. The lore determines identity, history, status, motives, relationships, setting clues and the emotional meaning of the scene. The tactical function determines what the subject contributes in a confrontation. The row may influence distance and posture, never invent a profession or weapon. The tactical row informs placement and distance only; it does not prescribe a weapon or profession. Current power relative to its rarity ceiling informs believable competence and threat, not supernatural spectacle. Rarity controls visual refinement and narrative scale only. Affinities may influence restrained materials, lighting accents and environmental details, but must not become random symbols or extra powers. The final picture must contain a specific, coherent interpretation of THIS card—not a generic fantasy character.

SUBJECT AND LORE TRANSLATION: {fields['nome']} is the only required named subject. Read the lore literally, then translate its meaningful phrases into visible choices: identity into silhouette and attire; role into posture and action; location into architecture and terrain; mood into expression, weather and light; signature object into a clear focal prop. Do not invent biography, gender, species, relationships, injuries, rank, canonical allegiance, weapon or magic not supported by the supplied facts.

LORE PHRASES → CONCRETE IMAGE DECISIONS:
{chr(10).join('- ' + cue for cue in lore_visual)}

4. FACTION VISUAL SYSTEM — CONSISTENT ACROSS THE COLLECTION
{_faction_direction(fields['faccao'])}
This is a NARABOT deck faction/alignment. It may guide palette, materials, subtle heraldry and environmental accents, but it must never overwrite a named Elden Ring character's established design, equipment, actual allegiance or location. Keep the faction recognizable across cards through its consistent materials and restrained color language, not by making every subject wear the same uniform.

5. RARITY, POWER AND TACTICAL LANGUAGE
{_rarity_direction(fields['raridade'])}
{_power_direction(fields['poder'], power_ceiling, fields['raridade'])}
TACTICAL FUNCTION: {tactical}.
TACTICAL ROW: {row}. {type_direction}

6. ABILITY, AFFINITY AND SYNERGY — ONLY WHAT THE CARD SUPPORTS
{('ABILITY VISUALIZATION: translate only the exact canonical rule into one subtle, readable action or consequence. The ability must have a visible source and physical interaction with the scene. Do not add a second ability, extra spell, unrelated creature or decorative magic. ' + ability_visual if tem_habilidade else 'NO SPECIAL ABILITY — HARD CONSTRAINT: the card has no special ability. Do not add spellcasting, magical attacks, supernatural aura, floating runes, unexplained glow, energy trails or artificial powers. Convey danger, skill or status through posture, expression, training, equipment, environment and composition. Canonical traits explicitly stated in the lore remain allowed, but do not invent anything beyond them.')}
AFFINITY CUES: {'; '.join(affinity_cues) if affinity_cues else 'No affinity-specific visual effect is required. Keep the palette grounded in the faction and the card lore.'}
SYNERGY / RELATIONSHIP CONTEXT: {('; '.join(sinergias) if sinergias else 'No synergy/relationship data supplied.')}. These are strategic relationships, not a requirement to show other named cards. Do not add another character merely to illustrate synergy; use a subtle shared motif, compatible material cue or environmental hint only when it helps the main subject's story.
SOURCE INGREDIENTS (transmutation context only): {('; '.join(ingredientes) if ingredientes else 'not supplied')}. Do not portray the ingredients as a group or copy their identities; they may inform the created card's dominant affinity and material character only.

7. COMPLETE CARD COMPOSITION AND DATA LAYOUT
Create ONE concrete moment with a readable action or tense pause and an implied before-and-after. For a named person, make that person the dominant subject. For a named relic, creature, spell, place or event, make that exact thing the protagonist instead of substituting a warrior. Specify a believable pose, expression, hands, equipment, material construction and one location that fits the lore. Use a deliberate vertical 2:3 complete-card composition with foreground, subject plane and background; strong silhouette; cinematic but physically motivated light; clear focal hierarchy; atmospheric depth. Keep face, hands, weapon and signature object inside safe margins. At card-thumbnail size, the subject and its defining identity must remain immediately readable.

8. MATERIAL REALISM AND FINISH
Use believable Elden Ring material language: articulated armor, attached straps, functional weapons, woven cloth, worn leather, oxidized metal, carved stone and weathered wood. Preserve natural anatomy, credible weight, correct perspective, grounded contact shadows and consistent light direction. Premium painterly realism, controlled brushwork, nuanced value grouping and restrained detail; no glossy CGI, plastic armor, waxy skin, anime proportions or random ornament overload.

9. COMPLETE CARD OUTPUT — REQUIRED
Generate the complete finished vertical 2:3 collectible card, including frame, artwork, title, faction, rarity, tactical row, cost, base-power medallion, separate maximum-power field, separate rarity-potency field, ability name/rule and lore. Copy every supplied Portuguese label and number exactly. Never substitute maximum power for base power; the main medallion must display the base-power field. Print only Corpo a corpo, Longa distância or Cerco (or Carta especial for a special card). Faction and tactical row are independent fields. Do not print obsolete combat classifications. No generic stock fantasy warrior, unrelated companion, arbitrary dragon/skull/castle, invented spell, random weapon, gratuitous gore, neon filter, excessive bloom, artificial grain, pixelation or compression artifacts. Do not add elements solely to fill empty space.

FINAL OUTPUT: one complete vertical 2:3 card (recommended 1024×1536), with fully rendered illustration, frame, readable Portuguese typography and all canonical metadata. Do not output isolated artwork or an empty template."""
    # A saída segue o contrato do Prompt-Mestre: análise PT + prompt EN + negative EN.
    from sistemas.direcao_arte_prompts import pacote_prompt_arte

    source_card = dict(definition)
    source_card.pop("tipo", None)  # remove snapshot legado; nunca é uma fonte de classificação
    source_card.update({
        "nome": fields["nome"],
        "descricao": fields["descricao"],
        "faccao": fields["faccao"],
        "raridade": fields["raridade"],
        "categoria": "Especial" if fields["categoria"].casefold() == "especial" else "Unidade",
        "poder": fields["poder"],
        "poder_base": fields["poder"],
        "poder_maximo": power_ceiling,
        "custo": fields["custo"],
        "potencia_raridade": fields["potencia_raridade"],
        "fileira": fields["fileira"],
        "row_label": row_label,
        "funcao_tatica": fields["funcao"],
        "afinidades": afinidades,
        "sinergias": sinergias,
    })
    scene_reference = " ".join(lore_visual)
    return pacote_prompt_arte(
        card_id=card_id,
        card=source_card,
        prompt=prompt,
        scene_reference=scene_reference,
        faction_direction=_faction_direction(fields["faccao"]),
        has_ability=tem_habilidade,
        ability_name=habilidade_nome,
        ability_rule=habilidade_regra,
    )
