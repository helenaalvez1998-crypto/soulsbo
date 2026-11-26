"""Contrato comum de direção de arte para todos os prompts visuais do NARABOT.

A análise é apresentada em português; o prompt e o negative prompt são entregues
em inglês para uso direto em geradores de imagem. Este módulo não gera imagens.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

ASPECT_RATIO = "2:3"
ART_WIDTH = 1024
ART_HEIGHT = 1536


def _text(value: Any, limit: int = 1000) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]", " ", str(value or ""))
    return re.sub(r"\s+", " ", value).strip()[:limit]


def _multiline(value: Any, limit: int = 24000) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)
    return text.strip()[:limit]


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


FACTIONS = {
    "ordem aurea": "Ordem Áurea",
    "veu carmesim": "Véu Carmesim",
    "lua negra": "Lua Negra",
    "os esquecidos": "Os Esquecidos",
}


def normalizar_faccao(valor: Any) -> str:
    """Resolve somente uma das quatro facções oficiais do campo faccao; nunca infere pela lore."""
    return FACTIONS.get(_norm(_text(valor, 100)), "")


def direcao_faccao(valor: Any) -> str:
    """Direção visual compartilhada. A entrada deve vir exclusivamente de card['faccao']."""
    canonical = normalizar_faccao(valor)
    directions = {
        "Ordem Áurea": (
            "FACTION ART STANDARD — ORDEM ÁUREA (LIGHT, LAW AND FAITH): this is a NARABOT deck faction, not proof that the named subject is canonically a member of the Golden Order. "
            "Faction signature: majesty, order, nobility, spirituality and sacred authority. Use aged gold, solar yellow, warm ivory, muted bronze and neutral weathered stone as a controlled palette. "
            "Express the faction primarily through motivated golden or warm reflected light, environmental atmosphere, monumental but weathered stone, restrained sacred geometry and subtle background motifs. "
            "Leyndell, Altus Plateau, Erdtree-related architecture, temples or processional spaces may be selected only when the character's canonical identity or card lore supports that location. "
            "Do not automatically add angel wings, halos, a giant Erdtree, a paladin archetype or a full-frame gold filter. The faction must never recolor, replace or redesign canonical armor, garments, skin, hair, weapons or signature equipment."
        ),
        "Véu Carmesim": (
            "FACTION ART STANDARD — VÉU CARMESIM (BLOOD, SACRIFICE AND HERESY): this is a NARABOT deck faction, not a claim that every card subject is an official member of Mohg's blood dynasty. "
            "Faction signature: blood, violence, combat, mystery, lineage and dark elegance. Use deep crimson, blood red, claret, oxblood, blackened iron, tarnished silver and neutral ash-grey as controlled environmental and lighting accents. "
            "Express the faction through dramatic motivated red reflections, deep shadows, severe atmosphere, restrained heraldic or ritual context only when supported, and a fitting fortress, noble estate, battlefield, ruin or ceremonial environment selected from the card's actual story. "
            "Do not automatically make the subject a vampire, assassin, blood mage or demon; do not add horns, tridents, gore, bloodflame or blood magic without explicit card support. Never recolor or redesign canonical armor, garments, skin, hair, weapons or signature equipment."
        ),
        "Lua Negra": (
            "FACTION ART STANDARD — LUA NEGRA (MAGIC, COSMOS AND SECRETS): this is a NARABOT deck faction, not proof that the named subject canonically belongs to the Carian royal family or a lunar order. "
            "Faction signature: mystery, darkness, cold, lunar forces, melancholy and restrained supernatural atmosphere. Use deep blue, lunar blue, blue-grey, silver, cold white and blue-black as controlled environmental and lighting accents. "
            "Express the faction through motivated moonlight, cool reflections, mist, deep shadows and ancient ruins, night landscapes, observatories or Carian architecture only when supported by the card's actual identity and lore. "
            "Do not automatically turn the subject into a wizard, sorcerer or lunar entity; do not add a moon, starfield, glintstone spell, runes or magical aura without explicit support. Never recolor or redesign canonical armor, garments, skin, hair, weapons or signature equipment."
        ),
        "Os Esquecidos": (
            "FACTION ART STANDARD — OS ESQUECIDOS: this is a NARABOT deck faction. "
            "Use the supplied faction reference as the visual authority: deep emerald green, antique gold, warm ivory and blackened metal; "
            "sacred geometric emblems and star motifs; weathered sanctuaries, solemn ruined architecture and restrained golden light. "
            "Keep these elements as faction styling only. Do not assign unsupported religious identity, symbols, powers, clothing or canonical allegiance to the card subject."
        ),
    }
    if canonical:
        return directions[canonical]
    raw = _text(valor, 100) or "blank"
    return (
        f"FACTION FIELD VALIDATION: the card's faccao field is '{raw}', which does not match one of the game's four official factions: "
        "Ordem Áurea, Véu Carmesim, Lua Negra or Os Esquecidos. Do not infer or assign a faction from the character name, lore, appearance, abilities, affinities or synergies. "
        "Do not create a fourth faction. Keep faction-specific heraldry, uniform, palette and allegiance neutral until the actual faccao field is corrected."
    )


# Referências explícitas para personagens/identidades recorrentes. A referência
# só é aplicada quando o nome ou a lore identifica o sujeito sem ambiguidade.
CANONICAL_REFERENCES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("ranni", "ranni the witch", "ranni bruxa"),
     "Ranni the Witch: preserve her canonical blue four-armed doll body, blue skin, long red hair, broad dark pointed witch hat and layered blue-white robes. Her four arms are a defining anatomical feature; do not humanize or alter her silhouette."),
    (("malenia", "blade of miquella", "lamina de miquella"),
     "Malenia, Blade of Miquella: preserve her copper-red hair, winged gold helm, ornate worn gold armor and canonical gold prosthetic limbs. Scarlet Rot traits may appear only when the card's story or ability calls for them; do not replace her with a generic valkyrie."),
    (("radahn", "starscourge radahn", "flagelo das estrelas"),
     "Starscourge Radahn: preserve his enormous red-haired demigod silhouette, battered lion-decorated armor, twin colossal curved greatswords and his small exhausted horse Leonard when depicting his canonical mounted appearance. Gravity effects require an explicit card-supported moment."),
    (("godfrey", "first elden lord", "primeiro lorde pristino"),
     "Godfrey, First Elden Lord: preserve his towering broad warrior build, long pale-gold hair, weathered face, heavy fur mantle, massive greataxe and Serosh as the spectral lion draped across his shoulders when that canonical aspect is depicted."),
    (("maliketh", "black blade", "lamina negra"),
     "Maliketh, the Black Blade: preserve his lean towering beast-clergyman anatomy, pale mane, dark layered armor and the distinctive Black Blade. Do not turn him into a human knight or an ordinary wolf."),
    (("messmer", "impaler", "empalador"),
     "Messmer the Impaler: preserve his pale red-haired demigod appearance, serpentine eye, ornate dark red and black armor, long spear and the great serpent when the canonical aspect is relevant. Do not replace this with a generic fire knight."),
    (("hoslow", "house hoslow", "casa hoslow"),
     "House Hoslow: use the recognizable fitted polished silver plate with fine floral/petal engraving, precise gauntlets, restrained dark red-brown cape and paired long flexible thorned whips when depicting a House Hoslow duelist. Do not substitute ordinary swords."),
    (("gurranq", "beast clergyman", "clerigo bestial"),
     "Gurranq, Beast Clergyman: preserve the hunched beastman anatomy, animalistic muzzle, clawed hands and austere dark layered cleric robes. Do not turn him into a human wizard."),
    (("black knife assassin", "assassino da faca negra", "assassina da faca negra"),
     "Black Knife Assassin: preserve the compact hooded silhouette, concealed face, close-fitting dark armor and characteristic curved Black Knife. Keep the face hidden; do not add unrelated blades."),
    (("blaidd", "half wolf", "meio lobo"),
     "Blaidd: preserve the recognizable wolf-headed warrior silhouette, grey fur, heavy dark armor and oversized greatsword. Do not humanize the head or replace his weapon with a generic sword."),
    (("mohg", "lord of blood", "senhor do sangue"),
     "Mohg, Lord of Blood: preserve his imposing horned Omen anatomy, ritual garments and characteristic trident when depicting the canonical character. Bloodflame is allowed only when the scene or card ability supports it; avoid gratuitous gore."),
    (("rykard", "lord of blasphemy", "senhor da blasfemia"),
     "Rykard, Lord of Blasphemy: preserve the colossal serpent-lord anatomy and the visual relationship between the blasphemous serpent and the embedded great blade. Do not depict an ordinary humanoid knight."),
)


def canonical_reference(card: dict[str, Any]) -> str:
    haystack = _norm(" ".join((_text(card.get("nome"), 200), _text(card.get("descricao") or card.get("lore"), 1200))))
    for aliases, reference in CANONICAL_REFERENCES:
        if any((" " + _norm(alias) + " ") in (" " + haystack + " ") for alias in aliases):
            return reference
    return (
        "CANONICAL IDENTITY CHECK: first determine whether the exact named character, creature, weapon, spell or place exists in Elden Ring. "
        "When it does, preserve its recognizable in-game model, silhouette, proportions, species, face, armor, clothing, equipment, signature weapon and canonical traits. "
        "Do not create an alternate version or substitute a generic role archetype. If the exact identity cannot be established from the supplied facts, do not invent canon; create only a restrained original subject fully consistent with the Lands Between and keep unknown physical details neutral."
    )


def gerar_analise_artistica(
    card: dict[str, Any],
    *,
    scene_reference: str = "",
    faction_direction: str = "",
    has_ability: bool | None = None,
    ability_name: str = "",
    ability_rule: str = "",
) -> str:
    """Resumo de produção baseado nos dados oficiais, sem classes antigas."""
    name = _text(card.get("nome") or card.get("name") or "Carta sem nome", 160)
    faction = _text(card.get("faccao") or "não informada", 80)
    rarity = _text(card.get("raridade") or "não informada", 60)
    category = _text(card.get("categoria") or "Unidade", 80)
    row = _text(card.get("fileira") or card.get("row") or "", 30)
    labels = {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}
    row_label = "Carta especial" if category.casefold() == "especial" else labels.get(row, "não informada")
    lore = _text(card.get("lore") or card.get("descricao") or card.get("description") or "", 1200)
    base_power = card.get("poder_base", card.get("poder", "não informado"))
    max_power = card.get("poder_maximo", card.get("max_power", "não informado"))
    cost = card.get("custo", "não informado")
    rarity_power = card.get("potencia_raridade", card.get("rarity_power", "não informado"))
    effect_name = _text(ability_name or card.get("habilidade_nome") or card.get("efeito_nome") or "", 160)
    effect_text = _text(ability_rule or card.get("habilidade_texto") or card.get("habilidade_descricao") or card.get("habilidade_regra") or card.get("efeito") or "", 700)
    if has_ability is None:
        has_ability = bool(effect_name or effect_text)
    synergies = card.get("sinergias") or card.get("sinergia") or card.get("synergies") or []
    if isinstance(synergies, (list, tuple, set)):
        synergy_text = "; ".join(_text(x.get("nome") or x.get("name") or x.get("descricao") or x, 180) if isinstance(x, dict) else _text(x, 180) for x in list(synergies)[:10])
    else:
        synergy_text = _text(synergies, 500)
    lines = [
        f"CARTA: {name}.", f"FACÇÃO: {faction}.", f"RARIDADE: {rarity}.",
        f"POSIÇÃO TÁTICA: {row_label}.", f"CATEGORIA: {category}.",
        f"CUSTO: {cost}.", f"PODER-BASE (valor do medalhão): {base_power}.",
        f"PODER MÁXIMO (campo separado): {max_power}.",
        f"POTÊNCIA DA RARIDADE (campo separado): {rarity_power}.",
    ]
    if lore: lines.append(f"LORE: {lore}")
    if has_ability:
        lines.append(f"HABILIDADE: {effect_name or 'Efeito registrado'}. {effect_text}")
    else:
        lines.append("HABILIDADE: Sem habilidade especial. Não inventar um efeito.")
    if synergy_text: lines.append(f"SINERGIAS: {synergy_text}.")
    if scene_reference: lines.append(f"REFERÊNCIA DE CENA: {_text(scene_reference, 1200)}")
    lines.append("REGRA: reproduzir todos os nomes, rótulos e valores exatamente como fornecidos. A facção e a posição tática são campos independentes. Não usar Força, Destreza ou Magia como classe de combate.")
    return "\n".join(lines)

def gerar_negative_prompt(card: dict[str, Any], *, has_ability: bool = True) -> str:
    """Negative prompt para evitar divergência visual sem proibir texto ou moldura."""
    base = [
        "misspelled Portuguese text, gibberish typography, wrong accent marks, incorrect card name, incorrect faction name, wrong tactical row label, wrong digits, substituted numbers, duplicated stats, duplicated labels, invented abilities, missing required card fields, extra unrequested attributes",
        "legacy combat class labels Força, Destreza or Magia, faction inferred from combat role, faction substituted for tactical row, tactical row substituted for faction",
        "wrong power badge value, maximum power shown as base power, rarity potency shown as combat power, cost shown as power, power values swapped or merged",
        "generic medieval fantasy, inaccurate Elden Ring identity, incorrect face, inaccurate species, wrong silhouette, incorrect canonical armor, clothing or signature weapon, unrelated companions, unsupported character, random dragon or skull",
        "broken anatomy, extra limbs, malformed hands, fused fingers, impossible weapon grip, floating equipment, impossible perspective, inconsistent light, unreadable layout, overlapping panels, cropped title, clipped text, cluttered composition",
        "anime, manga, cartoon, chibi, science fiction, futuristic armor, cyberpunk, glossy CGI, plastic armor, waxy skin, neon filter, excessive bloom, oversaturation, pixelation, compression artifacts, watermark, signature, external brand logo",
    ]
    if not has_ability:
        base.append("invented ability, spellcasting, magical attack, supernatural aura, floating runes, unexplained glow, energy beam or visual effect not present in the supplied card data")
    return "; ".join(base)

def montar_prompt_mestre(
    *, card: dict[str, Any], detail_prompt: str, scene_reference: str = "",
    has_ability: bool = True, ability_name: str = "", ability_rule: str = "",
    faction_direction: str = "", negative_prompt: str = "",
) -> str:
    """Monta um prompt integral para gerar a carta completa, com dados bloqueados."""
    name = _text(card.get("nome") or card.get("name") or "Carta sem nome", 160)
    category = _text(card.get("categoria") or "Unidade", 60)
    faction_raw = _text(card.get("faccao") or "", 80)
    faction = normalizar_faccao(faction_raw)
    rarity = _text(card.get("raridade") or "", 40)
    row = _text(card.get("fileira") or card.get("row") or "", 20)
    row_labels = {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}
    special = category.casefold() == "especial"
    row_label = "Carta especial" if special else row_labels.get(row, "")
    if not faction:
        raise ValueError(f"Facção ausente ou inválida para gerar a carta {name}.")
    if not rarity:
        raise ValueError(f"Raridade ausente para gerar a carta {name}.")
    if not special and not row_label:
        raise ValueError(f"Posição tática ausente ou inválida para gerar a carta {name}.")
    if special and row_label != "Carta especial":
        raise ValueError(f"Categoria especial inconsistente para gerar a carta {name}.")
    try:
        base_power = int(card.get("poder_base", card.get("poder")))
        max_power = int(card.get("poder_maximo", card.get("max_power", base_power)))
        cost = int(card.get("custo", 0))
        rarity_power = int(card.get("potencia_raridade", card.get("rarity_power", 0)) or 0)
    except (TypeError, ValueError):
        raise ValueError(f"Valores numéricos incompletos ou inválidos para gerar a carta {name}.")
    if special:
        if base_power != 0 or max_power != 0:
            raise ValueError(f"Carta especial {name}: poder-base e poder máximo devem ser zero.")
    elif base_power < 1 or max_power < base_power:
        raise ValueError(f"Carta {name}: poder-base/poder máximo inconsistentes.")
    lore = _text(card.get("descricao") or card.get("lore") or "Sem lore cadastrada.", 1400)
    effect_name = _text(ability_name or card.get("habilidade_nome") or "Sem habilidade especial", 140)
    effect_rule = _text(ability_rule or card.get("habilidade_texto") or card.get("habilidade_descricao") or "Sem habilidade especial.", 700)
    if not has_ability:
        effect_name, effect_rule = "Sem habilidade especial", "Sem habilidade especial. Não adicionar efeitos novos."
    synergies = card.get("sinergias") or []
    if isinstance(synergies, (list, tuple, set)):
        synergy_text = "; ".join(_text(x.get("nome") or x.get("name") or x, 160) if isinstance(x, dict) else _text(x, 160) for x in list(synergies)[:10]) or "Nenhuma sinergia cadastrada"
    else:
        synergy_text = _text(synergies, 600) or "Nenhuma sinergia cadastrada"
    card_id = _text(card.get("id") or card.get("card_id") or "não informado", 100)
    exemplar_id = _text(card.get("exemplar_id") or "não se aplica (modelo de criação)", 80)
    power_label = str(base_power)
    max_label = str(max_power)
    cost_label = str(cost)
    rarity_power_label = str(rarity_power)
    affinity = card.get("afinidades") or card.get("afinidade_dominante") or "não informada"
    if isinstance(affinity, (list, tuple, set)):
        affinity = ", ".join(_text(x, 80) for x in list(affinity)[:8]) or "não informada"
    canonical = canonical_reference(card)
    faction_text = faction_direction or direcao_faccao(faction)
    scene = _text(scene_reference, 1600) or "Derive a cena somente do nome, lore, identidade e habilidade cadastrados."
    detail = _multiline(detail_prompt, 18000)
    negative = negative_prompt or gerar_negative_prompt(card, has_ability=has_ability)
    return f"""NARABOT — PROMPT MESTRE DE CARTA COMPLETA — VERSÃO 2.0

