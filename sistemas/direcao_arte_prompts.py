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
    """Instruções visuais do modelo completo específico da facção."""
    canonical = normalizar_faccao(valor)
    directions = {
        "Ordem Áurea": (
            "FACTION CARD TEMPLATE — ORDEM ÁUREA. Use the supplied Ordem Áurea complete-card image as the exact layout and styling reference. "
            "Preserve its warm ivory/parchment field, fine dark outline, golden-brown accents, restrained gold ornament, circular power medallion at upper left, "
            "large upper illustration, centered name panel, dark tactical strip with gold lettering and diamond markers, gold faction ribbon on the right, "
            "open lore panel and gold rarity plaque at bottom right. Its visual identity is sacred, solar, noble and disciplined. "
            "Keep the faction's gold/ivory palette and tree/solar motifs; do not copy the reference character or its lore."
        ),
        "Véu Carmesim": (
            "FACTION CARD TEMPLATE — VÉU CARMESIM. Use the supplied Véu Carmesim complete-card image as the exact layout and styling reference. "
            "Preserve its warm parchment field, dark red corner ornaments, fine pale border, circular power medallion at upper left, "
            "dominant upper illustration, pale title strip, black tactical strip with crimson diamond markers, vertical crimson faction banner on the right, "
            "spacious lore area, crimson divider detail and dark red rarity plaque at bottom right. "
            "Its visual identity is blood-red, severe, ritualistic and somber. Do not copy the reference priest or its lore."
        ),
        "Lua Negra": (
            "FACTION CARD TEMPLATE — LUA NEGRA. Use the supplied Lua Negra complete-card image as the exact layout and styling reference. "
            "Preserve its pale parchment field, fine dark border, circular power medallion at upper left, expansive upper illustration, "
            "pale title strip, black tactical strip with blue diamond markers, vertical deep-blue faction banner on the right, "
            "spacious centered lore panel, blue divider detail and deep-blue rarity plaque at bottom right. "
            "Its visual identity is lunar, nocturnal, cold and mysterious, using deep blue, silver and moonlit highlights. Do not copy Hanni or her lore."
        ),
        "Os Esquecidos": (
            "FACTION CARD TEMPLATE — OS ESQUECIDOS. Use the supplied Os Esquecidos complete-card image as the exact layout and styling reference. "
            "Preserve its pale parchment field, fine dark border, circular power medallion at upper left, large upper illustration, "
            "pale title strip, dark emerald tactical strip with green diamond markers, vertical emerald faction banner on the right, "
            "spacious lore panel, green divider detail and emerald rarity plaque at bottom right. "
            "Its visual identity is ancient, solemn and mysterious, using emerald green, antique gold and ivory. Do not copy the reference pope or his lore."
        ),
    }
    if canonical:
        return directions[canonical]
    raw = _text(valor, 100) or "blank"
    return (f"FACTION VALIDATION: '{raw}' is not one of the four registered factions. Do not infer a faction or choose a template. "
            "Request correction before generating the card.")


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
    """Ficha artística enxuta: somente os seis dados oficiais solicitados."""
    name = _text(card.get("nome") or card.get("name") or "Carta sem nome", 160)
    faction = _text(card.get("faccao") or "não informada", 80)
    rarity = _text(card.get("raridade") or "não informada", 60)
    category = _text(card.get("categoria") or "Unidade", 80)
    row = _text(card.get("fileira") or card.get("row") or "", 30)
    labels = {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}
    row_label = "Carta especial" if category.casefold() == "especial" else labels.get(row, "não informada")
    lore = _text(card.get("lore") or card.get("descricao") or card.get("description") or "", 1400)
    base_power = card.get("poder_base", card.get("poder", "não informado"))
    return "\n".join([
        f"NOME DA CARTA: {name}",
        f"PODER-BASE: {base_power}",
        f"RARIDADE: {rarity}",
        f"POSIÇÃO TÁTICA: {row_label}",
        f"FACÇÃO: {faction}",
        f"LORE: {lore or '[LORE NÃO CADASTRADA]'}",
    ])


def gerar_negative_prompt(card: dict[str, Any], *, has_ability: bool = False) -> str:
    """Negative prompt alinhado ao layout atual de seis campos."""
    return "; ".join([
        "misspelled Portuguese text, gibberish typography, wrong accent marks, incorrect card name, incorrect faction, wrong tactical position, wrong rarity, wrong base-power digit",
        "cost field, maximum power field, rarity potency field, category field, ability field, synergy field, extra statistics, extra labels, invented card attributes",
        "faction confused with tactical position, tactical position confused with faction, Força, Destreza or Magia used as combat class",
        "wrong faction template, generic universal recolored template, copied sample character, copied sample card title, copied sample lore, copied sample power number",
        "generic medieval fantasy, inaccurate Elden Ring identity, incorrect face, inaccurate species, wrong silhouette, incorrect canonical armor, clothing or signature weapon",
        "broken anatomy, extra limbs, malformed hands, fused fingers, impossible weapon grip, floating equipment, impossible perspective, inconsistent light, unreadable layout, overlapping panels, cropped title, clipped lore, cluttered composition",
        "anime, manga, cartoon, chibi, science fiction, futuristic armor, cyberpunk, glossy CGI, plastic armor, waxy skin, neon filter, excessive bloom, oversaturation, pixelation, compression artifacts, watermark, signature, external brand logo",
    ])


def montar_prompt_mestre(
    *, card: dict[str, Any], detail_prompt: str, scene_reference: str = "",
    has_ability: bool = True, ability_name: str = "", ability_rule: str = "",
    faction_direction: str = "", negative_prompt: str = "",
) -> str:
    """Prompt integral para a nova identidade visual: seis campos e template por facção."""
    name = _text(card.get("nome") or card.get("name") or "Carta sem nome", 160)
    faction_raw = _text(card.get("faccao") or "", 80)
    faction = normalizar_faccao(faction_raw)
    rarity = _text(card.get("raridade") or "", 40)
    category = _text(card.get("categoria") or "Unidade", 60)
    row = _text(card.get("fileira") or card.get("row") or "", 20)
    row_labels = {"melee": "Corpo a corpo", "ranged": "Longa distância", "siege": "Cerco"}
    row_label = "Carta especial" if category.casefold() == "especial" else row_labels.get(row, "")
    if not faction:
        raise ValueError(f"Facção ausente ou inválida para gerar a carta {name}.")
    if not rarity:
        raise ValueError(f"Raridade ausente para gerar a carta {name}.")
    if not row_label:
        raise ValueError(f"Posição tática ausente ou inválida para gerar a carta {name}.")
    try:
        base_power = int(card.get("poder_base", card.get("poder")))
    except (TypeError, ValueError):
        raise ValueError(f"Poder-base inválido para gerar a carta {name}.")
    lore = _text(card.get("descricao") or card.get("lore") or "Sem lore cadastrada.", 1400)
    canonical = canonical_reference(card)
    faction_text = faction_direction or direcao_faccao(faction)
    scene = _text(scene_reference, 1800) or "Create a scene grounded only in the exact card name, lore and canonical identity. Do not invent powers, equipment or biography."
    # detail_prompt is intentionally not interpolated: legacy builders may contain
    # category, cost, max power, rarity potency, abilities or synergies, all excluded
    # from the new six-field card face.
    negative = negative_prompt or gerar_negative_prompt(card, has_ability=False)
    return f"""NARABOT — PROMPT MESTRE DE CARTA COMPLETA — NOVA IDENTIDADE VISUAL

OBJECTIVE: create ONE finished collectible card, not a standalone illustration. Use the attached faction-specific complete card as the visual template. Each of the four factions has its OWN complete template. Do not apply a universal layout and do not recolor another faction's template.

OFFICIAL CARD DATA — THESE SIX FIELDS ARE THE ONLY CARD DATA TO PRINT:
CARD NAME: {name}
BASE POWER (upper-left medallion): {base_power}
RARITY: {rarity}
TACTICAL POSITION: {row_label}
FACTION: {faction}
LORE: {lore}

HARD EXCLUSION RULE — NEVER PRINT OR VISUALLY REPRESENT:
COST, MAXIMUM POWER, RARITY POTENCY, CATEGORY, ABILITY, SYNERGIES, combat attributes, internal IDs or any other data fields. Do not create icons, badges, empty boxes or labels for excluded fields. These values may exist in internal game records but are not part of this card design.

FIELD PLACEMENT:
- BASE POWER: exact number {base_power} in the upper-left circular power medallion.
- CARD NAME: exact name in the horizontal title panel below the artwork.
- TACTICAL POSITION: exact label “{row_label}” in the dark horizontal strip below the title.
- FACTION: exact faction identity {faction}, represented by the faction's vertical side banner and its emblem. The faction name may appear vertically as in its supplied reference.
- LORE: reproduce the supplied lore in the lower parchment panel, preserving its meaning and wording. Do not add a lore heading unless the faction reference contains one.
- RARITY: exact value “{rarity}” in the bottom-right rarity plaque.

VISUAL TEMPLATE — FACTION-SPECIFIC, NOT UNIVERSAL:
{faction_text}
The attached reference image for this faction is authoritative for card proportions, border, parchment, panel placement, typography, banner, emblem placement, divider treatment, color accents and rarity plaque. Match its structure closely. Small faction-specific differences are intentional and must be preserved. Never copy the sample character, sample card name, sample power number, sample lore or sample rarity; replace them with the six official data fields above.

ART DIRECTION:
- Main illustration occupies the same large upper artwork region as the faction reference.
- Depict the exact named subject, preserving recognizable Elden Ring identity where applicable: {canonical}
- Translate the supplied lore into a specific scene, pose, expression, equipment, setting and atmosphere. Do not invent weapons, abilities, magic, companions, canonical allegiance or biography.
- Faction styling influences the card template, restrained environmental accents and lighting. It must not overwrite the subject's canonical appearance, armor, clothing, skin, hair or signature equipment.
- Scene guidance: {scene}

TEXT AND LAYOUT RULES:
- The card is a single complete vertical 2:3 collectible card.
- Keep the entire border visible; no mockup, hands, background canvas or multiple-card sheet.
- Use clear, accurate Portuguese typography with correct accents.
- Preserve the exact six field values. Do not paraphrase, translate, abbreviate or invent them.
- Fit lore legibly inside the existing lower panel; do not remove or shrink other required fields to add new fields.
- Do not show the old dark-metal multi-stat card layout. Use the newly supplied faction-specific parchment template.

FINAL VALIDATION:
Verify that the image contains exactly the authorized information: name “{name}”, base power “{base_power}”, rarity “{rarity}”, tactical position “{row_label}”, faction “{faction}” and the supplied lore. Verify that COST, MAXIMUM POWER, RARITY POTENCY, CATEGORY, ABILITY and SYNERGIES do not appear anywhere. Confirm the correct faction-specific template was followed.

NEGATIVE PROMPT:
{negative}

OUTPUT: one finished, high-resolution vertical 2:3 card, using the attached faction-specific reference as the template."""

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