OBJETIVO: gerar UMA CARTA COLECIONÁVEL COMPLETA, pronta para o jogo, em orientação vertical 2:3. NÃO gerar somente uma ilustração. A saída final deve conter a arte, o design integral da carta, a moldura e todos os campos abaixo, com tipografia legível em português.

FONTE OFICIAL E BLOQUEIO DE DADOS — NÃO INTERPRETAR NEM RECALCULAR:
ID DO MODELO: {card_id}
ID DO EXEMPLAR: {exemplar_id}
NOME EXATO: {name}
CATEGORIA: {category}
FACÇÃO EXATA: {faction}
RARIDADE EXATA: {rarity}
POSIÇÃO TÁTICA EXATA: {row_label}
CUSTO EXATO: {cost_label}
PODER-BASE EXATO: {power_label}
PODER MÁXIMO EXATO: {max_label}
POTÊNCIA DA RARIDADE EXATA: {rarity_power_label}
NOME DA HABILIDADE: {effect_name}
REGRA DA HABILIDADE: {effect_rule}
LORE: {lore}
AFINIDADES: {affinity}
SINERGIAS: {synergy_text}

REGRAS NUMÉRICAS ABSOLUTAS:
1. O medalhão principal deve exibir exatamente PODER-BASE = {power_label}. Nunca usar {max_label} no medalhão quando o poder-base for diferente.
2. O valor {max_label} só pode aparecer no campo separado rotulado PODER MÁXIMO. Não o substituir pelo poder-base.
3. O custo é {cost_label} e deve aparecer somente no campo de custo.
4. POTÊNCIA DA RARIDADE é {rarity_power_label}; deve aparecer em seu próprio campo, nunca como poder ou custo.
5. Não somar, arredondar, estimar, evoluir ou corrigir os números. Copiar os valores fonte exatamente.
6. Se algum dado estiver ausente, não inventar um valor; deixar o campo sem número e registrar a ausência. Neste prompt, todos os valores obrigatórios foram fornecidos.

REGRAS DE IDENTIDADE E TAXONOMIA:
- FACÇÃO é identidade/alinhamento da carta; POSIÇÃO TÁTICA é uma classificação separada.
- Para unidades, escrever a posição exatamente como “Corpo a corpo”, “Longa distância” ou “Cerco”, conforme o dado acima.
- Nunca usar “Força”, “Destreza” ou “Magia” como classe, tipo de combate, fileira ou posição tática. Magia pode existir apenas como tema, lore ou habilidade quando os dados a sustentarem.
- Não converter facção em posição, nem posição em facção. Não inventar outra facção.
- Para especiais, escrever “Carta especial” em vez de uma posição de unidade.

COMPOSIÇÃO E CONTEÚDO DA CARTA:
- Tela vertical 2:3, carta única centralizada, bordas completas visíveis, sem cortes, sem mockup, sem mãos segurando a carta.
- Moldura de qualidade premium, identidade visual coerente com a raridade e acentos de facção discretos; o design não pode esconder dados.
- Ilustração principal grande e específica à identidade e lore, respeitando o universo Elden Ring e referências canônicas: {canonical}
- Campo superior do nome: “{name}”.
- Campo de facção: “{faction}”.
- Campo de raridade: “{rarity}”.
- Campo de posição tática: “{row_label}”.
- Campo de custo: “{cost_label}”.
- Medalhão de poder-base: “{power_label}”.
- Campo distinto de poder máximo: “PODER MÁXIMO {max_label}”.
- Campo distinto de potência da raridade: “POTÊNCIA DA RARIDADE {rarity_power_label}”.
- Campo de habilidade: “{effect_name}” e o texto fiel “{effect_rule}”.
- Campo de lore: reproduzir a lore sem alterar o sentido e sem acrescentar fatos.
- Campo de sinergias: “{synergy_text}”, se houver espaço; não inventar relações.

DIREÇÃO ARTÍSTICA DA FACÇÃO:
{faction_text}

CENA E INTERPRETAÇÃO VISUAL:
{scene}
{detail}

CONTROLE DE QUALIDADE ANTES DA ENTREGA:
Confirme que o nome, facção, raridade, posição tática, custo, poder-base, poder máximo, potência da raridade, habilidade e lore coincidem caractere por caractere com a fonte acima. Conferir especialmente que o medalhão mostra {power_label}, não {max_label}. Corrigir qualquer campo duplicado, trocado, omitido, ilegível ou escrito incorretamente antes de finalizar. A arte não tem autorização para alterar os dados de jogo.

NEGATIVE PROMPT:
{negative}

FORMATO FINAL: uma única carta completa em orientação vertical 2:3 (1024×1536 recomendado), com moldura, ilustração e todas as informações oficiais. Não entregar arte isolada, carta sem texto, ficha separada, folha de cartas ou composição em painel."""

def pacote_prompt_arte(
    *,
    card_id: str,
    card: dict[str, Any],
    prompt: str,
    scene_reference: str = "",
    faction_direction: str = "",
    has_ability: bool = True,
    ability_name: str = "",
    ability_rule: str = "",
) -> dict[str, Any]:
    negative = gerar_negative_prompt(card, has_ability=has_ability)
    return {
        "card_id": str(card_id),
        "analysis": gerar_analise_artistica(
            card,
            scene_reference=scene_reference,
            faction_direction=faction_direction,
            has_ability=has_ability,
            ability_name=ability_name,
            ability_rule=ability_rule,
        ),
        "prompt": montar_prompt_mestre(
            card=card,
            detail_prompt=prompt,
            scene_reference=scene_reference,
            has_ability=has_ability,
            ability_name=ability_name,
            ability_rule=ability_rule,
            faction_direction=faction_direction,
            negative_prompt=negative,
        ),
        "negative_prompt": negative,
        "language": "en",
        "recommended_aspect_ratio": ASPECT_RATIO,
        "recommended_width": ART_WIDTH,
        "recommended_height": ART_HEIGHT,
    }
